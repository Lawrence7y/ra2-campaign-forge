# -*- coding: utf-8 -*-
"""步骤10：稳健性阶梯（同一指标在不同子集下是否稳定）+ 量子化幅度
目的：区分"对口径不敏感的结论"与"对口径敏感的结论"
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w153_common as C

OUT = []
EDGES = [(0, 25), (25, 50), (50, 75), (75, 100), (100, 125)]


def load():
    p = os.path.join(C.EVID, "segments.tsv")
    rows = []
    with open(p, "r", encoding="utf-8") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            for k in ("dframe",):
                r[k] = None if r[k] == "" else int(r[k])
            for k in ("span_s", "ms_per_frame", "a8_mean", "scans_per_frame"):
                r[k] = None if r[k] == "" else float(r[k])
            rows.append(r)
    return rows


def main():
    rows = [r for r in load() if r["ms_per_frame"] and (r["dframe"] or 0) > 0
            and (r["span_s"] or 0) >= 9.0 and r["a8_mean"] is not None]
    root = lambda r: r["rel"].split(os.sep)[0]

    SUBSETS = [
        ("全部（含 crash_step2 / 含 mode=2）", lambda r: True),
        ("去 crash_step2", lambda r: "crash_step2" not in r["trip"]),
        ("去 crash_step2 + mode=0", lambda r: "crash_step2" not in r["trip"] and r["mode_set"] == "0"),
        ("去 crash_step2 + 去 _archive_*", lambda r: "crash_step2" not in r["trip"] and "_archive" not in r["rel"]),
        ("只取 r10 (W110_crash)", lambda r: root(r) == "next_re_20261112_r10"),
        ("只取 r08 (W98_clean)", lambda r: root(r) == "next_re_20261112_r08"),
        ("只取 r04/r05 (W88/W90)", lambda r: root(r) in ("next_re_20261112_r04", "next_re_20261112_r05")),
        ("只取 r02 (W13-W20)", lambda r: root(r) == "next_re_20261112_r02"),
        ("mode=0 且 span 严格 10s", lambda r: r["mode_set"] == "0" and 9.99 <= r["span_s"] <= 10.01
         and "crash_step2" not in r["trip"]),
    ]
    OUT.append("=== A. 分桶中位在各子集下的稳定性（单元格 = 中位 ms / n）===")
    hdr = "  %-36s %5s %6s" % ("子集", "趟", "段")
    for lo, hi in EDGES:
        hdr += " %16s" % ("b%d-%d" % (lo, hi - 1))
    OUT.append(hdr)
    for name, pred in SUBSETS:
        sel = [r for r in rows if pred(r)]
        line = "  %-36s %5d %6d" % (name, len({r["trip"] for r in sel}), len(sel))
        for lo, hi in EDGES:
            b = [r["ms_per_frame"] for r in sel if lo <= r["a8_mean"] < hi]
            line += " %16s" % (("%.2f/%d" % (C.median(b), len(b))) if b else "-")
        OUT.append(line)

    OUT.append("")
    OUT.append("=== B. 拟合与 r 在同一批子集下（暴露敏感性）===")
    OUT.append("  %-36s %6s %22s %9s" % ("子集", "n(b>=30)", "y = a*x + c", "r(全部)"))
    for name, pred in SUBSETS:
        sel = [r for r in rows if pred(r)]
        fit = [r for r in sel if r["a8_mean"] >= 30]
        a, b, rmse, n = C.ols([r["a8_mean"] for r in fit], [r["ms_per_frame"] for r in fit])
        r1, _ = C.pearson([r["a8_mean"] for r in sel], [r["ms_per_frame"] for r in sel])
        OUT.append("  %-36s %6d %22s %9.4f" % (
            name, n, ("%.4f*x+%.2f (R%.2f)" % (a, b, rmse)) if a else "-", r1 if r1 else float("nan")))

    OUT.append("")
    OUT.append("=== C. 窗口级 ms/frame 的量子化幅度（Δframe 取整数导致）===")
    OUT.append("  ms/frame = 1000*Δt/Δframe；Δframe ±1 ⇒ 相对误差 1/Δframe")
    OUT.append("  %10s %8s %12s %12s" % ("ms/frame", "Δframe", "±1帧的幅度", "相对"))
    for ms, df in ((32.0, 312), (32.9, 303), (38.7, 258), (59.5, 168), (85.1, 117), (88.5, 113)):
        OUT.append("  %10.2f %8d %12.3f %11.2f%%" % (ms, df, ms / df, 100.0 / df))

    OUT.append("")
    OUT.append("=== D. 与 50 ms 探针口径的对比（同一真值在两种口径下的报表值）===")
    OUT.append("  真值来自 A 表（6 ms 采样 + 10 s 窗口 + Δt/Δframe）")
    OUT.append("  %12s %16s %14s" % ("真实 ms/frame", "本卡口径(6ms/10s)", "50ms逐区间中位口径"))
    for ms in (32.03, 38.67, 59.46, 85.09):
        S = 50.4
        x = S / ms
        lo = int(x)
        frac = x - lo
        med_n = 1 if lo == 0 else (lo if (1 - frac) >= 0.5 else lo + 1)
        OUT.append("  %12.2f %16.2f %14.2f" % (ms, ms, S / med_n))

    txt = "\n".join(OUT)
    print(txt)
    C.write_evidence("10_robust.txt", txt)


if __name__ == "__main__":
    main()
