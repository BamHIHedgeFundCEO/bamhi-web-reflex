import reflex as rx
import os

config = rx.Config(
    app_name="bamhi_reflex", 
    api_url=os.environ.get("API_URL", "http://localhost:8000"),
    cors_allowed_origins=["*"], 
    
    # 👇 加上這行！強迫 Reflex 後端對全世界廣播，讓 Render 能夠偵測到它！
    backend_host="0.0.0.0", 
)
