# W3-C1 派工单 · **任务 C 的 6 处〔改〕台账回填执行**（Qoder CN · 第四会话）

> 工作目录 `D:\Project\ra2-campaign-forge` · 本卡只做这一包。
> **来源**：任务 C 独立复核（Lead 已验收，`verify_ledger.py` EXIT=0）结论原文：
> > 「18 处 → 现 **33 处**；**6〔改〕/ 8〔注〕/ 19〔成〕**；**6 处〔改〕到 13:43 仍 0 处落地**；其中 2 处本包不定改法（#14、#11）、1 处不属权限（#17）」
> **本卡 = 把可执行的〔改〕逐条落地**（不可执行的 3 处给出"为什么不可执行"并转交）。
> **权威依据**：`out/re_work/qc/W3_20261001/coverage_ledger/CALIBER_CONSISTENCY_AUDIT.md` 的 **`[11] ★独立复核回填` 节**（含 33 处逐处表与〔改/注/成〕分类）+ `RESULT_TASKC_RECHECK_20261002.md`。

## 🔴 铁律（先读）
1. **改前先快照**：对每个将被修改的文件，先在 `out/re_work/qc/W3_20261002/c1_ledger_fix/snapshots_before/` 留全量副本 + manifest（path/mtime/sha256）。
2. **严格追加式或精确替换式**：更正一律「原句保留 + 注记」或「按〔改〕表给的精确替换」；**零删除、零无关改动**；每处带 `【C1 回填】` 标记。
3. **`verify_ledger.py` 改前改后各跑一次，两次都必须 EXIT=0**（原文都要落在 `runs/`）。**改后 EXIT≠0 ⇒ 立即回滚并报告**（回滚脚本先行写好）。
4. **#14/#11/#17 三处不硬改**：按任务 C 的原话（"本包不定改法"/"不属权限"）—— 给出 `_HANDOFF.md` 转交说明。
5. **`atlas_snapshots.game_body_0206` 悬空指针**按任务 C 建议处置：新增 `game_body_0927` 键（记现件 238,788 B / `2a917e45f890`）+ 旧键补 `archived_path`（**先证明 archived 件存在，找不到就标 NOT_FOUND 不许编路径**）。
6. **写域**：`coverage_ledger/`（本卡是它的唯一写者 —— Qoder 其他会话不写此目录）+ `out/re_work/qc/W3_20261002/c1_ledger_fix/`。
7. **空扫描报 `INSTRUMENT_FAILED`**；工具读数带作用域标签（`E-W3-04`）。

## 做什么（四件）
1. **逐条落地〔改〕6 处**（其中可执行的）：每处 = 改前 sha → 改后 sha + 原文引用。
2. **`game_body_0927` 新键 + `archived_path` 补注**（见铁律 5）。
3. **回填后全量复核**：`verify_ledger.py` 两次 EXIT=0 + 用官方工具重跑一次登记读数（确认 2,582/1,120/1,418@44.13% 仍可复现 —— 若因本次回填变化，立即回滚并报告）。
4. **反向验证**：构造"应当失败"对照 —— **故意把一处〔改〕改成错值 ⇒ `verify_ledger.py` 或字段断言必须报 FAIL**（证明门禁真在守，而不是橡皮图章）；在临时副本上做，不动真件。

## 交付
`C1_REPORT.md`（§A 十节骨架；`[0]` 直答：6 处落地几处/跳过几处+原因）· `c1_changes.json`（逐处 before/after sha）· `_HANDOFF.md`（#14/#11/#17 转交）· `snapshots_before/` + `runs/`（改前改后 verify 原文）· `verify_c1.py`（**EXIT=0 + `verdict tally` 行**）

## 回报 `[0]`
① 6 处各自动作与 sha ② game_body_0927 是否建成（archived 件路径）③ verify_ledger 改前/改后两次 EXIT ④ 官方读数复现结果 ⑤ 反向验证做法与结果 ⑥ `verdict tally` 原文

## 底线
> **宁可交"6 处落地 3 处、2 处发现会被 verify_ledger 拒绝因而回滚、1 处转交"，也不要交"6 处全改但门禁没跑"。**
> **任何一次改后 EXIT≠0 必须回滚 —— 台账是全库引用基准，不能带着红灯。**
