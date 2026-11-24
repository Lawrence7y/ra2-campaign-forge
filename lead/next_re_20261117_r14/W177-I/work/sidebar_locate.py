#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T1 最终：程序化定位侧栏 NAPOWR icon tile。全部坐标由像素剖面/连通块推导，不硬编码、不目测。
输入：全屏 PNG（本卡 EVIDENCE）。输出：EVIDENCE/sidebar_grid.json（每槽 rect + 所选槽中心 + 判据）。

算法：
 1) 侧栏搜索带 x∈[2246,2560]（任务给定物理范围），全高。
 2) 列结构：在"空槽行带"取 1px 列亮度剖面，找连续≥3px 的近黑间隙(lum<8)作列分隔；
    另取局部极大(凸缘高光)确认每列两边缘。得 2 列 x-跨度。
 3) 行结构：在左列 interior 取 1px 行亮度剖面，找近黑间隙(lum<8,连续≥3px)作行分隔；
    得每行的 y-跨度（等间距网格）。
 4) icon 检测：逐槽取 interior，算"彩色度"(max-min of RGB, 与灰度差)，
    含图标的槽彩色度显著高于空槽(近黑灰)；选彩色度最高且位于最上的槽 = NAPOWR(首槽)。
 5) 中心 = 槽 bbox 中心；断言中心离四边≥8px（防再点边界）。"""
import os, sys, json, statistics
from PIL import Image

EVID = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W177-I\EVIDENCE"
SX0, SX1 = 2246, 2560            # 任务给定侧栏物理范围（搜索带，非最终坐标）
EMPTY_Y0, EMPTY_Y1 = 560, 1330   # 空槽行带（首槽以下多为空格）

def lum(rgb):
    r, g, b = rgb[:3]; return 0.299*r + 0.587*g + 0.114*b

def colprof(px, x0, x1, y0, y1):
    out = {}
    for x in range(x0, x1):
        s = n = 0
        for y in range(y0, y1, 3):
            s += lum(px[x, y]); n += 1
        out[x] = s/n
    return out

def rowprof(px, x0, x1, y0, y1):
    out = {}
    for y in range(y0, y1):
        s = n = 0
        for x in range(x0, x1, 2):
            s += lum(px[x, y]); n += 1
        out[y] = s/n
    return out

def dark_gaps(prof, lo, hi, thresh=8, minrun=3):
    """找 prof 中连续 >=minrun 个 lum<thresh 的间隙 -> [(start,end)] 闭区间。"""
    gaps = []; run = []
    for k in range(lo, hi+1):
        v = prof.get(k, 255)
        if v < thresh:
            run.append(k)
        else:
            if len(run) >= minrun:
                gaps.append((run[0], run[-1]))
            run = []
    if len(run) >= minrun:
        gaps.append((run[0], run[-1]))
    return gaps

def colorfulness(px, x0, x1, y0, y1):
    """槽 interior 彩色度：mean(max(R,G,B)-min(R,G,B))。图标槽高，空槽≈暗灰低。"""
    vals = []
    for y in range(y0, y1, 3):
        for x in range(x0, x1, 3):
            r, g, b = px[x, y][:3]
            vals.append(max(r, g, b) - min(r, g, b))
    return sum(vals)/len(vals) if vals else 0.0

def mean_lum(px, x0, x1, y0, y1):
    vals = [lum(px[x, y]) for y in range(y0, y1, 3) for x in range(x0, x1, 3)]
    return sum(vals)/len(vals) if vals else 0.0

def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(EVID, "after_deploy.png")
    img = Image.open(src).convert("RGB"); px = img.load(); W, H = img.size

    cp = colprof(px, SX0, SX1, EMPTY_Y0, EMPTY_Y1)
    # 列分隔：近黑间隙；仅保留位于侧栏内部(两侧都有内容)的
    colgaps = dark_gaps(cp, SX0, SX1-1, thresh=8, minrun=3)
    colgaps = [g for g in colgaps if g[0] > SX0+5 and g[1] < SX1-5]
    # 取最显著的两个间隙作列间/列右界（按间隙宽度排序不必，直接取前两个内部的）
    # 侧栏 tile 区左界：从左向右，第一个"凸缘高光"(局部极大概 >90) 之后
    # 用列剖面局部极大找高光脊
    peaks = [x for x in range(SX0+2, SX1-2) if cp[x] > 100 and cp[x] >= cp[x-1] and cp[x] > cp[x+1]]
    # 合并相邻峰
    merged = []
    for x in peaks:
        if merged and x - merged[-1][-1] <= 2: merged[-1].append(x)
        else: merged.append([x])
    peak_centers = [int(round(sum(g)/len(g))) for g in merged]

    # 以间隙中点作列边：左界用第一个峰前的暗到亮跃迁，右界用各间隙
    # 更稳妥：列边界 = 间隙中点；首列左界 = 第一个高光峰-8；末列右界 = 最后一个高光峰+8
    # 先定列分隔间隙（列间）
    col_sep = [ (g[0]+g[1])//2 for g in colgaps ]
    # 左列：从第一个高光峰向左找暗谷，右列：从最后一个高光峰向右
    first_peak = peak_centers[0] if peak_centers else SX0+30
    last_peak = peak_centers[-1] if peak_centers else SX1-40
    # 找 tile 区左边界：first_peak 左侧最近的暗谷(lum 局部最小且在 x<first_peak)
    left_edge = None
    for x in range(first_peak-2, SX0, -1):
        if cp[x] < 25:
            left_edge = x; break
    if left_edge is None: left_edge = first_peak-10
    right_edge = None
    for x in range(last_peak+2, SX1):
        if cp[x] < 25:
            right_edge = x; break
    if right_edge is None: right_edge = last_peak+10

    # 由列分隔+左右边界构造 2 列 span
    bounds = [left_edge] + col_sep + [right_edge]
    # 过滤去重、排序
    bounds = sorted(set(bounds))
    cols = []
    for i in range(len(bounds)-1):
        a, b = bounds[i], bounds[i+1]
        if b-a >= 60:  # 至少 60px 宽才算一列 tile
            cols.append((a, b))
    # 若检测出多余列，取最左两列（侧栏建造列固定 2 列）
    cols = cols[:2]

    # 行结构：在左列 interior 取行剖面（跳过首槽图标干扰，用靠下的空槽区 y480..1330 反推周期）
    lx0, lx1 = cols[0][0]+8, cols[0][1]-8
    rp = rowprof(px, lx0, lx1, 400, H-80)
    rowgaps = dark_gaps(rp, 400, H-80, thresh=8, minrun=3)
    row_sep = [(g[0]+g[1])//2 for g in rowgaps]
    # 首行：第一行 sep 之前那一行 tile。用已检出 sep 的中位周期外推顶界，
    # 避免首槽图标干扰导致顶部暗谷(仅1px)未被 dark_gaps(minrun=3)捕获。
    first_sep = row_sep[0] if row_sep else H
    periods = [row_sep[i+1]-row_sep[i] for i in range(len(row_sep)-1)]
    period = int(round(statistics.median(periods))) if periods else 94
    top = first_sep - period
    # 微调：top 落到最近的一个暗谷(<12)附近（±4px），使 bbox 贴真实边沿
    best = top
    for y in range(top-4, top+5):
        if 400 <= y < H and rp.get(y, 255) < 12:
            best = y; break
    top = best
    ybounds = [top] + row_sep
    ybounds = sorted(set(ybounds))
    rows = []
    for i in range(len(ybounds)-1):
        a, b = ybounds[i], ybounds[i+1]
        if b-a >= 50:
            rows.append((a, b))
    # 每行间距应近似相等；取前 8 行
    rows = rows[:8]

    # 逐槽彩色度
    tiles = []
    for ri, (y0, y1) in enumerate(rows):
        for ci, (x0, x1) in enumerate(cols):
            ix0, ix1 = x0+8, x1-8
            iy0, iy1 = y0+6, y1-6
            if ix1 <= ix0 or iy1 <= iy0: continue
            cf = colorfulness(px, ix0, ix1, iy0, iy1)
            ml = mean_lum(px, ix0, ix1, iy0, iy1)
            tiles.append({"row": ri, "col": ci, "bbox": [x0, y0, x1, y1],
                          "center": [(x0+x1)//2, (y0+y1)//2],
                          "colorfulness": round(cf, 2), "mean_lum": round(ml, 2)})

    # 选 NAPOWR：彩色度最高的槽（空槽近黑灰、彩色度<5；图标槽远高于）
    # 若并列取最上(row 最小)、最左(col 最小)
    cand = sorted(tiles, key=lambda t: (-t["colorfulness"], t["row"], t["col"]))
    chosen = cand[0] if cand and cand[0]["colorfulness"] >= 6 else None
    out = {"src": os.path.basename(src), "image_size": [W, H],
           "search_band_x": [SX0, SX1], "empty_row_band_y": [EMPTY_Y0, EMPTY_Y1],
           "col_peak_centers": peak_centers, "col_dark_gaps": colgaps,
           "col_spans": cols, "row_sep": row_sep, "row_period": period,
           "row_spans": rows, "tiles": tiles, "chosen": chosen,
           "determination": ("colorfulness_max" if chosen else "none")}
    if chosen:
        cx, cy = chosen["center"]
        bx0, by0, bx1, by1 = chosen["bbox"]
        margin = min(cx-bx0, bx1-cx, cy-by0, by1-cy)
        out["center_margin_px"] = margin
        out["safe_click"] = margin >= 8
    p = os.path.join(EVID, "sidebar_grid.json")
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps({"cols": cols, "rows": rows, "chosen": chosen,
                      "margin": out.get("center_margin_px"), "safe": out.get("safe_click")},
                     ensure_ascii=False, indent=2))
    print("saved", p)
    return 0 if chosen and out.get("safe_click") else 3

if __name__ == "__main__":
    sys.exit(main())
