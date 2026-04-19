"""
data_pipeline/market/sentiment.py
負責抓取 AAII 散戶情緒與 S&P 500 對照數據 (包含超強 Excel 智慧解析)
"""
import pandas as pd
import requests
import yfinance as yf
import os
import io
# 設定資料路徑
DATA_DIR = "data"
SENTIMENT_FILE = os.path.join(DATA_DIR, "sentiment.csv")
HISTORY_FILE = os.path.join(DATA_DIR, "AAII_History.xlsx") 

def get_aaii_latest():
    """從 AAII 官網抓取最新一週數據"""
    url = "https://www.aaii.com/sentimentsurvey/sent_results"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }
    
    try:
        r = requests.get(url, headers=headers)
        # 解決 html5lib 的黃色警告
        import io
        tables = pd.read_html(io.StringIO(r.text), flavor='html5lib')
        df = tables[0].iloc[:, [0, 1, 2, 3]]
        df.columns = ['Date', 'Bullish', 'Neutral', 'Bearish']
        
        # 🔥 修正 1：強制轉換日期，若遇到 'Reported Date' 這種文字會變 NaT，然後把它刪掉
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce', format='mixed')
        df = df.dropna(subset=['Date'])
        
        for col in ['Bullish', 'Neutral', 'Bearish']:
            if df[col].dtype == object:
                df[col] = df[col].astype(str).str.replace('%', '').astype(float)
        
        df['Spread'] = df['Bullish'] - df['Bearish']
        return df
        
    except Exception as e:
        print(f"      [Error] AAII 爬蟲失敗: {e}")
        return pd.DataFrame()

def update():
    """主更新函數：整合歷史檔 + 網路爬蟲 + S&P 500"""
    print("   ↳ 🐂🐻 [AAII Sentiment] 正在更新散戶情緒指標...")
    
    if os.path.exists(SENTIMENT_FILE):
        base_df = pd.read_csv(SENTIMENT_FILE, parse_dates=['Date'])
    elif os.path.exists(HISTORY_FILE):
        # 💡 [智慧解析] 容忍各種 Excel 格式
        try:
            # 讀取你的 Excel 檔
            base_df = pd.read_excel(HISTORY_FILE, engine='openpyxl')
            
            # 處理 Date 欄位名稱 (如果官方表頭叫 Reported Date，自動改名)
            if 'Reported Date' in base_df.columns:
                base_df = base_df.rename(columns={'Reported Date': 'Date'})
                
            base_df['Date'] = pd.to_datetime(base_df['Date'], errors='coerce')
            base_df = base_df.dropna(subset=['Date']) # 刪除沒有日期的無效行
            
            # 🔥 核心魔法：自動把 0.75 這種小數轉換成 75.0
            for col in ['Bullish', 'Neutral', 'Bearish']:
                if col in base_df.columns:
                    # 強制轉為數字，忽略無法轉換的文字
                    base_df[col] = pd.to_numeric(base_df[col], errors='coerce')
                    # 如果這欄的最大值小於或等於 1.5，代表它是百分比小數 (例如 0.75)
                    if base_df[col].max() <= 1.5:
                        base_df[col] = base_df[col] * 100
                        
            if 'Spread' not in base_df.columns and 'Bullish' in base_df.columns:
                base_df['Spread'] = base_df['Bullish'] - base_df['Bearish']
                
            # 只取我們要的欄位
            base_df = base_df[['Date', 'Bullish', 'Neutral', 'Bearish', 'Spread']]
            
        except Exception as e:
            print(f"      [Error] 讀取 Excel 失敗: {e}")
            base_df = pd.DataFrame(columns=['Date', 'Bullish', 'Neutral', 'Bearish', 'Spread'])
    else:
        print("      ⚠️ 警告：找不到 sentiment.csv 或 AAII_History.xlsx，將初始化空表")
        base_df = pd.DataFrame(columns=['Date', 'Bullish', 'Neutral', 'Bearish', 'Spread'])

    # 2. 抓取最新數據並合併
    new_df = get_aaii_latest()
    if not new_df.empty:
        cols = ['Date', 'Bullish', 'Neutral', 'Bearish', 'Spread']
        base_df = base_df[cols] if not base_df.empty else base_df
        new_df = new_df[cols]
        full_df = pd.concat([base_df, new_df]).drop_duplicates(subset=['Date'], keep='last').sort_values('Date')
    else:
        full_df = base_df

    if full_df.empty:
        return

    # 3. 重算 20 週均線
    full_df['Spread_MA20'] = full_df['Spread'].rolling(window=20).mean()

    # 4. 補上 S&P 500 收盤價
# 4. 補上 S&P 500 收盤價
    start_date = full_df['Date'].min()
    try:
        sp500 = yf.download("^GSPC", start=start_date, progress=False, auto_adjust=False)['Close']
        if not sp500.empty:
            if isinstance(sp500, pd.DataFrame):
                sp500 = sp500.iloc[:, 0]
            sp500 = sp500.reset_index()
            sp500.columns = ['Date', 'SP500_Price']
            
            # 🔥 修正 2：合併前先刪除舊有的 SP500_Price，避免欄位名稱衝突 (_x, _y)
            if 'SP500_Price' in full_df.columns:
                full_df = full_df.drop(columns=['SP500_Price'])
                
            full_df = pd.merge_asof(full_df.sort_values('Date'), 
                                    sp500.sort_values('Date'), 
                                    on='Date', 
                                    direction='backward')
    except Exception as e:
        print(f"      [Error] S&P 500 下載失敗: {e}")
    # 5. 存檔
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    full_df.to_csv(SENTIMENT_FILE, index=False)
    print(f"   ✅ [AAII Sentiment] 儲存成功，最新日期: {full_df['Date'].iloc[-1].strftime('%Y-%m-%d')}")