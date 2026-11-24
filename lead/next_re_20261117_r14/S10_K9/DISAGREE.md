# S10-K9 DISAGREE
1. 卡面 named_L=511/526 与现场 name 列复算 513/526 不一致。派卡同时要求“现场读盘复算基线（统一大小写、只读第 5 列）”，而 grade 第 5 列 107/526 与卡面完全一致；因此仅记录 named 差异，不把 named 当作 grade 基线不符而停机。当前 PANEL.md 的 S10 named=513 也支持现场值。
2. K6/K8F 已穷举 QueueMission +0x1E8 家族；本卡没有重挖该家族，也不宣称推翻其结论。5 行均基于 InfantryClass 主虚表 +0x558 mission-state setter（0051D6F0）及 +0x500/+0x3C8/+0x53C 状态机，属于不同行为面。
3. 0051D6F0 的 0x21 等状态值不应被硬套入 YRpp Mission 枚举；delta 名称/语义只陈述字节证据（写字段、调用者实参、被调写回），未伪造源码名。
4. 未采纳任何仅凭 vftable 槽归属的 [已证] 行；RTTI/虚表链只用于类属和 entry 定位，满足第 ⑬ 类错源约束。
