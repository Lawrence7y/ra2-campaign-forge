"""V1 probe I: mechanical reading of the score-screen 时间 field, cross-checked against
measure_w*.json frame_edges, plus implied-fps table.  STDOUT ONLY (no writes).

Shape labels come from the bitmaps printed in V1_probeH_out.txt (a 5x9 digital font read
off the printed ASCII bitmaps; not OCR, not a vision model). Signatures are the ink bbox
padded/clipped into 8x10, so the two 1-px rendering offsets in the data collapse to one
shape per digit.
"""
import os, glob, json
import numpy as np
from PIL import Image

ROOT = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
R0, R1 = 120, 142
C0, C1 = 480, 545

GLYPHS = {
    "0": [".###.", "##.##", "##.##", "##.##", "##.##", "##.##", "##.##", "##.##", ".###."],
    "1": ["..##", ".###", "####", "#.##", "..##", "..##", "..##", "..##", "..##"],
    "2": [".###.", "##.##", "...##", "...##", "..##.", ".###.", "###..", "##...", "#####"],
    "3": [".###.", "##.##", "...##", "...##", "..##.", "...##", "...##", "##.##", ".###."],
    "4": ["..##.", "..##.", ".###.", ".###.", "#.##.", "#.##.", "#####", "..##.", "..##."],
    "5": [".####", ".##..", "##...", "####.", "#..##", "...##", "...##", "##.##", ".###."],
    "6": [".###.", "##.##", "##...", "####.", "##.##", "##.##", "##.##", "##.##", ".###."],
    "7": ["#####", "...##", "..##.", "..#..", ".##..", ".##..", ".##..", ".##..", ".##.."],
    "8": [".###.", "##.##", "##.##", "##.##", ".###.", "##.##", "##.##", "##.##", ".###."],
    "9": [".###.", "##.##", "##.##", "##.##", "##.##", ".####", "...##", "##.#.", ".###."],
}


def make_sig(pattern):
    h = len(pattern)
    w = max(len(p) for p in pattern)
    canvas = np.array([[1 if pattern[r][c] == "#" else 0 for c in range(w)] for r in range(h)], dtype=bool)
    out = np.zeros((8, 10), dtype=bool)
    out[:min(h, 8), :min(w, 10)] = canvas[:min(h, 8), :min(w, 10)]
    return "".join("1" if v else "0" for v in out.ravel())


SIG2LAB = {}
for lab, pat in GLYPHS.items():
    SIG2LAB.setdefault(make_sig(pat), []).append(lab)

print("shape library: %d digits -> %d distinct signatures (collision check)" % (
    len(GLYPHS), len(SIG2LAB)))
for s, labs in SIG2LAB.items():
    if len(labs) > 1:
        print("   COLLISION:", labs)


def yellow(a, hi=170, hg=150, lb=130):
    r = a[:, :, 0].astype(int); g = a[:, :, 1].astype(int); b = a[:, :, 2].astype(int)
    return (r > hi) & (g > hg) & (b < lb) & ((r - b) > 70) & ((g - b) > 50)


def extract(a, thr):
    m = yellow(a, *thr)
    sub = m[R0:R1, C0:C1]
    colsum = sub.sum(axis=0)
    cells, x = [], 0
    while x < sub.shape[1]:
        if colsum[x] > 0:
            y = x
            while y < sub.shape[1] and colsum[y] > 0:
                y += 1
            block = sub[:, x:y]
            ys, xs = np.where(block)
            bb = block[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
            h, w = bb.shape
            canvas = np.zeros((8, 10), dtype=bool)
            canvas[:min(h, 8), :min(w, 10)] = bb[:min(h, 8), :min(w, 10)]
            cells.append((C0 + x, C0 + y - 1, h, w, "".join("1" if v else "0" for v in canvas.ravel())))
            x = y
        else:
            x += 1
    return cells


def read_time(cells):
    if len(cells) != 10:
        return None, "cells=%d (no score-screen time field)" % len(cells)
    labs = []
    for i in (2, 3, 5, 6, 8, 9):
        cand = SIG2LAB.get(cells[i][4])
        if not cand:
            return None, "unknown glyph slot%d cols %d-%d h=%d w=%d sig=%s" % (
                i, cells[i][0], cells[i][1], cells[i][2], cells[i][3], cells[i][4])
        if len(cand) > 1:
            return None, "ambiguous %s slot%d" % (cand, i)
        labs.append(cand[0])
    for i in (4, 7):
        h, w = cells[i][2], cells[i][3]
        if w > 3 or h > 9:
            return None, "slot %d not a colon (h=%d w=%d)" % (i, h, w)
    return "%s%s:%s%s:%s%s" % tuple(labs), ""


def hms_to_sec(t):
    hh, mm, ss = t.split(":")
    return int(hh) * 3600 + int(mm) * 60 + int(ss)


files = sorted(glob.glob(os.path.join(ROOT, "*", "measure_w*_end_x.png")))
THRS = [(170, 150, 130), (150, 130, 110), (190, 170, 140)]
recs = []
print()
print("=== STEP 1/2: screen type + timer read, three yellow thresholds ===")
for f in files:
    rel = f[len(ROOT) + 1:].replace("\\", "/")
    a = np.asarray(Image.open(f).convert("RGB"))
    plate = int(yellow(a)[5:30, 665:760].sum())
    reads = [read_time(extract(a, thr)) for thr in THRS]
    base, note = reads[0]
    agree = all(r[0] == base for r in reads)
    trip = rel.split("/")[0]
    widx = int(rel.split("measure_w")[1][0])
    recs.append(dict(rel=rel, trip=trip, w=widx, plate=plate, time=base, note=note, agree=agree))
    print("%-22s w%d plate=%3d time=%-9s agree3=%-5s %s" % (trip, widx, plate, base, agree, note))

print()
print("=== STEP 3: frame_edges last frame vs on-screen time -> implied fps ===")
print("%-22s %-3s %-8s %-5s %-5s %-8s %-7s %-8s %s" % (
    "trip", "w", "last_f", "nedge", "sec", "fps", "fps-31.2", "fps_avg", "json"))
for r in recs:
    jf = os.path.join(ROOT, r["trip"], "measure_w%d.json" % r["w"])
    d = json.load(open(jf, encoding="utf-8"))
    fe = d.get("frame_edges") or []
    last = fe[-1][0] if fe else None
    st = d.get("stats") or {}
    sec = hms_to_sec(r["time"]) if r["time"] else None
    fps = (last / sec) if (sec and last) else None
    r.update(last_frame=last, n_edges=len(fe), sec=sec, fps=fps,
             fps_avg=st.get("fps_avg"), span_s=d.get("span_s"), json=jf,
             max_stall_s=st.get("max_stall_s"), logic_frames=st.get("logic_frames"))
    print("%-22s w%-2d %-8s %-5d %-5s %-8s %-7.2f %-8s" % (
        r["trip"], r["w"], last, len(fe), sec, ("%.2f" % fps) if fps else "-",
        (fps - 31.2) if fps else float("nan"), st.get("fps_avg")))

print()
print("readable-time images: %d of %d" % (sum(1 for r in recs if r["time"]), len(recs)))
inside = [r for r in recs if r["fps"] and 29.9 <= r["fps"] <= 31.4]
outside = [r for r in recs if r["fps"] and not (29.9 <= r["fps"] <= 31.4)]
print("implied fps in 29.9..31.4 : %d ->" % len(inside),
      [r["trip"] + "/w%d" % r["w"] for r in inside])
print("implied fps outside        : %d ->" % len(outside),
      [(r["trip"] + "/w%d" % r["w"], round(r["fps"], 2)) for r in outside])
print()
print("per-trip distinct trips with a readable time:", sorted({r["trip"] for r in recs if r["time"]}))
print()
print("FULL DUMP OF RECORDS")
for r in recs:
    print(json.dumps(r, ensure_ascii=False))
