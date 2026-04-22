"""
data_engine/market/strength.py
負責讀取 sector_strength.csv 與 etf_holdings.json，計算動能指標並繪製熱力圖 (純 Reflex 後端版)
"""
import plotly.graph_objects as go
import plotly.colors as pc
import plotly.express as px
import pandas as pd
import numpy as np
import yfinance as yf
import json
import os
# 假設你的 data_engine/__init__.py 有這個函數，若無請確保能正確讀取 csv
from data_engine import load_csv 

BENCHMARK = "VTI"

PORTFOLIO_STRUCTURE = {
    "通訊服務 (Communication)": {
        "XLC": "通訊服務 SPDR", "SOCL": "社群媒體", "HERO": "電競與遊戲"
    },
    "非必需消費 (Discretionary)": {
        "XLY": "非必需消費 SPDR", "ITB": "房屋建築 (iShares)", "XHB": "房屋建築 (SPDR)",
        "IBUY": "線上零售 (Amplify)", "ONLN": "線上零售 (ProShares)", "PEJ": "休閒娛樂", "XRT": "零售業 SPDR" 
    },
    "必需消費 (Staples)": {
        "XLP": "必需消費 SPDR", "PBJ": "食品與飲料"
    },
    "能源 (Energy)": {
        "XLE": "能源 SPDR", "GUNR": "全球天然資源", "FCG": "天然氣", "XOP": "油氣開採",
        "ICLN": "全球乾淨能源", "QCLN": "綠能與乾淨能源", "OIH": "石油服務", "TAN": "太陽能",
        "NLR": "鈾與核能", "AMLP": "能源基礎建設"
    },
    "金融 (Financial)": {
        "XLF": "金融 SPDR", "VFH": "金融 (Vanguard)", "KRE": "區域型銀行", "KBE": "銀行業 SPDR",
        "IAI": "券商與交易所", "KIE": "保險業", "IPAY": "數位支付", "BIZD": "商業發展公司(BDC)"
    },
    "醫療保健 (Health Care)": {
        "XLV": "醫療保健 SPDR", "IBB": "生技 (iShares)", "XBI": "生技 (SPDR)", "IHI": "醫療設備",
        "IHF": "醫療服務提供商", "XHE": "醫療器材", "XPH": "製藥業", "MJ": "大麻替代收成"
    },
    "工業 (Industrial)": {
        "XLI": "工業 SPDR", "ITA": "航太與國防", "ROKT": "太空與深海探勘", "UFO": "太空產業",
        "SHLD": "國防科技", "BOTZ": "機器人與AI", "IYT": "交通運輸", "JETS": "全球航空業",
        "SNSR": "物聯網", "DRIV": "自駕與電動車", "PAVE": "美國基礎建設", "GRID": "智慧電網"
    },
    "原物料 (Materials)": {
        "XLB": "原物料 SPDR", "GDX": "金礦開採", "SIL": "白銀開採", "COPX": "銅礦開採",
        "XME": "金屬與採礦", "LIT": "鋰電池技術", "IYM": "美國基本物料", "URA": "鈾礦 ETF", "REMX": "稀土與戰略金屬"
    },
    "不動產 (Real Estate)": {
        "XLRE": "不動產 SPDR", "VNQ": "美國房地產 (Vanguard)", "VNQI": "全球房地產(除美國)",
        "REET": "全球 REITs", "REM": "抵押貸款 REITs"
    },
    "科技 (Technology)": {
        "XLK": "科技 SPDR", "CHAT": "生成式 AI 與科技", "AIQ": "AI 與科技", "IXN": "全球科技",
        "QTEC": "納斯達克 100 科技", "QTUM": "量子運算", "VGT": "資訊科技 (Vanguard)",
        "SOXX": "半導體 (iShares)", "SMH": "半導體 (VanEck)", "XSD": "半導體(等權重)",
        "IGV": "軟體服務", "FDN": "網路指數", "KWEB": "中國互聯網", "CIBR": "網路資安 (First Trust)",
        "HACK": "網路資安 (Amplify)", "SKYY": "雲端運算", "METV": "元宇宙", "FINX": "金融科技", "XT": "指數型科技"
    },
    "公用事業 (Utilities)": {
        "XLU": "公用事業 SPDR", "IGF": "全球基礎建設"
    },
    "主題型與極端動能 (Thematic & Momentum)": {
        "MEME": "迷因股", "DXYZ": "Destiny Tech100", "BLOK": "區塊鏈技術", "IPO": "新股上市 IPO",
        "MOAT": "寬護城河優勢", "MOO": "全球農業", "ARKK": "ARK 創新", "ARKW": "ARK 下一代網路",
        "ARKF": "ARK 金融科技", "ARKX": "ARK 太空探勘", "ARKQ": "ARK 自行技術與機器人",
        "ARKG": "ARK 基因革命", "WGMI": "比特幣礦企"
    }
}

NAME_MAPPING = {t: name for group in PORTFOLIO_STRUCTURE.values() for t, name in group.items()}
GROUP_MAPPING = {t: group_name for group_name, tickers in PORTFOLIO_STRUCTURE.items() for t in tickers.keys()}

def fetch_data(ticker: str):
    df = load_csv("sector_strength.csv")
    if df is None or df.empty: return None
    if "date" in df.columns: df["date"] = pd.to_datetime(df["date"])
    latest_price = float(df[BENCHMARK].iloc[-1]) if BENCHMARK in df.columns else 0.0
    return {"history": df, "value": latest_price, "change_pct": 0.0}

# 保留純數學運算，供後續前端表格調用 (移除了 st.cache_data)
def get_etf_top_holdings(ticker: str):
    file_path = "data/etf_holdings.json"
    if not os.path.exists(file_path): return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            etf_holdings = json.load(f)
        return etf_holdings.get(ticker, [])
    except: return []

# 保留純數學運算，供後續前端表格調用 (移除了 st.cache_data)
def compute_universal_metrics(close_df, high_df=None, low_df=None, benchmark="VTI"):
    if benchmark not in close_df.columns: return pd.DataFrame()
    bench_close = close_df[benchmark].dropna()
    
    calc_data = []
    for t in close_df.columns:
        if t == benchmark: continue
        c = close_df[t].dropna()
        
        common_idx = c.index.intersection(bench_close.index)
        if len(common_idx) < 130: continue
        
        c = c.loc[common_idx]
        b = bench_close.loc[common_idx]
        
        curr = float(c.iloc[-1])
        b_curr = float(b.iloc[-1])
        
        ret1 = (curr / float(c.iloc[-2]) - 1) * 100
        ret3 = (curr / float(c.iloc[-4]) - 1) * 100 
        ret5 = (curr / float(c.iloc[-6]) - 1) * 100
        ret10 = (curr / float(c.iloc[-11]) - 1) * 100 
        ret20 = (curr / float(c.iloc[-21]) - 1) * 100
        ret60 = (curr / float(c.iloc[-61]) - 1) * 100
        ret120 = (curr / float(c.iloc[-121]) - 1) * 100
        
        rel5 = ret5 - ((b_curr / float(b.iloc[-6]) - 1) * 100)
        rel20 = ret20 - ((b_curr / float(b.iloc[-21]) - 1) * 100)

        rs_line = c / b
        rs_60ma = rs_line.rolling(window=60).mean()
        is_rs_above_ma = float(rs_line.iloc[-1]) > float(rs_60ma.iloc[-1])
        is_rs_ma_up = float(rs_60ma.iloc[-1]) > float(rs_60ma.iloc[-2])

        delta = c.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = -delta.clip(upper=0).rolling(14).mean()
        rs = gain / loss
        rs = rs.replace([np.inf, -np.inf], 9999)
        rsi = (100 - (100 / (1 + rs))).fillna(50)
        curr_rsi = float(rsi.iloc[-1])

        if high_df is not None and low_df is not None and t in high_df.columns:
            h = high_df[t].loc[common_idx]
            l = low_df[t].loc[common_idx]
            pc_val = c.shift(1)
            tr = pd.concat([h - l, (h - pc_val).abs(), (l - pc_val).abs()], axis=1).max(axis=1)
            atr_14 = float(tr.rolling(14).mean().iloc[-1])
        else:
            atr_14 = float(delta.abs().rolling(14).mean().iloc[-1])
            
        atr_pct = (atr_14 / curr) * 100 if curr > 0 else 0

        calc_data.append({
            "Ticker": t, "Name": NAME_MAPPING.get(t, t), "Group": GROUP_MAPPING.get(t, "個股"),
            "Price": curr, "1D%": ret1, "3D%": ret3, "10D%": ret10,
            "REL5": rel5, "REL20": rel20, "_ret20": ret20, "_ret60": ret60, "_ret120": ret120,
            "RSI": curr_rsi, "RS>60MA_bool": (is_rs_above_ma and is_rs_ma_up),
            "Is RS>60MA": "✅" if (is_rs_above_ma and is_rs_ma_up) else "❌",
            "ATR%": atr_pct, "Trend": c.tail(126).tolist()
        })
        
    df_res = pd.DataFrame(calc_data)
    if df_res.empty: return df_res
    
    df_res['20R'] = df_res['_ret20'].rank(pct=True) * 100
    df_res['60R'] = df_res['_ret60'].rank(pct=True) * 100
    df_res['120R'] = df_res['_ret120'].rank(pct=True) * 100
    df_res['Total Rank'] = (0.2 * df_res['20R']) + (0.4 * df_res['60R']) + (0.4 * df_res['120R'])
    
    # 自動標記符合「4大黃金條件」的標的
    conditions = (
        (df_res['Total Rank'] >= 80) & 
        (df_res['RS>60MA_bool'] == True) & 
        (df_res['RSI'] >= 45) & 
        (df_res['RSI'] <= 60) & 
        (df_res['1D%'] > 1.0 * df_res['ATR%'])
    )
    df_res['Signal'] = np.where(conditions, '🔥', '')
    
    return df_res

# 📊 專注繪製板塊熱力圖 (回傳給 Reflex)
def plot_chart(df_history, item_config):
    if df_history.empty:
        return go.Figure()

    # 預設觀察週期 20 天
    lookback_days = 20
    
    all_data = []
    df_sorted = df_history.sort_values("date").ffill()
    
    if len(df_sorted) > lookback_days + 1:
        latest = df_sorted.iloc[-1]
        prev = df_sorted.iloc[-(lookback_days + 1)]
        for group, tickers in PORTFOLIO_STRUCTURE.items():
            for t, name in tickers.items():
                if t in df_sorted.columns and pd.notna(latest.get(t)) and prev.get(t, 0) > 0:
                    change = ((latest[t] - prev[t]) / prev[t]) * 100
                    all_data.append({
                        "代號": t, "名稱": name, "群組": group, 
                        "現價": latest[t], "漲跌幅(%)": change, "強弱分數": change
                    })
                    
    result_df = pd.DataFrame(all_data)
    if result_df.empty:
        return go.Figure()

    fig_hm = px.treemap(
        result_df, path=[px.Constant("全市場板塊與主題"), '群組', '代號'], values=[1] * len(result_df),
        color='強弱分數', color_continuous_scale='RdYlGn', color_continuous_midpoint=0,
        custom_data=['名稱', '現價', '漲跌幅(%)'],
    )
    fig_hm.update_traces(
        texttemplate="<b>%{label}</b><br>%{customdata[2]:.2f}%", 
        hovertemplate="<b>%{label} (%{customdata[0]})</b><br>現價: %{customdata[1]:.2f}<br>漲跌幅: %{customdata[2]:.2f}%<extra></extra>"
    )
    fig_hm.update_layout(margin=dict(t=10, l=0, r=0, b=0), height=550, template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
    
    # 直接將圖表物件還給大腦
    return fig_hm