"""Lead 独立复算：①（子弹数 → 帧时间）证据链。

刻意独立于 W158/ W153 的实现。口径全部写死在这里，便于复核：
  - 只取 kind=="sample" 且 read_status=="ok" 的行
  - 按 t_mono_ns 升序，切 10 秒窗（窗宽由 --window 秒控制）
  - 窗内 ms/frame = 1000 * (t_last - t_first)/1e6 / (frame_last - frame_first)
  - 窗内 bullets = A8ED50 的均值
  - 丢弃 ms/frame > 200 的窗（引擎挂起段）
  - 丢弃 Δframe <= 0 或样本数 < --min-samples 的窗
  - 分桶按窗内 bullets 均值；趟内配对 hi = b>=75, lo = b<25

输出：逐趟表 + 分桶中位表 + 配对统计。不报 p 值/置信区间。
"""
import argparse
import glob
import json
import os
import statistics as st
import sys

DEFAULT_ROOT = r"D:\Project\ra2-campaign-forge"


def find_runs(root):
    # 支持 --list 传入的显式清单（避免反复递归 glob 整个仓库）
    if os.path.isfile(os.path.join(root, "run_files.txt")):
        with open(os.path.join(root, "run_files.txt"), encoding="utf-8") as f:
            out = [ln.strip() for ln in f if ln.strip()]
        if out:
            return sorted(out)
    hits = []
    for p in glob.glob(os.path.join(root, "**", "run.ndjson"), recursive=True):
        hits.append(p)
    return sorted(hits)


def load_samples(path):
    """流式读，返回 [(t_ns, frame, bullets, mode)]。

    语料里有**两套 schema**，必须都支持（否则会静默丢掉 130/137 个文件）：
      A（`_archive_us2` / W110_crash 等）：t_monotonic  = 秒(float)；mode  = int；t_perf_ns 有
      B（r02 早期等）              ：t_mono_ns    = 纳秒(int)；mode_A8B238 = int
    统一换算成纳秒整数。
    """
    rows = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if '"sample"' not in line:
                continue
            try:
                o = json.loads(line)
            except Exception:
                continue
            if o.get("kind") != "sample":
                continue
            if o.get("read_status") != "ok":
                continue

            t = o.get("t_mono_ns")
            if t is None:
                ts = o.get("t_monotonic")          # schema A：秒
                if ts is not None:
                    t = int(round(float(ts) * 1e9))
                else:
                    t = o.get("t_perf_ns")         # 退路
            if t is None:
                continue

            fr = o.get("frame")
            b = o.get("A8ED50")
            if fr is None or b is None:
                continue

            mode = o.get("mode_A8B238")
            if mode is None:
                mode = o.get("mode")               # schema A
            rows.append((int(t), fr, b, mode))
    rows.sort(key=lambda r: r[0])
    return rows


def windows(rows, window_s=10.0, min_samples=4, max_ms=200.0, mode_filter=None):
    if len(rows) < min_samples:
        return []
    span_ns = window_s * 1e9
    out = []
    i = 0
    n = len(rows)
    while i < n:
        j = i
        base = rows[i][0]
        while j < n and rows[j][0] - base < span_ns:
            j += 1
        chunk = rows[i:j]
        if len(chunk) >= min_samples:
            dt_ms = (chunk[-1][0] - chunk[0][0]) / 1e6
            dframe = chunk[-1][1] - chunk[0][1]
            modes = [c[3] for c in chunk]
            if dframe > 0 and dt_ms > 0:
                # dt_ms 已经是以毫秒为单位的真实时间 ⇒ ms/frame = dt_ms / dframe
                # （曾经错写成 1000*dt_ms/dframe，全表放大 1000 倍）
                ms = dt_ms / dframe
                if ms <= max_ms:
                    if mode_filter is None or all(m == mode_filter for m in modes):
                        out.append(dict(
                            ms=ms, bullets=st.mean(c[2] for c in chunk),
                            n=len(chunk), dframe=dframe, dt_ms=dt_ms,
                            mode=modes[0],
                        ))
        i = j if j > i else i + 1
    return out


BUCKETS = [(0, 24), (25, 49), (50, 74), (75, 99), (100, 124), (125, 10 ** 9)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=DEFAULT_ROOT)
    ap.add_argument("--window", type=float, default=10.0)
    ap.add_argument("--min-samples", type=int, default=4)
    ap.add_argument("--max-ms", type=float, default=200.0)
    ap.add_argument("--mode", type=int, default=None, help="只保留该 mode（不给=全要）")
    ap.add_argument("--pattern", default="", help="只处理路径含该子串的 run.ndjson")
    args = ap.parse_args()

    runs = find_runs(args.root)
    if args.pattern:
        runs = [r for r in runs if args.pattern in r]
    print("run.ndjson files: %d" % len(runs), file=sys.stderr)

    per_trip = []
    all_win = []
    for k, p in enumerate(runs):
        rows = load_samples(p)
        print("[%3d/%3d] %-70s samples=%d" % (k + 1, len(runs), os.path.basename(os.path.dirname(p))[:70], len(rows)),
              file=sys.stderr, flush=True)
        if not rows:
            continue
        w = windows(rows, args.window, args.min_samples, args.max_ms, args.mode)
        if not w:
            continue
        hi = [x["ms"] for x in w if x["bullets"] >= 75]
        lo = [x["ms"] for x in w if x["bullets"] < 25]
        trip = dict(
            path=p,
            n_samples=len(rows), n_win=len(w),
            b_max=max(x["bullets"] for x in w),
            b_mean=st.mean(x["bullets"] for x in w),
            ms_med=st.median(x["ms"] for x in w),
            n_hi=len(hi), n_lo=len(lo),
            ms_hi=st.median(hi) if hi else None,
            ms_lo=st.median(lo) if lo else None,
        )
        trip["delta"] = (trip["ms_hi"] - trip["ms_lo"]) if (hi and lo) else None
        per_trip.append(trip)
        for x in w:
            x["trip"] = p
            all_win.append(x)

    print()
    print("=" * 100)
    print("PER-TRIP (all trips with >=1 usable window)")
    print("=" * 100)
    print("%-58s %5s %5s %7s %7s %7s %6s %6s %8s %8s %8s"
          % ("path(rel)", "nsmp", "nwin", "b_mean", "b_max", "ms_med", "n_hi", "n_lo", "ms_hi", "ms_lo", "delta"))
    root = args.root
    for t in per_trip:
        rel = os.path.relpath(t["path"], root)
        print("%-58s %5d %5d %7.1f %7.1f %7.2f %6d %6d %8s %8s %8s"
              % (rel[-58:], t["n_samples"], t["n_win"], t["b_mean"], t["b_max"], t["ms_med"],
                 t["n_hi"], t["n_lo"],
                 ("%.2f" % t["ms_hi"]) if t["ms_hi"] is not None else "-",
                 ("%.2f" % t["ms_lo"]) if t["ms_lo"] is not None else "-",
                 ("%+.2f" % t["delta"]) if t["delta"] is not None else "-"))

    print()
    print("=" * 100)
    print("BUCKET MEDIANS (pooled windows, n=%d windows from %d trips)" % (len(all_win), len(per_trip)))
    print("=" * 100)
    base = None
    for lo_b, hi_b in BUCKETS:
        sel = [x["ms"] for x in all_win if lo_b <= x["bullets"] <= hi_b]
        if not sel:
            print("  %3d-%3s : n=0" % (lo_b, hi_b if hi_b < 10 ** 8 else "inf"))
            continue
        m = st.median(sel)
        if base is None:
            base = m
        print("  %3d-%3s : n=%-5d median=%7.2f ms  mean=%7.2f  min=%7.2f  max=%7.2f  ratio_vs_first=%.3fx"
              % (lo_b, hi_b if hi_b < 10 ** 8 else "inf", len(sel), m, st.mean(sel),
                 min(sel), max(sel), m / base))

    print()
    print("=" * 100)
    print("WITHIN-TRIP PAIRING  hi(b>=75) - lo(b<25)  [only trips having both]")
    print("=" * 100)
    deltas = [t["delta"] for t in per_trip if t["delta"] is not None]
    if deltas:
        print("  trips with both arms : n=%d" % len(deltas))
        print("  positive             : %d / %d" % (sum(1 for d in deltas if d > 0), len(deltas)))
        print("  median delta         : %+.2f ms" % st.median(deltas))
        print("  min / max delta      : %+.2f / %+.2f ms" % (min(deltas), max(deltas)))
        print("  all values           : %s" % ", ".join("%+.2f" % d for d in sorted(deltas)))
    else:
        print("  no trip has both arms")


if __name__ == "__main__":
    main()
