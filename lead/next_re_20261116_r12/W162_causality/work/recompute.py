# -*- coding: utf-8 -*-
"""W162 主重算：① 的因果性与混淆检验（Q1 CPU vs 墙钟 / Q2 混淆项 / Q3 台阶）。

口径（照 W158 §2.2，除时间源外不改）：
  窗口 k   = floor((t - t_趟首) / 10.0)          # 真实时间分窗
  t        = t_perf_ns/1e9 优先，缺则 t_mono_ns/1e9   # 两套 schema 都支持
  段 ms/帧 = 1000 * (t_last - t_first) / (frame_last - frame_first)
  段 子弹  = 窗内 A8ED50 均值
  CPU      = win_cpu_ms 端点差（缺则 sum(win_cpu_ms_delta)）；窗口内 [first,last]
  cpu_ms/帧 = cpu_ms / dframe
  duty     = cpu_ms / span_ms
过滤：n>=30 / span>=9.0s / dframe>=1 / ms<=200 / 趟名不含 crash_step2
      （**不用 mode 门**：见 UNKNOWNS U-2，schema A 的 mode 整趟恒 0，无过滤力）

输出：
  out/windows.tsv        每个合格窗一行（全部字段，供任何人复算）
  out/cpu_vs_wall.tsv    分桶表
  out/confounders.tsv    混淆项分布 + 趟内 hi/lo 配对
  stdout 全部分析
"""
import json, os, sys, math, collections, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = [l.strip() for l in open(os.path.join(HERE, "run_files.txt"), encoding="utf-8") if l.strip()]

WIN = 10.0
MIN_N = 30
MIN_SPAN = 9.0
MAX_MS = 200.0
BUCKETS = [(0, 25), (25, 50), (50, 75), (75, 100), (100, 125), (125, 150), (150, 200), (200, 10 ** 9)]
COUNTERS = ["B0CE88", "A8E9A0", "87E8E0", "X87E8E0", "ABCD58", "g1", "g2", "g3", "g4"]


def trip_name(p):
    d = os.path.dirname(p)
    return os.path.basename(d)


def t_of(o):
    v = o.get("t_perf_ns")
    if isinstance(v, (int, float)):
        return v / 1e9
    v = o.get("t_mono_ns")
    if isinstance(v, (int, float)):
        return v / 1e9
    return None


def med(v):
    return statistics.median(v) if v else None


class W:
    __slots__ = ("n", "t_first", "t_last", "f_first", "f_last", "b", "cpu_first",
                 "cpu_last", "cdelta", "ctr", "bmax", "bmin")

    def __init__(self):
        self.n = 0
        self.t_first = None
        self.t_last = None
        self.f_first = None
        self.f_last = None
        self.b = []
        self.bmax = None
        self.bmin = None
        self.cpu_first = None
        self.cpu_last = None
        self.cdelta = 0.0
        self.ctr = collections.defaultdict(list)


def scan_file(p):
    """返回 (windows dict, meta)"""
    windows = collections.OrderedDict()
    t0 = None
    first = {}          # meta
    have_cpu_cum = False
    have_cpu_delta = False
    modes = collections.Counter()
    tid = set()
    for line in open(p, "r", encoding="utf-8", buffering=1 << 20):
        line = line.strip()
        if not line:
            continue
        o = json.loads(line)
        t = t_of(o)
        if t is None:
            continue
        if t0 is None:
            t0 = t
        k = int(math.floor((t - t0) / WIN))
        w = windows.get(k)
        if w is None:
            w = windows[k] = W()
        w.n += 1
        if w.t_first is None:
            w.t_first = t
        w.t_last = t
        fr = o.get("frame")
        if isinstance(fr, (int, float)):
            if w.f_first is None:
                w.f_first = fr
            w.f_last = fr
        b = o.get("A8ED50")
        if isinstance(b, (int, float)):
            w.b.append(b)
            w.bmax = b if w.bmax is None else max(w.bmax, b)
            w.bmin = b if w.bmin is None else min(w.bmin, b)
        c = o.get("win_cpu_ms")
        if isinstance(c, (int, float)):
            have_cpu_cum = True
            if w.cpu_first is None:
                w.cpu_first = c
            w.cpu_last = c
        d = o.get("win_cpu_ms_delta")
        if isinstance(d, (int, float)):
            have_cpu_delta = True
            w.cdelta += d
        for name in COUNTERS:
            v = o.get(name)
            if isinstance(v, (int, float)):
                w.ctr[name].append(v)
        m = o.get("mode")
        if m is None:
            m = o.get("mode_A8B238")
        if m is not None:
            modes[m] += 1
        v = o.get("win_tid")
        if v is not None:
            tid.add(v)
    meta = dict(have_cpu_cum=have_cpu_cum, have_cpu_delta=have_cpu_delta,
                modes=dict(modes), tid=sorted(tid))
    return windows, meta


def main():
    rows = []          # 每个合格窗
    trip_meta = {}
    per_trip_cpu_total = {}
    sample_counts = collections.Counter()

    for p in FILES:
        name = trip_name(p)
        windows, meta = scan_file(p)
        trip_meta[p] = (name, meta)
        skip = "crash_step2" in name
        n_ok = 0
        for k in sorted(windows):
            w = windows[k]
            if w.n < MIN_N:
                continue
            if w.t_first is None or w.t_last is None:
                continue
            span = w.t_last - w.t_first
            if span < MIN_SPAN:
                continue
            if w.f_first is None or w.f_last is None:
                continue
            dframe = w.f_last - w.f_first
            if dframe < 1:
                continue
            ms = 1000.0 * span / dframe
            if ms > MAX_MS:
                continue
            if skip:
                continue
            # CPU
            cpu = None
            cpu_src = ""
            if w.cpu_first is not None and w.cpu_last is not None:
                cpu = w.cpu_last - w.cpu_first
                cpu_src = "cum"
            elif w.cdelta > 0:
                cpu = w.cdelta
                cpu_src = "delta"
            rec = dict(trip=name, file=p, win=k, n=w.n, span=span, dframe=int(dframe),
                       ms=ms, b_mean=sum(w.b) / len(w.b) if w.b else None,
                       b_max=w.bmax, b_min=w.bmin,
                       cpu_ms=cpu, cpu_src=cpu_src,
                       cpu_per_frame=(cpu / dframe) if cpu is not None else None,
                       duty=(cpu / (span * 1000.0)) if cpu is not None else None)
            for cn in COUNTERS:
                rec["m_" + cn] = med(w.ctr[cn]) if w.ctr[cn] else None
                rec["n_" + cn] = len(w.ctr[cn])
            rows.append(rec)
            n_ok += 1
        sample_counts[name] = n_ok
        per_trip_cpu_total[name] = (meta.get("have_cpu_cum"), meta.get("have_cpu_delta"))

    # ---------- 写出 windows.tsv ----------
    outdir = os.path.join(HERE, "out")
    os.makedirs(outdir, exist_ok=True)
    cols = ["trip", "win", "n", "span", "dframe", "ms", "b_mean", "b_max", "b_min",
            "cpu_ms", "cpu_src", "cpu_per_frame", "duty"] + \
           ["m_" + c for c in COUNTERS] + ["n_" + c for c in COUNTERS]
    with open(os.path.join(outdir, "windows.tsv"), "w", encoding="utf-8", newline="") as f:
        f.write("\t".join(cols) + "\n")
        for r in rows:
            f.write("\t".join("" if r.get(c) is None else
                              (("%.6f" % r[c]) if isinstance(r[c], float) else str(r[c]))
                              for c in cols) + "\n")

    def sect(t):
        print("\n" + "=" * 78)
        print("## " + t)
        print("=" * 78)

    sect("0 · 语料规模")
    n_with_b = sum(1 for r in rows if r["b_mean"] is not None)
    n_with_cpu = sum(1 for r in rows if r["cpu_ms"] is not None)
    print(f"合格窗 = {len(rows)}   趟 = {len(set(r['trip'] for r in rows))}")
    print(f"  有 b_mean = {n_with_b} ； 有 cpu_ms = {n_with_cpu}"
          f"（cum 源 {sum(1 for r in rows if r['cpu_src']=='cum')}，"
          f"delta 源 {sum(1 for r in rows if r['cpu_src']=='delta')}）")
    # mode 分布
    print("\n### mode 取值（schema A 的 mode / schema B 的 mode_A8B238）")
    cls = collections.Counter()
    for p, (name, meta) in trip_meta.items():
        ms_ = meta["modes"]
        if not ms_:
            cls["(无 mode 字段)"] += 1
            continue
        ks = sorted(ms_)
        if len(ks) == 1:
            cls["单值 %s（整趟恒定, n=%d 文件）" % (ks[0], 0)] += 1
        else:
            cls["多值 %s" % (ks,)] += 1
    for k, v in sorted(cls.items(), key=lambda kv: -kv[1]):
        print(f"  {v:4d} 个文件: {k}")
    print("  说明：schema A（r03–r10 的接战趟）整趟 mode=0 但帧在推进、子弹到 246 ⇒")
    print("        schema A 的 mode 与 schema B 的 mode_A8B238 语义不可互推（见 DISAGREE D-1）。")

    # ---------- Q1 分桶 ----------
    sect("Q1 · 分桶：墙钟 ms/帧 vs CPU ms/帧 vs CPU 占空比")
    print(f"{'bucket':>10s} {'n':>5s} {'n_cpu':>6s} {'wall_med':>9s} {'wall_min':>9s} "
          f"{'wall_max':>9s} {'cpu_med':>9s} {'cpu_min':>8s} {'cpu_max':>8s} "
          f"{'duty_med':>9s} {'duty_min':>9s} {'duty_max':>9s}")
    bucket_rows = []
    for lo, hi in BUCKETS:
        g = [r for r in rows if r["b_mean"] is not None and lo <= r["b_mean"] < hi]
        if not g:
            print(f"{lo:4d}-{hi:<5d} {0:>5d} {'-':>6s} {'-':>9s}")
            continue
        gc = [r for r in g if r["cpu_ms"] is not None]
        wm = [r["ms"] for r in g]
        cp = [r["cpu_per_frame"] for r in gc]
        du = [r["duty"] for r in gc]
        lbl = f"{lo}-{hi}" if hi < 10 ** 9 else f"{lo}+"
        print(f"{lbl:>10s} {len(g):5d} {len(gc):6d} {med(wm):9.3f} {min(wm):9.3f} {max(wm):9.3f} "
              + (f"{med(cp):9.3f} {min(cp):8.3f} {max(cp):8.3f} "
                 f"{med(du):9.4f} {min(du):9.4f} {max(du):9.4f}" if cp else "-"))
        bucket_rows.append((lbl, len(g), len(gc), med(wm), min(wm), max(wm),
                            med(cp), min(cp), max(cp), med(du), min(du), max(du)))

    # hi/lo 合并组
    print("\n### 合并组 lo(b<25) vs hi(b>=75) —— 墙钟 / CPU / 占空比")
    lo_g = [r for r in rows if r["b_mean"] is not None and r["b_mean"] < 25]
    hi_g = [r for r in rows if r["b_mean"] is not None and r["b_mean"] >= 75]
    for lbl, g in (("lo b<25", lo_g), ("hi b>=75", hi_g)):
        gc = [r for r in g if r["cpu_ms"] is not None]
        print(f"  {lbl:10s} n={len(g):5d} n_cpu={len(gc):4d} "
              f"wall_med={med([r['ms'] for r in g]):7.3f}  "
              f"cpu_med={med([r['cpu_per_frame'] for r in gc]):7.3f}  "
              f"duty_med={med([r['duty'] for r in gc]):6.4f}")
    dl = med([r["ms"] for r in hi_g]) - med([r["ms"] for r in lo_g]) if lo_g and hi_g else None
    dlc = (med([r["cpu_per_frame"] for r in hi_g if r["cpu_ms"] is not None])
           - med([r["cpu_per_frame"] for r in lo_g if r["cpu_ms"] is not None]))
    print(f"  Δ墙钟 = {dl:+.3f} ms/帧 ； ΔCPU = {dlc:+.3f} ms/帧"
          f" ⇒ CPU 解释墙钟增量的 {100.0*dlc/dl:.1f}%")

    # ---------- Q1 趟内配对（CPU 版） ----------
    sect("Q1b · 趟内配对（hi=b>=75 vs lo=b<25），CPU 与墙钟同时配对")
    print(f"{'trip':44s} {'n_hi':>4s} {'n_lo':>4s} {'wall_hi':>8s} {'wall_lo':>8s} "
          f"{'d_wall':>8s} {'cpu_hi':>8s} {'cpu_lo':>8s} {'d_cpu':>8s} {'duty_hi':>8s} {'duty_lo':>8s}")
    pairs = []
    by_trip = collections.defaultdict(list)
    for r in rows:
        by_trip[r["trip"]].append(r)
    for trip in sorted(by_trip):
        g = by_trip[trip]
        h = [r for r in g if r["b_mean"] is not None and r["b_mean"] >= 75]
        l = [r for r in g if r["b_mean"] is not None and r["b_mean"] < 25]
        if not h or not l:
            continue
        hc = [r for r in h if r["cpu_ms"] is not None]
        lc = [r for r in l if r["cpu_ms"] is not None]
        pairs.append(dict(trip=trip, n_hi=len(h), n_lo=len(l),
                          wall_hi=med([r["ms"] for r in h]), wall_lo=med([r["ms"] for r in l]),
                          d_wall=med([r["ms"] for r in h]) - med([r["ms"] for r in l]),
                          cpu_hi=med([r["cpu_per_frame"] for r in hc]) if hc else None,
                          cpu_lo=med([r["cpu_per_frame"] for r in lc]) if lc else None,
                          duty_hi=med([r["duty"] for r in hc]) if hc else None,
                          duty_lo=med([r["duty"] for r in lc]) if lc else None))
    for x in pairs:
        d_cpu = ((x["cpu_hi"] - x["cpu_lo"]) if x["cpu_hi"] is not None and x["cpu_lo"] is not None
                 else None)
        print(f"{x['trip']:44s} {x['n_hi']:4d} {x['n_lo']:4d} {x['wall_hi']:8.2f} {x['wall_lo']:8.2f} "
              f"{x['d_wall']:+8.2f} "
              + (f"{x['cpu_hi']:8.2f} {x['cpu_lo']:8.2f} {d_cpu:+8.2f} "
                 f"{x['duty_hi']:8.4f} {x['duty_lo']:8.4f}" if d_cpu is not None else
                 f"{'-':>8s} {'-':>8s} {'-':>8s} {'-':>8s} {'-':>8s}"))
    dw = [x["d_wall"] for x in pairs]
    dc = [x["cpu_hi"] - x["cpu_lo"] for x in pairs
          if x["cpu_hi"] is not None and x["cpu_lo"] is not None]
    print(f"\n有墙钟配对的趟 = {len(pairs)}；d_wall 正/负 = "
          f"{sum(1 for v in dw if v>0)}/{sum(1 for v in dw if v<0)}；"
          f"中位 {med(dw):+.3f}；极差 {min(dw):+.3f} ~ {max(dw):+.3f}")
    if dc:
        print(f"有 CPU 配对的趟 = {len(dc)}；d_cpu 正/负 = "
              f"{sum(1 for v in dc if v>0)}/{sum(1 for v in dc if v<0)}；"
              f"中位 {med(dc):+.3f}；极差 {min(dc):+.3f} ~ {max(dc):+.3f}")

    # ---------- 每趟 CPU 总量表（找反例） ----------
    sect("Q1c · 逐趟总览（找'子弹少但 CPU 高'的反例）")
    print(f"{'trip':44s} {'n_win':>5s} {'b_med':>7s} {'b_max':>6s} {'wall_med':>8s} "
          f"{'cpu_med':>8s} {'duty_med':>8s} {'cpu_sum_ms':>10s}")
    trip_tab = []
    for trip in sorted(by_trip):
        g = by_trip[trip]
        bs = [r["b_mean"] for r in g if r["b_mean"] is not None]
        gc = [r for r in g if r["cpu_ms"] is not None]
        bmax = max([r["b_max"] for r in g if r["b_max"] is not None] or [0])
        csum = sum(r["cpu_ms"] for r in gc) if gc else None
        trip_tab.append((trip, len(g), med(bs), bmax, med([r["ms"] for r in g]),
                         med([r["cpu_per_frame"] for r in gc]) if gc else None,
                         med([r["duty"] for r in gc]) if gc else None, csum))
    for t in sorted(trip_tab, key=lambda x: -(x[7] or -1)):
        print(f"{t[0]:44s} {t[1]:5d} {(t[2] or 0):7.1f} {t[3]:6d} {t[4]:8.2f} "
              + (f"{t[5]:8.2f} {t[6]:8.4f} {t[7]:10.1f}" if t[5] is not None else
                 f"{'-':>8s} {'-':>8s} {'-':>10s}"))

    # ---------- Q2 混淆项 ----------
    sect("Q2 · 混淆项分布（全语料样本级）")
    dist = {}
    for p in FILES:
        pass  # 已在下面单独扫
    print("（样本级分布见 EVIDENCE/03_counter_dist.txt；此处报窗内中位）")
    print(f"\n{'counter':10s} {'窗数有值':>8s} {'窗中位的中位':>12s} {'窗中位的max':>12s} {'非零窗%':>8s}")
    for cn in COUNTERS:
        key = "m_" + cn
        vals = [(r[key], r["b_mean"]) for r in rows if r[key] is not None]
        if not vals:
            print(f"{cn:10s} {'0':>8s}   —— 本语料无该字段")
            continue
        v = [x[0] for x in vals]
        nz = sum(1 for x in v if x != 0)
        print(f"{cn:10s} {len(v):8d} {med(v):12.3f} {max(v):12.3f} {100.0*nz/len(v):7.1f}%")

    sect("Q2b · 混淆项趟内配对（只比较 hi 与 lo 都有的趟）")
    print(f"{'counter':10s} {'n_trips':>7s} {'d_hi-lo 中位':>12s} {'正/负':>7s} "
          f"{'极差':>18s} {'d_wall 中位':>11s}")
    conf_rows = []
    for cn in COUNTERS:
        key = "m_" + cn
        ds = []
        for trip in sorted(by_trip):
            g = by_trip[trip]
            h = [r[key] for r in g if r["b_mean"] is not None and r["b_mean"] >= 75 and r[key] is not None]
            l = [r[key] for r in g if r["b_mean"] is not None and r["b_mean"] < 25 and r[key] is not None]
            if len(h) < 1 or len(l) < 1:
                continue
            ds.append((trip, med(h) - med(l), med(h), med(l)))
        if not ds:
            print(f"{cn:10s} {'0':>7s}   —— 无配对趟")
            continue
        dv = [x[1] for x in ds]
        dwv = [x["d_wall"] for x in pairs]
        print(f"{cn:10s} {len(ds):7d} {med(dv):12.3f} "
              f"{sum(1 for v in dv if v>0):3d}/{sum(1 for v in dv if v<0):<3d} "
              f"{min(dv):+9.3f}~{max(dv):+8.3f} {med(dwv):11.2f}")
        conf_rows.append((cn, len(ds), med(dv), sum(1 for v in dv if v > 0),
                          sum(1 for v in dv if v < 0), min(dv), max(dv)))
        for x in ds:
            print(f"      {x[0]:40s} hi_med={x[2]:10.3f} lo_med={x[3]:10.3f} d={x[1]:+10.3f}")

    # ---------- Q3 台阶 ----------
    sect("Q3 · 墙钟 ms/帧 的直方图与台阶")
    vals = [r["ms"] for r in rows]
    print(f"n={len(vals)}  min={min(vals):.4f}  med={med(vals):.4f}  max={max(vals):.4f}")
    c = collections.Counter(round(v, 2) for v in vals)
    print("\n全语料最常见 20 个值（0.01 ms 网格）：")
    for v, k in c.most_common(20):
        print(f"  {v:8.2f} ms  n={k:5d}  {100.0*k/len(vals):5.2f}%")
    # 逐值（0.1 ms 网格）
    c1 = collections.Counter(round(v, 1) for v in vals)
    print("\n0.1 ms 网格 top12：")
    for v, k in c1.most_common(12):
        print(f"  {v:8.1f} ms  n={k:5d}  {100.0*k/len(vals):5.2f}%")

    print("\n### 整数字 Δframe 网格检验")
    print("ms = 1000*span/dframe，dframe 是整数 ⇒ 取值只能落在 {1000*span/d} 的格点上。")
    print("若一档内的 dframe 只占少数几个整数，则该档的'离散'是估计器栅格，不是引擎台阶。")
    for lo, hi in BUCKETS[:5]:
        g = [r for r in rows if r["b_mean"] is not None and lo <= r["b_mean"] < hi]
        if not g:
            continue
        dfs = collections.Counter(r["dframe"] for r in g)
        print(f"  桶 {lo:3d}-{hi:<3d} n={len(g):5d}  distinct dframe={len(dfs):4d} "
              f"top5={dfs.most_common(5)}  grid_step@med={1000.0*med([r['span'] for r in g])/(med([r['dframe'] for r in g])**2):.4f} ms")

    print("\n### 基周期 P 拟合：落在 P 的整数倍 ±5% 的窗占比")
    for P in (15.625, 16.0, 16.667, 21.333, 25.20, 31.875, 32.0, 40.0, 50.4):
        k = 0
        for v in vals:
            m = round(v / P)
            if m >= 1 and abs(v - m * P) <= 0.05 * m * P:
                k += 1
        print(f"  P={P:8.3f} ms : 命中 {k:5d}/{len(vals)} = {100.0*k/len(vals):5.2f}%")

    print("\n### 25.x / 50.x 台阶是否存在于本（6 ms 采样、t_perf_ns）语料")
    for a, b in ((24.0, 26.5), (49.0, 52.0), (15.0, 17.5)):
        g = [v for v in vals if a <= v <= b]
        print(f"  ms∈[{a},{b}] : n={len(g)}  " + (f"值={sorted(set(round(x,2) for x in g))[:8]}" if g else "无"))

    print("\n### 地板：b<5 的窗的 ms/帧 分布（引擎空载）")
    g = [r for r in rows if r["b_mean"] is not None and r["b_mean"] < 5]
    if g:
        v = sorted(r["ms"] for r in g)
        print(f"  n={len(v)} min={v[0]:.4f} p10={v[len(v)//10]:.4f} med={med(v):.4f} "
              f"p90={v[9*len(v)//10]:.4f} max={v[-1]:.4f}")
        print(f"  <32.0 的窗数 = {sum(1 for x in v if x < 32.0)} ;  <31.5 的 = {sum(1 for x in v if x < 31.5)}")
        gc = [r for r in g if r["cpu_ms"] is not None]
        if gc:
            print(f"  这些窗的 duty 中位 = {med([r['duty'] for r in gc]):.4f} "
                  f"（极差 {min(r['duty'] for r in gc):.4f} ~ {max(r['duty'] for r in gc):.4f}）")

    # ---------- 写 cpu_vs_wall.tsv / confounders.tsv ----------
    CARD = os.path.dirname(HERE)          # W162_causality\（交付物放这一层）
    with open(os.path.join(CARD, "cpu_vs_wall.tsv"), "w", encoding="utf-8", newline="") as f:
        f.write("bucket\tn\tn_cpu\twall_med\twall_min\twall_max\tcpu_per_frame_med\t"
                "cpu_per_frame_min\tcpu_per_frame_max\tduty_med\tduty_min\tduty_max\n")
        for b in bucket_rows:
            f.write("\t".join("%.4f" % x if isinstance(x, float) else str(x) for x in b) + "\n")
    with open(os.path.join(CARD, "confounders.tsv"), "w", encoding="utf-8", newline="") as f:
        f.write("counter\tn_paired_trips\td_hi_minus_lo_median\tn_positive\tn_negative\t"
                "min\tmax\td_wall_median\n")
        dwv = med([x["d_wall"] for x in pairs])
        for r_ in conf_rows:
            f.write(f"{r_[0]}\t{r_[1]}\t{r_[2]:.4f}\t{r_[3]}\t{r_[4]}\t{r_[5]:.4f}\t{r_[6]:.4f}\t{dwv:.4f}\n")
    print("\n[written] out/windows.tsv cpu_vs_wall.tsv confounders.tsv")


if __name__ == "__main__":
    main()
