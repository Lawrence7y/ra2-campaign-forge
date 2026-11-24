# -*- coding: utf-8 -*-
"""V1 口径核验：fps_avg 分母到底是什么；活段 fps 是否编造口径。

零真机、只读真机数据、独立复算（不信 json 里的 stats）。
"""
import datetime
import glob
import json
import os
import statistics

TRIP = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

files = sorted(glob.glob(os.path.join(TRIP, "*", "measure_w*.json")))
files += sorted(glob.glob(os.path.join(TRIP, "measure_w*.json")))
# also check deeper nesting to prove the two-layer claim is complete
deep = sorted(glob.glob(os.path.join(TRIP, "**", "measure_w*.json"), recursive=True))

print("files(1-level+root) = %d   files(recursive **) = %d" % (len(files), len(deep)))
only_deep = sorted(set(deep) - set(files))
print("only-in-recursive: %d" % len(only_deep))
for p in only_deep[:10]:
    print("   ", os.path.relpath(p, TRIP))


def pctl(sorted_vals, q):
    """re-implement harness _measure_pctl (linear interpolation)."""
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return float(sorted_vals[0])
    idx = (len(sorted_vals) - 1) * q
    lo = int(idx)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = idx - lo
    return float(sorted_vals[lo] * (1.0 - frac) + sorted_vals[hi] * frac)


rows = []
bad = []
for p in files:
    rel = os.path.relpath(p, TRIP).replace("\\", "/")
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception as e:
        bad.append((rel, repr(e)[:120]))
        continue
    st = d.get("stats") or {}
    s = d.get("samples") or {}
    t = s.get("t") or []
    f = s.get("f") or []
    ej = d.get("frame_edges")

    # ---- independent re-derivation of frame_edges from raw samples ----
    edges_re = []
    prev = None
    for _t, _f in zip(t, f):
        fi = int(_f)
        if prev is None or fi != prev:
            edges_re.append((fi, _t))
            prev = fi
    edges_match = None
    if ej is not None:
        edges_match = (len(ej) == len(edges_re) and
                       all(int(a[0]) == b[0] and abs(float(a[1]) - b[1]) < 1e-6
                           for a, b in zip(ej, edges_re)))

    # ---- independent recomputation of harness stats ----
    span_recalc = (t[-1] - t[0]) if len(t) >= 2 else None
    logic_recalc = (int(f[-1]) - int(f[0])) if len(f) >= 2 else None
    fps_avg_recalc = (logic_recalc / span_recalc
                      if span_recalc and span_recalc > 0 and logic_recalc and logic_recalc > 0
                      else None)

    fm_ms = []
    n_multi = 0
    for (fa, ta), (fb, tb) in zip(edges_re, edges_re[1:]):
        df = fb - fa
        if df == 1:
            fm_ms.append((tb - ta) * 1000.0)
        elif df > 1:
            n_multi += 1
    fm_ms.sort()
    p50_recalc = pctl(fm_ms, 0.50)
    fps_p50_recalc = (1000.0 / p50_recalc) if p50_recalc else None

    # ---- "live segment" fps as §544 defines it: edges-only span ----
    live_fps = None
    tail_s = None
    if len(edges_re) >= 2:
        dt_e = edges_re[-1][1] - edges_re[0][1]
        if dt_e > 0:
            live_fps = (edges_re[-1][0] - edges_re[0][0]) / dt_e
        tail_s = t[-1] - edges_re[-1][1]
    elif len(edges_re) == 1:
        tail_s = t[-1] - edges_re[0][1]

    # ---- sampling gap (dt > 10 ms) over raw samples ----
    gap_sum = 0.0
    gap_n = 0
    gap_max = 0.0
    for i in range(len(t) - 1):
        dt = t[i + 1] - t[i]
        if dt > 0.010:
            gap_n += 1
            gap_sum += dt
            if dt > gap_max:
                gap_max = dt

    gate = d.get("gate") or {}
    t_abs0 = d.get("t_abs0")
    when = (datetime.datetime.fromtimestamp(t_abs0).strftime("%Y-%m-%d %H:%M:%S")
            if t_abs0 else "?")

    rows.append(dict(
        name=rel, trip=d.get("trip_id"), schema=d.get("schema"), when=when,
        verdict=d.get("verdict"), span_s_json=d.get("span_s"), settle_s=d.get("settle_s"),
        n_samples=len(t), span_recalc=span_recalc, logic_recalc=logic_recalc,
        has_edges=(ej is not None),
        edges_match=edges_match, n_edges=len(edges_re), n_multi=n_multi,
        fps_avg_json=st.get("fps_avg"), fps_avg_recalc=fps_avg_recalc,
        fps_p50_json=st.get("fps_p50"), fps_p50_recalc=fps_p50_recalc,
        frame_ms_p50_json=st.get("frame_ms_p50"), p50_ms_recalc=p50_recalc,
        live_fps=live_fps, tail_s=tail_s,
        max_stall_json=st.get("max_stall_s"), note=st.get("note"),
        units0=gate.get("units0"), pre_fps15=gate.get("pre_fps15"), gate_ok=gate.get("ok"),
        map_sha=(d.get("map_sha256") or "")[:12], gm_sha=(d.get("gamemd_sha256") or "")[:12],
        gap_s=gap_sum, gap_n=gap_n, gap_max=gap_max,
        hz_eff=st.get("hz_effective"),
    ))

print("\nread_ok = %d   read_fail = %d" % (len(rows), len(bad)))
for b in bad:
    print("   READ_FAIL", b)


def fnum(x, nd=3):
    return ("%.*f" % (nd, x)) if isinstance(x, (int, float)) else "None"


# ---------- sanity: does json fps_avg equal my independent recompute? ----------
print("\n=== [1] 口径自洽检查：json.stats.fps_avg vs 独立复算 (logic/span) ===")
worst = 0.0
worst_row = None
mism = []
for r in rows:
    a, b = r["fps_avg_json"], r["fps_avg_recalc"]
    if a is None and b is None:
        continue
    if (a is None) != (b is None):
        mism.append((r["name"], a, b))
        continue
    rel_err = abs(a - b) / max(abs(a), 1e-9)
    if rel_err > worst:
        worst, worst_row = rel_err, r["name"]
    if rel_err > 0.002:
        mism.append((r["name"], a, b))
print("max rel err = %.6f  (%s)" % (worst, worst_row))
print("mismatch>0.2%% or null-vs-number: %d" % len(mism))
for m in mism[:20]:
    print("   ", m)

print("\n=== [1b] 独立复算 edges 与 json.frame_edges 是否一致 ===")
from collections import Counter
print("  edges_match True : %d" % sum(1 for r in rows if r["edges_match"] is True))
print("  edges_match False: %d" % sum(1 for r in rows if r["edges_match"] is False))
print("  no frame_edges key: %d" % sum(1 for r in rows if not r["has_edges"]))

print("\n=== [1c] 独立复算 fps_p50 vs json ===")
p50mism = []
for r in rows:
    a, b = r["fps_p50_json"], r["fps_p50_recalc"]
    if a is None and b is None:
        continue
    if a is None or b is None or abs(a - b) / max(abs(a), 1e-9) > 0.005:
        p50mism.append((r["name"], a, b))
print("  mismatch: %d" % len(p50mism))
for m in p50mism[:20]:
    print("     ", m)

# ---------- main table ----------
print("\n=== [2] 全量表：fps_avg / live_fps / fps_p50（单位 fps；span=实测窗长） ===")
hdr = ("%-26s %-4s %6s %7s %7s %7s %8s %7s %6s %5s %6s %6s %s" %
       ("name", "w", "span", "fpsavg", "live", "p50", "tail_s", "logic",
        "units0", "nedge", "nmulti", "gap_s", "verdict"))
print(hdr)
adv = [r for r in rows if r["fps_avg_recalc"] is not None]
for r in sorted(rows, key=lambda x: (x["name"])):
    print("%-26s %6s %7s %7s %8s %7s %6s %6s %6s %5s %7s %6s %6s" % (
        r["name"][:26], r["trip"], fnum(r["span_recalc"], 2),
        fnum(r["fps_avg_json"], 2), fnum(r["live_fps"], 2), fnum(r["fps_p50_json"], 2),
        fnum(r["tail_s"], 2), r["logic_recalc"], r["units0"], r["n_edges"],
        r["n_multi"], fnum(r["gap_s"], 2), r["verdict"]))

# ---------- classifications ----------
TH = 28.0
print("\n=== [3] 阈值分类（28 fps） ===")
noadv = [r for r in rows if r["fps_avg_recalc"] is None]
print("  零推进/不可测窗 (stats.fps_avg=None 或 logic<=0): %d" % len(noadv))
print("    note 分布: %s" % Counter(r["note"] for r in noadv))

c1 = [r for r in adv if (r["fps_avg_json"] or 0) < TH and (r["fps_p50_json"] or 0) >= TH]
print("\n  ★ fps_avg<28 但 fps_p50>=28 的窗: %d" % len(c1))
for r in sorted(c1, key=lambda x: x["fps_avg_json"]):
    print("    %-26s fps_avg=%6.2f live=%6.2f p50=%6.2f tail=%6.2fs span=%5.2fs logic=%5d units0=%6s nmulti=%4d gap=%6.2fs maxstall=%6.2fs %s" % (
        r["name"], r["fps_avg_json"], r["live_fps"] or -1, r["fps_p50_json"],
        r["tail_s"] or -1, r["span_recalc"], r["logic_recalc"], r["units0"],
        r["n_multi"], r["gap_s"], r["max_stall_json"] or -1, r["trip"]))

c1b = [r for r in adv if (r["fps_avg_json"] or 0) < TH and (r["live_fps"] or 0) >= TH]
print("\n  （对照）fps_avg<28 但 live_fps>=28 的窗: %d" % len(c1b))
for r in sorted(c1b, key=lambda x: x["fps_avg_json"]):
    print("    %-26s fps_avg=%6.2f live=%6.2f p50=%6.2f tail=%6.2fs" % (
        r["name"], r["fps_avg_json"], r["live_fps"], r["fps_p50_json"] or -1, r["tail_s"] or -1))

c2 = [r for r in adv if (r["live_fps"] or 0) < TH]
print("\n  live_fps<28 的窗: %d" % len(c2))
c3 = [r for r in adv if (r["fps_p50_json"] or 0) < TH]
print("  fps_p50<28 的窗: %d" % len(c3))
for r in sorted(c3, key=lambda x: x["fps_p50_json"]):
    print("    %-26s p50=%6.2f fps_avg=%6.2f live=%6.2f tail=%6.2fs units0=%6s trip=%s" % (
        r["name"], r["fps_p50_json"], r["fps_avg_json"], r["live_fps"] or -1,
        r["tail_s"] or -1, r["units0"], r["trip"]))

c4 = [r for r in adv if (r["fps_avg_json"] or 0) >= TH]
print("\n  fps_avg>=28 的窗: %d ; 其中 p50<28 的: %d" % (len(c4), sum(1 for r in c4 if (r["fps_p50_json"] or 0) < TH)))

# ---------- structural relation: live_fps >= fps_avg always? ----------
print("\n=== [4] 结构关系：live_fps 与 fps_avg 的分母差 ===")
viol = [r for r in adv if r["live_fps"] is not None and r["live_fps"] < r["fps_avg_json"] - 1e-9]
print("  live_fps < fps_avg 的窗（应为 0，因分子同、分母只截尾）: %d" % len(viol))
for r in viol[:10]:
    print("     ", r["name"], r["fps_avg_json"], r["live_fps"], r["tail_s"])
rat = [(r["live_fps"] / r["fps_avg_json"]) for r in adv if r["live_fps"]]
rat.sort()
print("  live/fps_avg 比值: min %.3f  中位 %.3f  p90 %.3f  max %.3f  n=%d" % (
    rat[0], statistics.median(rat), rat[int(len(rat) * 0.9)], rat[-1], len(rat)))
big = [r for r in adv if r["live_fps"] and r["live_fps"] / r["fps_avg_json"] > 1.5]
print("  比值>1.5（活段比整窗快 50%% 以上）的窗: %d" % len(big))
print("  比值>2.0 的窗: %d" % sum(1 for r in adv if r["live_fps"] and r["live_fps"] / r["fps_avg_json"] > 2.0))

# head-stall check: does window start frozen? (first edge to 2nd edge time)
print("\n  头部停滞检查（首样→首个帧变化的时间）：")
head = []
for p in files:
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception:
        continue
    s = d.get("samples") or {}
    t = s.get("t") or []
    f = s.get("f") or []
    if len(t) < 3:
        continue
    # first time frame changes
    t0 = t[0]; f0 = int(f[0]); tj = None
    for i in range(1, len(t)):
        if int(f[i]) != f0:
            tj = t[i]; break
    if tj is not None:
        head.append((os.path.relpath(p, TRIP).replace("\\", "/"), tj - t0))
head.sort(key=lambda x: -x[1])
print("   窗首冻结时长 top12: ")
for nm, h in head[:12]:
    print("     %-30s %.3fs" % (nm, h))
print("   窗首冻结>2s 的窗数: %d / %d" % (sum(1 for x in head if x[1] > 2), len(head)))

# ---------- p50 vs avg disagreement: does p50 ignore stalls? ----------
print("\n=== [5] fps_p50 忽略了什么（每窗：停摆总时长 vs 窗长） ===")
print("  stall_total_s = 所有 df>1 沿间隔时间 + 尾停 + 头停（近似：span - Σ(df==1 沿间隔)）")
for r in sorted(adv, key=lambda x: (x["fps_avg_json"] or 0))[:18]:
    sum_active = 0.0
    for p2 in [None]:
        pass
    print("    %-26s fps_avg=%6.2f p50=%7s n_multi=%4d" % (r["name"], r["fps_avg_json"] or -1, fnum(r["fps_p50_json"], 2), r["n_multi"]))

# ---------- special: archive_T34/measure_w0.json ----------
print("\n=== [6] 特别核：archive_T34/measure_w0.json ===")
q = os.path.join(TRIP, "archive_T34", "measure_w0.json")
d34 = json.load(open(q, encoding="utf-8"))
s34 = d34["samples"]; t34 = s34["t"]; f34 = s34["f"]
print("  json.stats: %s" % json.dumps(d34["stats"], ensure_ascii=False))
gs = []
for i in range(len(t34) - 1):
    dt = t34[i + 1] - t34[i]
    if dt > 0.010:
        gs.append((i, dt, t34[i] - t34[0]))
print("  samples 数=%d  span=%.3fs" % (len(t34), t34[-1] - t34[0]))
print("  dt>10ms 处数=%d  累计=%.3fs  最大单次=%.3fs" % (len(gs), sum(g[1] for g in gs), max((g[1] for g in gs), default=0)))
print("  累计缺口 / span = %.1f%%" % (100 * sum(g[1] for g in gs) / (t34[-1] - t34[0])))
for i, dt, tr in gs[:40]:
    print("     idx %6d  t_rel %8.3f  dt %8.3fs   f %s -> %s" % (i, tr, dt, int(f34[i]), int(f34[i + 1])))
print("  帧号范围: %s .. %s" % (int(f34[0]), int(f34[-1])))
# per-second frame advance profile
print("  逐秒帧推进 (t_rel, f 增量):")
import collections
per = collections.Counter()
for i in range(len(t34) - 1):
    tr = int(t34[i + 1] - t34[0])
    if int(f34[i + 1]) != int(f34[i]):
        per[tr] += 1
mx = int(t34[-1] - t34[0])
print("   " + " ".join("%d:%d" % (k, per.get(k, 0)) for k in range(mx + 1)))
