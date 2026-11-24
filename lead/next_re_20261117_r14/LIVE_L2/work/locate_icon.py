#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Screenshot + locate the build sidebar icon for the LIVE-L2 session."""
import os, json, sys
from PIL import Image
import ctypes
from w177_click import game_hwnd, force_foreground

CARD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\LIVE_L2"
EVID = os.path.join(CARD, "EVIDENCE")
PID = 41892
u32 = ctypes.windll.user32
try: u32.SetProcessDPIAware()
except Exception: pass

force_foreground(game_hwnd(PID), 0.5)
img = Image.grab = None
from PIL import ImageGrab
shot = ImageGrab.grab(all_screens=False)
p = os.path.join(EVID, "sidebar_session.png")
shot.save(p)
print("size", shot.size, "saved", p)

# adapt sidebar_locate: find most colorful build tile in sidebar band
SX0, SX1 = 2246, 2560
EMPTY_Y0, EMPTY_Y1 = 560, 1330
im = shot.convert("RGB"); px = im.load(); Wd, Ht = im.size

def lum(rgb):
    r, g, b = rgb[:3]; return 0.299*r + 0.587*g + 0.114*b
def colorfulness(x0, x1, y0, y1):
    vals = []
    for y in range(y0, y1, 3):
        for x in range(x0, x1, 3):
            r, g, b = px[x, y][:3]
            vals.append(max(r, g, b) - min(r, g, b))
    return sum(vals)/len(vals) if vals else 0.0
def colprof(x0, x1, y0, y1):
    out = {}
    for x in range(x0, x1):
        s = n = 0
        for y in range(y0, y1, 3):
            s += lum(px[x, y]); n += 1
        out[x] = s/n
    return out
def dark_gaps(prof, lo, hi, thresh=8, minrun=3):
    gaps = []; run = []
    for k in range(lo, hi+1):
        if prof.get(k, 255) < thresh: run.append(k)
        else:
            if len(run) >= minrun: gaps.append((run[0], run[-1]))
            run = []
    if len(run) >= minrun: gaps.append((run[0], run[-1]))
    return gaps
def rowprof(x0, x1, y0, y1):
    out = {}
    for y in range(y0, y1):
        s = n = 0
        for x in range(x0, x1, 2):
            s += lum(px[x, y]); n += 1
        out[y] = s/n
    return out

cp = colprof(SX0, SX1, EMPTY_Y0, EMPTY_Y1)
colgaps = [g for g in dark_gaps(cp, SX0, SX1-1, 8, 3) if g[0] > SX0+5 and g[1] < SX1-5]
peaks = [x for x in range(SX0+2, SX1-2) if cp[x] > 100 and cp[x] >= cp[x-1] and cp[x] > cp[x+1]]
merged = []
for x in peaks:
    if merged and x - merged[-1][-1] <= 2: merged[-1].append(x)
    else: merged.append([x])
peak_centers = [int(round(sum(g)/len(g))) for g in merged]
first_peak = peak_centers[0] if peak_centers else SX0+30
last_peak = peak_centers[-1] if peak_centers else SX1-40
left_edge = first_peak-10
for x in range(first_peak-2, SX0, -1):
    if cp[x] < 25: left_edge = x; break
right_edge = last_peak+10
for x in range(last_peak+2, SX1):
    if cp[x] < 25: right_edge = x; break
col_sep = [(g[0]+g[1])//2 for g in colgaps]
bounds = sorted(set([left_edge] + col_sep + [right_edge]))
cols = [(bounds[i], bounds[i+1]) for i in range(len(bounds)-1) if bounds[i+1]-bounds[i] >= 60][:2]
if not cols: cols = [(2272,2400),(2400,2530)]
lx0, lx1 = cols[0][0]+8, cols[0][1]-8
rp = rowprof(lx0, lx1, 400, Ht-80)
rowgaps = dark_gaps(rp, 400, Ht-80, 8, 3)
row_sep = [(g[0]+g[1])//2 for g in rowgaps]
first_sep = row_sep[0] if row_sep else Ht
periods = [row_sep[i+1]-row_sep[i] for i in range(len(row_sep)-1)]
import statistics
period = int(round(statistics.median(periods))) if periods else 94
top = first_sep - period
rows = []
ybounds = sorted(set([top] + row_sep))
for i in range(len(ybounds)-1):
    if ybounds[i+1]-ybounds[i] >= 50: rows.append((ybounds[i], ybounds[i+1]))
rows = rows[:8]
tiles = []
for ri, (y0, y1) in enumerate(rows):
    for ci, (x0, x1) in enumerate(cols):
        ix0, ix1 = x0+8, x1-8; iy0, iy1 = y0+6, y1-6
        if ix1 <= ix0 or iy1 <= iy0: continue
        tiles.append({"row": ri, "col": ci, "bbox": [x0,y0,x1,y1],
                      "center": [(x0+x1)//2,(y0+y1)//2],
                      "cf": round(colorfulness(ix0,ix1,iy0,iy1),2)})
cand = sorted(tiles, key=lambda t: (-t["cf"], t["row"], t["col"]))
out = {"screen": [Wd,Ht], "cols": cols, "row_sep": row_sep, "period": period,
       "tiles": tiles, "top": cand[:6]}
json.dump(out, open(os.path.join(EVID,"sidebar_session.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=2)
print(json.dumps(out, ensure_ascii=False, indent=2))
