# M74 MERGE LOG — 并表 6 行（NAMED_PUSH_AUDIT16 PASS 6/6，全 S13）

- 时间：2026-11-20T15:57:55+08:00（before 采集） / 2026-11-20T16:17:11+08:00（after 采集）；复核 2026-11-20T16:17:45+08:00。
- 角色：本轮唯一 COVERAGE 写者；仅写 `COVERAGE/coverage.tsv` 与 `COVERAGE/PANEL.md`（及本 `MERGE_M74/` 交付目录）。
- 未 git commit；未碰 `R14_COMMON.md`、`STATUS_BOARD.md`、台账、`BOARD_ARCHIVE.md`、任何 `NAMED_PUSH_*` 与 `AUDIT*`、`INVENTORY`。

## 1. 输入与交集（并行数 = 本次并表行数 = 6）

| 审计表 | delta 来源 | 应并行数 | 实算 |
|---|---|---:|---:|
| `NAMED_PUSH_AUDIT16/verdict.tsv` | `NAMED_PUSH_S13_B1/delta.tsv` | 6 | 6 |

- 6 entry：`004684E0`、`00629FD0`、`0075E0C0`、`0075E2C0`、`00772CD0`、`00772EB0`（全 S13）。
- 交集 `NAMED_PUSH_AUDIT16/verdict.tsv ∩ NAMED_PUSH_S13_B1/delta.tsv` = **正好 6 行** = 预期 6 entry，无多无少；verdict 6/6 全 PASS；AUDIT-only / DELTA-only = 0 / 0。
- 6 entry 各自在 coverage 恰好出现 1 次。
- atlas 内校验（entry 小写归一，`function_atlas.tsv` 12,916 数据行）：**6/6 全在 atlas 内**。
- delta 第 4 列逐行核：6 行语义均不含字面 `[未证]`，故 strict 随 proved 同增。
- 交集正好 6 行的硬条件已满足，未触发「停下报告」。

## 2. 否决史与 Lead 裁定（卡片特别说明）

- 这 6 entry 曾被 `S13-PUSH` 产出、因「④ 与 ② 共用同一虚表槽」被 Lead 拒绝并表。
- 本批把 ④ 改锚到行外构造器的 `.text` 写点重做，异族审计（`NAMED_PUSH_AUDIT16`）判 6/6 PASS。
- 审计同时明确两点，并表时必须一并记录：
  - (a)「④ 与 ② 是两条独立证据链」**不成立**：④ = ①表是活的（`.text` 构造器写点，这半边独立）+ ②entry 占该表第 N 槽（读 `.rdata` 的 `mem[vt+4N]==entry`，正是 ② 判类用的同一条数据）。比旧版多了一半独立事实，**枢轴未消除**。`0075E0C0`/`0075E2C0` 与 `00772CD0`/`00772EB0` 两对甚至共用同一条安装指令，两行间唯一可区分信息只剩槽号（即 ② 的槽）。
  - (b) 6 行**全部触及** M69 已披露的已知限制（PANEL L146–149）。
- Lead 裁定：**按现行 D-43(A) 成文口径 + M69 整批裁定，准予并表**，同时在本轮披露里写清「PASS 的依据是口径而非④已独立」。
- 按审计建议 117–120，README 对外**不得**表述为「④ 已独立于 ②」或「§12.3 已解决」。

## 3. Lead 已核前置（改前，不符即停）

| 指标 | 卡片给定 | 盘上实算 | 一致 |
|---|---:|---:|---|
| 数据行数 | 18,498 | 18,498 | ✅ |
| 全表 `[已证]` | 1,615 | 1,615 | ✅ |
| atlas 内 `[已证]` | 1,609 | 1,609 | ✅ |
| atlas 外 `[已证]` | 6 | 6 | ✅ |
| S13 atlas 内 proved | 100 | 100 | ✅ |

- 两文件改前 sha256 与 `MERGE_M73/VERIFY.txt` 记录的改后值一致，确认起点承接 M73。任一不符即停下的条件均未触发。

## 4. coverage.tsv 改动

对 6 行各改 3 列，逐行断言其余 5 列逐字节不变：

- 第 4 列 `one_line_semantics` ← `NAMED_PUSH_S13_B1/delta.tsv` 第 4 列原文照抄（逐字节核对 PASS）。
- 第 5 列 `grade`：`[静态推断]` → `[已证]`。
- 第 6 列 `evidence_path`：原值 → `NAMED_PUSH_AUDIT16/VERDICT.md`（6 行统一）。
- 第 1/2/3/7/8 列不动。数据行仍 18,498、8 列、TAB 分隔；行数不增不减；无 BOM、LF、无尾随换行（逐字节保持）。
- 改动行（文件 1-based 行号）：1488（004684E0）、7438（00629FD0）、11273（0075E0C0）、11274（0075E2C0）、11625（00772CD0）、11626（00772EB0）。

## 5. PANEL.md 同步

- 全表 `[已证]` / atlas 内 `[已证]`：`1,615 / 1,609` → `1,621 / 1,615`；atlas 外仍 6。
- 面板主表 S13 行：proved `100→106`、proved_pct `41.67→44.17`（106/240）；named 各列（216/108）不动。
- 面板主表 TOTAL 行：proved `1609→1615`、proved_pct `12.46→12.50`。
- 严格口径双列表 S13 行：proved `100→106 / 41.67→44.17`，proved_strict `99→105 / 41.25→43.75`（105/240）；门槛 120 与达标旗标不动。
- 严格口径双列表 TOTAL 行：proved `1609→1615 / 12.46→12.50`，proved_strict `1292→1298 / 10.00→10.05`；达标旗标 3/22、1/22 不动。
- 备注列追加（S13/TOTAL 备注首部、全表/atlas 单元格备注、标题行），原文（自卡片逐字提取）：
  `M74 并表 NAMED_PUSH_AUDIT16 PASS 6 行（S13 004684E0/00629FD0/0075E0C0/0075E2C0/00772CD0/00772EB0，evidence_path 改指 NAMED_PUSH_AUDIT16/VERDICT.md；这 6 行曾被 S13-PUSH 否决，本批 ④ 改锚行外构造器写点后过审；PASS 依据为 D-43(A) 口径 + M69 整批裁定，非「④ 已独立」）`
- 标题行首追加 M74 并表摘要（与既有 M73/M72/… 同格式）。
- **第四条披露**：自卡片「必须追加的第四条披露」围栏逐字提取 5 行，**原样写入**（不许改写），接在 M71 披露块最后一行之后；落点第 **160–164** 行（M71 披露为 155–159 行）。披露含 D-43(A) 与 §12.3 正面冲突、`0075E0C0`/`0075E2C0` 与 `00772CD0`/`00772EB0` 两对共用安装指令、Lead 处置（D-43(A) 先行、§12.3 让位）、并列为待裁项 D-47。
- strict 用带方括号字面 `[未证]` 口径（`if "[未证]" not in sem:`）；6 行新语义逐行核 delta 第 4 列均不含字面 `[未证]`，故 strict 随 proved 同增（S13 +6、TOTAL +6）。

## 6. 达标翻转（不得改变）

- 名义达标：3/22 = S15 / S16 / S17（未变）。
- 严格达标：1/22 = S17（未变）。
- S13 门槛：named 216（216/240=90.00% 已过 90% 门槛）、proved 门槛 120（现 106，仍未过）；proved 106/240=44.17% 远低于 50%。本批 +6 proved 不足以使 S13 名义或严格达标。
- **无达标翻转**（算出即停下报告；本次未触发）。

## 7. 复核结果

- `MERGE_M74/verify.py`：OVERALL **ALL PASS（75/75 checks）**（含并行数 6、交集正好 6、6 行三列、6 行全 atlas 内、行数/列数、全表/atlas 内/外已证数、S13 proved/strict、TOTAL、nominal/strict 达标无翻转、PANEL 各串存在性与旧串消失、M74 披露逐字存在且在 M71 之后紧邻）。
- `MERGE_M74/precheck.py`：改前全部前置 PASS。
- `MERGE_M74/apply_coverage.py`：内置前置断言（交集 6、全 PASS、6 行全 S13、6 行全 atlas 内、其余 5 列不动、新语义无 `[未证]`）全部 PASS。
- `MERGE_M74/apply_panel.py`：6 处替换各命中 1 次、M74 披露插入 1 次（逐字比对卡片）。
- 改前/改后 mtime/字节/sha256 见 `MERGE_M74/BEFORE_AFTER.txt`；强制指标汇总见 `MERGE_M74/VERIFY.txt`。
