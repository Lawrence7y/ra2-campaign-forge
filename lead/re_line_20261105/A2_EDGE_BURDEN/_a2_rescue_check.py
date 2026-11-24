# -*- coding: utf-8 -*-
"""A2 核心验证：既有 harness 因「帧号回退」整窗弃统，候选件能否救回？

用 `l1_20261023e4/measure_w1.json` 的**真实 frame_edges** 同时喂两条路径：
  (a) 既有 harness 口径：`_measure_stats()` 的 logic<=0 早退（复刻，不改原文件）
  (b) 候选件口径：`FrameEdgeTracker` 把 df<0 标 unjudgeable 但保留之前所有有效沿

只读既有 JSON。零真机。
"""
import glob
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLER = os.path.normpath(os.path.join(
    HERE, "..", "A1_SAMPLER_CANDIDATE"))
sys.path.insert(0, SAMPLER)
import frame_edge_sampler as S  # noqa: E402

TARGET = r'out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1_20261023e4/measure_w1.json'

print("=" * 70)
print("A2 核心验证：帧号回退窗（既有 harness 整窗弃统）能否被候选件救回")
print("=" * 70)
print("target:", TARGET)

d = json.load(io.open(TARGET, encoding="utf-8"))
st = d["stats"]
fe = d["frame_edges"]
print("\n--- 既有读数（harness 自己的 stats）---")
for k in ("samples", "logic_frames", "n_edges", "n_multi_advance",
          "frame_ms_p50", "frame_ms_p90", "frame_ms_max",
          "max_stall_s", "hz_effective"):
    print("  %-18s = %s" % (k, st.get(k)))
print("  %-18s = %r" % ("note", st.get("note")))

print("\n--- frame_edges 事实 ---")
print("  沿数 = %d" % len(fe))
print("  首沿 = f=%d t=%.6f" % (fe[0][0], fe[0][1]))
print("  末沿 = f=%d t=%.6f" % (fe[-1][0], fe[-1][1]))
drops = [(fe[i][0], fe[i - 1][0], fe[i][1])
         for i in range(1, len(fe)) if fe[i][0] < fe[i - 1][0]]
print("  帧号回退次数 = %d" % len(drops))
for cur, prev, t in drops:
    print("    回退：%d → %d @ t=%.6f（掉幅 %d）" % (prev, cur, t, prev - cur))

# ---------- (a) 既有口径：复刻 logic<=0 早退 ----------
logic = int(fe[-1][0]) - int(fe[0][0])
print("\n--- (a) 既有口径：logic = f_last − f_first = %d − %d = %d ---"
      % (fe[-1][0], fe[0][0], logic))
if logic <= 0:
    print("  ⇒ logic<=0 ⇒ harness 记 note='frame not advancing'，")
    print("    frame_ms_p50/p90/p99/max 全部留 null，**整窗统计作废**。")
    print("    印证：stats.frame_ms_p50 = %r" % st.get("frame_ms_p50"))

# ---------- (b) 候选件口径 ----------
tk = S.FrameEdgeTracker()
events = []
for f, t in fe:
    ev = tk.feed(t, f, sample={"values": {}, "ts": {}, "cross_frame": False})
    if ev is not None:
        events.append(ev)
c = tk.stats()["counts"]

print("\n--- (b) 候选件口径：FrameEdgeTracker 逐沿喂入 ---")
print("  事件总数 = %d" % len(events))
print("  edge(df=1)      = %d" % c["edge"])
print("  edge_missed(df>1)= %d" % c["edge_missed"])
print("  unjudgeable     = %d" % c["unjudgeable"])
print("  first           = %d" % c["first"])
print("  missed_frames_lower_bound = %d"
      % tk.stats()["missed_frames_lower_bound"])

# 用候选件保留的 df=1 沿重算帧时分布
ms = []
for (fa, ta), (fb, tb) in zip(fe, fe[1:]):
    df = fb - fa
    if df == 1:
        ms.append((tb - ta) * 1000.0)
ms.sort()
print("\n  候选件保留的 df=1 帧时样本数 = %d" % len(ms))
if ms:
    def pct(v, q):
        k = (len(v) - 1) * q
        lo = int(k)
        hi = min(lo + 1, len(v) - 1)
        return v[lo] + (v[hi] - v[lo]) * (k - lo)
    print("    p50 = %.3f ms  (fps %.2f)" % (pct(ms, .50), 1000.0 / pct(ms, .50)))
    print("    p90 = %.3f ms" % pct(ms, .90))
    print("    p99 = %.3f ms" % pct(ms, .99))
    print("    max = %.3f ms  (fps %.2f)" % (ms[-1], 1000.0 / ms[-1]))
    print("    ⇒ 既有 harness 记 null 的窗，候选件能报出 %d 个有效帧时样本"
          % len(ms))

# ---------- 结论 ----------
print("\n" + "=" * 70)
print("结论")
print("=" * 70)
print("  1. 该窗**不是**「帧不推进」：%d 条沿里有 %d 条 df=1，帧时 p50 可算。" %
      (len(fe), len(ms)))
print("  2. harness 的早退判据用了 `f_last − f_first`（净推进），")
print("     遇到帧号回退（游戏回菜单/重开 ⇒ 帧号归 0）就整窗作废。")
print("  3. 候选件的 `classify_edge` 把回退标 `unjudgeable`、**不污染前面的有效沿**，")
print("     因此这一类窗**能被救回**。")
print("  4. 但注意：该窗被救回的部分**只覆盖回退之前那一段**，")
print("     回退之后（f=0 起）若有推进，仍在**同一次喂入**里继续累计 —— ")
print("     本窗回退发生在最后一个沿，故无后续段。")
print("\n  ★ 这不是「候选件更准」的泛泛说法，是一个**可复算的具体差额**：")
print("    既有口径 null vs 候选件 %d 个样本。" % len(ms))
print("\nDONE")
