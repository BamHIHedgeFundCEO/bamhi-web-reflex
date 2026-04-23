import reflex as rx
import os

config = rx.Config(
    app_name="bamhi_reflex", 
    
    # 👇 把這行原本的 os.environ... 刪掉，直接寫死你的後端網址！
    # ⚠️ 注意：網址開頭要是 https://，結尾「不要」有斜線 /
    api_url="https://bamhi-web-reflex.onrender.com", 
    
    cors_allowed_origins=["*"], 
    backend_host="0.0.0.0", 
)