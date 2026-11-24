# IMPACT_BY_CARD.md — 逐片 noinit_t 误剔影响

目标 `ra2youli\gamemd.exe` SHA-256 `73201CC0…F67476`｜判据见 `BASELINE.md`（已收窄：上一行确为 `: Xxx(noinit_t())` **且** 下一行有 `JMP_THIS(0x…)`）。
分级仅用 [已证] / [静态推断] / [未证]。high 口径 = self_known([已证]) + vtable-core，与 cards 的 `classification_trace.tsv` / `_audit\VERDICT.md` 一致。

## 汇总（本轮新增 vs 已入账修正）

| 卡 | 入账 high | 误剔地址数 | 本轮 high 增量 | 修正后 high | 修正归属 |
|---|---|---:|---:|---|---|
| C01 | 96 | 0 | 0 | 96 | 无需修正 |
| C02 | 840 | 9 | 0 | 840 | 无需修正 |
| C03 | 428 | 6 | 0 | 428 | 无需修正 |
| C04 | 776 | 7 | +7 | 783 | 本轮新增 |
| C05 | 565 | 6 | +6 | 571 | 本轮新增 |
| C06 | 382（严格 274） | 8 | +8 | 390（严格 282） | 本轮新增 |
| C07 | 559（严格 359） | 13 | +13 | 572（严格 372） | 本轮新增 |
| C08 | 417（严格 416） | 9 | 0 | 417（严格 416） | 已入账（§960） |
| C09 | 438 | 15 | 0 | 438 | 已入账（§942） |
| C10 | 254 | 0 | 0 | 254 | 无需修正 |

**本轮新增 high 增量合计 = +34**（C04 +7 / C05 +6 / C06 +8 / C07 +13）。C08 +9、C09 +15 已在 417/438 中，**不重复计入**。
C02/C03 的 15 个 `::noinit_t` 名字本身错，但已 high，故 high 增量 0 —— 属命名问题，不是误剔降级。

**停机核验**：本卡按 lead 给的入账值求和 = 96+840+428+776+565+382+559+417+438+254 = **4755**，与 P0-CLOSE 的 **4752** 差 +3；已定位为 C01(96 vs 102 = −6) 与 C08(417 vs 408 = +9) 两处口径差，非本卡凑数（详见 `SUMMARY.md`）。

## 逐片明细（addr / 现名 / 应为）
> 每片列出该片 atlas 区间内、收窄判据命中的全部实例。重复地址（同码折叠）逐条列出，high 增量按唯一地址计。

### C01 — 误剔 0 / 本轮增量 0 / 修正后 high 96

已正确处理：15 个具名地址本就写作 `Xxx::Xxx` [已证]，无 noinit_t 降级。0x40E320/0x52ACE0 等重复地址属同码折叠，不影响。

- `0x0040E320` 现=`GenericNode::GenericNode` [[已证]] → 应为=`GenericNode::GenericNode()` [[已证]]（GenericList.h:15）
- `0x0040E320` 现=`GenericNode::GenericNode` [[已证]] → 应为=`Node::Node()` [[已证]]（GenericList.h:38）
- `0x00410170` 现=`AbstractClass::AbstractClass` [[已证]] → 应为=`AbstractClass::AbstractClass() noexcept` [[已证]]（AbstractClass.h:149）
- `0x00410800` 现=`AbstractTypeClass::AbstractTypeClass` [[已证]] → 应为=`AbstractTypeClass::AbstractTypeClass(const char* pID) noexcept` [[已证]]（AbstractTypeClass.h:63）
- `0x00413D20` 现=`AircraftClass::AircraftClass` [[已证]] → 应为=`AircraftClass::AircraftClass(AircraftTypeClass* pType, HouseClass* pOwner) noexcept` [[已证]]（AircraftClass.h:54）
- `0x0041C8B0` 现=`AircraftTypeClass::AircraftTypeClass` [[已证]] → 应为=`AircraftTypeClass::AircraftTypeClass(const char* pID) noexcept` [[已证]]（AircraftTypeClass.h:31）
- `0x0041D380` 现=`AirstrikeClass::AirstrikeClass` [[已证]] → 应为=`AirstrikeClass::AirstrikeClass(TechnoClass* pOwner) noexcept` [[已证]]（AirstrikeClass.h:36）
- `0x0041E350` 现=`AITriggerTypeClass::AITriggerTypeClass` [[已证]] → 应为=`AITriggerTypeClass::AITriggerTypeClass(const char* pID) noexcept` [[已证]]（AITriggerTypeClass.h:151）
- `0x00420960` 现=`AlphaShapeClass::AlphaShapeClass` [[已证]] → 应为=`AlphaShapeClass::AlphaShapeClass(ObjectClass* pObj, int nX, int nY) noexcept` [[已证]]（AlphaShapeClass.h:36）
- `0x00421EA0` 现=`AnimClass::AnimClass` [[已证]] → 应为=`AnimClass::AnimClass(AnimTypeClass* pAnimType, const CoordStruct& Location, int LoopDelay = 0,` [[已证]]（AnimClass.h:62）
- `0x00427530` 现=`AnimTypeClass::AnimTypeClass` [[已证]] → 应为=`AnimTypeClass::AnimTypeClass(const char* pID) noexcept` [[已证]]（AnimTypeClass.h:42）
- `0x00431B20` 现=`BufferIOFileClass::BufferIOFileClass` [[已证]] → 应为=`BufferIOFileClass::BufferIOFileClass()` [[已证]]（CCFileClass.h:134）
- `0x00435820` 现=`BuildingLightClass::BuildingLightClass` [[已证]] → 应为=`BuildingLightClass::BuildingLightClass(ObjectClass* pOwner) noexcept` [[已证]]（BuildingLightClass.h:33）
- `0x004385D0` 现=`BombClass::BombClass` [[已证]] → 应为=`BombClass::BombClass() noexcept` [[已证]]（BombClass.h:49）
- `0x0043A350` 现=`NeuronClass::NeuronClass` [[已证]] → 应为=`NeuronClass::NeuronClass() noexcept` [[已证]]（NeuronClass.h:31）
- `0x0043B740` 现=`BuildingClass::BuildingClass` [[已证]] → 应为=`BuildingClass::BuildingClass(BuildingTypeClass* pType, HouseClass* pOwner) noexcept` [[已证]]（BuildingClass.h:197）

### C02 — 误剔 9 / 本轮增量 0 / 修正后 high 840

9 行叫 `Xxx::noinit_t`，但 trace `conf=high / source=self_known`，**已计入 840**，high 增量 0；属错名（应改具名构造器名），非降级。

- `0x0045DD90` 现=`BuildingTypeClass::noinit_t` [[已证]] → 应为=`BuildingTypeClass::BuildingTypeClass(const char* pID) noexcept` [[已证]]（BuildingTypeClass.h:90）
- `0x00466380` 现=`BulletClass::noinit_t` [[已证]] → 应为=`BulletClass::BulletClass() noexcept` [[已证]]（BulletClass.h:114）
- `0x0046BBC0` 现=`BulletTypeClass::noinit_t` [[已证]] → 应为=`BulletTypeClass::BulletTypeClass(const char* pID) noexcept` [[已证]]（BulletTypeClass.h:61）
- `0x0046CB60` 现=`CampaignClass::noinit_t` [[已证]] → 应为=`CampaignClass::CampaignClass(const char *name) noexcept` [[已证]]（CampaignClass.h:12）
- `0x004717D0` 现=`CaptureManagerClass::noinit_t` [[已证]] → 应为=`CaptureManagerClass::CaptureManagerClass(TechnoClass* pOwner, int nMaxControlNodes, bool bInfiniteControl) noexcept` [[已证]]（CaptureManagerClass.h:73）
- `0x004739F0` 现=`CCFileClass::noinit_t` [[已证]] → 应为=`CCFileClass::CCFileClass(const char* pFileName)` [[已证]]（CCFileClass.h:202）
- `0x0047AA30` 现=`CCFileClass::noinit_t` [[已证]] → 应为=`CDFileClass::CDFileClass()` [[已证]]（CCFileClass.h:175）
- `0x0047BBF0` 现=`CellClass::noinit_t` [[已证]] → 应为=`CellClass::CellClass() noexcept` [[已证]]（CellClass.h:324）
- `0x0048E740` 现=`ConvertClass::noinit_t` [[已证]] → 应为=`ConvertClass::ConvertClass(` [[已证]]（ConvertClass.h:46）

### C03 — 误剔 6 / 本轮增量 0 / 修正后 high 428

6 行叫 `Xxx::noinit_t`，但 trace `conf=high / source=self_strong`，**已计入 428**，high 增量 0；同 C02 属错名。

- `0x004A7A30` 现=`DiskLaserClass::noinit_t` [[已证]] → 应为=`DiskLaserClass::DiskLaserClass() noexcept` [[已证]]（DiskLaserClass.h:44）
- `0x004BA5A0` 现=`Surface::noinit_t` [[已证]] → 应为=`DSurface::DSurface(int width, int height, bool backBuffer, bool force3D) noexcept` [[已证]]（Surface.h:466）
- `0x004C52B0` 现=`EMPulseClass::noinit_t` [[已证]] → 应为=`EMPulseClass::EMPulseClass(CellStruct dwCrd, int nSpread, int nDuration,` [[已证]]（EMPulseClass.h:33）
- `0x004C98B0` 现=`FactoryClass::noinit_t` [[已证]] → 应为=`FactoryClass::FactoryClass() noexcept` [[已证]]（FactoryClass.h:104）
- `0x004CC9A0` 现=`FlyLocomotionClass::noinit_t` [[已证]] → 应为=`FlyLocomotionClass::FlyLocomotionClass()` [[已证]]（FlyLocomotionClass.h:43）
- `0x004D31E0` 现=`FootClass::noinit_t` [[已证]] → 应为=`FootClass::FootClass(HouseClass* owner) noexcept` [[已证]]（FootClass.h:132）

### C04 — 误剔 7 / 本轮增量 +7 / 修正后 high 783

7 个唯一地址（9 行含 0x52ACE0/0x5447C0 各 2 实例）全为 `sub_XXXXXX` [未证] / conf=low，真实具名构造器被降级 → **本轮 +7**。C04 VERDICT §反向问题已报 10 个 noinit_t 落名，其中 3 个 Sxx 归属错另计（见 UNKNOWNS），high 口径本卡此前未补。

- `0x004F54A0` 现=`sub_004F54A0` [[未证]] → 应为=`HouseClass::HouseClass(HouseTypeClass* pCountry) noexcept` [[已证]]（HouseClass.h:662）
- `0x005113F0` 现=`sub_005113F0` [[未证]] → 应为=`HouseTypeClass::HouseTypeClass(const char* pID) noexcept` [[已证]]（HouseTypeClass.h:50）
- `0x00517A50` 现=`sub_00517A50` [[未证]] → 应为=`InfantryClass::InfantryClass(InfantryTypeClass* pType, HouseClass* pOwner) noexcept` [[已证]]（InfantryClass.h:34）
- `0x005236A0` 现=`sub_005236A0` [[未证]] → 应为=`InfantryTypeClass::InfantryTypeClass(const char* pID) noexcept` [[已证]]（InfantryTypeClass.h:63）
- `0x0052ACE0` 现=`sub_0052ACE0` [[未证]] → 应为=`GenericList::GenericList()` [[已证]]（GenericList.h:55）
- `0x0052ACE0` 现=`sub_0052ACE0` [[未证]] → 应为=`List::List()` [[已证]]（GenericList.h:78）
- `0x00543780` 现=`sub_00543780` [[未证]] → 应为=`IsometricTileClass::IsometricTileClass(int idxType, CellStruct const& location) noexcept` [[已证]]（IsometricTileClass.h:37）
- `0x005447C0` 现=`sub_005447C0` [[未证]] → 应为=`IsometricTileTypeClass::IsometricTileTypeClass(int ArrayIndex, int Minus65, int Zero1,` [[已证]]（IsometricTileTypeClass.h:43）
- `0x005447C0` 现=`sub_005447C0` [[未证]] → 应为=`TagTypeClass::TagTypeClass(char const* pName) noexcept` [[已证]]（TagTypeClass.h:82）

### C05 — 误剔 6 / 本轮增量 +6 / 修正后 high 571

6 地址全为 `sub_XXXXXX`：3 个 conf=low [未证]、3 个 conf=med [静态推断]（MPObserverTeam / MPSiegeDefenderTeam / MPSiegeAttackerTeam），均未进 565 → **本轮 +6**。

- `0x00554760` 现=`sub_00554760` [[未证]] → 应为=`LightSourceClass::LightSourceClass(` [[已证]]（LightSourceClass.h:41）
- `0x00555DA0` 现=`sub_00555DA0` [[未证]] → 应为=`LightConvertClass::LightConvertClass<see ConvertClass.h:98>` [[已证]]（ConvertClass.h:98）
- `0x0055A6C0` 现=`sub_0055A6C0` [[未证]] → 应为=`LocomotionClass::LocomotionClass()` [[已证]]（LocomotionClass.h:282）
- `0x005C9470` 现=`sub_005C9470` [[静态推断]] → 应为=`MPObserverTeam::MPObserverTeam()` [[已证]]（MPTeams.h:84）
- `0x005CAE10` 现=`sub_005CAE10` [[静态推断]] → 应为=`MPSiegeDefenderTeam::MPSiegeDefenderTeam()` [[已证]]（MPTeams.h:58）
- `0x005CAEB0` 现=`sub_005CAEB0` [[静态推断]] → 应为=`MPSiegeAttackerTeam::MPSiegeAttackerTeam()` [[已证]]（MPTeams.h:71）

### C06 — 误剔 8 / 本轮增量 +8 / 修正后 high 390（严格 282）

9 地址：8 个 `sub_` [未证]/conf=low 被降级 → **本轮 +8**；另 `0x5D8170` conf=high 但名为 vtable 槽 `T_Initializer_VMultiplayerBattle___MultiplayerGameMode::slot1` [静态推断]，已进 382，不属「noinit_t 形态 / low/[未证]」，按纪律 §954 不计入误剔，仅记为命名异常。

- `0x005D8170` 现=`T_Initializer_VMultiplayerBattle___MultiplayerGameMode::slot1` [[静态推断]] → 应为=`MPBattleClass::MPBattleClass(wchar_t **CSFTitle, wchar_t **CSFTooltip, char **INIFileName, char **mapfilter, bool AIAllowed, int MPModeIndex)` [[已证]]（MPGameModeClass.h:272）
- `0x005F3900` 现=`sub_005F3900` [[未证]] → 应为=`ObjectClass::ObjectClass()  noexcept` [[已证]]（ObjectClass.h:250）
- `0x005F7090` 现=`sub_005F7090` [[未证]] → 应为=`ObjectTypeClass::ObjectTypeClass(const char* pID) noexcept` [[已证]]（ObjectTypeClass.h:51）
- `0x005FC380` 现=`sub_005FC380` [[未证]] → 应为=`OverlayClass::OverlayClass(OverlayTypeClass* pType) noexcept` [[已证]]（OverlayClass.h:63）
- `0x005FE020` 现=`sub_005FE020` [[未证]] → 应为=`XSurface::XSurface(int width, int height) noexcept : XSurface(noinit_t())` [[已证]]（Surface.h:281）
- `0x005FE250` 现=`sub_005FE250` [[未证]] → 应为=`OverlayTypeClass::OverlayTypeClass(const char* pID) noexcept` [[已证]]（OverlayTypeClass.h:45）
- `0x006292B0` 现=`sub_006292B0` [[未证]] → 应为=`ParasiteClass::ParasiteClass(FootClass* pOwner = nullptr) noexcept` [[已证]]（ParasiteClass.h:50）
- `0x0062B5E0` 现=`sub_0062B5E0` [[未证]] → 应为=`ParticleClass::ParticleClass(` [[已证]]（ParticleClass.h:42）
- `0x0062DC50` 现=`sub_0062DC50` [[未证]] → 应为=`ParticleSystemClass::ParticleSystemClass<see ParticleSystemClass.h:40>` [[已证]]（ParticleSystemClass.h:40）

### C07 — 误剔 13 / 本轮增量 +13 / 修正后 high 572（严格 372）

13 地址全为 `sub_XXXXXX` [未证] / conf=low，真实构造器被降级 → **本轮 +13**。

- `0x006440A0` 现=`sub_006440A0` [[未证]] → 应为=`ParticleSystemTypeClass::ParticleSystemTypeClass(const char* pID) noexcept` [[已证]]（ParticleSystemTypeClass.h:39）
- `0x00644BE0` 现=`sub_00644BE0` [[未证]] → 应为=`ParticleTypeClass::ParticleTypeClass(const char* pID) noexcept` [[已证]]（ParticleTypeClass.h:40）
- `0x0065A750` 现=`sub_0065A750` [[未证]] → 应为=`RadioClass::RadioClass() noexcept` [[已证]]（RadioClass.h:61）
- `0x0065B1E0` 现=`sub_0065B1E0` [[未证]] → 应为=`RadSiteClass::RadSiteClass()` [[已证]]（RadSiteClass.h:94）
- `0x0065CA80` 现=`sub_0065CA80` [[未证]] → 应为=`RawFileClass::RawFileClass(const char* pFileName)` [[已证]]（CCFileClass.h:99）
- `0x00661EC0` 现=`sub_00661EC0` [[未证]] → 应为=`RocketLocomotionClass::RocketLocomotionClass()` [[已证]]（RocketLocomotionClass.h:43）
- `0x006913C0` 现=`sub_006913C0` [[未证]] → 应为=`ScriptClass::ScriptClass(ScriptTypeClass* pType) noexcept` [[已证]]（ScriptClass.h:51）
- `0x006916B0` 现=`sub_006916B0` [[未证]] → 应为=`ScriptTypeClass::ScriptTypeClass(const char* pID) noexcept` [[已证]]（ScriptTypeClass.h:46）
- `0x006A4550` 现=`sub_006A4550` [[未证]] → 应为=`SideClass::SideClass(const char* pID) noexcept` [[已证]]（SideClass.h:33）
- `0x006AF1A0` 现=`sub_006AF1A0` [[未证]] → 应为=`SlaveManagerClass::SlaveManagerClass(` [[已证]]（SlaveManagerClass.h:94）
- `0x006B4A50` 现=`sub_006B4A50` [[未证]] → 应为=`SmudgeClass::SmudgeClass(SmudgeTypeClass* pType) noexcept` [[已证]]（SmudgeClass.h:34）
- `0x006B5260` 现=`sub_006B5260` [[未证]] → 应为=`SmudgeTypeClass::SmudgeTypeClass(const char* pID) noexcept` [[已证]]（SmudgeTypeClass.h:40）
- `0x006B6C90` 现=`sub_006B6C90` [[未证]] → 应为=`SpawnManagerClass::SpawnManagerClass(` [[已证]]（SpawnManagerClass.h:83）

### C08 — 误剔 9 / 本轮增量 0 / 修正后 high 417（严格 416）

9 地址全为 `sub_` [未证]/conf=low；**§960 已修正 +9（408→417，严格 416）**，本轮不重复计入。

- `0x006CAF90` 现=`sub_006CAF90` [[未证]] → 应为=`SuperClass::SuperClass(SuperWeaponTypeClass* pSWType, HouseClass* pOwner) noexcept` [[已证]]（SuperClass.h:102）
- `0x006CE5B0` 现=`sub_006CE5B0` [[未证]] → 应为=`SuperWeaponTypeClass::SuperWeaponTypeClass(const char* pID) noexcept` [[已证]]（SuperWeaponTypeClass.h:46）
- `0x006E4DE0` 现=`sub_006E4DE0` [[未证]] → 应为=`TagClass::TagClass(TagTypeClass* pType) noexcept` [[已证]]（TagClass.h:107）
- `0x006E7E80` 现=`sub_006E7E80` [[未证]] → 应为=`TaskForceClass::TaskForceClass(const char* pID) noexcept` [[已证]]（TaskForceClass.h:42）
- `0x006E8A90` 现=`sub_006E8A90` [[未证]] → 应为=`TeamClass::TeamClass(TeamTypeClass* pType) noexcept` [[已证]]（TeamClass.h:43）
- `0x006F06E0` 现=`sub_006F06E0` [[未证]] → 应为=`TeamTypeClass::TeamTypeClass(const char* pID) noexcept` [[已证]]（TeamTypeClass.h:77）
- `0x006F2B40` 现=`sub_006F2B40` [[未证]] → 应为=`TechnoClass::TechnoClass(HouseClass* pOwner) noexcept` [[已证]]（TechnoClass.h:465）
- `0x00710AF0` 现=`sub_00710AF0` [[未证]] → 应为=`TechnoTypeClass::TechnoTypeClass(const char* id, SpeedType speedtype) noexcept` [[已证]]（TechnoTypeClass.h:166）
- `0x00718000` 现=`sub_00718000` [[未证]] → 应为=`TeleportLocomotionClass::TeleportLocomotionClass()` [[已证]]（TeleportLocomotionClass.h:52）

### C09 — 误剔 15 / 本轮增量 0 / 修正后 high 438

15 唯一地址（16 行含 0x71E6A0 双实例）全为 `sub_` [未证]/conf=low；**§942 已修正 +15（423→438）**，本轮不重复计入。

- `0x0071A4E0` 现=`sub_0071A4E0` [[未证]] → 应为=`TemporalClass::TemporalClass(TechnoClass* pOwnerUnit) noexcept` [[已证]]（TemporalClass.h:51）
- `0x0071BB90` 现=`sub_0071BB90` [[未证]] → 应为=`TerrainClass::TerrainClass(TerrainTypeClass* tt, CellStruct coords) noexcept` [[已证]]（TerrainClass.h:35）
- `0x0071DA80` 现=`sub_0071DA80` [[未证]] → 应为=`TerrainTypeClass::TerrainTypeClass(const char* pID) noexcept` [[已证]]（TerrainTypeClass.h:37）
- `0x0071E6A0` 现=`sub_0071E6A0` [[未证]] → 应为=`TActionClass::TActionClass() noexcept` [[已证]]（TActionClass.h:272）
- `0x0071E6A0` 现=`sub_0071E6A0` [[未证]] → 应为=`TEventClass::TEventClass() noexcept` [[已证]]（TEventClass.h:65）
- `0x007216C0` 现=`sub_007216C0` [[未证]] → 应为=`TiberiumClass::TiberiumClass(const char* pID)` [[已证]]（TiberiumClass.h:55）
- `0x00725FA0` 现=`sub_00725FA0` [[未证]] → 应为=`TriggerClass::TriggerClass(TriggerTypeClass* pType)` [[已证]]（TriggerClass.h:106）
- `0x00726C80` 现=`sub_00726C80` [[未证]] → 应为=`TriggerTypeClass::TriggerTypeClass(char const* pName)` [[已证]]（TriggerTypeClass.h:88）
- `0x007353C0` 现=`sub_007353C0` [[未证]] → 应为=`UnitClass::UnitClass(UnitTypeClass* pType, HouseClass* pOwner) noexcept` [[已证]]（UnitClass.h:50）
- `0x007470D0` 现=`sub_007470D0` [[未证]] → 应为=`UnitTypeClass::UnitTypeClass(const char* pID) noexcept` [[已证]]（UnitTypeClass.h:39）
- `0x007493B0` 现=`sub_007493B0` [[未证]] → 应为=`VoxelAnimClass::VoxelAnimClass(` [[已证]]（VoxelAnimClass.h:42）
- `0x0074AD80` 现=`sub_0074AD80` [[未证]] → 应为=`VoxelAnimTypeClass::VoxelAnimTypeClass(const char* pID)` [[已证]]（VoxelAnimTypeClass.h:40）
- `0x0075CEC0` 现=`sub_0075CEC0` [[未证]] → 应为=`WarheadTypeClass::WarheadTypeClass(const char* pID)` [[已证]]（WarheadTypeClass.h:48）
- `0x0075E950` 现=`sub_0075E950` [[未证]] → 应为=`WaveClass::WaveClass(` [[已证]]（WaveClass.h:43）
- `0x00763810` 现=`sub_00763810` [[未证]] → 应为=`WaypointPathClass::WaypointPathClass(int idx)` [[已证]]（WaypointPathClass.h:48）
- `0x00771C70` 现=`sub_00771C70` [[未证]] → 应为=`WeaponTypeClass::WeaponTypeClass(const char* pID = nullptr)` [[已证]]（WeaponTypeClass.h:44）

### C10 — 误剔 0 / 本轮增量 0 / 修正后 high 254

本片 atlas 区间内无 noinit_t 真构造器地址（0 行），无影响。

- （无命中）

