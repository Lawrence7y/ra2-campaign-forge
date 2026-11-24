# -*- coding: utf-8 -*-
"""W162 step 0b: 逐文件字段存在表（决定 Q1/Q2 的可测范围）。"""
import json, os, collections

FILES = [l.strip() for l in open(
    os.path.join(os.path.dirname(__file__), "run_files.txt"), encoding="utf-8") if l.strip()]

WANT = ["t_monotonic", "t_perf_ns", "t_mono_ns", "mode", "mode_A8B238",
        "A8ED50", "B0CE88", "A8E9A0", "87E8E0", "X87E8E0", "ABCD58",
        "g1", "g2", "g3", "g4",
        "win_cpu_ms", "win_cpu_ms_delta", "win_cycle", "win_cyc_delta",
        "win_kernel_ms", "win_user_ms", "win_tid", "frame",
        "n_threads", "sum_all_threads_cpu_ms", "win_ctx_switches", "sched_late_ms",
        "win_foreground"]


def main():
    rows = []
    for p in FILES:
        cnt = collections.Counter()
        n = 0
        for line in open(p, "r", encoding="utf-8", buffering=1 << 20):
            line = line.strip()
            if not line:
                continue
            n += 1
            o = json.loads(line)
            for k in WANT:
                if k in o and o[k] is not None:
                    cnt[k] += 1
        rows.append((p, n, cnt))

    hdr = f"{'n':>8s} " + " ".join(f"{k[:9]:>9s}" for k in WANT)
    print("=== per-file non-null field counts ===")
    print(hdr)
    trip = lambda p: os.path.basename(os.path.dirname(p))
    for p, n, c in rows:
        print(f"{n:8d} " + " ".join(f"{c.get(k,0):9d}" for k in WANT) + "  " + trip(p) + "  " + p)

    print("\n=== 汇总：有 X 个字段的文件数 ===")
    for k in WANT:
        nf = sum(1 for _, _, c in rows if c.get(k, 0) > 0)
        ns = sum(c.get(k, 0) for _, _, c in rows)
        print(f"  {k:24s} files={nf:4d}  samples={ns:9d}")

    # 分组：按 CPU 字段有/无 + schema
    print("\n=== 分组（决定 Q1 可测范围）===")
    g = collections.Counter()
    for p, n, c in rows:
        has_cpu = c.get("win_cpu_ms", 0) > 0
        has_delta = c.get("win_cpu_ms_delta", 0) > 0
        tsf = "perf_ns" if c.get("t_perf_ns", 0) > 0 else ("mono_ns" if c.get("t_mono_ns", 0) > 0 else "NONE")
        sch = "A(mode)" if c.get("mode", 0) > 0 else ("B(mode_A8B238)" if c.get("mode_A8B238", 0) > 0 else "none")
        g[(has_cpu, has_delta, tsf, sch)] += 1
    for k, v in g.items():
        print(f"  win_cpu_ms={k[0]!s:5s} delta={k[1]!s:5s} ts={k[2]:8s} schema={k[3]:16s} files={v}")


if __name__ == "__main__":
    main()
