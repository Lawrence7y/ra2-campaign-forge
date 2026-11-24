"""Lead 独立复算：① 的 **CPU 时间 vs 墙钟时间**（判定"在算"还是"在等"）。

口径（写死，便于复核）：
  * 只取 kind=="sample" 且 read_status=="ok"
  * 时间源优先 t_perf_ns；退路 t_mono_ns；再退 t_monotonic(秒)
  * 10 秒窗（按真实时间 t），窗内：
        wall_ms_per_frame = (Δt_ms) / Δframe
        cpu_ms_per_frame  = (Σ win_cpu_ms_delta 增量) / Δframe
        duty              = cpu_ms / wall_ms
  * 丢弃 Δframe<=0、样本数<4、wall_ms_per_frame>200 的窗
  * 按窗内 A8ED50 均值分桶（0-24/25-49/50-74/75-99/100-124/125+）

注意：win_cpu_ms 是**累计** CPU 毫秒；win_cpu_ms_delta 是每样本增量。
若某文件只有 win_cpu_ms 而无 delta，则用窗内 win_cpu_ms 的差。
台账 §630-5 记 win_cpu_ms 有 6.04 ms 节拍 —— 10 秒窗内累积多个节拍，够用。
"""
import json
import os
import statistics as st
import sys

LIST = r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\_lead_audit\run_files.txt"
BUCKETS = [(0, 24), (25, 49), (50, 74), (75, 99), (100, 124), (125, 10 ** 9)]


def load(path):
    rows = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if '"sample"' not in line:
                continue
            try:
                o = json.loads(line)
            except Exception:
                continue
            if o.get("kind") != "sample" or o.get("read_status") != "ok":
                continue
            t = o.get("t_perf_ns")
            if t is None:
                t = o.get("t_mono_ns")
            if t is None:
                ts = o.get("t_monotonic")
                t = int(round(float(ts) * 1e9)) if ts is not None else None
            if t is None:
                continue
            fr = o.get("frame")
            b = o.get("A8ED50")
            if fr is None or b is None:
                continue
            cpu = o.get("win_cpu_ms_delta")
            if cpu is None:
                cpu = o.get("win_cpu_ms")
                cpu_cum = True
            else:
                cpu_cum = False
            rows.append((int(t), fr, b, cpu, cpu_cum, o.get("win_cpu_ms")))
    rows.sort(key=lambda r: r[0])
    return rows


def windows(rows, window_s=10.0, min_samples=4, max_ms=200.0):
    if not rows:
        return []
    span = window_s * 1e9
    out = []
    i = 0
    n = len(rows)
    while i < n:
        j = i
        base = rows[i][0]
        while j < n and rows[j][0] - base < span:
            j += 1
        c = rows[i:j]
        i = j if j > i else i + 1
        if len(c) < min_samples:
            continue
        dt_ms = (c[-1][0] - c[0][0]) / 1e6
        dframe = c[-1][1] - c[0][1]
        if dt_ms <= 0 or dframe <= 0:
            continue
        wall = dt_ms / dframe
        if wall > max_ms:
            continue
        # CPU：优先 delta 求和；否则用累计差
        if any(x[5] is None for x in c):
            continue
        if c[0][4]:
            cpu_total = c[-1][5] - c[0][5]
        else:
            cpu_total = sum(x[3] for x in c if x[3] is not None)
        if cpu_total is None or cpu_total <= 0:
            continue
        cpu_pf = cpu_total / dframe
        out.append(dict(wall=wall, cpu=cpu_pf, duty=cpu_pf / wall,
                        bullets=st.mean(x[2] for x in c), n=len(c), dframe=dframe))
    return out


def bucket_report(wins, key, label):
    print("  %s" % label)
    print("    %-8s %6s %10s %10s %10s %10s" % ("bucket", "n", "median", "mean", "min", "max"))
    base = None
    for lo, hi in BUCKETS:
        sel = [w[key] for w in wins if lo <= w["bullets"] <= hi]
        if not sel:
            print("    %3d-%3s %6d %10s" % (lo, hi if hi < 10 ** 8 else "inf", 0, "-"))
            continue
        m = st.median(sel)
        if base is None:
            base = m
        print("    %3d-%3s %6d %10.3f %10.3f %10.3f %10.3f   (%.3fx)"
              % (lo, hi if hi < 10 ** 8 else "inf", len(sel), m, st.mean(sel),
                 min(sel), max(sel), m / base))


def main():
    files = [l.strip() for l in open(LIST, encoding="utf-8") if l.strip()]
    allw = []
    trips = 0
    for k, p in enumerate(files):
        rows = load(p)
        w = windows(rows)
        if w:
            trips += 1
            allw.extend(w)
        print("[%3d/%3d] %-52s samples=%-6d win=%d"
              % (k + 1, len(files), os.path.basename(os.path.dirname(p))[:52], len(rows), len(w)),
              file=sys.stderr, flush=True)

    print()
    print("=" * 84)
    print("CPU vs WALL : %d windows from %d trips" % (len(allw), trips))
    print("=" * 84)
    bucket_report(allw, "wall", "wall_ms_per_frame")
    print()
    bucket_report(allw, "cpu", "cpu_ms_per_frame")
    print()
    bucket_report(allw, "duty", "cpu_duty (cpu/wall)")

    print()
    print("=== 关键判据 ===")
    lo_w = [w for w in allw if w["bullets"] < 25]
    hi_w = [w for w in allw if w["bullets"] >= 75]
    if lo_w and hi_w:
        print("  lo(b<25) n=%d : wall=%.2f cpu=%.3f duty=%.4f"
              % (len(lo_w), st.median(x["wall"] for x in lo_w),
                 st.median(x["cpu"] for x in lo_w), st.median(x["duty"] for x in lo_w)))
        print("  hi(b>=75) n=%d : wall=%.2f cpu=%.3f duty=%.4f"
              % (len(hi_w), st.median(x["wall"] for x in hi_w),
                 st.median(x["cpu"] for x in hi_w), st.median(x["duty"] for x in hi_w)))
        dw = st.median(x["wall"] for x in hi_w) - st.median(x["wall"] for x in lo_w)
        dc = st.median(x["cpu"] for x in hi_w) - st.median(x["cpu"] for x in lo_w)
        print("  Δwall = %+0.2f ms/frame ;  Δcpu = %+0.3f ms/frame" % (dw, dc))
        print("  ⇒ 墙钟增加量中被 CPU 解释的比例 = %.1f%%" % (100.0 * dc / dw if dw else float("nan")))


if __name__ == "__main__":
    main()
