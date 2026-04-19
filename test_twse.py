import requests
import json

# 我們要查的目標：上市公司的綜合損益表
url = "https://openapi.twse.com.tw/v1/opendata/t187ap06_L_ci"

# 你的完美偽裝
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json"
}

print("🚀 正在向台灣證交所發送請求...")
res = requests.get(url, headers=headers, timeout=15)
print(f"📡 伺服器狀態碼: {res.status_code}")

if res.status_code == 200:
    try:
        # 採用你找到的文章解法：用 text 搭配 json.loads
        data = json.loads(res.text)
        print(f"✅ 成功下載資料！政府這次總共給了 {len(data)} 家公司的財報。")
        
        if len(data) > 0:
            print(f"\n👉 第一家公司的資料長這樣：")
            print(data[0])
            
            # 尋找台積電
            tsmc = next((item for item in data if str(item.get('公司代號', '')).strip() == '2330'), None)
            if tsmc:
                print("\n🎉 恭喜！找到台積電了！資料如下：")
                print(tsmc)
            else:
                print("\n💀 悲劇！這幾千家公司裡面，真的沒有 2330！")
                print("可能原因：政府最新一季的財報清單中，台積電尚未更新或被歸類到別的地方。")
                
    except Exception as e:
        print(f"❌ 解析 JSON 失敗: {e}")
        print(f"政府回傳的原始內容前 200 字: {res.text[:200]}")
else:
    print("❌ 請求失敗，被擋下來了！")