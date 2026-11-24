#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
W158 / recompute.py —— ① 证据链基线「一键复跑全表」

用法（PowerShell）:
  cd D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\W158_baseline\work
  $env:PYTHONIOENCODING="utf-8"
  python recompute.py                 # 全流程：抽取 pass + 全部表格（约 2-6 分钟，读 1.3 GB）
  python recompute.py --use-cache     # 复用已有 EVIDENCE\segments.tsv，跳过抽取（秒级）
  python recompute.py --limit 5       # 只跑前 5 个文件（冒烟测试）

口径（写死，见 PERF_BASELINE_V2.md §2）:
  窗口      : win = floor((t - t_趟首样本) / 10 s)，t 用 t_monotonic（真实时间，不用样本序号）
  段 ms/帧  : 1000 * (t_last - t_first) / (frame_last - frame_first)
  段 子弹   : 该窗口内 A8ED50 的算术均值
  段保留条件: span >= 9.0 s 且 Δframe >= 1 且 n_samples >= 30
  异常段    : 段 ms/帧 > 200 视为挂起，剔除并单列
  趟纳入    : 趟名不含 crash_step2（已知重叠病态）；mode == 0（排除非局内 mode=2）

纯只读：只读 run.ndjson 与旁路 JSON，不写任何游戏文件、不碰主台账。
"""
from __future__ import print_function
import os, sys, io, json, glob, math, collections, statistics

ROOT = r"D:\Project\ra2-campaign-forge"
CARD = os.path.join(ROOT, r"lead\next_re_20261116_r12\W158_baseline")
EVID = os.path.join(CARD, "EVIDENCE")
WORK = os.path.join(CARD, "work")
RUNLIST = os.path.join(WORK, "run_files.txt")
SEG = os.path.join(EVID, "segments.tsv")
TRIPS = os.path.join(EVID, "trips.tsv")

WIN_S = 10.0          # 窗口长度（秒，真实时间）
MIN_SPAN = 9.0        # 段最小跨度（秒）
MIN_N = 30            # 段最小样本数
HANG_MS = 200.0       # 异常（挂起）阈值 ms/frame

BUCKETS = [(0, 24), (25, 49), (50, 74), (75, 99), (100, 124),
           (125, 149), (150, 199), (200, 999)]
HI_B, LO_B = 75.0, 25.0

def ensure_dirs():
    for d in (EVID, WORK):
        if not os.path.isdir(d):
            os.makedirs(d)

# ----------------------------------------------------------------------------- 文件清单
def get_run_files():
    if os.path.isfile(RUNLIST):
        with io.open(RUNLIST, "r", encoding="utf-8") as f:
            xs = [ln.strip() for ln in f if ln.strip()]
        xs = [x for x in xs if os.path.isfile(x)]
        if len(xs) == 137:
            return xs
    # 缓存不全/不存在 -> 只枚举 9 个轮次目录（全仓 os.walk 在本机极慢）
    xs = []
    lead = os.path.join(ROOT, "lead")
    for d in sorted(os.listdir(lead)):
        if not d.startswith("next_re_20261112_r"):
            continue
        base = os.path.join(lead, d)
        if not os.path.isdir(base):
            continue
        for dp, dns, fns in os.walk(base):
            if "run.ndjson" in fns:
                xs.append(os.path.join(dp, "run.ndjson"))
    xs.sort()
    with io.open(RUNLIST, "w", encoding="utf-8", newline="\n") as f:
        for x in xs:
            f.write(x + "\n")
    return xs

# ----------------------------------------------------------------------------- 单文件处理
def process(path):
    """流式读一个 run.ndjson。返回 (meta, segs, diag)。"""
    t0 = None
    f0 = None
    fprev = None
    nline = 0
    nrec = 0
    steps = collections.Counter()
    modes = collections.Counter()
    readst = collections.Counter()
    a8ec_raw_lines = 0
    a8ec_keys = set()
    n_no_tmono = 0
    t_used_perf = False
    bmax = None
    bsum = 0.0
    bn = 0
    wins = collections.defaultdict(list)   # win -> list of (t_mono, t_perf, frame, a8, mode)
    tprev = None
    dframe_hist = collections.Counter()
    tlast = None
    flast = None

    with io.open(path, "r", encoding="utf-8", errors="replace", buffering=1 << 20) as fh:
        for ln in fh:
            nline += 1
            if "A8EC" in ln:                     # 原始字节级命中计数（不依赖解析）
                a8ec_raw_lines += 1
            s = ln.strip()
            if not s:
                continue
            try:
                o = json.loads(s)
            except Exception:
                continue
            nrec += 1
            if a8ec_raw_lines:
                for k in o:
                    if k.upper().startswith("A8EC"):
                        a8ec_keys.add(k)
            steps[repr(o.get("step"))] += 1
            modes[o.get("mode")] += 1
            readst[repr(o.get("read_status"))] += 1

            t = o.get("t_monotonic")
            tp = o.get("t_perf_ns")
            fr = o.get("frame")
            a8 = o.get("A8ED50")
            md = o.get("mode")
            if fr is None:
                continue
            if t is None:
                # 6 个 W94_batchrun 文件**没有 t_monotonic 字段**，必须回落 t_perf_ns
                n_no_tmono += 1
                if tp is None:
                    continue
                t_used_perf = True
                t = float(tp) / 1e9
            else:
                t = float(t)
            fr = int(fr)
            tp = float(tp) / 1e9 if tp is not None else t
            if t0 is None:
                t0, f0 = t, fr
            if tprev is not None:
                dframe_hist[fr - fprev] += 1
            tprev, fprev = t, fr
            tlast, flast = t, fr

            if a8 is not None:
                a8 = int(a8)
                bsum += a8
                bn += 1
                if bmax is None or a8 > bmax:
                    bmax = a8
            win = int((t - t0) // WIN_S) if WIN_S > 0 else 0
            wins[win].append((t, tp, fr, a8, md))

    trip = os.path.basename(os.path.dirname(path))
    segs = []
    for win in sorted(wins):
        arr = wins[win]
        n = len(arr)
        tf, tl = arr[0][0], arr[-1][0]
        tpf, tpl = arr[0][1], arr[-1][1]
        ff, fl = arr[0][2], arr[-1][2]
        df = fl - ff
        span = tl - tf
        bs = [x[3] for x in arr if x[3] is not None]
        mds = [x[4] for x in arr]
        m2 = sum(1 for m in mds if m is not None and m != 0)
        seg = dict(trip=trip, path=path, rel=os.path.relpath(path, ROOT),
                   win=win, n=n, t_first=tf, t_last=tl,
                   f_first=ff, f_last=fl, dframe=df, span=span,
                   b_mean=(sum(bs) / float(len(bs))) if bs else None,
                   b_max=(max(bs) if bs else None),
                   b_min=(min(bs) if bs else None),
                   mode2=m2, mode_ok=(m2 == 0))
        seg["ms"] = (1000.0 * span / df) if df > 0 else None
        seg["ms_perf"] = (1000.0 * (tpl - tpf) / df) if df > 0 else None
        segs.append(seg)

    meta = dict(trip=trip, path=path, rel=os.path.relpath(path, ROOT),
                nline=nline, nrec=nrec,
                t0=t0, t_end=tlast, f0=f0, f_end=flast,
                dur=(tlast - t0) if (t0 is not None and tlast is not None) else 0.0,
                frame_span=(flast - f0) if (f0 is not None and flast is not None) else 0,
                b_max=bmax, b_mean=(bsum / bn) if bn else None, b_n=bn,
                step=steps.most_common(1)[0][0] if steps else "None",
                n_mode2=(modes.get(2) or 0),
                modes=dict((str(k), v) for k, v in modes.items()),
                readst=dict((k, v) for k, v in readst.items()),
                a8ec_raw=a8ec_raw_lines, a8ec_keys=sorted(a8ec_keys),
                n_no_tmono=n_no_tmono,
                df_hist=dict((str(k), v) for k, v in dframe_hist.items()),
                nseg=len(segs))
    return meta, segs

# ----------------------------------------------------------------------------- 写/读 segments
SEG_COLS = ["trip", "win", "n", "t_first", "t_last", "f_first", "f_last", "dframe",
            "span", "ms", "ms_perf", "b_mean", "b_max", "b_min", "mode2", "mode_ok", "rel"]

def write_segments(segs):
    with io.open(SEG, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(SEG_COLS) + "\n")
        for s in segs:
            f.write("\t".join([
                s["trip"], str(s["win"]), str(s["n"]),
                "%.6f" % s["t_first"], "%.6f" % s["t_last"],
                str(s["f_first"]), str(s["f_last"]), str(s["dframe"]),
                "%.6f" % s["span"],
                ("%.6f" % s["ms"]) if s["ms"] is not None else "",
                ("%.6f" % s["ms_perf"]) if s["ms_perf"] is not None else "",
                ("%.6f" % s["b_mean"]) if s["b_mean"] is not None else "",
                (str(s["b_max"]) if s["b_max"] is not None else ""),
                (str(s["b_min"]) if s["b_min"] is not None else ""),
                str(s["mode2"]), "1" if s["mode_ok"] else "0", s["rel"]]) + "\n")

def read_segments():
    out = []
    with io.open(SEG, "r", encoding="utf-8") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        idx = dict((c, i) for i, c in enumerate(hdr))
        for ln in f:
            p = ln.rstrip("\n").split("\t")
            if len(p) < len(hdr):
                continue
            g = lambda c: p[idx[c]]
            d = dict(trip=g("trip"), win=int(g("win")), n=int(g("n")),
                     t_first=float(g("t_first")), t_last=float(g("t_last")),
                     f_first=int(g("f_first")), f_last=int(g("f_last")),
                     dframe=int(g("dframe")), span=float(g("span")),
                     b_mean=float(g("b_mean")) if g("b_mean") else None,
                     b_max=int(g("b_max")) if g("b_max") else None,
                     b_min=int(g("b_min")) if g("b_min") else None,
                     mode2=int(g("mode2")), mode_ok=(g("mode_ok") == "1"),
                     rel=g("rel"))
            d["path"] = os.path.join(ROOT, d["rel"])
            d["ms"] = float(g("ms")) if g("ms") else None
            d["ms_perf"] = float(g("ms_perf")) if g("ms_perf") else None
            out.append(d)
    return out

# ----------------------------------------------------------------------------- 统计小工具
def med(xs):
    return statistics.median(xs) if xs else None

def q(xs, p):
    if not xs:
        return None
    ys = sorted(xs)
    k = (len(ys) - 1) * p
    lo, hi = int(math.floor(k)), int(math.ceil(k))
    if lo == hi:
        return ys[lo]
    return ys[lo] + (ys[hi] - ys[lo]) * (k - lo)

def f2(x, nd=2):
    return "n/a" if x is None else ("%.*f" % (nd, x))

# ----------------------------------------------------------------------------- 过滤器
def is_crash_step2(trip):
    return "crash_step2" in trip.lower()

def seg_ok(s, mode_strict=True, hang=HANG_MS, use_perf=False):
    v = s["ms_perf"] if use_perf else s["ms"]
    if v is None:
        return False
    if s["span"] < MIN_SPAN or s["dframe"] < 1 or s["n"] < MIN_N:
        return False
    if s["b_mean"] is None:
        return False
    if mode_strict and not s["mode_ok"]:
        return False
    if hang is not None and v > hang:
        return False
    return True

def build_set(segs, mode_strict=True, drop_crash2=True, hang=HANG_MS, use_perf=False):
    out = []
    for s in segs:
        if drop_crash2 and is_crash_step2(s["trip"]):
            continue
        if seg_ok(s, mode_strict, hang, use_perf):
            if use_perf:
                # 用 t_perf_ns 派生的 ms 替换 ms（返回副本，不改原表）
                s2 = dict(s)
                s2["ms"] = s["ms_perf"]
                out.append(s2)
            else:
                out.append(s)
    return out

# ----------------------------------------------------------------------------- 表 1 分桶
def table_buckets(base, label, out):
    w = out.write
    w("\n### %s\n" % label)
    w("n_seg=%d  n_trip=%d\n" % (len(base), len(set(s["trip"] for s in base))))
    w("%-12s %6s %10s %10s %10s %10s %10s\n" %
      ("bucket", "n", "median", "mean", "p10", "p90", "min/max"))
    for lo, hi in BUCKETS:
        xs = [s["ms"] for s in base if s["b_mean"] is not None and lo <= s["b_mean"] <= hi]
        xs = [x for x in xs if x is not None]
        if not xs:
            w("%-12s %6d %10s\n" % ("%d-%d" % (lo, hi), 0, "-"))
            continue
        w("%-12s %6d %10.4f %10.4f %10.4f %10.4f %10.2f/%10.2f\n" %
          ("%d-%d" % (lo, hi), len(xs), med(xs), sum(xs) / len(xs),
           q(xs, 0.10), q(xs, 0.90), min(xs), max(xs)))
    # 比值
    a = [s["ms"] for s in base if s["b_mean"] is not None and 0 <= s["b_mean"] <= 24]
    b = [s["ms"] for s in base if s["b_mean"] is not None and 100 <= s["b_mean"] <= 124]
    if a and b:
        w("ratio median(100-124)/median(0-24) = %.4f  (%.4f / %.4f)\n" %
          (med(b) / med(a), med(b), med(a)))
    return

# ----------------------------------------------------------------------------- 表 2 趟内配对
def table_paired(base, label, out):
    w = out.write
    by = collections.defaultdict(list)
    for s in base:
        by[s["trip"]].append(s)
    rows = []
    for trip, xs in sorted(by.items()):
        hi = [s["ms"] for s in xs if s["b_mean"] >= HI_B]
        lo = [s["ms"] for s in xs if s["b_mean"] < LO_B]
        if not hi or not lo:
            continue
        rows.append(dict(trip=trip, n_hi=len(hi), n_lo=len(lo),
                         hi=med(hi), lo=med(lo), diff=med(hi) - med(lo),
                         n_seg=len(xs)))
    w("\n### %s\n" % label)
    w("趟内配对（hi = 段 b_mean >= %.0f, lo = 段 b_mean < %.0f, 键 = 段 ms/frame 中位）\n" % (HI_B, LO_B))
    w("%-46s %5s %5s %10s %10s %10s\n" % ("trip", "n_hi", "n_lo", "med_hi", "med_lo", "diff"))
    for r in rows:
        w("%-46s %5d %5d %10.4f %10.4f %+10.4f\n" %
          (r["trip"], r["n_hi"], r["n_lo"], r["hi"], r["lo"], r["diff"]))
    ds = [r["diff"] for r in rows]
    w("\n有配对趟数 = %d\n" % len(rows))
    if ds:
        w("diff: 正值 %d / 负值 %d / 零 %d\n" %
          (sum(1 for d in ds if d > 0), sum(1 for d in ds if d < 0), sum(1 for d in ds if d == 0)))
        w("diff: median = %+.4f  mean = %+.4f  min = %+.4f  max = %+.4f\n" %
          (med(ds), sum(ds) / len(ds), min(ds), max(ds)))
        w("diff 逐值（升序）: %s\n" % ", ".join("%+.2f" % d for d in sorted(ds)))
    return rows

# ----------------------------------------------------------------------------- 表 3 逐趟
def table_per_trip(segs, out):
    w = out.write
    by = collections.defaultdict(list)
    for s in segs:
        by[s["trip"]].append(s)
    rows = []
    for trip, xs in sorted(by.items()):
        rel = xs[0]["rel"]
        used = [s for s in xs if seg_ok(s, True, HANG_MS, False)]
        allms = [s["ms"] for s in xs if s["ms"] is not None]
        ums = [s["ms"] for s in used]
        hi = [s["ms"] for s in used if s["b_mean"] >= HI_B]
        lo = [s["ms"] for s in used if s["b_mean"] < LO_B]
        bm = [s["b_mean"] for s in xs if s["b_mean"] is not None]
        bx = [s["b_max"] for s in xs if s["b_max"] is not None]
        rows.append(dict(
            trip=trip, rel=rel, nseg=len(xs), nseg_used=len(used),
            n_hang=sum(1 for s in allms if s > HANG_MS),
            n_mode2=sum(1 for s in xs if not s["mode_ok"]),
            ms_med=med(ums), ms_min=min(ums) if ums else None, ms_max=max(ums) if ums else None,
            b_med=med(bm), b_max_seg=(max(bx) if bx else None),
            n_hi=len(hi), n_lo=len(lo),
            med_hi=med(hi), med_lo=med(lo),
            diff=(med(hi) - med(lo)) if (hi and lo) else None,
            excluded_crash2=is_crash_step2(trip)))
    w("\n### 逐趟值（只列产生了窗口段的趟；used = 通过段保留条件且 mode==0 的段）\n")
    w("%-44s %5s %5s %5s %5s %10s %10s %10s %7s %7s %5s %5s %10s %10s %10s\n" %
      ("trip", "nseg", "used", "hang", "md2", "ms_med", "ms_min", "ms_max",
       "b_med", "b_max", "n_hi", "n_lo", "med_hi", "med_lo", "diff"))
    for r in rows:
        w("%-44s %5d %5d %5d %5d %10s %10s %10s %7s %7s %5d %5d %10s %10s %10s\n" % (
            r["trip"][:44], r["nseg"], r["nseg_used"], r["n_hang"], r["n_mode2"],
            f2(r["ms_med"], 3), f2(r["ms_min"], 3), f2(r["ms_max"], 3),
            f2(r["b_med"], 2), ("%d" % r["b_max_seg"]) if r["b_max_seg"] is not None else "n/a",
            r["n_hi"], r["n_lo"], f2(r["med_hi"], 3), f2(r["med_lo"], 3), f2(r["diff"], 3)))
    # TSV
    cols = ["trip", "rel", "nseg", "nseg_used", "n_hang", "n_mode2", "ms_med", "ms_min", "ms_max",
            "b_med", "b_max_seg", "n_hi", "n_lo", "med_hi", "med_lo", "diff", "excluded_crash2"]
    with io.open(os.path.join(CARD, "per_trip.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(cols) + "\n")
        for r in rows:
            f.write("\t".join(
                (("%.4f" % r[c]) if isinstance(r[c], float) else str(r[c])) for c in cols) + "\n")
    return rows

# ----------------------------------------------------------------------------- 表 4 异常段
def table_anomalies(segs, out):
    w = out.write
    w("\n### 异常段（ms/frame > %.0f，按口径视为挂起）\n" % HANG_MS)
    xs = [s for s in segs if s["ms"] is not None and s["ms"] > HANG_MS]
    w("count = %d\n" % len(xs))
    w("%-46s %4s %8s %8s %10s %8s %6s\n" % ("trip", "win", "n", "dframe", "ms", "span", "b_mean"))
    for s in sorted(xs, key=lambda z: -(z["ms"] or 0)):
        w("%-46s %4d %8d %8d %10.3f %8.3f %6s\n" %
          (s["trip"][:46], s["win"], s["n"], s["dframe"], s["ms"], s["span"], f2(s["b_mean"], 2)))
    return xs

# ----------------------------------------------------------------------------- 表 5 mode=2 段
def table_mode2(segs, out):
    w = out.write
    xs = [s for s in segs if not s["mode_ok"]]
    w("\n### mode != 0 的段（非局内）\n")
    w("count = %d, 涉及趟 = %d\n" % (len(xs), len(set(s["trip"] for s in xs))))
    by = collections.defaultdict(list)
    for s in xs:
        by[s["trip"]].append(s)
    for trip, ys in sorted(by.items()):
        ms = [s["ms"] for s in ys if s["ms"] is not None]
        bs = [s["b_mean"] for s in ys if s["b_mean"] is not None]
        w("  %-40s n_seg=%3d ms_range=%.2f..%.2f b_mean_range=%.2f..%.2f  %s\n" %
          (trip[:40], len(ys),
           min(ms) if ms else float('nan'), max(ms) if ms else float('nan'),
           min(bs) if bs else float('nan'), max(bs) if bs else float('nan'),
           ys[0]["rel"]))
    return xs

# ----------------------------------------------------------------------------- 表 6 量子化
def table_quantum(segs, run_files, out):
    """把 6 ms 原始序列按真实时间抽稀到 50.4 ms，比较两种口径 -> 复算压缩幅度。"""
    w = out.write
    w("\n## 量子化（50.4 ms 粗采样口径 vs 本卡 Δt/Δframe 口径）\n")
    # 选“窗口子弹均值最高”的趟（必须 6 ms 采样、有高子弹端）
    # 预扫：每个候选文件的中位采样间隔（只读前 800 行，便宜）
    by_trip = {}
    for s in segs:
        by_trip.setdefault(s["trip"], s)
    mid = {}
    for trip, s in by_trip.items():
        dts = []
        try:
            with io.open(s["path"], "r", encoding="utf-8", errors="replace") as fh:
                prev = None
                for k, ln in enumerate(fh):
                    if k > 800:
                        break
                    try:
                        o = json.loads(ln)
                    except Exception:
                        continue
                    t = o.get("t_monotonic")
                    tp = o.get("t_perf_ns")
                    # 采样率必须用 t_perf_ns 量（t_monotonic 被量化到 15.625 ms）
                    tt = (float(tp) / 1e9) if tp is not None else (float(t) if t is not None else None)
                    if tt is None:
                        continue
                    if prev is not None and tt > prev:
                        dts.append((tt - prev) * 1000.0)
                    prev = tt
        except Exception:
            continue
        mid[trip] = med(dts) if dts else None
    w("预扫中位采样间隔：可用趟 %d，其中 <=8 ms 的 %d 个\n" %
      (len([v for v in mid.values() if v]), len([v for v in mid.values() if v and v <= 8.0])))

    best = None
    for s in segs:
        if s["b_mean"] is None or s["ms"] is None:
            continue
        if s["span"] < MIN_SPAN or s["dframe"] < 1:
            continue
        md_ = mid.get(s["trip"])
        if md_ is None or md_ > 8.0:      # 只接受 6 ms 级采样
            continue
        if best is None or s["b_mean"] > best["b_mean"]:
            best = s
    if best is None:
        w("找不到候选段\n")
        return
    trip, path = best["trip"], best["path"]
    w("样本趟 = %s（该趟 b_mean 最高段 = win%d, b=%.2f, ms=%.3f）\n%s\n" %
      (trip, best["win"], best["b_mean"], best["ms"], path))

    rows = []
    with io.open(path, "r", encoding="utf-8", errors="replace", buffering=1 << 20) as fh:
        for ln in fh:
            s = ln.strip()
            if not s:
                continue
            try:
                o = json.loads(s)
            except Exception:
                continue
            t, tp, fr, a8 = o.get("t_monotonic"), o.get("t_perf_ns"), o.get("frame"), o.get("A8ED50")
            if fr is None:
                continue
            if t is None and tp is None:
                continue
            tt = float(tp) / 1e9 if t is None else float(t)
            rows.append((tt, float(fr), int(a8) if a8 is not None else 0))
    if not rows:
        w("空文件\n")
        return
    rows.sort(key=lambda z: z[0])
    t0 = rows[0][0]
    dt = [rows[i + 1][0] - rows[i][0] for i in range(min(2000, len(rows) - 1))]
    med_dt = med([d * 1000.0 for d in dt if d > 0])
    w("样本数 = %d  中位采样间隔 = %.3f ms  跨度 = %.1f s\n" % (len(rows), med_dt, rows[-1][0] - t0))

    # 分窗（真值）
    wins = collections.defaultdict(list)
    for (t, fr, a8) in rows:
        wins[int((t - t0) // WIN_S)].append((t, fr, a8))

    PRINT = 50.4
    w("\n%-4s %10s %12s %14s %14s %10s %10s\n" %
      ("win", "n_raw", "truth", "decim_dt/df", "decim_med_int", "decim_mean", "b_mean"))
    recs = []
    for win in sorted(wins):
        arr = wins[win]
        if len(arr) < 10:
            continue
        tf, tl = arr[0][0], arr[-1][0]
        ff, fl = arr[0][1], arr[-1][1]
        if fl - ff <= 0 or (tl - tf) < MIN_SPAN:
            continue
        truth = 1000.0 * (tl - tf) / (fl - ff)
        # 抽稀：取最接近 t0 + k*PRINT 的样本
        dec = [arr[0]]
        k = 1
        target = arr[0][0] + PRINT / 1000.0
        i = 1
        while i < len(arr):
            if arr[i][0] >= target:
                dec.append(arr[i])
                k += 1
                target = arr[0][0] + k * PRINT / 1000.0
            i += 1
        if len(dec) < 3:
            continue
        # 逐区间（仅 Δframe>0 的区间）
        iv = []
        for j in range(len(dec) - 1):
            ddt = dec[j + 1][0] - dec[j][0]
            ddf = dec[j + 1][1] - dec[j][1]
            if ddf > 0:
                iv.append(1000.0 * ddt / ddf)
        if not iv:
            continue
        # 抽稀序列自己的 Δt/Δframe
        ddt = dec[-1][0] - dec[0][0]
        ddf = dec[-1][1] - dec[0][1]
        dec_tf = 1000.0 * ddt / ddf if ddf > 0 else None
        bmean = sum(x[2] for x in arr) / float(len(arr))
        recs.append(dict(win=win, n=len(arr), truth=truth, dec_tf=dec_tf,
                         dec_med=med(iv), dec_mean=sum(iv) / len(iv), b=bmean))
        w("%-4d %10d %12.3f %14s %14.3f %10.3f %10.2f\n" %
          (win, len(arr), truth, f2(dec_tf, 3), med(iv), sum(iv) / len(iv), bmean))

    # 压缩幅度
    if recs:
        w("\n压缩幅度（相对真值）：decim_med_int 口径\n")
        w("%-4s %10s %12s %12s %10s\n" % ("win", "b_mean", "truth", "dec_med_int", "err_%"))
        for r in recs:
            w("%-4d %10.2f %12.3f %12.3f %+10.1f\n" %
              (r["win"], r["b"], r["truth"], r["dec_med"], 100.0 * (r["dec_med"] - r["truth"]) / r["truth"]))
        hi = [r for r in recs if r["b"] >= 75]
        lo = [r for r in recs if r["b"] < 25]
        if hi:
            e = [100.0 * (r["dec_med"] - r["truth"]) / r["truth"] for r in hi]
            w("\nb>=75 窗（n=%d）: 误差中位 %+.1f%%  极差 %+.1f%% .. %+.1f%%\n" %
              (len(e), med(e), min(e), max(e)))
        if lo:
            e = [100.0 * (r["dec_med"] - r["truth"]) / r["truth"] for r in lo]
            w("b<25 窗（n=%d）: 误差中位 %+.1f%%  极差 %+.1f%% .. %+.1f%%\n" %
              (len(e), med(e), min(e), max(e)))

        # 动态范围压缩比
        if hi and lo:
            th = med([r["truth"] for r in hi]) if hi else None
            dh = med([r["dec_med"] for r in hi]) if hi else None
            tlow = med([r["truth"] for r in lo]) if lo else None
            dlow = med([r["dec_med"] for r in lo]) if lo else None
            if th and tlow and dlow:
                w("\n动态范围: 真值 hi/lo = %.3f / %.3f = %.3fx\n" % (th, tlow, th / tlow))
                w("          粗口径 hi/lo = %.3f / %.3f = %.3fx\n" % (dh, dlow, dh / dlow))
                w("          => 动态范围被压缩到原来的 %.1f%%\n" %
                  (100.0 * (dh / dlow) / (th / tlow)))
    return recs

# ----------------------------------------------------------------------------- 表 7 A8EC 审计
def a8ec_scan(run_files):
    """纯字节级扫描：统计 'A8EC' 子串在全部 run.ndjson 里出现多少次、在哪些文件。"""
    hits = []
    total = 0
    CH = 8 << 20
    for p in run_files:
        n = 0
        with io.open(p, "rb") as f:
            while True:
                b = f.read(CH)
                if not b:
                    break
                n += b.count(b"A8EC")
        if n:
            hits.append((os.path.relpath(p, ROOT), n))
        total += n
    return total, hits

def table_a8ec(metas, run_files, out):
    w = out.write
    w("\n## A8ECxx 键审计（W153 未证项 b）\n")
    total, hits = a8ec_scan(run_files)
    w("字节级扫描：%d 个 run.ndjson 中，子串 'A8EC' 出现 **%d** 次\n" % (len(run_files), total))
    if hits:
        for rel, n in hits[:50]:
            w("  命中 %6d 次  %s\n" % (n, rel))
    if metas:
        raw = sum(m["a8ec_raw"] for m in metas)
        keys = set()
        for m in metas:
            keys.update(m["a8ec_keys"])
        w("解析口径：含 'A8EC' 的行数 = %d ; 以 A8EC 开头的 key = %r\n" % (raw, sorted(keys)))
    if total == 0:
        w("结论: A8ECxx（含 A8EC34 = Greatest_Threat 调用计数）在全部 %d 个文件里 **0 次出现**。\n"
          % len(run_files))
    else:
        w("结论: 存在命中，需进一步定性。\n")
    return total, hits

# ----------------------------------------------------------------------------- 表 8 单位数
UNIT_KEYS = ["n_units", "n_struct", "units", "unit_count", "UnitCount", "unit_total"]

def harvest_units(run_files, out):
    """从 run.ndjson 旁的 design / BUILD / matrix JSON 里取单位数（W153 未证项 a）。"""
    import re
    from collections import Counter
    w = out.write
    w("\n## 单位数取证（W153 未证项 a）\n")
    trip_dirs = sorted(set(os.path.dirname(p) for p in run_files))
    table = {}
    scanned = 0
    for d in trip_dirs:
        trip = os.path.basename(d)
        parent = os.path.dirname(d)
        cands = []
        cands += glob.glob(os.path.join(d, "installed_inputs", "*.json"))
        cands += glob.glob(os.path.join(d, "*.json"))
        cands += glob.glob(os.path.join(parent, "inputs", "*", "*.json"))
        cands += glob.glob(os.path.join(parent, "specs", "*.json"))
        gp = os.path.dirname(parent)
        cands += glob.glob(os.path.join(gp, "matrix_*.json"))
        cands += glob.glob(os.path.join(gp, "matrices", "*.json"))
        ggp = os.path.dirname(gp)
        cands += glob.glob(os.path.join(ggp, "matrix_*.json"))
        rec = dict(trip=trip, design=None, n_units=None, n_struct=None, n_inf=None,
                   unit_scale=None, cell=None, src=None, enemy_zone=None)
        for c in sorted(set(cands)):
            try:
                if os.path.getsize(c) > 40 * 1024 * 1024:
                    continue
            except OSError:
                continue
            scanned += 1
            try:
                o = json.load(io.open(c, "r", encoding="utf-8", errors="replace"))
            except Exception:
                continue
            # (1) design 形态: missions[].units / structures / infantry
            if isinstance(o, dict) and isinstance(o.get("missions"), list):
                for m in o["missions"]:
                    if not isinstance(m, dict):
                        continue
                    un, st, inf = m.get("units"), m.get("structures"), m.get("infantry")
                    if isinstance(un, list):
                        rec["n_units"] = len(un)
                        rec["n_struct"] = len(st) if isinstance(st, list) else None
                        rec["n_inf"] = len(inf) if isinstance(inf, list) else None
                        rec["design"] = os.path.relpath(c, ROOT)
                        break
            # (2) matrix 形态: cells[].overrides.unit_scale
            #     只接受 **cell id 出现在本趟名称里** 的那一格（否则会把别人的 override 记到自己头上）
            if isinstance(o, dict) and isinstance(o.get("cells"), list):
                for cell in o["cells"]:
                    if not isinstance(cell, dict):
                        continue
                    cid = cell.get("id") or ""
                    if not cid or cid not in trip:
                        continue
                    ov = cell.get("overrides") or {}
                    rec["cell"] = cid
                    rec["src"] = os.path.relpath(c, ROOT)
                    if "unit_scale" in ov:
                        rec["unit_scale"] = ov["unit_scale"]
                    break
            # (3) BUILD 形态: design.n_units / arm.enemy_zone
            if isinstance(o, dict) and isinstance(o.get("arm"), dict):
                des = o.get("design") or {}
                if isinstance(des, dict) and des.get("n_units") is not None:
                    rec["n_units"] = des.get("n_units")
                    rec["n_struct"] = des.get("n_struct")
                    rec["src"] = os.path.relpath(c, ROOT)
                rec["enemy_zone"] = o["arm"].get("enemy_zone")
        table[trip] = rec

    w("扫描 trip 目录数 = %d，读入候选 JSON = %d 次\n" % (len(trip_dirs), scanned))
    have_u = [t for t, r in table.items() if r["n_units"] is not None]
    have_s = [t for t, r in table.items() if r["unit_scale"] is not None]
    w("拿到 **design 实际单位数组长度** 的趟 = %d / %d\n" % (len(have_u), len(trip_dirs)))
    w("拿到 **matrix unit_scale** 的趟 = %d / %d\n" % (len(have_s), len(trip_dirs)))
    w("design n_units 取值分布 = %r\n" % dict(Counter(table[t]["n_units"] for t in have_u)))
    w("design n_struct 取值分布 = %r\n" % dict(Counter(table[t]["n_struct"] for t in have_u)))
    w("unit_scale 取值分布 = %r\n" % dict(Counter(table[t]["unit_scale"] for t in have_s)))

    with io.open(os.path.join(EVID, "units_map.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("trip\tn_units\tn_struct\tn_infantry\tunit_scale\tmatrix_cell\tname_n\tdesign_json\tenemy_zone\n")
        for trip in sorted(table):
            r = table[trip]
            m = re.search(r"_n(\d+)", trip)
            f.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
                trip, r["n_units"], r["n_struct"], r["n_inf"], r["unit_scale"], r["cell"],
                m.group(1) if m else "", r["design"] or "", r["enemy_zone"] or ""))
    return table

def table_units_vs_bmax(table, per_trip_rows, out):
    import re
    w = out.write
    w("\n### b_max（趟内 A8ED50 峰值） vs 单位数\n")
    by = dict((r["trip"], r) for r in per_trip_rows)
    w("%-34s %7s %8s %8s %8s %7s %9s %8s\n" %
      ("trip", "name_n", "n_units", "n_struct", "u_scale", "b_max", "ms_med", "zone"))
    rows = []
    for trip in sorted(table):
        r = table[trip]
        p = by.get(trip)
        if p is None:
            continue
        m = re.search(r"_n(\d+)", trip)
        w("%-34s %7s %8s %8s %8s %7s %9s %8s\n" % (
            trip[:34], (m.group(1) if m else ""),
            r["n_units"] if r["n_units"] is not None else "-",
            r["n_struct"] if r["n_struct"] is not None else "-",
            r["unit_scale"] if r["unit_scale"] is not None else "-",
            ("%d" % p["b_max_seg"]) if p["b_max_seg"] is not None else "n/a",
            f2(p["ms_med"], 3), r["enemy_zone"] or "-"))
        rows.append((trip, m.group(1) if m else "", r["n_units"], r["unit_scale"],
                     p["b_max_seg"], r["enemy_zone"]))
    return rows

# ----------------------------------------------------------------------------- 表 9 稳健性
def table_robust(segs, out):
    """对窗口/样本/挂起/mode/时间源做灵敏度扫描：看五桶中位是否随口径变。"""
    w = out.write
    w("\n## 稳健性灵敏度（五桶中位 vs 口径）\n")
    w("%-58s %5s %5s %8s %8s %8s %8s %8s\n" %
      ("variant", "trip", "seg", "b0-24", "b25-49", "b50-74", "b75-99", "b100-124"))
    base = []
    for s in segs:
        if s["ms"] is None or s["b_mean"] is None:
            continue
        base.append(s)
    variants = []
    for min_n in (2, 10, 30, 100):
        for min_span in (9.0, 9.5, 10.0):
            for hang in (None, 200.0):
                for mode_strict in (True, False):
                    for use_perf in (False, True):
                        variants.append((min_n, min_span, hang, mode_strict, use_perf, True))
    seen = set()
    for (min_n, min_span, hang, mode_strict, use_perf, drop2) in variants:
        S = []
        for s in base:
            if drop2 and is_crash_step2(s["trip"]):
                continue
            v = s["ms_perf"] if use_perf else s["ms"]
            if v is None:
                continue
            if s["span"] < min_span or s["dframe"] < 1 or s["n"] < min_n:
                continue
            if mode_strict and not s["mode_ok"]:
                continue
            if hang is not None and v > hang:
                continue
            S.append((s, v))
        meds = []
        for lo, hi in BUCKETS[:5]:
            xs = [v for (s, v) in S if lo <= s["b_mean"] <= hi]
            meds.append(med(xs))
        key = tuple("%.3f" % m if m is not None else None for m in meds)
        lab = "min_n=%-3d span>=%.1f hang=%-4s mode0=%-5s t=%s" % (
            min_n, min_span, ("200" if hang else "off"), str(mode_strict), ("perf" if use_perf else "mono"))
        w("%-58s %5d %5d %8s %8s %8s %8s %8s\n" % (
            lab, len(set(s["trip"] for (s, v) in S)), len(S),
            *[f2(m, 3) for m in meds]))
        seen.add(key)
    w("\n不同的五桶中位向量个数 = %d （若为 1 则该表对口径完全不敏感）\n" % len(seen))
    return seen

# ----------------------------------------------------------------------------- main
def main():
    ensure_dirs()
    argv = sys.argv[1:]
    use_cache = "--use-cache" in argv
    limit = None
    if "--limit" in argv:
        limit = int(argv[argv.index("--limit") + 1])

    run_files = get_run_files()
    print("run.ndjson = %d" % len(run_files))
    if "--trip" in argv:
        pat = argv[argv.index("--trip") + 1]
        run_files = [p for p in run_files if pat in os.path.basename(os.path.dirname(p))]
        print("--trip %r -> %d files" % (pat, len(run_files)))
    if "--limit" in argv:
        run_files = run_files[:limit]
        print("LIMIT -> %d" % len(run_files))
    tot_bytes = sum(os.path.getsize(p) for p in run_files)
    print("total bytes = %d (%.1f MB)" % (tot_bytes, tot_bytes / 1048576.0))

    outp = os.path.join(EVID, "recompute_report.txt")
    out = io.open(outp, "w", encoding="utf-8", newline="\n")
    w = out.write

    metas = []
    segs = []
    if use_cache and os.path.isfile(SEG):
        print("--use-cache: 读 %s" % SEG)
        segs = read_segments()
    else:
        for i, p in enumerate(run_files):
            m, ss = process(p)
            metas.append(m)
            segs.extend(ss)
            if (i + 1) % 10 == 0 or i == 0:
                print("  %3d/%d  %-44s lines=%d segs=%d" %
                      (i + 1, len(run_files), m["trip"][:44], m["nline"], len(ss)), flush=True)
        write_segments(segs)

    # 元数据表
    out.write("# W158 recompute report\n")
    if metas:
        with io.open(TRIPS, "w", encoding="utf-8", newline="\n") as f:
            f.write("trip\trel\tnline\tnrec\tnseg\tdur_s\tframe_span\tb_max\tb_mean\tstep\tmode2_n\tread_status\ta8ec_raw\n")
            for m in metas:
                f.write("%s\t%s\t%d\t%d\t%d\t%.3f\t%d\t%s\t%s\t%s\t%d\t%s\t%d\n" % (
                    m["trip"], m["rel"], m["nline"], m["nrec"], m["nseg"], m["dur"],
                    m["frame_span"], m["b_max"], f2(m["b_mean"], 3), m["step"],
                    m["n_mode2"], json.dumps(m["readst"], ensure_ascii=False), m["a8ec_raw"]))
        w("总行数 = %d ; 总样本记录 = %d\n" % (sum(m["nline"] for m in metas),
                                              sum(m["nrec"] for m in metas)))
        w("总趟数 = %d ; 有有效帧推进的趟 = %d\n" %
          (len(metas), sum(1 for m in metas if m["frame_span"] > 0)))

    # ---------- 过滤器阶梯
    all_segs = segs
    F0 = [s for s in all_segs if seg_ok(s, mode_strict=False, hang=None)]
    F1 = [s for s in all_segs if seg_ok(s, mode_strict=True, hang=None)]
    F2 = build_set(all_segs, mode_strict=True, drop_crash2=True, hang=HANG_MS)
    F3 = build_set(all_segs, mode_strict=True, drop_crash2=True, hang=HANG_MS, use_perf=True)

    w("\n## 0 · 筛选阶梯\n")
    w("%-52s %6s %6s\n" % ("filter", "n_seg", "n_trip"))
    for lab, S in [("S0 全部段（无 mode 约束、无挂起剔除）", F0),
                   ("S1 + mode==0", F1),
                   ("S2 + 去 crash_step2 + 去 ms>200  [主口径 P0]", F2),
                   ("S3 = S2 但 ms 用 t_perf_ns 计算（交叉核对）", F3)]:
        w("%-52s %6d %6d\n" % (lab, len(S), len(set(s["trip"] for s in S))))

    w("\n### 时间源交叉核对（S2 vs S3 同段 ms 差）\n")
    m3 = dict(((s["trip"], s["win"]), s["ms"]) for s in F3)
    d = []
    for s in F2:
        k = (s["trip"], s["win"])
        if k in m3 and m3[k] is not None and s["ms"] is not None:
            d.append(abs(m3[k] - s["ms"]))
    if d:
        w("n=%d  |Δ| 中位 %.4f ms  最大 %.4f ms\n" % (len(d), med(d), max(d)))

    # 缺 t_monotonic 的文件（必须回落 t_perf_ns）
    if metas:
        w("\n### 缺 `t_monotonic` 字段的文件（只能回落 t_perf_ns）\n")
        miss = [m for m in metas if m.get("n_no_tmono", 0) > 0]
        w("趟数 = %d ; 这些文件里 t_monotonic 为 null 的样本 = %d\n" %
          (len(miss), sum(m.get("n_no_tmono", 0) for m in miss)))
        for m in miss:
            w("  %-40s n_null_t_monotonic=%-7d n_lines=%-7d %s\n" %
              (m["trip"][:40], m["n_no_tmono"], m["nline"], m["rel"]))

    # ---------- 表
    table_buckets(F2, "1 · 分桶中位表（主口径 P0）", out)
    table_buckets(F3, "1' · 分桶中位表（P0' = 同集合但 ms 用 t_perf_ns；建议口径）", out)
    table_buckets(F0, "1b · 分桶中位表（S0 全段，对照）", out)
    table_buckets(F1, "1c · 分桶中位表（S1 = mode0，未去挂起，对照）", out)
    rows = table_paired(F2, "2 · 趟内配对（主口径 P0）", out)
    table_paired(F3, "2' · 趟内配对（P0'，ms 用 t_perf_ns）", out)
    table_paired(F0, "2b · 趟内配对（S0 全段，对照）", out)
    ptr = table_per_trip(all_segs, out)
    table_anomalies(all_segs, out)
    table_mode2(all_segs, out)
    a8ec_raw, a8ec_keys = table_a8ec(metas, run_files, out)
    found = harvest_units(run_files, out)
    table_units_vs_bmax(found, ptr, out)
    table_robust(all_segs, out)
    # 量子化
    try:
        table_quantum(all_segs, run_files, out)
    except Exception as e:
        w("\n量子化复算异常: %r\n" % (e,))

    out.close()
    print("\n写出: %s" % outp)
    print("写出: %s" % SEG)
    print("写出: %s" % os.path.join(CARD, "per_trip.tsv"))

if __name__ == "__main__":
    main()
