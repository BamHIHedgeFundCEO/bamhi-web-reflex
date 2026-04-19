import reflex as rx
from components.charts import render_dynamic_chart, ChartState

# ============== 🧠 選單對應本地端資料引擎 (Mapping) ==============
# 這個字典依然是我們切換資料流的核心導航圖
UI_TOOLS_MAPPING = {
    "美股板塊強弱": {"cat_id": "market", "module": "strength", "ticker": "ALL", "name": "美股板塊強弱 (Sector Strength)", "id": "SECTOR_STRENGTH"},
    "全球市場強弱": {"cat_id": "market", "module": "world_sectors", "ticker": "WORLD", "name": "龜族全景動能儀表板", "id": "world_sectors"},
}

# ============== 🧠 交易工具專屬狀態大腦 (State) ==============
class TradingToolsState(rx.State):
    """管理交易工具頁面的選單狀態，並負責通知圖表大腦更新資料"""
    
    # 預設選擇第一個工具
    selected_tool: str = "美股板塊強弱"

    # 以下三個是 @rx.var (計算屬性)，它們會根據 selected_tool 自動抓取對應的字典值
    @rx.var
    def current_cat_id(self) -> str:
        return UI_TOOLS_MAPPING[self.selected_tool]["cat_id"]

    @rx.var
    def current_module(self) -> str:
        return UI_TOOLS_MAPPING[self.selected_tool]["module"]

    @rx.var
    def current_ticker(self) -> str:
        return UI_TOOLS_MAPPING[self.selected_tool]["ticker"]

    def handle_tool_change(self, new_tool: str):
        """當使用者點擊 Radio 選單時，會觸發這個函數"""
        # 1. 更新現在選定的工具名稱
        self.selected_tool = new_tool
        
        # 2. 取得新工具的設定參數
        config = UI_TOOLS_MAPPING[new_tool]
        
        # 3. 🎯 狀態聯動：回傳一個 Event，直接命令 ChartState 去載入新資料！
        return ChartState.load_data(config["cat_id"], config["module"], config["ticker"])


# ============== 🛠️ 交易工具分頁 (UI) ==============
def render_trading_tools() -> rx.Component:
    options = list(UI_TOOLS_MAPPING.keys())

    return rx.box(
        rx.heading("🛠️ 交易工具", size="7", color="white", margin_bottom="1rem"),
        
        # 模擬下拉的水平選單 (使用 Radio)
        rx.radio(
            items=options,
            value=TradingToolsState.selected_tool,
            on_change=TradingToolsState.handle_tool_change, # 綁定我們寫好的聯動函數
            direction="row",
            spacing="4",
            color_scheme="blue",
        ),
        
        rx.divider(border_color="#1f2937", margin_y="1.5rem"),
        
        # 動態顯示標題
        rx.heading(
            f"🎯 {TradingToolsState.selected_tool}", 
            size="5", 
            color="white", 
            margin_bottom="1.5rem"
        ),
        
        # 呼叫共用的動態圖表元件，並傳入目前的動態參數
        render_dynamic_chart(
            TradingToolsState.current_cat_id,
            TradingToolsState.current_module,
            TradingToolsState.current_ticker
        ),
        
        # 當整個頁面第一次載入時，強制通知圖表大腦去抓預設工具的資料
        on_mount=ChartState.load_data(
            UI_TOOLS_MAPPING["美股板塊強弱"]["cat_id"],
            UI_TOOLS_MAPPING["美股板塊強弱"]["module"],
            UI_TOOLS_MAPPING["美股板塊強弱"]["ticker"]
        ),
        
        width="100%",
        padding="2rem"
    )