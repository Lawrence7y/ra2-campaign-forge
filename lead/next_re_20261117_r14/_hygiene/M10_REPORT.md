# M10_REPORT — name-only repair（2026-11-18）
写域：COVERAGE/ + _hygiene/；仅改 name 列，不动任何 grade/subsystem/semantics/evidence/conflict。
快照：_hygiene/M10_before/coverage.tsv SHA-256 a3141883ae09acd8be14655a345fe29f3c07bd05fbf748101e9b49d86037847a

## 逐条改名（entry / old → new / 来源卡 / 裁决）
- 00517A50 sub_00517A50→InfantryClass::InfantryClass [S05-K1/PARTIAL] ; 005F3900 sub_005F3900→ObjectClass::ObjectClass [S05-K1/PARTIAL] ; 0047BB60 sub_0047BB60→CellClass::~CellClass [S06-K1/PARTIAL]
- 0047FF80 sub_0047FF80→CellClass::GetCenterCoords [S06-K1/PARTIAL] ; 00486840 CellClass::slot18→CellClass::GetCellCenterCoord [S06-K1/PARTIAL] ; 00487E70 CellClass::slot12→CellClass::GetSize [S06-K1/PARTIAL]
- 004A8730 sub_004A8730→DisplayClass::DisplayClass [S06-K1/PARTIAL] ; 004F4410 MouseClass::slot12→MapClass::(no GetSize) [S06-K1/PARTIAL] ; 00565090 sub_00565090→MapClass::MapClass [S06-K1/PARTIAL]
- 005656D0 MouseClass::slot3→MapClass::IsValidCellStruct [S06-K1/PARTIAL] ; 005657E0 sub_005657E0→MapClass::IsCellOccupied [S06-K1/PARTIAL] ; 00565800 MapClass::slot5→MapClass::InitDimensions [S06-K1/PARTIAL]
- 005FDD20 sub_005FDD20→TiberiumClass::GetIndexByTypeID [S06-K1/PARTIAL] ; 006B6C90 sub_006B6C90→SpawnManagerClass::SpawnManagerClass_5args [S10_K8/PARTIAL] ; 0041C250 sub_0041C250→LocomotionClass::CreateInstance [S11-K1/PARTIAL]
- 004AFD40 DriveLocomotionClass::slot17→DriveLocomotion::Move_To [S11-K1/PARTIAL] ; 004B0500 DriveLocomotionClass::slot16→DriveLocomotion::Process [S11-K1/PARTIAL] ; 004D55C0 AircraftClass::slot320→FootClass::StopMoving [S11-K1/PARTIAL]
- 004D55F0 AircraftClass::slot319→FootClass::MoveTo [S11-K1/PARTIAL] ; 004D9C10 FootClass::slot107→FootClass::Can_Enter_Cell [S11-K1/PARTIAL] ; 004DA530 FootClass::slot23→FootClass::AI [S11-K1/PARTIAL]
- 006BB9A0 sub_006BB9A0→COM_ClassRegistration [S11-K1/PARTIAL] ; 006C3F40 sub_006C3F40→DriveClassFactory::ctor [S11-K1/PARTIAL] ; 006C4010 T_TClassFactory_VDriveLocomotionClass__::slot3→DriveClassFactory::CreateInstance [S11-K1/PARTIAL]
- 006C40C0 sub_006C40C0→JumpjetClassFactory::ctor [S11-K1/PARTIAL] ; 006C4240 sub_006C4240→HoverClassFactory::ctor [S11-K1/PARTIAL] ; 006C4310 T_TClassFactory_VHoverLocomotionClass__::slot3→HoverClassFactory::CreateInstance [S11-K1/PARTIAL]
- 006C43C0 sub_006C43C0→RocketClassFactory::ctor [S11-K1/PARTIAL] ; 006C4490 T_TClassFactory_VRocketLocomotionClass__::slot3→RocketClassFactory::CreateInstance [S11-K1/PARTIAL] ; 006C4540 sub_006C4540→TunnelClassFactory::ctor [S11-K1/PARTIAL]
- 006C4610 T_TClassFactory_VTunnelLocomotionClass__::slot3→TunnelClassFactory::CreateInstance [S11-K1/PARTIAL] ; 006C46C0 sub_006C46C0→WalkClassFactory::ctor [S11-K1/PARTIAL] ; 006C4790 T_TClassFactory_VWalkLocomotionClass__::slot3→WalkClassFactory::CreateInstance [S11-K1/PARTIAL]
- 006C4840 sub_006C4840→DropPodClassFactory::ctor [S11-K1/PARTIAL] ; 006C4910 T_TClassFactory_VDropPodLocomotionClass__::slot3→DropPodClassFactory::CreateInstance [S11-K1/PARTIAL] ; 006C49C0 sub_006C49C0→FlyClassFactory::ctor [S11-K1/PARTIAL]
- 006C4A90 T_TClassFactory_VFlyLocomotionClass__::slot3→FlyClassFactory::CreateInstance [S11-K1/PARTIAL] ; 006C4B40 sub_006C4B40→TeleportClassFactory::ctor [S11-K1/PARTIAL] ; 006C4C10 T_TClassFactory_VTeleportLocomotionClass__::slot3→TeleportClassFactory::CreateInstance [S11-K1/PARTIAL]
- 006C4CC0 sub_006C4CC0→MechClassFactory::ctor [S11-K1/PARTIAL] ; 006C4D90 T_TClassFactory_VMechLocomotionClass__::slot3→MechClassFactory::CreateInstance [S11-K1/PARTIAL] ; 006C4E40 sub_006C4E40→ShipClassFactory::ctor [S11-K1/PARTIAL]
- 006C4F10 T_TClassFactory_VShipLocomotionClass__::slot3→ShipClassFactory::CreateInstance [S11-K1/PARTIAL] ; 006C6400 sub_006C6400→RegisterClassObject_Wrapper [S11-K1/PARTIAL] ; 0075AC80 WalkLocomotionClass::slot16→WalkLocomotion::Process [S11-K1/PARTIAL]
- 0075ACB0 WalkLocomotionClass::slot17→WalkLocomotion::Move_To [S11-K1/PARTIAL] ; 0041BEA0 AircraftClass::vslot110→ObjectClass::GetMapCoords [S12-Q2/PARTIAL] ; 00459ED0 BuildingClass::slot36→BuildingClass_slot90_getTypeField [S12-Q2/PARTIAL]
- 00459EE0 BuildingClass::slot34→BuildingClass::GetType_slot88 [S12-Q2/PARTIAL] ; 005F6940 AnimClass::slot109→ObjectClass::SetLocation [S12-Q2/PARTIAL] ; 0041FB10 AITriggerTypeClass::vslot26→AITriggerTypeClass::LoadFromINI [S14-F1/PARTIAL]
- 006F0AB0 sub_006F0AB0→AITriggerTypeClass::Evaluate [S14-F1/PARTIAL] ; 0062B5E0 sub_0062B5E0→ParticleClass::ctor [S20-K1/PARTIAL] ; 0062DC50 sub_0062DC50→ParticleSystemClass::ctor [S20-K1/PARTIAL]
- 0052CB90 sub_0052CB90→BATTLEMD_Enumerate [S21-F1/PARTIAL]

## 排除与冲突
- FAIL 卡：无候选行命中（S03-K2R、S11_K4 等 FAIL 卡无符合 a–e 的行）。
- 无 VERDICT：S10_K8F 有候选 006B6C90 sub_006B6C90→SpawnManagerClass::SpawnManagerClass_5args，已排除；该 entry 由 S10_K8(PARTIAL) 同名提供，已改名。
- 名字冲突（多卡不同真名）：0。CONFLICTS.tsv 新增 0 行。
- 多卡同名一致：0047BB60/0047FF80(S06-K1,K2)、00487E70(S06-K1,K2,S12-K2)、004DA530(S11-K1,S14-F1)，取 PASS 优先后按卡号序，非冲突。

## 自检证据
- 行数 before=18431 after=18431（无增删 entry）。
- grade 分布 before={"[未证]":11031,"[已证]":1362,"[静态推断]":6038} after={"[未证]":11031,"[已证]":1362,"[静态推断]":6038} → 完全一致。
- 逐行对比：55 行变化，仅第 3 列 name 变化；其余 7 列 0 处差异。
- named 全表：L 11506→11533；S(R14) 11498→11525；S(strict) 5186→5241。
- named atlas 内：L 7166→7193；S(R14) 7158→7185；S(strict) 1256→1311；proved 1357 不变。
- PENDING_CORRECTIONS.tsv 新增 55 行（理由 name-only repair from <卡号>（该卡 VERDICT=<裁决>））。
- 改名行数：55。
