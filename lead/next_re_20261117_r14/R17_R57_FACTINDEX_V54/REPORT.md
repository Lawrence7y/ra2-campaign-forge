# REPORT.md — R17_R57_FACTINDEX_V54（FACT_INDEX v5.4）

## 1. 基底与产物

- 基底：`R17_R56_FACTINDEX_V53\FACT_INDEX.tsv`（v5.3，54 条）。
- 产物：`FACT_INDEX.tsv` / `CHANGES.md` / `README.md` / `REPORT.md` / `anchor_check.tsv`。
- 未修改任何既有 FACT_INDEX 目录。

## 2. 自证

| 检查 | 结果 |
|---|---|
| 数据行 | 54 |
| fact_id 连续 | F01–F54，无跳号 |
| 列数 | 全表恒 5 |
| grade 四档 | 27 / 1 / 24 / 2 = 54，无第五档 |
| 改动行数 | 16（仅 evidence_paths 列） |
| 未动行数 | 38（含表头共 39 行逐字节相同） |
| CR 字节 | 0 |
| STATUS_BOARD 段锚残留 | 0 |

## 3. 边界与未取得（如实记）

- 本版**不新增任何技术结论**，只改证据锚的落点。
- **未取得**：`BOARD_ARCHIVE.md` 内部段的**行号级**定位未提供（archive 持续追加，行号必然位移；本版一律用段标题锚，不写行号）。
- **未取得**：`LEAD_LOCK` 与 `GOAL_THREE_TARGETS_20261018.md` 的锚点虽经归一化匹配 117/117 命中，但这两份文件**同样会被追加**，其段标题稳定性未被单独证明；若将来重排章节，这些锚需重新核验。
- 锚点核验口径见 `CHANGES.md` §2——**该口径本身经过三次纠错才成立**，换人或换脚本复核时必须沿用同一口径，否则数字不可比。
