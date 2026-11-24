# R17-R42-F23-FIX · REPORT

## 结论

- 基底：`R17_R40_FACTINDEX_V3/FACT_INDEX.tsv`（v3）。
- 产物：`FACT_INDEX.tsv`（v3.1，26 条），`REPORT.md`。
- 修改范围：仅 `F23` 的 `limitations` 一格；`F01`–`F22`、`F24`–`F26` 25 条逐字节不动。
- 三个前序 FACT_INDEX 目录未写入。

## 改前原文（F23 limitations）

口径必须写明；宽松正则 /direct call/ 会多计 10 行（「无 direct caller」等字样），判形态须用全串「④ direct call」。

## 改后原文（F23 limitations）

口径必须写明。另：宽松子串 direct call 命中 12 行，按「减去含全串 ④ direct call 的 2 行」的减法读法为多计 10；按「相对宽口径 W=293 的集合差」为 9（因其中 3 行本已在 W 内）。两读法并列，引用时须注明是哪一种，不得单独写 10 或 9。该 12 行中 6 行为否定式（无 direct caller 等）、2 行为 callers 计数，真正非否定的多计仅 3 行且全为 direct caller。判 ④ 形态须用全串「④ direct call」。

## 校验

- 文件行数/记录数：基底与产物均为 28 行（含末尾空行），记录 26 条。
- 仅有差异行：24（即 F23 所在行）；差异格数：1。
- 其余 25 条逐字节一致：PASS（25/25，Buffer.equals）。
- 表头逐字节一致：PASS。
- F23 前四列（fact_id/statement/grade/evidence_paths）逐字节未变：PASS；列数仍为 5。
- 末尾换行保持：PASS。
- CR（0x0D）校验：FACT_INDEX.tsv PASS（无 CR）；REPORT.md PASS（无 CR，写入后自校验）。
- 三个前序目录文件内容哈希前后一致：PASS。

校验方式：按原始字节读取，以 `\n` 切行后对每一行做 `Buffer.equals`；25 条其余事实为 F01–F22 与 F24–F26；F23 行单独校验前四列字节前缀与第五列替换。产物写出时不引入 `\r`。
