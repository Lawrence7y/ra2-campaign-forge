# -*- coding: utf-8 -*-
"""步骤9：最终复算（筛选阶梯）+ 与台账逐项对比
筛选阶梯（每一层都在上一层基础上加一条，规则可复述）：
  F0 基础   ：10 s 窗口、span>=9 s、Δframe>0、A8ED50 均值非空
  F1 去病态 ：排除 crash_step2（多格建筑重叠病态，§790/§794 口径）
  F2 去非游戏态：mode==0（引擎模式选择器 [0xA8B238]；mode=2 是另一种状态，实测 107 ms/帧且子弹=0）
  F3 去挂起段 ：排除 ms/frame>200 的段（trip_pressure_* 的崩溃/挂起态）
"""
import csv
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w153_common as C

OUT = []
EDGES = [(0, 25), (25, 50), (50, 75), (75, 100), (100, 125)]
LEDGER = {"0-24": 32.00, "25-49": 32.85, "50-74": 38.70, "75-99": 59.43, "100-124": 85.33}
LEDGER_N = {"0-24": 598, "25-49": 55, "50-74": 17, "75-99": 13, "100-124": 18}


def load():
    p = os.path.join(C.EVID, "segments.tsv")
    rows = []
    with open(p, "r", encoding="utf-8") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            for k in ("win", "dframe", "a8_max"):
                r[k] = None if r[k] == "" else int(r[k])
            for k in ("span_s", "ms_per_frame", "a8_mean", "b0_mean", "scans_per_frame"):
                r[k] = None if r[k] == "" else float(r[k])
            rows.append(r)
    return rows


def base(r):
    return (r["ms_per_frame"] is not None and (r["dframe"] or 0) > 0
            and (r["span_s"] or 0) >= 9.0 and r["a8_mean"] is not None)


def report(name, rows):
    OUT.append("")
    OUT.append("--- %s：分段数=%d，趟数=%d ---" % (name, len(rows), len({r["trip"] for r in rows})))
    OUT.append("  %-9s %5s %10s %10s %10s   %s" % ("桶", "n", "中位ms", "p10", "p90", "台账(中位/n)"))
    for lo, hi in EDGES:
        sel = [r for r in rows if lo <= r["a8_mean"] < hi]
        ms = [r["ms_per_frame"] for r in sel]
        key = "%d-%d" % (lo, hi - 1)
        if not ms:
            OUT.append("  %-9s %5d %10s" % (key, 0, "-"))
            continue
        OUT.append("  %-9s %5d %10.4f %10.4f %10.4f   %.2f/%d" % (
            key, len(sel), C.median(ms), C.quantile(ms, 0.1), C.quantile(ms, 0.9),
            LEDGER[key], LEDGER_N[key]))
    fit = [r for r in rows if r["a8_mean"] >= 30]
    a, b, rmse, n = C.ols([r["a8_mean"] for r in fit], [r["ms_per_frame"] for r in fit])
    if a is not None:
        OUT.append("  拟合 b>=30: y = %.4f*x + %.3f  RMSE=%.3f  n=%d   （台账 0.6496*x+7.61 RMSE10.73 n=60）" % (a, b, rmse, n))
    r1, n1 = C.pearson([r["a8_mean"] for r in rows], [r["ms_per_frame"] for r in rows])
    r2, _ = C.pearson([r["scans_per_frame"] for r in rows], [r["ms_per_frame"] for r in rows])
    r3, _ = C.pearson([r["scans_per_frame"] for r in rows], [r["a8_mean"] for r in rows])
    OUT.append("  r(子弹, ms/frame) = %.4f n=%d      （台账 0.921）" % (r1, n1))
    OUT.append("  r(scans/frame, ms/frame) = %.4f   （台账 0.442）" % r2)
    OUT.append("  r(scans/frame, 子弹) = %.4f       （台账 0.329）" % r3)
    # 逐趟配对
    by = defaultdict(list)
    for r in rows:
        by[r["trip"]].append(r)
    diffs = []
    for t, seg in by.items():
        hi = [s for s in seg if s["a8_mean"] >= 75]
        lo = [s for s in seg if s["a8_mean"] < 25]
        if hi and lo:
            diffs.append((C.mean([s["ms_per_frame"] for s in hi]) - C.median([s["ms_per_frame"] for s in lo]), t))
    if diffs:
        dv = [d for d, _ in diffs]
        OUT.append("  趟内配对(高b>=75 vs 低b<25)：趟数=%d 差中位=%+.2f ms 全为正=%s" % (
            len(dv), C.median(dv), all(x > 0 for x in dv)))


def main():
    rows = [r for r in load() if base(r)]
    OUT.append("=== 0. 基础集（F0）= %d 段 / %d 趟 ===" % (len(rows), len({r["trip"] for r in rows})))

    F0 = rows
    F1 = [r for r in rows if "crash_step2" not in r["trip"]]
    F2 = [r for r in F1 if r["trip"] in MODE0]
    F3 = [r for r in F2 if r["ms_per_frame"] <= 200]

    report("F0 基础", F0)
    report("F1 = F0 - crash_step2", F1)
    report("F2 = F1 + mode==0", F2)
    report("F3 = F2 - ms>200", F3)

    # 与台账关键交叉核对
    OUT.append("")
    OUT.append("=== 4. 与台账其它数字的交叉核对 ===")
    rng = [r for r in rows if r["trip"] == "trip_range1_r1"]
    OUT.append("  trip_range1_r1（Range 干预臂）最差窗口 ms/frame = %.2f（台账 §3.5 报 123.26）" % max(
        r["ms_per_frame"] for r in rng))
    for t in ("trip_g_idle_r1", "trip_ai_guard_r1", "trip_CTRL_C6"):
        sel = [r for r in rows if r["trip"] == t]
        if sel:
            OUT.append("  %-18s（零子弹对照）ms/frame 中位=%.2f 极差=%.2f–%.2f" % (
                t, C.median([r["ms_per_frame"] for r in sel]),
                min(r["ms_per_frame"] for r in sel), max(r["ms_per_frame"] for r in sel)))
    # 免费阈值
    OUT.append("")
    OUT.append("=== 5. 免费阈值（F2 集，2.5 发一档）===")
    for lo in range(0, 60, 5):
        sel = [r for r in F2 if lo <= r["a8_mean"] < lo + 5]
        if sel:
            ms = [r["ms_per_frame"] for r in sel]
            OUT.append("  b=%2d-%2d n=%4d 中位=%7.3f p90=%7.3f" % (lo, lo + 4, len(sel), C.median(ms), C.quantile(ms, 0.9)))

    txt = "\n".join(OUT)
    print(txt)
    C.write_evidence("09_final.txt", txt)


# 先算 mode 分类（一次小 pass，从 segments.tsv 读 mode_set 即可）
def _mode0_set():
    p = os.path.join(C.EVID, "segments.tsv")
    s = set()
    with open(p, "r", encoding="utf-8") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            if r["mode_set"] == "0":
                s.add(r["trip"])
    return s


MODE0 = _mode0_set()

if __name__ == "__main__":
    main()
