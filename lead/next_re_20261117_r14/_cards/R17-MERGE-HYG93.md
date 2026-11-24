> 卡号：R17-MERGE-HYG93
> 角色：**合并员**（`work/cn:hy4flash-free`）—— **`coverage.tsv` 的唯一写者**
> 写域：`COVERAGE\coverage.tsv`（唯一被允许改的共享文件）+ `lead\next_re_20261117_r14\R17_MERGE_HYG93\**`
> 日期：2026-11-21（R17 第 1 轮）
> **本卡是全项目唯一被授权改 `coverage.tsv` 的卡。单写者纪律：开工前确认没有别的卡在写它（本卡发出时无并发写者）。**

## 0. 绝对边界

1. **只允许改 `COVERAGE\coverage.tsv` 的第 4 列（`one_line_semantics`），且只允许改下面点名的 93 行。**
2. **禁止**改第 1/2/3/5/6/7/8 列、禁止改 `grade`、禁止改任何数字、禁止增删行、禁止改表头。
3. **禁止**改 `COVERAGE\PANEL.md` / `R14_COMMON.md` / 台账 / 看板 / `_cards\` / 其它卡目录。
4. 不涉及逆向：不读 `gamemd.exe`、不跑 capstone/Ghidra/pefile、不读 `EVIDENCE\` 原始输出。
5. 不许编造。

## 1. 输入（6 份 delta，全部已由 Lead 独立对盘校验通过）

| 卡目录 | 行数 | 改法 |
|---|---:|---|
| `R17_HYG_A1_B1\delta.tsv` | 16 | 追加 |
| `R17_HYG_A1_B2\delta.tsv` | 16 | 追加 |
| `R17_HYG_A1_B3\delta.tsv` | 16 | 追加 |
| `R17_HYG_A1_B4\delta.tsv` | 16 | 追加 |
| `R17_HYG_A1_B5\delta.tsv` | 16 | 追加 |
| `R17_HYG_A1_B6\delta.tsv` | 11 | 追加 |
| `R17_HYG_A1_B6\delta.tsv` 中另含 2 行 | 2 | **替换**（A2：004AF540 / 004B5AB0） |

- **A1 共 91 行**：`new_col4 = old_col4 + SENTENCE`，`SENTENCE` =
  `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`（65 字符）
- **A2 共 2 行**：把第 4 列末尾的 `（D-47 披露指针：R14_COMMON §12.6 与 PANEL 对应披露）` **替换**为
  `（本行 ④ 为 direct call 形态 1，不属于「活 vtable 槽位」形态；D-47(A) 的披露纪律不适用于本行，故不引该披露）`
- 合计改动 **93 行**（91 追加 + 2 替换）。

## 2. 写盘铁律（逐条执行，缺一不可）

1. **先落 before 备份**：把当前 `coverage.tsv` 复制到 `R17_MERGE_HYG93\coverage.before.tsv`，记 `bytes` / `mtime` / `sha256`。
   （Lead 侧另有一份 `R17_LEAD_BASELINE\coverage.before_hyg.tsv`，`sha256` 前缀 `A07A74C1`，可用作交叉核对。）
2. **禁止在 PowerShell 里用 `$a` / `$b` 等单字母变量**（R16 11:49 事故根因：`$b` 冲突把 41,860 B 的看板覆写成 1,829 B）。
3. 读全文 → 在内存里构造**完整新字节数组** → 断言 → **一次性写盘** → 读回复验。
4. 追加后必须验证「**旧长度前缀的 sha256 == 改动前**」不可行（本卡是行内改，不是纯追加）⇒ 改用
   **「逐行比对：只有点名的 93 行不同，其余 18,405 行逐字节相同」**这一断言，并在报告里报出实际比对行数。
5. 行尾：`coverage.tsv` 现为 bare LF（无 CRLF）。**不得**引入 CRLF；写盘后复核 CR 计数仍为 **0**。

## 3. 断言（全部必须为真；任一为假 ⇒ 立即停止、**不写盘**、报差异）

- N1：数据行数改动前后都是 **18,498**；每行 8 列；表头字节不变。
- N2：**恰好 93 行**的第 4 列发生变化；其余 **18,405 行**逐字节相同（含其第 4 列）。
- N3：91 行满足 `len_after - len_before == 65` 且 `after == before + SENTENCE`。
- N4：2 行（`004AF540` / `004B5AB0`）满足「旧段恰好 1 次且在末尾、替换后**不含** `§12.6` 子串、**仍含** `④ direct call`」。
- N5：`grade` 列计数前后完全相同：`[已证] 1,654 / [静态推断] 5,875 / [未证] 10,969`。
- N6：`§12.6` 命中数：改动前 **234** → 改动后**必须等于 323**（234 + 91 − 2）。
- N7：`§12.4` 残留仍为 **0**；`CLSID None` 仍为 **0**。
- N8：④ 口径 A 仍为 **458**、口径 B 仍为 **291**、宽口径仍为 **293**、完全无 ④ 仍为 **1,196**（本卡只加披露句，不改 ④ 形态，这些数**不应变动**；若变动即报异常）。

## 4. 产物（`R17_MERGE_HYG93\`）

1. `merge.py`（或 `.ps1`）—— 可复跑
2. `coverage.before.tsv` —— 改动前完整副本
3. `MERGE_REPORT.md` —— 含 §2 的 before/after 三元组（bytes / mtime / sha256）、§3 的 N1–N8 逐项实测值、以及「哪些行变了」的完整行号清单（93 个行号）
4. `changed_rows.tsv` —— `line	entry	kind(add|replace)	len_before	len_after`

## 5. 回复里只给什么

只给：before/after 的 bytes + sha256 前 12 位、N1–N8 每项实测值（一行一项）、以及「N2 实测变化行数」。**不要贴全表、不要贴脚本全文。**
