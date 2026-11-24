# -*- coding: utf-8 -*-
"""Lead 复算 W13 长时漂移：10 s 窗速率、首/末 1/3 中位、斜率、停推段。只读。"""
import json
import os
import statistics

P = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W13_longrun_drift\out\run.ndjson"

S = [json.loads(l) for l in open(P, encoding="utf-8") if l.strip()]
kinds = {}
for r in S:
    k = r.get("kind")
    kinds[k] = kinds.get(k, 0) + 1
print("总行数:", len(S), " kind 分布:", kinds)

smp = [r for r in S if r.get("kind") == "sample"]
ok = [r for r in smp if r.get("read_status") == "ok"
      and isinstance(r.get("frame"), int) and isinstance(r.get("t_mono_ns"), int)]
print("sample=%d ok=%d" % (len(smp), len(ok)))
if len(ok) < 10:
    raise SystemExit("样本不足")

# 局内段：从首个 frame>0 起，到最后一个 frame>0 之前（排除 post_end 冻结）
first = next(i for i, r in enumerate(ok) if r["frame"] > 0)
last_pos = max(i for i, r in enumerate(ok) if r["frame"] > 0)
seg = ok[first:last_pos + 1]
t0 = seg[0]["t_mono_ns"]
span = (seg[-1]["t_mono_ns"] - t0) / 1e9
dfr = seg[-1]["frame"] - seg[0]["frame"]
print("有效局内段: n=%d  span=%.3f s  Δframe=%d  整体速率=%.4f 计数/s"
      % (len(seg), span, dfr, dfr / span if span else 0))

# 10 s 窗
W = 10.0
windows = []
i = 0
while i < len(seg):
    ws = seg[i]["t_mono_ns"]
    j = i
    while j + 1 < len(seg) and (seg[j + 1]["t_mono_ns"] - ws) / 1e9 < W:
        j += 1
    if j > i and (seg[j]["t_mono_ns"] - ws) / 1e9 >= W * 0.9:
        d = seg[j]["frame"] - seg[i]["frame"]
        dt = (seg[j]["t_mono_ns"] - ws) / 1e9
        windows.append((round((ws - t0) / 1e9, 1), d, dt, d / dt if dt else 0))
    i = j + 1 if j > i else i + 1

rates = [w[3] for w in windows]
print("10 s 窗数=%d  速率范围 [%.4f, %.4f]" % (len(rates), min(rates), max(rates)))
if len(rates) >= 6:
    k = len(rates) // 3
    a = statistics.median(rates[:k])
    b = statistics.median(rates[-k:])
    print("首 1/3 中位=%.4f  末 1/3 中位=%.4f  降幅=%.4f%%" % (a, b, 100.0 * (a - b) / a))
    n = len(rates)
    xs = list(range(n))
    mx = sum(xs) / n
    my = sum(rates) / n
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, rates)) / sum((x - mx) ** 2 for x in xs)
    print("斜率=%.6f 计数/s per 10s  （%d 窗）" % (slope, n))

# 停推段
runs = []
cur = None
for i in range(1, len(seg)):
    same = seg[i]["frame"] == seg[i - 1]["frame"]
    if same:
        if cur is None:
            cur = [i - 1, i]
        else:
            cur[1] = i
    else:
        if cur:
            dur = (seg[cur[1]]["t_mono_ns"] - seg[cur[0]]["t_mono_ns"]) / 1e9
            if dur >= 1.0:
                runs.append((round((seg[cur[0]]["t_mono_ns"] - t0) / 1e9, 1), round(dur, 3), seg[cur[0]]["frame"]))
            cur = None
print("局内 ≥1 s 停推段: %d %s" % (len(runs), runs))

fails = sum(1 for r in smp if r.get("read_status") != "ok")
print("读失败拍数:", fails)
