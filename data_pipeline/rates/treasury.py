"""
data_pipeline/rates/treasury.py
負責抓取美國公債利率 (FRED) -> 存成 data/rates.csv
"""
import pandas_datareader.data as web
import datetime as dt
import pandas as pd
import os

def update():
    print("   ↳ 📉 [Treasury] 正在下載公債殖利率...")
    start = dt.datetime(1980, 1, 1)
    end = dt.datetime.now()
    
    try:
        df = web.DataReader(["DGS10", "DGS2"], "fred", start, end)
        df["Spread"] = df["DGS10"] - df["DGS2"]
        df = df.dropna().reset_index()
        df.rename(columns={"DATE": "date"}, inplace=True)
        
        if not os.path.exists("data"): os.makedirs("data")
        
        df.to_csv("data/rates.csv", index=False)
        print("   ✅ [Treasury] 儲存成功 data/rates.csv")
    except Exception as e:
        print(f"   ❌ [Treasury] 失敗: {e}")