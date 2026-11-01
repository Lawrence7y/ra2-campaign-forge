# -*- coding: utf-8 -*-
"""_append_477.py - append S477 (reconciliation recovery) to shared ledgers. Additive only."""


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


S477 = """

# §477　异族对账判定书到盘并回收（qfmodel，14 探针+42KB 判定书；Leader 亲验承重三条全命中）：
#        5 主读数 4 复现 0 推翻；2 红项照录采纳（均小、不动主结论）；11 黄项收紧；
#        §6 增量线索=Δ(hwnd归零延迟)对闩/不闩 n=11 完美二分——「阶段中介」具体化为可测判据

- **对账件**：`lead/codex_round_20261030/XVERIFY_TRIPS_20261030/XVERIFY_TRIPS_20261030.md`（364 行）+ 14 支自写探针
  `_xv_s01..s14` + `_raw/` 全量留档；工作流 ask 因 provider backoff 两轮未 settle，**交付以盘面件为准**（不重启不修订）。
- **Leader 亲验（三条承重，全命中）**：R-1 hold14 闩→退原始时间戳差 **2.005**（台账 2.008 系 `exit_after_close_s`
  round2 与 `latch_after_close_s` round3 精度混用伪差，驱动 :507）；Δ 二分 hold13/14=**0.101/0.101**、hold15=**4.822**；
  闩=持续态（hold13/14 `exitstate==1` 仅 2 行 vs 挂死趟 204123 **1017 行** ⇒ 0.1s 快采样无漏检）。
- **红项 2 条照录采纳（勘误落地，不构成 RC-4 放松）**：
  - **R-1**：hold14 闩→退 **2.008→2.005**；hold13 2.004 ✓。主结论「≈2.0s 跨会话复现」**不变**（5 趟实算
    2.004/2.005/2.004/2.009/2.108，带宽 ≤0.104s）。**纪律**：闩→退一律由 `timeline.close_rows` 原始时间戳相减，
    勿用 `_rec` 舍入字段。
  - **R-2**：①r 趟「逐秒下降」→**24 步中 23 步降**（idx16 持平 866→866）、净 −81；q 趟严格 24/24。措辞级，不影响活动窗判定。
- **黄项 11 条收紧（Y-1..Y-11，摘要）**：Y-1 边界句须带「每点 n=1、未收窄到点、上界未收紧（E5 已有 16.091 不闩，
  本批 16.272 反退 0.18s，收窄全在下界）」；Y-2 cpu 轴免责与 ws 对称（中位含 1/2 跨退出样本，净退前 **n=1** 仍 ≥0.7 ⇒ 标签不倒）；
  Y-3 发射前 selftest/preflight **会话内亲跑但无当批落盘**（盘上留档是 E5 07:18 批）⇒ 该主张降格、今后批次须 tee 落盘；
  Y-4 短 TEMP 无 ② 留痕 UNVERIFIED；Y-5 「缝内零测点」严格化=「除左端点档 E5h10(11.193) 自身外」；Y-6 gate_fps15_min=3.0
  与 V11-a 25 两套口径勿并读；Y-7 「真交火」降格「活动窗 units 单调下降、非静态在场」（b/aircraft 无对应损失、计数语义未定义）；
  Y-8 跨档对照混 harness 代际（h3 无 keep-rect vs h7+keep-rect）；Y-9 W1/W2「冻结前有变化步」应显式；Y-10 趟数账批内相对口径
  （GOAL1 26 / GOAL2 27 并读有歧义，终账 29）；Y-11 §474 前提件「31 档长停顿全是终局」对 **l1a W2 不严格成立**
  （dU=−77/chpts=21 时 1.782s 停顿）且 **archive_T47/w0=31档活动窗 6.62s 停顿（251u）** ⇒ 归纳强度削弱；
  **本批高负载（900+）结论不受影响**。
- **§6 增量线索（台账未表述，登记为新轴/开放项；供下批②设计）**：
  - **Δ=关窗→hwnd 归零延迟对闩/不闩 n=11 完美二分零例外**（闩 8 趟 max 0.122s；不闩 3 趟 min 0.402s；判据 Δ<0.15⇒闩/Δ>0.35⇒不闩）
    ——把「关窗时机经引擎阶段中介」**具体化**：hwnd 是否紧跟 WM_CLOSE 归零（引擎当时是否仍响应 destroy 路径）决定后续闩与否。
    **限制：只判闩/不闩，不判正常退**（挂死趟 204123 Δ=0.102 闩了但不退、`exitstate==1` 达 1017 行）。
  - **~21s 绝对引擎事件带**（不闩趟 hwnd 归零聚集 21.094/21.114/21.651；闩趟归零在 close+0.1s）——与「否证纯绝对时钟」不冲突：
    存在绝对阶段边界，闩取决于关窗与该边界的先后。
  - hold15 singleton 与 hwnd **同一步**(idx=48)归零（闩趟 idx=1）⇒ 引擎阶段第二轴。
- **对账后句态（②收敛更硬）**：5 主读数 4 复现 0 推翻；闩边界/绝对时钟否证/闩→退≈2.0s 全部存活；
  **正常退出硬门槛仍未达成、RC-4 不收口——对账未提供任何放松依据**（挂死 T204123 单例未复现、六臂 9/9 不退在案）。
- **①句态**：31 档 × 900+ 交火长停顿 0 结论存活；前提件归纳强度按 Y-11 收紧（l1a W2 例外显式化）。
- **下一最小动作**：① 下批 ② 设计以 **Δ 二分轴**为承重观测（判据已具体化）；② harness8 实现择机（安全门误报已登记）；
  ③ RE-ATLAS 两注（§475）仍待他线；④ E3 未授权维持。
"""

LOG = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
GOAL = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

a = append_lines(LOG, S477)
b = append_lines(GOAL, S477)
print("APPENDED LOG +%d, GOAL +%d" % (a, b))
