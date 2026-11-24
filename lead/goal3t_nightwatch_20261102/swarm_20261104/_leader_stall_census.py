# -*- coding: utf-8 -*-
"""§537 Leader 亲算 -- 全库 measure 窗停滞形态普查（承接 Q02 的 C5）。

只读 measure_w*.json。零真机、零写入（除 stdout）。

要回答：
  1. 多少个窗是「停摆型」（长等值帧游程 + 占比高）vs「健康型」？
  2. 「停摆型」的动力学形态：冻结后**是否补帧**（永不补 vs 追上）？
  3. 两个 regime（等待段慢爬 / 采窗段停摆）的数据画像分别是什么？
  4. 每个窗的 units0 与形态的关系（复核或推翻 §521 的 -0.2005）。
"""
import glob
import json
import os
import statistics as st

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
FILES = sorted(glob.glob(os.path.join(BASE, "*", "measure_w*.json")))
print("measure files: %d" % len(FILES))


def analyze(p):
    j = json.load(open(p, encoding="utf-8"))
    ed = j.get("frame_edges") or []
    if len(ed) < 2:
        return None
    ts = [e[1] for e in ed]
    fs = [e[0] for e in ed]
    span = ts[-1] - ts[0]
    if span <= 0:
        return None
    # 等值帧游程（frame 不变的连续段）
    runs = []
    start = 0
    for i in range(1, len(ed)):
        if fs[i] != fs[i - 1]:
            if i - 1 > start:
                runs.append((ts[start], ts[i - 1] - ts[start], fs[start]))
            start = i
    if len(ed) - 1 > start:
        runs.append((ts[start], ts[-1] - ts[start], fs[start]))
    longest = max((r[1] for r in runs), default=0.0)
    total_stall = sum(r[1] for r in runs if r[1] >= 0.1)
    # 冻结后是否补帧：最后一个长游程之后是否还有推进
    tail_adv = 0
    if runs:
        last = max(runs, key=lambda r: r[1])
        after = [e for e in ed if e[1] > last[0] + last[1]]
        tail_adv = len(after)
    return {
        "path": p,
        "trip": os.path.basename(os.path.dirname(p)),
        "win": j.get("window"),
        "span": span,
        "n_edges": len(ed),
        "f0": fs[0], "f1": fs[-1],
        "df": fs[-1] - fs[0],
        "fps": (fs[-1] - fs[0]) / span,
        "longest": longest,
        "stall_frac": total_stall / span,
        "n_runs": len(runs),
        "units0": (j.get("gate") or {}).get("units0"),
        "tail_adv_after_longest": tail_adv,
        "stats": j.get("stats") or {},
    }


rows = []
for p in FILES:
    try:
        r = analyze(p)
        if r:
            rows.append(r)
    except Exception as e:
        print("  skip %s: %s" % (p, e))

print("analyzed: %d" % len(rows))
print()

# ---- 形态分类 -------------------------------------------------------------
# 停摆型：最长等值游程 >= 2s 且 占窗 > 50%
STALL = [r for r in rows if r["longest"] >= 2.0 and r["stall_frac"] > 0.50]
# 有长停但占比不高
PARTIAL = [r for r in rows if r["longest"] >= 2.0 and r["stall_frac"] <= 0.50]
HEALTHY = [r for r in rows if r["longest"] < 2.0]

print("=" * 86)
print("形态分类（判据：最长等值帧游程 >= 2s）")
print("=" * 86)
print("  STALL-DOMINATED (>=2s 且占比>50%%) : %2d 窗" % len(STALL))
print("  PARTIAL         (>=2s 但占比<=50%%) : %2d 窗" % len(PARTIAL))
print("  HEALTHY         (<2s)               : %2d 窗" % len(HEALTHY))
print("  合计 %d" % (len(STALL) + len(PARTIAL) + len(HEALTHY)))
print()

print("=" * 86)
print("STALL-DOMINATED 明细（按最长游程降序，前 25）")
print("=" * 86)
print("%-26s %-3s %7s %6s %8s %9s %8s %7s %s" % (
    "trip", "win", "span_s", "df", "fps", "longest", "stall%", "runs", "units0"))
for r in sorted(STALL, key=lambda x: -x["longest"])[:25]:
    print("%-26s %-3s %7.2f %6d %8.2f %9.3f %7.1f%% %7d %s" % (
        r["trip"][:26], r["win"], r["span"], r["df"], r["fps"],
        r["longest"], 100 * r["stall_frac"], r["n_runs"], r["units0"]))
print()

print("=" * 86)
print("★ 关键：停摆后是否补帧（df 是否回到 span*fps_healthy 量级）")
print("=" * 86)
for r in sorted(STALL, key=lambda x: -x["longest"])[:12]:
    # 若从未停摆，25s * 31fps ≈ 775 帧
    expected = r["span"] * 31.24
    shortfall = expected - r["df"]
    print("%-26s w%d longest=%7.3fs df=%4d 期望≈%4.0f 缺口=%4.0f (%.0f%%) 最长游程后推进=%d" % (
        r["trip"][:26], r["win"], r["longest"], r["df"], expected, shortfall,
        100 * shortfall / expected if expected else 0, r["tail_adv_after_longest"]))
print()

print("=" * 86)
print("HEALTHY 明细（前 12，按 fps 降序）")
print("=" * 86)
for r in sorted(HEALTHY, key=lambda x: -x["fps"])[:12]:
    print("%-26s w%-2s span=%6.2f df=%4d fps=%6.2f longest=%6.3fs runs=%3d units0=%s" % (
        r["trip"][:26], r["win"], r["span"], r["df"], r["fps"],
        r["longest"], r["n_runs"], r["units0"]))

# ---- units0 与形态的关系（换因变量重算） --------------------------------
print()
print("=" * 86)
print("★ units0 vs 形态（换因变量：用 fps 与 longest，不用 B%）")
print("=" * 86)
pairs = [(r["units0"], r["fps"]) for r in rows if isinstance(r["units0"], int)]
if len(pairs) >= 5:
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in pairs)
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    print("  Pearson r(units0, fps) = %+.4f   (n=%d)" % (num / den if den else 0, n))
    pairs2 = [(r["units0"], r["longest"]) for r in rows if isinstance(r["units0"], int)]
    xs2 = [p[0] for p in pairs2]
    ys2 = [p[1] for p in pairs2]
    mx2, my2 = sum(xs2) / n, sum(ys2) / n
    num2 = sum((x - mx2) * (y - my2) for x, y in pairs2)
    den2 = (sum((x - mx2) ** 2 for x in xs2) * sum((y - my2) ** 2 for y in ys2)) ** 0.5
    print("  Pearson r(units0, longest) = %+.4f" % (num2 / den2 if den2 else 0))
    # 分层
    print()
    print("  按 units0 分档:")
    for lo, hi, name in [(0, 200, "<200"), (200, 500, "200-500"), (500, 1000, "500-1000"),
                         (1000, 10 ** 9, ">=1000")]:
        g = [r for r in rows if isinstance(r["units0"], int) and lo <= r["units0"] < hi]
        if not g:
            print("    %-9s n=0" % name)
            continue
        print("    %-9s n=%2d  fps中位=%6.2f  longest中位=%7.3fs  STALL窗=%d/%d" % (
            name, len(g),
            st.median([r["fps"] for r in g]),
            st.median([r["longest"] for r in g]),
            sum(1 for r in g if r in STALL), len(g)))
