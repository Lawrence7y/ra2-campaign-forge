# -*- coding: utf-8 -*-
"""V1 补充3：pre_fps15 是不是独立变量；ρ(pre_fps15, 活段fps) 是否同义反复 / 样本重复计数。"""
import glob
import json
import os

TRIP = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
files = sorted(glob.glob(os.path.join(TRIP, "*", "measure_w*.json")))
files += sorted(glob.glob(os.path.join(TRIP, "measure_w*.json")))


def rank(xs):
    idx = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(idx):
        j = i
        while j + 1 < len(idx) and xs[idx[j + 1]] == xs[idx[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            r[idx[k]] = avg
        i = j + 1
    return r


def spearman(xs, ys):
    if len(xs) < 3:
        return None, None
    rx, ry = rank(xs), rank(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    vx = sum((a - mx) ** 2 for a in rx)
    vy = sum((b - my) ** 2 for b in ry)
    return cov / (vx ** 0.5 * vy ** 0.5) if vx and vy else None, n


rows = []
for p in files:
    d = json.load(open(p, encoding="utf-8"))
    st, g = d["stats"], d.get("gate") or {}
    t = d["samples"]["t"]
    ej = d.get("frame_edges") or []
    if st.get("fps_avg") is None or len(ej) < 2:
        continue
    live_s = ej[-1][1] - ej[0][1]
    if live_s <= 0:
        continue
    live = (ej[-1][0] - ej[0][0]) / live_s
    rows.append(dict(name=os.path.relpath(p, TRIP).replace("\\", "/"), trip=d["trip_id"],
                     win=d["window"], pre=g.get("pre_fps15"), units0=g.get("units0"),
                     avg=st["fps_avg"], p50=st.get("fps_p50"), live=live, live_s=live_s,
                     gate_ok=g.get("ok")))

print("可算窗（有推进且活段>0）=%d  涉及趟=%d" % (len(rows), len(set(r["trip"] for r in rows))))
same = {}
for r in rows:
    same.setdefault(r["trip"], set()).add(r["pre"])
print("\n=== [E] 同一趟的 gate.pre_fps15 是否三个窗共用一个值 ===")
shared = sum(1 for k, v in same.items() if len(v) == 1)
print("  趟数=%d  其中 pre_fps15 在该趟所有窗完全相同: %d" % (len(same), shared))
for k, v in sorted(same.items()):
    if len(v) > 1:
        print("   差异趟:", k, sorted(x for x in v))

print("\n=== [F] ρ(pre_fps15, ·) 复算 ===")
sub = [r for r in rows if r["pre"]]
for label, key in [("live_fps", "live"), ("fps_avg", "avg"), ("fps_p50", "p50")]:
    rho, n = spearman([r["pre"] for r in sub], [r[key] for r in sub])
    print("  全窗(每窗一行) ρ(pre_fps15, %-8s) = %s  n=%d" % (label, ("%.4f" % rho) if rho else "None", n))

w0 = [r for r in sub if r["win"] == 0]
for label, key in [("live_fps", "live"), ("fps_avg", "avg"), ("fps_p50", "p50")]:
    rho, n = spearman([r["pre"] for r in w0], [r[key] for r in w0])
    print("  仅 w0（闸紧邻） ρ(pre_fps15, %-8s) = %s  n=%d" % (label, ("%.4f" % rho) if rho else "None", n))

per = {}
for r in sub:
    per.setdefault(r["trip"], []).append(r)
tp_pre, tp_live = [], []
for k, v in per.items():
    tp_pre.append(v[0]["pre"])
    tp_live.append(sum(x["live"] for x in v) / len(v))
rho, n = spearman(tp_pre, tp_live)
print("  按趟聚合（去重复计数） ρ(pre_fps15, 活段fps均值) = %s  n_趟=%d" % (("%.4f" % rho) if rho else "None", n))

print("\n=== [G] 「尾段稀释」是否影响重负载慢窗（units0 分档） ===")
for lo, hi in [(0, 300), (300, 700), (700, 1000), (1000, 1400)]:
    ss = [r for r in rows if r["units0"] is not None and lo <= r["units0"] < hi]
    fake = [r for r in ss if r["avg"] < 28 and (r["p50"] or 0) >= 28]
    slow = [r for r in ss if r["avg"] < 28]
    slowp = [r for r in ss if (r["p50"] or 0) < 28]
    print("  units0 %4d-%4d: 窗=%2d  avg<28: %2d  p50<28: %2d  「avg<28但p50>=28」=%2d  其中活段<5s: %d" % (
        lo, hi, len(ss), len(slow), len(slowp), len(fake), sum(1 for r in fake if r["live_s"] < 5)))
    for r in sorted(fake, key=lambda x: x["avg"]):
        print("      %-30s avg=%6.2f p50=%6.2f live=%6.2f live_s=%7.3f units0=%s trip=%s w%s" % (
            r["name"], r["avg"], r["p50"], r["live"], r["live_s"], r["units0"], r["trip"], r["win"]))
