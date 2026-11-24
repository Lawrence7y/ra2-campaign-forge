# S14-F1 · DISAGREE

| # | 对象 | 说法 | 本卡裁决 | 依据 |
|---|---|---|---|---|
| 1 | 任务书交叉线索 | “RulesClass 单例 = `0x87F7E8`（§951）” | **不成立/引用错节**。§951 说的是 `MapClass` 单例 `0x87F7E8`；`[0x8871E0]` 才是 RuleClass 指针（§931，非多态）。本卡全部 RulesClass 字段写为 `[0x8871E0]` 指向对象，未把两者混用。 | `R14_COMMON §4.3`；台账 §931/§951；`E01` 同时出现 `mov ecx,0x87F7E8`（取格）与 `mov ecx,[0x8871E0]`（读规则）。 |
| 2 | `docs/re/house_team_ai_update.md` §1/§3 | `0x6F0AB0` “触发后逐个 `TeamTypeClass::CreateTeam`”画在该函数内部 | **需收窄**：`0x6F0AB0` 只评估并把 TeamType* 压入结果向量（`0x6F0D5B/0x6F0DA9`）；真正 `call 0x6F09C0` 在调用方 `HouseClass::Update @0x4F8AAD`。 | `EVIDENCE/E02_aitrigger_eval.txt` 全函数无 `E8 ... 6F09C0`；`EVIDENCE/E01_update_window.txt:480`。 |
| 3 | `docs/re/house_team_ai_update.md` §2.4 / `ARCHITECTURE_ATLAS` | `+0xB8/+0x104/+0x108` 命名不一致 | 本卡只采用经审计纠偏的语义：`+0xB8`=double 权重当前值；`+0x104`/`+0x108` 为两个执行计数，具体成功/总次数命名沿用台账 §946 纠正，不据此扩写。 | `E03`；`docs/re/trigger_tag_abi_deep_dive.md` 仅作线索；台账 §946。 |
| 4 | `docs/re/house_team_ai_update.md` §2.1 | `AITriggerTypeClass::Array` Count 记 `0xA8B210` | **一致**；但 TeamType 数组 Count 是 `0xA8ECB0`，不是 `0xA8ECA8`（后者 Capacity）。本卡未沿用旧表的 TeamType Count。 | `E02:0x6F0C29/6F0CBC`；`house_team_ai_update.md` 自带 task-11 勘误。 |
| 5 | S16-K1 交叉线索 | `0x4F8440` “每帧一次” | **降级**：每 Super 恰 1 次 `[已证]`；House::Update 每帧恰 1 次仍 `[静态推断]`，与 S16-K1 审计一致。 | 台账 §945/S16-K1 审计；`EVIDENCE/E07_house_caller_window.txt`。 |
| 6 | 任务书措辞 | “AI 倍率字段（如建造速度、资金作弊）” | 本卡计数 9 是 6 double + 3 int 的**数值调参口径**；若审计要求“纯浮点倍率”应为 6。未把 `IgnoreGlobalAITriggers`（写点 `Scenario+0x34B4`）误算进 RulesClass。 | `FLOW.md §4`；`EVIDENCE/E13_rules_ai_key_stores.txt`；RulesClass ctor size `0x18C0`（W175）。 |
