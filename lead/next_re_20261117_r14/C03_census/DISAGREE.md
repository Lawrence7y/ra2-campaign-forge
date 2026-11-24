# C03 · DISAGREE（与台账/他源的分歧与判断记录）

> 卡号 C03｜片：逻辑行 2585–3876（1292 函数）

## 1. 类→子系统映射的歧义判断（均标 [静态推断]/[未证]，非 [已证]）

| 类族 | 本卡归属 | 依据 | 歧义 / 他解 |
|---|---|---|---|
| FootClass / UnitClass / InfantryClass / AircraftClass / MissionClass | **S10** | PLAN §1 S10 明列「Foot/Unit/Infantry/Aircraft::AI」；C02 已把派生类 Unit/Infantry/Aircraft 归 S10，保持一致 | PLAN §1 S05 也含「Foot 族布局与虚表」；若按对象模型应归 S05。本卡按「方法实现 = 行为/AI」主导，取 S10。语义未证 |
| DiskLaserClass / EBolt / EMPulseClass | **S20** | PLAN §1 S20 明列「粒子/Anim/特效」；三者为武器生成的持续视觉效果对象 | 也含 `Fire`/`SetOwner`，可争 S13 战斗。取 S20（特效本体），语义未证 |
| DrivePod/Fly/Rocket/Tunnel/Hover/Mech/Teleport/Jumpjet/Walk/Ship/DropPodLocomotionClass | **S11** | PLAN §1 S11 明列「Drive/Walk/Fly/Jumpjet/Ship/Teleport…」，逐字对应 | 无实质分歧 |
| FactoryClass | **S12** | PLAN §1 S12 含「生产/工厂」；YRpp 名 `FactoryClass::DemandProduction/AbandonProduction` 佐证 | 无 |
| MovieHandle | **S19** | PLAN §1 S19 含「VQA 视频」 | 无 |
| RTacticalClass_RadarClass / RadarClass | **S08** | PLAN §1 S08 含「雷达小地图」 | 无 |

> 上述归属只影响「归类到哪个子系统」，不影响证据分级；所有一行语义仍为 `[未证]` 猜测。

## 2. 与台账的具体冲突点

- **0x004C9150**：本卡因 re_atlas/kb 地址名给 `[已证]` 名 `AbstractClass`（归 S05）。
  但台账 `GOAL_THREE_TARGETS_20261018.md` §20008/§20078 记录该地址是共享「空实现」桩 `xor eax,eax; ret`（被引 197 次）。
  ⇒ 该 [已证] 名来自 kb 的批量地址名抓取，实际语义是空桩而非 AbstractClass 方法。
  本卡不改 kb、不改台账，仅在此登记；建议 P1 主攻 S05 时修订（本卡 grade 仍按来源标 [已证]，语义标 [未证]）。
- **0x004E1340**：atlas 空洞 high(call) 目标，boundary=True 但函数序言识别为 `(no-prologue-in-4)`。
  可能是极短 thunk 或热补丁块内的 call 目标，未据此断言「是完整函数」；仅按 C02 口径（call 目标 + owner=None + 非指令内部）计入空洞数。

## 3. 未发现的分歧

- 除上述 0x4C9150 外，本片 64 个 YRpp/kb 显式地址名的归属与台账/re_atlas kb 无冲突。
- 未把任何猜测写成 [已证]；未写游戏文件、台账、共享覆盖表；未 git commit/push。
