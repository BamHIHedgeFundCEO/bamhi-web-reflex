# config.py

INDICATORS = {
    "rates": {
        "title": "利率市場 (Rates)",
        "items": [
            {"id": "DGS10", "name": "10 Years Yield", "ticker": "DGS10", "module": "treasury"},
            {"id": "DGS2", "name": "2 Years Yield", "ticker": "DGS2", "module": "treasury"},
            {"id": "SPREAD_10_2", "name": "10-2 Spread", "ticker": "SPREAD_10_2", "module": "treasury"},
        ],
    },
    "market": {
        "title": "大盤與寬度 (Market)",
        "items": [
            # 第 1 個按鈕：市場寬度
            {"id": "BREADTH_SP500", "name": "S&P 500 市場寬度", "ticker": "SP500_BREADTH", "module": "breadth"},
            
            # 👇 第 2 個按鈕：板塊強弱 (記得要放在這個中括號裡面！)
            {
                "id": "SECTOR_STRENGTH",   # 記得加個 id 讓程式辨認
                "name": "美股板塊強弱 (Sector Strength)", 
                "ticker": "ALL", 
                "module": "strength"
            },
            {
                "id": "SENTIMENT_COMBO",
                "name": "散戶 & 機構情緒方向", 
                "ticker": "NAAIM_AAII", 
                "module": "naaim" # 指向我們新寫的 naaim 模組
            },
            {
                "id": "world_sectors",
                "name": "龜族全景動能儀表板",
                "ticker": "WORLD",
                "module": "world_sectors"
            },
        ],
    },
    "oil": {
        "title": "能源 (Energy)",
        "items": []
    }
}
