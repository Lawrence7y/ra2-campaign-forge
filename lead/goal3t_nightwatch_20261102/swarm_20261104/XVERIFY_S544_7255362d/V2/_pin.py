# -*- coding: utf-8 -*-
"""V2 补充：(1) 定位 §544 的 ρ=0.8925 出自哪个样本池；(2) 负载代理比较；
(3) 31.25 帽位；(4) 快慢组合物构成对照。"""
import csv
import json
import math
import os
import statistics
from collections import defaultdict

ROOT = r"D:\Project\ra2-campaign-forge"
TRIPS = ROOT + r"\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
OUT = os.path.dirname(os.path.abspath(__file__))


def ff(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    dx = math.sqrt(sum((a - mx) ** 2 for a in xs))
    dy = math.sqrt(sum((b - my) ** 2 for b in ys))
    return num / (dx * dy) if dx > 0 and dy > 0 else None


def ranks(v):
    order = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r


def spearman(xs, ys):
    return pearson(ranks(xs), ranks(ys))


rows = []
with open(os.path.join(OUT, "census.csv"), encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        if r["base_tag"] != "mirror":
            continue
        for k in ("live_fps", "units0", "pre_fps15", "span_s", "fps_avg_json", "fps_p50_json", "gap_s"):
            r[k] = ff(r[k])
        r["ts"] = r["fields_ts_first"] or ""
        rows.append(r)

comp = {}
for r in rows:
    p = os.path.join(TRIPS, r["dir"], "measure_w%s.json" % r["window"]) if r["dir"] != "." \
        else os.path.join(TRIPS, "measure_w%s.json" % r["window"])
    if not os.path.exists(p):
        continue
    j = json.load(open(p, encoding="utf-8"))
    cs = j.get("counters") or []
    def mean(key):
        vals = [c.get(key) for c in cs if isinstance(c.get(key), int)]
        return sum(vals) / len(vals) if vals else None
    comp[(r["dir"], r["window"])] = {k: mean(k) for k in
                                     ("units", "infantry", "aircraft", "techno", "g", "b", "ws_kb", "pf_kb")}
for r in rows:
    c = comp.get((r["dir"], r["window"]), {})
    for k in ("units", "infantry", "techno", "g", "b", "ws_kb", "pf_kb"):
        r["c_" + k] = c.get(k)

strict = [r for r in rows if r["verdict"] == "ok" and r["span_s"] == 25.0]


def hlabel(r):
    if r["harness_sha16"]:
        return r["harness_sha16"]
    ap = r["argv_harness"] or r["harness_path"]
    return "name:" + os.path.basename(ap) if ap else "UNKNOWN"


print("=" * 110)
print("T. 定位 §544 的 ρ(pre_fps15, 活段fps)=0.8925")
print("=" * 110)
cands = {
    "严格 25s 窗 全部": strict,
    "严格 ∧ live>0 ∧ units0 非空": [r for r in strict if r["live_fps"] and r["live_fps"] > 0 and r["units0"] is not None],
    "严格 ∧ live>0 ∧ units0>0": [r for r in strict if r["live_fps"] and r["live_fps"] > 0 and (r["units0"] or 0) > 0],
    "带内 units0 1180-1360 严格窗": [r for r in strict if r["units0"] is not None and 1180 <= r["units0"] <= 1360 and r["live_fps"]],
    "带内 1180-1360 含 settle 伪窗": [r for r in rows if r["units0"] is not None and 1180 <= r["units0"] <= 1360 and r["live_fps"] and r["live_fps"] > 0],
    "units0>=800 严格窗": [r for r in strict if (r["units0"] or 0) >= 800 and r["live_fps"]],
    "units0>=800 全部可算": [r for r in rows if (r["units0"] or 0) >= 800 and r["live_fps"] and r["live_fps"] > 0],
    "L3 图 f3bb0a4e 严格窗": [r for r in strict if (r["map_sha256"] or "").startswith("f3bb0a4e") and r["live_fps"]],
    "趟级（严格窗，趟中位 live）": None,
}
for name, pl in cands.items():
    if pl is None:
        tr = defaultdict(list)
        for r in strict:
            if r["live_fps"] and r["live_fps"] > 0 and r["units0"] is not None and r["pre_fps15"] is not None:
                tr[r["dir"]].append(r)
        ds = sorted(tr)
        a = [tr[d][0]["pre_fps15"] for d in ds]
        b = [statistics.median([x["live_fps"] for x in tr[d]]) for d in ds]
        print("  %-34s n=%2d ρ_P=%.4f ρ_S=%.4f  ← 与 0.8925 差 %.4f" % (
            name, len(ds), pearson(a, b), spearman(a, b), abs(pearson(a, b) - 0.8925)))
        continue
    pl = [r for r in pl if r["pre_fps15"] is not None and r["live_fps"] and r["live_fps"] > 0]
    if len(pl) < 3:
        continue
    rp = pearson([r["pre_fps15"] for r in pl], [r["live_fps"] for r in pl])
    print("  %-34s n=%2d ρ_P=%.4f ρ_S=%.4f  ← 与 0.8925 差 %.4f" % (
        name, len(pl), rp, spearman([r["pre_fps15"] for r in pl], [r["live_fps"] for r in pl]),
        abs(rp - 0.8925)))

print("\n" + "=" * 110)
print("U. 负载代理谁更解释 live_fps（严格窗，live>0，units0 非空）")
print("=" * 110)
pl = [r for r in strict if r["live_fps"] and r["live_fps"] > 0 and r["units0"] is not None]
for f in ("units0", "c_units", "c_infantry", "c_techno", "c_g", "c_ws_kb", "c_pf_kb", "pre_fps15", "c_g"):
    sub = [r for r in pl if r.get(f) is not None]
    if len(set(r[f] for r in sub)) < 2:
        continue
    print("  ρ_P(%-11s, live) = %+.4f   ρ_S = %+.4f  n=%d" % (
        f, pearson([r[f] for r in sub], [r["live_fps"] for r in sub]),
        spearman([r[f] for r in sub], [r["live_fps"] for r in sub]), len(sub)))
# 对数-对数 or 1/fps 线性化（帧时 vs 负载）
sub = [r for r in pl if r["c_units"] is not None]
ms = [1000.0 / r["live_fps"] for r in sub]
print("  帧时(ms) 对 c_units：ρ_P=%+.4f ；对 units0：ρ_P=%+.4f" % (
    pearson([r["c_units"] for r in sub], ms),
    pearson([r["units0"] for r in sub], ms)))

print("\n" + "=" * 110)
print("V. 31.2-31.3 帽位：所有 live>=28 窗的 live 分布（是否卡在同一常数）")
print("=" * 110)
fast = sorted(r["live_fps"] for r in pl if r["live_fps"] >= 28)
print("  n=%d  min=%.3f max=%.3f  分位 %s" % (
    len(fast), min(fast), max(fast), [round(statistics.quantiles(fast, n=10)[i], 3) for i in range(9)] if len(fast) >= 10 else "-"))
print("  32.0 ms/帧 = %.4f fps（引擎帽）；fast 组中位 %.3f → 帧时 %.3f ms" % (
    1000 / 32.0, statistics.median(fast), 1000 / statistics.median(fast)))

print("\n" + "=" * 110)
print("W. L1 图 0add791d 上 732(10-20) / 702(10-26) vs 866-881(10-21) 的构成对照")
print("=" * 110)
for d in ("l1a_20261020", "l1_20261023e4", "l1c_20261021", "l1d_20261021", "l1e_20261021",
          "t55k_20261020", "archive_T49_u0800", "l3_20261021", "l3_20261023q", "l3_20261031hb",
          "l3_1101v3a", "l3_1101v3b", "l3_1101v4c", "l3_1101v4d", "l3_1101v4e"):
    rs = [r for r in strict if r["dir"] == d and r["live_fps"]]
    if not rs:
        continue
    r = sorted(rs, key=lambda x: int(x["window"]))[0]
    print("  %-18s %-10s units0=%-5d live=%6.2f harness=%-22s c_units=%-7.1f inf=%-6.1f tech=%-7.1f g=%-7.1f 每单位步=%s 载体图=%s" % (
        d, r["ts"][:10], r["units0"], statistics.median([x["live_fps"] for x in rs]),
        hlabel(r)[:22], r["c_units"], r["c_infantry"], r["c_techno"], r["c_g"],
        round(r["c_infantry"] / r["c_units"], 3) if r["c_units"] else "-",
        (r["map_sha256"] or "")[:10]))

print("\n  同一 L1 图 (0add791d) 上按窗内均值负载排序：")
sub = [r for r in strict if (r["map_sha256"] or "").startswith("0add791d") and r["live_fps"] and r["c_units"]]
seen = set()
for r in sorted(sub, key=lambda x: x["c_units"]):
    if r["dir"] in seen:
        continue
    seen.add(r["dir"])
    ls = [x["live_fps"] for x in strict if x["dir"] == r["dir"] and x["live_fps"]]
    print("     %-18s %-10s c_units=%-7.1f inf=%-6.1f tech=%-7.1f live中位=%6.2f harness=%s" % (
        r["dir"], r["ts"][:10], r["c_units"], r["c_infantry"], r["c_techno"],
        statistics.median(ls), hlabel(r)[:22]))
print("\n  同一 L3 图 (f3bb0a4e) 上按窗内均值负载排序：")
sub = [r for r in strict if (r["map_sha256"] or "").startswith("f3bb0a4e") and r["live_fps"] and r["c_units"]]
seen = set()
for r in sorted(sub, key=lambda x: x["c_units"]):
    if r["dir"] in seen:
        continue
    seen.add(r["dir"])
    ls = [x["live_fps"] for x in strict if x["dir"] == r["dir"] and x["live_fps"]]
    print("     %-18s %-10s c_units=%-7.1f inf=%-6.1f tech=%-7.1f live中位=%6.2f harness=%-22s sf=%s" % (
        r["dir"], r["ts"][:10], r["c_units"], r["c_infantry"], r["c_techno"],
        statistics.median(ls), hlabel(r)[:22],
        "?"))

print("\n" + "=" * 110)
print("X. §544 点名的四个窗（自己算）")
print("=" * 110)
spec = [("l3_1101v4d", 11, "11-01 16:48"), ("l3_1101v4e", 11, "11-03 11:20"),
        ("l1c_20261021", 11, "10-21 19:03"), ("l3_20261031hb", 11, "10-31 20:15")]
for d, _, lab in spec:
    rs = sorted([r for r in rows if r["dir"] == d], key=lambda x: int(x["window"]))
    inband = all(1180 <= (r["units0"] or 0) <= 1360 for r in rs if r["units0"] is not None)
    print("  %-16s %-12s ts=%s units0=%-6s map=%s harness=%-22s live(逐窗)=%s  ∈1180-1360带? %s" % (
        d, lab, rs[0]["ts"][:19], int(rs[0]["units0"]) if rs[0]["units0"] is not None else "-",
        (rs[0]["map_sha256"] or "")[:12], hlabel(rs[0])[:22],
        " ".join("%.2f" % r["live_fps"] for r in rs if r["live_fps"]),
        "是" if inband else "否"))
