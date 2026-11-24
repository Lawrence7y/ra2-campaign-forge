# -*- coding: utf8 -*-
"""RC-B：「同负载跨时段」前提复算。
1) 严格窗池里，同一 units0 精确值是否出现在 >=2 个日期
2) 带内 fast/slow 两组 units0 集合是否真的差 113-163（还是重叠于 1229）
3) 首窗首沿帧（战斗相位）按 w0 口径重算
4) 同一 units0 值跨窗/跨趟的最大倍率
"""
import csv, os, statistics
from collections import defaultdict

OUT = os.path.dirname(os.path.abspath(__file__))
rows = [r for r in csv.DictReader(open(os.path.join(OUT, "rc_census.csv"), encoding="utf-8"))]
for r in rows:
    for k in ("units0", "live", "span_s", "c_units", "f0"):
        try:
            r[k] = float(r[k])
        except (TypeError, ValueError):
            r[k] = None
    r["date"] = (r["ts"] or "")[:10]
M = [r for r in rows if r["base_tag"] == "mirror"]
S = [r for r in M if r["verdict"] == "ok" and r["span_s"] == 25.0 and r["live"] and r["live"] > 0
     and r["units0"] is not None]
print("严格窗 n=%d" % len(S))

print("\n== 1) units0 精确值 → 日期集合（严格窗）==")
u2d = defaultdict(set)
u2n = defaultdict(int)
for r in S:
    u2d[int(r["units0"])].add(r["date"])
    u2n[int(r["units0"])] += 1
multi = {u: ds for u, ds in u2d.items() if len(ds) >= 2}
print("  distinct units0 值=%d；跨 >=2 日期的值=%d %s" % (len(u2d), len(multi), sorted(multi.items())))
print("  出现 >=2 次窗数的值：%s" % sorted((u, n) for u, n in u2n.items() if n >= 2))

print("\n== 1b) 放宽到「同一图 + units0 相差<=40」跨日期是否可配对 ==")
by = defaultdict(list)
for r in S:
    by[(r["map_sha256"] or "")[:8]].append(r)
for mp, rs in sorted(by.items(), key=lambda x: -len(x[1])):
    dates = sorted(set(r["date"] for r in rs if r["date"]))
    span = [r for r in rs if r["units0"] and 1180 <= r["units0"] <= 1360]
    sd = sorted(set(r["date"] for r in span))
    print("  map %s 严格窗 n=%2d 日期=%s ；带内窗 n=%d 日期=%s" % (mp, len(rs), dates, len(span), sd))

print("\n== 2) 带内 fast/slow 的 units0 集合 ==")
B = [r for r in S if 1180 <= r["units0"] <= 1360]
F = [r for r in B if r["live"] >= 28]
SL = [r for r in B if r["live"] < 28]
fu, su = sorted(set(int(r["units0"]) for r in F)), sorted(set(int(r["units0"]) for r in SL))
print("  fast units0=%s\n  slow units0=%s\n  交集=%s" % (fu, su, sorted(set(fu) & set(su))))
print("  最小差（fast max vs slow min 方向）：slow_min=%s fast_max=%s" % (min(su), max(fu)))
for v in sorted(set(fu) & set(su)):
    ff = [x["live"] for x in F if int(x["units0"]) == v]
    ss = [x["live"] for x in SL if int(x["units0"]) == v]
    print("  units0=%d 同值同时出现在快慢两侧：fast %s vs slow %s → 倍率 %.2fx" % (
        v, ["%.2f" % y for y in ff], ["%.2f" % y for y in ss], max(ff + ss) / min(ff + ss)))

print("\n== 3) 首窗（w0）首沿帧 = 战斗相位 ==")
for r in sorted([x for x in B if x["window"] == "0"], key=lambda y: y["live"]):
    print("   w0 live=%6.2f units0=%-5d f0=%-6d %-16s %-10s %s" % (
        r["live"], r["units0"], r["f0"], r["dir"], (r["sha16"] or "harness3")[:10], r["ts"][:16]))
print("  fast 组 w0 f0=%s  slow 组 w0 f0=%s" % (
    sorted(int(x["f0"]) for x in B if x["window"] == "0" and x["live"] >= 28),
    sorted(int(x["f0"]) for x in B if x["window"] == "0" and x["live"] < 28)))

print("\n== 4) 全部严格窗：同一 units0 值跨趟最大倍率（不限带内）==")
best = []
for u, ds in u2d.items():
    rs = [r for r in S if int(r["units0"]) == u]
    if len(rs) >= 2:
        ls = [r["live"] for r in rs]
        best.append((max(ls) / min(ls), u, len(rs), sorted(set(r["dir"] for r in rs)),
                     sorted(set(r["sha16"] or "harness3" for r in rs))))
for ratio, u, n, dirs, sh in sorted(best, reverse=True)[:8]:
    print("   %5.2fx units0=%-5d n窗=%d 趟=%s 版本=%s" % (ratio, u, n, dirs, [x[:10] for x in sh]))
if not best:
    print("   （无任何 units0 精确值有 >=2 窗可比）")
