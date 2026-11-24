# -*- coding: utf-8 -*-
"""Lead 复核 RE-N03 的 ndjson：字段名、mode 取值、分相位速率。只读。"""
import json
from collections import Counter, OrderedDict

P = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W7_load_baseline\out\run1.ndjson"
S = [json.loads(l) for l in open(P, encoding="utf-8") if l.strip()]
print("总行数:", len(S))
print("首行字段:", sorted(S[0].keys()))
print()

cand = [k for k in S[0] if "238" in k.lower() or "mode" in k.lower() or "g_mode" in k.lower()]
print("疑似 mode 字段:", cand)
for k in cand:
    print("  %s 取值分布: %s" % (k, dict(Counter(r.get(k) for r in S).most_common(8))))
print()

if "phase" in S[0]:
    ph = Counter(r.get("phase") for r in S)
    print("phase 分布:", dict(ph))
    for p in ph:
        rs = [r for r in S if r.get("phase") == p and isinstance(r.get("frame"), int)
              and isinstance(r.get("t_mono_ns"), int)]
        if len(rs) >= 2:
            d = rs[-1]["frame"] - rs[0]["frame"]
            t = (rs[-1]["t_mono_ns"] - rs[0]["t_mono_ns"]) / 1e9
            rate = d / t if t > 0 else 0
            print("  %-18s n=%-5d  dframe=%-5d / %.2fs = %.3f 计数/s" % (p, len(rs), d, t, rate))
else:
    print("无 phase 字段；按 frame 是否推进自行切段：")
    # 找 frame 首次非零 / 最后一段稳定推进
    seg = []
    cur = None
    for r in S:
        f = r.get("frame")
        t = r.get("t_mono_ns")
        if not isinstance(f, int) or not isinstance(t, int):
            continue
        if cur is None:
            cur = [r, r]
        if f != cur[1].get("frame"):
            cur[1] = r
        seg.append(r)
    ok = [r for r in S if isinstance(r.get("frame"), int) and isinstance(r.get("t_mono_ns"), int)]
    if len(ok) >= 2:
        # 最后 75 秒窗口
        t_end = ok[-1]["t_mono_ns"]
        win = [r for r in ok if r["t_mono_ns"] >= t_end - 75e9]
        if len(win) >= 2:
            d = win[-1]["frame"] - win[0]["frame"]
            t = (win[-1]["t_mono_ns"] - win[0]["t_mono_ns"]) / 1e9
            print("  末 75s 窗口: n=%d dframe=%d / %.2fs = %.3f 计数/s" % (len(win), d, t, d / t if t > 0 else 0))
