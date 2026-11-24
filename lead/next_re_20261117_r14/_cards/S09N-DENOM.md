# S09N-DENOM — 面板分母与表行数一致性普查

## 任务

`COVERAGE\PANEL.md` 里每个子系统的 `n` 列，与 `COVERAGE\coverage.tsv` 里该子系统的实际数据行数，**是否一致**？不一致的，差在哪、谁对。

## 已确认的起点（不要再重复验证，直接用）

- `coverage.tsv`：数据行 **18,498**，每行 **8 列**、行内**制表符**分隔；表头 1 行、**逗号**分隔。第 5 列 = grade，第 2 列 = subsystem。
- PANEL.md 对 **S09** 记 `n = 1051`；而 `coverage.tsv` 中 `subsystem == S09` 的行数是 **1,102**。差 **51** 行。
- S09 中落在 `function_atlas.tsv`（`D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv`，12,916 数据行，第 1 列 `entry`）内的只有 **198** 行，atlas 外 **904** 行。
  ⇒ **面板的 n 不是"atlas 内行数"**，这个候选已被证伪。

## 必须完成的事

1. **逐子系统普查（22 行）**：对每个子系统给出
   - `cov_rows`：`coverage.tsv` 中该 subsystem 的数据行数
   - `panel_n`：`PANEL.md` 中该子系统的 n 值（把出现位置的行号记下来）
   - `diff = cov_rows - panel_n`
   - `atlas_in_rows`：该子系统行中 entry 在 atlas 内的行数

2. **判定 n 的真实口径**：用数据证伪，不要猜。至少排除/确认这些候选：
   - atlas 内行数（已被 S09 证伪：198 ≠ 1051）
   - 去掉名字空行的行数
   - 去掉 `initterm_thunk_NNNN` 的行数
   - 旧快照遗留（某次合并后未随表更新）
   - 其它你能用数验证的口径
   给结论时必须附"若口径为 X，则 22 个子系统的 diff 应全为 0 / 应呈现某模式"的检验结果。

3. **51 行的去向**：找出 S09 那 51 行差是**行被改过 subsystem**（从别处改归 S09）还是**面板从未随某次合并更新**。给出可复现的筛选命令与命中明细。

4. **影响面**：
   - 若 n 需更正，逐个给出更正后的 `n`，以及受影响百分比（named / proved）与 DoD 阈值 `ceil(0.9*n)`、`ceil(0.5*n)`。
   - **明确回答：更正后有没有任何子系统的达标结论发生翻转？**（达标 ↔ 未达标）

5. **顺带比对 named 列**：把 PANEL 的 named 值与按 `coverage.tsv` 第 3 列重算的值逐子系统比对。重算口径：
   - `named_pct_L`：非空且不以 `sub_` 开头
   - `named_pct_S(R14)`：在 L 基础上再排除匹配 `::sub_[0-9A-Fa-f]+$` 的
   - `named_pct_S(strict)`：在 S 基础上再排除含 `::slotN` / `::vslotN` 的
   报告三者与 PANEL 对应列的差。

## 输出

- `S09N_DENOM\REPORT.md`：结论 + 证据 + 命令
- `S09N_DENOM\n_table.tsv`：表头 `subsystem	cov_rows	panel_n	diff	atlas_in_rows	verdict`，22 行数据
- `S09N_DENOM\named_check.tsv`：表头 `subsystem	panel_named_L	recalc_L	panel_S	recalc_S	panel_strict	recalc_strict`

## 纪律

- **不得修改** `PANEL.md`、`coverage.tsv`、`R14_COMMON.md` 或任何既有台账文件；只写 `S09N_DENOM\` 目录。
- 结论必须能被一条可复现命令验证；只给数字不给命令的不算完成。
- 发现面板对但表错、或两边都错，都要如实说，不要为了"面板是对的"而挑口径。
