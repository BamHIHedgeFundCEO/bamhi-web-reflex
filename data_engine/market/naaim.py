"""
data_engine/market/naaim.py
讀取 naaim.csv 與 sentiment.csv，處理機構與散戶情緒數據 (純 Reflex 後端版)
"""
import pandas as pd
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf

# 移除 st.cache_data
def get_daily_sp500():
    try:
        sp = yf.download("^GSPC", period="max", progress=False, auto_adjust=False)
        if isinstance(sp, pd.DataFrame) and 'Close' in sp.columns:
            sp = sp['Close']
        if isinstance(sp, pd.DataFrame):
            sp = sp.iloc[:, 0]
            
        df = sp.reset_index()
        df.columns = ['date', 'SP500_Daily']
        df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
        return df
    except:
        return pd.DataFrame(columns=['date', 'SP500_Daily'])

def fetch_data(ticker: str):
    naaim_path = "data/naaim.csv"
    aaii_path = "data/sentiment.csv"
    
    df_naaim = pd.read_csv(naaim_path) if os.path.exists(naaim_path) else pd.DataFrame()
    df_aaii = pd.read_csv(aaii_path) if os.path.exists(aaii_path) else pd.DataFrame()
    
    if df_naaim.empty and df_aaii.empty:
        return None

    min_dates = []
    if not df_naaim.empty:
        df_naaim = df_naaim.rename(columns={'Date': 'date'})
        df_naaim['date'] = pd.to_datetime(df_naaim['date']).dt.tz_localize(None)
        min_dates.append(df_naaim['date'].min())
        
    if not df_aaii.empty:
        df_aaii = df_aaii.rename(columns={'Date': 'date'})
        df_aaii['date'] = pd.to_datetime(df_aaii['date']).dt.tz_localize(None)
        cols = ['date', 'Spread', 'Spread_MA20']
        df_aaii = df_aaii[[c for c in cols if c in df_aaii.columns]].rename(
            columns={'Spread': 'AAII_Spread', 'Spread_MA20': 'AAII_MA20'}
        )
        min_dates.append(df_aaii['date'].min())

    df_sp500 = get_daily_sp500()

    if min_dates and not df_sp500.empty:
        earliest_date = min(min_dates)
        df_sp500 = df_sp500[df_sp500['date'] >= earliest_date]

    dfs = []
    if not df_sp500.empty: dfs.append(df_sp500)
    if not df_naaim.empty: dfs.append(df_naaim)
    if not df_aaii.empty: dfs.append(df_aaii)

    if not dfs: return None

    df_merged = dfs[0]
    for d in dfs[1:]:
        df_merged = pd.merge(df_merged, d, on='date', how='outer')
        
    df_merged = df_merged.sort_values('date').reset_index(drop=True)

    latest_val = 0.0
    if 'NAAIM' in df_merged.columns:
        valid_naaim = df_merged['NAAIM'].dropna()
        if not valid_naaim.empty:
            latest_val = float(valid_naaim.iloc[-1])
    
    return {
        "history": df_merged,
        "value": latest_val,
        "change_pct": 0.0 
    }

def _create_macro_chart(df, title, raw_col, ma_col, raw_color, ma_color, h_upper, h_lower):
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # 1. S&P 500 (右軸)
    if 'SP500_Daily' in df.columns:
        fig.add_trace(
            go.Scatter(x=df['date'], y=df['SP500_Daily'], name="S&P 500",
                       line=dict(color='rgba(255, 255, 255, 0.4)', width=1.5),
                       connectgaps=True), 
            secondary_y=True
        )

    # 2. 原始數據 (左軸)
    if raw_col in df.columns:
        fig.add_trace(
            go.Scatter(x=df['date'], y=df[raw_col], name=f"{title} (Weekly)",
                       line=dict(color=raw_color, width=1), opacity=0.6,
                       connectgaps=True),
            secondary_y=False
        )

    # 3. MA20 均線 (左軸)
    if ma_col in df.columns:
        fig.add_trace(
            go.Scatter(x=df['date'], y=df[ma_col], name="MA20",
                       line=dict(color=ma_color, width=2.5),
                       connectgaps=True),
            secondary_y=False
        )

    # 4. 關鍵參考線
    fig.add_hline(y=h_upper, line_dash="dash", line_color="#888888", secondary_y=False)
    fig.add_hline(y=h_lower, line_dash="dash", line_color="#888888", secondary_y=False)

    # 灰底衰退帶
    recessions = [
        ("2001-03-01", "2001-11-30"), 
        ("2007-12-01", "2009-06-30"), 
        ("2020-02-01", "2020-04-30")  
    ]
    
    for s, e in recessions:
        start_date = pd.to_datetime(s).to_pydatetime()
        end_date = pd.to_datetime(e).to_pydatetime()
        
        fig.add_vrect(
            x0=start_date, x1=end_date,
            fillcolor="white", 
            opacity=0.25,  
            layer="below", 
            line_width=0
        )

    fig.update_layout(
        height=550, 
        template="plotly_dark",
        hovermode="x unified", 
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
        margin=dict(l=20, r=20, t=30, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    
    fig.update_xaxes(type="date", showgrid=True, gridcolor="#333333") 
    fig.update_yaxes(title_text="Index / Spread", secondary_y=False, showgrid=True, gridcolor="#333333")
    fig.update_yaxes(title_text="S&P 500 (Log Scale)", showgrid=False, secondary_y=True, type="log")

    return fig
    
# 智慧判斷回傳圖表 (移除 st.tabs 與 st.plotly_chart)
def plot_chart(df, item_config):
    if df.empty: return go.Figure()

    # 讀取前端指定的 ticker (預設為 NAAIM)
    ticker = item_config.get("ticker", "NAAIM") if isinstance(item_config, dict) else str(item_config)
    
    if ticker == "AAII":
        fig = _create_macro_chart(
            df, title="AAII Spread", 
            raw_col="AAII_Spread", ma_col="AAII_MA20", 
            raw_color="rgba(102, 255, 204, 0.6)", ma_color="#00cc66", 
            h_upper=25, h_lower=-25
        )
    else:
        fig = _create_macro_chart(
            df, title="NAAIM Exposure", 
            raw_col="NAAIM", ma_col="NAAIM_MA20", 
            raw_color="rgba(255, 204, 102, 0.8)", ma_color="#ff4d4d", 
            h_upper=100, h_lower=40
        )

    return fig