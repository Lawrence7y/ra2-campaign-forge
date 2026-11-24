D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe  sha256 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476

# R17-R20-RECON · RTTI × coverage 对账纠正版

> 🔴 本项**不是类名正确性判定**。未解析只表示：按本卡口径，in-binary RTTI 里没有同名类；不得据此说 coverage 的类名是错的。

- 校验：镜像第一行路径与 sha256 实测一致，前缀 73201CC0，结果有效。镜像大小 4825360 B。
- 静态读取：仅解析 PE 节表并只读 .rdata / .data；.rdata raw 0x3e1000 长度 200704 B，.data raw 0x412000 长度 442368 B，合计 **643072 B**。未建进程、未调试、未启动 gamemd。
- coverage.tsv：只读；4147334 B；sha256 C2EE063FD4F61F784585EF2ABCC4FF563FA09EC1B1F7F5079643076E359C744A；写后复核 C2EE063FD4F61F784585EF2ABCC4FF563FA09EC1B1F7F5079643076E359C744A；未修改。
- 中间结果先落盘：`_stage0_sections.json`、`_stage1_rtti.json`、`_stage2_coverage.json`、`_stage3_normalization.json`、`_stage4_reconcile.json`；全部产物只写本目录。

## Q1 · 两边集合与口径

- in-binary：装饰名 988 个，唯一 988 个；前缀 .?AV 962、.?AU 26。
- 去 .?AV/.?AU/.?AW 与尾部 @@ 后裸名 988 个；模板实例 634 个，首段基名附加键 109 个。
- coverage：第 4 列按 `(?<![A-Za-z0-9_])[A-Za-z_][A-Za-z0-9_]*Class(?![A-Za-z0-9_])` 抽 token；每行去重后按行数计数。
- coverage 数据行 18498；列宽异常 0；命中行 3270；原始 token 出现 4812 次（每行去重后 3777 次）；不同 token 429 个。
- 全量裸名/附加键：`rtti_names.tsv`；原始 token 与上下文片段：`_coverage_contexts.tsv`。

## Q2 · 归一化规则、消解率与 20 条抽检

显式规则（在 `work.py` 中实现，按优先级短路，避免把合法全名改坏）：

1. **原 token 精确命中优先**：大小写不敏感，直接等于任一 in-binary 裸名即停；不继续剥离。
2. **前导 `?`**：仅去一个前导 `?` 后再作精确裸名判定。
3. **MSVC 前缀链**：对未命中的 token，枚举长度 1–4、字符全属于 `P/A/V` 的前缀候选（含 `PAV`、`AV`、`PA`、`V`、`A` 等），仅当剥离后的剩余串**完整等于** in-binary 裸名才接受。
4. **下划线复合名**：对原串及前缀剥离结果按 `_` 分段，仅当某个完整段**完整等于** in-binary 裸名才接受。
5. **模板附加键**：若 token 或上述候选等于模板名 `?$Xxx@...` 的首段基名 `Xxx`，则命中该模板族；原模板形态仍保留。
6. 所有相等判定均大小写不敏感；不做子串、模糊或编辑距离匹配。

- 旧 COVERAGE_ONLY 220 条中消解 194 条，消解率 **88.18%**；剩余 26 条。
- 全 coverage token 429 条中消解 403 条，消解率 **93.94%**。
- 机制分解：exact=209，template_base=2，msvc_prefix=186，underscore=6。Lead 粗算的 186 对应本脚本的 MSVC 前缀链单规则结果；本卡另加下划线段（+6）与模板首段基名（+2），故权威可消解数为 194，不是 34 条未解析。

抽样 20 条（完整表见 `normalization.tsv`）：

| 原 token | 归一化后 | 命中 in-binary 名 | 是否合理 |
|---|---|---|---|
| AircraftClass | AircraftClass | AircraftClass | 是（exact）：原 token 已是 in-binary 裸名，未做扩展 |
| FileClass | FileClass | FileClass | 是（exact）：原 token 已是 in-binary 裸名，未做扩展 |
| AVAircraftClass | AircraftClass | AircraftClass | 是（msvc_prefix）：仅去 P/A/V 前缀链后即与完整裸名相等 |
| AVFootClass | FootClass | FootClass | 是（msvc_prefix）：仅去 P/A/V 前缀链后即与完整裸名相等 |
| AVTechnoClass | TechnoClass | TechnoClass | 是（msvc_prefix）：仅去 P/A/V 前缀链后即与完整裸名相等 |
| PAVBombClass | BombClass | BombClass | 是（msvc_prefix）：仅去 P/A/V 前缀链后即与完整裸名相等 |
| PAVInfantryClass | InfantryClass | InfantryClass | 是（msvc_prefix）：仅去 P/A/V 前缀链后即与完整裸名相等 |
| AVWWMouseClass | WWMouseClass | WWMouseClass | 是（msvc_prefix）：仅去 P/A/V 前缀链后即与完整裸名相等 |
| VAircraftTypeClass | AircraftTypeClass | AircraftTypeClass | 是（msvc_prefix）：仅去 P/A/V 前缀链后即与完整裸名相等 |
| VNeuronClass | NeuronClass | NeuronClass | 是（msvc_prefix）：仅去 P/A/V 前缀链后即与完整裸名相等 |
| PAVAbstractClass | AbstractClass | AbstractClass | 是（msvc_prefix）：仅去 P/A/V 前缀链后即与完整裸名相等 |
| RTacticalClass_RadarClass | RadarClass | RadarClass | 是（underscore）：下划线复合名取段，段本身是完整裸名 |
| INIEntry_INIClass | INIClass | INIClass | 是（underscore）：下划线复合名取段，段本身是完整裸名 |
| SelectClass_StripClass_SidebarClass | SidebarClass | SidebarClass | 是（underscore）：下划线复合名取段，段本身是完整裸名 |
| TacticalClass_DisplayClass | DisplayClass | DisplayClass | 是（underscore）：下划线复合名取段，段本身是完整裸名 |
| SBGadgetClass_SidebarClass | SidebarClass | SidebarClass | 是（underscore）：下划线复合名取段，段本身是完整裸名 |
| INISection_INIClass | INIClass | INIClass | 是（underscore）：下划线复合名取段，段本身是完整裸名 |
| DynamicVectorClass | DynamicVectorClass | ?$DynamicVectorClass@PAVTechnoClass@@ | 是（template_base）：首段基名命中模板实例 ?$DynamicVectorClass@PAVTechnoClass@@ |
| VectorClass | VectorClass | ?$VectorClass@USubzoneConnectionStruct@@ | 是（template_base）：首段基名命中模板实例 ?$VectorClass@USubzoneConnectionStruct@@ |
| AVCDFileClass | CDFileClass | CDFileClass | 是（msvc_prefix）：仅去 P/A/V 前缀链后即与完整裸名相等 |

## Q3 · 三桶重算（与旧数并列）

口径说明：`BOTH` / `COVERAGE_ONLY` 的分母是 coverage 侧 429 个不同 token；`RTTI_ONLY` 的分母是 in-binary 侧 988 个裸名条目。归一化后多对一会出现，因此三桶不再要求相加成同一个全集；另列 RTTI 条目侧覆盖数以避免误读。

| 桶 | 旧数 | 纠正后 | 变化 | 原因 |
|---|---:|---:|---:|---|
| BOTH | 209 | 403 | +194 | 旧 COVERAGE_ONLY 中 186 条 MSVC 前缀残片、6 条下划线复合名片段、2 条模板首段基名现在命中；精确命中仍 209 |
| COVERAGE_ONLY | 220 | 26 | -194 | 与上项镜像：220 - 194 = 26；未解析项见 Q4 |
| RTTI_ONLY | 779 | 383 | -396 | 200 个 `?$VectorClass@...` 与 196 个 `?$DynamicVectorClass@...` 因 coverage 的 VectorClass / DynamicVectorClass 命中首段基名而移出；前缀/分段剥离未新增直接裸名命中 |

- RTTI 条目侧交叉检查：覆盖 605（直接裸名 209 + 模板首段基名 396）+ RTTI_ONLY 383 = 988。
- 三桶全量见 `_stage4_reconcile.json`；未解析逐条见 `unresolved.tsv`。

## Q4 · 剩余未解析逐条归因

共 26 条。分布：(a) 无独立 vtable 的类 6，(d) 疑似命名差异/拼写差异 5，(b) 多重继承或嵌套导致的复合名片段 3，(c) 模板类 9，(e) 其它/无法判定 3。

| 名字 | coverage 行数 | 归因分类 | 依据 |
|---|---:|---|---|
| RulesClass | 37 | (a) 无独立 vtable 的类 | coverage L1042 entry=004355B0 name=ColorStruct::ColorStruct；候选键 RulesClass 与 in-binary RTTI 裸名/模板首段基名均无大小写不敏感等号命中；扫描节内无同名 TD，coverage 上下文为管理/静态/命名空间式入口且无 vt 槽见证；据此归为无独立 vtable 类 |
| MPGameModeClass | 36 | (d) 疑似命名差异/拼写差异 | coverage L6291 entry=005C0E90 name=MPGameModeClass::vt_entry_58；候选键 MPGameModeClass 与 in-binary RTTI 裸名/模板首段基名均无大小写不敏感等号命中；coverage 上下文活表见证写有 .?A[UV]MultiplayerBattle@@，对应 TD 0x82daa8；仅标疑似 |
| TacticalClass | 10 | (b) 多重继承或嵌套导致的复合名片段 | coverage L9589 entry=006D1FE0 name=TacticalClass::AdjustForZShapeMove；候选键 TacticalClass 与 in-binary RTTI 裸名/模板首段基名均无大小写不敏感等号命中；RTTI 存在嵌套复合形态 TacticalClass@DisplayClass@TD 0x820048，token 是其首段/前缀后片段 |
| VocClass | 7 | (c) 模板类 | coverage L92 entry=00405190 name=sub_00405190；候选键 VocClass\|ocClass 与 in-binary RTTI 裸名/模板首段基名均无大小写不敏感等号命中；仅见模板名实参内出现，TD ?$VectorClass@PAVVocClass@@ @0x8464c8、?$DynamicVectorClass@PAVVocClass@@ @0x8464f8 |
| VoxClass | 7 | (c) 模板类 | coverage L379 entry=0040F0A0 name=?$DynamicVectorClass::PAVVox::vslot2；候选键 VoxClass\|oxClass 与 in-binary RTTI 裸名/模板首段基名均无大小写不敏感等号命中；仅见模板名实参内出现，TD ?$VectorClass@PAVVoxClass@@ @0x846618、?$DynamicVectorClass@PAVVoxClass@@ @0x846648 |
| ScenarioClass | 5 | (a) 无独立 vtable 的类 | coverage L2674 entry=004AE4C0 name=ScenarioClass::UpdateCellLighting；候选键 ScenarioClass 与 in-binary RTTI 裸名/模板首段基名均无大小写不敏感等号命中；扫描节内无同名 TD，coverage 上下文为管理/静态/命名空间式入口且无 vt 槽见证；据此归为无独立 vtable 类 |
| IonBlastClass | 3 | (c) 模板类 | coverage L4986 entry=0053CB10 name=IonBlastClass::IonBlastClass；候选键 IonBlastClass 与 in-binary RTTI 裸名/模板首段基名均无大小写不敏感等号命中；仅见模板名实参内出现，TD ?$VectorClass@PAVIonBlastClass@@ @0x8280d0、?$DynamicVectorClass@PAVIonBlastClass@@ @0x828100 |
| LaserDrawClass | 3 | (c) 模板类 | coverage L5272 entry=0054FE60 name=LaserDrawClass::LaserDrawClass；候选键 LaserDrawClass 与 in-binary RTTI 裸名/模板首段基名均无大小写不敏感等号命中；仅见模板名实参内出现，TD ?$VectorClass@PAVLaserDrawClass@@ @0x8296e0、?$DynamicVectorClass@PAVLaserDrawClass@@ @0x829710 |
| InputManagerClass | 2 | (a) 无独立 vtable 的类 | coverage L5265 entry=0054F5C0 name=InputManagerClass::IsKeyPressed；候选键 InputManagerClass 与 in-binary RTTI 裸名/模板首段基名均无大小写不敏感等号命中；扫描节内无同名 TD，coverage 上下文为管理/静态/命名空间式入口且无 vt 槽见证；据此归为无独立 vtable 类 |
| PAVLaserDrawClass | 2 | (c) 模板类 | coverage L5286 entry=005514B0 name=T_DynamicVectorClass_PAVLaserDrawClass__::slot2；候选键 PAVLaserDrawClass\|AVLaserDrawClass\|VLaserDrawClass\|LaserDrawClass 与 in-binary RTTI 裸名/模板首段基名均无大小写不敏感等号命中；仅见模板名实参内出现，TD ?$VectorClass@PAVLaserDrawClass@@ @0x8296e0、?$DynamicVectorClass@PAVLaserDrawClass@@ @0x829710 |
| RadarEventClass | 2 | (c) 模板类 | coverage L8007 entry=0065B2F0 name=RadarEventClass::RadarEventClass；候选键 RadarEventClass 与 in-binary RTTI 裸名/模板首段基名均无大小写不敏感等号命中；仅见模板名实参内出现，TD ?$VectorClass@PAVRadarEventClass@@ @0x839920、?$DynamicVectorClass@PAVRadarEventClass@@ @0x839958 |
| SpotlightClass | 2 | (c) 模板类 | coverage L7197 entry=005FF250 name=SpotlightClass::SpotlightClass；候选键 SpotlightClass 与 in-binary RTTI 裸名/模板首段基名均无大小写不敏感等号命中；仅见模板名实参内出现，TD ?$VectorClass@PAVSpotLightClass@@ @0x8335e8、?$DynamicVectorClass@PAVSpotLightClass@@ @0x833618 |
| ABufferClass | 1 | (e) 其它/无法判定 | coverage L449 entry=00410CE0 name=ABufferClass::ABufferClass；候选键 ABufferClass\|BufferClass 与 in-binary RTTI 裸名/模板首段基名均无大小写不敏感等号命中；无模板实参/嵌套/替代 RTTI 名的表内证据，无法判定 |
| AVRTacticalClass | 1 | (b) 多重继承或嵌套导致的复合名片段 | coverage L7894 entry=006539D0 name=RTacticalClass_RadarClass::slot31；候选键 AVRTacticalClass\|VRTacticalClass\|RTacticalClass 与 in-binary RTTI 裸名/模板首段基名均无大小写不敏感等号命中；RTTI 存在嵌套复合形态 RTacticalClass@RadarClass@TD 0x839298，token 是其首段/前缀后片段 |
| CDDriveManagerClass | 1 | (a) 无独立 vtable 的类 | coverage L3410 entry=004E6070 name=CD::CDDriveManagerClass；候选键 CDDriveManagerClass 与 in-binary RTTI 裸名/模板首段基名均无大小写不敏感等号命中；扫描节内无同名 TD，coverage 上下文为管理/静态/命名空间式入口且无 vt 槽见证；据此归为无独立 vtable 类 |
| GameOptionsClass | 1 | (a) 无独立 vtable 的类 | coverage L7153 entry=005FB2E0 name=GameOptionsClass::GetAnimSpeed；候选键 GameOptionsClass 与 in-binary RTTI 裸名/模板首段基名均无大小写不敏感等号命中；扫描节内无同名 TD，coverage 上下文为管理/静态/命名空间式入口且无 vt 槽见证；据此归为无独立 vtable 类 |
| MessageListClass | 1 | (e) 其它/无法判定 | coverage L6651 entry=005D3BA0 name=MessageListClass::MessageListClass；候选键 MessageListClass 与 in-binary RTTI 裸名/模板首段基名均无大小写不敏感等号命中；无模板实参/嵌套/替代 RTTI 名的表内证据，无法判定 |
| MissionControlClass | 1 | (e) 其它/无法判定 | coverage L6126 entry=005B3700 name=MissionClass::MissionControlClass；候选键 MissionControlClass 与 in-binary RTTI 裸名/模板首段基名均无大小写不敏感等号命中；无模板实参/嵌套/替代 RTTI 名的表内证据，无法判定 |
| MPBattleClass | 1 | (d) 疑似命名差异/拼写差异 | coverage L6309 entry=005C0FE0 name=MPGameModeClass::MPBattleClass；候选键 MPBattleClass 与 in-binary RTTI 裸名/模板首段基名均无大小写不敏感等号命中；coverage 上下文活表见证写有 .?A[UV]MultiplayerBattle@@，对应 TD 0x82daa8；仅标疑似 |
| MPMegawealthClass | 1 | (d) 疑似命名差异/拼写差异 | coverage L6425 entry=005C9440 name=MPGameModeClass::MPMegawealthClass；候选键 MPMegawealthClass 与 in-binary RTTI 裸名/模板首段基名均无大小写不敏感等号命中；coverage 上下文活表见证写有 .?A[UV]Megawealth@@，对应 TD 0x82fce8；仅标疑似 |
| MPSiegeClass | 1 | (d) 疑似命名差异/拼写差异 | coverage L6442 entry=005CABD0 name=MPGameModeClass::MPSiegeClass；候选键 MPSiegeClass 与 in-binary RTTI 裸名/模板首段基名均无大小写不敏感等号命中；coverage 上下文活表见证写有 .?A[UV]MultiplayerSiege@@，对应 TD 0x82fec8；仅标疑似 |
| MPUnholyAllianceClass | 1 | (d) 疑似命名差异/拼写差异 | coverage L6454 entry=005CB540 name=MPGameModeClass::MPUnholyAllianceClass；候选键 MPUnholyAllianceClass 与 in-binary RTTI 裸名/模板首段基名均无大小写不敏感等号命中；coverage 上下文活表见证写有 .?A[UV]UnholyAlliance@@，对应 TD 0x830058；仅标疑似 |
| PBVAnimClass | 1 | (c) 模板类 | coverage L4982 entry=0053C6A0 name=T_DynamicVectorClass_PBVAnimClass__::slot2；候选键 PBVAnimClass\|BVAnimClass 与 in-binary RTTI 裸名/模板首段基名均无大小写不敏感等号命中；仅见模板名实参内出现，TD ?$VectorClass@PBVAnimClass@@ @0x827fd0、?$DynamicVectorClass@PBVAnimClass@@ @0x828000 |
| PlanningTokenClass | 1 | (c) 模板类 | coverage L7586 entry=00636310 name=PlanningTokenClass::Clear；候选键 PlanningTokenClass\|lanningTokenClass 与 in-binary RTTI 裸名/模板首段基名均无大小写不敏感等号命中；仅见模板名实参内出现，TD ?$VectorClass@PAVPlanningTokenClass@@ @0x836970、?$DynamicVectorClass@PAVPlanningTokenClass@@ @0x8369a8 |
| RTacticalClass | 1 | (b) 多重继承或嵌套导致的复合名片段 | coverage L7894 entry=006539D0 name=RTacticalClass_RadarClass::slot31；候选键 RTacticalClass 与 in-binary RTTI 裸名/模板首段基名均无大小写不敏感等号命中；RTTI 存在嵌套复合形态 RTacticalClass@RadarClass@TD 0x839298，token 是其首段/前缀后片段 |
| ZBufferClass | 1 | (a) 无独立 vtable 的类 | coverage L12283 entry=007BC970 name=Drawing::ZBufferClass；候选键 ZBufferClass 与 in-binary RTTI 裸名/模板首段基名均无大小写不敏感等号命中；扫描节内无同名 TD，coverage 上下文为管理/静态/命名空间式入口且无 vt 槽见证；据此归为无独立 vtable 类 |

限制声明：以上分类只说明“按本卡静态/表内证据，in-binary RTTI 里没有同名类”；**不是类名正确性判定**，不得反推 coverage 名字错误。

## 产物与复跑

- `REPORT.md`、`normalization.tsv`、`unresolved.tsv`、`work.py`；另有 rtti/coverage/context/stage 中间文件，均在本目录。
- `work.py` 纯静态只读输入，重跑会校验镜像 sha256 前缀并复核 coverage.tsv 未改。

未取得项：0。