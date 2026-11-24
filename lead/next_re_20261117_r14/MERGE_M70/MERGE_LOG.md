# M70 MERGE LOG — 并表 11 行（NAMED_PUSH_AUDIT11，S22 TClassFactory 同族）

- 时间：2026-11-20T13:35:10+08:00（before 采集） / 2026-11-20T13:38:04+08:00（after 采集）
- 角色：本轮唯一 COVERAGE 写者；仅写 `COVERAGE/coverage.tsv` 与 `COVERAGE/PANEL.md`（及本 `MERGE_M70/` 交付目录）。
- 未 git commit；未碰 `R14_COMMON.md`、`STATUS_BOARD.md`、台账、`NAMED_PUSH_*`、`NAMED_PUSH_AUDIT*`、`INVENTORY`。

## 1. 输入与交集

- 审计表：`NAMED_PUSH_AUDIT11/verdict.tsv` — 11 行、8 列、verdict 全 PASS。
- delta 来源：`NAMED_PUSH_S22_B3/delta.tsv` — 11 行、6 列。
- 11 entry：`006C2B10` `006C2C90` `006C2E10` `006C2F90` `006C3110` `006C3290` `006C3410` `006C3590` `006C3890` `006C3A10` `006C3B90`。
- 交集 `verdict ∩ delta ∩ coverage` = 正好 11 行，等于上述 11 entry，无多无少；`verdict−delta`、`delta−verdict` 均为空；每 entry 在 coverage 恰好出现 1 次。
- atlas 内校验（entry 小写归一，复刻 `strict_panel.py` 的 `ne()` 归一化）：11/11 全在 atlas 内。

## 2. Lead 前置复核（改前）

| 指标 | 卡片给定 | 盘上实算 | 一致 |
|---|---:|---:|---|
| 数据行数 | 18,498 | 18,498 | ✅ |
| 全表 `[已证]` | 1,580 | 1,580 | ✅ |
| atlas 内 `[已证]` | 1,574 | 1,574 | ✅ |
| atlas 外 `[已证]` | 6 | 6 | ✅ |
| S22 atlas 内 proved | 87 | 87 | ✅ |

任一不符即停下的条件均未触发。

## 3. coverage.tsv 改动

对 11 行各改 3 列，逐行断言其余 5 列逐字节不变：

- 第 4 列 `one_line_semantics` ← `NAMED_PUSH_S22_B3/delta.tsv` 第 4 列原文照抄（逐字节核对 PASS）；
- 第 5 列 `grade`：`[未证]` → `[已证]`；
- 第 6 列 `evidence_path`：`EVIDENCE/classification_trace.tsv#<entry>` → `NAMED_PUSH_AUDIT11/VERDICT.md`。

第 1/2/3/7/8 列不动。数据行仍 18,498、8 列、TAB 分隔；行数不增不减。
改动行（文件 1-based 行号）：9222, 9227, 9232, 9237, 9242, 9247, 9252, 9257, 9267, 9272, 9277。

## 4. PANEL.md 同步

- 全表 `[已证]` / atlas 内 `[已证]`：`1,580 / 1,574` → `1,591 / 1,585`；atlas 外仍 6。
- 面板主表 S22 行：`proved 87→98`、`proved_pct 1.79→2.02`（98/4851）；strict 列 34/0.70 不动（该列是 named_S(strict)，非 proved_strict）。
- 面板主表 TOTAL 行：`proved 1574→1585`、`proved_pct 12.19→12.27`。
- 严格口径双列表 S22 行：`proved 87→98 / 1.79→2.02`，`proved_strict 44→55 / 0.91→1.13`（55/4851）。
- 严格口径双列表 TOTAL 行：`proved 1574→1585 / 12.19→12.27`，`proved_strict 1257→1268 / 9.73→9.82`。
- 备注列追加（S22 与 TOTAL 备注首部，以及全表/atlas 单元格备注）：
  `M70 并表 NAMED_PUSH_AUDIT11 PASS 11 行（S22 TClassFactory 同族），evidence_path 改指 NAMED_PUSH_AUDIT11/VERDICT.md`
- 标题行首追加 M70 并表摘要（与既有 M69/M68/… 同格式）。
- strict 用带方括号字面 `[未证]` 口径（`strict_panel.py` 第 78 行 `if "[未证]" not in sem:`）；11 行新语义逐行核 delta 第 4 列均不含字面 `[未证]`，故 strict 随 proved 同增 11（S22 +11、TOTAL +11）。

## 5. M70 披露（不许省略、不许改写）

- 位置：`PANEL.md` 第 150–154 行（起始行 150），紧接 M69 披露（146–149 行）之后。
- 内容：逐字节从 `M70-MERGE.md` 第 46–50 行提取并插入，`verify.py` 断言 verbatim-identical = PASS。
- 披露要点：工厂族 ③b② 的"消费方"在函数内部、本 entry 自身返回码无消费方；两处措辞级缺口（不判 FAIL）；引用时不得表述为「该工厂函数被外部调用并检查其返回码」。

## 6. 达标翻转

- 名义达标：3/22 = S15 / S16 / S17（未变）。
- 严格达标：1/22 = S17（未变）。
- **无达标翻转。** 11 行全属 S22，S22 不参与达标排名（门槛 2426，proved 98 / strict 55 远低于门槛）。

## 7. 复核结果

- `MERGE_M70/verify.py`：OVERALL **ALL PASS**（含披露逐字节核对、11 行三列核对、atlas 内校验、行数/列数、全表/atlas 内/外已证数、S22 proved/strict、无翻转）。
- `MERGE_M70/compute.py`：S22 proved 98 strict 55；TOTAL proved 1585 strict 1268；NO_FLIP True。
- 改前/改后 mtime/字节/sha256 见 `MERGE_M70/BEFORE_AFTER.txt`。
- 强制指标汇总见 `MERGE_M70/VERIFY.txt`。
