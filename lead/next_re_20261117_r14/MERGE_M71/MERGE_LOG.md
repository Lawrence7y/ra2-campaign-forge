# M71 MERGE LOG — 并表 11 行（NAMED_PUSH_AUDIT12，S22_B4 工厂族）

- 时间：2026-11-20T14:02:22+08:00（before 采集） / 2026-11-20T14:06:34+08:00（after 采集）
- 角色：本轮唯一 COVERAGE 写者；仅写 `COVERAGE/coverage.tsv` 与 `COVERAGE/PANEL.md`（及本 `MERGE_M71/` 交付目录）。
- 未 git commit；未碰 `R14_COMMON.md`、`STATUS_BOARD.md`、台账、`NAMED_PUSH_*`、`NAMED_PUSH_AUDIT*`、`INVENTORY`。

## 1. 输入与交集

- 审计表：`NAMED_PUSH_AUDIT12/verdict.tsv` — 11 行、8 列、verdict 全 PASS。
- delta 来源：`NAMED_PUSH_S22_B4/delta.tsv` — 11 行、6 列。
- 11 entry：`006C5210` `006C5390` `006C5510` `006C5690` `006C5810` `006C5990` `006C5B10` `006C5C90` `006C5E10` `006C5F90` `006C6110`。
- 交集 `verdict ∩ delta` = 正好 11 行，等于上述 11 entry，无多无少；`verdict−delta`、`delta−verdict` 均为空；每 entry 在 coverage 恰好出现 1 次。
- atlas 内校验（entry 小写归一，复刻 `strict_panel.py` 的 `ne()` 归一化）：11/11 全在 atlas 内。
- 不进并表：`NAMED_PUSH_S22_B5/delta.tsv` 为空（0 数据行；9 行 vector 族四环齐全 0，③b 全败于 {0,1} AL 布尔）。

## 2. Lead 前置复核（改前）

| 指标 | 卡片给定 | 盘上实算 | 一致 |
|---|---:|---:|---|
| 数据行数 | 18,498 | 18,498 | ✅ |
| 全表 `[已证]` | 1,591 | 1,591 | ✅ |
| atlas 内 `[已证]` | 1,585 | 1,585 | ✅ |
| atlas 外 `[已证]` | 6 | 6 | ✅ |
| S22 atlas 内 proved | 98 | 98 | ✅ |

任一不符即停下的条件均未触发。

## 3. coverage.tsv 改动

对 11 行各改 3 列，逐行断言其余 5 列逐字节不变：

- 第 4 列 `one_line_semantics` ← `NAMED_PUSH_S22_B4/delta.tsv` 第 4 列原文照抄（逐字节核对 PASS）；
- 第 5 列 `grade`：`[未证]` → `[已证]`；
- 第 6 列 `evidence_path`：`EVIDENCE/classification_trace.tsv#<entry>` 等原值 → `NAMED_PUSH_AUDIT12/VERDICT.md`。

第 1/2/3/7/8 列不动。数据行仍 18,498、8 列、TAB 分隔；行数不增不减。
改动行（文件 1-based 行号）：9352, 9357, 9362, 9367, 9372, 9377, 9382, 9387, 9392, 9397, 9402。

## 4. PANEL.md 同步

- 全表 `[已证]` / atlas 内 `[已证]`：`1,591 / 1,585` → `1,602 / 1,596`；atlas 外仍 6。
- 面板主表 S22 行：`proved 98→109`、`proved_pct 2.02→2.25`（109/4851）；named 各列不动。
- 面板主表 TOTAL 行：`proved 1585→1596`、`proved_pct 12.27→12.36`。
- 严格口径双列表 S22 行：`proved 98→109 / 2.02→2.25`，`proved_strict 55→66 / 1.13→1.36`（66/4851）。
- 严格口径双列表 TOTAL 行：`proved 1585→1596 / 12.27→12.36`，`proved_strict 1268→1279 / 9.82→9.90`。
- 备注列追加（S22 与 TOTAL 备注首部，以及全表/atlas 单元格备注），原文：
  `M71 并表 NAMED_PUSH_AUDIT12 PASS 11 行（S22_B4 工厂族）；S22 named 池至此清空（B1 18 + B2 18 + B3 13 + B4 13 + B5 9 = 71 = 全池），B5 的 9 行 vector 族四环齐全 0（③b 全败于 {0,1} AL 布尔）`
- 标题行首追加 M71 并表摘要（与既有 M70/M69/… 同格式）。
- strict 用带方括号字面 `[未证]` 口径（`if "[未证]" not in sem:`）；11 行新语义逐行核 delta 第 4 列均不含字面 `[未证]`，故 strict 随 proved 同增 11（S22 +11、TOTAL +11）。

## 5. M71 第三条披露（原样写入，不许省略/改写）

- 位置：`PANEL.md` 第 155–159 行（起始行 155），紧接 M70 披露（150–154 行）之后。
- 内容：逐字节从 `M71-MERGE.md` 的 fenced block 提取并插入，`verify.py` 断言 verbatim-identical = PASS。
- 披露要点：④ 的严格读法会翻转 ≥21 行（未执行、待成文规则）；Lead 处置「不追溯、先披露」；更正 M70 披露强度（静态意义上准确但不得写成绝对，存在 0x41C250 按 CLSID 创建路径）；AddRef/Release 为 `mov eax,1; ret 4` 桩、Release 实际不释放，「失败 Release」实走 vt+0x20 删除析构器。

## 6. 达标翻转

- 名义达标：3/22 = S15 / S16 / S17（未变）。
- 严格达标：1/22 = S17（未变）。
- **无达标翻转。** 11 行全属 S22，S22 不参与达标排名（门槛 2426，proved 109 / strict 66 远低于门槛）。

## 7. 复核结果

- `MERGE_M71/verify.py`：OVERALL **ALL PASS**（含交集=11、披露逐字节核对、11 行三列核对、atlas 内校验、行数/列数、全表/atlas 内/外已证数、S22 proved/strict、无翻转）。
- `MERGE_M71/precheck.py`：改前交集=11、前置五项全部吻合、11 行全 atlas 内。
- `MERGE_M71/simulate.py`：改后全表 1602 / atlas 内 1596 / atlas 外 6；S22 proved 109 strict 66；TOTAL proved 1596 strict 1279；NO_FLIP。
- 改前/改后 mtime/字节/sha256 见 `MERGE_M71/BEFORE_AFTER.txt`。
- 强制指标汇总见 `MERGE_M71/VERIFY.txt`。
