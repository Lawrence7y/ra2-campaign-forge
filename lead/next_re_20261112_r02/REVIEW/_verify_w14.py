# -*- coding: utf-8 -*-
"""Lead 复算 W14：采样间隔、相邻递增间隔分布、≥64ms 次数、跳多拍次数。只读。"""
import csv
import json
import os
import statistics

BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W14_tick_timeliness\out"

# 1) 采样间隔（从 run.ndjson）
S = [json.loads(l) for l in open(os.path.join(BASE, "run.ndjson"), encoding="utf-8") if l.strip()]
smp = [r for r in S if r.get("kind") == "sample"]
ok = [r for r in smp if r.get("read_status") == "ok" and isinstance(r.get("t_mono_ns"), int)]
ts = [r["t_mono_ns"] for r in ok]
gaps = [(ts[i + 1] - ts[i]) / 1e6 for i in range(len(ts) - 1)]
gaps.sort()


def q(a, p):
    if not a:
        return None
    return a[min(len(a) - 1, int(len(a) * p))]


print("sample=%d ok=%d" % (len(smp), len(ok)))
print("采样间隔 ms: min=%.3f 中位=%.3f p90=%.3f p99=%.3f max=%.3f  >20ms=%d(%.4f%%)" % (
    gaps[0], statistics.median(gaps), q(gaps, .9), q(gaps, .99), gaps[-1],
    sum(1 for g in gaps if g > 20), 100.0 * sum(1 for g in gaps if g > 20) / len(gaps)))

# 2) 递增间隔（从 increments.csv）
inc_path = os.path.join(BASE, "increments.csv")
rows = []
with open(inc_path, encoding="utf-8") as f:
    rd = csv.DictReader(f)
    for r in rd:
        rows.append(r)
print("\nincrements.csv 行数=%d 列=%s" % (len(rows), list(rows[0].keys())[:8]))

# 找间隔列与 delta 列
def pick(*names):
    for n in names:
        if rows and n in rows[0]:
            return n
    return None

gap_col = pick("interval_ms", "gap_ms", "dt_ms", "间隔ms")
d_col = pick("delta", "frame_delta", "dframe", "delta_frame")
t_col = pick("t_rel_s", "t_rel", "rel_s")
print("识别列: gap=%s delta=%s t=%s" % (gap_col, d_col, t_col))

if gap_col:
    ig = [float(r[gap_col]) for r in rows if r[gap_col] not in ("", None)]
    # 第一个递增可能没有间隔
    ig2 = sorted(x for x in ig if x > 0)
    print("相邻递增间隔 ms: n=%d min=%.3f 中位=%.3f p90=%.3f p99=%.3f max=%.3f mean=%.3f" % (
        len(ig2), ig2[0], statistics.median(ig2), q(ig2, .9), q(ig2, .99), ig2[-1],
        sum(ig2) / len(ig2)))
    buckets = {"[0,32)": 0, "[32,36)": 0, "[36,40)": 0, "[40,48)": 0, ">=48": 0, ">=64": 0}
    for x in ig2:
        if x < 32: buckets["[0,32)"] += 1
        elif x < 36: buckets["[32,36)"] += 1
        elif x < 40: buckets["[36,40)"] += 1
        elif x < 48: buckets["[40,48)"] += 1
        else: buckets[">=48"] += 1
        if x >= 64: buckets[">=64"] += 1
    print("直方图:", buckets)

if d_col:
    ds = [int(float(r[d_col])) for r in rows if r[d_col] not in ("", None)]
    from collections import Counter
    print("Δframe 分布:", dict(Counter(ds)))
    print("Δframe>=2 的次数:", sum(1 for d in ds if d >= 2))
