# -*- coding: utf-8 -*-
"""步骤3：窗口层复算
- ms/frame 的取值是否离散（量子化）
- 分桶中位表、线性拟合、段间相关
- 多种筛选口径的敏感性
"""
import csv
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w153_common as C

OUT = []


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


def is_crash_step2(r):
    return "crash_step2" in r["trip"]


def usable(r, min_span=9.0, require_df=True):
    if r["ms_per_frame"] is None:
        return False
    if r["span_s"] is None or r["span_s"] < min_span:
        return False
    if require_df and (r["dframe"] is None or r["dframe"] <= 0):
        return False
    if r["a8_mean"] is None:
        return False
    return True


def bucket_tab(rows, edges):
    OUT.append("  %-12s %5s %12s %12s %12s %12s" % ("桶", "n", "中位ms", "p10", "p90", "均值"))
    for lo, hi in edges:
        sel = [r for r in rows if lo <= r["a8_mean"] < hi]
        if not sel:
            OUT.append("  %-12s %5d %12s" % ("%d-%d" % (lo, hi - 1), 0, "-"))
            continue
        ms = [r["ms_per_frame"] for r in sel]
        OUT.append("  %-12s %5d %12.4f %12.4f %12.4f %12.4f" % (
            "%d-%d" % (lo, hi - 1), len(sel), C.median(ms), C.quantile(ms, 0.1),
            C.quantile(ms, 0.9), C.mean(ms)))


def main():
    rows = load_segments()
    OUT.append("=== 0. 分段总量 ===")
    OUT.append("  segments.tsv 行数=%d" % len(rows))
    trips = sorted({r["trip"] for r in rows})
    OUT.append("  涉及趟数=%d" % len(trips))

    OUT.append("")
    OUT.append("=== 1. 窗口覆盖度：span_s 与 dt_ms 的分布 ===")
    for lo, hi in [(0, 1), (1, 5), (5, 9), (9, 9.99), (9.99, 10.01), (10.01, 11), (11, 20), (20, 1e9)]:
        n = sum(1 for r in rows if r["span_s"] is not None and lo <= r["span_s"] < hi)
        OUT.append("  span in [%s,%s): n=%d" % (lo, hi, n))
    spans = [r["span_s"] for r in rows if r["span_s"] is not None]
    OUT.append("  span_s: min=%.4f 中位=%.4f max=%.4f" % (min(spans), C.median(spans), max(spans)))
    dts = [r["dt_ms"] for r in rows if r["dt_ms"] is not None]
    OUT.append("  dt_ms : min=%.3f 中位=%.3f max=%.3f" % (min(dts), C.median(dts), max(dts)))

    OUT.append("")
    OUT.append("=== 2. ms/frame 的取值离散性（量子化检查）===")
    ok = [r for r in rows if usable(r)]
    OUT.append("  合格分段（span>=9s 且 dframe>0 且 a8_mean 非空）= %d" % len(ok))
    vals = [round(r["ms_per_frame"], 2) for r in ok]
    c = Counter(vals)
    OUT.append("  不同 ms/frame 值（2 位小数）个数 = %d / %d" % (len(c), len(vals)))
    OUT.append("  最频 25 个值：")
    tot = len(vals)
    for v, n in c.most_common(25):
        OUT.append("    ms/frame=%8.2f  n=%4d (%.3f%%)" % (v, n, 100.0 * n / tot))
    OUT.append("  前 5 个值占比 = %.2f%%" % (100.0 * sum(n for _, n in c.most_common(5)) / tot))
    OUT.append("  前 20 个值占比 = %.2f%%" % (100.0 * sum(n for _, n in c.most_common(20)) / tot))

    OUT.append("")
    OUT.append("=== 3. 台账声称的离散台阶值是否真在数据里（±0.02 容差）===")
    for target in (25.30, 25.35, 32.00, 32.85, 38.70, 50.30, 50.40, 59.43, 85.33):
        n = sum(1 for v in vals if abs(v - target) <= 0.02)
        OUT.append("    %6.2f : n=%d" % (target, n))

    OUT.append("")
    OUT.append("=== 4. Δframe 是否只取偶数（窗口层）===")
    par = Counter(r["dframe"] % 2 for r in ok if r["dframe"])
    OUT.append("  dframe 奇偶: %s" % dict(par))
    dfs = [r["dframe"] for r in ok if r["dframe"]]
    OUT.append("  dframe: min=%d 中位=%d max=%d" % (min(dfs), C.median(dfs), max(dfs)))
    OUT.append("  Δframe 的取值分布（前 15）: %s" % Counter(dfs).most_common(15))

    EDGES = [(0, 25), (25, 50), (50, 75), (75, 100), (100, 125)]
    OUT.append("")
    OUT.append("=== 5a. 分桶中位（全部合格分段，含 crash_step2）n=%d ===" % len(ok))
    bucket_tab(ok, EDGES)
    clean = [r for r in ok if not is_crash_step2(r)]
    OUT.append("")
    OUT.append("=== 5b. 分桶中位（排除 crash_step2）n=%d  ← 台账口径 ===" % len(clean))
    bucket_tab(clean, EDGES)
    OUT.append("")
    OUT.append("=== 5c. 分桶中位（排除 crash_step2 且 span in [9.99,10.01]）===")
    tight = [r for r in clean if 9.99 <= r["span_s"] <= 10.01]
    OUT.append("  n=%d" % len(tight))
    bucket_tab(tight, EDGES)
    OUT.append("")
    OUT.append("=== 5d. 分桶中位（台账 §784-2 的细桶，排除 crash_step2）===")
    bucket_tab(clean, [(0, 10), (10, 20), (20, 30), (30, 40), (40, 50), (50, 60), (60, 70), (70, 80),
                       (80, 90), (90, 100), (100, 110), (110, 125), (125, 1000)])

    OUT.append("")
    OUT.append("=== 6. 线性拟合 ms = a*b + c ===")
    for name, sel in (("b>=30 (排除 crash_step2)", [r for r in clean if r["a8_mean"] >= 30]),
                      ("b>=30 (全部)", [r for r in ok if r["a8_mean"] >= 30]),
                      ("b>=30 & span tight", [r for r in tight if r["a8_mean"] >= 30]),
                      ("b>0 (全部)", [r for r in clean if r["a8_mean"] > 0])):
        xs = [r["a8_mean"] for r in sel]
        ys = [r["ms_per_frame"] for r in sel]
        a, b, rmse, n = C.ols(xs, ys)
        if a is None:
            OUT.append("  %-24s n=%d 无法拟合" % (name, n))
            continue
        OUT.append("  %-24s n=%3d  y = %.4f*x + %.3f   RMSE=%.3f" % (name, n, a, b, rmse))

    OUT.append("")
    OUT.append("=== 7. 段间相关（对所有合格分段）===")
    def corr(name, xs, ys):
        r, n = C.pearson(xs, ys)
        OUT.append("  %-40s r=%s  n=%d" % (name, ("%.4f" % r) if r is not None else "n/a", n))
    corr("r(子弹 a8_mean, ms/frame)", [x["a8_mean"] for x in clean], [x["ms_per_frame"] for x in clean])
    corr("r(scans/frame, ms/frame)", [x["scans_per_frame"] for x in clean], [x["ms_per_frame"] for x in clean])
    corr("r(scans/frame, 子弹)", [x["scans_per_frame"] for x in clean], [x["a8_mean"] for x in clean])
    corr("r(b0_mean 脏矩形, ms/frame)", [x["b0_mean"] for x in clean], [x["ms_per_frame"] for x in clean])

    txt = "\n".join(OUT)
    print(txt)
    C.write_evidence("03_windows.txt", txt)


if __name__ == "__main__":
    main()
