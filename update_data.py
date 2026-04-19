"""
update_data.py - 數據更新總指揮
"""
import data_pipeline.rates as rates_dept
import data_pipeline.market as market_dept

def main():
    print("==========================================")
    print("🚀 BamHI 數據流水線 (Data Pipeline) 啟動")
    print("==========================================")

    # 1. 叫利率部門做事
    try:
        rates_dept.update()
    except Exception as e:
        print(f"❌ 利率部門回報錯誤: {e}")

    print("-" * 30)

    # 2. 叫市場部門做事
    try:
        market_dept.update()
    except Exception as e:
        print(f"❌ 市場部門回報錯誤: {e}")

    print("==========================================")
    print("✅ 所有任務執行完畢！")

if __name__ == "__main__":
    main()