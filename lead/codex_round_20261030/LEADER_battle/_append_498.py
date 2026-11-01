# -*- coding: utf-8 -*-
"""_append_498.py - append S498 (stall spectrum, regime switching) to shared ledgers. Additive only."""


def append_lines(path, text):
    raw = open(path, "rb").read()
    crlf = raw.count(b"\r\n"); lf = raw.count(b"\n") - crlf
    nl = b"\r\n" if crlf > lf else b"\n"
    body = text.replace("\r\n", "\n").strip("\n")
    out = nl + nl.join(x.encode("utf-8") for x in body.split("\n")) + nl
    fh = open(path, "ab")
    try:
        fh.write(out)
    finally:
        fh.close()
    return len(out)


S498 = """

# §498　停滞谱全提取（10 窗+q/r 对照，Leader 亲算，tee `stall_spectrum_20261101.txt`）：
#        **①现象最终形态学=帧钟周期性停滞**；快态=零停滞；**停滞机制趟内动态切换**（推翻静态会话方差框架）

- **数字**：慢窗停滞段（>0.1s）6-135 段/窗、占比 **6%-100%**、模态时长 ~0.12-0.5s（max 0.750s=hb w1）；
  v3-a w2=135 段几乎背靠背铺满 24.9s（周期性停滞链）；**q/r 快会话晚相=0 段**（778/783 帧沿零间隙>0.1s）。
- **三决定性观察**：
  1. 快慢之别=**有无周期性停滞**（快态零停滞+帧沿均匀 ~32ms），非帧时快慢；
  2. **停滞机制趟内动态切换**：同会话 v3-a 24%→7%→97%、v3-b 6%→47%→52%（~25s 尺度）——
     「会话方差」（Y-11）细化为「**趟内状态机切换**」：存在快/慢两种帧钟状态，切换时间常数 ≤25s；
  3. 停滞发生于 units 1336→1114 全域（无单位量阈值；§496「fps-units 非单调」的机制解释）。
- **①现象重定义（终版）**：用户主诉「卡顿」=帧钟周期性停滞链（0.15-0.5s/段、可达 97% 占窗），
  快态零停滞——病灶=某状态使帧钟反复停摆（逻辑/同步/泵送类），非每帧渲染工作量。
- **对下一批的设计约束**：判别目标=**状态切换的触发器**（帧轴位置？事件？时间常数？）——
  需要跨切换的连续观测（现有 25s 窗太短，看不到完整切换过程；v3 框架加长窗或全趟帧轴采样
  （等待环+窗连采不停）是候选）；E3 栈采样（未授权）采点=停滞段内。
- 趟数 37 不变；输出 tee 在 LEADER_battle/；句态按 §496+本节形态学。
"""

LOG = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
GOAL = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

a = append_lines(LOG, S498)
b = append_lines(GOAL, S498)
print("APPENDED LOG +%d, GOAL +%d" % (a, b))
