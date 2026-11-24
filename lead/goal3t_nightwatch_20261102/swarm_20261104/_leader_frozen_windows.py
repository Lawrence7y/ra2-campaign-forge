# -*- coding: utf-8 -*-
"""§538 -- 战斗段完全冻结窗普查（本仓首次识别）。

判据：frame_edges[0].frame != 0（已进图，非加载段）且 df==0（整窗一帧未推进）。
只读 measure_w*.json。零真机、零写入。"""
import glob
import json
import os

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

rows = []
for p in sorted(glob.glob(os.path.join(BASE, "*", "measure_w*.json"))):
    j = json.load(open(p, encoding="utf-8"))
    ed = j.get("frame_edges") or []
    st = j.get("stats") or {}
    g = j.get("gate") or {}
    if not ed:
        continue
    rows.append({
        "trip": os.path.basename(os.path.dirname(p)),
        "win": j.get("window"),
        "f0": ed[0][0],
        "f1": ed[-1][0],
        "n_edges": len(ed),
        "span": j.get("span_s") or 0.0,
        "logic_frames": st.get("logic_frames"),
        "max_stall": st.get("max_stall_s"),
        "fps_avg": st.get("fps_avg"),
        "gate_ok": g.get("ok"),
        "pre_fps15": g.get("pre_fps15"),
        "units0": g.get("units0"),
        "verdict": j.get("verdict"),
        "samples_n": len((j.get("samples") or {}).get("t") or []),
    })

print("总窗数（有 frame_edges）: %d" % len(rows))
print()

frozen = [r for r in rows if r["f0"] != 0 and r["f0"] == r["f1"]]
loading = [r for r in rows if r["f0"] == 0 and r["f0"] == r["f1"]]
healthy = [r for r in rows if r["f0"] != r["f1"]]

print("=" * 100)
print("分类")
print("=" * 100)
print("  战斗段完全冻结 (f0!=0, df==0) : %2d 窗" % len(frozen))
print("  加载段冻结   (f0==0, df==0) : %2d 窗" % len(loading))
print("  有推进       (df!=0)        : %2d 窗" % len(healthy))
print()

print("=" * 100)
print("★ 战斗段完全冻结窗全表（%d 个）" % len(frozen))
print("=" * 100)
hdr = "%-24s %-3s %8s %8s %6s %8s %10s %8s %10s" % (
    "trip", "win", "f0", "span_s", "采样拍", "max_stall", "logic_frames", "pre_fps", "units0")
print(hdr)
print("-" * 100)
for r in sorted(frozen, key=lambda x: x["trip"]):
    print("%-24s %-3s %8d %8.2f %6d %8s %10s %8s %10s" % (
        r["trip"][:24], r["win"], r["f0"], r["span"], r["samples_n"],
        ("%.3f" % r["max_stall"]) if isinstance(r["max_stall"], (int, float)) else "-",
        r["logic_frames"], r["pre_fps15"], r["units0"]))
print()

print("=" * 100)
print("按趟归组（哪些趟有战斗段冻结）")
print("=" * 100)
bytrip = {}
for r in frozen:
    bytrip.setdefault(r["trip"], []).append(r)
for t in sorted(bytrip):
    ws = bytrip[t]
    print("  %-26s %d 窗: %s   采样拍=%s  gate_ok=%s" % (
        t, len(ws), ",".join("w%s" % x["win"] for x in ws),
        sorted(set(x["samples_n"] for x in ws)),
        sorted(set(str(x["gate_ok"]) for x in ws))))
print()

print("=" * 100)
print("健康窗的采样拍对照（证明采样通道本身正常）")
print("=" * 100)
hn = sorted(set(r["samples_n"] for r in healthy))
print("  健康窗 samples_n 取值: %s" % hn)
print("  冻结窗 samples_n 取值: %s" % sorted(set(r["samples_n"] for r in frozen)))
print()

print("=" * 100)
print("max_stall_s >= 2 的全部窗")
print("=" * 100)
big = [r for r in rows if isinstance(r["max_stall"], (int, float)) and r["max_stall"] >= 2]
for r in sorted(big, key=lambda x: -x["max_stall"]):
    print("  %-24s w%-2s f0=%-5d df=%-4d logic_frames=%-5s max_stall=%7.3f units0=%s" % (
        r["trip"][:24], r["win"], r["f0"], r["f1"] - r["f0"],
        r["logic_frames"], r["max_stall"], r["units0"]))
