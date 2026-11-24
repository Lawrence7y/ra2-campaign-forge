# -*- coding: utf-8 -*-
"""W162 独立审计脚本：只用 LEAD_AUDIT 三条，**不复用** recompute.py 的任何函数。

刻意写成另一套风格（先按文件切窗再全局汇总），用来验证 recompute.py 有没有实现错误。
运行：python audit.py
"""
import json, os, glob, statistics

ROOT = r"D:\Project\ra2-campaign-forge"
HERE = os.path.dirname(os.path.abspath(__file__))


def all_files():
    out = []
    for p in glob.glob(os.path.join(ROOT, "lead", "**", "run.ndjson"), recursive=True):
        if "W162_causality" in p:
            continue
        out.append(p)
    return sorted(out)


def gettime(o):
    v = o.get("t_perf_ns")
    if isinstance(v, (int, float)):
        return v * 1e-9
    v = o.get("t_mono_ns")
    if isinstance(v, (int, float)):
        return v * 1e-9
    return None


def segs(path):
    """用 dict 累积，最后一次性算，不共享 recompute.py 的 W 类。"""
    acc = {}
    acc_delta = {}
    t0 = None
    for raw in open(path, encoding="utf-8"):
        raw = raw.strip()
        if not raw:
            continue
        o = json.loads(raw)
        t = gettime(o)
        if t is None:
            continue
        if t0 is None:
            t0 = t
        k = int((t - t0) // 10.0)              # 注意：直接整除，不调 math.floor
        a = acc.get(k)
        if a is None:
            a = acc[k] = [0, t, t, None, None, [], None, None]
        a[0] += 1
        a[2] = t
        f = o.get("frame")
        if isinstance(f, (int, float)):
            if a[3] is None:
                a[3] = f
            a[4] = f
        d = o.get("win_cpu_ms_delta")
        if isinstance(d, (int, float)):
            acc_delta[k] = acc_delta.get(k, 0.0) + d
        b = o.get("A8ED50")
        if isinstance(b, (int, float)):
            a[5].append(b)
        c = o.get("win_cpu_ms")
        if isinstance(c, (int, float)):
            if a[6] is None:
                a[6] = c            # cum_first
            a[7] = c                # cum_last
    rows = []
    for k, a in acc.items():
        if a[0] < 30 or a[3] is None or a[4] is None:
            continue
        span = a[2] - a[1]
        df = a[4] - a[3]
        if span < 9.0 or df < 1 or not a[5]:
            continue
        ms = 1000.0 * span / df
        if ms > 200.0:
            continue
        cpu = None
        if a[6] is not None and a[7] is not None:
            cpu = a[7] - a[6]      # 端点差（主口径）
        else:
            cpu = acc_delta.get(k)  # 只有 delta 通道的文件
        rows.append(dict(win=k, span=span, df=df, ms=ms,
                         b=sum(a[5]) / len(a[5]), n=a[0],
                         cpu_ms=cpu if (cpu is not None and cpu > 0) else None))
    return rows


def main():
    files = all_files()
    print(f"files = {len(files)}")
    per = {}
    for p in files:
        name = os.path.basename(os.path.dirname(p))
        if "crash_step2" in name:
            continue
        per[p] = (name, segs(p))

    # ---- A-2: 分桶三表 ----
    print("\n=== A-2 分桶（独立实现）===")
    BUCK = [(0, 25), (25, 50), (50, 75), (75, 100), (100, 125)]
    allrows = [(n, r) for p, (n, rs) in per.items() for r in rs]
    print(f"合格窗 = {len(allrows)}  趟 = {len(set(n for n, _ in allrows))}")
    print(f"{'bucket':>10s} {'n':>5s} {'wall_med':>9s} {'cpu_med':>8s} {'duty_med':>9s}")
    for lo, hi in BUCK:
        g = [r for n, r in allrows if lo <= r["b"] < hi]
        gc = [r for r in g if r["cpu_ms"] is not None]
        wm = statistics.median([r["ms"] for r in g]) if g else None
        cm = statistics.median([r["cpu_ms"] / r["df"] for r in gc]) if gc else None
        dm = statistics.median([r["cpu_ms"] / (r["span"] * 1000.0) for r in gc]) if gc else None
        print(f"{lo:5d}-{hi:<4d} {len(g):5d} {wm:9.3f} {cm:8.3f} {dm:9.4f}")

    # ---- A-1: hi/lo 窗的趟内位置 ----
    print("\n=== A-1 hi/lo 窗在趟内的位置（独立实现）===")
    npair = 0
    overlap = 0
    hi_not_in_01 = []
    for p, (name, rs) in sorted(per.items()):
        h = [r["win"] for r in rs if r["b"] >= 75]
        l = [r["win"] for r in rs if r["b"] < 25]
        if not h or not l:
            continue
        npair += 1
        if not (max(h) < min(l) or max(l) < min(h)):
            overlap += 1
        if any(x > 1 for x in h):
            hi_not_in_01.append((name, sorted(h)))
        print(f"  {name:34s} hi={sorted(h)}  lo={min(l)}..{max(l)}")
    print(f"有配对趟={npair}  重叠趟={overlap}  hi 窗超出 {0,1} 的趟={hi_not_in_01}")

    # ---- A-3: range1 窗 0 ----
    print("\n=== A-3 trip_range1_r1 窗 0（独立实现）===")
    for p, (name, rs) in per.items():
        if name != "trip_range1_r1":
            continue
        r = [x for x in rs if x["win"] == 0]
        if r:
            r = r[0]
            print(f"  file = {p}")
            print(f"  win0: n={r['n']} span={r['span']:.6f} dframe={r['df']} "
                  f"ms={r['ms']:.3f} b_mean={r['b']:.4f} cpu_ms={r['cpu_ms']} "
                  f"cpu/frame={r['cpu_ms']/r['df']:.3f} "
                  f"duty={r['cpu_ms']/(r['span']*1000.0):.4f}")

    # ---- 地板 ----
    print("\n=== 地板（独立实现）===")
    v = sorted(r["ms"] for n, r in allrows)
    print(f"  n={len(v)} min={v[0]:.4f}  低于 31.5 的 = {sum(1 for x in v if x < 31.5)}")


if __name__ == "__main__":
    main()
