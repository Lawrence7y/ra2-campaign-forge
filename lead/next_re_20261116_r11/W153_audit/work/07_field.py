# -*- coding: utf-8 -*-
"""步骤7：
A) A8ED50 的语义核证（守卫/不接战 vs 贴脸接战对照；与 mode/step 的一致性；极值）
B) 饱和 ~250 是真饱和还是采样/记录上限
C) X87E8E0 的语义旁证（它是单调累加器还是别的）
"""
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w153_common as C

OUT = []


def classify(trip):
    t = trip.lower()
    if "guard" in t:
        return "guard"
    if "idle" in t or "static" in t or t.startswith("trip_c0") or "ctrl_c6" in t:
        return "idle"
    if "near" in t or "dense" in t or "close" in t or "carrier" in t or "scan" in t:
        return "near"
    if "far" in t:
        return "far"
    return "other"


def main():
    files = C.all_files()
    per_trip = {}
    a8_hist = Counter()
    max_rows = []       # (a8, trip, t_rel, mode, step)
    steps_by_class = defaultdict(Counter)
    modes_by_class = defaultdict(Counter)
    read_status = Counter()
    n_over = Counter()
    x87_first = {}

    for p in files:
        rows, meta = C.load_series(p)
        if not rows:
            continue
        t0 = rows[0]["t"]
        a8 = [r["A8ED50"] for r in rows if r["A8ED50"] is not None]
        cls = classify(meta["trip"])
        if not a8:
            continue
        mx = max(a8)
        nz = sum(1 for x in a8 if x)
        per_trip[meta["trip"]] = dict(rel=meta["rel"], cls=cls, n=len(a8), mx=mx,
                                      nz=nz, nz_pct=100.0 * nz / len(a8),
                                      mean=C.mean(a8), med=C.median(a8),
                                      p90=C.quantile(a8, 0.9),
                                      n_gt250=sum(1 for x in a8 if x > 250),
                                      n_gt258=sum(1 for x in a8 if x > 258),
                                      n_ge250=sum(1 for x in a8 if x >= 250))
        for x in a8:
            if x >= 200:
                a8_hist[x] += 1
        for r in rows:
            if r["A8ED50"] is not None and r["A8ED50"] >= 200:
                max_rows.append((r["A8ED50"], meta["trip"], round(r["t"] - t0, 3), r["mode"], r["step"]))
        for r in rows[:4000]:
            steps_by_class[cls][r["step"]] += 1
            modes_by_class[cls][r["mode"]] += 1

    # ---- A) 分类对照 ----
    OUT.append("=== A. A8ED50（子弹容器 Count）按趟分类对照 ===")
    OUT.append("  分类规则：trip 名含 guard / idle|static / near|dense|close|carrier|scan / far")
    OUT.append("  %-34s %-7s %6s %6s %8s %8s %8s %8s" % ("trip", "类别", "n", "峰值", "非零%", "均值", "中位", "p90"))
    for cls in ("guard", "idle", "far", "near", "other"):
        sel = [(t, d) for t, d in per_trip.items() if d["cls"] == cls]
        if not sel:
            continue
        OUT.append("  --- %s（%d 趟）---" % (cls, len(sel)))
        for t, d in sorted(sel)[:14]:
            OUT.append("  %-34s %-7s %6d %6d %7.2f%% %8.2f %8.1f %8.1f" % (
                t[:34], cls, d["n"], d["mx"], d["nz_pct"], d["mean"], d["med"], d["p90"]))
        OUT.append("    [%s 汇总] 峰值 max=%d 中位=%s ；非零%% 中位=%.2f%%" % (
            cls, max(d["mx"] for _, d in sel),
            ("%.1f" % C.median([d["mx"] for _, d in sel])),
            C.median([d["nz_pct"] for _, d in sel])))

    OUT.append("")
    OUT.append("=== A2. 每类的 step / mode 取值（前 4000 样本）===")
    for cls in ("guard", "idle", "far", "near", "other"):
        if cls in steps_by_class:
            OUT.append("  %-7s step=%s" % (cls, steps_by_class[cls].most_common(6)))
            OUT.append("  %-7s mode=%s" % ("", modes_by_class[cls].most_common(6)))

    # ---- B) 饱和 ----
    OUT.append("")
    OUT.append("=== B. 饱和 ~250 的核查 ===")
    allmx = [(d["mx"], t) for t, d in per_trip.items()]
    allmx.sort(reverse=True)
    OUT.append("  全部 %d 趟的 A8ED50 峰值，前 15：" % len(allmx))
    for mx, t in allmx[:15]:
        d = per_trip[t]
        OUT.append("    %-34s 峰值=%3d  ≥250的样本=%d  >250=%d  >258=%d" % (
            t[:34], mx, d["n_ge250"], d["n_gt250"], d["n_gt258"]))
    OUT.append("  全局最高 = %d" % allmx[0][0])
    OUT.append("  A8ED50>=200 的取值直方图（值:样本数）：%s" % dict(sorted(a8_hist.items())))
    tot_ge = sum(a8_hist.values())
    OUT.append("  >=200 的样本总数 = %d ; 其中 >=250 = %d ; >250 = %d" % (
        tot_ge, sum(v for k, v in a8_hist.items() if k >= 250),
        sum(v for k, v in a8_hist.items() if k > 250)))
    OUT.append("  >=250 出现在这些趟：%s" % sorted({m[1] for m in max_rows if m[0] >= 250}))
    OUT.append("  最高值样本明细（前 12）：")
    for a, t, tr, mo, st in sorted(max_rows, reverse=True)[:12]:
        OUT.append("    a8=%3d trip=%-32s t=%8.3fs mode=%s step=%s" % (a, t[:32], tr, mo, st))

    txt = "\n".join(OUT)
    print(txt)
    C.write_evidence("07_field.txt", txt)

    # per-trip 表落盘
    cols = ["trip", "cls", "n", "mx", "nz", "nz_pct", "mean", "med", "p90", "n_ge250", "n_gt250", "n_gt258", "rel"]
    p = os.path.join(C.EVID, "a8_per_trip.tsv")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write("\t".join(cols) + "\n")
        for t, d in sorted(per_trip.items()):
            fh.write("\t".join(str(d.get(c)) for c in cols) + "\n")


if __name__ == "__main__":
    main()
