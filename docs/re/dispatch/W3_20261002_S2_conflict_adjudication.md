# W3-S2 派工单 · **S1 的 3 条 CONFLICT 独立裁决**（ZCode 客户端 · 续会话）

> 工作目录 `D:\Project\ra2-campaign-forge` · 本卡只做这一包。
> **来源**：S1 汇总九章审计后产出 **3 条 CONFLICT**（两份审计对同一 VA/同一 claim 给出互斥裁决），按卡面纪律**并列原文未取一**，移交裁决。
> **已知冲突候选（S1 过程中曾点名）**：`0x00A40D2C` —— M28R 判 FALSIFIED（M25 的 `FrameTimer_SelectAutoTarget` 命名）vs M30R 判 HOLDS（M30 的 `CurrentFrame` 命名）。
> **权威输入**：`out/re_work/zcode_live/W3_20261002/s1_falsified_consolidation/falsified_consolidated.json`（`conflicts` 段）+ 两份原审计件。

## 🔴 铁律（先读）
1. **S1 与九份审计件全部只读**；你产出**裁决件**，不改任何审计结论。
2. **裁决必须落在二进制上**：`ra2youli/game.exe` 实读（段映射 `E-W3-01`）+ 反汇编/RTTI 结构；**禁止用"哪份报告更权威"当理由**。
3. **判据优先级**：字节实读 > 结构推导 > 报告互引。**两份审计都可能错** —— 允许判 `BOTH_WRONG`，但必须给出正确值。
4. **空扫描报 `INSTRUMENT_FAILED`**；`[]` 与 `not_attempted` 两种输出。
5. **写域仅此一处**：`out/re_work/zcode_live/W3_20261002/s2_conflict_adjudication/`

## 做什么（四件）
1. **逐条裁决 3 CONFLICT**：每条给 `verdict ∈ {AUDIT_A_RIGHT, AUDIT_B_RIGHT, BOTH_WRONG, BOTH_PARTIAL, INSUFFICIENT}` + **字节级 evidence**（hex + 反汇编 + 结构链）。
2. **给出正确值**：不管判谁对，**必须给出你实测的正确值**（命名/地址/槽索引/表种，视冲突内容）。
3. **影响面**：该 VA 还出现在哪些审计/原卡/文档里（grep 全库）⇒ **回填时要改几处**。
4. **反向验证**：构造"应当失败"对照（例：用你自己的判据去裁一条**已知无冲突**的同型条目 ⇒ 应判一致；若你的判据连已知条目都会判错 ⇒ 说明判据不稳）。

## 交付
`S2_REPORT.md`（§A 十节骨架；`[0]` 直答）· `conflict_adjudication.json`（逐条：冲突原文两侧 / verdict / evidence / correct_value / affected_files）· `verify_s2.py`（**EXIT=0 + `verdict tally` 行**）· `raw/stepNN_*.txt` + `raw/progress.log`

## 回报 `[0]`
① 3 条逐条 verdict ② 每条的正确值 ③ 影响面（各几处）④ 反向验证 ⑤ `verdict tally` 原文

## 底线
> **宁可交"3 条里 1 条 INSUFFICIENT（缺字节证据）"，也不要交"3 条都判给某一方"。**
> **裁决一旦给出就会进回填清单 —— 错的裁决比不裁决更贵。**
