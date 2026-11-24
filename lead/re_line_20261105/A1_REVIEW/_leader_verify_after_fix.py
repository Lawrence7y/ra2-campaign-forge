# -*- coding: utf-8 -*-
"""独立验证 A1 复核报出的 5 条缺陷是否已修复（修复后版本）。

★ 只在**修复后的候选件**上跑；期望值 = 修复后应有的正确行为。
★ 不采信复核报告、不采信我自己的单测——独立写一遍。
零真机。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.normpath(os.path.join(HERE, "..", "A1_SAMPLER_CANDIDATE"))
sys.path.insert(0, CAND)
import frame_edge_sampler as S  # noqa: E402

PASS = 0
FAIL = 0


def ck(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print("  PASS  %s" % name)
    else:
        FAIL += 1
        print("  FAIL  %s   %s" % (name, detail))


def feed(seq):
    tk = S.FrameEdgeTracker()
    evs = []
    for t, f in seq:
        e = tk.feed(t, f, sample={"values": {}, "ts": {}, "cross_frame": False})
        if e is not None:
            evs.append(e)
    return tk, tk.stats(), evs


print("=" * 70)
print("修复后独立验证：A1 复核 5 条缺陷是否已闭合")
print("=" * 70)

# ---------- R4-1：读失败后恢复同值 ----------
print("\n--- R4-1 [100, None, 100]：修复前虚报 freeze_max_s=0.02 ---")
_, s1, e1 = feed([(0.0, 100), (0.01, None), (0.02, 100)])
ck("不虚报冻结（frame_clock_freeze_max_s == 0）",
   s1["frame_clock_freeze_max_s"] == 0.0,
   "got=%r" % s1["frame_clock_freeze_max_s"])
ck("记 1 次 resume_after_loss", s1["counts"]["resume_after_loss"] == 1,
   "got=%r" % s1["counts"]["resume_after_loss"])
ck("不产 edge/same 事件", len(e1) == 0 and s1["counts"]["edge"] == 0)

# ---------- R4-2：读失败后恢复跳值 ----------
print("\n--- R4-2 [100, None, 150]：修复前虚报 missed=49 + 假聚合 ---")
_, s2, e2 = feed([(0.0, 100), (0.01, None), (0.02, 150)])
ck("不虚报漏沿（missed_frames_lower_bound == 0）",
   s2["missed_frames_lower_bound"] == 0,
   "got=%r" % s2["missed_frames_lower_bound"])
ck("不产假聚合事件", len(e2) == 0, "got=%d events" % len(e2))
ck("记 1 次 resume_after_loss", s2["counts"]["resume_after_loss"] == 1)

# ---------- R4-3：长时间读失败再恢复 ----------
print("\n--- R4-3 [100, None×5, 100]：修复前虚报 freeze=6.0 s ---")
_, s3, _ = feed([(0.0, 100), (1.0, None), (2.0, None), (3.0, None),
                 (4.0, None), (5.0, None), (6.0, 100)])
ck("读失败墙钟不计入冻结", s3["frame_clock_freeze_max_s"] == 0.0,
   "got=%r" % s3["frame_clock_freeze_max_s"])

# ---------- R4-4：真冻结仍能测到（修复不能过度吞掉） ----------
print("\n--- R4-4 反证：真冻结必须仍被测到 ---")
_, s4, _ = feed([(0.0, 200), (0.5, 200), (1.0, 200), (1.5, 200), (2.0, 201)])
ck("真冻结 ≥1.5 s 仍被测到", s4["frame_clock_freeze_max_s"] >= 1.5,
   "got=%r" % s4["frame_clock_freeze_max_s"])
ck("真冻结后正常出 edge", s4["counts"]["edge"] == 1,
   "got=%r" % s4["counts"]["edge"])

# ---------- R5：键名自解释 ----------
print("\n--- R5 键名自解释 ---")
ck("旧键 freeze_max_s 已消失", "freeze_max_s" not in s1)
ck("新键 frame_clock_freeze_max_s 在场",
   "frame_clock_freeze_max_s" in s1)
numeric = {k: v for k, v in s1.items()
           if isinstance(v, (int, float)) and not isinstance(v, bool)}
ck("下游只取数值键时看不到含业务味的 freeze_max_s",
   "freeze_max_s" not in numeric, "numeric=%r" % numeric)
ck("note 明写读失败墙钟不计入",
   "不计入" in s1["note"] and "读失败" in s1["note"])

# ---------- 我发现的第 5 条：dt/df 物理相容性 ----------
print("\n--- 附加 [100, 150] 10 ms 内 df=50（5000 fps，物理不可能）---")
_, s5, e5 = feed([(0.0, 100), (0.01, 150)])
ck("记 implausible_df=1", s5["counts"]["implausible_df"] == 1,
   "got=%r" % s5["counts"]["implausible_df"])
ck("事件带 df_dt_plausible=False",
   bool(e5) and e5[0].get("df_dt_plausible") is False,
   "got=%r" % (e5[0].get("df_dt_plausible") if e5 else None))

print("\n--- 反证：合理的 df=5/1s（5 fps）不得误报 ---")
_, s6, _ = feed([(0.0, 100), (1.0, 105)])
ck("合理的 df 不误报", s6["counts"]["implausible_df"] == 0,
   "got=%r" % s6["counts"]["implausible_df"])
ck("合理 df 仍记 edge_missed=1", s6["counts"]["edge_missed"] == 1)

# ---------- 反证：df<0 仍不可判（修复不能把它吃掉） ----------
print("\n--- 反证：df<0 仍记 unjudgeable ---")
_, s7, _ = feed([(0.0, 500), (0.1, 400)])
ck("df<0 仍记 unjudgeable=1", s7["counts"]["unjudgeable"] == 1,
   "got=%r" % s7["counts"]["unjudgeable"])

# ---------- schema 升版 ----------
print("\n--- schema 升版 ---")
ck("SCHEMA 已升到 V2", S.SCHEMA == "FRAME_EDGE_V2", "got=%r" % S.SCHEMA)

print("\n" + "=" * 70)
print("SUMMARY  PASS=%d  FAIL=%d" % (PASS, FAIL))
print("=" * 70)
sys.exit(0 if FAIL == 0 else 1)
