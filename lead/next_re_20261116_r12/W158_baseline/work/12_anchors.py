#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""W158 / 12_anchors.py —— 复核报告散文中提到的计数类断言（全部自己重算，不抄上游）。
输出 EVIDENCE/12_anchors.txt
"""
import io, os, json, collections, statistics

ROOT = r"D:\Project\ra2-campaign-forge"
CARD = os.path.join(ROOT, r"lead\next_re_20261116_r12\W158_baseline")
EVID = os.path.join(CARD, "EVIDENCE")
RUNLIST = os.path.join(CARD, "work", "run_files.txt")

def main():
    runs = [l.strip() for l in io.open(RUNLIST, encoding="utf-8") if l.strip()]
    out = io.open(os.path.join(EVID, "12_anchors.txt"), "w", encoding="utf-8", newline="\n")
    w = out.write

    gmax = None
    gmax_trip = None
    n_gt250 = 0
    n_ge250 = 0
    per_trip = {}
    hist = collections.Counter()
    tot = 0
    for p in runs:
        trip = os.path.basename(os.path.dirname(p))
        mx = None
        c250 = 0
        cge = 0
        n = 0
        with io.open(p, "r", encoding="utf-8", errors="replace") as f:
            for ln in f:
                s = ln.strip()
                if not s:
                    continue
                try:
                    o = json.loads(s)
                except Exception:
                    continue
                a = o.get("A8ED50")
                fr = o.get("frame")
                if a is None or fr is None:
                    continue
                a = int(a)
                n += 1
                tot += 1
                if mx is None or a > mx:
                    mx = a
                if a > 250:
                    c250 += 1
                    n_gt250 += 1
                if a >= 250:
                    cge += 1
                    n_ge250 += 1
                if 200 <= a <= 300:
                    hist[a] += 1
                if gmax is None or a > gmax:
                    gmax = a
                    gmax_trip = trip
        per_trip[trip] = dict(max=mx, gt250=c250, ge250=cge, n=n)

    w("总样本（有 frame 且 A8ED50 的记录）= %d\n" % tot)
    w("全局 A8ED50 最大值 = %d  出现在趟 = %s\n" % (gmax, gmax_trip))
    w("A8ED50 > 250 的样本数 = %d ; >= 250 的样本数 = %d\n" % (n_gt250, n_ge250))
    w("\n### 240..260 直方（看有没有断壁/堆叠）\n")
    for k in range(238, 262):
        if hist.get(k):
            w("  %d : %d\n" % (k, hist[k]))
    w("\n### 峰值 >= 238 的趟\n")
    w("%-40s %6s %8s %8s\n" % ("trip", "max", "gt250", "ge250"))
    hi = [(t, v) for t, v in per_trip.items() if v["max"] is not None and v["max"] >= 238]
    for t, v in sorted(hi, key=lambda z: -z[1]["max"]):
        w("%-40s %6d %8d %8d\n" % (t[:40], v["max"], v["gt250"], v["ge250"]))
    w("峰值 >= 238 的趟数 = %d\n" % len(hi))

    # 用 per_trip.tsv 做趟级统计
    pt = os.path.join(CARD, "per_trip.tsv")
    rows = []
    hdr = io.open(pt, encoding="utf-8").readline().rstrip("\n").split("\t")
    for ln in io.open(pt, encoding="utf-8").readlines()[1:]:
        p = ln.rstrip("\n").split("\t")
        if len(p) < len(hdr):
            continue
        d = dict(zip(hdr, p))
        rows.append(d)
    used0 = [r for r in rows if int(r["nseg_used"]) == 0]
    w("\n趟数 = %d ; used=0 的趟数 = %d\n" % (len(rows), len(used0)))
    w("used=0 的趟: %s\n" % ", ".join(r["trip"] for r in used0))

    zero32 = []
    for r in rows:
        if int(r["nseg_used"]) > 0 and r["b_max_seg"] not in ("", "n/a") and int(r["b_max_seg"]) == 0:
            if abs(float(r["ms_med"]) - 32.0) < 1e-6:
                zero32.append(r["trip"])
    w("\nused>0 且 b_max==0 且 ms_med 恰为 32.000 的趟数 = %d\n" % len(zero32))
    w("  %s\n" % ", ".join(zero32))

    def as_int(x):
        try:
            return int(x)
        except (TypeError, ValueError):
            return None
    nb = [r for r in rows if as_int(r["b_max_seg"]) is not None and as_int(r["b_max_seg"]) >= 238]
    w("\nper_trip 里 b_max_seg >= 238 的趟数 = %d\n" % len(nb))
    for r in nb:
        w("  %-38s b_max=%-5s ms_max=%s\n" % (r["trip"][:38], r["b_max_seg"], r["ms_max"]))

    w("\n### trip_c2_near_r2 单趟明细\n")
    v = per_trip.get("trip_c2_near_r2")
    w("  max=%s  >250 样本=%s  >=250 样本=%s  总样本=%s\n" %
      (v["max"], v["gt250"], v["ge250"], v["n"]))
    # 接战趟的 A8ED50 分布（中位 / p90 / 均值）
    for trip in ("trip_c2_near_r2", "trip_scan_near_r1", "trip_g_near_r1"):
        vals = []
        p = None
        for q in runs:
            if os.path.basename(os.path.dirname(q)) == trip:
                p = q
                break
        if not p:
            continue
        with io.open(p, "r", encoding="utf-8", errors="replace") as f:
            for ln in f:
                s = ln.strip()
                if not s:
                    continue
                try:
                    o = json.loads(s)
                except Exception:
                    continue
                if o.get("A8ED50") is not None and o.get("frame") is not None:
                    vals.append(int(o["A8ED50"]))
        if vals:
            ys = sorted(vals)
            def qq(pp):
                k = (len(ys) - 1) * pp
                lo, hi_ = int(k // 1), int(min(len(ys) - 1, int(k) + 1))
                return ys[lo] + (ys[hi_] - ys[lo]) * (k - lo)
            w("  %-24s n=%-6d median=%-5.1f p90=%-5.1f mean=%-6.2f max=%d\n" %
              (trip, len(ys), statistics.median(ys), qq(0.90),
               sum(ys) / len(ys), max(ys)))
    out.close()
    print("wrote 12_anchors.txt")

if __name__ == "__main__":
    main()
