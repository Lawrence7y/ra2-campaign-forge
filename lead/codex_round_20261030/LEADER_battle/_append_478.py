# -*- coding: utf-8 -*-
"""_append_478.py - append S478 (R-3 upgrade + next-batch-2 card) to shared ledgers. Additive only."""


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


S478 = """

# §478　对账书增量回收（判定书 01:43 增写）：Y-11 升格红项 R-3 采纳（§474 前提件改写 22/24）；
#        下批②批次卡片落稿（Δ 二分轴出样本检验：hold15.3/15.8 双点双轴互证）

- **R-3 采纳（勘误落地，不构成 RC-4 放松）**：§474 前提件「31 档战斗趟（t55k/l1a/e4）长停顿**全是**终局帧冻结」
  被 2/24 反例否证——l1a W2（dU=−77/chpts=21 时 1.782s 停顿，窗末 23.22s 起）与 archive_T47 W0（dU=−8/chpts=7 时
  6.618s 停顿，31 档活动窗、units0=251）。两条均为 Leader 早前 STALL_ANATOMY 自算数据，**无需再验直接采纳**。
  改写口径（采对账员文本）：「既有 31 档战斗趟长停顿 **22/24 为终局**（units ≤5 变化），余 2 条为窗末/低负载仍降项」；
  并登记：「31 档活动窗内从未见长停顿」**不成立**（T47 反例），成立的是「31 档 × 900+ 交火负载未见长停顿」。
- **增量线索补强（对账书 01:43 版 §6-5）**：hwnd 与 singleton 归零**同步同一步**（闩族 idx=1/close+0.101s；
  不闩族同一步但延迟 4.8~5.0s 或 0.4s）⇒ 两轴反映同一次 destroy/teardown 节拍，可区分「关窗被即时处理」vs
  「关窗排队到 ~21s 边界才被处理」——Δ 轴的第二观测面。
- **下批②批次卡片（落稿待批，本唤醒不发射）**：`GOAL2_BATCH2_DELTA_AXIS_20261031.md`——在未收窄区间
  (14.997,16.272] 内取 hold=15.3/15.8 双点，**出样本检验 Δ 二分轴**（预测：若边界在区间内则两趟均不闩、Δ>0.35、
  exitstate 值域 {0}、singleton 同步行；若任一趟闩（Δ<0.15）⇒ 边界上移）。双轴互证：Δ 轴与 exitstate 轴若出现
  分歧（如 Δ<0.15 却不闩）⇒ 二分轴被否、登记新 UNKNOWN。≤2 趟或 20min，V11-c 发射时重测 BOOT。
"""

LOG = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
GOAL = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

a = append_lines(LOG, S478)
b = append_lines(GOAL, S478)
print("APPENDED LOG +%d, GOAL +%d" % (a, b))
