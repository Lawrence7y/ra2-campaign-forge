# S11-K1 · DISAGREE（与旧线索/作废索引的分歧）

| # | 旧说法（出处） | 本卡裁决 | 依据 |
|---|---|---|---|
| 1 | W164「`FindPath 0x42C900 = 1563 指令`」 | **作废，不引用**（真值 327）。本卡未引用该数。 | R14_COMMON §1 |
| 2 | 「`[loco+0x54]==-1` 或 `[loco+0x5F]==0` ⇒ 跳过寻路」 | **不准确**：只跳过 Process 第一段分支，跳过后仍走第二个 `call 0x4B2630`（`0x4B0A79`）。本卡不引用该因果。 | R14_COMMON §1 / 台账 §916-4 |
| 3 | 「FootClass::AI 移动/寻路每 16 帧执行一次」 | **否证**：`frame % [[0x8871E0]+0x1808]` 门（`0x4DA560`）只跳过 `[0x4DA56E,0x4DA63B)`；`0x4DA877`（slot16 Process 派发）在 `0x4DA63B` 之后，**每帧都跑**。 | R14_COMMON §1 / 本卡 `slot_anchors.txt` |
| 4 | `N=[[0x8871E0]+0x1808]=16` 外推为「移动段每 16 帧一次」 | **外推错**：N 的真实身份是 INI `RadApplicationDelay`，只门控那 60 条应答/声音块。 | R14_COMMON §1 / §931 |
| 5 | `pathfinding_locomotion.md` 说 `ILocomotion 段 50 槽`、`Walk v[16]=0x75AC80`、`v[17]=0x75ACB0` | **一致**（本卡实测 vtable off4 = 50 槽、slot16/17 同值）。但该文说「WalkLocomotion vtable=0x7F69F8」需澄清：`0x7F69F8` 是 off4 ILocomotion 子表，另有 off0 主表 `0x7F6AC4`、off24 `0x7F69D4`；类名只认 RTTI TD。 | 本卡 `ch1_rtti_enum.txt` / `slot_anchors.txt` |
| 6 | `pathfinding_locomotion.md` 说「Fly v[17]=0x4CCC80」但 §1.3 表列 `0x004CCB40` 为 Process 且 §1.2 说 Fly Move_To=`0x4CCC80` | **本卡实测**：Fly slot16=0x4CCB40、slot17=0x4CCC80、slot18=0x4CCFD0，与该文 §1.2 一致；§1.3 表把 `0x4CCB40` 同时写在 Move_To 行是笔误。 | 本卡 `slot_anchors.txt` |
| 7 | 台账 §849-4「子表槽数 ≤ 主表槽数」不变量 | **被否证**（台账已作废该不变量）：LocomotionClass 家族 off4 子表 50 槽 > off0 主表 10 槽；本卡实测确认。 | 台账 §849-4 / 本卡 `ch1_rtti_enum.txt` |
| 8 | 「CLSID 表是 `.rdata` 中 16B GUID 与类工厂指针并列的静态数组」 | **本卡修正**：GUID 确实连续在 `.rdata`（11×16B），但「GUID→工厂」映射不在数据段并列，而在注册函数 `0x6BB9A0` 的代码序列里（每类 `new` 工厂 + `CoRegisterClassObject`）。 | 本卡 `clsid_scan.txt` / `disasm_6BD130.txt` |
