# W3-E1 派工单 · **8 项缺口机器可读化闭环的独立复核**（WorkBuddy · 续会话）

> 工作目录 `D:\Project\ra2-campaign-forge` · 本卡只做这一包。
> **来源**：两个已验收包在同一件事上会合，需要第三方闭环：
> - **Qoder 任务 D**（`qc/W3_20261001/m27_claims_machinereadable/`，Lead 验收 17/17）：`0X→0x` + 字节串加空格后，covered 1120→**1128**、**§3 dangling 527→519**，恰好等于 M16 那个 519。
> - **WorkBuddy M34R**（你上一包，Lead 验收 17/17）：8 VA「**仍未建账 —— 不是没人做过，是做过但没做成机器可读**」，并给出「任何已实测作用域下都不得宣称 100%」。
> **本卡 = 独立证明这两条结论是否闭合同一件事**：**Task D 的机器可读副本是否恰好覆盖 M34R 点名的那 8 个 VA？**

## 🔴 铁律（先读）
1. **两包产物全部只读**（`m27_claims_machinereadable/**` 与 `m34r_m27_recheck/**` 一个字节不许改 —— 它们都已验收）。
2. **官方工具是唯一权威**：`tools/atlas_va_crosscheck.py`（**指向你自己的输出目录**）。
3. **任何 dangling/covered 数字必须带 `--claims` 作用域标签**（`E-W3-04`）。
4. **空扫描报 `INSTRUMENT_FAILED`**；`[]` 与 `not_attempted` 两种输出。
5. **写域仅此一处**：`out/re_work/workbuddy/W3_20261002/e1_claims_closure/`

## 做什么（四件）
1. **集合对拍（本卡核心）**：
   - 取 M34R 的 8 VA 清单（`m34r_m27_recheck/eight_va_status.json` 或其报告 §③）。
   - 取 Task D 的机器可读副本（`m27_claims_machinereadable/claims.txt`）解析出的 VA 集。
   - **逐个判：8 个里几个在副本里、几个不在**。**完全覆盖 ⇒ 闭合；有漏 ⇒ 逐个给漏的原因。**
2. **端到端官方工具实测（4 档对照，全部带作用域标签）**：
   - a) `claims_game/ch*.txt` 基线；b) + M27 **原件**（0X 大写）；c) + **机器可读副本**；d) + 副本后**再手工加入 8 VA 中缺的那些**（若 b 已含则此档= c）。
   - **报告每档的 covered / dangling / §3 dangling** ⇒ **验证「缺口闭合 = 纯机器可读化」这条断言在端到端上成立**。
3. **一致性检查**：M34R 报告给的现网读数（ATLAS 口径剩 37 / 字节口径剩 35）与你本次实测是否一致；不一致 ⇒ 报冲突并给两侧作用域差异（不许静默取一）。
4. **反向验证**：构造"应当失败"对照（例：把副本的 `0x` 故意改回 `0X` 跑一次 ⇒ 读数应退回 b 档）。

## 交付
`E1_REPORT.md`（§A 十节骨架；`[0]` 直答）· `closure_matrix.json`（8 VA × 4 档逐项）· `scope_readings.json`（四档读数+作用域标签）· `verify_e1.py`（**EXIT=0 + `verdict tally` 行**）· `raw/stepNN_*.txt` + `raw/progress.log`

## 回报 `[0]`
① 8 VA 覆盖几/8（漏的逐个给原因）② 四档读数表 ③ M34R 读数一致性 ④ 反向验证 ⑤ `verdict tally` 原文

## 底线
> **宁可交"8 个覆盖了 6 个，缺的 2 个原因是 X"，也不要交"全部闭合"。**
