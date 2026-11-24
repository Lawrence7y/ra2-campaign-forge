# S21-F1 PROGRESS — 战役流程数据流

卡号 S21-F1｜静态卡（未跑真机）｜目标 gamemd.exe SHA-256 `73201CC0…F67476`｜写域 `S21-F1\`、`_ghidra\S21-F1\`

## 结论表

| # | 结论 | 分级 | 证据路径 |
|---|---|---|---|
| T1-1 | `BATTLEMD*.INI` 通配枚举 @0x52CB90，FindFirstFileA/NextFileA，到达序无排序；无散装回退 0x526198 "BATTLEMD.INI" | [已证] | `EVIDENCE/FLOW_EVIDENCE.md#§A1` |
| T1-2 | `[Battles]` 归并 = `CampaignClass::CreateFromINIList 0x46CE10`；判重键 `CampaignClass+0x24` 用 `_stricmp` | [已证] | `EVIDENCE/FLOW_EVIDENCE.md#§A2` |
| T1-3 | 战役段读取函数 = slot25 `0x46CCD0`；5 键 CD/FinalMovie/Scenario/DebugOnly/Description + 基类 2 键 Name/UIName | [已证] | `EVIDENCE/FLOW_EVIDENCE.md#§A3/§A4` |
| T1-4 | CampaignClass 类名 RTTI 实测 `.?AVCampaignClass@@`；GetSize=0x3A0 双证（v[12]@0x46D070 + new@0x46CE97） | [已证] | `EVIDENCE/FLOW_EVIDENCE.md#§A5` |
| T1-5 | 字段 +0x24/0x3D/0x60/0x64/0x98/0x9C/0x29C/0x2A0 写入点定位；仅 +0x24 有写+读双支撑，其余语义 [静态推断] | [静态推断] | `EVIDENCE/FLOW_EVIDENCE.md#§A5` |
| T1-6 | `CampaignClass::FindIndex 0x46CC90` name→index；唯一调用点 0x52F260（位于 atlas 空洞） | [已证] | `EVIDENCE/FLOW_EVIDENCE.md#§A6` |
| T2-1 | 战役名→关卡序号的 UI 桥：0x52F260 `call FindIndex` → 写 UI 槽 `[edi]`；选中槽全局 0xA8F7A8（20 refs） | [已证]+[静态推断] | `EVIDENCE/FLOW_EVIDENCE.md#§B1` |
| T2-2 | 关卡载入：`Scenario=@+0x9C`→MapSeedClass::LoadMission 0x597A30；直连边未定位 | [未证] | `EVIDENCE/FLOW_EVIDENCE.md#§B2` |
| T3-1 | S15 触发器/事件已入账（TEventClass::HasOccured 0x71E940 两表派发），本卡复用不重做 | [已证]（S15） | `EVIDENCE/FLOW_EVIDENCE.md#§C`（引 kb/10_map_triggers §3） |
| T3-2 | 结局判定/消息分发候选函数 0x470D30（CampScor.cpp），EndOfGame/NextScenario 字符串在镜像但绝对 xref 0 | [静态推断] | `EVIDENCE/FLOW_EVIDENCE.md#§C` |
| T3-3 | 判定条件精确读点 + 结局函数入口 + 「关卡结束→结算」过渡边 | [未证] | `UNKNOWNS.md#U1/U2` |
| T4-1 | CampaignScoreClass / CampaignEndScoreClass 类名 RTTI 实测；vtable 0x7E4AAC / 0x7E4AB8 | [已证] | `EVIDENCE/FLOW_EVIDENCE.md#§D1` |
| T4-2 | 构造/析构 0x46D330/0x46D350/0x471500/0x471520；时间格式化 0x46D360/0x470C90 | [已证] | `EVIDENCE/FLOW_EVIDENCE.md#§D2` |
| T4-3 | 得分数据：全局 0x89E000(8项)、浮点 0x89E120/0x89E170/0x89E158 累加/读取 | [静态推断] | `EVIDENCE/FLOW_EVIDENCE.md#§D3` |
| T4-4 | 结算界面绘制入口函数归属 | [未证] | `UNKNOWNS.md#U4` |
| T5 | 4 条接口（S15/S17/S09/S14）见 §E；S09、S15 有调用点，S17 序列化有字节，S14 未定位 | [已证]/[静态推断]/[未证] | `EVIDENCE/FLOW_EVIDENCE.md#§E` |

链上跳数：配置→选择 9 跳有明确调用点；全链 16 跳（[已证] 10 / [静态推断] 4 / [未证] 2）。见 `FLOW.md`。

## 给审计员的 3 个核心数字（可独立复算）

1. **CampaignClass GetSize = 0x3A0（930 B）**。复算：① `python work/ra2.py 46D070 10` → `mov eax,0x3a0; ret`；② `python work/ra2.py 46CE90 20` → `push 0x3a0; call 0x7c8e17`(new)。两处立即数独立对上（纪律：GetSize 双向核对）。
2. **战役段键名数 = 5（本类 slot25）+ 2（基类 Load）= 7**。复算：`python work/keys1.py`，看 slot25 引用串地址 0x81B1D4/1C8/1BC/1B0/1A4 与 0x410A60 引用 0x817854/0x81784C；均带读取调用点，非凭印象。
3. **配置→选择子链 9 跳有调用点**：0x685609 / 0x52CBA0 / 0x52CC67 / 0x46CE97 / 0x46CF65 / 0x46CCEB / 0x46CE77 / 0x46CCAC / 0x52F260。复算：`python work/callers1.py` + `work/chain1.py`，逐跳 VA 在 `FLOW.md` 表内。

## 基线（纪律 1，写 N/N 前先测；本卡未写任何 N/N 通过断言）
三次实证基线 36.5% / 6.91% / 86.0%（R14_COMMON §8.2④），本卡数字均注明分母与来源，不以「全 True / N/N」作证据。

## 状态
- 未写 `COVERAGE\coverage.tsv`、未改游戏文件、未 git commit/push。新增 `coverage_delta.tsv`（12 条；11 条升级为 [已证] + 1 条新增 0x410A60）。
- 未借用 atlas 边界反推虚表；类名全走 RTTI TD；capstone 全程 skipdata=True（全 .text 1,394,120 指令）。
