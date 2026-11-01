# -*- coding: utf-8 -*-
"""_append_479.py - append S479 (R-3 withdrawal + final-return confirmations). Additive only."""


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


S479 = """

# §479　对账工作流正式完成（ask settle，最终回执）；**Leader 勘误自纠：撤回 §478 对 R-3 的采纳**——
#        对账员自证判据错误后重验，§474 前提件「长停顿全是终局」按正确判据 CONFIRMED；新增强确认登记

- **勘误（Leader 自纠，覆盖 §478）**：§478「R-3 采纳」**作废**。对账员最终回执自证：其先前反例系**判据错误**
  （用 STALL_ANATOMY 的 chpts=整窗 units 变化点数，而正确判据=**冻结起点之后**的变化步）；按正确判据重验 24 条：
  **23 条冻结后 0 变化步**；原点名 2 条实为终局（archive_T47 停变 13.018 < 冻结 18.380，差 5.362s；l1a 停变 21.030 <
  冻结 23.218，差 2.188s 且 b 已归零）；唯一非零项 l1_20261023e4/w2 = frame 恒 0 空窗（游戏已退），在台账「W1W2 空窗」
  并列表述内。⇒ **§474 前提件「既有 31 档战斗趟长停顿全是终局帧冻结」恢复 CONFIRMED**；连带撤回 §478 的
  「31 档活动窗内曾见长停顿（T47）」——该句同样源于错误判据。对账员全过程+stdout 留档 `_xv_s15/_raw/s15_stdout.txt`。
  **Leader 教训**：采纳红项前未独立套用「冻结期判据」，被整窗计数误导——复核红项须按其主张的语义重验，不能仅对数。
- **对账最终回执新增确认（此前盘面版未含，均带 path:line/逐位证据）**：
  - **驱动身份排他代码指纹**：三趟 _rec 含 `hold_override`+`e2_params.hold_after_window_s` 仅 E5 candidate 副本可写
    （root/fix 副本恒拼 6.0 无 normalize_hold_s）+ pyc 取证（source_size/mtime 与源件吻合）⇒ 三趟确由 90a1890a 候选所跑。
  - **绝对时钟否证加强**：n=3 趟/2 个已证会话全覆盖闩绝对全距（8 趟 20.145~22.552）仍不闩，反例搜索无果（_xv_s14）。
  - **零注入**：s4 模块表 10/11 模块无 ra2render.dll/rc4guard、S4.hit_count=0、via_loader=false、WER=0、EXCEPT 1046 行恒。
  - **冻结母本双锚**：盘上 sha256 与三趟 `e2_params.frozen_masters_sha256_at_import` 逐位相同。
  - **hold15 hwnd/singleton 归零 +21.094s**（绝对带内）、采样节律 median 0.1s 无空洞 ⇒ 非盲区假阴。
  - **守卫面**：三趟 ra2render_close_last.log 逐字 `EnableRC4Guard=1 EnableRC4ExitBail=1 DryRun=0`、守卫 8/8、bail 1/1。
- **新增口径限定（并入 Y-7/比较基准）**：「与 842/732 旧读数同量级」须加两注——l1a W0 实为**近静态**（dU=−3、24 步仅 3 变）
  不可当交火强度基准；e4（702u、活动窗 23/24）p99/max=61.0/69.6 **高于**本批 ⇒ 只能说「在 974/941 未见 ≥0.5s 停顿」，
  **不能**断言帧时与负载单调无关。另登记开放项：① counters 的 units/g/b/techno **字段语义无定义来源**（须 RE 线给出，
  或把「交火窗」改述「units 持续单调下降窗」）；② E12 驱动建议按 harness7 的 `CARRIER.pathlen_near_limit` 形态补 TEMP 长度实测字段。
- **红项终态**：**R-1/R-2 维持采纳**（§477 办理不变）；R-3 撤回。黄项 Y-1..Y-11 维持收紧。
- **句态（不变）**：①受测窗有限未复现（前提件经正确判据复验后**更强**）· ②硬门槛未达成、RC-4 不收口 · ③保持态。趟数 29。
"""

LOG = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
GOAL = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

a = append_lines(LOG, S479)
b = append_lines(GOAL, S479)
print("APPENDED LOG +%d, GOAL +%d" % (a, b))
