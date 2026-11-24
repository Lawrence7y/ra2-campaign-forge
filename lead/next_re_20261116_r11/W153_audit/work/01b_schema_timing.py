# -*- coding: utf-8 -*-
"""步骤1b：key 的文件级覆盖 + 时间源精度对比
输出：每个 key 出现在多少个文件里；t_monotonic 与 t_perf_ns 的量化粒度
"""
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w153_common as C

OUT = []


def main():
    files = C.all_files()
    fs_count = Counter()
    per_file = {}
    for p in files:
        ks = set()
        with open(p, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    o = json.loads(line)
                except Exception:
                    continue
                ks |= set(o.keys())
        per_file[C.trip_rel(p)] = ks
        fs_count.update(ks)
    OUT.append("=== key -> 文件数 (总 %d 文件) ===" % len(files))
    for k, c in sorted(fs_count.items(), key=lambda kv: (-kv[1], kv[0])):
        OUT.append("  %-26s files=%3d" % (k, c))

    OUT.append("")
    OUT.append("=== A8EC34 / 目标搜索 相关 ===")
    hit = [r for r, ks in per_file.items() if "A8EC34" in ks or any("A8EC" in k for k in ks)]
    OUT.append("含 A8ECxx 任一键的文件数 = %d" % len(hit))
    allkeys = set()
    for ks in per_file.values():
        allkeys |= ks
    OUT.append("全部 key 里含 'A8EC' 的 = %s" % sorted(k for k in allkeys if "A8EC" in k))
    OUT.append("")
    OUT.append("=== 含 X87E8E0 的文件数 = %d ; 含 '87E8E0'(无X) = %d ===" % (
        fs_count.get("X87E8E0", 0), fs_count.get("87E8E0", 0)))
    both = [r for r, ks in per_file.items() if "X87E8E0" in ks and "87E8E0" in ks]
    OUT.append("同时含两者的文件 = %d" % len(both))

    # 时间源精度：挑 3 个代表文件
    OUT.append("")
    OUT.append("=== 时间源：t_monotonic 的量化粒度 ===")
    probes = [
        r"next_re_20261112_r10\W110_crash\out\trip_scan_near_r1\run.ndjson",
        r"next_re_20261112_r10\W110_crash\out\_archive_close\trip_hunt_near_r1\run.ndjson",
        r"next_re_20261112_r08\W98_clean\out\trip_g_idle_r1\run.ndjson",
    ]
    for rel in probes:
        p = os.path.join(C.ROOT, rel)
        if not os.path.exists(p):
            OUT.append("missing: " + rel)
            continue
        tmono = []
        tperf = []
        ima = []
        with open(p, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    o = json.loads(line)
                except Exception:
                    continue
                if o.get("kind") != "sample":
                    continue
                if o.get("t_perf_ns") is not None:
                    tperf.append(o["t_perf_ns"])
                if o.get("t_monotonic") is not None:
                    tmono.append(o["t_monotonic"])
                if o.get("interval_ms_actual") is not None:
                    ima.append(o["interval_ms_actual"])
        OUT.append("")
        OUT.append("file=%s  n_tmono=%d n_tperf=%d" % (rel, len(tmono), len(tperf)))
        OUT.append("  t_perf_ns 最小正增量 = %s ns" % (min(b - a for a, b in zip(tperf, tperf[1:]) if b > a) if len(tperf) > 1 else "n/a"))
        d = [round(b - a, 6) for a, b in zip(tmono, tmono[1:]) if b > a]
        OUT.append("  t_monotonic 正增量最频值 = %s" % Counter(d).most_common(6))
        # t_monotonic 值本身是否只落在某个网格上
        OUT.append("  t_monotonic 前 8 个值 = %s" % tmono[:8])
        OUT.append("  t_perf_ns/1e9 前 8 个值 = %s" % [round(x * 1e-9, 9) for x in tperf[:8]])
        OUT.append("  interval_ms_actual 前 8 个值 = %s" % ima[:8])
        if len(tperf) > 2:
            # 检查 t_perf_ns 是否为 100ns 网格
            OUT.append("  t_perf_ns 末两位分布 = %s" % Counter(x % 100 for x in tperf).most_common(5))

    txt = "\n".join(OUT)
    print(txt)
    C.write_evidence("01b_schema_timing.txt", txt)


if __name__ == "__main__":
    main()
