import reflex as rx
from components.charts import render_dynamic_chart, ChartState

# ============== 🧠 選單對應本地端資料引擎 (Mapping) ==============
UI_TOOLS_MAPPING = {
    "美股板塊強弱": {"cat_id": "market", "module": "strength", "ticker": "ALL", "name": "美股板塊強弱 (Sector Strength)", "id": "SECTOR_STRENGTH"},
    "全球市場強弱": {"cat_id": "market", "module": "world_sectors", "ticker": "WORLD", "name": "龜族全景動能儀表板", "id": "world_sectors"},
}

# ============== 🧠 交易工具專屬狀態大腦 (State) ==============
class TradingToolsState(rx.State):
    """管理交易工具頁面的選單狀態，並負責通知圖表大腦更新資料"""
    
    selected_tool: str = "美股板塊強弱"

    @rx.var
    def current_cat_id(self) -> str:
        return UI_TOOLS_MAPPING[self.selected_tool]["cat_id"]

    @rx.var
    def current_module(self) -> str:
        return UI_TOOLS_MAPPING[self.selected_tool]["module"]

    @rx.var
    def current_ticker(self) -> str:
        return UI_TOOLS_MAPPING[self.selected_tool]["ticker"]

    # 👇 1. 新增：抓取顯示名稱供 UI 使用
    @rx.var
    def current_name(self) -> str:
        return UI_TOOLS_MAPPING[self.selected_tool]["name"]

    def handle_tool_change(self, new_tool: str):
        """當使用者點擊 Radio 選單時觸發"""
        self.selected_tool = new_tool
        config = UI_TOOLS_MAPPING[new_tool]
        
        # 🎯 狀態聯動：直接命令 ChartState 去載入新資料
        # 👇 2. 補上 config["name"]，這樣圖表引擎才不會報 KeyError
        return ChartState.load_data(config["cat_id"], config["module"], config["ticker"], config["name"])


# ============== 🛠️ 交易工具分頁 (UI) ==============
def render_trading_tools() -> rx.Component:
    options = list(UI_TOOLS_MAPPING.keys())

    return rx.box(
        rx.heading("🛠️ 交易工具", size="7", color="white", margin_bottom="1rem"),
        
        # 模擬下拉的水平選單 (使用 Radio)
        rx.radio(
            items=options,
            value=TradingToolsState.selected_tool,
            on_change=TradingToolsState.handle_tool_change,
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
        
        # 呼叫共用的動態圖表元件
        render_dynamic_chart(
            TradingToolsState.current_cat_id,
            TradingToolsState.current_module,
            TradingToolsState.current_ticker,
            TradingToolsState.current_name # 👇 3. 補上傳遞名稱參數
        ),
        
        # 當頁面第一次載入時，強制通知圖表大腦抓取預設資料
        on_mount=ChartState.load_data(
            UI_TOOLS_MAPPING["美股板塊強弱"]["cat_id"],
            UI_TOOLS_MAPPING["美股板塊強弱"]["module"],
            UI_TOOLS_MAPPING["美股板塊強弱"]["ticker"],
            UI_TOOLS_MAPPING["美股板塊強弱"]["name"] # 👇 4. 預設載入時也補上名稱
        ),
        
        width="100%",
        padding="2rem"
    )