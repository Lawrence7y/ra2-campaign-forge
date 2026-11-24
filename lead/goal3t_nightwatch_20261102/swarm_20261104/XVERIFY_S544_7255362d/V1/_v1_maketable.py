# -*- coding: utf-8 -*-
"""V1：生成 REPORT 用的全量窗口表（markdown）。只读数据，输出到本目录 _v1_table.md。"""
import glob
import json
import os

TRIP = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_v1_table.md")
files = sorted(glob.glob(os.path.join(TRIP, "*", "measure_w*.json")))
files += sorted(glob.glob(os.path.join(TRIP, "measure_w*.json")))

rows = []
for p in files:
    rel = os.path.relpath(p, TRIP).replace("\\", "/")
    d = json.load(open(p, encoding="utf-8"))
    st, g = d["stats"], d.get("gate") or {}
    t, f = d["samples"]["t"], d["samples"]["f"]
    ej = d.get("frame_edges") or []
    span = (t[-1] - t[0]) if len(t) >= 2 else None
    logic = (int(f[-1]) - int(f[0])) if len(f) >= 2 else None
    avg_re = logic / span if span and logic and logic > 0 else None
    live = live_s = tail = None
    if len(ej) >= 2:
        live_s = ej[-1][1] - ej[0][1]
        live = (ej[-1][0] - ej[0][0]) / live_s if live_s > 0 else None
        tail = t[-1] - ej[-1][1]
    ngap = sum(1 for (fa, _), (fb, _) in zip(ej, ej[1:]) if fb - fa == 1)
    gap = 0.0
    for i in range(len(t) - 1):
        dt = t[i + 1] - t[i]
        if dt > 0.010:
            gap += dt
    rows.append((rel, d.get("trip_id"), d.get("window"), g.get("units0"), st.get("fps_avg"),
                 avg_re, live, st.get("fps_p50"), live_s, tail, ngap, logic, span, gap,
                 st.get("note")))

hdr = ("| 窗 | 趟 | u0 | fps_avg(json) | fps_avg(复算) | live_fps(复算) | fps_p50(json) "
       "| 活段s | 尾停s | n_gap | logic | span | 缺口s | note |")
sep = "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"


def fmt(x, nd=2):
    return ("%.*f" % (nd, x)) if isinstance(x, (int, float)) else "—"


lines = ["全量 %d 份 measure_w*.json（趟根 3 + 子目录 100）。命令：python -I -X utf8 _v1_maketable.py" % len(rows),
         "", hdr, sep]
for r in sorted(rows, key=lambda x: x[0]):
    lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
        r[0], r[1], r[3], fmt(r[4]), fmt(r[5]), fmt(r[6]), fmt(r[7]), fmt(r[8], 3),
        fmt(r[9], 3), r[10], r[11], fmt(r[12]), fmt(r[13], 3), r[14] or ""))
open(OUT, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("wrote", OUT, "rows", len(rows))
