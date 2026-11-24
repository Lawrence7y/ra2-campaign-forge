# gamemd.exe 子系统切分报告（glm_seg）

- 目标：`D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`（PE32，ImageBase 0x400000，只读，全程未写入）
- 分析基线：`function_atlas.tsv` **12,916 行**（2026-11-15 11:47 再生成版）。
  ⚠️ 任务书写的 8,578 是 11:12 旧快照；本次扫描时发现 atlas 已更新（旧集合是新集合的严格子集，已验证
  old ⊆ new，+4,338 个新函数）。本报告以 **12,916** 为准。
- 产物：`subsystems.tsv`、`function_assign.tsv`（12,916 行全量）、`evidence.json`、`assign_debug.json`、本报告。
- 复现脚本：`scan_evidence.py`（capstone 全量反汇编）→ `classify.py`（规则管线）。

## 1. 方法与证据管线

**证据采集**（scan_evidence.py，13s）：
- pefile `get_memory_mapped_image()`，索引 0 == ImageBase；`.text` 指针判据 0x00401000..0x007E038D；
  `.data` raw 字节校验到 0x0087E000（之后 BSS 不读）。
- capstone 5 `skipdata=True` + `detail=True`，逐函数（entry..entry+size）提取：
  **全部 IAT 导入引用**（MEM 操作数 disp ∈ IAT 槽位表，372 槽，1,001 个函数命中）与
  **静态调用边**（E8 rel32 / 尾调用 JMP，31,263 条）。
- 虚表槽重建：vtables_canonical.json 的 1,214 个 vt 地址逐槽读 4 字节指针（连续 .text 指针即槽），
  得到 665+ 函数 → 类归属（新旧 atlas 变化后以 evidence.json 重算为准）。

**归类管线**（classify.py，首中保护，prio 不允许低级覆盖高级）：

| 级 | 证据 | 函数数 | 置信 |
|---|---|---|---|
| P0a | assert `__FILE__` 路径字符串 / module_attribution → 西木源文件表 | 396 | 高 |
| P1 | 虚表槽 → 类名规则（容器模板/文件流/网络接口/对象类/*TypeClass…） | 5,630 | 高 |
| P2 | 导入指纹（DDRAW/Bink/WSOCK32/DSOUND/Reg\*/文件 API/ole32；CRT 区间除外） | 90 | 高/中 |
| P3 | 字符串规则（有序首中，52 条）+ CRT 区间(≥0x7C8900) + 10 个区间种子 | 1,299+538 | 高/中/低 |
| P4 | 调用图传播 4 轮：已归类邻边 ≥70% 多数（排除 CRT/UNASS 票） | 1,246 | 中 |
| P5 | 地址簇填充（gap≥512 切簇，dom≥0.75 且多数≥5，排除 CRT 票） | 1,519 | 低/中 |

纪律执行：地址邻近**从不单独**定类（P5 只在簇内已有多数强证据时填充，标注低/中）；
未匹配一律 UNASSIGNED（2,736 函数 / 552,687 字节，见 §5）。

## 2. 覆盖率

| 指标 | 数值 |
|---|---|
| 函数覆盖 | **10,180 / 12,916 = 78.8%** |
| 字节覆盖（函数体合计口径） | **2,673,158 / 3,225,845 = 82.9%** |
| 置信分布 | 高 6,696 / 中 2,831 / 低 653 |
| UNASSIGNED | 2,736 函数 / 552,687 字节（17.1% 字节） |

`subsystems.tsv` 的 confidence 列是该子系统内出现的**最高档**；逐档分布如下（高/中/低）：
GameObj 1392/159/1309、Misc 1783/134/162、Audio 19/293/36、MP 66/228/14、WOL 112/161/13、
Scenario 182/55/49、Ini_Rules 363/21/136、Sidebar 62/16/74、Video 46/33/57、Net 230/86/6、
Movement 412/28/29、Graphics 444/68/0、其余见 assign_debug.json。

## 3. 子系统边界证据（逐个）

**Main_Init_Flow**（191 函数）— 模块直证：`Init.cpp`@0052D9A0/0052F3F0（RA2MD.INI、PortBase、RENEGADE.BIK）、
`Startup.CPP`、`MainLoop.CPP`；0x532100 区 `SYSTEM MEMORY;CPU: %d Mhz;VRAM reported`（硬件自检）。
**Menus_Main_Intro**（12）— `Credits.CPP`@004A2370、`Egos.CPP`@004C3E30、`ownrdraw.cpp`（STT:MainButton*）、
菜单背景 `dbak6440.pcx;gdii.pcx;nodi.pcx;rani.pcx;usai.pcx;japi.pcx`。
**Render_DDraw_Display**（54）— `DDRAW.DLL Error code = %08X`@0x49A2xx 区、DirectDrawCreate 调用点、
Display.CPP 模块簇 0x4A71A0（Theater/IsoMapPack 渲染侧）。
**Graphics_Blit_Shape**（512）— P1 虚表 444：`?$BlitTransLucent*` 模板族、LightConvertClass、BSurface、
AlphaShapeClass；`.SHP/.SHA/.PCX` 字符串（0x47A920 FOG.SHP/SHROUD.SHP、0x4B6440 Dropship SHP 组）。
**Video_Bink**（136）— binkw32 导入 9 函数、`BinkSetSoundSystem`、0x7BD690 自封闭播放辅助（被 Bink 路径 20 边调用）、
`RENEGADE.BIK`、`BeginMovie/EndMovie/subtitlemd.txt`、`%s.VQA`。
**Audio_Sound_Music**（348）— 引擎区种子 0x403ED0-0x409E00（`Audio Stream`、`AUDIOMD.MIX`、优先级
LOWEST/AMBIENT/VIOLENT）、DSOUND 导入、0x74D450（Invalid Voc/VERSION.TXT/Volume）、语音区
0x752290（`EVA Stream;Taunt Stream;taunts\tauam%02i.wav`）、主题区 0x720590（`Themes;Music Stream;No theme`）。
**Text_Language_Table**（22）— 0x734120-0x735180 种子：`***FATAL*** String Manager failed to initilaized`、
`MISSING:'%hs'`、0x734E60 入度 1,073（查表原语）。
**File_Mix_FS**（126）— 虚表 CCFileClass/CDFileClass/RawFileClass/BufferIOFileClass@0x8263344 等、
KERNEL32 文件 API（FindFirstFile/CreateFile/SetFilePointer）、`.MIX` 字符串（LOADMD.MIX/新 MIX 名）。
**File_Stream_Crypto**（67）— Straw/Pipe 族虚表：Base64Straw/Pipe@0x8263548 邻域、BlowStraw、LCWStraw、
LZOStraw、PKStraw、SHAPipe、RandomStraw（RA2 存档/网络加密流层）。
**Config_Registry**（12）— ADVAPI32 Reg\*（RegOpenKeyExA/RegQueryValueExA/RegCloseKey）@0049F8B0、0x5175F0、0x5BB580。
**Net_Transport**（322）— 虚表 IPXManagerClass/NullModemClass/WinsockInterfaceClass/UDPInterfaceClass/ConnectionClass；
WSOCK32 导入；0x5400D0（`Multicast;Rtry delta: %d;FSPS`）、0x5D7570（`FirewallSettings;mangler1.westwood.com`）、
`Packet Loss Simulation`、`%d.%d.%d.%d`、`SYNC%01d_%03d.TXT`、`Ra2ts_s/Ra2ts_l`（握手密钥）、
ModemHst/Gst、SendFile.CPP@0x692290。
**MP_Lobby_Session**（308）— 模块 Multiplayer/Session/netshare/netdlg2/MPLayer/MPCoop/Skirmish 等 64 函数；
0x505180-0x510A20 会话初始化种子（`<Player @ A>`、`GAPLUG`、`Forcing House %`）、`@Open@/@Closed@/@EasyAI@`、
`MinPlayers/MaxPlayers/[Digest]`、`ObserverMode/Preview.bin`、MAPSELMD.INI、GetDlgItem/SendDlgItemMessageA 簇。
**WOL_Online**（286）— wonline.cpp@0x77CF40-0x7A30F7（TXT_CANT_CONNECT/WOL:Buddy*/ob_41_）、
WOLPersonaInformation（wolinfoMD.ini/AutoLogin）、ole32 COM（CoCreateInstance×14@0x413D20 等）、
`SOFTWARE\Westwood\WOLAPI`@0x512680、CLSID\WW.TiberianSun@0x6BAC40、`HTMLPath/BadPage.htm`@0x773500、
WOLAPI 选项（AllowPage/LangFilter/LobMusic）。
**WDT_WorldDom**（24）— WorldDom.cpp（WDT.MIX/TheaterChoice%sMenu）、WDTSel（WDT:TerritorySelectToolTip）、
WDTHist.ini@0x764B90。
**UI_Gadget_Dialog**（327）— 虚表 Gadget/Control/Dialog/Gauge/List/Edit 族 268 个；`ToolTip`、
Win32 控件封装（ScrollBar/ListBox/ComboBox/msctls_trackbar32@0x60F4B0）、GameDlg/Options/ToolTip 模块。
**Input_Commands_Mouse**（104）— MouseClass 虚表@0x40D270、wwmous.cpp 模块簇 0x7B4170/0x7BA090、
`MOUSE.SHA`@0x560BF0、KEYBOARDMD.INI、UICmnds.cpp 命令入口。
**Sidebar_Radar_HUD**（152）— Radar.CPP@0x653F50（TXT_KILLS_COLON/TXT_NAME_COLON）、Sidebar.CPP@0x6A4DC0
（SELL.SHP/GCLOCK2.SHP/DARKEN.SHP）、生产队列 Queue.CPP（TXT_QUEUE_FULL）、`Cost: %d/Cost: N/A`@0x4B69B0、
EVA_ConstructionComplete/Canceled/OnHold 簇 0x6A8B30。
**Tactical_MapView**（22）— TacticalClass@DisplayClass 虚表@0x4AAC10、`shroud` 断言串
（`We tried to reset the shroud without an owner`@0x577AB0）、Tactical.CPP。
**GameObj_Logic**（2,860）— P1 虚表 1,380：Object/Techno/Unit/Infantry/Building/Aircraft/Foot/Cell/Anim/
Overlay/Smudge/Terrain/Tiberium/Wave/Tube/Bullet/Factory/Radio/Particle/Locomotion 外的全部运行时对象类；
Conquer.CPP/House.CPP/Unit.CPP/Infantry.CPP/Beacon.CPP 模块；EVA_*（低置信规则）。
**Ini_Rules_DB**（520）— AbsType.cpp@0x410960、AbstractTypeClass 虚表；规则解析巨簇 0x658330-0x67C6DE
（Countries/ColorAdd/LANGRULE.INI）与 0x664D20（InfantryTypes/VehicleTypes/Animations/Particles）、
0x41A160（AITriggerTypes/Aircraft/LROTOR.SHP）、INI 关键词族（UIName/Prerequisite/LandTargeting/ElevationModel）。
**AI_Team_Script**（314）— TeamClass/TeamTypeClass/TaskForceClass/ScriptClass/AITriggerTypeClass/NeuronClass
虚表；PlanMgr.cpp@0x6339B0/0x639740（MSG:PostTerminatingCommand/AlliedLoad/SovietLoad）；ScriptTypes@0x690EF0。
**Movement_Locomotion**（469）— LocomotionClass 族虚表 412：DriveLocomotionClass@0x4AF610、
Fly/Hover/Mech/Rocket/Tunnel、WaypointPathClass；0x4AF540 簇 dom 50/63。
**Scenario_Map**（286）— Scenario.CPP@0x67CEF0、MapGen.cpp@0x593030/0x596300、MapSel 簇、
`IsoMapPack/OverlayPack/CellTags/Theater`、Trigger/Tag/TEvent/TAction 虚表、
0x7258D0（Triggers/Tubes/Volatile/Semi-persistant）。
**SaveLoad**（16）— LoadDlg.CPP@0x552A40（\*.%3s/loadmd.MIX/LOAD.MIX）、LdPrgMgr.cpp、`coopsave.ini`、Restate.cpp。
**Superweapon_Special**（7）— Ion.cpp@0x539760（TXT_LIGHTNING_STORM/EVA_LightningStormCreated）、
Super.CPP、`MultiMissile/IronCurtain/PsychicDominator`。
**Campaign_Meta**（66）— CampaignClass 虚表@0x46CCD0、CampScor.cpp（FinalMovie/Scenario/Battles）、
MPScore.cpp（TXT_TIME_FORMAT_HOURS/Winner）、Dropship.cpp（LOADOUT.SHP/DROPSHIP.PAL）。
**Misc_Util_Mem**（2,079）— 容器模板实例化虚表 1,783（DynamicVectorClass\<T\>/VectorClass/StackClass 等，
全镜像散布）、0x40B640 区分配器、0x7C5BC0-0x7C8900 原语区（0x7C5F00 入度 543）。
**Crt_Runtime**（538）— 区域规则 ≥0x7C8900：`LC_COLLATE/LC_CTYPE`、`1#SNAN`、`typeid of NUL`、
`Sunday;Monday`、`user32.dll;MessageBoxA`（0x7C8962-0x7E038D）。

## 4. 冲突与处理

1. **`.PCX` 双重身份**（菜单背景 vs 图形解码）：dbak/gdii/nodi 等 8 个具体文件名规则排在通用 `.PCX` 之前。
2. **`.MIX` 双重身份**（文件层 vs 音频包）：`AUDIOMD.MIX/AUDIO.MIX/SOUNDS.MIX` 音频规则先于通用 `.MIX`。
3. **GameObj_Logic 的 1,309 个低/中置信级联**（P4 878 + P5 572）：对象逻辑确实是最大子系统，但下游若要
   精修，应从这 1,309 个函数开始用调用图人工复核。
4. **Misc_Util_Mem 是模板实例化集合**：DynamicVectorClass\<T\> 对每个 T 生成 dtor/FreeAll，语义正确但
   地址上不构成连续子系统——报告中按"横切层"理解。
5. **CRT 边界**：0x7C5BC0-0x7C8900（543 入度 memset 原语区）归 Misc_Util_Mem；0x7C8900 之后归 Crt_Runtime。
   判据：字符串指纹 + 入度 + 无导入，两者互斥无缝。
6. **atlas 版本漂移**：分析中途 function_atlas.tsv 从 8,578 → 12,916（11:47 再生成）。已用当前版重扫证据
   （evidence.json 与 atlas 行数断言一致），三个交付物均基于 12,916。

## 5. UNASSIGNED 残余（2,736 函数 / 552,687 字节）

最大残余簇：0x7291F0 UICmnds 内部（部分已归 Input）、0x664D20 规则解析尾部、0x7AC500-0x7AEFF8、
0x620F60-0x6278BF（83 函数无字符串）、0x6BB8E0-0x6C663A（83 个微函数，WOL COM 邻域）、0x730970、
0x69A1F0、0x7B57A0（格式化辅助，种子只吸收部分）。共同特征：无字符串/无导入/虚表外，
P4 投票分裂（被多个子系统调用）——按纪律 6 不强行赋类。

## 6. 最不确定的 3 个子系统

1. **Menus_Main_Intro（12 函数）**：主菜单/开场流程大半被 `.PCX`/`.SHP` 规则吸进 Graphics_Blit_Shape，
   只剩模块直证的 12 个函数；实际规模被低估，与 Graphics/UI 的边界最不可信。
2. **Tactical_MapView（22 函数）**：TacticalClass 虚表直证仅 15 个；战术视图的滚动/选择/绘制逻辑混在
   Graphics 与 GameObj 的簇填充里，0x56B3F0-0x587C4D 109KB 巨簇只吸收了 22 个。
3. **SaveLoad（16 函数）**：只有 LoadDlg/LdPrgMgr 的 9 个模块直证；RA2 存档的序列化核心分散在
   File_Stream_Crypto（BlowStraw）与 Scenario_Map，本类边界不闭合。

（次级关注：Audio_Sound_Music 293/348 来自区间种子、Render_DDraw_Display 46/54 来自 P5 簇。）

## 7. 交付文件

- `glm_seg\subsystems.tsv` — 28 个子系统 × (函数数/字节/地址区间/证据/置信)
- `glm_seg\function_assign.tsv` — 12,916 行逐函数（entry/subsystem/evidence_kind/confidence）
- `glm_seg\scan_evidence.py` + `classify.py` + `evidence.json` + `assign_debug.json` — 复现链
