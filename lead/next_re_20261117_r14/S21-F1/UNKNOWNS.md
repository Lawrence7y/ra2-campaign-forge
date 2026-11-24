# S21-F1 UNKNOWNS

| ID | 未知项 | 现状 | 需补取证 | 分级 |
|---|---|---|---|---|
| U1 | 「本关胜利/失败」判定条件的精确读点 | S15 已证 TEventClass::HasOccured 0x71E940 两表派发，TAction 触发胜负；但哪个 TAction ID 写结局状态、读到哪个全局未定位 | 从 TAction 胜利/失败槽（kb/10_map_triggers §2 145 项动作）反查写点；追 `0x470D30` 前置 `0x622B50` 返回值语义 | [未证] |
| U2 | 结局函数入口 +「关卡结束→弹结算」过渡边 | 候选区 0x470D30（CampScor.cpp 消息分发），但 `EndOfGame`@0x83E138 / `NextScenario`@0x83E18F 绝对 xref=0（实际走 `[reg+off]`，纪律 19） | 全 .text 扫 `mov reg,0x83E138` 等立即数载入基址 + `[reg+off]`；追 `0x7E1474`/`0x7E14A8`/`0x7E14A4` 三个间接调用目标 | [未证] |
| U3 | 战役选择 → MapSeedClass::LoadMission 0x597A30 的直连边 | 0x597A30/0x597760/0x597D50/0x597D60 全镜像直接 call 0 命中（经 vtable 或其它入口）；选中槽 0xA8F7A8 到 `Scenario=@+0x9C` 的路径未闭合 | 扫 `call [reg+off]` 中目标落在 0x597xxx 的间接调用；查 0xA8F7A8→CampaignClass+0x9C 的读取点 | [未证] |
| U4 | 结算界面绘制入口函数 | ScorePrintClass/ScoreTimeClass vtable 已定位（0x808DA0/0x808D70，TD 0x83E2D0/0x83E2F0），但绘制入口归属未展开（本卡范围外） | 从 vtable 槽值反查调用者；S09 UI 卡联动 | [未证] |
| U5 | 战役进度是否入档（S17 接口方向） | CampaignClass::slot13 0x46CFC0 序列化 +0x98/+0x9C/+0x29C（write），slot25 读回；但这是战役**定义**对象序列化，非「玩家通关进度」 | 查存档 .SAV 里是否写 CampaignClass 下标（0xA8F7A8 或 FindIndex 结果）；联 S17-F1 | [未证] |
| U6 | S21 ↔ S14 AI 接口 | 仅见 0x46D430 检查 8 个对象完成态（0x5E93F0），方向与语义未定 | 追 0xA8DA90..0xA8DAB0 这 8 个对象类型与 HouseClass 关系 | [未证] |
| U7 | Base Load 0x410A60 读 Name/UIName 的段来源 | 用 `&this+0x24`（战役名）作段名，但标准 BATTLEMD 段（如 [SOV1]）无 Name/UIName 键——该基类可能同时服务别的 INI | 追 0x526810 段查找返回结构，确认是否另有默认段 | [静态推断] |

## 方法论保留
- 0x52F260 在 atlas 空洞内：按纪律 17，未用 `entry_at_or_before` 强行归属函数；仅记调用点 VA。
- 字段偏移→语义只 +0x24 有本类写+读双支撑；其余标 [静态推断]（纪律 4）。
- 类名全部来自 TD，未用头文件/前向声明推断（纪律 5 / 错源 ④）。
