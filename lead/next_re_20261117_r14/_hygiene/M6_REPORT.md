# M6 补完报告（M6B · 2026-11-18）
## 1. 核验结论
- **通过**：18,431→18,431 行，entry 集合/顺序一致，subsystem、conflict 0 变化。
- grade 变化 **62 行**，全部可溯源到 7 份入场 delta 实载 62 行（entry+old/new grade+payload 一致），**无越权、无不可溯源条目**。
- name 55 行、semantics 62 行、evidence/n_sources 各 62 行变化均在同 62 entry 内；name/evidence 与 payload 逐字一致，19 行 S10_K3 语义为 delta 证据忠实浓缩。
- 派卡 70 行 vs 实载 62 行差额来自 S01-K2 卡面报 8 行但 delta 自述 0，P0_GATE_C 无 delta；快照 diff 穷尽，无漏合。
## 2. grade before/after（第 5 列）
| 项 | before | after | delta |
|---|---:|---:|---:|
| 数据行 | 18,431 | 18,431 | 0 |
| `[已证]` | 1,278 | 1,339 | +61 |
| `[静态推断]` | 6,091 | 6,041 | −50 |
| `[未证]` | 11,062 | 11,051 | −11 |
分卡：S15_K4 2 / S10_K3 23 / S13_K4 13 / S06_K4 23 / S06_K5 1；S01-K2、P0_GATE_C 0。逐行见 `COVERAGE/_m6_upgrade_log.json`（未改）。
## 3. CONFLICTS
- 新增 **0 行**（325→325；conflict=1 仍 181）。4 个重叠 entry（0046C790/0075CEC0/0075E3B0/00771C70）已在册且标 conflict=1；delta 与保留值同 subsystem/name，只与卡方旧 sub_/S22 异，属既有冲突，只登记不裁决、保留旧值。
## 4. PANEL 逐子系统 DoD（一句/subsystem）
- S01：named(S) 8/53、proved 6/53，未达标。
- S02：named(S) 30/327、proved 31/327，未达标。
- S03：named(S) 12/194、proved 18/194，未达标。
- S04：named(S) 88/316、proved 92/316，未达标。
- S05：named(S) 153/643、proved 170/643，未达标。
- S06：K4+K5 已并入、proved 127/848=14.98%，named(S) 117/848，未达标。
- S07：named(S) 64/804、proved 68/804，未达标。
- S08：仅 22 行、named(S) 0、proved 1，未达标。
- S09：named(S) 80/1051、proved 69/1051，未达标。
- S10：K3 23 行已并入、K4 19 行语义更正未并入；proved 111/526，未达标。
- S11：L=358/368；DoD-S 32/368（COMMON-R4F）｜34/368（审计）分歧未裁；proved 29/368，未达标。
- S12：named(S) 53/279、proved 57/279，未达标。
- S13：240 口径 74/240=30.83%｜148 口径 74/148=50.00%，D-37 待裁不宣布达标；atlas proved 60/240。
- S14：named(S) 133/489、proved 107/489，未达标。
- S15：141/158=89.24%，差 2，未达标；atlas proved 96/158。
- S16：named(S) 46/90、proved 46/90，未达标。
- S17：卡级 92/102=90.20%、proved 54/102，达标 + 零余量警告；atlas proved 53/102 差异待裁。
- S18：named(S) 56/659、proved 53/659，未达标。
- S19：named(S) 20/357、proved 21/357，未达标。
- S20：named(S) 41/410、proved 40/410，未达标。
- S21：named(S) 25/129、proved 26/129，未达标。
- S22：不得参与百分比排名或覆盖率结论。
## 5. 待裁决
- **D-37**：S13 named 依 240（74/240=30.83%，未达标）vs 148（74/148=50.00%，压线）；裁决前按 240，不得宣布达标。
- **D-35**：②-a 补丁落地与否；裁决前按 A 不打，PENDING 151 条不新增落地。另：S11 32 vs 34、S10_K4 19 行语义、S17 proved 54 vs 53 均未裁/未并入。
## 6. 写域
- 只写 `COVERAGE/PANEL.md` 与本报告；`coverage.tsv` / `CONFLICTS.tsv` 核验后保持原状（M6_before 快照可对照）。
