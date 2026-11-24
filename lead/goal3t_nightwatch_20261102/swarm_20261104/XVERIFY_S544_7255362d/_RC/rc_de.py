# -*- coding: utf8 -*-
"""RC-D/E：ρ 池敏感性、pre15/live 比值、趟内vs趟间、settle 伪窗计数。全部自算。"""
import csv, os, statistics
from collections import defaultdict

OUT = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(OUT, "rc_census.csv"), encoding="utf-8")))
for r in rows:
    for k in ("units0", "live", "span_s", "pre_fps15", "gap_s", "c_units"):
        try:
            r[k] = float(r[k])
        except (TypeError, ValueError):
            r[k] = None
M = [r for r in rows if r["base_tag"] == "mirror"]

def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs)/n, sum(ys)/n
    dx = sum((a-mx)**2 for a in xs) ** .5
    dy = sum((b-my)**2 for b in ys) ** .5
    return None if dx == 0 or dy == 0 else sum((a-mx)*(b-my) for a, b in zip(xs, ys))/(dx*dy)

def spearman(xs, ys):
    def rk(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0]*len(v); i = 0
        while i < len(o):
            j = i
            while j+1 < len(o) and v[o[j+1]] == v[o[i]]:
                j += 1
            avg = (i+j)/2.0+1.0
            for k in range(i, j+1):
                r[o[k]] = avg
            i = j+1
        return r
    return pearson(rk(xs), rk(ys))

P1 = [r for r in M if r["units0"] is not None and r["live"] is not None]
P2 = [r for r in P1 if r["live"] > 0]
P3 = [r for r in P2 if r["verdict"] == "ok" and r["span_s"] == 25.0]
BAND = [r for r in P3 if 1180 <= r["units0"] <= 1360]
print("P1=%d P2=%d P3=%d BAND=%d" % (len(P1), len(P2), len(P3), len(BAND)))
print("\n== ρ(pre_fps15, live) 池敏感性 ==")
for nm, pool in (("P1 字面(含负live)", P1), ("P2 live>0", P2), ("P3 严格25s", P3),
                 ("BAND 1180-1360", BAND), ("units0>=800 严格窗", [r for r in P3 if r["units0"] >= 800])):
    pp = [r for r in pool if r["pre_fps15"] is not None]
    if not pp:
        continue
    print("  %-22s n=%2d ρ_P=%+.4f ρ_S=%+.4f | ρ_P(units0,live)=%+.4f" % (
        nm, len(pool), pearson([r["pre_fps15"] for r in pp], [r["live"] for r in pp]),
        spearman([r["pre_fps15"] for r in pp], [r["live"] for r in pp]),
        pearson([r["units0"] for r in pool], [r["live"] for r in pool]) or float('nan')))
trips = defaultdict(list)
for r in P3:
    trips[r["dir"]].append(r)
TL = [dict(live=statistics.median(x["live"] for x in rs),
           units0=rs[0]["units0"], pre=rs[0]["pre_fps15"]) for rs in trips.values()]
TL = [t for t in TL if t["pre"] is not None]
print("  %-22s n=%2d ρ_P=%+.4f ρ_S=%+.4f | ρ_P(units0,live)=%+.4f" % (
    "趟级(每趟live中位)", len(TL), pearson([t["pre"] for t in TL], [t["live"] for t in TL]),
    spearman([t["pre"] for t in TL], [t["live"] for t in TL]),
    pearson([t["units0"] for t in TL], [t["live"] for t in TL])))

print("\n== pre15 / live 窗级比值 ==")
rt = sorted(r["pre_fps15"]/r["live"] for r in P3 if r["pre_fps15"] and r["live"])
print("  n=%d 中位=%.3f min=%.3f max=%.3f" % (len(rt), statistics.median(rt), rt[0], rt[-1]))
for d in ("l3_1101v4e", "t55k_20261020"):
    for r in M:
        if r["dir"] == d and r["window"] == "0":
            print("   %s w0 pre15=%.3f live=%.3f ratio=%.3f" % (d, r["pre_fps15"], r["live"], r["pre_fps15"]/r["live"]))

print("\n== settle 伪窗（span=4.0）进入 P1 的个数 ==")
sp4 = [r for r in P1 if r["span_s"] == 4.0]
print("  P1 中 span_s=4.0 的窗：%d  %s" % (len(sp4), sorted(set(r["dir"] for r in sp4))))
print("  全库 span_s=4.0 行：%d" % sum(1 for r in M if r["span_s"] == 4.0))
print("  其中带 frame_edges 且 live 可算：%d" % len([r for r in M if r["span_s"] == 4.0 and r["live"]]))

print("\n== 趟内 vs 趟间（严格窗）==")
rng_i, ratios = [], []
for d, rs in trips.items():
    if len(rs) >= 2:
        ls = sorted(r["live"] for r in rs)
        rng_i.append(ls[-1]-ls[0]); ratios.append(ls[-1]/ls[0])
print("  趟内窗间极差 n=%d 中位=%.2f fps 倍率中位=%.2fx max=%.2fx" % (
    len(rng_i), statistics.median(rng_i), statistics.median(ratios), max(ratios)))
tm = sorted(statistics.median(r["live"] for r in rs) for rs in trips.values())
print("  趟级中位 live 趟间极差=%.2f (%.2f..%.2f, %.2fx)" % (tm[-1]-tm[0], tm[0], tm[-1], tm[-1]/tm[0]))
tb = sorted(statistics.median(r["live"] for r in rs) for d, rs in trips.items()
            if any(1180 <= x["units0"] <= 1360 for x in rs))
print("  带内趟间极差=%.2f (%.2f..%.2f, %.2fx)" % (tb[-1]-tb[0], tb[0], tb[-1], tb[-1]/tb[0]))
print("  快趟(趟中位>=28)窗间极差: %s" % sorted(round(max(x["live"] for x in rs)-min(x["live"] for x in rs), 2)
        for d, rs in trips.items() if statistics.median(x["live"] for x in rs) >= 28))
print("  慢趟(趟中位<20)窗间极差: %s" % sorted(round(max(x["live"] for x in rs)-min(x["live"] for x in rs), 2)
        for d, rs in trips.items() if len(rs) >= 2 and statistics.median(x["live"] for x in rs) < 20))
