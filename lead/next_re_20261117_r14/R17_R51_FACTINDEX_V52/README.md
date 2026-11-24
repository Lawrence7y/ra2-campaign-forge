# R17_R51_FACTINDEX_V52 — 用法说明（FACT_INDEX v5.2）

## 口径
- 基底：v5.1（`R17_R47_GRADE_NORM\FACT_INDEX.tsv`）；F01–F49 不改号，新增 F50–F54。
- 总条数：**54**。
- `grade` 仍只允许 4 档：`[已证]` / `[静态推断]` / `[流程]` / `未取得`。
- `evidence_paths` 一律仓库根相对；无裸行号；括号内无分号。
- 全部产物 LF、无 CR。

## 文件
- `FACT_INDEX.tsv`：v5.2 主表，5 列，54 条。
- `CHANGES.md`：逐条改动与依据产物。
- `REPORT.md`：计数、路径解析与格式自证。
- `README.md`：本说明。

## grade 统计
| grade | 条数 |
|---|---:|
| [已证] | 27 |
| [静态推断] | 1 |
| [流程] | 24 |
| 未取得 | 2 |
| 合计 | 54 |
