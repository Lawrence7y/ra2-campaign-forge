# M35 PROGRESS — 66 行语义栏补写合并（SEMFIX-S10 25 + SEMFIX-REST 41）

时点：2026-11-18（Asia/Shanghai）

## 交付结果

| 项 | 值 |
|---|---|
| 修改行数 | **66**（S10 25 + REST 41，只改第 4 列 one_line_semantics） |
| 数据行数 | 18,431（前后不变） |
| conflict=1 | 254（前后不变） |
| name 差异（盘上 vs delta） | 0（逐字相同） |
| grade 变更 | 0（盘上全部 [已证]，delta 全部 [已证]） |
| 其他列差异 | 0（subsystem/evidence_path/n_sources/conflict 等逐字节不变） |

## 直方图（前后必须相等）

| grade | 前 | 后 |
|---|---:|---:|
| [已证] | 1,366 | 1366 |
| [静态推断] | 6,041 | 6041 |
| [未证] | 11,024 | 11024 |

**结论：完全相等 ✓**

## 实质产出指标：「[已证] 且语义栏含 未定/弱信号/线索/槽语义未证」行数

- **前：76**（实测；其中非 S22 = 66，S22 = 10）
- **后：10**（实测；全部为 S22，非 S22 = 0）

**76 → 10 ✓**（剩余 10 行 S22 按 §1 不裁）

## coverage SHA-256

- 改前：`f7080727f1f3825e30c0faf40b8565e02e7f9107208344c7c1ddfce855d2f08e`
- 改后：`4570f4cafa314a2f6f1800688ae7eb9808697d2d57c0f71904ffe59d7b4c61e1`
- 备份：`_hygiene\coverage.M35.bak`（改前二进制副本，SHA 同改前）

## 产出文件

- `COVERAGE\coverage.tsv`（66 行第 4 列替换，其余零差异）
- `COVERAGE\PANEL.md`（新增 M35 并表说明，不改任何面板数字）
- `M35\MERGE_LOG.tsv`（66 行 entry / old_semantics前40 / new_semantics前40 / 来源卡）
- `_hygiene\coverage.M35.bak`（改前备份）
