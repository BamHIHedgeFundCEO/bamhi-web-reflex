import reflex as rx


class AppState(rx.State):
    """管理整個網站的頁面切換與搜尋狀態"""
    current_page: str = "首頁"

    def navigate_to(self, page_name: str):
        """處理 Navbar 的選單點擊"""
        clean_name = page_name.replace(" ▼", "")
        self.current_page = clean_name

    # 👇 新增這個專門處理表單的函式
    def handle_search_form(self, form_data: dict):
        """處理頂部表單的輸入並跳轉"""
        # "search_input" 是我們等一下要在 UI 設定的欄位名稱
        query = form_data.get("search_input", "").strip() 
        
        if query:
            self.current_page = "搜尋結果"

    def clear_search(self):
        """結束搜尋，返回首頁"""
        self.current_page = "首頁"