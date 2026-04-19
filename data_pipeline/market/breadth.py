"""
data_pipeline/market/breadth.py
負責抓取 S&P 500 市場寬度 -> 存成 data/breadth.csv
(採用 Batch 分批運算，防止記憶體爆炸)
"""
import yfinance as yf
import pandas as pd
import requests
from io import StringIO
import os
import gc  # 垃圾回收機制，用來清記憶體

def update():
    print("   ↳ 📊 [Breadth] 正在分析 S&P 500 市場寬度 (防爆模式啟動)...")
    
    START_DATE = "2007-01-01"
    BATCH_SIZE = 50  # 每次只處理 50 檔股票

    # 1. 抓成分股清單
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers)
        tickers = pd.read_html(StringIO(r.text))[0]['Symbol'].tolist()
        tickers = [t.replace('.', '-') for t in tickers]
    except Exception as e:
        print(f"   ❌ [Breadth] 無法抓取成分股: {e}")
        return

    # 2. 下載資料 (這步最久，請耐心等候)
    print("      📥 下載 500 檔股價數據中...")
    try:
        data = yf.download(tickers, start=START_DATE, auto_adjust=True, threads=True, progress=False)['Close']
        # 簡單清理
        data = data.dropna(axis=1, how='all').ffill().astype('float32')
    except Exception as e:
        print(f"   ❌ [Breadth] 下載失敗: {e}")
        return

    # 3. 分批計算寬度 (你的防爆邏輯)
    print("      🧮 開始分批運算 (Batch Processing)...")
    
    numerator_50 = pd.Series(0, index=data.index, dtype='float32')
    numerator_200 = pd.Series(0, index=data.index, dtype='float32')
    denominator = pd.Series(0, index=data.index, dtype='float32')

    all_cols = data.columns
    total_stocks = len(all_cols)

    # 開始分批切肉
    for i in range(0, total_stocks, BATCH_SIZE):
        batch_cols = all_cols[i : i + BATCH_SIZE]
        batch_data = data[batch_cols]
        
        # 計算 MA
        ma50_batch = batch_data.rolling(window=50).mean()
        ma200_batch = batch_data.rolling(window=200).mean()
        
        # 判斷是否站上均線
        above_50_batch = (batch_data > ma50_batch).astype('float32')
        above_200_batch = (batch_data > ma200_batch).astype('float32')
        valid_batch = batch_data.notna().astype('float32')
        
        # 累加結果
        numerator_50 = numerator_50.add(above_50_batch.sum(axis=1).fillna(0), fill_value=0)
        numerator_200 = numerator_200.add(above_200_batch.sum(axis=1).fillna(0), fill_value=0)
        denominator = denominator.add(valid_batch.sum(axis=1).fillna(0), fill_value=0)
        
        # 🧹 清理記憶體 (關鍵！)
        del batch_data, ma50_batch, ma200_batch, above_50_batch, above_200_batch, valid_batch
        gc.collect()

    # 計算最終百分比
    breadth_50 = (numerator_50 / denominator).fillna(0) * 100
    breadth_200 = (numerator_200 / denominator).fillna(0) * 100
    
    # 平滑處理 (避免鋸齒狀太醜)
    breadth_50_smooth = breadth_50.rolling(window=3).mean()

    # 清除原始大數據，釋放記憶體
    del data, numerator_50, numerator_200, denominator
    gc.collect()

    # 4. 下載大盤指數 (當作基準)
    print("      📥 下載 S&P 500 指數...")
    sp500_df = yf.download("^GSPC", start=START_DATE, auto_adjust=True, progress=False)
    sp500 = sp500_df['Close'].squeeze() if 'Close' in sp500_df.columns else sp500_df.squeeze()

    # 5. 合併並存檔
    df_result = pd.DataFrame({
        "value": sp500,
        "breadth_200": breadth_200,
        "breadth_50": breadth_50_smooth
    }).dropna().reset_index()

    # 統一欄位名稱
    if "Date" in df_result.columns:
        df_result.rename(columns={"Date": "date"}, inplace=True)
    
    # 存檔
    if not os.path.exists("data"): os.makedirs("data")
    file_path = "data/breadth.csv"
    df_result.to_csv(file_path, index=False)
    
    print(f"   ✅ [Breadth] 成功更新並存檔: {file_path}")

if __name__ == "__main__":
    update()