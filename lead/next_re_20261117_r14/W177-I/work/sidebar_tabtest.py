#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T1 附证：切换侧栏分页(建筑->防御->建筑)，验证 tile 网格几何不变、图标槽位随分页变。
只读截图 + 合成点击。坐标来自 tab 区域裁图的像素位置(相对裁图 3x)。"""
import os, subprocess, json
from PIL import Image
CARD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W177-I"
W = os.path.join(CARD, "work"); EVID = os.path.join(CARD, "EVIDENCE")
# tab 裁图 x2246..2560(3x), y300..440(3x): house~crop(195,295)->orig(2311,398); shield~crop(375,295)->orig(2371,398)
HOUSE = (2311, 398); SHIELD = (2371, 398)

def click(x, y):
    subprocess.run(["python", os.path.join(W, "driver.py"), "click", str(x), str(y)], cwd=W, check=False)
def shot(tag):
    subprocess.run(["python", os.path.join(W, "driver.py"), "shot", tag], cwd=W, check=False)
def locate(tag):
    p = subprocess.run(["python", os.path.join(W, "sidebar_locate.py"), os.path.join(EVID, tag+".png")],
                       cwd=W, capture_output=True, text=True)
    print(tag, "locate rc=", p.returncode)
    print(p.stdout[-600:])
    # 备份 grid（locate 会覆盖 sidebar_grid.json）
    import shutil
    shutil.copy(os.path.join(EVID, "sidebar_grid.json"), os.path.join(EVID, "sidebar_grid_"+tag+".json"))

shot("t1_tab_buildings")
locate("t1_tab_buildings")
click(*SHIELD); shot("t1_tab_defense"); locate("t1_tab_defense")
click(*HOUSE); shot("t1_tab_back"); locate("t1_tab_back")
print("done - compare col_spans/row_spans across 3 grids")
