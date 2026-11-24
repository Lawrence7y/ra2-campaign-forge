# -*- coding: utf-8 -*-
"""V6 驱动器自查：D-21 裁 A 的复用前读，会不会**弱化跨帧检测**？

背景：D-21 裁决书说复用「把外层观测至 S5 的整个区间括住，**可能更保守地暴露跨帧**」。
这是裁决员的判断，我要自己验一遍：把「外层锚」与「进入函数时刻」之间的那段窗口
从跨帧检测里**漏掉了**吗？

只 import A1 候选件做离线语义模拟。零真机。
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.normpath(os.path.join(HERE, "..", "A1_SAMPLER_CANDIDATE"))
sys.path.insert(0, CAND)
import frame_edge_sampler as S  # noqa: E402

print("=" * 74)
print("自查：复用前读是否会弱化跨帧检测")
print("=" * 74)

# 场景：外层在 t=0.000 读到 f=100；进入 read_sample 是 t=0.030；其间帧推进到 101；
# 四 VA 读在 0.030..0.040；f_post 读到 101。
CALLS = []


def fake_reader(frame_value):
    def rd(va):
        CALLS.append(va)
        if va == S.FRAME_VA:
            return frame_value
        return 1234
    return rd


print("\n--- 场景 A：复用外层锚（D-21 裁 A 之后的实际路径）---")
CALLS.clear()


def counting_clock(start=0.030, step=0.002):
    """不穷举序列，按步长无限递推——避免 clock 调用次数猜错。"""
    state = {"t": start}

    def clk():
        v = state["t"]
        state["t"] += step
        return v
    return clk


rec = S.read_sample(fake_reader(101), counting_clock(), f_pre=100, t_pre=0.000)
print("  f_pre =", rec["f_pre"], " f_post =", rec["f_post"])
print("  cross_frame =", rec["cross_frame"])
print("  ts.f_pre =", rec["ts"]["f_pre"], " ts.segment_start =", rec["ts"]["segment_start"])
print("  reads_per_sample =", rec["reads_per_sample"], " f_pre_reused =", rec["f_pre_reused"])
print("  实际 reader 调用 VA 序列长度 =", len(CALLS), "（应为 5）")
print("  其中 FRAME_VA 次数 =", sum(1 for v in CALLS if v == S.FRAME_VA), "（应为 1，仅 f_post）")
print("  ⇒ 括号 = [t_pre=0.000, segment_end≈0.040]，**覆盖**了 100→101 的那次推进")
print("  ⇒ cross_frame =", rec["cross_frame"], "（True = 检测到了）")

print("\n--- 场景 B：自读前帧号（旧 6 读路径）---")
CALLS.clear()
rec2 = S.read_sample(fake_reader(101), counting_clock())
print("  f_pre =", rec2["f_pre"], " f_post =", rec2["f_post"])
print("  cross_frame =", rec2["cross_frame"])
print("  实际 reader 调用次数 =", len(CALLS), "（应为 6）")

print("\n" + "=" * 74)
print("判定")
print("=" * 74)
print("  1. 复用模式的括号起点是 **t_pre**（外层读前时刻），不是进入函数的时刻 ⇒")
print("     它把「外层读到 f=100」到「业务读数」之间的整段**都括进去了**，")
print("     **不是**从 0.030 才开始括 ⇒ **没有漏掉 0.000..0.030 这段**。")
print("  2. 因此裁决书那句「可能更保守地暴露跨帧」**成立**：")
print("     旧路径的前锚是 0.030 的 f_pre（已错过 0.000 的观测），括号更窄。")
print("  3. 但有一个**必须写进卡片的限定**：")
print("     `f_pre=100` 这个值本身是 0.000 时刻的观测，")
print("     ⇒ 若在 0.000..0.030 之间帧推进了**两次**又回到 100（ABA），")
print("        括号两端都吃到 100 ⇒ **误判为未跨帧**。")
print("     ★ 这不是复用模式**引入**的缺陷（旧路径同样存在 ABA 盲区，")
print("       只是窗口更短），但复用模式把窗口**拉长了** ⇒ ABA 概率**升高**。")

print("\n--- 场景 C：ABA 反例（复用模式下窗口更长，暴露更差）---")
CALLS.clear()
# 0.000 读到 100；0.000..0.030 之间帧真实推进过；0.030 后回到 100
rec3 = S.read_sample(fake_reader(100), counting_clock(), f_pre=100, t_pre=0.000)
print("  外层 f_pre=100 @ t=0.000；f_post=100 @ ~0.040（其间真实推进过）")
print("  cross_frame =", rec3["cross_frame"], "（False = **漏判**）")
print("  ⇒ ABA 盲区确认存在；复用模式窗口 0.040 s，旧模式窗口 ~0.010 s")

print("\n" + "=" * 74)
print("结论（写进台账）")
print("=" * 74)
print("  ✅ D-21 裁 A **没有**引入新的跨帧检测缺陷；它把括号**拉长**了，")
print("     对**单次**跨帧更保守（更容易检出）。")
print("  ⚠ 但 ABA（推进后回到同值）在两种模式下都会漏判，")
print("     且复用模式因窗口更长而**漏判概率更高**。")
print("  ⇒ 这必须写进字段卡：`cross_frame == False` **不等于**「四 VA 严格同帧」，")
print("     只等于「外层锚与后读两次帧号观测相同」。")
print("\nDONE")
