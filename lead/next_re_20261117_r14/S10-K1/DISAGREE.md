# S10-K1 · DISAGREE

| # | 议题 | 本卡结论 | 他源说法 / 分歧点 | 处理 |
|---:|---|---|---|---|
| D1 | Mission 派发形态 | **两级混合**：mission 号跳表（`0x5B34E8`,32项）→ stub → 虚槽 v[129..156]（`call [vptr+0x204..0x270]`） | 任务书设为二选一"跳表 vs 每 Mission 一个虚函数槽"；两者都只说对一半 | 明确写为混合：`LAYOUT §3`。表 `0x5B34E8` 与 v 槽范围均有逐指令证据。 |
| D2 | Mission 号 → 实现 | Harvester 的 Harvest(10) 实现 `0x522E70` 出现在所标 `InfantryClass` vtable `0x7EB058` 的 v[137] | 语义上 Harvest 属 UnitClass（Tiberian Harvester 是 Unit）。若 `0x7EB058` 的 RTTI 名被误标为 Infantry，则实现归属要改 | 已按 RTTI TD 验 `0x7EB058`→COL `0x8033B8`→TD `0x825508`（`rtti_verify.txt`），但 TD name 未逐字符读出（TD 在 0x825508，超出本卡 name-read 范围检查）。标 `[静态推断]`，见 U4。 |
| D3 | "每 Mission 一个虚函数槽" | 28 个连续 v 槽 v[129..156] 对应 28 种 handler，**但** 32 个 Mission 号中有 4 个复用（3/29→v129，6→v135 同 5，17→v133 同 8） | 若按"每 Mission 独立槽"应有 32 个不同槽 | 实际 28 槽、32 表项；`mission_dispatch_map.txt` 逐项列明。 |
| D4 | Mission 派发与 FootClass::AI 的每帧性 | 派发在 `FootClass::AI → TechnoClass::AI → MissionClass::AI` 调用链首段，每帧 | `R14_COMMON §1` 作废索引曾纠正"frame%16 跳过移动段"的误读；本卡不复用该错误叙事 | 明确派发 call `0x6FA655` 位于 `frame%N` 门控区（`0x4DA56E..0x4DA63B`）之外；依纪律 10 不引 EIP 权重。 |
| D5 | 类名归属 S10 vs S05 | C03/C06 Census 把多数 MissionClass/RadioClass 虚表函数按"多类 most_common"归 S20/S06/S05/S18，S10 仅 2 | 本卡把 Mission 调度结构整体归 S10（按 PLAN §1 "Mission 系统/单位行为 AI"） | 仅登记，不改共享台账；由 Lead/合并员裁决。证据 `lead\GOAL_THREE_TARGETS_20261018.md:27281`,`C06_census\UNKNOWNS.md:20`。 |

## 无冲突项

- `docs\re\R3_ai_hooks.md`（线索）给的是 House/Team招募三兄弟与 `TeamClass::AI` 跳表 `0x6E945B/@0x6E9F74`（Action 派发），与本卡 Mission 号派发 `0x5B30C1/@0x5B34E8` 是**两套不同跳表**，未混用。
- R14_COMMON §1 作废索引中无 Mission 相关条目；本卡结论未被其任何作废节覆盖。
