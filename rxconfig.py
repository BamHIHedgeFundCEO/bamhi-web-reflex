import reflex as rx
import os

config = rx.Config(
    app_name="bamhi_reflex", # 保持你原本的名字
    # 告訴前端：大腦現在住在哪個網址？(預設是本機，上線時會讀取環境變數)
    api_url=os.environ.get("API_URL", "http://localhost:8000"),
    # 允許任何網址的前端來索取資料，避免被瀏覽器擋下
    cors_allowed_origins=["*"], 
)
