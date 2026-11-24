# -*- coding: utf-8 -*-
"""V2 产物：逐窗独立分类表 + 计数校验 + 38 慢窗清单。

只输出到 stdout（由 shell 重定向落盘），脚本自身零写入。
截图可得性用固定前缀/后缀切出的窗号集合判断，不动态拼路径。
"""
import glob
import json
import os
from collections import Counter

BASE = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
PRE = "measure_w"
SUF = "_end_x.png"

png_by_dir = {}
for q in glob.glob(os.path.join(BASE, "*", "*.png")):
    b = os.path.basename(q)
    if b.startswith(PRE) and b.endswith(SUF):
        core = b[len(PRE):len(b) - len(SUF)]
        if core.isdigit():
            png_by_dir.setdefault(os.path.basename(os.path.dirname(q)), set()).add(int(core))

paths = sorted(glob.glob(os.path.join(BASE, "*", "measure_w*.json")))
rows = []
for p in paths:
    j = json.load(open(p, encoding="utf-8"))
    ed = j.get("frame_edges") or []
    st = j.get("stats") or {}
    g = j.get("gate") or {}
    d = os.path.basename(os.path.dirname(p))
    if ed:
        f0, f1 = ed[0][0], ed[-1][0]
        df = f1 - f0
        cls = "ADV" if df > 0 else ("BACK" if df < 0 else ("LOAD" if f0 == 0 else "FRZ"))
    else:
        f0 = f1 = df = None
        cls = "NO_EDGES"
    cs = j.get("counters") or []
    units = [c.get("units") for c in cs]
    w = int(j.get("window"))
    rows.append(dict(dir=d, trip_id=j.get("trip_id"), w=w, cls=cls, f0=f0, f1=f1, df=df,
                     fps_avg=st.get("fps_avg"),
                     df_over_span=(df / j["span_s"]) if (df is not None and j.get("span_s")) else None,
                     logic_frames=st.get("logic_frames"), max_stall_s=st.get("max_stall_s"),
                     span_s=j.get("span_s"), pre_fps15=g.get("pre_fps15"), gate_ok=g.get("ok"),
                     units0=g.get("units0"), units_first=units[0] if units else None,
                     n_uniq_units=len(set(units)) if units else 0,
                     samples=st.get("samples"), n_edges=len(ed), verdict=j.get("verdict"),
                     map8=(j.get("map_sha256") or "")[:8],
                     end_png="Y" if w in png_by_dir.get(d, set()) else "-",
                     game_s_at_f0=(f0 / 31.2) if f0 else None))

c = Counter(r["cls"] for r in rows)
print("subdir-only glob: 文件 %d ；分类计数 %s" % (len(paths), dict(c)))
print("趟目录数（有至少 1 个可分类窗）= %d" % len({r["dir"] for r in rows if r["cls"] != "NO_EDGES"}))
adv = [r for r in rows if r["cls"] == "ADV"]
lo = sorted([r for r in adv if (r["fps_avg"] or 99) < 28], key=lambda x: x["fps_avg"])
hi = [r for r in adv if (r["fps_avg"] or 0) >= 28]
print("ADV=%d  fps_avg>=28:%d  <28:%d" % (len(adv), len(hi), len(lo)))
print()
print("=== 38 个 fps_avg<28 的窗（目标①候选样本）===")
for i, r in enumerate(lo, 1):
    print("  %2d %-18s w%-2s fps=%8.3f df=%5d stall=%8.3f span=%5.1f df/span=%7.3f map=%s 窗末png=%s" %
          (i, r["dir"], r["w"], r["fps_avg"], r["df"], r["max_stall_s"] or 0, r["span_s"],
           r["df_over_span"], r["map8"], r["end_png"]))
print()
frz = [r for r in rows if r["cls"] == "FRZ"]
print("=== 29 个 FRZ 窗的核对汇总 ===")
print("FRZ=%d ；有窗末 PNG 的 %d ；无 PNG 的 %d" %
      (len(frz), sum(1 for r in frz if r["end_png"] == "Y"), sum(1 for r in frz if r["end_png"] == "-")))
print("pre_fps15>=28 且 logic_frames==0 的：%d" %
      sum(1 for r in frz if (r["pre_fps15"] or 0) >= 28 and r["logic_frames"] == 0))
print("窗内 units 唯一值==1 的：%d" % sum(1 for r in frz if r["n_uniq_units"] == 1))
print("|max_stall_s - span_s| <= 0.05 的：%d" %
      sum(1 for r in frz if r["span_s"] and abs((r["max_stall_s"] or 0) - r["span_s"]) <= 0.05))
print("game_s_at_f0 = f0/31.2 <= 30 s 的：%d" % sum(1 for r in frz if (r["game_s_at_f0"] or 0) <= 30.0))
print("冻结窗首秒 units < gate.units0 的：%d" %
      sum(1 for r in frz if r["units0"] and r["units_first"] is not None and r["units_first"] < r["units0"]))
print("无 PNG 的 FRZ 窗：%s" % [(r["dir"], r["w"]) for r in frz if r["end_png"] == "-"])
print()
print("=== 逐窗全表（我的独立分类，管道分隔）===")
print("dir|trip_id|w|cls|f0|f1|df|fps_avg|df/span|logic|stall|span|pre_fps15|gate_ok|units0|units冻|uniqU|samples|n_edges|map8|png|verdict")
for r in sorted(rows, key=lambda x: (x["dir"], x["w"])):
    print("%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s" % (
        r["dir"], r["trip_id"], r["w"], r["cls"], r["f0"], r["f1"], r["df"],
        ("%.3f" % r["fps_avg"]) if r["fps_avg"] is not None else "-",
        ("%.3f" % r["df_over_span"]) if r["df_over_span"] is not None else "-",
        r["logic_frames"], r["max_stall_s"], r["span_s"], r["pre_fps15"], r["gate_ok"],
        r["units0"], r["units_first"], r["n_uniq_units"], r["samples"], r["n_edges"],
        r["map8"], r["end_png"], r["verdict"]))
