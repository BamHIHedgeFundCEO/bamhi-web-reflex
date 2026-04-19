import reflex as rx
from app_state import AppState
from views.search_view import SearchViewState

# ============== 🧭 頂部導覽列 (Navbar) ==============
def render_navbar() -> rx.Component:
    nav_items = [
        {"name": "首頁", "icon": "home"},
        {"name": "總經市場", "icon": "activity"},
        {"name": "交易工具", "icon": "wrench"},
        {"name": "交易模型", "icon": "cpu"},
        {"name": "專區", "icon": "star"},
        {"name": "功能教學", "icon": "book"},
    ]

    return rx.hstack(
        # 左側：Logo
        rx.heading("🌌 BamHI Quant", size="6", color="#3b82f6", weight="bold"),
        
        # 中間：選單
        rx.hstack(
            *[
                rx.button(
                    rx.icon(tag=item["icon"], size=16, color="#9ca3af"),
                    rx.text(item["name"], size="2", color="#d1d5db"),
                    variant="ghost",
                    on_click=AppState.navigate_to(item["name"]),
                    _hover={"bg": "#1f2937", "color": "white"},
                    padding="10px",
                )
                for item in nav_items
            ],
            spacing="2",
            # 👇 修改點 1：Navbar 響應式隱藏
            display={"initial": "none", "md": "flex"},
        ),

        # 右側：搜尋框
        rx.box(
            rx.form(
                rx.input(
                    name="search_input",
                    placeholder="🔍 搜尋美股代碼...",
                    variant="surface",
                    radius="full",
                    style={
                        "background_color": "#1f2937",
                        "border_color": "#374151",
                        "color": "white",
                        "width": "200px"
                    }
                ),
                on_submit=[AppState.handle_search_form, SearchViewState.handle_search],
                reset_on_submit=True,
            )
        ),
        justify="between",
        align="center",
        width="100%",
        padding_x="2rem",
        padding_y="1rem",
        border_bottom="1px solid #1f2937",
        bg="#0f1319",
    )


# ============== 🏠 封面區塊 (Hero Section) ==============
def render_hero_section() -> rx.Component:
    return rx.flex(
        # === 左側：文案區 (佔比較大) ===
        rx.vstack(
            rx.badge("▲ BAMHI QUANT 趨勢追蹤器", bg="#064e3b", color="#34d399", padding="4px 10px", radius="full"),
            rx.heading("更早看懂市場，", size="9", color="white", weight="bold", line_height="1.1"),
            rx.heading("少走研究彎路", size="9", color="#9ca3af", weight="bold", line_height="1.1", margin_bottom="1rem"),
            
            rx.text(
                "BamHI Quant 把全市場掃描、板塊輪動、趨勢雷達、回測驗證、機構與內部人追蹤，整合出一套每天可以直接執行的研究工作流。",
                color="#9ca3af", size="4", line_height="1.6", max_width="600px"
            ),
            rx.text(
                "重視資訊量，而且想更快找到值得研究的標的與時機，BamHI 是最貼近你需求的工具。新『專區』功能也會持續更新研究當下的原始紀錄與 AI 工作流，不只給你最後結論。",
                color="#9ca3af", size="4", line_height="1.6", max_width="600px", margin_bottom="1.5rem"
            ),
            
            rx.hstack(
                rx.button("🚀 開始 7 天免費試用", bg="#10b981", color="white", _hover={"bg": "#059669"}, size="3", radius="large"),
                rx.button("👤 登入 / 建立帳號", bg="#1f2937", color="white", border="1px solid #374151", _hover={"bg": "#374151"}, size="3", radius="large"),
                rx.button("📖 查看 10 大功能", bg="#1f2937", color="white", border="1px solid #374151", _hover={"bg": "#374151"}, size="3", radius="large"),
                spacing="4",
                wrap="wrap"
            ),
            
            rx.text("⚡ 試用期間全功能開放，包含會員專區與 AI 工作流相關內容。", color="#fbbf24", size="2", margin_top="1rem"),
            
            align_items="start",
            spacing="4",
            # 👇 修改點 2：左側文案區寬度
            width={"initial": "100%", "md": "55%"},
        ),

        # === 右側：Bento 卡片區 ===
        rx.box(
            rx.badge("會員專區亮點", bg="#064e3b", color="#34d399", padding="4px 10px", radius="full", margin_bottom="10px"),
            rx.heading("會員專區 + AI 工作流，\n讓你更早看到研究過程", size="6", color="white", margin_bottom="10px", white_space="pre-line"),
            rx.text("不只看整理後結論，而是更早看到我如何追蹤題材、整理資料、記錄部位與持續追蹤。", color="#9ca3af", size="2", margin_bottom="20px"),
            
            rx.vstack(
                _feature_item("第一手研究紀錄", "交易想法、部位變化與事件追蹤，持續更新在專區。"),
                _feature_item("AI 工作流拆解", "直接看到我如何用 AI 協助研究、整理資料與建立觀察名單。"),
                _feature_item("從想法到執行一條龍", "先用工具找機會，再回到專區持續跟進，讓研究能一路追蹤下去。"),
                spacing="3",
                width="100%",
            ),
            
            bg="#111827",
            border="1px solid #1f2937",
            border_radius="16px",
            padding="2rem",
            # 👇 修改點 3：右側卡片區寬度
            width={"initial": "100%", "md": "45%"},
            box_shadow="0 25px 50px -12px rgba(0, 0, 0, 0.25)",
        ),

        # 👇 修改點 4：手機直排、電腦橫排 (這就是引發報錯的那行)
        direction={"initial": "column", "md": "row"},
        
        spacing="7",
        width="100%",
        max_width="1200px",
        margin="0 auto",
        padding_top="4rem",
        padding_x="2rem",
    )

def _feature_item(title: str, desc: str) -> rx.Component:
    return rx.box(
        rx.text(title, weight="bold", color="white", size="2"),
        rx.text(desc, color="#9ca3af", size="1", margin_top="4px"),
        bg="#1f2937",
        padding="15px",
        border_radius="10px",
        width="100%"
    )