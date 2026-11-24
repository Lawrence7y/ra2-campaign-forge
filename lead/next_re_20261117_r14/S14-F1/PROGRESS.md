# S14-F1 · PROGRESS

> 卡号 S14-F1｜执行：静态双通道（capstone `skipdata=True` + Ghidra `-noanalysis`）｜写域内交付。
> 分级：本表结论均为 `[已证]`，仅“House::Update 每帧恰 1 次”保持 `[静态推断]`（见 `DISAGREE.md`）。

## 结论表

| # | 结论 | 级 | 证据 |
|---|---|---|---|
| 1 | `HouseClass::Update=0x4F8440`，区间 `[0x4F8440,0x4F9367)`；主链 **11 个主调度子步骤**，Super 充能循环位于第 8 步 `0x4F8E28..0x4F8E84`，调用 `0x6CBCA0 @0x4F8E4A` | 已证 | `FLOW.md §1`；`EVIDENCE/E01_update_window.txt`；`EVIDENCE/G01_ghidra_disasm.txt` |
| 2 | `0x4F8440` = HouseClass vtable `0x7EA8A0` slot 23；`0x55E269 call [eax+0x5C]` 位于 `0x55E160` 函数区间 | 已证 | `EVIDENCE/E07_house_caller_window.txt`；`EVIDENCE/E14_ai_vtable_slots.txt` |
| 3 | AITrigger 评估入口 **`0x6F0AB0`**；唯一活调用点 `0x4F8A6A`；本函数只返回 TeamType 向量，CreateTeam 在调用方 `0x4F8AAD` | 已证 | `EVIDENCE/E01_update_window.txt`；`EVIDENCE/E02_aitrigger_eval.txt`；`G01` |
| 4 | `ConditionMet=0x41E720`；`ConditionType=+0x98`，`Team1=+0xDC`，`Team2=+0xE0`，`Amount=+0xE4`，`Comparator=+0xE8`（跳表 `0x41F2C4`: `<,<=,==,>=,>,!=`） | 已证 | `EVIDENCE/E03_conditionmet.txt`；`EVIDENCE/E11_aitrigger_rulesloader.txt`；`EVIDENCE/E15_condition_helpers.txt` |
| 5 | `TeamTypeClass::CreateTeam=0x6F09C0`；**Team 分配 `0xA0`=160 B**；ctor `0x6E8A90` 写 `+0x24=TeamType*`、`+0x2C=HouseClass*`、`+0x54=FirstUnit`、`+0x28=ScriptClass*` | 已证 | `EVIDENCE/E04_createteam.txt`；`EVIDENCE/E05_team_ctor.txt`；`G01` |
| 6 | `[0x8871E0]` 指向 RulesClass（非多态）；本卡口径 **9 个 AI/作弊相关数值字段**（6 double + 3 int），逐项有 key push + 读取调用 + 写点 | 已证 | `EVIDENCE/E13_rules_ai_key_stores.txt`；`G01`；`FLOW.md §4` |
| 7 | `FootClass::AI=0x4DA530`，`0x4DA877` 在其体内；与 House::Update 是**并列循环**，三个直接调用点 `0x414DA3/0x51BC9F/0x73647B` 均不在 House 函数区间 | 已证 | `EVIDENCE/E06_foot_ai_window.txt`；`EVIDENCE/E14_ai_vtable_slots.txt`；`R14_COMMON §1` |
| 8 | 0x87F7E8 实测身份是 **MapClass**（§951），不是 RulesClass；`[0x8871E0]` 才是 RulesClass 指针（§931） | 已证 | `R14_COMMON §4.3`；`docs/re/...` 仅作线索；`DISAGREE.md` |

## 核心数字与复算

1. **子步骤数 = 11**：数 `FLOW.md §1` 调用点表行数；每行至少一个 `EVIDENCE/E01` 中 `0x4F84..0x4F93` 调用地址，Ghidra `G01` 同址复核。
2. **AITrigger 评估入口 = `0x006F0AB0`**：`grep -i "call.*0x6f0ab0" EVIDENCE/E01_update_window.txt G01_ghidra_disasm.txt`；反查 `0x6F0C58 call 0x41e720`。
3. **Team 分配大小 = `0xA0`（160 B）**：`grep "006F0A4D" EVIDENCE/E04_createteam.txt` 得 `68 a0 00 00 00`；`0x6F0A52 call 0x7c8e17`；`G01` 同址。
4. **AI 数值字段数 = 9**：`python work/t4_rules_ai.py`，在 `EVIDENCE/E13_rules_ai_key_stores.txt` 按 `FLOW.md §4` 的 9 个键取首个 `PUSH → call 0x5276d0/0x5283d0 → [esi+off]` 三元组；Ghidra `G01` 校验 5 个代表键。

## 证据与复跑路径

- 原始反汇编（不截断）：`EVIDENCE/E01..E15_*.txt`、`EVIDENCE/G01_ghidra_disasm.txt`。
- 可复跑：`work/wbase.py`（PE+skipdata+call/imm 扫描）、`work/t1_dump.py`、`work/t2_keys.py`、`work/t3_key_slots.py`、`work/t4_rules_ai.py`、`work/t6_vtables.py`、`work/ExportS14.java`。
- 双通道独立性：A 不读 `function_atlas`；B 由 Ghidra 项目副本 `-noanalysis` 输出，副本已删除。
- 未决/分歧：`UNKNOWNS.md`、`DISAGREE.md`；delta：`coverage_delta.tsv`。
