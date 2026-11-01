# -*- coding: utf-8 -*-
"""_append_475.py — Leader 追加 §475（B 线中间证据续办验收 + A 线空交付）到共享台账。
二进制追加，各文件按其主导换行；不触碰历史字节（规避 §403 教训）。"""
import os

LOG = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
GOAL = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

S475_LOG = """

# §475　A/B 工作流（dwfrun-be5d1896）用户主动停止于汇总前；B 线 6 支自写探针中间证据由 Leader 逐字节
#        独立复算续办验收=R-064 定谳（附 1 精化/1 计数加严/1 待议）；A 线空交付（实质已由本批②实测覆盖）

- **停止事实**：用户主动停止 A/B 工作流（stop_reason=user），run 死于「汇总两线判定」前 ⇒ 两线均**无最终报告落盘**；
  Leader **不重启/不修订/不重建**（遵用户停止意图）。
- **B 线（qfmodel R-064 独立复核续办）**：中间证据**全部落盘可续办**——`brev_probe_a..f` 六支**自写全新实现**探针（独立于
  _r064rev_probe1-7 与 R-064 probe）+ probe1-7 首次留档 + R-062 **门禁 126/126** + **变异 112/112 全量(64m46s)**。
  所有 .err 仅 `/usr/bin/time` 计时行非错误 ⇒ 六支真跑成。Leader 亲跑 gamemd 73201cc0 命中 + capstone 逐字节复算 9 处
  witness 落格 + 0x5256F0 三 stamp + CHD numBases(List<INISection*>=2/GenericList=1)——**与 B 线转录逐位相符**。
  判定书 `lead/codex_round_20261030/B_r064rev/R064REV_LEADER_VERDICT_20261030.md`（Leader 单上下文验收·非 B 线作者自证）。
- **对 R-064 的验收结论=PASS（定谳·静态范围）**，四条核心问题全 CONFIRMED：esp-D 归一化可独立复现、物理槽错位恒 0xC 为真、
  RTTI 双链组合非继承为真、E1–E6 零字节越界属实。**三项补充**：
  ① **精化（非推翻）**：R-064「GL stamp 错位 0xC ⇒ 无配对/杂散」语气过强——0xC = 被传 INIClass 对象**自身内嵌 GenericList
     成员偏移**（0x52571E `mov[esi+0xC],0x7E1B04` 铁证），落格**有结构**；witness≠GenericList 主判不变，R-062 五行配对仍 REFUTED。
  ② **计数加严**：R-064「17/17 witness=INIClass」应分层——E2 网格实证 **14 行 STRICT 恒等闭合 + 帧 D 7 行依赖 c1=4 假设**
     （仅 c1=4∧u∈{None,8} 命中 7/7，其余 14 组 0；HYPV 真翻转风险，与 R-064 自设 HYPV 实验同向但计数表述宜精确）。
  ③ **待议（不采信）**：brev_g–k 为未收口中间探针，brev_k 显帧 F 边界 capstone 线性解码错位（同 R-064 E6 难点）⇒ UNVERIFIED，不作红项。
- **A 线（GLM 退出判别设计）**：空交付——仅一支静态观测点字节探针 `_aexitdisc_static_probe.py`（无输出留档、无设计报告，
  provider 限流 backoff 后随停止死亡）。**其目标产出（两形态判别/边界收窄/进环不可辨识）已由本会话 §474 Leader 亲执 ②
  hold13/14/15 三趟真机直接覆盖并推进**（同会话闩边界收窄 (14.997,16.272] + 绝对时钟模型否证）⇒ A 线不阻塞②。
- **③**：本轮续办纯离线（Leader 只读复算，零真机、零新落盘他人件）；gamemd/v2 冻结件复算前后 sha 不变
  （73201cc0 / 6afe2711）；R-064 裁定书件 11baaa8b945ab05f 未动（Leader 不改 RE-ATLAS 线写域，勘误建议转他线自办）。
- **开放项**：① R-064 定名异族（不同模型家族）复算**仍未派**（R-064 诚实账自认单甄别员同族；本书亦 Leader 单上下文）；
  ② R-064 §裁定「无配对」精化 + 17/17 分层两条注 → 转 RE-ATLAS 线按 R-062 冻结口径追加式办理（Leader 不代改他线书）；
  ③ ①② 真机读数（§474）异族对账仍 pending。三目标句态不变：①有限未复现、②硬门槛未达 RC-4 不收口、③保持态。
"""

S475_GOAL = """

### 收口更新⑭（A/B 工作流停止回收：B 线中间证据 Leader 逐字节续办=R-064 定谳 PASS + A 线空交付已由本批②覆盖——台账 §475）

- **B 线续办**：A/B 工作流（`dwfrun-be5d1896`）用户主动停止于汇总前、两线无最终报告；B 线 6 支**自写全新实现**探针
  + probe1–7 首次留档 + R-062 门禁 **126/126** + 变异 **112/112 全量(64m46s)** 全落盘（.err 均仅 time 行）。
  Leader 亲跑 gamemd `73201cc0` 命中 + capstone 逐字节复算全部承重结论（9 witness 落格 / 0x5256F0 三 stamp /
  CHD numBases List<INISection*>=2·GenericList=1）**与转录逐位相符**。判定书 `B_r064rev/R064REV_LEADER_VERDICT_20261030.md`。
- **R-064 验收=PASS（定谳·静态范围）**：esp 归一化可独立复现、物理槽错位恒 0xC 真、RTTI 双链组合非继承真、E1–E6 零字节越界属实。
  **三补充**：①精化——R-064「无配对/杂散」语气过强，0xC=被传 INIClass **自身内嵌 GenericList 成员偏移**（`52571E mov[esi+0xC],0x7E1B04` 铁证），
  落格有结构；witness≠GenericList 主判不变、R-062 五行配对仍 REFUTED。②计数加严——「17/17」应分层 14 行 STRICT 恒等 + 帧 D 7 行依赖 c1=4（E2 网格翻转风险）。③帧 F 解码错位=brev_k UNVERIFIED 不作红项。
- **A 线空交付**：GLM 通道 provider 限流 backoff 后随停止死，仅一支静态字节探针无报告；其目标产出（②两形态判别/边界/进环不可辨识）
  **已由 §474 Leader 亲执 hold13/14/15 真机直接覆盖推进** ⇒ A 不阻塞②，如需独立复核可下轮另派。
- **③**：本轮续办纯离线（Leader 只读复算、零真机、零改他人件）；gamemd/v2 前后 sha 不变；R-064 裁定书件 11baaa8b 未动（勘误建议转 RE-ATLAS 线自办，不改他线写域）。
- **开放项**：① R-064 定名**异族复算仍未派**（本书亦 Leader 单上下文）；② 精化+分层两注转 RE-ATLAS 线追加式办理；③ §474 ①② 真机读数异族对账 pending。
- **三目标句态不变**：①受测窗有限未复现；②硬门槛未达成、RC-4 不收口；③保持态。趟数账 29（本轮续办零真机新增）。"""


def dominant_nl(path):
    raw = open(path, "rb").read()
    crlf = raw.count(b"\r\n"); lf = raw.count(b"\n") - crlf
    return b"\r\n" if crlf > lf else b"\n"


def append_lines(path, text):
    nl = dominant_nl(path)
    body = text.replace("\r\n", "\n").strip("\n")
    out = nl + nl.join(x.encode("utf-8") for x in body.split("\n")) + nl
    with open(path, "ab") as fh:
        fh.write(out)
    return len(out), nl


for p, t in [(LOG, S475_LOG), (GOAL, S475_GOAL)]:
    n, nl = append_lines(p, t)
    print("APPENDED %s +%d bytes (nl=%s)" % (os.path.basename(p), n, nl))
