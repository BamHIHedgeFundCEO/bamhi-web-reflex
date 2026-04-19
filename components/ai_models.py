import reflex as rx
import pandas as pd
import os
from datetime import datetime
from functools import lru_cache

# ============== 🧠 效能優化：後端資料快取 ==============
# 這完美取代了 @st.cache_data，讓伺服器讀取 CSV 的速度極大化
@lru_cache(maxsize=10)
def fetch_cached_dataframe(csv_path: str, modified_time: float) -> pd.DataFrame:
    """
    傳入 modified_time 作為參數，當檔案被 GitHub Actions 更新時，
    modified_time 會改變，快取就會自動失效並重新讀取！
    """
    return pd.read_csv(csv_path)

# ============== 🧠 表格狀態管理大腦 (State) ==============
class AITableState(rx.State):
    """管理 Alpha 與 Genesis 引擎表格資料的狀態"""
    
    # 儲存處理過後的二維陣列資料，供前端表格渲染
    alpha_data: list[list[str]] = []
    alpha_cols: list[str] = []
    alpha_last_update: str = ""
    
    genesis_data: list[list[str]] = []
    genesis_cols: list[str] = []
    genesis_last_update: str = ""

    def load_engine_data(self, csv_path: str, engine_type: str):
        """讀取 CSV 並在後端完成所有格式化，減輕前端負擔"""
        if not os.path.exists(csv_path):
            return

        # 取得檔案最後修改時間，並呼叫快取函數
        mtime = os.path.getmtime(csv_path)
        updated_time = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        df = fetch_cached_dataframe(csv_path, mtime)
        
        # 複製一份來做格式化處理，避免污染原始快取
        df_display = df.copy()

        if 'Win_Prob' in df_display.columns: 
            df_display['Win_Prob'] = df_display['Win_Prob'] * 100

        # === Alpha 引擎格式化 ===
        if engine_type == "alpha":
            cols = ['Ticker', 'Resonance_Score', 'Win_Prob', 'Price', 'RS_Rating', 'Ov_Supply', 'POC_Dist', 'MA20_DP', 'Vol_Dry_Up', 'Turtle']
            cols = [c for c in cols if c in df_display.columns]
            df_display = df_display[cols]
            
            # 使用 Pandas 向量化處理，效能極高
            if 'Resonance_Score' in df_display: df_display['Resonance_Score'] = df_display['Resonance_Score'].apply(lambda x: f"🔥 {x:.1f}")
            if 'Win_Prob' in df_display: df_display['Win_Prob'] = df_display['Win_Prob'].apply(lambda x: f"🤖 {x:.1f}%")
            if 'Price' in df_display: df_display['Price'] = df_display['Price'].apply(lambda x: f"${x:.2f}")
            if 'RS_Rating' in df_display: df_display['RS_Rating'] = df_display['RS_Rating'].apply(lambda x: f"{x:.0f}")
            if 'Ov_Supply' in df_display: df_display['Ov_Supply'] = df_display['Ov_Supply'].apply(lambda x: f"{x:.1f}%")
            if 'POC_Dist' in df_display: df_display['POC_Dist'] = df_display['POC_Dist'].apply(lambda x: f"{x:.1f}%")
            
            self.alpha_cols = cols
            self.alpha_data = df_display.astype(str).values.tolist()
            self.alpha_last_update = updated_time

        # === Genesis 引擎格式化 ===
        elif engine_type == "genesis":
            cols = ['Ticker', 'Resonance_Score', 'Win_Prob', 'Price', 'MA_Conv', 'Vol_Z', 'Breakout', 'MA20_Slope', 'Ov_Supply', 'POC_Dist']
            cols = [c for c in cols if c in df_display.columns]
            df_display = df_display[cols]
            
            if 'Resonance_Score' in df_display: df_display['Resonance_Score'] = df_display['Resonance_Score'].apply(lambda x: f"⚡ {x:.1f}")
            if 'Win_Prob' in df_display: df_display['Win_Prob'] = df_display['Win_Prob'].apply(lambda x: f"🤖 {x:.1f}%")
            if 'Price' in df_display: df_display['Price'] = df_display['Price'].apply(lambda x: f"${x:.2f}")
            if 'MA_Conv' in df_display: df_display['MA_Conv'] = df_display['MA_Conv'].apply(lambda x: f"{x:.2f}%")
            if 'Vol_Z' in df_display: df_display['Vol_Z'] = df_display['Vol_Z'].apply(lambda x: f"{x:.2f}")
            if 'Breakout' in df_display: df_display['Breakout'] = df_display['Breakout'].apply(lambda x: f"{x:.1f}%")
            if 'MA20_Slope' in df_display: df_display['MA20_Slope'] = df_display['MA20_Slope'].apply(lambda x: f"{x:.2f}%")
            if 'Ov_Supply' in df_display: df_display['Ov_Supply'] = df_display['Ov_Supply'].apply(lambda x: f"{x:.1f}%")
            if 'POC_Dist' in df_display: df_display['POC_Dist'] = df_display['POC_Dist'].apply(lambda x: f"{x:.1f}%")

            self.genesis_cols = cols
            self.genesis_data = df_display.astype(str).values.tolist()
            self.genesis_last_update = updated_time


# ============== 📊 畫面渲染 (UI) ==============
def draw_ai_table(engine_type: str) -> rx.Component:
    """
    動態渲染 AI 表格。
    注意：在 Reflex 中，元件渲染時無法帶入動態路徑（如 csv_path），
    必須由呼叫它的母頁面（例如 trading_models.py）去觸發 load_engine_data。
    """
    
    # 根據引擎類型，自動綁定對應的 State 變數
    if engine_type == "alpha":
        data_source = AITableState.alpha_data
        columns_source = AITableState.alpha_cols
        update_time = AITableState.alpha_last_update
    else:
        data_source = AITableState.genesis_data
        columns_source = AITableState.genesis_cols
        update_time = AITableState.genesis_last_update

    return rx.box(
        rx.cond(
            data_source.length() > 0,
            # 如果有資料，顯示高階資料表
            rx.vstack(
                rx.data_table(
                    data=data_source,
                    columns=columns_source,
                    pagination=True,  # 內建分頁
                    search=True,      # 內建搜尋框！
                    sort=True,        # 點擊表頭即可排序！
                    style={
                        "background_color": "#111827",
                        "color": "#e5e7eb",
                        "border_radius": "8px",
                    }
                ),
                rx.text(f"🔄 最後更新：{update_time}", color="#9ca3af", size="2", margin_top="10px"),
                width="100%"
            ),
            # 如果沒有資料，顯示等待提示
            rx.callout(
                "⏳ 該引擎資料尚未產生或同步中...",
                icon="info",
                color_scheme="blue",
            )
        ),
        width="100%"
    )