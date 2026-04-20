import reflex as rx
import pandas as pd
from datetime import datetime
import importlib
import plotly.graph_objects as go

from data_engine import get_data
import notes

# ============== 🧠 圖表狀態管理大腦 (State) ==============
class ChartState(rx.State):
    selected_range: str = "All"
    
    cat_id: str = ""
    module_name: str = ""
    ticker: str = ""
    display_name: str = ""  # 👈 新增：用來儲存指標的顯示名稱
    
    latest_value: float = 0.0
    change_pct: float = 0.0
    has_data: bool = False
    error_message: str = ""
    note_content: str = ""

    def set_selected_range(self, value: str):
        self.selected_range = value

    @rx.var
    def formatted_change_pct(self) -> str:
        """把數字轉換成帶有正負號的字串"""
        return f"{self.change_pct:+.2f}%"

    # 👇 新增 display_name 參數
    def load_data(self, cat_id: str, module_name: str, ticker: str, display_name: str = ""):
        self.cat_id = cat_id
        self.module_name = module_name
        self.ticker = ticker
        self.display_name = display_name  # 👈 存入大腦
        
        row_data = get_data(cat_id, module_name, ticker)
        if row_data:
            self.latest_value = row_data.get('value', 0)
            self.change_pct = row_data.get('change_pct', 0)
            self.has_data = True
            self.error_message = ""
        else:
            self.has_data = False
            self.error_message = f"無法取得數據！請確認 data/{module_name}.csv 檔案是否存在。"
            
        try:
            self.note_content = notes.fetch_note(cat_id, module_name, ticker)
        except Exception:
            self.note_content = ""
            
        print(f"--- 除錯資訊 ---")
        print(f"正在嘗試載入模組: data_engine.{cat_id}.{module_name}")
        print(f"搜尋 Ticker: {ticker}, 名稱: {display_name}")

    @rx.var
    def filtered_figure(self) -> go.Figure:
        """直接回傳 plotly 原生 Figure 物件"""
        if not self.has_data:
            return go.Figure()
            
        row_data = get_data(self.cat_id, self.module_name, self.ticker)
        if not row_data:
            return go.Figure()
            
        df = row_data.get("history", pd.DataFrame())
        if df.empty or "date" not in df.columns:
            return go.Figure()

        df["date"] = pd.to_datetime(df["date"])
        end = df["date"].max()
        
        if self.selected_range == "All": start = df["date"].min()
        elif self.selected_range == "6m": start = end - pd.DateOffset(months=6)
        elif self.selected_range == "YTD": start = datetime(end.year, 1, 1)
        elif self.selected_range == "1Y": start = end - pd.DateOffset(years=1)
        elif self.selected_range == "3Y": start = end - pd.DateOffset(years=3)
        elif self.selected_range == "5Y": start = end - pd.DateOffset(years=5)
        else: start = end - pd.DateOffset(years=10)

        df_filtered = df[(df["date"] >= start) & (df["date"] <= end)]

        try:
            mod = importlib.import_module(f"data_engine.{self.cat_id}.{self.module_name}")
            # 👇 關鍵修正：把 name 包裝進去傳給繪圖引擎
            item_config = {
                "cat_id": self.cat_id, 
                "module": self.module_name, 
                "ticker": self.ticker,
                "name": self.display_name
            }
            fig = mod.plot_chart(df_filtered, item_config)
            return fig
        except Exception as e:
            print(f"繪圖錯誤: {e}")
            return go.Figure()


# ============== 📊 畫面渲染 (UI) ==============
# 👇 新增 display_name 參數
def render_dynamic_chart(cat_id: str, module_name: str, ticker: str, display_name: str = "") -> rx.Component:
    ranges = ["All", "6m", "YTD", "1Y", "3Y", "5Y", "10Y"]

    return rx.box(
        # 1. 前面放所有的「UI 元件」(沒有名字的位置參數)
        rx.cond(
            ChartState.has_data,
            rx.vstack(
                rx.hstack(
                    rx.text("最新數值: ", color="#9ca3af", size="2"),
                    rx.text(ChartState.latest_value.to_string(), weight="bold", color="white", size="2"),
                    rx.text(" | 漲跌幅: ", color="#9ca3af", size="2"),
                    rx.text(
                        ChartState.formatted_change_pct, 
                        color=rx.cond(ChartState.change_pct >= 0, "#34d399", "#ef4444"),
                        weight="bold", size="2"
                    ),
                    spacing="2",
                    margin_bottom="1rem"
                ),
                rx.divider(border_color="#1f2937", margin_bottom="1rem"),
                rx.hstack(
                    rx.text("時間區間", color="#9ca3af", size="2", padding_top="5px"),
                    rx.radio(
                        items=ranges,
                        value=ChartState.selected_range,
                        on_change=ChartState.set_selected_range,
                        direction="row",
                        spacing="4",
                        color_scheme="blue",
                    ),
                    align="center",
                    margin_bottom="1.5rem"
                ),
                rx.plotly(data=ChartState.filtered_figure, height="400px", width="100%"),
                width="100%"
            ),
            rx.callout(ChartState.error_message, icon="triangle_alert", color_scheme="red")
        ),
        rx.divider(border_color="#1f2937", margin_y="2rem"),
        rx.heading("📝 交易筆記與紀錄", size="4", color="white", margin_bottom="1rem"),
        rx.cond(
            ChartState.note_content != "",
            rx.markdown(ChartState.note_content, color="#d1d5db"),
            rx.text("尚無此指標筆記。", color="#9ca3af", size="2")
        ),
        
        # 2. 最後面放所有的「設定值與事件」(有名字的關鍵字參數)
        # 👇 確保這裡把 display_name 傳給大腦
        on_mount=ChartState.load_data(cat_id, module_name, ticker, display_name),
        width="100%", 
        padding="1rem", 
        bg="#111827", 
        border_radius="12px"
    )