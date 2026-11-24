# -*- coding: utf-8 -*-
"""§537 v2 -- 停摆窗普查（修正判据）。

第一版错误：把 frame_edges 为空/极少（=整窗帧号不动）的窗当"无法分析"跳过。
但这些正是**停摆窗本身**——verdict=no_advance 即"帧号未推进"。

修正后的分类轴：
  A. verdict 轴（harness 自己的判定）：ok / no_advance / frame_wait_timeout
  B. 形态轴（对 ok 窗）：等值帧游程（frame 重复）→ 区分健康 vs 有停滞
"""
import glob
import json
import os
import statistics as st

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
FILES = sorted(glob.glob(os.path.join(BASE, "*", "measure_w*.json")))

rows = []
for p in FILES:
    j = json.load(open(p, encoding="utf-8"))
    ed = j.get("frame_edges") or []
    span = (j.get("span_s") or 0.0)
    rows.append({
        "trip": os.path.basename(os.path.dirname(p)),
        "win": j.get("window"),
        "verdict": j.get("verdict"),
        "edges": len(ed),
        "span": span,
        "f0": ed[0][0] if ed else None,
        "f1": ed[-1][0] if ed else None,
        "units0": (j.get("gate") or {}).get("units0"),
        "err": (j.get("error") or "")[:60],
        "stats": j.get("stats") or {},
        "ed": ed,
    })

print("total windows: %d" % len(rows))
print()

print("=" * 88)
print("A. verdict 轴（harness 自判）")
print("=" * 88)
from collections import Counter
c = Counter(r["verdict"] for r in rows)
for k, v in c.most_common():
    print("  %-22s %d" % (k, v))
print()

NOADV = [r for r in rows if r["verdict"] == "no_advance"]
TO = [r for r in rows if r["verdict"] == "frame_wait_timeout"]

print("=" * 88)
print("B. ★ no_advance 窗明细（%d 个）—— 整窗帧号几乎不推进" % len(NOADV))
print("=" * 88)
print("%-24s %-3s %6s %6s %8s %8s %s" % ("trip", "win", "edges", "df", "span_s", "units0", "err"))
for r in NOADV:
    df = (r["f1"] - r["f0"]) if r["edges"] else 0
    print("%-24s %-3s %6d %6s %8.2f %8s %s" % (
        r["trip"][:24], r["win"], r["edges"], df, r["span"], r["units0"], r["err"]))
print()

print("=" * 88)
print("C. frame_wait_timeout 窗（%d 个）—— 等不到目标帧号" % len(TO))
print("=" * 88)
for r in TO:
    print("  %-24s w%-2s span=%6.2f units0=%s" % (r["trip"][:24], r["win"], r["span"], r["units0"]))
    print("     %s" % r["err"])
print()

# ---- ok 窗的形态分析 -----------------------------------------------------
OK = [r for r in rows if r["verdict"] == "ok" and r["edges"] >= 2]
print("=" * 88)
print("D. ok 窗形态（%d 个可分析）" % len(OK))
print("=" * 88)

def runs_of(ed):
    """返回 [(t_start, dur, frame)] —— frame 不变的连续段。"""
    out = []
    start = 0
    for i in range(1, len(ed)):
        if ed[i][0] != ed[i - 1][0]:
            if i - 1 > start:
                out.append((ed[start][1], ed[i - 1][1] - ed[start][1], ed[start][0]))
            start = i
    if len(ed) - 1 > start:
        out.append((ed[start][1], ed[-1][1] - ed[start][1], ed[start][0]))
    return out


stall_any = []
for r in OK:
    ed = r["ed"]
    rn = runs_of(ed)
    longest = max((x[1] for x in rn), default=0.0)
    r["longest"] = longest
    r["n_runs"] = len(rn)
    r["df"] = ed[-1][0] - ed[0][0]
    r["fps"] = r["df"] / r["span"] if r["span"] else 0
    if longest >= 0.5:
        stall_any.append(r)

print("  ok 窗里有 >=0.5s 等值帧游程的: %d / %d" % (len(stall_any), len(OK)))
print("  最长游程分布: max=%.3fs  p90=%.3fs  中位=%.3fs" % (
    max((r["longest"] for r in OK), default=0),
    st.quantiles([r["longest"] for r in OK], n=10)[-1] if len(OK) > 10 else 0,
    st.median([r["longest"] for r in OK])))
print()
print("  ★ 有 >=0.5s 停滞的 ok 窗（按最长游程降序，前 20）：")
print("  %-24s %-3s %6s %6s %8s %9s %7s" % ("trip", "win", "span", "df", "fps", "longest", "units0"))
for r in sorted(stall_any, key=lambda x: -x["longest"])[:20]:
    print("  %-24s %-3s %6.2f %6d %8.2f %9.3f %7s" % (
        r["trip"][:24], r["win"], r["span"], r["df"], r["fps"], r["longest"], r["units0"]))
print()

# ---- 全库 fps 与 units0 ---------------------------------------------------
print("=" * 88)
print("E. units0 vs 帧率（全部可用于分析的窗，含 no_advance 视为 fps≈0）")
print("=" * 88)
allp = []
for r in rows:
    u = r["units0"]
    if not isinstance(u, int):
        continue
    if r["verdict"] == "no_advance":
        allp.append((u, 0.0))
    elif r["verdict"] == "ok" and r["edges"] >= 2 and r["span"]:
        allp.append((u, (r["ed"][-1][0] - r["ed"][0][0]) / r["span"]))
if len(allp) >= 5:
    xs = [p[0] for p in allp]
    ys = [p[1] for p in allp]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in allp)
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    print("  n=%d  Pearson r(units0, fps) = %+.4f" % (n, num / den if den else 0))
    print()
    for lo, hi, name in [(0, 200, "<200"), (200, 500, "200-500"), (500, 1000, "500-1000"),
                         (1000, 10 ** 9, ">=1000")]:
        g = [p for p in allp if lo <= p[0] < hi]
        if not g:
            print("    %-9s n=0" % name)
            continue
        fps_ = sorted(p[1] for p in g)
        print("    %-9s n=%2d  fps中位=%6.2f  最低=%5.2f  最高=%6.2f  fps<5 的窗=%d" % (
            name, len(g), st.median(fps_), fps_[0], fps_[-1], sum(1 for f in fps_ if f < 5)))
