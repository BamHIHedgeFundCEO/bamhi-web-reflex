import reflex as rx
import pandas as pd
from deep_translator import GoogleTranslator
import json
import plotly.graph_objects as go
import plotly.io as pio
from app_state import AppState
# 假設這些是你原本的模組
import data_engine.equity as equity_engine

# ==========================================
# 🧠 股票深度搜尋狀態大腦 (State)
# ==========================================
class SearchViewState(rx.State):
    """管理深度搜尋頁面的所有狀態與資料處理"""
    
    # --- 搜尋與控制參數 ---
    ticker: str = ""
    period_opt: str = "2y"
    interval_opt: str = "1d"
    
    # --- UI 狀態 ---
    is_loading: bool = False
    has_error: bool = False
    error_message: str = ""
    
    # --- 基本報價與資訊 ---
    company_name: str = ""
    current_price: float = 0.0
    change: float = 0.0
    change_pct: float = 0.0
    market_cap_str: str = "N/A"
    pe_ratio_str: str = "N/A"
    pb_ratio_str: str = "N/A"
    roe_str: str = "N/A"
    sector: str = "N/A"
    industry: str = "N/A"
    employees: str = "N/A"
    business_summary: str = "暫無公司業務介紹。"
    translated_summary: str = ""
    is_translating: bool = False
    info_source: str = "Yahoo Finance"
    
    # --- 技術線圖狀態 ---
    chart_figure: go.Figure = go.Figure()
    has_chart: bool = False
    trend_status: str = "分析中..."
    status_emoji: str = "⚪ 觀望持有"
    last_score: float = 0.0
    
    # --- 財報狀態 ---
    finance_source: str = ""
    gross_margin_str: str = "N/A"
    yoy_str: str = "N/A"
    net_margin_str: str = "N/A"
    eps_str: str = "N/A"
    finance_data: list[list[str]] = []
    finance_cols: list[str] = []

    @rx.var
    def formatted_change(self) -> str:
        """格式化漲跌幅字串，加入正負號"""
        return f"{self.change:+.2f} ({self.change_pct:+.2f}%)"

# 👇 把原本的 (self, query: str) 改成收字典 (self, form_data: dict)
    def handle_search(self, form_data: dict):
        """當 Navbar 傳來搜尋表單請求時觸發"""
        # 從字典裡面把使用者輸入的字串抓出來
        query = form_data.get("search_input", "").strip()
        
        if not query:
            return
            
        self.ticker = query.upper()
        self.is_loading = True
        self.has_error = False
        return SearchViewState.fetch_stock_data
        
    def handle_period_change(self, value: str):
        self.period_opt = value
        # 防呆機制
        if self.interval_opt == "1h" and value in ["5y", "10y", "max"]:
            self.period_opt = "2y"
        return SearchViewState.fetch_stock_data

    def handle_interval_change(self, value: str):
        self.interval_opt = value
        # 防呆機制
        if value == "1h" and self.period_opt in ["5y", "10y", "max"]:
            self.period_opt = "2y"
        return SearchViewState.fetch_stock_data

    def fetch_stock_data(self):
        """執行全網掃描與資料處理 (這部分會在後端非同步執行)"""
        try:
            data = equity_engine.fetch_stock_profile(self.ticker, period=self.period_opt, interval=self.interval_opt)
            
            if not data:
                self.has_error = True
                self.error_message = f"⚠️ 找不到代碼 {self.ticker}，請確認輸入是否正確。"
                self.is_loading = False
                return

            info = data.get("info", {})
            hist = data.get("history", pd.DataFrame())

            # --- 1. 基本報價 ---
            self.current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            prev_close = info.get('previousClose', self.current_price)
            self.change = self.current_price - prev_close
            self.change_pct = (self.change / prev_close * 100) if prev_close else 0
            self.company_name = info.get('shortName', info.get('longName', self.ticker))

            # --- 2. 核心指標四宮格 ---
            pe = info.get('trailingPE', 'N/A')
            self.pe_ratio_str = f"{pe:.2f}" if isinstance(pe, (int, float)) else str(pe)
            
            pb = info.get('priceToBook', 'N/A')
            self.pb_ratio_str = f"{pb:.2f}" if isinstance(pb, (int, float)) else str(pb)
            
            mc = info.get('marketCap', 0)
            self.market_cap_str = f"${mc / 1e9:.2f} B" if mc else "N/A"
            
            roe = info.get('returnOnEquity', 0)
            self.roe_str = f"{roe * 100:.2f}%" if roe else "N/A"

            # --- 3. 公司簡介 ---
            self.sector = info.get('sector', 'N/A')
            self.industry = info.get('industry', 'N/A')
            emp = info.get('fullTimeEmployees')
            self.employees = f"{emp:,}" if isinstance(emp, (int, float)) else "N/A"
            
            raw_summary = info.get('longBusinessSummary', '暫無公司業務介紹。')
            self.business_summary = raw_summary
            self.translated_summary = raw_summary # 先顯示原文，稍後再翻譯
            
            is_tw = "台灣" in str(self.sector) or "TWSE" in str(self.sector)
            self.info_source = "FMP (Financial Modeling Prep)" if is_tw else "Yahoo Finance"

            # --- 4. 技術線圖與趨勢 ---
            if not hist.empty:
                # 趨勢與分數
                if 'Composite' in hist.columns:
                    self.last_score = hist['Composite'].iloc[-1]
                    ma20 = hist['MA_20'].iloc[-1] if 'MA_20' in hist.columns else 0
                    ma60 = hist['MA_60'].iloc[-1] if 'MA_60' in hist.columns else 0
                    ma120 = hist['MA_120'].iloc[-1] if 'MA_120' in hist.columns else 0
                    
                    if ma20 > ma60 > ma120: self.trend_status = "多頭 🐂 (均線發散)"
                    elif ma20 < ma60 < ma120: self.trend_status = "空頭 🐻 (均線蓋頭)"
                    else: self.trend_status = "盤整震盪 ⚖️ (均線糾結)"
                    
                    if self.last_score > 75: self.status_emoji = "🔴 過熱警示 (賣訊)"
                    elif self.last_score < 25: self.status_emoji = "🟢 超跌機會 (買訊)"
                    else: self.status_emoji = "⚪ 觀望持有"
                
                # 產生 Plotly 圖表
                fig = equity_engine.plot_candlestick(hist, self.ticker, interval=self.interval_opt)
                if fig:
                    self.chart_figure = fig
                    self.has_chart = True
                else:
                    self.chart_figure = go.Figure()
                    self.has_chart = False

            # --- 5. 財務報表處理 ---
            self.finance_source = data.get("finance_source", "")
            is_twse = self.sector == '台灣市場 (TWSE)'
            currency = "NT$" if is_twse else "$"
            divisor = 1000 if is_twse else 1000000 
            
            df_fin = data.get("income_stmt", pd.DataFrame())
            
            if not df_fin.empty:
                latest_col = df_fin.columns[0]
                
                def get_val(r_name):
                    if r_name in df_fin.index:
                        v = df_fin.at[r_name, latest_col]
                        if pd.notna(v) and v is not None: return float(v)
                    return None
                
                gm = get_val('毛利率 (Gross Margin)')
                yoy = get_val('營收年增率 (YoY)')
                nm = get_val('淨利率 (Net Margin)')
                eps = get_val('單季 EPS')
                
                self.gross_margin_str = f"{gm*100:.2f}%" if gm is not None else "N/A"
                self.yoy_str = f"{yoy*100:.2f}%" if yoy is not None else "N/A"
                self.net_margin_str = f"{nm*100:.2f}%" if nm is not None else "N/A"
                self.eps_str = f"{currency} {eps:.2f}" if eps is not None else "N/A"

                # 格式化表格供前端顯示
                df_display = df_fin.copy()
                for col in df_display.columns:
                    for row in ['營收 (Revenue)', '營運現金流 (Operating CF)', '自由現金流 (Free CF)']:
                        if row in df_display.index:
                            v = df_display.at[row, col]
                            df_display.at[row, col] = f"{currency} {float(v) / divisor:,.1f} M" if pd.notna(v) and v is not None else "N/A"
                            
                    for row in ['營收年增率 (YoY)', '毛利率 (Gross Margin)', '淨利率 (Net Margin)']:
                        if row in df_display.index:
                            v = df_display.at[row, col]
                            df_display.at[row, col] = f"{float(v) * 100:.2f} %" if pd.notna(v) and v is not None else "N/A"
                            
                    if '單季 EPS' in df_display.index:
                        v = df_display.at['單季 EPS', col]
                        df_display.at['單季 EPS', col] = f"{currency} {float(v):.2f}" if pd.notna(v) and v is not None else "N/A"
                
                # 把 index 變成一個欄位，供 Reflex 表格顯示
                df_display.insert(0, "項目", df_display.index)
                self.finance_cols = list(df_display.columns)
                self.finance_data = df_display.astype(str).values.tolist()
            else:
                self.finance_data = []

            # 結束 Loading
            self.is_loading = False
            
            # 觸發背景翻譯
            if self.business_summary != '暫無公司業務介紹。':
                return SearchViewState.translate_summary

        except Exception as e:
            print(f"Error fetching data: {e}")
            self.has_error = True
            self.error_message = f"系統發生錯誤：{str(e)}"
            self.is_loading = False

    async def translate_summary(self):
        """非同步執行 Google 翻譯，避免卡住主線程"""
        self.is_translating = True
        try:
            self.translated_summary = GoogleTranslator(source='auto', target='zh-TW').translate(self.business_summary)
        except Exception:
            self.translated_summary = f"{self.business_summary}\n\n*(翻譯伺服器暫時忙碌，顯示原文)*"
        self.is_translating = False

# ==========================================
# 📊 局部元件 (UI Components)
# ==========================================
def render_metric_card(title: str, value: str) -> rx.Component:
    return rx.card(
        rx.text(title, size="2", color="#9ca3af"),
        rx.heading(value, size="5", color="white"),
        bg="#1f2937", border_color="#374151"
    )

# ==========================================
# 🔍 搜尋結果主頁面 (UI)
# ==========================================
def render_search_result() -> rx.Component:
    return rx.box(
        # 修改這一行
        rx.button("← 結束搜尋，返回首頁", on_click=AppState.clear_search, variant="ghost", color="#9ca3af", margin_bottom="1rem"),
        
        # 載入中狀態
        rx.cond(
            SearchViewState.is_loading,
            rx.center(rx.spinner(size="3"), rx.text(f"正在全網掃描 {SearchViewState.ticker} 的深度數據...", margin_left="10px"), padding="3rem"),
            
            # 載入完成後的畫面
            rx.cond(
                SearchViewState.has_error,
                rx.callout(SearchViewState.error_message, icon="triangle_alert", color_scheme="red"),
                
                rx.vstack(
                    # --- 頂部參數設定 ---
                    rx.heading("⚙️ 圖表參數設定", size="4", color="white", margin_bottom="0.5rem"),
                    rx.hstack(
                        rx.select(
                            ["6mo", "1y", "2y", "5y", "10y", "max"],
                            value=SearchViewState.period_opt,
                            on_change=SearchViewState.handle_period_change,
                            placeholder="📅 歷史區間"
                        ),
                        rx.select(
                            ["1h", "1d", "1wk"],
                            value=SearchViewState.interval_opt,
                            on_change=SearchViewState.handle_interval_change,
                            placeholder="⏱️ K線級別"
                        ),
                        spacing="4"
                    ),
                    rx.divider(margin_y="1.5rem", border_color="#1f2937"),
                    
                    # --- 標題與價格區塊 ---
                    rx.heading(f"{SearchViewState.company_name} ({SearchViewState.ticker})", size="8", color="white"),
                    rx.hstack(
                        rx.heading(f"${SearchViewState.current_price:.2f}", size="9", color=rx.cond(SearchViewState.change >= 0, "#34d399", "#ef4444")),
                        rx.text(
                            SearchViewState.formatted_change,
                            weight="bold", size="5",
                            color=rx.cond(SearchViewState.change >= 0, "#34d399", "#ef4444")
                        ),
                        align="baseline", spacing="4", margin_bottom="1.5rem"
                    ),
                    
                    # --- 四宮格 ---
                    rx.grid(
                        render_metric_card("總市值", SearchViewState.market_cap_str),
                        render_metric_card("本益比 (P/E)", SearchViewState.pe_ratio_str),
                        render_metric_card("股價淨值比 (P/B)", SearchViewState.pb_ratio_str),
                        render_metric_card("ROE", SearchViewState.roe_str),
                        columns="4", spacing="4", width="100%", margin_bottom="2rem"
                    ),
                    
                    # --- 深度分析 Tabs ---
                    rx.tabs.root(
                        rx.tabs.list(
                            rx.tabs.trigger("📈 技術線圖", value="chart"),
                            rx.tabs.trigger("🏢 基本資料", value="info"),
                            rx.tabs.trigger("📊 財務報表", value="finance"),
                            rx.tabs.trigger("🤖 進階交易", value="quant"),
                        ),
                        
                        # Tab 1: 技術線圖
                        rx.tabs.content(
                            rx.vstack(
                                rx.hstack(
                                    rx.callout(f"趨勢狀態: {SearchViewState.trend_status}", icon="trending_up", color_scheme="blue", width="100%"),
                                    rx.callout(f"量化訊號: {SearchViewState.status_emoji} (分數: {SearchViewState.last_score:.1f})", icon="activity", color_scheme="purple", width="100%"),
                                    spacing="4", width="100%", margin_y="1rem"
                                ),
                                rx.cond(
                                    SearchViewState.has_chart,
                                    rx.plotly(data=SearchViewState.chart_figure, height="600px", width="100%"),
                                    rx.text("暫無歷史價格數據。", color="#9ca3af")
                                ),
                                width="100%"
                            ),
                            value="chart"
                        ),
                        
                        # Tab 2: 基本資料
                        rx.tabs.content(
                            rx.grid(
                                rx.box(
                                    rx.text("所屬板塊 (Sector)", size="1", color="#9ca3af"),
                                    rx.text(SearchViewState.sector, size="4", weight="bold", color="white", margin_bottom="1rem"),
                                    rx.text("所屬產業 (Industry)", size="1", color="#9ca3af"),
                                    rx.text(SearchViewState.industry, size="4", weight="bold", color="white", margin_bottom="1rem"),
                                    rx.text("全職員工數", size="1", color="#9ca3af"),
                                    rx.text(SearchViewState.employees, size="4", weight="bold", color="white"),
                                    bg="#111827", padding="1.5rem", border_radius="12px", border="1px solid #1f2937"
                                ),
                                rx.box(
                                    rx.cond(
                                        SearchViewState.is_translating,
                                        rx.text("🤖 正在將公司簡介翻譯為繁體中文...", color="#3b82f6"),
                                        rx.markdown(SearchViewState.translated_summary, color="#d1d5db")
                                    ),
                                    rx.text(f"💡 來源: {SearchViewState.info_source} | 翻譯: Google", size="1", color="#6b7280", margin_top="1rem"),
                                    bg="#1f2937", padding="1.5rem", border_radius="12px"
                                ),
                                columns="2", spacing="4", margin_top="1.5rem"
                            ),
                            value="info"
                        ),
                        
                        # Tab 3: 財務報表
                        rx.tabs.content(
                            rx.vstack(
                                rx.hstack(
                                    rx.heading("關鍵財務數據", size="5", color="white"),
                                    rx.badge(f"來源: {SearchViewState.finance_source}", color_scheme="gray"),
                                    align="center", spacing="4", margin_top="1.5rem", margin_bottom="1rem"
                                ),
                                rx.grid(
                                    render_metric_card("毛利率", SearchViewState.gross_margin_str),
                                    render_metric_card("營收 YoY", SearchViewState.yoy_str),
                                    render_metric_card("淨利率", SearchViewState.net_margin_str),
                                    render_metric_card("單季 EPS", SearchViewState.eps_str),
                                    columns="4", spacing="4", width="100%", margin_bottom="2rem"
                                ),
                                rx.cond(
                                    SearchViewState.finance_data.length() > 0,
                                    rx.data_table(
                                        data=SearchViewState.finance_data,
                                        columns=SearchViewState.finance_cols,
                                        style={"background_color": "#111827", "color": "#e5e7eb"}
                                    ),
                                    rx.text("無法取得損益表資料。", color="#9ca3af")
                                ),
                                width="100%"
                            ),
                            value="finance"
                        ),
                        
                        # Tab 4: 進階交易 (保持原樣的骨架)
                        rx.tabs.content(
                            rx.grid(
                                rx.box(
                                    rx.heading("🕵️ 內部人與機構動向", size="4", color="#60a5fa", margin_bottom="10px"),
                                    rx.text("追蹤 CEO/CFO 買賣紀錄與大戶籌碼流向。", color="#9ca3af", size="2", margin_bottom="15px"),
                                    rx.badge("🚧 爬蟲程式開發中", color_scheme="yellow"),
                                    bg="#111827", padding="1.5rem", border_radius="12px", border="1px solid #1f2937"
                                ),
                                rx.box(
                                    rx.heading("🕸️ 網格與期權雷達", size="4", color="#a78bfa", margin_bottom="10px"),
                                    rx.text("選擇權未平倉量 (OI) 分佈與適合網格交易區間。", color="#9ca3af", size="2", margin_bottom="15px"),
                                    rx.badge("🚧 模組建置中", color_scheme="yellow"),
                                    bg="#111827", padding="1.5rem", border_radius="12px", border="1px solid #1f2937"
                                ),
                                columns="2", spacing="4", margin_top="1.5rem"
                            ),
                            value="quant"
                        ),
                        width="100%"
                    ),
                    width="100%",
                    align_items="start"
                )
            )
        ),
        padding="2rem", width="100%"
    )