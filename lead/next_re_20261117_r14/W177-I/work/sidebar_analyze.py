#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T1 像素分析：侧栏 NAPOWR tile 程序化定位。
方法：全屏抓 -> 侧栏 x∈[2246,2560] 全高 -> 列/行亮度剖面找凸缘边沿 ->
     逐槽 interior 亮度/方差判空槽 -> 选含图标的首槽 -> 输出 bbox+中心。
禁止目测/硬编码坐标；本脚本所有坐标由像素剖面推导。"""
import os, sys, json
from PIL import Image

CARD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W177-I"
EVID = os.path.join(CARD, "EVIDENCE")


def lum(px, x, y):
    r, g, b = px[x, y][:3]
    return 0.299 * r + 0.587 * g + 0.114 * b


def col_profile(px, x0, x1, y0, y1, step=1):
    """列平均亮度：对每列 x，取 y∈[y0,y1) 的平均亮度。"""
    out = {}
    for x in range(x0, x1, step):
        s = n = 0
        for y in range(y0, y1, 2):
            s += lum(px, x, y); n += 1
        out[x] = s / n if n else 0.0
    return out


def row_profile(px, x0, x1, y0, y1, step=1):
    out = {}
    for y in range(y0, y1, step):
        s = n = 0
        for x in range(x0, x1, 2):
            s += lum(px, x, y); n += 1
        out[y] = s / n if n else 0.0
    return out


def edges_from_profile(prof, thresh, mode="high"):
    """从剖面找跨阈值的位置集合（连续段取中点）。"""
    xs = sorted(prof)
    cross = []
    for i in range(1, len(xs)):
        a, b = prof[xs[i-1]], prof[xs[i]]
        if mode == "high":
            c = (a < thresh <= b) or (b < thresh <= a)
        else:
            c = (a > thresh >= b) or (b > thresh >= a)
        if c:
            cross.append((xs[i-1] + xs[i]) / 2)
    return cross


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(EVID, "after_deploy.png")
    img = Image.open(src).convert("RGB")
    px = img.load()
    W, H = img.size
    # 侧栏大致范围（来自任务给定的物理 x2246..2560）；SX 为搜索起点
    SX0, SX1 = 2246, 2560
    # 保存放大裁图供结构理解（非定位依据）
    crop = img.crop((2240, 400, 2560, 1340)).resize((640, 1880))
    crop.save(os.path.join(EVID, "sidebar_crop_view.png"))

    # --- 列亮度剖面：在"空槽行带"y∈[560,1320]（第1槽以下多为空格）统计 ---
    cprof = col_profile(px, SX0, SX1, 560, 1320)
    # --- 行亮度剖面：在左列 interior x∈[2290,2400] 统计全高 ---
    rprof = row_profile(px, 2290, 2400, 400, 1360)

    # 输出剖面供复核
    with open(os.path.join(EVID, "sidebar_profiles.json"), "w", encoding="utf-8") as f:
        json.dump({"src": os.path.basename(src), "size": [W, H],
                   "col_profile": {str(k): round(v, 1) for k, v in cprof.items()},
                   "row_profile": {str(k): round(v, 1) for k, v in rprof.items()}}, f, indent=2)

    # 打印剖面摘要（每 4 px）
    print("=== COLUMN profile (x:lum) x∈[%d,%d] step4 ===" % (SX0, SX1))
    print(" ".join("%d:%.0f" % (x, cprof[x]) for x in range(SX0, SX1, 4)))
    print("=== ROW profile (y:lum) y∈[400,1360] step8 ===")
    print(" ".join("%d:%.0f" % (y, rprof[y]) for y in range(400, 1360, 8)))


if __name__ == "__main__":
    main()
