# -*- coding: utf8 -*-
"""RC-I：协议旗标 → 首窗首沿帧 的因果链 + 负载在趟级的解释力（报告 §4 把它否掉了）。"""
import csv, os, statistics
from collections import defaultdict

OUT = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(OUT, "rc_census.csv"), encoding="utf-8")))
for r in rows:
    for k in ("units0", "live", "span_s", "c_units", "f0", "f1"):
        try:
            r[k] = float(r[k])
        except (TypeError, ValueError):
            r[k] = None
P3 = [r for r in rows if r["base_tag"] == "mirror" and r["verdict"] == "ok" and r["span_s"] == 25.0
      and r["live"] and r["live"] > 0]

print("== 1) --h7-measure-start-frame 设定值 vs 首窗首沿帧 w0 ==")
d0 = defaultdict(set)
for r in P3:
    if r["window"] == "0":
        d0[r["sf"] or "default"].add((r["dir"], int(r["f0"]), int(r["units0"]) if r["units0"] else None))
for k in sorted(d0):
    print("  sf=%-8s w0 首沿帧/units0: %s" % (k, sorted(d0[k], key=lambda x: x[1])))

print("\n== 2) 负载在趟级的解释力（各图）==")
def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs)/n, sum(ys)/n
    dx = sum((a-mx)**2 for a in xs) ** .5
    dy = sum((b-my)**2 for b in ys) ** .5
    return None if n < 3 or dx == 0 or dy == 0 else sum((a-mx)*(b-my) for a, b in zip(xs, ys))/(dx*dy)
for mp in ("f3bb0a4e", "0add791d"):
    g = defaultdict(list)
    for r in P3:
        if (r["map_sha256"] or "").startswith(mp) and r["c_units"]:
            g[r["dir"]].append(r)
    pts = [(statistics.median(x["c_units"] for x in rs), statistics.median(x["live"] for x in rs), d)
           for d, rs in g.items() if len(rs) >= 2]
    rp = pearson([p[0] for p in pts], [p[1] for p in pts])
    print("  map %s 趟 n=%d ρ_P(c_units,live)=%+.4f  r²=%.3f" % (mp, len(pts), rp, rp*rp))
    for c, l, d in sorted(pts):
        print("      c_units=%7.1f live=%6.2f  %s" % (c, l, d))

print("\n== 3) 报告 §4 的两条 prose 核对 ==")
g = defaultdict(list)
for r in P3:
    if (r["map_sha256"] or "").startswith("f3bb0a4e"):
        g[r["dir"]].append(r)
both = 0
for d, rs in g.items():
    rs.sort(key=lambda x: int(x["window"]))
    if len(rs) >= 2 and rs[0]["live"] > rs[-1]["live"]:
        both += 1
print("  L3 多窗趟 %d；「负载降 2 步而 live 也降」= live(w0)>live(w末) 的趟数 %d" % (
    len([1 for rs in g.values() if len(rs) >= 2]), both))
print("  报告 AC 原表口径是「live 升 2 步 ⇒ 一致」：一致 1 / 不一致 8 —— 与上面不是同一命题")

print("\n== 4) 快档帽位松紧（V2-C 的 31.25 之说）==")
F = [r for r in P3 if r["live"] >= 28]
print("  n=%d；>31.25fps（即帧时<31.98ms）的窗 %d 个 (%.0f%%)" % (
    len(F), sum(1 for r in F if r["live"] > 31.25), 100*sum(1 for r in F if r["live"] > 31.25)/len(F)))
print("  超出帽位最多：%s" % sorted([("%.2f %s" % (r["live"], r["dir"])) for r in F if r["live"] > 31.3])[-4:])
print("  31.25±0.15 带内窗数 %d / %d" % (sum(1 for r in F if abs(r["live"]-31.25) <= .15), len(F)))
