"""
市場部門經理
"""
from . import breadth
from . import strength # 👈 新增這行
from . import naaim
from . import sentiment
from . import world_sectors

def update():
    print("🔹 [Market Dept] 開始更新...")
    breadth.update()
    strength.update()   # 👈 新增這行
    naaim.update()
    sentiment.update()
    world_sectors.update()