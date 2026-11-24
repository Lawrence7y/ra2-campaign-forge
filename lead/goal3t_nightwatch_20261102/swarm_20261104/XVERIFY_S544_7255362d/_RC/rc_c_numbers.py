# -*- coding: utf8 -*-
"""RC-C：点名窗逐帧手算 + 快窗「引擎帽」检验 + 趟配对级 Fisher（去伪重复）。"""
import csv, json, os, statistics, itertools
from math import comb

ROOT = r"D:\Project\ra2-campaign-forge"
MIRROR = ROOT + r"\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
OUT = os.path.dirname(os.path.abspath(__file__))

NAMED = [("l3_1101v4d", 0), ("l3_1101v4e", 0), ("l3_20261031hb", 0), ("l3_20261021", 0),
         ("l1c_20261021", 0), ("l3_1101v3a", 0), ("l3_1101v4c", 0), ("l3_1101v4e", 2)]
print("== 1) 点名窗：直接从 frame_edges 首末元素手算 live ==")
for d, w in NAMED:
    j = json.load(open(os.path.join(MIRROR, d, "measure_w%d.json" % w), encoding="utf-8"))
    e = j["frame_edges"]
    f0, t0, f1, t1 = e[0][0], e[0][1], e[-1][0], e[-1][1]
    df, dt = f1 - f0, t1 - t0
    print("  %-15s w%d edges (%d, %.6f)->(%d, %.6f)  df=%d dt=%.6f  live=%.4f | json fps_avg=%s p50=%s units0=%s" % (
        d, w, f0, t0, f1, t1, df, dt, df / dt, j["stats"]["fps_avg"], j["stats"]["fps_p50"],
        j["gate"]["units0"]))

print("\n== 2) §544 引用的 9.2fps 窗（l1c_20261021）身份核对 ==")
ALL = list(csv.DictReader(open(os.path.join(OUT, "rc_census.csv"), encoding="utf-8")))
for d in ("l1c_20261021", "l3_1101v4d", "l3_1101v4e", "l3_20261021", "l3_20261031hb"):
    grp = [x for x in ALL if x["dir"] == d and x["base_tag"] == "mirror"]
    base = sorted(grp, key=lambda x: int(x["window"]))[0]
    lv = float(base["live"]) if base["live"] else None
    u0 = float(base["units0"]) if base["units0"] else None
    print("  %-15s ts=%s units0=%-6s ∈[1180,1360]?%-3s map=%s 逐窗=%s" % (
        d, (base["ts"] or "")[:19], int(u0) if u0 else "-",
        "是" if u0 and 1180 <= u0 <= 1360 else "★否", (base["map_sha256"] or "")[:12],
        " ".join("%.2f" % float(x["live"]) for x in grp if x["live"] and float(x["live"]) > 0)))

print("\n== 3) 快窗「引擎帽」：全库严格窗 live>=28 的分布 ==")
rows = [r for r in csv.DictReader(open(os.path.join(OUT, "rc_census.csv"), encoding="utf-8"))
        if r["base_tag"] == "mirror"]
for r in rows:
    for k in ("live", "span_s", "units0", "pre_fps15"):
        try:
            r[k] = float(r[k])
        except (TypeError, ValueError):
            r[k] = None
F = [r for r in rows if r["verdict"] == "ok" and r["span_s"] == 25.0 and r["live"] and r["live"] >= 28]
ls = sorted(r["live"] for r in F)
print("  n=%d min=%.3f 中位=%.3f max=%.3f ；>31.25 的窗数=%d ；>32 的=%d" % (
    len(ls), ls[0], statistics.median(ls), ls[-1], sum(1 for x in ls if x > 31.25), sum(1 for x in ls if x > 32)))
print("  中位对应帧时 %.3f ms ；1000/32=%.4f ms ；max 对应 %.3f ms" % (
    1000 / statistics.median(ls), 1000 / 32.0, 1000 / ls[-1]))
print("  分位：%s" % ["%.2f" % ls[int(q * (len(ls) - 1))] for q in (0, .25, .5, .75, 1)])
print("  超过 31.25 帽位的窗：", sorted(set("%.2f %s" % (r["live"], r["dir"]) for r in F if r["live"] > 31.3)))

print("\n== 4) 去伪重复：趟配对级（同图 L3 + 窗负载±40）==  ")
L3 = [r for r in rows if r["verdict"] == "ok" and r["span_s"] == 25.0 and r["live"] and r["live"] > 0
      and r["units0"] and (r["map_sha256"] or "").startswith("f3bb0a4e")]
for r in L3:
    r["c_units"] = float(r["c_units"]) if r["c_units"] else None
tp = {}
for a, b in itertools.combinations(L3, 2):
    if a["dir"] == b["dir"] or a["c_units"] is None or b["c_units"] is None:
        continue
    if abs(a["c_units"] - b["c_units"]) > 40:
        continue
    ratio = max(a["live"], b["live"]) / min(a["live"], b["live"])
    same = (a["sha16"] or a["argv"]) == (b["sha16"] or b["argv"])
    key = tuple(sorted((a["dir"], b["dir"])))
    tp.setdefault(key, [0, 1 if same else 0, 0.0])
    tp[key][2] = max(tp[key][2], ratio)
samep = [v for v in tp.values() if v[1]]
crossp = [v for v in tp.values() if not v[1]]
print("  不同趟对（每对取最大倍率）：同版本 %d 对 max %.2fx | 跨版本 %d 对 max %.2fx" % (
    len(samep), max(v[2] for v in samep), len(crossp), max(v[2] for v in crossp)))
print("  >3x 的趟对：同版本 %d / 跨版本 %d" % (sum(1 for v in samep if v[2] > 3), sum(1 for v in crossp if v[2] > 3)))
a, b = sum(1 for v in crossp if v[2] > 3), sum(1 for v in crossp if v[2] <= 3)
c, d = sum(1 for v in samep if v[2] > 3), sum(1 for v in samep if v[2] <= 3)
n, r1, c1 = a + b + c + d, a + b, a + c
def P(x):
    return comb(r1, x) * comb(n - r1, c1 - x) / comb(n, c1) if 0 <= c1 - x <= n - r1 and 0 <= x <= r1 else 0.0
po = P(a)
print("  趟对级列联 [[%d,%d],[%d,%d]] 双侧 Fisher p=%.5g" % (a, b, c, d, sum(P(x) for x in range(max(0, c1-(n-r1)), min(r1, c1)+1) if P(x) <= po*(1+1e-12))))
