"""
data_engine/market/world_sectors.py
讀取 world_sectors.csv，計算動能與波動率，並繪製熱力圖與輸出表格數據
"""
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go

PORTFOLIO_STRUCTURE = {
    "🌐 全球與美國大盤 (Global & US Broad)": {
        "VT": "全球全市場", "ACWI": "全球市場(ACWI)", "ACWX": "全球(除美國)",
        "VTI": "美股全市場", "SPY": "標普500", "QQQ": "納斯達克", "DIA": "道瓊工業",
        "IWM": "羅素2000", "MDY": "中型股", 
        "XLK": "科技板塊", "XLF": "金融板塊", "XLV": "醫療保健"
    },
    "🌏 亞洲與太平洋 (Asia & Pacific)": {
        "EWA": "澳洲", "EWH": "香港", "EWM": "馬來西亞", "EWS": "新加坡",
        "EWT": "台灣", "EWY": "南韓", "IFN": "印度(IFN)", "INDA": "印度(INDA)", 
        "EWJ": "日本", "EPP": "亞洲(不含日本)", "AAXJ": "亞洲(除日本)",
        "FXI": "中國大型股(H股)", "MCHI": "中國全市場", "ASHR": "中國滬深300(A股)", 
        "KWEB": "中國互聯網", "VNM": "越南", "EIDO": "印尼", "THD": "泰國", "EPHE": "菲律賓"
    },
    "🌎 美洲與新興市場 (Americas & EM)": {
        "EEM": "新興市場", "EMXC": "新興市場(除中國)", "VWO": "新興市場(Vanguard)",
        "ILF": "拉丁美洲", "EWC": "加拿⼤", "EWW": "墨西哥", "EWZ": "巴西",
        "ARS": "阿根廷", "ARGT": "阿根廷(ARGT)", "ECH": "智利", "EPU": "秘魯", "GXG": "哥倫比亞"
    },
    "🌍 歐洲板塊 (Europe)": {
        "EFA": "歐澳遠東", "EZU": "歐元區", "IEUR": "歐洲全市場", "VGK": "歐洲(Vanguard)",
        "EWD": "瑞典", "EWG": "德國", "EWK": "比利時", "EWL": "瑞士",
        "EWN": "荷蘭", "EWO": "奧地利", "EWP": "西班牙", "EWQ": "法國", 
        "EWU": "英國", "EWI": "義大利", "GREK": "希臘", "EPOL": "波蘭"
    },
    "🐫 中東與非洲 (Middle East & Africa)": {
        "EZA": "南非", "TUR": "土耳其", "KSA": "沙烏地阿拉伯", 
        "EIS": "以色列", "AFK": "非洲全市場"
    },
    "🏢 房地產與抵押債 (Real Estate)": {
        "VNQ": "美國房地產", "VNQI": "全球房地產(除美國)", "REET": "全球REITs", 
        "REM": "抵押貸款REITs", "MBB": "MBS抵押債券"
    },
    "💰 高股息與進階收益 (Dividend & Income)": {
        "PFF": "特別股與收益", "DVY": "精選高股息", "SCHD": "美國紅利", "IDV": "國際高股息", 
        "AMLP": "能源MLP", "JEPI": "標普掩護性買權", "JEPQ": "納指掩護性買權", 
        "QQQI": "納斯達克高收益", "DIVO": "增強型股息", "QDVO": "成長與收益", 
        "QYLD": "納指Covered Call", "XYLD": "標普Covered Call"
    },
    "🛡️ 固定收益與債券 (Fixed Income)": {
        "BND": "全市場債券", "AGG": "美國總體債", "BNDX": "國際債券", 
        "TIP": "抗通膨債", "VTIP": "短期抗通膨債", 
        "TLT": "20年期公債", "TLH": "10-20年公債", "IEF": "7-10年公債", 
        "IEI": "3-7年公債", "SHY": "1-3年公債", "BILS": "3-12個月國庫券", 
        "BIL": "1-3個月國庫券", "SGOV": "0-3個月國庫券", 
        "LQD": "投資級公司債", "HYG": "高收益債", "BINC": "主動型彈性收益", 
        "JAAA": "AAA級CLO", "JBBB": "BBB級CLO", "EMB": "新興市場債", "EMHY": "新興市場高收債"
    },
    "🛢️ 大宗商品與加密資產 (Commodities & Crypto)": {
        "DBC": "廣泛大宗商品", "PDBC": "大宗商品(PDBC)", "DBB": "基本金屬", "DBA": "農產品", 
        "GLD": "黃金", "SLV": "白銀", "CPER": "銅礦指數",
        "USO": "美國原油", "UNG": "天然氣", 
        "UUP": "美元指數", "IBIT": "比特幣"
    }
}

def fetch_data(ticker: str):
    file_path = "data/world_sectors.csv"
    if os.path.exists(file_path):
        df = pd.read_csv(file_path, parse_dates=['date'])
        return {"history": df, "value": 0, "change_pct": 0}
    return None

# 🧠 獨立出運算邏輯：給熱力圖和表格共用
def get_calculated_df(df, lookback=20):
    if df.empty: return pd.DataFrame()
    df = df.set_index('date').ffill()
    all_data = []
    
    if len(df) > lookback + 1:
        curr_prices = df.iloc[-1]
        prev_prices = df.iloc[-lookback-1]
        pct_changes = (curr_prices - prev_prices) / prev_prices
        if lookback >= 5:
            daily_returns = df.pct_change().tail(lookback)
            period_vols = daily_returns.std()
            
        for group, tickers in PORTFOLIO_STRUCTURE.items():
            for t, name in tickers.items():
                if t not in df.columns or pd.isna(curr_prices.get(t)): continue
                pct_chg = pct_changes[t]
                if lookback < 5:
                    score = pct_chg * 100
                else:
                    vol = period_vols[t]
                    score = (pct_chg / vol) if vol > 0 else 0
                
                all_data.append({
                    "群組": group,
                    "代號": t,
                    "名稱": name,
                    "現價": f"{curr_prices[t]:.2f}",
                    "漲跌幅(%)": f"{pct_chg * 100:+.2f}%",
                    "強弱分數": f"{score:+.2f}"
                })
    res_df = pd.DataFrame(all_data)
    # 按照群組與分數排序
    if not res_df.empty:
        res_df = res_df.sort_values(by=['群組', '強弱分數'], ascending=[True, False])
    return res_df

# 📊 畫圖邏輯：純粹回傳 fig
def plot_chart(df, item_config):
    result_df = get_calculated_df(df, 20)
    if result_df.empty:
        err_fig = go.Figure()
        err_fig.update_layout(title="無數據", template="plotly_dark")
        return err_fig

    fig = px.treemap(
        result_df, path=[px.Constant("全球資產"), '群組', '代號'], values=[1] * len(result_df),
        color='強弱分數', color_continuous_scale='RdYlGn', color_continuous_midpoint=0,
        custom_data=['名稱', '現價', '漲跌幅(%)', '強弱分數'],
    )
    fig.update_traces(
        textposition='middle center',
        texttemplate="<b>%{label}</b><br>%{customdata[2]}",
        hovertemplate="<b>%{label} (%{customdata[0]})</b><br>現價: %{customdata[1]}<br>漲跌幅: %{customdata[2]}<br>強弱分: %{customdata[3]}<extra></extra>"
    )
    fig.update_layout(margin=dict(t=10, l=0, r=0, b=0), height=550, template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
    return fig