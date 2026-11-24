# M36 PROGRESS — 6 行语义栏补写合并（SEMFIX-6）

时点：2026-11-18（Asia/Shanghai）

## 交付结果

| 项 | 值 |
|---|---|
| 修改行数 | **6**（只改第 4 列 one_line_semantics） |
| 数据行数 | 18,431（前后不变） |
| conflict=1 | 254（前后不变） |
| grade 变更 | 0（6 行盘上 / delta 均 `[已证]`） |
| name 差异（盘上 vs delta） | 0（逐字相同） |
| 其他列差异 | 0（entry / subsystem / grade / evidence_path / n_sources / conflict 逐字节不变） |
| 新语义长度 | 220 / 232 / 198 / 245 / 298 / 236（与卡面一致） |
| 改动行号 | 379 / 380 / 526 / 537 / 697 / 1195 |

## 直方图（前后完全相等）

| grade | 前 | 后 |
|---|---:|---:|
| [已证] | 1,366 | 1,366 |
| [静态推断] | 6,041 | 6,041 |
| [未证] | 11,024 | 11,024 |

## 「`[已证]` 且语义栏自陈未证」行数（两个口径）

| 口径 | 前 | 后 | 说明 |
|---|---:|---:|---|
| A：`未定\|弱信号\|线索\|槽语义未证` | 10 | 10 | M35 使用的窄口径；剩余 10 行均为 S22，按卡面不裁 |
| B：A + `rtti-vftable` | 16 | 10 | 6 行模板语替换后，B 从 16 降到 10 |

## coverage SHA-256

- 改前：`4570f4cafa314a2f6f1800688ae7eb9808697d2d57c0f71904ffe59d7b4c61e1`
- 改后：`815683a15081ee3ec219423bd170809b0f292c77228043a728008ae6249ffd55`
- 备份：`_hygiene\coverage.M36.bak`（改前二进制副本，SHA 同改前：`4570f4cafa314a2f6f1800688ae7eb9808697d2d57c0f71904ffe59d7b4c61e1`）

## 产出文件

- `COVERAGE\coverage.tsv`（6 行第 4 列替换，其余零差异）
- `M36\MERGE_LOG.tsv`（6 行 entry / old_semantics / new_semantics / source_card）
- `M36\PROGRESS.md`（本文件）
- `_hygiene\coverage.M36.bak`（改前备份）
