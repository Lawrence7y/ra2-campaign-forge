# REPORT.md - R17-R40-FACTINDEX_V3 交付报告

## 改动范围
- 只写入新目录 `lead\next_re_20261117_r14\R17_R40_FACTINDEX_V3\`；未修改 `lead\next_re_20261117_r14\R17_R34_FACT_INDEX\` 与 `lead\next_re_20261117_r14\R17_R38_FACTINDEX_FIX\` 下任何文件。
- 产物：`FACT_INDEX.tsv`、`README.md`、`conflicts.md`、`REPORT.md`。

## 升级内容
- `FACT_INDEX.tsv`：以 v2 为基底，F01-F21 原文不动，仅在末尾追加 F22-F26，合计 26 条；fact_id 连续，已有编号不重排。
- 新增行逐条取自卡面：F22 记 1,654 与三项强制同引限定；F23 记 ④ 三口径；F24 记 R_OK 863、R_TRACE_ONLY 791 与边界；F25 记 strict 1,331 的上界方向；F26 记 DoD 上限与 D-49 裁定。
- F22-F25 是本轮引用最多且最易被断章引用的四条，`limitations` 均非空并保留强制同引约束；`README.md` 已显著标注。
- `conflicts.md`：沿用 v2；本轮无新增矛盾。
- `README.md`：更新主索引编号与用法，并强调 F22-F25 不可断章引用。

## 自检
- TSV 表头为 5 列；数据行 fact_id 为 F01-F26 连续编号，且每行 5 列。
- F01-F21 与 v2 原文逐字节一致；新增行无内嵌制表符、换行符。
- 两个只读源目录的文件清单与 SHA-256 写入前后一致。
- CR 校验：4 个产物逐文件统计回车符，均为 0（合计 0），LF 合规。
