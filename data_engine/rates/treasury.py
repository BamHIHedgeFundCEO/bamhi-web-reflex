"""利率數據：10Y、2Y、10-2 Spread（FRED）與專屬繪圖邏輯"""
"""
data_engine/rates/treasury.py
(極速版) 讀取 data/rates.csv
"""
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
from data_engine import load_csv  # 👈 引用我們剛寫好的工具

# ❌ 舊的 @st.cache_data 拿掉，讀 CSV 不需要快取
def fetch_data(ticker: str):
    # 1. 秒讀 CSV
    df = load_csv("rates.csv")
    if df is None: return None

    # 2. 根據 ticker 挑選數據
    # CSV 裡的欄位是: date, DGS10, DGS2, Spread
    if ticker == "DGS10": series = df["DGS10"]
    elif ticker == "DGS2": series = df["DGS2"]
    elif ticker == "SPREAD_10_2": series = df["Spread"]
    else: return None

    # 3. 準備回傳格式
    history = df[["date", "DGS10", "DGS2", "Spread"]].copy()
    history["value"] = series.values # 為了畫圖統一，複製一份叫 value
    
    current_val = float(series.iloc[-1])
    # 簡單算一下漲跌 (跟第一筆比)
    change = (current_val - float(series.iloc[0])) / float(series.iloc[0]) * 100.0

    return {"value": current_val, "change_pct": change, "history": history}

def plot_chart(df_filtered, item):
    """
    負責繪製利率圖表。
    此時收到的 df_filtered 已經是 app.py 切割好區間的資料了！
    """
    start = df_filtered["date"].min()
    end = df_filtered["date"].max()

    recessions = [
        (datetime(1990, 7, 1), datetime(1991, 3, 31)),
        (datetime(2001, 3, 1), datetime(2001, 11, 30)),
        (datetime(2007, 12, 1), datetime(2009, 6, 30)),
        (datetime(2020, 2, 1), datetime(2020, 4, 30)),
    ]

    fig = go.Figure()

    if item.get("id") == "SPREAD_10_2" and "Spread" in df_filtered.columns:
        fig.add_trace(go.Scatter(x=df_filtered["date"], y=df_filtered["DGS10"], mode="lines", name="10Y (L)", line=dict(color="#2980b9", width=1.5), yaxis="y1"))
        fig.add_trace(go.Scatter(x=df_filtered["date"], y=df_filtered["DGS2"], mode="lines", name="2Y (L)", line=dict(color="#e74c3c", width=1.5), yaxis="y1"))
        fig.add_trace(go.Scatter(x=df_filtered["date"], y=df_filtered["Spread"], mode="lines", name="Spread (R)", line=dict(color="#f1c40f", width=0.5), fill="tozeroy", fillcolor="rgba(241, 196, 15, 0.35)", yaxis="y2"))
        
        yaxis_config = dict(title="Yield (%)", gridcolor="#30363d", showgrid=True)
        yaxis2_config = dict(title="Spread (%)", overlaying="y", side="right", showgrid=False)
        legend_config = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    else:
        series_name = "DGS10" if item.get("id") == "DGS10" else ("DGS2" if item.get("id") == "DGS2" else "value")
        color = "#2980b9" if series_name == "DGS10" else ("#e74c3c" if series_name == "DGS2" else "#58a6ff")
        target_col = series_name if series_name in df_filtered.columns else "value"

        fig.add_trace(go.Scatter(x=df_filtered["date"], y=df_filtered[target_col], mode="lines", name=item["name"], line=dict(color=color, width=1.8), fill="tozeroy", fillcolor="rgba(88, 166, 255, 0.10)"))
        
        yaxis_config = dict(title="Yield (%)", gridcolor="#30363d", showgrid=True)
        yaxis2_config = None
        legend_config = dict()

    # 繪製衰退區塊 (共用邏輯)
    for start_rec, end_rec in recessions:
        x0 = max(start_rec, start)
        x1 = min(end_rec, end)
        if x0 >= x1: continue
        fig.add_shape(type="rect", xref="x", yref="paper", x0=x0, x1=x1, y0=0, y1=1, fillcolor="rgba(127, 140, 141, 0.35)", line=dict(width=0), layer="below")

    layout_args = dict(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(22, 27, 34, 0.9)",
        font=dict(color="#c9d1d9", size=12), margin=dict(l=50, r=30, t=40, b=50),
        xaxis=dict(gridcolor="#30363d", showgrid=True), yaxis=yaxis_config, hovermode="x unified",
        height=450 if item.get("id") == "SPREAD_10_2" else 400
    )
    if yaxis2_config: layout_args['yaxis2'] = yaxis2_config
    if legend_config: layout_args['legend'] = legend_config
        
    fig.update_layout(**layout_args)
    return fig