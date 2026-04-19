import reflex as rx
import glob
import re
import os
from components.ai_models import draw_ai_table, AITableState

# ============== 🧠 交易模型頁面狀態大腦 (State) ==============
class TradingModelsState(rx.State):
    available_dates: list[tuple[str, str]] = []
    selected_option: str = "🔥 最新戰報 (Latest)"
    display_date_text: str = "(Latest)"

    def on_load(self):
        self.scan_history_files()
        return self.handle_date_change("🔥 最新戰報 (Latest)")

    def scan_history_files(self):
        history_files = glob.glob("data/BamHI_Dashboard_20*.csv")
        temp_dates = []
        for f in history_files:
            match = re.search(r"(\d{8})", f)
            if match:
                d_str = match.group(1)
                formatted = f"{d_str[:4]}-{d_str[4:6]}-{d_str[6:]}"
                temp_dates.append((formatted, d_str))
        
        sorted_dates = sorted(temp_dates, key=lambda x: x[0], reverse=True)
        self.available_dates = sorted_dates

    @rx.var
    def select_options(self) -> list[str]:
        return ["🔥 最新戰報 (Latest)"] + [f"🕰️ 歷史紀錄: {d[0]}" for d in self.available_dates]

    def handle_date_change(self, value: str):
        self.selected_option = value
        
        if value == "🔥 最新戰報 (Latest)":
            alpha_path = "data/BamHI_Dashboard_Latest.csv"
            genesis_path = "data/BamHI_Genesis_Dashboard_Latest.csv"
            self.display_date_text = "(Latest)"
        else:
            date_str = ""
            for formatted, raw in self.available_dates:
                if f"🕰️ 歷史紀錄: {formatted}" == value:
                    date_str = raw
                    self.display_date_text = formatted
                    break
            
            alpha_path = f"data/BamHI_Dashboard_{date_str}.csv"
            genesis_path = f"data/BamHI_Genesis_Dashboard_{date_str}.csv"

        return [
            AITableState.load_engine_data(alpha_path, "alpha"),
            AITableState.load_engine_data(genesis_path, "genesis")
        ]

# ============== 📊 局部元件 ==============

def feature_importance_bar(label: str, value: int) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(label, size="2", color="#d1d5db"),
            rx.spacer(),
            rx.text(f"{value}%", size="1", color="#9ca3af"),
            width="100%",
        ),
        rx.progress(value=value, color_scheme="blue", width="100%"),
        spacing="1",
        width="100%",
        margin_bottom="0.5rem"
    )

# 👇 新增：我們自己做一個更漂亮的統計卡片，取代被官方刪除的 rx.stat
def render_stat_card(label: str, value: str, value_color: str = "white") -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.text(label, size="2", color="#9ca3af"),
            rx.heading(value, size="6", color=value_color),
            spacing="1"
        ),
        bg="#1f2937", border_color="#374151"
    )

# ============== 🤖 交易模型主頁面 (UI) ==============
def render_trading_models() -> rx.Component:
    return rx.box(
        rx.heading("🤖 BamHI 量化模型庫與每日戰報", size="8", color="white"),
        rx.text("揭開 BamHI 交易決策背後的 AI 大腦，展示雙引擎狙擊名單。", color="#9ca3af", margin_bottom="2rem"),
        
        rx.vstack(
            rx.heading("📅 戰報日期選擇", size="4", color="white", margin_bottom="0.5rem"),
            rx.select(
                TradingModelsState.select_options,
                value=TradingModelsState.selected_option,
                on_change=TradingModelsState.handle_date_change,
                width="300px",
                variant="surface",
            ),
            bg="#111827", padding="1.5rem", border_radius="12px", border="1px solid #1f2937", margin_bottom="2rem"
        ),

        rx.tabs.root(
            rx.tabs.list(
                rx.tabs.trigger("🌊 Alpha 趨勢大腦", value="alpha"),
                rx.tabs.trigger("🌋 Genesis 創世紀大腦", value="genesis"),
                rx.tabs.trigger("📈 歷史回測績效", value="backtest"),
            ),
            
            rx.tabs.content(
                rx.vstack(
                    rx.heading("Alpha 趨勢追蹤模型 (V7.3)", size="5", margin_top="1.5rem"),
                    rx.text("專攻：主升段強勢股。架構：LightGBM + Optuna", color="#9ca3af", size="2"),
                    
                    rx.grid(
                        # 👇 這裡改用我們自製的卡片
                        render_stat_card("歷史驗證 AUC", "0.825", "#34d399"),
                        render_stat_card("模型深度", "4"),
                        render_stat_card("訓練樣本數", "15,000+"),
                        columns="3", spacing="4", width="100%", margin_y="1rem"
                    ),
                    
                    rx.box(
                        rx.text("🧠 核心決策特徵權重", weight="bold", margin_bottom="1rem"),
                        feature_importance_bar("1. RSI 強弱指標", 85),
                        feature_importance_bar("2. 距離 52 週高點比例", 72),
                        feature_importance_bar("3. 相對大盤強度", 68),
                        feature_importance_bar("4. 20MA 未來扣抵推力", 55),
                        bg="#1f2937", padding="1.5rem", border_radius="10px", width="100%"
                    ),
                    
                    rx.divider(margin_y="2rem", border_color="#1f2937"),
                    rx.heading(f"🎯 AI 嚴選名單 🌊 Alpha 引擎 {TradingModelsState.display_date_text}", size="5"),
                    draw_ai_table("alpha"),
                    
                    align_items="start", width="100%"
                ),
                value="alpha",
            ),
            
            rx.tabs.content(
                rx.vstack(
                    rx.heading("Genesis 底部翻轉模型 (V1.0)", size="5", margin_top="1.5rem"),
                    rx.text("專攻：均線糾結、底部帶量突破。", color="#9ca3af", size="2"),
                    
                    rx.grid(
                        render_stat_card("歷史驗證 AUC", "0.798", "#3b82f6"),
                        render_stat_card("均線糾結容忍度", "< 15%"),
                        render_stat_card("底部爆量要求", "Z > 1.5"),
                        columns="3", spacing="4", width="100%", margin_y="1rem"
                    ),
                    
                    rx.box(
                        rx.text("🧠 核心決策特徵權重", weight="bold", margin_bottom="1rem"),
                        feature_importance_bar("1. 均線糾結度", 88),
                        feature_importance_bar("2. 底部爆量 Z-Score", 76),
                        feature_importance_bar("3. 波動率壓縮 (ATR)", 70),
                        feature_importance_bar("4. 上方套牢籌碼比例", 62),
                        bg="#1f2937", padding="1.5rem", border_radius="10px", width="100%"
                    ),

                    rx.divider(margin_y="2rem", border_color="#1f2937"),
                    rx.heading(f"🎯 AI 嚴選名單 🌋 Genesis 引擎 {TradingModelsState.display_date_text}", size="5"),
                    draw_ai_table("genesis"),
                    
                    align_items="start", width="100%"
                ),
                value="genesis",
            ),
            
            rx.tabs.content(
                rx.center(
                    rx.vstack(
                        rx.icon(tag="wrench", size=48, color="#fbbf24"),
                        rx.heading("回測系統建置中", size="5"),
                        rx.text("未來將串接 Equity Curve 與 Sharpe Ratio 等數據。", color="#9ca3af"),
                        padding="4rem", align="center"
                    )
                ),
                value="backtest",
            ),
        ),
        
        on_mount=TradingModelsState.on_load,
        width="100%",
        padding="2rem"
    )