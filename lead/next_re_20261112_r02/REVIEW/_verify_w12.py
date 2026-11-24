# -*- coding: utf-8 -*-
"""Lead 复算 W12 的 R1–R4：区间速率、Δframe==0 占比、停推段。只读。"""
import glob
import json
import os
import statistics

BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W12_perf_baseline\out"

for p in sorted(glob.glob(os.path.join(BASE, "R*.ndjson"))):
    S = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
    if not S:
        print(os.path.basename(p), "空")
        continue
    kinds = set(r.get("kind") for r in S)
    smp = [r for r in S if r.get("kind") == "sample"] or S
    ok = [r for r in smp if r.get("read_status") == "ok" and isinstance(r.get("frame"), int)
          and isinstance(r.get("t_mono_ns"), int)]
    name = os.path.basename(p)
    if len(ok) < 2:
        print("%-12s samples=%d ok=%d  (不足)" % (name, len(smp), len(ok)))
        continue
    t0, t1 = ok[0]["t_mono_ns"], ok[-1]["t_mono_ns"]
    span = (t1 - t0) / 1e9
    dframe = ok[-1]["frame"] - ok[0]["frame"]
    rate = dframe / span if span > 0 else 0

    deltas = [ok[i + 1]["frame"] - ok[i]["frame"] for i in range(len(ok) - 1)]
    zero = sum(1 for d in deltas if d == 0)
    p90 = statistics.quantiles(deltas, n=10)[-1] if len(deltas) >= 10 else None

    # 连续 >=1s frame 不变的段
    runs = 0
    cur_t = None
    longest = 0.0
    for i in range(1, len(ok)):
        if deltas[i - 1] == 0:
            if cur_t is None:
                cur_t = ok[i - 1]["t_mono_ns"]
            dur = (ok[i]["t_mono_ns"] - cur_t) / 1e9
            longest = max(longest, dur)
        else:
            if cur_t is not None and (ok[i]["t_mono_ns"] - cur_t) / 1e9 >= 1.0:
                runs += 1
            cur_t = None
    if cur_t is not None and (ok[-1]["t_mono_ns"] - cur_t) / 1e9 >= 1.0:
        runs += 1

    fails = sum(1 for r in smp if r.get("read_status") != "ok")
    modes = {}
    for r in ok:
        k = r.get("mode_A8B238")
        modes[k] = modes.get(k, 0) + 1

    print("%-12s n=%-5d span=%7.3fs  Δframe=%-5d  速率=%.4f 计数/s" %
          (name, len(ok), span, dframe, rate))
    print("             Δframe==0 占比=%.3f%%  增量 min/med/p90/max=%s/%s/%s/%s" %
          (100.0 * zero / len(deltas), min(deltas),
           statistics.median(deltas), (("%.1f" % p90) if p90 is not None else "-"), max(deltas)))
    print("             ≥1s 停推段=%d 最长=%.3fs  读失败=%d  mode 分布=%s" %
          (runs, longest, fails, modes))
