# -*- coding: utf-8 -*-
"""步骤4：相关性的分层诊断（为什么台账 r=0.921，我算 0.07）
- 逐趟 r 的分布（组内相关）
- 去除趟内均值后的合并相关（去混杂）
- 找出"子弹≈0 但 ms/frame 很大"的离群段
- 台账 §784-1 的"段数>=12 的完整趟"子集复算
"""
import csv
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w153_common as C

OUT = []
EDGES = [(0, 25), (25, 50), (50, 75), (75, 100), (100, 125)]


def load_segments():
    p = os.path.join(C.EVID, "segments.tsv")
    rows = []
    with open(p, "r", encoding="utf-8") as fh:
        rd = csv.DictReader(fh, delimiter="\t")
        for r in rd:
            for k in ("win", "n_samp", "first_frame", "last_frame", "dframe", "a8_max", "a8_min", "iv_n", "iv_adv_n"):
                r[k] = None if r[k] == "" else int(r[k])
            for k in ("t_start_s", "t_end_s", "span_s", "dt_ms", "ms_per_frame", "ms_per_frame_exact10",
                      "a8_mean", "a8_med", "b0_mean", "x87_delta", "scans_per_frame", "iv_med_ms",
                      "iv_med_msperframe"):
                r[k] = None if r[k] == "" else float(r[k])
            rows.append(r)
    return rows


def usable(r, min_span=9.0):
    return (r["ms_per_frame"] is not None and r["span_s"] is not None
            and r["span_s"] >= min_span and (r["dframe"] or 0) > 0 and r["a8_mean"] is not None)


def main():
    rows = [r for r in load_segments() if usable(r)]
    clean = [r for r in rows if "crash_step2" not in r["trip"]]
    OUT.append("合格分段 n=%d（排除 crash_step2 后 n=%d），趟数=%d" %
               (len(rows), len(clean), len({r["trip"] for r in clean})))

    # ---------- A. 逐趟相关 ----------
    by = defaultdict(list)
    for r in clean:
        by[r["trip"]].append(r)
    OUT.append("")
    OUT.append("=== A. 逐趟组内 r(子弹均值, ms/frame)（>=5 段的趟）===")
    OUT.append("  %-34s %4s %10s %10s %10s" % ("trip", "n段", "r", "b范围", "ms范围"))
    rs = []
    for trip in sorted(by):
        seg = by[trip]
        if len(seg) < 5:
            continue
        r, n = C.pearson([s["a8_mean"] for s in seg], [s["ms_per_frame"] for s in seg])
        bs = [s["a8_mean"] for s in seg]
        ms = [s["ms_per_frame"] for s in seg]
        if r is not None:
            rs.append(r)
        OUT.append("  %-34s %4d %10s %10s %10s" % (
            trip[:34], n, ("%.4f" % r) if r is not None else "n/a",
            "%.1f-%.1f" % (min(bs), max(bs)), "%.1f-%.1f" % (min(ms), max(ms))))
    OUT.append("")
    OUT.append("  逐趟 r：n=%d 中位=%.4f 均值=%.4f min=%.4f max=%.4f  r>0.5 的趟数=%d" % (
        len(rs), C.median(rs), C.mean(rs), min(rs), max(rs), sum(1 for x in rs if x > 0.5)))

    # ---------- B. 组内去均值后的合并相关 ----------
    OUT.append("")
    OUT.append("=== B. 去趟内均值后的合并相关（within-trip centered）===")
    xb, yb = [], []
    for trip, seg in by.items():
        mb = C.mean([s["a8_mean"] for s in seg])
        my = C.mean([s["ms_per_frame"] for s in seg])
        for s in seg:
            xb.append(s["a8_mean"] - mb)
            yb.append(s["ms_per_frame"] - my)
    r, n = C.pearson(xb, yb)
    OUT.append("  r_centered(子弹, ms/frame) = %.4f  n=%d" % (r, n))

    # ---------- C. 离群段：子弹低但帧慢 ----------
    OUT.append("")
    OUT.append("=== C. '子弹<25 且 ms/frame>60' 的离群分段（前 40，按 ms 降序）===")
    out = [r for r in clean if r["a8_mean"] < 25 and r["ms_per_frame"] > 60]
    OUT.append("  计数 = %d / %d (%.2f%%)" % (len(out), len(clean), 100.0 * len(out) / len(clean)))
    OUT.append("  %-32s %4s %8s %8s %8s %8s %6s" % ("trip", "win", "ms/fr", "b均值", "b最大", "脏矩形", "dframe"))
    for r in sorted(out, key=lambda z: -z["ms_per_frame"])[:40]:
        OUT.append("  %-32s %4d %8.2f %8.2f %8d %8s %6d" % (
            r["trip"][:32], r["win"], r["ms_per_frame"], r["a8_mean"], r["a8_max"] or -1,
            ("%.1f" % r["b0_mean"]) if r["b0_mean"] is not None else "-", r["dframe"]))
    trips_out = Counter(r["trip"] for r in out)
    OUT.append("  按趟归并: %s" % trips_out.most_common(12))

    # ---------- D. 分桶（对这些离群段做敏感性）----------
    OUT.append("")
    OUT.append("=== D. 排除 'b<25 且 ms>60' 离群段后的分桶中位 ===")
    kept = [r for r in clean if not (r["a8_mean"] < 25 and r["ms_per_frame"] > 60)]
    OUT.append("  n=%d" % len(kept))
    for lo, hi in EDGES:
        sel = [r for r in kept if lo <= r["a8_mean"] < hi]
        ms = [r["ms_per_frame"] for r in sel]
        OUT.append("  %-10s n=%4d 中位=%8.4f p90=%8.4f" % (
            "%d-%d" % (lo, hi - 1), len(sel), C.median(ms) if ms else float("nan"),
            C.quantile(ms, 0.9) if ms else float("nan")))
    r, n = C.pearson([r["a8_mean"] for r in kept], [r["ms_per_frame"] for r in kept])
    OUT.append("  相关 r(子弹, ms/frame) = %.4f n=%d" % (r, n))

    # ---------- E. 台账 "段数>=12 的完整趟" 子集 ----------
    OUT.append("")
    OUT.append("=== E. 只取'段数>=12 的完整趟'（§784-1 口径）===")
    trips12 = {t for t, seg in by.items() if len(seg) >= 12}
    sub = [r for r in clean if r["trip"] in trips12]
    OUT.append("  趟数=%d 分段数=%d" % (len(trips12), len(sub)))
    for lo, hi in EDGES:
        sel = [r for r in sub if lo <= r["a8_mean"] < hi]
        ms = [r["ms_per_frame"] for r in sel]
        OUT.append("  %-10s n=%4d 中位=%s" % (
            "%d-%d" % (lo, hi - 1), len(sel),
            ("%.4f" % C.median(ms)) if ms else "-"))
    fit = [r for r in sub if r["a8_mean"] >= 30]
    a, b, rmse, n = C.ols([r["a8_mean"] for r in fit], [r["ms_per_frame"] for r in fit])
    OUT.append("  拟合 b>=30: y=%.4f*x+%.3f RMSE=%.3f n=%d" % (a, b, rmse, n))
    r1, n1 = C.pearson([r["a8_mean"] for r in sub], [r["ms_per_frame"] for r in sub])
    OUT.append("  r(子弹, ms/frame)=%.4f n=%d" % (r1, n1))

    # ---------- F. 每趟内"高子弹 vs 低子弹"配对 ----------
    OUT.append("")
    OUT.append("=== F. 趟内配对：同一趟里 b>=75 段 与 b<25 段 的 ms/frame ===")
    OUT.append("  %-32s %10s %10s %10s %8s" % ("trip", "高b段ms", "高b均值", "低b段ms", "差"))
    diffs = []
    for trip in sorted(by):
        seg = by[trip]
        hi = [s for s in seg if s["a8_mean"] >= 75]
        lo = [s for s in seg if s["a8_mean"] < 25]
        if not hi or not lo:
            continue
        mh = C.mean([s["ms_per_frame"] for s in hi])
        ml = C.median([s["ms_per_frame"] for s in lo])
        diffs.append(mh - ml)
        OUT.append("  %-32s %10.2f %10.1f %10.2f %8.2f" % (trip[:32], mh, C.mean([s["a8_mean"] for s in hi]), ml, mh - ml))
    if diffs:
        OUT.append("  差：n=%d 中位=%.2f 均值=%.2f min=%.2f max=%.2f  全为正? %s" % (
            len(diffs), C.median(diffs), C.mean(diffs), min(diffs), max(diffs), all(d > 0 for d in diffs)))

    txt = "\n".join(OUT)
    print(txt)
    C.write_evidence("04_corr_diag.txt", txt)


if __name__ == "__main__":
    main()
