#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""黄色文字连通块定位（任务 §7：按钮须像素分析，不目测坐标）。
在 800x600 左上区域找黄色/金黄色文字像素，做连通块（8-邻接）聚类，输出 bbox/centroid/size。
用法: python pxfind.py --tag menu (先 shot.py 截图) 或直接 --region 0,0,800,600 现场抓屏。
"""
import argparse
import ctypes
from collections import deque

import numpy as np
from PIL import ImageGrab

try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

EVID = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W177-D\EVIDENCE"


def yellow_mask(arr, ry=70, gy=45, by=90, rmin=110, gmin=80):
    r = arr[:, :, 0].astype(int)
    g = arr[:, :, 1].astype(int)
    b = arr[:, :, 2].astype(int)
    # 黄色/金黄：R 高、G 中高、B 低；允许一定范围
    return (r >= rmin) & (g >= gmin) & (b <= by) & ((r - b) >= ry) & ((g - b) >= gy)


def components(mask, minpx=12):
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    out = []
    ys, xs = np.nonzero(mask)
    for sy, sx in zip(ys, xs):
        if seen[sy, sx]:
            continue
        q = deque([(sy, sx)])
        seen[sy, sx] = True
        pts = []
        while q:
            y, x = q.popleft()
            pts.append((y, x))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        q.append((ny, nx))
        if len(pts) >= minpx:
            py = [p[0] for p in pts]
            px = [p[1] for p in pts]
            out.append({"n": len(pts),
                        "x0": min(px), "x1": max(px), "y0": min(py), "y1": max(py),
                        "cx": sum(px) / len(px), "cy": sum(py) / len(py)})
    out.sort(key=lambda d: -d["n"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="0,0,800,600")
    ap.add_argument("--minpx", type=int, default=12)
    ap.add_argument("--ry", type=int, default=70)
    ap.add_argument("--gy", type=int, default=45)
    ap.add_argument("--by", type=int, default=90)
    ap.add_argument("--rmin", type=int, default=110)
    ap.add_argument("--gmin", type=int, default=80)
    a = ap.parse_args()
    x0, y0, x1, y1 = [int(v) for v in a.region.split(",")]
    arr = np.array(ImageGrab.grab(bbox=(x0, y0, x1, y1), all_screens=False).convert("RGB"))
    mask = yellow_mask(arr, a.ry, a.gy, a.by, a.rmin, a.gmin)
    comps = components(mask, a.minpx)
    print("region=(%d,%d,%d,%d) yellow_px=%d comps>=%d: %d" %
          (x0, y0, x1, y1, int(mask.sum()), a.minpx, len(comps)))
    for c in comps[:60]:
        # 输出屏幕绝对坐标
        print("  n=%5d bbox=(%d,%d)-(%d,%d) center=(%.0f,%.0f) abs=(%.0f,%.0f)" %
              (c["n"], c["x0"], c["y0"], c["x1"], c["y1"], c["cx"], c["cy"],
               x0 + c["cx"], y0 + c["cy"]))


if __name__ == "__main__":
    main()
