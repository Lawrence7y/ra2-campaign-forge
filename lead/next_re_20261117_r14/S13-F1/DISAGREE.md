# S13-F1 DISAGREE.md

> 与 `docs/re/` 旧线索文档及卡面候选假设的分歧。权威 = 本卡字节级实测（ImageBase 0x400000，SHA-256 73201CC0…F67476）。
> 台账 `GOAL_THREE_TARGETS_20261018.md` 无与本卡直接冲突的 [已证] 节；R14_COMMON §1 作废索引已查，无命中。

| # | 来源 | 旧表述 | 本卡实测 | 结论 |
|---|---|---|---|---|
| D1 | 卡面候选假设 | `TechnoClass/FootClass Fire +0x154 slot 85 或相近` | slot 85(+0x154)=`0x70E2B0`（TurretControl 计时），真 Fire=**slot 243 (+0x3CC)=0x6FDD50**；.rdata 定界直读 | 卡面猜测**否证**（纪律 11：候选假设须自证/否证） |
| D2 | `docs/re/weapons_damage_production.md:24/135/153` | `Verses[11]` 在 `Warhead+0xB0`（后附勘误已改 +0xA0） | `Verses[0]` 起于 `+0xA0`，`+0xB0`=`Verses[2]`；与 S13-K1 §7 一致，三通道复核 | 采纳勘误后的 +0xA0；本卡独立复核通过 |
| D3 | `docs/re/weapons_damage_production.md:221-232`、`warhead_abi_verses_deform_deep_dive.md:200-206` | 「Verses 不在 ReceiveDamage 体内，只在 DamageArea 前的独立块 0x4891C6」 | `0x4891C6` 不是函数头，真入口是 **`0x489180`**（fn_at 区间包含）；**ReceiveDamage 在 0x701D64 直呼 0x489180** ⇒ Verses 经 helper 进入伤害主路径；0x4891C6 只是 `jge 0x4891c6` 的内部标签 | 更正值：Verses **经 GetTotalDamage(0x489180) 参与 ReceiveDamage 结算**；旧「不在 ReceiveDamage 路径」[实证] 不成立 |
| D4 | `docs/re/weapons_damage_production.md:220`、`warhead_abi_verses_deform_deep_dive.md §3.1` | 「`0x4891C6` 无 E8/E9 直引，属主未定」 | 全镜像扫 `call 0x489180` **3 处**：0x5F540F、0x6FDD29、**0x701D64**（ReceiveDamage）；属主已定 | 属主 = GetTotalDamage 0x489180；「无调用者」表述作废（纪律 7） |
| D5 | `docs/re/weapons_damage_production.md:220` / S24 §勘误2 | `0x70D4A0` 在 ReceiveDamage 内清引用 | 本卡在 ReceiveDamage **全函数体无 `call 0x70D4A0`**（hits=[]）；6 处直呼全在 DamageArea（0x4896BA/0x48A044/0x48A1C8/0x48A265/0x48A2BF/0x48A319） | 「ReceiveDamage 调 0x70D4A0」不成立；清引用在 DamageArea 分摊层 |
| D6 | `docs/re/weapons_damage_production.md:46` | FootClass v[243] Fire = `0x415EE0`（薄包装） | .rdata 直读 FootClass vt 0x7E8C94 slot243 = **`0x6FDD50`（本体）**；0x415EE0 是 AircraftClass slot243；Unit=0x741340、Infantry=0x51DF60 才是包装 | FootClass 直连本体；旧表把 Aircraft 的入口误挂 Foot（RTTI/虚表直读优先） |
| D7 | `docs/re/weapons_damage_production.md:58` | `BulletClass::Construct` 是「17 处直呼之一」 | 本卡扫 ctor 0x466380 仅 1 处（工厂 0x6C50CF），Construct 0x4664C0 直呼 6 处（0x469F7F/0x46A150/0x46A5A1/0x46AA16/0x46B0A6/0x46B408）+Fire 0x6FF859 = 7 处；旧 17 处含间接/其他语义 | 「17 处」不作为本卡结论引用（口径不同，未采信） |

说明：本卡未修改任何共享文档/台账；上述分歧仅登记，供 Lead 决定是否入台账更正节。
