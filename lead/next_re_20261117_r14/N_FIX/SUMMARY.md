# SUMMARY.md — N-FIX noinit_t 误剔专项结论

目标 `ra2youli\gamemd.exe` SHA-256 `73201CC0…F67476`｜ImageBase 0x400000｜只读。
判据（经 §952 基线收窄，见 `BASELINE.md`）：上一行确为 `: Xxx(noinit_t())` 委托初始化行 **且** 下一行有 `JMP_THIS(0x…)`。
分级仅用 [已证] / [静态推断] / [未证]。

## 核心数字（给审计）

| 项 | 数 | 限定语 |
|---|---:|---|
| `noinit_t` 总行数（全镜像 238 文件） | **300** | 所有含 `noinit_t` 的源码行 |
| 收窄判据命中（真误剔候选） | **99 实例 / 95 唯一地址** | 有 `JMP_THIS` 紧随；C08=9 / C09=15 已知集全部在命中集内 |
| 真误剔数（= 有 JMP_THIS 跟随） | **99** | 其中 74 唯一地址落入十片 coverage_delta，15 为 C01 已正确具名、6 不在任何卡 |
| 纯空桩数（无地址，不提升） | **106** | `explicit __forceinline Xxx(noinit_t)` 空内联桩；完整清单见下 |
| 本轮新增 high 增量 | **+34** | C04 +7 / C05 +6 / C06 +8 / C07 +13（C08 +9、C09 +15 已入账，不重复） |
| 十片 high 修正合计 | **4,789** | 以 lead 入账值和 4,755 为基线 +34；见下节对账 |

## 十片 high 对账与 P0-CLOSE 4,752 差异

- lead 给的入账值求和：96+840+428+776+565+382+559+417+438+254 = **4,755**。
- P0-CLOSE `_audit\VERDICT.md` 的 4,752 = 102+840+428+776+565+382+559+**408**+438+254。
- **停机核验（§954）**：4,755 − 4,752 = **+3**，逐项定位为 C01 96 vs 102（−6，C01「计数 102／可信 96」口径差）+ C08 417 vs 408（+9，§960 已修正）= −6+9 = +3。**非本卡凑数**，两处均为既有账的不同取值口径。
- 本卡修正后合计 = 4,755（lead 入账基线）+ 34（本轮新增）= **4,789**。
- 对 P0-CLOSE 4,752 的净差 = 4,789 − 4,752 = **+37** = C08 +9 − C01 6 + 本轮 +34。
- 若改用 P0-CLOSE 基线（C01=102、C08=408、已含 C09 +15、未含 C08 +9）：4,752 + 9（C08 §960）+ 34（本轮）= **4,795**；此数仅作口径对照，正式入账以 lead 给的逐片值（4,789）为准。

## 本轮新增修正（需上调的卡）

| 卡 | 现入账 high | 需上调 | 修正后 | 依据 |
|---|---:|---:|---:|---|
| C04 | 776 | +7 | 783 | 7 唯一地址 `sub_` [未证]/conf=low，YRpp JMP_THIS 具名构造器 |
| C05 | 565 | +6 | 571 | 6 地址 `sub_`（3 low [未证] + 3 med [静态推断]） |
| C06 | 382（严格 274） | +8 | 390（严格 282） | 8 地址 `sub_` [未证]/conf=low；另 0x5D8170 已 high 不计 |
| C07 | 559（严格 359） | +13 | 572（严格 372） | 13 地址 `sub_` [未证]/conf=low |
| **合计** | | **+34** | | |

**不需上调**：C01（15 地址已具名 high）、C02（9 个 `::noinit_t` 名字已 high，仅错名）、C03（6 个同）、C08（§960 已 +9）、C09（§942 已 +15）、C10（0 命中）。

## 纯空桩清单（106，不应提升）

判据：YRpp 源码行形如 `explicit __forceinline Xxx(noinit_t)`，后面 3 行内**无** JMP_THIS（多为 `: Base(noinit_t())` + `{ }`），即空内联桩、无机器码地址。
以下 106 个按 §954「不在 X 内 ≠ 是 Y」明确排除，**不进 NOINIT_CENSUS.tsv 的真误剔，也不提升 high**。逐条：

| # | YRpp 行 | 类名 | 源码 |
|---:|---|---|---|
| 1 | `AITriggerTypeClass.h:155` | AITriggerTypeClass | `explicit __forceinline AITriggerTypeClass(noinit_t) noexcept` |
| 2 | `AbstractClass.h:153` | AbstractClass | `explicit __forceinline AbstractClass(noinit_t) noexcept` |
| 3 | `AbstractTypeClass.h:67` | AbstractTypeClass | `explicit __forceinline AbstractTypeClass(noinit_t) noexcept` |
| 4 | `AircraftClass.h:58` | AircraftClass | `explicit __forceinline AircraftClass(noinit_t) noexcept` |
| 5 | `AircraftTypeClass.h:35` | AircraftTypeClass | `explicit __forceinline AircraftTypeClass(noinit_t) noexcept` |
| 6 | `AirstrikeClass.h:40` | AirstrikeClass | `explicit __forceinline AirstrikeClass(noinit_t) noexcept` |
| 7 | `AlphaShapeClass.h:40` | AlphaShapeClass | `explicit __forceinline AlphaShapeClass(noinit_t) noexcept` |
| 8 | `AnimClass.h:66` | AnimClass | `explicit __forceinline AnimClass(noinit_t) noexcept` |
| 9 | `AnimTypeClass.h:46` | AnimTypeClass | `explicit __forceinline AnimTypeClass(noinit_t) noexcept` |
| 10 | `BombClass.h:53` | BombClass | `explicit __forceinline BombClass(noinit_t) noexcept` |
| 11 | `BuildingClass.h:201` | BuildingClass | `explicit __forceinline BuildingClass(noinit_t) noexcept` |
| 12 | `BuildingLightClass.h:37` | BuildingLightClass | `explicit __forceinline BuildingLightClass(noinit_t) noexcept` |
| 13 | `BuildingTypeClass.h:94` | BuildingTypeClass | `explicit __forceinline BuildingTypeClass(noinit_t) noexcept` |
| 14 | `BulletClass.h:118` | BulletClass | `explicit __forceinline BulletClass(noinit_t) noexcept` |
| 15 | `BulletTypeClass.h:65` | BulletTypeClass | `explicit __forceinline BulletTypeClass(noinit_t) noexcept` |
| 16 | `CCFileClass.h:61` | FileClass | `explicit __forceinline FileClass(noinit_t)` |
| 17 | `CCFileClass.h:103` | RawFileClass | `explicit __forceinline RawFileClass(noinit_t)` |
| 18 | `CCFileClass.h:138` | BufferIOFileClass | `explicit __forceinline BufferIOFileClass(noinit_t)` |
| 19 | `CCFileClass.h:179` | CDFileClass | `explicit __forceinline CDFileClass(noinit_t)` |
| 20 | `CCFileClass.h:206` | CCFileClass | `explicit __forceinline CCFileClass(noinit_t)` |
| 21 | `CampaignClass.h:16` | CampaignClass | `explicit __forceinline CampaignClass(noinit_t) noexcept` |
| 22 | `CaptureManagerClass.h:77` | CaptureManagerClass | `explicit __forceinline CaptureManagerClass(noinit_t) noexcept` |
| 23 | `CellClass.h:327` | CellClass | `explicit __forceinline CellClass(noinit_t) noexcept` |
| 24 | `ConvertClass.h:50` | ConvertClass | `explicit __forceinline ConvertClass(noinit_t)` |
| 25 | `ConvertClass.h:102` | LightConvertClass | `explicit __forceinline LightConvertClass(noinit_t)` |
| 26 | `DiskLaserClass.h:48` | DiskLaserClass | `explicit __forceinline DiskLaserClass(noinit_t) noexcept` |
| 27 | `EMPulseClass.h:37` | EMPulseClass | `explicit __forceinline EMPulseClass(noinit_t) noexcept` |
| 28 | `FactoryClass.h:108` | FactoryClass | `explicit __forceinline FactoryClass(noinit_t) noexcept` |
| 29 | `FlyLocomotionClass.h:47` | FlyLocomotionClass | `explicit __forceinline FlyLocomotionClass(noinit_t)` |
| 30 | `FootClass.h:136` | FootClass | `explicit __forceinline FootClass(noinit_t) noexcept` |
| 31 | `GenericList.h:19` | GenericNode | `explicit __forceinline GenericNode(noinit_t)` |
| 32 | `GenericList.h:42` | Node | `explicit __forceinline Node(noinit_t)` |
| 33 | `GenericList.h:59` | GenericList | `explicit __forceinline GenericList(noinit_t)` |
| 34 | `GenericList.h:82` | List | `explicit __forceinline List(noinit_t)` |
| 35 | `Helpers/CompileTime.h:12` | constant_ptr | `constexpr constant_ptr(noinit_t) noexcept {}` |
| 36 | `Helpers/CompileTime.h:47` | reference | `constexpr reference(noinit_t) noexcept {}` |
| 37 | `Helpers/CompileTime.h:102` | reference | `constexpr reference(noinit_t) noexcept {}` |
| 38 | `HouseClass.h:666` | HouseClass | `explicit __forceinline HouseClass(noinit_t) noexcept` |
| 39 | `HouseTypeClass.h:54` | HouseTypeClass | `explicit __forceinline HouseTypeClass(noinit_t) noexcept` |
| 40 | `InfantryClass.h:38` | InfantryClass | `explicit __forceinline InfantryClass(noinit_t) noexcept` |
| 41 | `InfantryTypeClass.h:67` | InfantryTypeClass | `explicit __forceinline InfantryTypeClass(noinit_t) noexcept` |
| 42 | `IsometricTileClass.h:41` | IsometricTileClass | `explicit __forceinline IsometricTileClass(noinit_t) noexcept` |
| 43 | `IsometricTileTypeClass.h:47` | IsometricTileTypeClass | `explicit __forceinline IsometricTileTypeClass(noinit_t) noexcept` |
| 44 | `LightSourceClass.h:45` | LightSourceClass | `explicit __forceinline LightSourceClass(noinit_t) noexcept` |
| 45 | `LocomotionClass.h:286` | LocomotionClass | `explicit __forceinline LocomotionClass(noinit_t)` |
| 46 | `MPGameModeClass.h:231` | MPGameModeClass | `explicit __forceinline MPGameModeClass(noinit_t)` |
| 47 | `MPGameModeClass.h:276` | MPBattleClass | `explicit __forceinline MPBattleClass(noinit_t)` |
| 48 | `MPGameModeClass.h:300` | MPManBattleClass | `explicit __forceinline MPManBattleClass(noinit_t)` |
| 49 | `MPGameModeClass.h:339` | MPFreeForAllClass | `explicit __forceinline MPFreeForAllClass(noinit_t)` |
| 50 | `MPGameModeClass.h:361` | MPMegawealthClass | `explicit __forceinline MPMegawealthClass(noinit_t)` |
| 51 | `MPGameModeClass.h:396` | MPUnholyAllianceClass | `explicit __forceinline MPUnholyAllianceClass(noinit_t)` |
| 52 | `MPGameModeClass.h:444` | MPSiegeClass | `explicit __forceinline MPSiegeClass(noinit_t)` |
| 53 | `MPTeams.h:21` | MPTeam | `MPTeam(noinit_t)` |
| 54 | `MissionClass.h:101` | MissionClass | `explicit __forceinline MissionClass(noinit_t) noexcept` |
| 55 | `NeuronClass.h:35` | NeuronClass | `explicit __forceinline NeuronClass(noinit_t) noexcept` |
| 56 | `ObjectClass.h:254` | ObjectClass | `explicit __forceinline ObjectClass(noinit_t)  noexcept` |
| 57 | `ObjectTypeClass.h:55` | ObjectTypeClass | `explicit __forceinline ObjectTypeClass(noinit_t) noexcept` |
| 58 | `OverlayClass.h:67` | OverlayClass | `explicit __forceinline OverlayClass(noinit_t) noexcept` |
| 59 | `OverlayTypeClass.h:49` | OverlayTypeClass | `explicit __forceinline OverlayTypeClass(noinit_t) noexcept` |
| 60 | `ParasiteClass.h:54` | ParasiteClass | `explicit __forceinline ParasiteClass(noinit_t) noexcept` |
| 61 | `ParticleClass.h:46` | ParticleClass | `explicit __forceinline ParticleClass(noinit_t) noexcept` |
| 62 | `ParticleSystemClass.h:44` | ParticleSystemClass | `explicit __forceinline ParticleSystemClass(noinit_t) noexcept` |
| 63 | `ParticleSystemTypeClass.h:43` | ParticleSystemTypeClass | `explicit __forceinline ParticleSystemTypeClass(noinit_t) noexcept` |
| 64 | `ParticleTypeClass.h:44` | ParticleTypeClass | `explicit __forceinline ParticleTypeClass(noinit_t) noexcept` |
| 65 | `RadSiteClass.h:106` | RadSiteClass | `explicit __forceinline RadSiteClass(noinit_t) noexcept` |
| 66 | `RadioClass.h:65` | RadioClass | `explicit __forceinline RadioClass(noinit_t) noexcept` |
| 67 | `RocketLocomotionClass.h:47` | RocketLocomotionClass | `explicit __forceinline RocketLocomotionClass(noinit_t)` |
| 68 | `RulesClass.h:77` | RocketStruct | `explicit RocketStruct(noinit_t) noexcept` |
| 69 | `ScriptClass.h:55` | ScriptClass | `explicit __forceinline ScriptClass(noinit_t) noexcept` |
| 70 | `ScriptTypeClass.h:50` | ScriptTypeClass | `explicit __forceinline ScriptTypeClass(noinit_t) noexcept` |
| 71 | `SideClass.h:37` | SideClass | `explicit __forceinline SideClass(noinit_t) noexcept` |
| 72 | `SlaveManagerClass.h:98` | SlaveManagerClass | `explicit __forceinline SlaveManagerClass(noinit_t) noexcept` |
| 73 | `SmudgeClass.h:38` | SmudgeClass | `explicit __forceinline SmudgeClass(noinit_t) noexcept` |
| 74 | `SmudgeTypeClass.h:44` | SmudgeTypeClass | `explicit __forceinline SmudgeTypeClass(noinit_t) noexcept` |
| 75 | `SpawnManagerClass.h:87` | SpawnManagerClass | `explicit __forceinline SpawnManagerClass(noinit_t) noexcept` |
| 76 | `SuperClass.h:106` | SuperClass | `explicit __forceinline SuperClass(noinit_t) noexcept` |
| 77 | `SuperWeaponTypeClass.h:50` | SuperWeaponTypeClass | `explicit __forceinline SuperWeaponTypeClass(noinit_t) noexcept` |
| 78 | `Surface.h:40` | Surface | `explicit __forceinline Surface(noinit_t) noexcept` |
| 79 | `Surface.h:289` | XSurface | `explicit __forceinline XSurface(noinit_t) noexcept` |
| 80 | `Surface.h:424` | BSurface | `explicit __forceinline BSurface(noinit_t) noexcept` |
| 81 | `Surface.h:470` | DSurface | `explicit __forceinline DSurface(noinit_t) noexcept : XSurface(noinit_t())` |
| 82 | `SwizzleManagerClass.h:57` | SwizzleManagerClass | `explicit __forceinline SwizzleManagerClass(noinit_t)` |
| 83 | `TActionClass.h:276` | TActionClass | `explicit __forceinline TActionClass(noinit_t) noexcept` |
| 84 | `TEventClass.h:69` | TEventClass | `explicit __forceinline TEventClass(noinit_t) noexcept` |
| 85 | `TagClass.h:111` | TagClass | `explicit __forceinline TagClass(noinit_t) noexcept` |
| 86 | `TagTypeClass.h:86` | TagTypeClass | `explicit __forceinline TagTypeClass(noinit_t) noexcept` |
| 87 | `TaskForceClass.h:46` | TaskForceClass | `explicit __forceinline TaskForceClass(noinit_t) noexcept` |
| 88 | `TeamClass.h:47` | TeamClass | `explicit __forceinline TeamClass(noinit_t) noexcept` |
| 89 | `TeamTypeClass.h:81` | TeamTypeClass | `explicit __forceinline TeamTypeClass(noinit_t) noexcept` |
| 90 | `TechnoClass.h:469` | TechnoClass | `explicit __forceinline TechnoClass(noinit_t) noexcept` |
| 91 | `TechnoTypeClass.h:170` | TechnoTypeClass | `explicit __forceinline TechnoTypeClass(noinit_t) noexcept` |
| 92 | `TeleportLocomotionClass.h:56` | TeleportLocomotionClass | `explicit __forceinline TeleportLocomotionClass(noinit_t)` |
| 93 | `TemporalClass.h:55` | TemporalClass | `explicit __forceinline TemporalClass(noinit_t) noexcept` |
| 94 | `TerrainClass.h:39` | TerrainClass | `explicit __forceinline TerrainClass(noinit_t) noexcept` |
| 95 | `TerrainTypeClass.h:41` | TerrainTypeClass | `explicit __forceinline TerrainTypeClass(noinit_t) noexcept` |
| 96 | `TiberiumClass.h:59` | TiberiumClass | `explicit __forceinline TiberiumClass(noinit_t)` |
| 97 | `TriggerClass.h:110` | TriggerClass | `explicit __forceinline TriggerClass(noinit_t)` |
| 98 | `TriggerTypeClass.h:92` | TriggerTypeClass | `explicit __forceinline TriggerTypeClass(noinit_t)` |
| 99 | `UnitClass.h:54` | UnitClass | `explicit __forceinline UnitClass(noinit_t) noexcept` |
| 100 | `UnitTypeClass.h:43` | UnitTypeClass | `explicit __forceinline UnitTypeClass(noinit_t) noexcept` |
| 101 | `VoxelAnimClass.h:46` | VoxelAnimClass | `explicit __forceinline VoxelAnimClass(noinit_t)` |
| 102 | `VoxelAnimTypeClass.h:44` | VoxelAnimTypeClass | `explicit __forceinline VoxelAnimTypeClass(noinit_t)` |
| 103 | `WarheadTypeClass.h:52` | WarheadTypeClass | `explicit __forceinline WarheadTypeClass(noinit_t)` |
| 104 | `WaveClass.h:47` | WaveClass | `explicit __forceinline WaveClass(noinit_t)` |
| 105 | `WaypointPathClass.h:52` | WaypointPathClass | `explicit __forceinline WaypointPathClass(noinit_t)` |
| 106 | `WeaponTypeClass.h:48` | WeaponTypeClass | `explicit __forceinline WeaponTypeClass(noinit_t)` |

## 反向核查（防过度纠正）

- 300 个 `noinit_t` 行中：99 个下一行有 JMP_THIS（真构造器）；106 个是空桩定义；余 95 个是空桩体内的 `: Base(noinit_t())` 委托行。
- 只有「上一行 `: Xxx(noinit_t())` + 下一行 JMP_THIS」的双条件命中才入真误剔；空桩 106 个零提升。
- 4 个地址重复（同码折叠）：0x40E320（GenericNode/Node）、0x52ACE0（GenericList/List）、0x5447C0（IsometricTileTypeClass/TagTypeClass）、0x71E6A0（TActionClass/TEventClass）；high 增量按唯一地址计，实例在 TSV 中逐条列。
- 6 个真构造器地址不在任何卡 coverage_delta：0x5C5CE0/0x5C6150/0x5C93E0/0x5CA630/0x5CB3A0（MPGameModeClass 五个派生类）、0x6CF180（SwizzleManagerClass）—— 不属十片，不产生 high 增量，仅登记。

## 证据与复跑

- `NOINIT_CENSUS.tsv`：99 行 addr/card/current/grade/should/should-grade/evidence_yrpp_line。
- `EVIDENCE\census_detailed.json`：99 实例 + 106 空桩 + 816 JMP_THIS 基线分桶（未截断）。
- `EVIDENCE\scan_noinit_raw.txt`：300 个 noinit_t 行逐行上下文（未截断）。
- `EVIDENCE\percard_correlation.json`、`EVIDENCE\card_detail_block.txt`：逐片关联与明细。
- `work\*.py`：全部可复跑脚本。`capstone skipdata=True` 为本任务族基线约束；本卡判据为 YRpp 文本扫描，未自行反汇编，站点归属沿用各卡 coverage_delta 的 atlas 区间（函数区间包含），未用 entry_at_or_before。
