"""
data_engine 動態路由器 + 通用 CSV 讀取器
"""
import importlib
import pandas as pd
import os
import streamlit as st

# 🔥 [新增功能] 通用讀取器：負責去 data 資料夾拿便當
def load_csv(filename):
    path = f"data/{filename}"
    
    # 如果找不到檔案（便當還沒做），就回傳 None
    if not os.path.exists(path):
        return None
        
    try:
        df = pd.read_csv(path)
        # 自動把 date 欄位轉成時間格式，畫圖才不會錯
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
        return df
    except Exception as e:
        print(f"讀取 CSV 失敗: {e}")
        return None

# (原本的路由器邏輯，保持不變)
def get_data(category: str, module_name: str, ticker: str):
    if not module_name: return None
    try:
        mod = importlib.import_module(f"data_engine.{category}.{module_name}")
        return mod.fetch_data(ticker)
    except Exception as e:
        print(f"⚠️ 無法載入 data_engine.{category}.{module_name}: {e}")
        return None