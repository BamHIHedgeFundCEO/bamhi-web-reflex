import reflex as rx

# 匯入我們的設計系統與狀態大腦
from style import BASE_STYLE
from app_state import AppState

# 匯入所有我們做好的模組積木
from components.ui_layout import render_navbar, render_hero_section
from views.macro_market import render_macro_market
from views.trading_tools import render_trading_tools
from views.trading_models import render_trading_models
from views.search_view import render_search_result

# ============== 網頁主結構 (SPA 單頁應用程式) ==============
@rx.page(title="BamHI Quant | 趨勢追蹤器", route="/")
def index() -> rx.Component:
    return rx.box(
        # 1. 頂部導覽列 (永遠固定在上方)
        render_navbar(), 
        
        # 2. 主要內容區 (這就是 SPA 的魔力：根據 State 動態抽換內容，不用重新讀取網頁)
        rx.box(
            rx.match(
                AppState.current_page,
                ("首頁", render_hero_section()),
                ("總經市場", render_macro_market()),
                ("交易工具", render_trading_tools()),
                ("交易模型", render_trading_models()),
                ("搜尋結果", render_search_result()),
                
                # 預設：開發中頁面 (專區、功能教學)
                rx.center(
                    rx.vstack(
                        rx.icon(tag="construction", size=48, color="#fbbf24"),
                        rx.heading(f"🚧 {AppState.current_page}", size="7", color="white"),
                        rx.text("此功能正在開發中...", color="#9ca3af"),
                        align="center"
                    ),
                    padding="10rem"
                )
            ),
            width="100%",
            max_width="1400px", # 限制最大寬度，在大螢幕上會置中
            margin="0 auto"     # 讓內容水平置中
        ),
        
        # 確保全站底色一致，且高度至少填滿螢幕
        min_height="100vh",
        bg="#0f1319"
    )

# ============== 🚀 啟動 Reflex 應用程式 ==============
app = rx.App(
    style=BASE_STYLE,  # 👈 你的 CSS 設計系統直接套用在全站！
    theme=rx.theme(
        appearance="dark", 
        has_background=True, 
        radius="large",
        accent_color="blue"
    )
)