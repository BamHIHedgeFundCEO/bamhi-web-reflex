import reflex as rx

# ==========================================
# 🎨 BamHI Trend-Core 全域樣式設定檔 (style.py)
# ==========================================

# 1. 全域基礎樣式 (將在主程式 app.py 中套用給整個網站)
BASE_STYLE = {
    "background_color": "#0f1319",
    "color": "#e5e7eb",
    "font_family": "system-ui, -apple-system, sans-serif",
    
    # 讓全站所有的 rx.button 都自帶平滑動畫
    rx.button: { 
        "transition": "all 0.2s ease-in-out",
    }
}

# ==========================================
# 🧱 可重複使用的元件樣式字典 (Design Tokens)
# ==========================================

# 標題樣式 (對應 .hero-title, .hero-subtitle)
hero_title_style = {
    "font_size": "3.5rem",
    "font_weight": "800",
    "line_height": "1.2",
    "color": "#ffffff",
    "margin_bottom": "1rem",
}

hero_subtitle_style = {
    "font_size": "1.1rem",
    "color": "#9ca3af",
    "line_height": "1.6",
    "margin_bottom": "2rem",
}

# 主力按鈕樣式 (對應 .primary-btn)
primary_btn_style = {
    "background_color": "#10b981",
    "color": "#ffffff",
    "padding": "0.75rem 1.5rem",
    "border_radius": "8px",
    "font_weight": "600",
    # Hover 動態效果在 Reflex 中使用 "_hover" 鍵
    "_hover": {
        "background_color": "#059669",
        "transform": "translateY(-2px)",
    },
}

# 次要按鈕樣式 (對應 .secondary-btn)
secondary_btn_style = {
    "background_color": "#1f2937",
    "color": "#e5e7eb",
    "padding": "0.75rem 1.5rem",
    "border_radius": "8px",
    "font_weight": "600",
    "border": "1px solid #374151",
    "margin_left": "10px",
    "_hover": {
        "background_color": "#374151",
    },
}

# 右側排版卡片與標籤 (對應 .bento-card, .bento-tag)
bento_card_style = {
    "background_color": "#111827",
    "border": "1px solid #1f2937",
    "border_radius": "16px",
    "padding": "1.5rem",
    "margin_bottom": "1rem",
    "box_shadow": "0 10px 15px -3px rgba(0, 0, 0, 0.1)", # 加上一點現代感陰影
}

bento_tag_style = {
    "background_color": "#064e3b",
    "color": "#34d399",
    "padding": "4px 10px",
    "border_radius": "12px",
    "font_size": "0.75rem",
    "font_weight": "bold",
    "margin_bottom": "10px",
    "display": "inline-block",
}