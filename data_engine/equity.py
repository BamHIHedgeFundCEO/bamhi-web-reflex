"""
data_engine/equity.py
負責處理單一個股 (Tearsheet) 的即時資料抓取、指標計算與繪圖 (純 Reflex 後端版)
架構：YFinance (股價) + FMP (美股財報) + TWSE 官方 API / FinMind (台股財報 - 絕對防封鎖)
"""
import numpy as np
from plotly.subplots import make_subplots
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import requests
from datetime import datetime, timedelta

# 🔑 你的專屬 FMP API 金鑰
FMP_API_KEY = "29epqrFbGsBfasHJHyU7fnFT8CcUdeaF"

# 移除 st.cache_data
def fetch_stock_profile(ticker: str, period: str = "2y", interval: str = "1d"):
    """
    BamHI 終極大腦：硬派白嫖流，台股財報全面改用 FinMind 官方端點！
    """
    ticker_upper = ticker.upper()
    is_taiwan_stock = ticker_upper.endswith(".TW") or ticker_upper.endswith(".TWO")

    # ==========================================
    # 引擎 1：YFinance (統一負責 K 線與技術分析 - 雲端安全)
    # ==========================================
    stock = yf.Ticker(ticker_upper)
    try:
        hist = stock.history(period=period, interval=interval)
    except Exception:
        hist = pd.DataFrame()
        
    if hist.empty: return None 

    ma_windows = [5, 10, 20, 60, 120, 240]
    for ma in ma_windows:
        hist[f'MA_{ma}'] = hist['Close'].rolling(window=ma).mean()

    hist['Max_20'] = hist['High'].shift(1).rolling(window=20).max()
    hist['Min_20'] = hist['Low'].shift(1).rolling(window=20).min()
    hist['Signal_Up'] = (hist['Close'] > hist['Max_20']) & (hist['Close'].shift(1) <= hist['Max_20'].shift(1))
    hist['Signal_Down'] = (hist['Close'] < hist['Min_20']) & (hist['Close'].shift(1) >= hist['Min_20'].shift(1))

    # ==========================================
    # 🧠 植入 BamHI 量化多因子運算 (MFI, MACD, Bias)
    # ==========================================
    try:
        # 1. MFI
        typical = (hist['High'] + hist['Low'] + hist['Close']) / 3
        flow = typical * hist['Volume']
        delta = typical.diff()
        pos = pd.Series(np.where(delta > 0, flow, 0), index=hist.index).rolling(14).sum()
        neg = pd.Series(np.where(delta < 0, flow, 0), index=hist.index).rolling(14).sum()
        with np.errstate(divide='ignore', invalid='ignore'):
            mfi = 100 - (100 / (1 + pos / neg))
        hist['MFI'] = mfi.fillna(50)

        # 2. MACD
        exp12 = hist['Close'].ewm(span=12, adjust=False).mean()
        exp26 = hist['Close'].ewm(span=26, adjust=False).mean()
        macd = exp12 - exp26
        signal = macd.ewm(span=9, adjust=False).mean()
        hist['MACD_Hist'] = macd - signal

        # 3. Bias (乖離率)
        if 'MA_60' in hist.columns:
            hist['Bias'] = (hist['Close'] - hist['MA_60']) / hist['MA_60'] * 100
        else:
            hist['Bias'] = 0

        # 4. 滾動排名 (Composite Score)
        lookback = min(250, len(hist)) # 防呆：如果選擇半年線，資料不夠 250 天就拿最大天數
        if lookback > 10:
            def get_rank(series):
                return series.rolling(lookback, min_periods=1).apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1] * 100, raw=False)

            hist['Score_MFI'] = get_rank(hist['MFI'])
            hist['Score_MACD'] = get_rank(hist['MACD_Hist'])
            hist['Score_Bias'] = get_rank(hist['Bias'])
            hist['Composite'] = (hist['Score_MFI'] + hist['Score_MACD'] + hist['Score_Bias']) / 3
        else:
            hist['Composite'] = 50 # 資料太少時給中性分數
    except Exception as e:
        print(f"量化指標計算失敗: {e}")

    # ==========================================
    # 引擎 2：智能分流財務萃取
    # ==========================================
    info = {}
    income_stmt = pd.DataFrame()
    finance_source = None

    if is_taiwan_stock:
        # 🟢 【台股模式 - 雲端專業量化版：FMP (英文簡介) + FinMind (台股財報)】
        symbol = ticker_upper.split('.')[0]
        info['sector'] = '台灣市場 (TWSE)'
        
        # 💡 從歷史 K 線拿最新收盤價，這是計算估值指標的核心！
        current_price = float(hist['Close'].iloc[-1]) if not hist.empty else 0
        info['currentPrice'] = current_price

        # ==========================================
        # A. 質性簡介 (FMP 拿深度英文介紹，雲端安全)
        # ==========================================
        try:
            profile_url = f"https://financialmodelingprep.com/stable/profile?symbol={ticker_upper}&apikey={FMP_API_KEY}"
            p_resp = requests.get(profile_url, timeout=10).json()
            if p_resp:
                p = p_resp[0] if isinstance(p_resp, list) else p_resp
                info['shortName'] = p.get('companyName', ticker_upper)
                info['industry'] = p.get('industry', 'N/A')
                info['longBusinessSummary'] = p.get('description', '暫無公司業務介紹。')
                info['fullTimeEmployees'] = p.get('fullTimeEmployees', 'N/A')
        except Exception as e:
            print(f"FMP 基本資料抓取失敗: {e}")

        # ==========================================
        # B. 財務數據 (FinMind API - 專為量化交易設計，不怕雲端封鎖)
        # ==========================================
        # 設定抓取近一年的資料，確保能精準抓到最新一季
        start_date = (datetime.now() - timedelta(days=400)).strftime('%Y-%m-%d')
        fm_url = "https://api.finmindtrade.com/api/v4/data"

        try:
            print(f"🚀 啟動 FinMind 專業量化引擎抓取 {symbol} 財報...")
            
            # 1. 綜合損益表
            is_params = {"dataset": "TaiwanStockFinancialStatements", "data_id": symbol, "start_date": start_date}
            is_resp = requests.get(fm_url, params=is_params, timeout=15).json()
            
            # 2. 資產負債表
            bs_params = {"dataset": "TaiwanStockBalanceSheet", "data_id": symbol, "start_date": start_date}
            bs_resp = requests.get(fm_url, params=bs_params, timeout=15).json()

            # 🌟 3. 新增：現金流量表 (用來算 Operating CF 與 Free CF)
            cf_params = {"dataset": "TaiwanStockCashFlowsStatement", "data_id": symbol, "start_date": start_date}
            cf_resp = requests.get(fm_url, params=cf_params, timeout=15).json()

            # 4. 官方每日估值 (P/E, P/B)
            per_params = {"dataset": "TaiwanStockPER", "data_id": symbol, "start_date": start_date}
            per_resp = requests.get(fm_url, params=per_params, timeout=15).json()

            def get_val(d, keys):
                for k in keys:
                    if k in d: return float(d[k])
                return 0

            # --- 處理每日估值 (P/E, P/B) ---
            if per_resp.get("msg") == "success" and len(per_resp.get("data", [])) > 0:
                df_per = pd.DataFrame(per_resp["data"])
                latest_per = df_per.iloc[-1]
                info['trailingPE'] = float(latest_per.get('PER', 0))
                info['priceToBook'] = float(latest_per.get('PBR', 0))

            # 🌟 --- 處理現金流量表 ---
            op_cf, free_cf = None, None
            if cf_resp.get("msg") == "success" and len(cf_resp.get("data", [])) > 0:
                df_cf = pd.DataFrame(cf_resp["data"])
                latest_date_cf = df_cf['date'].max()
                df_cf_latest = df_cf[df_cf['date'] == latest_date_cf]
                cf_dict = dict(zip(df_cf_latest['type'], df_cf_latest['value']))
                
                # 營運現金流 (IFRS 詞彙)
                op_cf = get_val(cf_dict, ['NetCashGeneratedFromUsedInOperatingActivities', 'NetCashFlowsFromOperatingActivities'])
                
                # 資本支出 CAPEX (取得不動產、廠房及設備，通常為負值流出)
                capex = get_val(cf_dict, ['AcquisitionOfPropertyPlantAndEquipment', 'PurchasesOfPropertyPlantAndEquipment'])
                
                # 計算自由現金流 = 營運現金流 - 資本支出的絕對值
                if op_cf != 0:
                    free_cf = op_cf - abs(capex)

            # --- 處理損益表 ---
            if is_resp.get("msg") == "success" and len(is_resp.get("data", [])) > 0:
                df_is = pd.DataFrame(is_resp["data"])
                latest_date_is = df_is['date'].max()
                df_is_latest = df_is[df_is['date'] == latest_date_is]
                is_dict = dict(zip(df_is_latest['type'], df_is_latest['value']))

                rev = get_val(is_dict, ['Revenue', 'OperatingRevenue', 'NetRevenue'])
                gp = get_val(is_dict, ['GrossProfit', 'OperatingIncome'])
                ni = get_val(is_dict, ['NetIncome', 'NetIncomeLoss', 'ProfitLoss', 'ProfitLossAttributableToOwnersOfParent'])
                eps = get_val(is_dict, ['EPS', 'BasicEarningsLossPerShare'])

                if 'trailingPE' not in info and eps > 0 and current_price > 0:
                    info['trailingPE'] = current_price / (eps * 4)

                col_name = f"{latest_date_is} (FinMind)"
                tw_fin = pd.DataFrame(index=[
                    '營收 (Revenue)', '營收年增率 (YoY)', '毛利率 (Gross Margin)', '淨利率 (Net Margin)',
                    '單季 EPS', '營運現金流 (Operating CF)', '自由現金流 (Free CF)'
                ], columns=[col_name])

                tw_fin.loc['營收 (Revenue)', col_name] = rev / 1000 if rev else 0
                tw_fin.loc['營收年增率 (YoY)', col_name] = None 
                tw_fin.loc['毛利率 (Gross Margin)', col_name] = gp / rev if rev else 0
                tw_fin.loc['淨利率 (Net Margin)', col_name] = ni / rev if rev else 0
                tw_fin.loc['單季 EPS', col_name] = eps
                
                # 🌟 把剛剛算好的現金流放進來，並除以 1000 配合 M (百萬) 單位
                tw_fin.loc['營運現金流 (Operating CF)', col_name] = op_cf / 1000 if op_cf is not None else None
                tw_fin.loc['自由現金流 (Free CF)', col_name] = free_cf / 1000 if free_cf is not None else None
                
                income_stmt = tw_fin

                # --- 處理資產負債表 ---
                if bs_resp.get("msg") == "success" and len(bs_resp.get("data", [])) > 0:
                    df_bs = pd.DataFrame(bs_resp["data"])
                    latest_date_bs = df_bs['date'].max()
                    df_bs_latest = df_bs[df_bs['date'] == latest_date_bs]
                    bs_dict = dict(zip(df_bs_latest['type'], df_bs_latest['value']))

                    equity = get_val(bs_dict, ['TotalEquity', 'EquityAttributableToOwnersOfParent', 'Equity'])
                    ordinary_shares = get_val(bs_dict, ['OrdinaryShareCapital', 'ShareCapital', 'CapitalStock', 'OrdinaryShares']) 

                    if equity > 0 and ni != 0:
                        info['returnOnEquity'] = ni / equity

                    if ordinary_shares > 0 and current_price > 0:
                        info['marketCap'] = (ordinary_shares / 10) * current_price

        except Exception as e:
            print(f"FinMind 量化引擎抓取失敗: {e}")
    else:
        # 🔵 【美股模式 - 雲端專業版：100% FMP 引擎】
        info['currentPrice'] = float(hist['Close'].iloc[-1]) if not hist.empty else 0

        # ==========================================
        # A. 基本資料與估值 (向 FMP 拿，雲端防封鎖)
        # ==========================================
        try:
            # 1. 拿公司介紹與市值
            profile_url = f"https://financialmodelingprep.com/stable/profile?symbol={ticker_upper}&apikey={FMP_API_KEY}"
            p_resp = requests.get(profile_url, timeout=10).json()
            if p_resp:
                p = p_resp[0] if isinstance(p_resp, list) else p_resp
                info['shortName'] = p.get('companyName', ticker_upper)
                info['sector'] = p.get('sector', 'N/A')
                info['industry'] = p.get('industry', 'N/A')
                info['longBusinessSummary'] = p.get('description', '暫無公司業務介紹。')
                info['website'] = p.get('website', 'N/A')
                info['fullTimeEmployees'] = p.get('fullTimeEmployees', 'N/A')
                info['marketCap'] = p.get('mktCap', 0)

            # 2. 拿 P/E, P/B, ROE
            metrics_url = f"https://financialmodelingprep.com/stable/key-metrics-ttm?symbol={ticker_upper}&apikey={FMP_API_KEY}"
            m_resp = requests.get(metrics_url, timeout=10).json()
            if m_resp:
                m = m_resp[0] if isinstance(m_resp, list) else m_resp
                info['trailingPE'] = m.get('peRatioTTM', None)
                info['priceToBook'] = m.get('pbRatioTTM', None)
                info['returnOnEquity'] = m.get('roeTTM', None)
        except Exception as e:
            print(f"美股基本資料抓取失敗: {e}")

        # ==========================================
        # B. 財務數據 (向 FMP 拿單季財報，並自行精算利潤率)
        # ==========================================
        try:
            is_url = f"https://financialmodelingprep.com/stable/income-statement?symbol={ticker_upper}&period=quarter&limit=5&apikey={FMP_API_KEY}"
            cf_url = f"https://financialmodelingprep.com/stable/cash-flow-statement?symbol={ticker_upper}&period=quarter&limit=4&apikey={FMP_API_KEY}"
            is_resp = requests.get(is_url, timeout=10).json()
            cf_resp = requests.get(cf_url, timeout=10).json()

            if is_resp and cf_resp:
                df_is = pd.DataFrame(is_resp if isinstance(is_resp, list) else [is_resp])
                df_cf = pd.DataFrame(cf_resp if isinstance(cf_resp, list) else [cf_resp])
                
                if not df_is.empty and not df_cf.empty:
                    df_is.set_index('date', inplace=True)
                    df_cf.set_index('date', inplace=True)
                    
                    # 💡 安全機制：自己算毛利率與淨利率，不依賴 API 提供的 ratio 欄位
                    if 'grossProfit' in df_is.columns and 'revenue' in df_is.columns:
                        df_is['grossProfitRatio'] = df_is['grossProfit'] / df_is['revenue']
                    if 'netIncome' in df_is.columns and 'revenue' in df_is.columns:
                        df_is['netIncomeRatio'] = df_is['netIncome'] / df_is['revenue']
                    
                    # 算營收年增率 (YoY)
                    if len(df_is) >= 5: 
                        df_is['revenue_YoY'] = df_is['revenue'].pct_change(periods=-4)
                    else: 
                        df_is['revenue_YoY'] = None
                        
                    df_combined = pd.concat([df_is.head(4), df_cf.head(4)], axis=1).T
                    mapping = {
                        'revenue': '營收 (Revenue)', 
                        'revenue_YoY': '營收年增率 (YoY)', 
                        'grossProfitRatio': '毛利率 (Gross Margin)', 
                        'netIncomeRatio': '淨利率 (Net Margin)', 
                        'eps': '單季 EPS', 
                        'operatingCashFlow': '營運現金流 (Operating CF)', 
                        'freeCashFlow': '自由現金流 (Free CF)'
                    }
                    available_cols = [c for c in mapping.keys() if c in df_combined.index]
                    income_stmt = df_combined.loc[available_cols].rename(index=mapping)
        except Exception as e:
            print(f"美股財報抓取失敗: {e}")

    # 防呆補上收盤價
    if 'currentPrice' not in info and not hist.empty:
        info['currentPrice'] = float(hist['Close'].iloc[-1])
        info['previousClose'] = float(hist['Close'].iloc[-2]) if len(hist) > 1 else float(hist['Close'].iloc[-1])
    
    return {"info": info, "history": hist, "income_stmt": income_stmt, "finance_source": finance_source}

# ==========================================
# 繪圖引擎 (完全保留高質感 K 線與中文設定)
# ==========================================
def plot_candlestick(hist: pd.DataFrame, ticker: str, interval: str = "1d"):
    if hist.empty: return go.Figure()
        
    # 🌟 建立雙層圖表：上圖佔 70% (K線)，下圖佔 30% (指標)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        row_heights=[0.7, 0.3], vertical_spacing=0.05)

    hover_text = hist.apply(
        lambda row: f"<b>日期: {row.name.strftime('%Y-%m-%d %H:%M') if pd.notna(row.name) else ''}</b><br><br>"
                    f"開盤價: $ {row['Open']:.2f}<br>最高價: $ {row['High']:.2f}<br>"
                    f"最低價: $ {row['Low']:.2f}<br>收盤價: $ {row['Close']:.2f}", axis=1
    )

    # 1️⃣ 上圖 (Row 1): K 線
    fig.add_trace(go.Candlestick(
        x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'],
        name="K線", hovertext=hover_text, hoverinfo="text"       
    ), row=1, col=1)

    # 2️⃣ 上圖 (Row 1): 均線系統
    ma_colors = { 5: '#f59e0b', 10: '#3b82f6', 20: '#ec4899', 60: '#10b981', 120: '#DA70D6', 240: '#ef4444' }
    for ma, color in ma_colors.items():
        if f'MA_{ma}' in hist.columns:
            plot_df = hist.dropna(subset=[f'MA_{ma}'])
            fig.add_trace(go.Scatter(
                x=plot_df.index, y=plot_df[f'MA_{ma}'], mode='lines', name=f'{ma}MA',
                line=dict(color=color, width=1.2), hoverinfo='skip' 
            ), row=1, col=1)

    # 🎯 3️⃣ 上圖 (Row 1): 補回你的 20 期突破/跌破訊號！
    if 'Signal_Up' in hist.columns and 'Signal_Down' in hist.columns:
        up_signals = hist[hist['Signal_Up']]
        down_signals = hist[hist['Signal_Down']]

        if not up_signals.empty:
            fig.add_trace(go.Scatter(
                x=up_signals.index, y=up_signals['Low'] * 0.96,
                mode='markers', name='突破20期高',
                marker=dict(symbol='triangle-up', size=14, color='#34d399', line=dict(width=1, color='black'))
            ), row=1, col=1) 

        if not down_signals.empty:
            fig.add_trace(go.Scatter(
                x=down_signals.index, y=down_signals['High'] * 1.04,
                mode='markers', name='跌破20期低',
                marker=dict(symbol='triangle-down', size=14, color='#ef4444', line=dict(width=1, color='black'))
            ), row=1, col=1) 

    # 📊 4️⃣ 下圖 (Row 2): 多因子綜合分數 (Composite)
    if 'Composite' in hist.columns:
        fig.add_trace(go.Scatter(
            x=hist.index, y=hist['Composite'], mode='lines', name='量化分數 (Composite)',
            line=dict(color='#00BFFF', width=2)
        ), row=2, col=1)

        # 畫出超買(75)與超賣(25)的警戒線與紅色/綠色填滿區域
        fig.add_hline(y=75, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=25, line_dash="dash", line_color="green", row=2, col=1)
        fig.add_hrect(y0=75, y1=100, fillcolor="red", opacity=0.1, layer="below", row=2, col=1)
        fig.add_hrect(y0=0, y1=25, fillcolor="green", opacity=0.1, layer="below", row=2, col=1)

    # 隱藏六日的空白區塊
    breaks = [dict(bounds=["sat", "mon"])] 
    if interval == "1h": breaks.append(dict(bounds=[16, 9.5], pattern="hour"))
    fig.update_xaxes(rangebreaks=breaks)

    # 樣式設定
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=30, b=0), xaxis_rangeslider_visible=False,
        height=700, 
        title=f"{ticker} 價格走勢與 BamHI 綜合訊號",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # 設定 Y 軸標題與範圍
    fig.update_yaxes(title_text="股價", row=1, col=1)
    fig.update_yaxes(title_text="分數 (0-100)", range=[0, 100], row=2, col=1)
    
    return fig