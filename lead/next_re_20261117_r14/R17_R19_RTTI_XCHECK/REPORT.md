D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe  sha256 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476

# R17-R19-RTTI-XCHECK · in-binary RTTI 类名 × coverage 类名表内对账

- 镜像校验：实际路径见第一行；sha256 以 **73201CC0** 开头，符合卡面期望，结果有效。
- 镜像大小：4,825,360 B。读取方式：纯静态只读；未建进程、未调试、未启动 gamemd。
- 数据扫描：只读 PE 节 .rdata raw 0x3E1000 长度 0x31000 = 200,704 B；.data raw 0x412000 长度 0x6C000 = 442,368 B；合计 **643,072 B**。未扫描 .text/.rsrc/.detour。
- coverage.tsv：只读打开；大小 4,147,334 B；sha256 C2EE063FD4F61F784585EF2ABCC4FF563FA09EC1B1F7F5079643076E359C744A；写后复核 sha256 C2EE063FD4F61F784585EF2ABCC4FF563FA09EC1B1F7F5079643076E359C744A，**未修改**。
- 中间结果已先落盘：`_stage0_sections.json`、`_stage1_td.json`、`_stage2_coverage.json`、`_stage3_reconcile.json`。
- 产物目录：`lead\next_re_20261117_r14\R17_R19_RTTI_XCHECK\`；未写其他目录。

## Q1 · in-binary RTTI 类名集合

- 方法：自行解析 PE 节表；在 .rdata/.data 的 raw-backed 字节中，按 4 字节步进寻找 TypeDescriptor 形态 `vftable=0x7F9594, spare=0, nameVA=TD+8, name以 .? 起`，读取 NUL 结尾 ASCII 名；未复用既有 names.tsv 作为输入。
- 装饰名总数：**988**；唯一装饰名 988。
- 前缀分布：`.?AV` **962**，`.?AU` **26**，`.?AW` 0，`??_7` 0，其它 0；与卡面 988 = 962 + 26 一致。
- 归一化：去 `.?AV` / `.?AU` 前缀与尾部 `@@` 后，裸类名 **988** 个；全小写裸名 **988** 个（仅用于备注旁证，不改变主比对的大小写原样口径）。
- 首项：TD VA 0x815de0 → `.?AVFileClass@@` → `FileClass`；末项：TD VA 0x87da10 → `.?AV_com_error@@` → `_com_error`。
- RTTI 结构旁证：.rdata 内 signature=0、cdOffset=0、offset∈{0,4,8,12} 且 pTD 命中上述 TD 集的 COL 记录 **1201** 条，覆盖 **954** 个 TD；说明这批名字不是裸字符串猜测，而是挂在 RTTI COL/TypeDescriptor 链上的 in-binary 名字。
- 全量裸名、前缀、TD VA：`rtti_names.tsv`。

## Q2 · coverage.tsv 第 4 列类名抽取

- 数据行：**18,498**；列宽异常行：0。
- 抽取规则：第 4 列中匹配正则 `(?<![A-Za-z0-9_])[A-Za-z_][A-Za-z0-9_]*Class(?![A-Za-z0-9_])`，即“ASCII 标识符且整体以 Class 结尾”；每行去重后按行计数（同一行出现多次只记 1 行）。
- 命中行：**3,270**；原始 token 出现次数：**4,812**；不同类名：**429**。
- 全量类名与行数：`coverage_classnames.tsv`。

Top 30：

| # | class_name | 出现行数 |
|---|---|---|
| 1 | AircraftClass | 201 |
| 2 | HouseClass | 114 |
| 3 | BuildingClass | 94 |
| 4 | DynamicVectorClass | 91 |
| 5 | InfantryClass | 76 |
| 6 | UnitClass | 70 |
| 7 | DriveLocomotionClass | 65 |
| 8 | AnimClass | 64 |
| 9 | FootClass | 64 |
| 10 | TechnoClass | 58 |
| 11 | MapClass | 57 |
| 12 | CellClass | 56 |
| 13 | CCINIClass | 52 |
| 14 | CheckListClass | 51 |
| 15 | DropPodLocomotionClass | 43 |
| 16 | TActionClass | 43 |
| 17 | ShipLocomotionClass | 42 |
| 18 | TeamClass | 42 |
| 19 | RulesClass | 37 |
| 20 | MPGameModeClass | 36 |
| 21 | ObjectClass | 36 |
| 22 | MouseClass | 33 |
| 23 | WalkLocomotionClass | 32 |
| 24 | FlyLocomotionClass | 30 |
| 25 | JumpjetLocomotionClass | 29 |
| 26 | BuildingTypeClass | 28 |
| 27 | MissionClass | 28 |
| 28 | TeleportLocomotionClass | 28 |
| 29 | FactoryClass | 25 |
| 30 | IPXManagerClass | 25 |

## Q3 · 三桶对账

- 主口径：Q2 抽取标识符与 Q1 裸类名按**大小写原样精确**比对；小写集合只用于 COVERAGE_ONLY 的“可能原因与依据”旁证。
- **BOTH 209**；**COVERAGE_ONLY 220**；**RTTI_ONLY 779**；三桶合计 1208。

BOTH 举例（≤10）：`AbstractClass`、`AbstractTypeClass`、`AddTeamCommandClass`、`AircraftClass`、`AircraftTypeClass`、`AirstrikeClass`、`AITriggerTypeClass`、`AllianceCommandClass`、`AllToCheerCommandClass`、`AlphaShapeClass`。

COVERAGE_ONLY 全量（220 条；每行只给可能原因与依据，不作断言）：

| class_name | 行数 | 可能原因与依据 |
|---|---|---|
| DynamicVectorClass | 91 | 可能原因：模板或参数化类名在coverage里被展开或省略模板实参；依据：Q1裸名 ?$DynamicVectorClass@PAVTechnoClass@@、?$DynamicVectorClass@PAVBombClass@@、?$DynamicVectorClass@PBVCommandClass@@ 包含该token字符串 |
| RulesClass | 37 | 可能原因：YRpp或人工语义命名差异、拼写差异或Class后缀抽取噪声；依据：该token来自coverage第4列，未命中Q1裸名大小写原样集合与全小写集合 |
| MPGameModeClass | 36 | 可能原因：YRpp或人工语义命名差异、拼写差异或Class后缀抽取噪声；依据：该token来自coverage第4列，未命中Q1裸名大小写原样集合与全小写集合 |
| AVWWMouseClass | 16 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 WWMouseClass，该裸名在Q1集合中 |
| AVFootClass | 11 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 FootClass，该裸名在Q1集合中 |
| AVTechnoClass | 11 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 TechnoClass，该裸名在Q1集合中 |
| AVAircraftClass | 10 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 AircraftClass，该裸名在Q1集合中 |
| TacticalClass | 10 | 可能原因：模板或参数化类名在coverage里被展开或省略模板实参；依据：Q1裸名 TacticalClass@DisplayClass、RTacticalClass@RadarClass 包含该token字符串 |
| AVInfantryClass | 9 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 InfantryClass，该裸名在Q1集合中 |
| AVMapSeedClass | 8 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 MapSeedClass，该裸名在Q1集合中 |
| AVLoadOptionsClass | 7 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 LoadOptionsClass，该裸名在Q1集合中 |
| VocClass | 7 | 可能原因：模板或参数化类名在coverage里被展开或省略模板实参；依据：Q1裸名 ?$VectorClass@PAVVocClass@@、?$DynamicVectorClass@PAVVocClass@@ 包含该token字符串 |
| VoxClass | 7 | 可能原因：模板或参数化类名在coverage里被展开或省略模板实参；依据：Q1裸名 ?$VectorClass@PAVVoxClass@@、?$DynamicVectorClass@PAVVoxClass@@ 包含该token字符串 |
| AVBuildingClass | 6 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 BuildingClass，该裸名在Q1集合中 |
| AVRadarClass | 6 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 RadarClass，该裸名在Q1集合中 |
| AVTabClass | 6 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 TabClass，该裸名在Q1集合中 |
| AVCDFileClass | 5 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 CDFileClass，该裸名在Q1集合中 |
| AVIPXInterfaceClass | 5 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 IPXInterfaceClass，该裸名在Q1集合中 |
| AVMissionClass | 5 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 MissionClass，该裸名在Q1集合中 |
| AVMouseClass | 5 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 MouseClass，该裸名在Q1集合中 |
| AVRawFileClass | 5 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 RawFileClass，该裸名在Q1集合中 |
| AVUDPInterfaceClass | 5 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 UDPInterfaceClass，该裸名在Q1集合中 |
| ScenarioClass | 5 | 可能原因：YRpp或人工语义命名差异、拼写差异或Class后缀抽取噪声；依据：该token来自coverage第4列，未命中Q1裸名大小写原样集合与全小写集合 |
| VectorClass | 5 | 可能原因：模板或参数化类名在coverage里被展开或省略模板实参；依据：Q1裸名 ?$VectorClass@USubzoneConnectionStruct@@、?$VectorClass@PAVTechnoClass@@、?$DynamicVectorClass@PAVTechnoClass@@ 包含该token字符串 |
| AVCCFileClass | 4 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 CCFileClass，该裸名在Q1集合中 |
| AVColorListClass | 4 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 ColorListClass，该裸名在Q1集合中 |
| AVDriveLocomotionClass | 4 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 DriveLocomotionClass，该裸名在Q1集合中 |
| AVDropPodLocomotionClass | 4 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 DropPodLocomotionClass，该裸名在Q1集合中 |
| AVFlyLocomotionClass | 4 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 FlyLocomotionClass，该裸名在Q1集合中 |
| AVFoggedObjectClass | 4 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 FoggedObjectClass，该裸名在Q1集合中 |
| AVSidebarClass | 4 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 SidebarClass，该裸名在Q1集合中 |
| PAVBombClass | 4 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 PAV 后为 BombClass，该裸名在Q1集合中 |
| PAVParasiteClass | 4 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 PAV 后为 ParasiteClass，该裸名在Q1集合中 |
| PAVRadSiteClass | 4 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 PAV 后为 RadSiteClass，该裸名在Q1集合中 |
| AVAnimClass | 3 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 AnimClass，该裸名在Q1集合中 |
| AVBombClass | 3 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 BombClass，该裸名在Q1集合中 |
| AVBufferIOFileClass | 3 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 BufferIOFileClass，该裸名在Q1集合中 |
| AVCellClass | 3 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 CellClass，该裸名在Q1集合中 |
| AVDisplayClass | 3 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 DisplayClass，该裸名在Q1集合中 |
| AVLightSourceClass | 3 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 LightSourceClass，该裸名在Q1集合中 |
| AVParasiteClass | 3 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 ParasiteClass，该裸名在Q1集合中 |
| AVPowerClass | 3 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 PowerClass，该裸名在Q1集合中 |
| AVSpawnManagerClass | 3 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 SpawnManagerClass，该裸名在Q1集合中 |
| AVTActionClass | 3 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 TActionClass，该裸名在Q1集合中 |
| AVTagTypeClass | 3 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 TagTypeClass，该裸名在Q1集合中 |
| AVTEventClass | 3 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 TEventClass，该裸名在Q1集合中 |
| AVTiberiumClass | 3 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 TiberiumClass，该裸名在Q1集合中 |
| AVTriggerClass | 3 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 TriggerClass，该裸名在Q1集合中 |
| AVTriggerTypeClass | 3 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 TriggerTypeClass，该裸名在Q1集合中 |
| AVWarheadTypeClass | 3 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 WarheadTypeClass，该裸名在Q1集合中 |
| AVWeaponTypeClass | 3 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 WeaponTypeClass，该裸名在Q1集合中 |
| IonBlastClass | 3 | 可能原因：模板或参数化类名在coverage里被展开或省略模板实参；依据：Q1裸名 ?$VectorClass@PAVIonBlastClass@@、?$DynamicVectorClass@PAVIonBlastClass@@ 包含该token字符串 |
| LaserDrawClass | 3 | 可能原因：模板或参数化类名在coverage里被展开或省略模板实参；依据：Q1裸名 ?$VectorClass@PAVLaserDrawClass@@、?$DynamicVectorClass@PAVLaserDrawClass@@ 包含该token字符串 |
| PAVBulletClass | 3 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 PAV 后为 BulletClass，该裸名在Q1集合中 |
| PAVFoggedObjectClass | 3 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 PAV 后为 FoggedObjectClass，该裸名在Q1集合中 |
| PAVInfantryClass | 3 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 PAV 后为 InfantryClass，该裸名在Q1集合中 |
| PAVSlaveManagerClass | 3 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 PAV 后为 SlaveManagerClass，该裸名在Q1集合中 |
| PAVSpawnManagerClass | 3 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 PAV 后为 SpawnManagerClass，该裸名在Q1集合中 |
| PAVWarheadTypeClass | 3 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 PAV 后为 WarheadTypeClass，该裸名在Q1集合中 |
| PAVWeaponTypeClass | 3 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 PAV 后为 WeaponTypeClass，该裸名在Q1集合中 |
| SelectClass_StripClass_SidebarClass | 3 | 可能原因：人工组合名或子系统名被Class后缀抽取当作单个类名；依据：token含下划线，拆分片段为 SelectClass + StripClass + SidebarClass，其中 SidebarClass命中Q1集合 |
| AVBuildingTypeClass | 2 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 BuildingTypeClass，该裸名在Q1集合中 |
| AVCampaignClass | 2 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 CampaignClass，该裸名在Q1集合中 |
| AVCaptureManagerClass | 2 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 CaptureManagerClass，该裸名在Q1集合中 |
| AVCStreamClass | 2 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 CStreamClass，该裸名在Q1集合中 |
| AVEMPulseClass | 2 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 EMPulseClass，该裸名在Q1集合中 |
| AVFactoryClass | 2 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 FactoryClass，该裸名在Q1集合中 |
| AVHouseTypeClass | 2 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 HouseTypeClass，该裸名在Q1集合中 |
| AVIsometricTileTypeClass | 2 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 IsometricTileTypeClass，该裸名在Q1集合中 |
| AVLogicClass | 2 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 LogicClass，该裸名在Q1集合中 |
| AVMapClass | 2 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 MapClass，该裸名在Q1集合中 |
| AVOverlayClass | 2 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 OverlayClass，该裸名在Q1集合中 |
| AVOverlayTypeClass | 2 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 OverlayTypeClass，该裸名在Q1集合中 |
| AVParticleClass | 2 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 ParticleClass，该裸名在Q1集合中 |
| AVParticleSystemClass | 2 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 ParticleSystemClass，该裸名在Q1集合中 |
| AVParticleTypeClass | 2 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 ParticleTypeClass，该裸名在Q1集合中 |
| AVRadSiteClass | 2 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 RadSiteClass，该裸名在Q1集合中 |
| AVScriptTypeClass | 2 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 ScriptTypeClass，该裸名在Q1集合中 |
| AVScrollClass | 2 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 ScrollClass，该裸名在Q1集合中 |
| AVSmudgeTypeClass | 2 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 SmudgeTypeClass，该裸名在Q1集合中 |
| AVSwizzleManagerClass | 2 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 SwizzleManagerClass，该裸名在Q1集合中 |
| AVTagClass | 2 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 TagClass，该裸名在Q1集合中 |
| AVTechnoTypeClass | 2 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 TechnoTypeClass，该裸名在Q1集合中 |
| AVTerrainClass | 2 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 TerrainClass，该裸名在Q1集合中 |
| AVTerrainTypeClass | 2 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 TerrainTypeClass，该裸名在Q1集合中 |
| AVTubeClass | 2 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 TubeClass，该裸名在Q1集合中 |
| AVUnitClass | 2 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 UnitClass，该裸名在Q1集合中 |
| AVWaypointPathClass | 2 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 WaypointPathClass，该裸名在Q1集合中 |
| InputManagerClass | 2 | 可能原因：YRpp或人工语义命名差异、拼写差异或Class后缀抽取噪声；依据：该token来自coverage第4列，未命中Q1裸名大小写原样集合与全小写集合 |
| PAVAbstractClass | 2 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 PAV 后为 AbstractClass，该裸名在Q1集合中 |
| PAVCaptureManagerClass | 2 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 PAV 后为 CaptureManagerClass，该裸名在Q1集合中 |
| PAVLaserDrawClass | 2 | 可能原因：模板或参数化类名在coverage里被展开或省略模板实参；依据：Q1裸名 ?$VectorClass@PAVLaserDrawClass@@、?$DynamicVectorClass@PAVLaserDrawClass@@ 包含该token字符串 |
| PAVTemporalClass | 2 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 PAV 后为 TemporalClass，该裸名在Q1集合中 |
| RadarEventClass | 2 | 可能原因：模板或参数化类名在coverage里被展开或省略模板实参；依据：Q1裸名 ?$VectorClass@PAVRadarEventClass@@、?$DynamicVectorClass@PAVRadarEventClass@@ 包含该token字符串 |
| SBGadgetClass_SidebarClass | 2 | 可能原因：人工组合名或子系统名被Class后缀抽取当作单个类名；依据：token含下划线，拆分片段为 SBGadgetClass + SidebarClass，其中 SidebarClass命中Q1集合 |
| SpotlightClass | 2 | 可能原因：模板或参数化类名在coverage里被展开或省略模板实参；依据：Q1裸名 ?$VectorClass@PAVSpotLightClass@@、?$DynamicVectorClass@PAVSpotLightClass@@ 包含该token字符串 |
| TacticalClass_DisplayClass | 2 | 可能原因：人工组合名或子系统名被Class后缀抽取当作单个类名；依据：token含下划线，拆分片段为 TacticalClass + DisplayClass，其中 DisplayClass命中Q1集合 |
| ABufferClass | 1 | 可能原因：YRpp或人工语义命名差异、拼写差异或Class后缀抽取噪声；依据：该token来自coverage第4列，未命中Q1裸名大小写原样集合与全小写集合 |
| AVAbstractClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 AbstractClass，该裸名在Q1集合中 |
| AVAbstractTypeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 AbstractTypeClass，该裸名在Q1集合中 |
| AVAircraftTypeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 AircraftTypeClass，该裸名在Q1集合中 |
| AVAITriggerTypeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 AITriggerTypeClass，该裸名在Q1集合中 |
| AVAlphaShapeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 AlphaShapeClass，该裸名在Q1集合中 |
| AVAnimTypeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 AnimTypeClass，该裸名在Q1集合中 |
| AVBuildingLightClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 BuildingLightClass，该裸名在Q1集合中 |
| AVBulletClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 BulletClass，该裸名在Q1集合中 |
| AVBulletTypeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 BulletTypeClass，该裸名在Q1集合中 |
| AVConvertClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 ConvertClass，该裸名在Q1集合中 |
| AVCounterClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 CounterClass，该裸名在Q1集合中 |
| AVDiskLaserClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 DiskLaserClass，该裸名在Q1集合中 |
| AVHouseClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 HouseClass，该裸名在Q1集合中 |
| AVInfantryTypeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 InfantryTypeClass，该裸名在Q1集合中 |
| AVIPXManagerClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 IPXManagerClass，该裸名在Q1集合中 |
| AVIsometricTileClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 IsometricTileClass，该裸名在Q1集合中 |
| AVJumpjetLocomotionClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 JumpjetLocomotionClass，该裸名在Q1集合中 |
| AVLayerClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 LayerClass，该裸名在Q1集合中 |
| AVLightConvertClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 LightConvertClass，该裸名在Q1集合中 |
| AVListClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 ListClass，该裸名在Q1集合中 |
| AVMixFileClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 MixFileClass，该裸名在Q1集合中 |
| AVObjectTypeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 ObjectTypeClass，该裸名在Q1集合中 |
| AVParticleSystemTypeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 ParticleSystemTypeClass，该裸名在Q1集合中 |
| AVRTacticalClass | 1 | 可能原因：人工语义文本把名字片段粘连到Class后缀标识符；依据：coverage token包含Q1裸名 Tactical |
| AVScriptClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 ScriptClass，该裸名在Q1集合中 |
| AVShipLocomotionClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 ShipLocomotionClass，该裸名在Q1集合中 |
| AVSideClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 SideClass，该裸名在Q1集合中 |
| AVSlaveManagerClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 SlaveManagerClass，该裸名在Q1集合中 |
| AVSmudgeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 SmudgeClass，该裸名在Q1集合中 |
| AVStaticButtonClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 StaticButtonClass，该裸名在Q1集合中 |
| AVSuperWeaponTypeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 SuperWeaponTypeClass，该裸名在Q1集合中 |
| AVTaskForceClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 TaskForceClass，该裸名在Q1集合中 |
| AVTeamClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 TeamClass，该裸名在Q1集合中 |
| AVTeleportLocomotionClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 TeleportLocomotionClass，该裸名在Q1集合中 |
| AVTemporalClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 TemporalClass，该裸名在Q1集合中 |
| AVUnitTypeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 UnitTypeClass，该裸名在Q1集合中 |
| AVVoxelAnimClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 VoxelAnimClass，该裸名在Q1集合中 |
| AVVoxelAnimTypeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 VoxelAnimTypeClass，该裸名在Q1集合中 |
| AVWalkLocomotionClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 WalkLocomotionClass，该裸名在Q1集合中 |
| AVWaveClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 AV 后为 WaveClass，该裸名在Q1集合中 |
| CDDriveManagerClass | 1 | 可能原因：YRpp或人工语义命名差异、拼写差异或Class后缀抽取噪声；依据：该token来自coverage第4列，未命中Q1裸名大小写原样集合与全小写集合 |
| GameOptionsClass | 1 | 可能原因：YRpp或人工语义命名差异、拼写差异或Class后缀抽取噪声；依据：该token来自coverage第4列，未命中Q1裸名大小写原样集合与全小写集合 |
| INIEntry_INIClass | 1 | 可能原因：人工组合名或子系统名被Class后缀抽取当作单个类名；依据：token含下划线，拆分片段为 INIEntry + INIClass，其中 INIClass命中Q1集合 |
| INISection_INIClass | 1 | 可能原因：人工组合名或子系统名被Class后缀抽取当作单个类名；依据：token含下划线，拆分片段为 INISection + INIClass，其中 INIClass命中Q1集合 |
| MessageListClass | 1 | 可能原因：人工语义文本把名字片段粘连到Class后缀标识符；依据：coverage token包含Q1裸名 ListClass |
| MissionControlClass | 1 | 可能原因：人工语义文本把名字片段粘连到Class后缀标识符；依据：coverage token包含Q1裸名 ControlClass |
| MPBattleClass | 1 | 可能原因：YRpp或人工语义命名差异、拼写差异或Class后缀抽取噪声；依据：该token来自coverage第4列，未命中Q1裸名大小写原样集合与全小写集合 |
| MPMegawealthClass | 1 | 可能原因：人工语义文本把名字片段粘连到Class后缀标识符；依据：coverage token包含Q1裸名 Megawealth |
| MPSiegeClass | 1 | 可能原因：YRpp或人工语义命名差异、拼写差异或Class后缀抽取噪声；依据：该token来自coverage第4列，未命中Q1裸名大小写原样集合与全小写集合 |
| MPUnholyAllianceClass | 1 | 可能原因：人工语义文本把名字片段粘连到Class后缀标识符；依据：coverage token包含Q1裸名 UnholyAlliance |
| PAVAirstrikeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 PAV 后为 AirstrikeClass，该裸名在Q1集合中 |
| PAVAlphaShapeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 PAV 后为 AlphaShapeClass，该裸名在Q1集合中 |
| PAVCampaignClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 PAV 后为 CampaignClass，该裸名在Q1集合中 |
| PAVDiskLaserClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 PAV 后为 DiskLaserClass，该裸名在Q1集合中 |
| PAVEMPulseClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 PAV 后为 EMPulseClass，该裸名在Q1集合中 |
| PAVFactoryClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 PAV 后为 FactoryClass，该裸名在Q1集合中 |
| PAVSuperClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 PAV 后为 SuperClass，该裸名在Q1集合中 |
| PAVSuperWeaponTypeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 PAV 后为 SuperWeaponTypeClass，该裸名在Q1集合中 |
| PAVTechnoClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 PAV 后为 TechnoClass，该裸名在Q1集合中 |
| PAVTerrainClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 PAV 后为 TerrainClass，该裸名在Q1集合中 |
| PAVTerrainTypeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 PAV 后为 TerrainTypeClass，该裸名在Q1集合中 |
| PAVWaveClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 PAV 后为 WaveClass，该裸名在Q1集合中 |
| PBVAnimClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 PBV 后为 AnimClass，该裸名在Q1集合中 |
| PlanningTokenClass | 1 | 可能原因：模板或参数化类名在coverage里被展开或省略模板实参；依据：Q1裸名 ?$VectorClass@PAVPlanningTokenClass@@、?$DynamicVectorClass@PAVPlanningTokenClass@@ 包含该token字符串 |
| RTacticalClass | 1 | 可能原因：模板或参数化类名在coverage里被展开或省略模板实参；依据：Q1裸名 RTacticalClass@RadarClass 包含该token字符串 |
| RTacticalClass_RadarClass | 1 | 可能原因：人工组合名或子系统名被Class后缀抽取当作单个类名；依据：token含下划线，拆分片段为 RTacticalClass + RadarClass，其中 RadarClass命中Q1集合 |
| VAircraftTypeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 AircraftTypeClass，该裸名在Q1集合中 |
| VAirstrikeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 AirstrikeClass，该裸名在Q1集合中 |
| VAITriggerTypeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 AITriggerTypeClass，该裸名在Q1集合中 |
| VAlphaShapeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 AlphaShapeClass，该裸名在Q1集合中 |
| VAnimClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 AnimClass，该裸名在Q1集合中 |
| VAnimTypeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 AnimTypeClass，该裸名在Q1集合中 |
| VBombClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 BombClass，该裸名在Q1集合中 |
| VBuildingClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 BuildingClass，该裸名在Q1集合中 |
| VBuildingLightClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 BuildingLightClass，该裸名在Q1集合中 |
| VBuildingTypeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 BuildingTypeClass，该裸名在Q1集合中 |
| VBulletTypeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 BulletTypeClass，该裸名在Q1集合中 |
| VCampaignClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 CampaignClass，该裸名在Q1集合中 |
| VCaptureManagerClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 CaptureManagerClass，该裸名在Q1集合中 |
| VCellClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 CellClass，该裸名在Q1集合中 |
| VCStreamClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 CStreamClass，该裸名在Q1集合中 |
| VDiskLaserClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 DiskLaserClass，该裸名在Q1集合中 |
| VEMPulseClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 EMPulseClass，该裸名在Q1集合中 |
| VFactoryClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 FactoryClass，该裸名在Q1集合中 |
| VFoggedObjectClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 FoggedObjectClass，该裸名在Q1集合中 |
| VInfantryClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 InfantryClass，该裸名在Q1集合中 |
| VInfantryTypeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 InfantryTypeClass，该裸名在Q1集合中 |
| VIsometricTileTypeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 IsometricTileTypeClass，该裸名在Q1集合中 |
| VLightSourceClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 LightSourceClass，该裸名在Q1集合中 |
| VNeuronClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 NeuronClass，该裸名在Q1集合中 |
| VOverlayTypeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 OverlayTypeClass，该裸名在Q1集合中 |
| VParasiteClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 ParasiteClass，该裸名在Q1集合中 |
| VParticleClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 ParticleClass，该裸名在Q1集合中 |
| VParticleSystemClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 ParticleSystemClass，该裸名在Q1集合中 |
| VParticleSystemTypeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 ParticleSystemTypeClass，该裸名在Q1集合中 |
| VParticleTypeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 ParticleTypeClass，该裸名在Q1集合中 |
| VRadSiteClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 RadSiteClass，该裸名在Q1集合中 |
| VScriptClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 ScriptClass，该裸名在Q1集合中 |
| VScriptTypeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 ScriptTypeClass，该裸名在Q1集合中 |
| VSideClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 SideClass，该裸名在Q1集合中 |
| VSlaveManagerClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 SlaveManagerClass，该裸名在Q1集合中 |
| VSmudgeTypeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 SmudgeTypeClass，该裸名在Q1集合中 |
| VSuperClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 SuperClass，该裸名在Q1集合中 |
| VTActionClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 TActionClass，该裸名在Q1集合中 |
| VTagClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 TagClass，该裸名在Q1集合中 |
| VTagTypeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 TagTypeClass，该裸名在Q1集合中 |
| VTaskForceClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 TaskForceClass，该裸名在Q1集合中 |
| VTeamClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 TeamClass，该裸名在Q1集合中 |
| VTeamTypeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 TeamTypeClass，该裸名在Q1集合中 |
| VTemporalClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 TemporalClass，该裸名在Q1集合中 |
| VTEventClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 TEventClass，该裸名在Q1集合中 |
| VTriggerClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 TriggerClass，该裸名在Q1集合中 |
| VTriggerTypeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 TriggerTypeClass，该裸名在Q1集合中 |
| VTubeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 TubeClass，该裸名在Q1集合中 |
| VUnitClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 UnitClass，该裸名在Q1集合中 |
| VUnitTypeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 UnitTypeClass，该裸名在Q1集合中 |
| VVoxelAnimClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 VoxelAnimClass，该裸名在Q1集合中 |
| VVoxelAnimTypeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 VoxelAnimTypeClass，该裸名在Q1集合中 |
| VWarheadTypeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 WarheadTypeClass，该裸名在Q1集合中 |
| VWaypointPathClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 WaypointPathClass，该裸名在Q1集合中 |
| VWeaponTypeClass | 1 | 可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 V 后为 WeaponTypeClass，该裸名在Q1集合中 |
| ZBufferClass | 1 | 可能原因：YRpp或人工语义命名差异、拼写差异或Class后缀抽取噪声；依据：该token来自coverage第4列，未命中Q1裸名大小写原样集合与全小写集合 |

RTTI_ONLY 举例（≤10）：`__non_rtti_object`、`_com_error`、`?$BlitPlain@E`、`?$BlitPlain@G`、`?$BlitPlainXlat@E`、`?$BlitPlainXlat@G`、`?$BlitPlainXlatAlpha@G`、`?$BlitPlainXlatZRead@G`、`?$BlitPlainXlatZReadWrite@G`、`?$BlitTrans@E`。

- 三桶全量：`reconcile.tsv`（每行：类名 / 桶 / 备注）。

## Q4 · 诚实限制

1. **in-binary 名字集合只覆盖有 RTTI 的类**；无 RTTI 的类不会出现在 Q1 集合里，因此 RTTI_ONLY 不能解释为“coverage 一定错”。
2. **coverage 类名是人工语义文本**；本卡靠 `Class` 后缀抽取，会漏（不含 Class 后缀、别名、缩写）也会多（装饰器残片、组合名、子系统名被当成类名）。
3. 因此 **BOTH 只说明两边不矛盾**，不是类名正确性判定；**COVERAGE_ONLY 不等于名字错**，只表示按本卡抽取口径未与 988 个有 RTTI 的裸类名精确相撞。

未取得项：0。