import reflex as rx
from components.charts import render_dynamic_chart, ChartState

# ============== 🧠 選單對應本地端資料引擎 (Mapping) ==============
UI_MACRO_MAPPING = {
    "10年期美債殖利率": {"cat_id": "rates", "module": "treasury", "ticker": "DGS10", "name": "10 Years Yield", "id": "DGS10"},
    "2年期美債殖利率": {"cat_id": "rates", "module": "treasury", "ticker": "DGS2", "name": "2 Years Yield", "id": "DGS2"},
    "10-2 spread": {"cat_id": "rates", "module": "treasury", "ticker": "SPREAD_10_2", "name": "10-2 Spread", "id": "SPREAD_10_2"},
    "市場寬度": {"cat_id": "market", "module": "breadth", "ticker": "SP500_BREADTH", "name": "S&P 500 市場寬度", "id": "BREADTH_SP500"},
    "情緒方向": {"cat_id": "market", "module": "naaim", "ticker": "NAAIM_AAII", "name": "散戶 & 機構情緒方向", "id": "SENTIMENT_COMBO"},
}

# ============== 🧠 總經市場專屬狀態大腦 (State) ==============
class MacroMarketState(rx.State):
    """管理總經市場頁面的選單狀態，並負責通知圖表大腦更新資料"""
    
    # 預設選擇第一個指標
    selected_indicator: str = "10年期美債殖利率"

    @rx.var
    def current_cat_id(self) -> str:
        return UI_MACRO_MAPPING[self.selected_indicator]["cat_id"]

    @rx.var
    def current_module(self) -> str:
        return UI_MACRO_MAPPING[self.selected_indicator]["module"]

    @rx.var
    def current_ticker(self) -> str:
        return UI_MACRO_MAPPING[self.selected_indicator]["ticker"]

    def handle_indicator_change(self, new_indicator: str):
        """當使用者點擊 Radio 選單時觸發"""
        self.selected_indicator = new_indicator
        config = UI_MACRO_MAPPING[new_indicator]
        
        # 🎯 狀態聯動：直接命令 ChartState 去載入新資料
        return ChartState.load_data(config["cat_id"], config["module"], config["ticker"])


# ============== 🏠 總經市場分頁 (UI) ==============
def render_macro_market() -> rx.Component:
    options = list(UI_MACRO_MAPPING.keys())

    return rx.box(
        rx.heading("📊 總經市場指標", size="7", color="white", margin_bottom="1rem"),
        
        # 模擬下拉的水平選單 (Radio Group)
        rx.radio(
            items=options,
            value=MacroMarketState.selected_indicator,
            on_change=MacroMarketState.handle_indicator_change,
            direction="row",
            spacing="4",
            color_scheme="blue",
        ),
        
        rx.divider(border_color="#1f2937", margin_y="1.5rem"),
        
        # 動態顯示標題
        rx.heading(
            f"📉 {MacroMarketState.selected_indicator}", 
            size="5", 
            color="white", 
            margin_bottom="1.5rem"
        ),
        
        # 呼叫共用的動態圖表元件
        render_dynamic_chart(
            MacroMarketState.current_cat_id,
            MacroMarketState.current_module,
            MacroMarketState.current_ticker
        ),
        
        # 當頁面第一次載入時，強制通知圖表大腦抓取預設資料
        on_mount=ChartState.load_data(
            UI_MACRO_MAPPING["10年期美債殖利率"]["cat_id"],
            UI_MACRO_MAPPING["10年期美債殖利率"]["module"],
            UI_MACRO_MAPPING["10年期美債殖利率"]["ticker"]
        ),
        
        width="100%",
        padding="2rem"
    )
