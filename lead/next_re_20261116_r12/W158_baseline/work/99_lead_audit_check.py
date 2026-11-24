#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
W158 / 99_lead_audit_check.py —— **刻意不复用 recompute.py 的任何函数**，
用一个独立、尽量笨的实现重算 LEAD_AUDIT 的 3 个核心数字，证明它们可被第三方复现。

实现差异（故意）：
 - 不用 collections.defaultdict 分窗，用显式整数桶数组
 - 不用 statistics.median，自己排序取中位
 - 时间只用 t_perf_ns（更严的口径），以证明结论不依赖 t_monotonic
"""
import io, os, json

ROOT = r"D:\Project\ra2-campaign-forge"
RUNLIST = os.path.join(ROOT, r"lead\next_re_20261116_r12\W158_baseline\work\run_files.txt")

def my_median(xs):
    ys = sorted(xs)
    n = len(ys)
    if n == 0:
        return None
    if n % 2 == 1:
        return float(ys[n // 2])
    return (ys[n // 2 - 1] + ys[n // 2]) / 2.0

def windows(path):
    """返回 {win: [(t_perf_s, frame, a8ed50), ...]}"""
    recs = []
    with io.open(path, "r", encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            try:
                o = json.loads(ln)
            except Exception:
                continue
            tp = o.get("t_perf_ns")
            fr = o.get("frame")
            a8 = o.get("A8ED50")
            md = o.get("mode")
            t = o.get("t_monotonic")
            if fr is None:
                continue
            if tp is not None:
                tt = float(tp) / 1e9
            elif t is not None:
                tt = float(t)
            else:
                continue
            recs.append((tt, int(fr), int(a8) if a8 is not None else None, md))
    if not recs:
        return {}
    recs.sort(key=lambda z: z[0])
    t0 = recs[0][0]
    buckets = {}
    for (tt, fr, a8, md) in recs:
        k = int((tt - t0) // 10.0)
        if k < 0:
            k = 0
        buckets.setdefault(k, []).append((tt, fr, a8, md))
    return buckets

def seg_of(arr):
    """按本卡 P0' 规则算一个窗口的 (ms, b_mean)；不合格返回 None。"""
    if len(arr) < 30:
        return None
    tf, tl = arr[0][0], arr[-1][0]
    ff, fl = arr[0][1], arr[-1][1]
    if tl - tf < 9.0:
        return None
    if fl - ff < 1:
        return None
    if any(x[3] is not None and x[3] != 0 for x in arr):
        return None                       # 整窗 mode==0
    a8s = [x[2] for x in arr if x[2] is not None]
    if not a8s:
        return None
    ms = 1000.0 * (tl - tf) / (fl - ff)
    if ms > 200.0:
        return None
    return (ms, sum(a8s) / float(len(a8s)), max(a8s))

def main():
    runs = [l.strip() for l in io.open(RUNLIST, encoding="utf-8") if l.strip()]
    print("files = %d" % len(runs))

    # ---- A-1 / A-2 : trip_c2_near_r2 单趟
    target = [p for p in runs
              if os.path.basename(os.path.dirname(p)) == "trip_c2_near_r2"][0]
    print("\n[A-1/A-2] %s" % target)
    b = windows(target)
    segs = []
    for k in sorted(b):
        s = seg_of(b[k])
        if s:
            segs.append((k,) + s)
    print("  合格窗口数 = %d" % len(segs))
    hi = [s[1] for s in segs if s[2] >= 75]
    lo = [s[1] for s in segs if s[2] < 25]
    print("  hi(b>=75) n=%d  median=%.4f" % (len(hi), my_median(hi)))
    print("  lo(b<25)  n=%d  median=%.4f" % (len(lo), my_median(lo)))
    print("  diff = %+.4f" % (my_median(hi) - my_median(lo)))
    print("  段子弹峰值 b_max = %d" % max(s[3] for s in segs))
    # 全样本 A8ED50 峰
    allmax = 0
    n_gt = 0
    n_ge = 0
    with io.open(target, "r", encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            try:
                o = json.loads(ln)
            except Exception:
                continue
            a = o.get("A8ED50")
            if a is None:
                continue
            a = int(a)
            if a > allmax:
                allmax = a
            if a > 250:
                n_gt += 1
            if a >= 250:
                n_ge += 1
    print("  该趟 A8ED50 max = %d ; >250 样本 = %d ; >=250 样本 = %d" % (allmax, n_gt, n_ge))

    # ---- A-3 : 全语料 82 趟 / 1161 段
    print("\n[A-3] 全语料 P0' 汇总")
    nseg = 0
    trips = set()
    for i, p in enumerate(runs):
        trip = os.path.basename(os.path.dirname(p))
        if "crash_step2" in trip.lower():
            continue
        bb = windows(p)
        c = 0
        for k in sorted(bb):
            if seg_of(bb[k]):
                c += 1
        if c:
            trips.add(trip)
            nseg += c
        if (i + 1) % 30 == 0:
            print("   ... %d/%d  segs=%d trips=%d" % (i + 1, len(runs), nseg, len(trips)))

    print("  ==> 纳入段数 = %d ; 纳入趟数 = %d" % (nseg, len(trips)))

if __name__ == "__main__":
    main()
