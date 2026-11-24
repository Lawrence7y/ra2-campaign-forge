# UNKNOWNS.md — S10-K2 未证项清单

| # | 项 | 现状 | 补证路径 |
|---|---|---|---|
| 1 | `+0xCC` 另一侧（读点） | 已入账 2 写/0 读；全 .text 广扫 109 个 dword `[reg+0xCC]` 读点全在无关类（`0x409A5D`,`0x41E68C`,`0x4220BB`…），无 MissionClass 归属 | 需要能确证 `this` 为 MissionClass 对象的调用者上下文；跨类偏移禁止套用 |
| 2 | `+0x6C` 另一侧（写点） | 已入账 0 写/1 读（`0x5B30A7` MissionClass::AI）；广扫 80 个 dword 写点在无关类 ctor（`0x5F3919` ObjectClass 等）；`0x74431F` 同类读点在 UnitClass 派生方法，严格"同类双支撑"不足 | 找到 MissionClass 自身方法内的写点，或用 RTTI/调用图证明读写同一对象 |
| 3 | `+0xB8` 读点归属 | `0x74431F`（UnitClass::slot128）有 mission 上下文的字节读，但在派生类而非 MissionClass 自身方法 ⇒ 记候选未升 [已证] | 异族审计裁定是否接受派生类同对象读点 |
| 4 | 6 个全桩槽为何"全桩" | 已落地地址（v129/130/131/141/142/154 = `0x5B2E10`/20/30/`ED0`/`EE0`/`FA0`），但引擎为何不给任何类实现（设计层面）未证 | YRpp 源码若可得；或真机观察这些 Mission 从不派发 |
| 5 | 若干派生大 vtable 的精确表尾 | Foot/Infantry/Aircraft/Building/Techno/Unit 的 code-cont 达 309..344 槽（capstone maxn=400 上界内），真实表尾 COL/SEP 未逐一定界（不影响 v129..v156 结论） | 提高 maxn 并对表尾做 COL/SEP/非 code 三重确认 |
| 6 | `ret 0xC` 基线定义差 | 本卡全 .text 指令级 `ret 0xC` = 1651；§969 记 672；本卡未用该判据定任何结论 | 需查 §969 的 672 的确切范围/形态（可能限 vtable 函数或特定段） |
| 7 | S10 真机验证 | 本卡静态 K 卡，未申请真机；派发/槽/GetSize/字段皆可静态定 | L 卡真机注入地图/AI 状态验证"某帧派发哪个 Mission" |
| 8 | 跨子系统 delta 归属 | 37 条 delta 中 22 条 entry 现分属 S05(13)/S12(8)/S08(1)，本卡按派卡格式标 subsystem=S10 | 合并员按 entry 升级 grade 即可；是否改 subsystem 由 Lead 裁决 |
