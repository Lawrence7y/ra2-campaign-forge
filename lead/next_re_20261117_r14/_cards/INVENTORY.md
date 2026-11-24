# INVENTORY — 具名候选池余量与预期产出（收口判据）

## 为什么要这张卡

具名通道已经跑了 9 批，实测四环齐全率在 0.06–0.89 之间波动，且**池正在耗尽**：

- S20 具名池仅 38 行 → B1 18 + B2 18 + B3 2，**已用尽**
- S12 具名池仅 33 行 → B1 18 + B2 15，**已用尽**
- S06 具名池 46 行 → B1 18 + B2 18 + B3 10，**已用尽**
- S14 具名 51 行但其中 16 个是 `fn_` 伪名 → 实际 35 行，B1 18 + B2 18，**已用尽**

**需要一张表回答：还剩哪些池、每个池还能产出多少行、什么时候这条线彻底结束。** 没有这个，就会继续派无意义的批次。

## 输入（全部只读）

- `lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv`（1,733 行；含 entry / subsystem / name / grade / p3b2_named）
- `lead\next_re_20261117_r14\COVERAGE\coverage.tsv`（18,498 行、8 列；第 5 列 grade 为当前真值）
- `lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv`（12,916 行；`entry` 小写须归一）
- 已跑过的批次目录（用于算"已消费"）：`NAMED_PUSH_*` 下每个含 `delta.tsv` 与 `REPORT.md` 的目录
  - 注意：**已消费 ≠ 已并表**。一批里报审 18 行、只有 N 行进 delta，但那 18 行都已核过，**不该再派**。所以"已消费"要按各批 `REPORT.md` 里**核过的行**算，不只是 delta。

## 要产出什么

### 表 A · 逐子系统余量

`subsystem | named_pool_total | fn_like_excluded | real_named | consumed | remaining | measured_rate | expected_yield`

- `named_pool_total`：`hits_detail` 中该子系统 `p3b2_named == True` 的行数
- `fn_like_excluded`：其中名字匹配 `^(fn_|.*::fn_)` 的行数（伪名，② 物理不可得）
- `real_named` = `named_pool_total − fn_like_excluded`
- `consumed`：各 `NAMED_PUSH_*` 批次 `REPORT.md` 里已核过的、属于该子系统的行数（**去重**）
- `remaining` = `real_named − consumed`
- `measured_rate`：该子系统已跑批次里 `四环齐全 / 核过行数` 的加权平均
- `expected_yield` = `remaining × measured_rate`（**预期产出，不是保证**）

### 表 B · 总量与收口判据

| 量 | 值 |
|---|---|
| 全表 `real_named` 合计 | ? |
| 已消费合计 | ? |
| 剩余合计 | ? |
| 加权平均四环齐全率 | ? |
| **预期可再产出** | **? 行** |
| 折成全表 `[已证]` 增幅 | ? 个百分点 |

### 表 C · 明确回答三个问题

1. **还有几个子系统有未消费的具名候选？各剩多少行？**
2. **按实测率，预期还能并入多少行？这个数相对于"事实底座完整性"是否还有实质意义？**（给出你判断所依据的两个数）
3. **这条线什么时候结束？**——给出一个可操作的停止判据（例如"剩余 < N 行"或"预期产出 < M 行"），并说明为什么是这个数。

### 表 D · 未消费但**不该派**的行

列出那些名字是 `fn_`/`sub_` 伪名、或虽有名但名字本身给不出类身份的行数（按子系统），说明为什么它们即使派了也大概率为 0。

## 输出

- `INVENTORY\inventory.tsv`（表 A，22 行）
- `INVENTORY\REPORT.md`（表 B + 表 C 三问 + 表 D）
- `INVENTORY\inventory.py`（可复跑）

## 纪律

- **只读**。不许改 `coverage.tsv`、`PANEL.md`、`R14_COMMON.md`、台账、任何 `NAMED_PUSH_*` 与 `RESCAN_MOVED`；只写 `INVENTORY\`。
- `consumed` 的统计必须**列出你实际读了哪些批次的 REPORT**，并说明"核过行数"从哪里取；只给数字不给来源的不算完成。
- 22 行一行不许跳，池为 0 的照写 0。
- `expected_yield` 必须标为**预期**，不许写成"可产出"。
