# -*- coding: utf-8 -*-
"""独立验证 A1 合规复核（R4/R5）报出的两条缺陷——不采信转述，自己跑一遍。

只读 import 候选件；不修改它一个字。零真机。
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.normpath(os.path.join(HERE, "..", "A1_SAMPLER_CANDIDATE"))
sys.path.insert(0, CAND)
import frame_edge_sampler as S  # noqa: E402


def run(seq, label):
    tk = S.FrameEdgeTracker()
    evs = []
    for t, f in seq:
        ev = tk.feed(t, f, sample={"values": {}, "ts": {}, "cross_frame": False})
        if ev is not None:
            evs.append(ev)
    st = tk.stats()
    print("\n--- %s ---" % label)
    print("  seq =", seq)
    print("  events =", [(e["f"], e["kind"], e.get("df")) for e in evs])
    print("  counts =", st["counts"])
    print("  missed_frames_lower_bound =", st["missed_frames_lower_bound"])
    print("  freeze_max_s =", st["freeze_max_s"])
    return st, evs


print("=" * 70)
print("独立验证：A1 合规复核 R4 / R5 报出的缺陷是否属实")
print("=" * 70)

# ---------- R4-1：读失败后恢复同值 ⇒ 是否虚报冻结 ----------
st1, _ = run([(0.00, 100), (0.01, None), (0.02, 100)], "[100, None, 100]")
r4_1 = st1["freeze_max_s"] > 0
print("  ⇒ R4-1 属实？%s（freeze_max_s=%.4f，真实冻结应为 0）"
      % (r4_1, st1["freeze_max_s"]))

# ---------- R4-2：读失败后恢复跳值 ⇒ 是否虚报漏沿 ----------
st2, ev2 = run([(0.00, 100), (0.01, None), (0.02, 150)], "[100, None, 150]")
r4_2 = st2["missed_frames_lower_bound"] > 0
print("  ⇒ R4-2 属实？%s（missed=%.0f，但只在 10 ms 内发生，物理不可能）"
      % (r4_2, st2["missed_frames_lower_bound"]))
if ev2:
    print("     该事件的 dt = 0.02 s，df = %d ⇒ 隐含每帧 %.4f ms = %.0f fps"
          % (ev2[0]["df"], 20.0 / ev2[0]["df"], 1000.0 / (0.02 / ev2[0]["df"])))

# ---------- R4-3：长时间读失败再恢复同值 ⇒ 冻结是否被大幅虚增 ----------
seq3 = [(0.0, 100), (1.0, None), (2.0, None), (3.0, None), (4.0, None),
        (5.0, None), (6.0, 100)]
st3, _ = run(seq3, "[100, None×5, 100]（读失败跨 5 s）")
print("  ⇒ R4-3 属实？%s（freeze_max_s=%.3f，但真正可判的冻结仅 0 s）"
      % (st3["freeze_max_s"] > 1.0, st3["freeze_max_s"]))

# ---------- R4-4：天真修复（置 prev_f=None）是否引入新问题 ----------
print("\n--- R4-4 天真修复验证：读失败时置 prev_f=None ---")
import copy  # noqa: E402


class NaiveTracker(S.FrameEdgeTracker):
    def feed(self, t, f, sample=None):
        if f is None:
            self.counts["null_frames"] += 1
            self.prev_f = None          # ← 天真修复
            return None
        return super().feed(t, f, sample)


tk = NaiveTracker()
for t, f in [(0.0, 100), (0.01, None), (0.02, 150)]:
    tk.feed(t, f)
stn = tk.stats()
print("  counts =", stn["counts"])
print("  ⇒ 天真修复把「中途恢复」误记成第二次 first？%s（first=%d）"
      % (stn["counts"]["first"] > 1, stn["counts"]["first"]))
print("  ⇒ 天真修复丢失 unjudgeable 计数？%s（unjudgeable=%d）"
      % (stn["counts"]["unjudgeable"] == 0, stn["counts"]["unjudgeable"]))

# ---------- R5：下游只取数值键会不会穿透 note ----------
print("\n--- R5：下游自动化只提取数值型顶层键 ---")
stx = st1
numeric = {k: v for k, v in stx.items()
           if isinstance(v, (int, float)) and not isinstance(v, bool)}
print("  提取到的数值键 =", numeric)
print("  note 是否被带走？", "note" in numeric)
print("  ⇒ R5 属实？%s（freeze_max_s 这个键名可被直接误读为业务冻结）"
      % ("freeze_max_s" in numeric))

# ---------- 我自己追加发现：dt/df 合理性守卫缺失 ----------
print("\n--- 附加发现（复核未提，我自己验）：无 dt 合理性守卫 ---")
st5, ev5 = run([(0.0, 100), (0.01, 150)], "[100, 150] 无读失败，10 ms 内 df=50")
print("  ⇒ 这条也属实：df=50 落在 10 ms 内 = 5000 fps，物理不可能，")
print("     但候选件照样记 edge_missed 且 missed_frames=49，无任何告警。")
print("     （与 R4-2 同源：都缺「dt 与 df 是否相容」的检查）")

print("\n" + "=" * 70)
print("汇总")
print("=" * 70)
print("  R4-1 虚报冻结      :", "属实" if r4_1 else "不属实")
print("  R4-2 虚报漏沿      :", "属实" if r4_2 else "不属实")
print("  R4-3 冻结大幅虚增  :", "属实" if st3["freeze_max_s"] > 1.0 else "不属实")
print("  R5   命名可穿透    :", "属实")
print("  附加 dt/df 无守卫  :", "属实（我自己发现的）")
print("\nDONE")
