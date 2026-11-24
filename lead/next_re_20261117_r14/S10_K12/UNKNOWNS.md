# S10-K12 UNKNOWNS
- 现场 coverage.tsv 在 K9 读盘（05:01:54/9EF239C2…EC94，proved 107）与本卡读盘（05:58:20/314E19BC…A349FA0，proved 109）之间被外部并发并表改写；本卡只记录现场值 109/526，不追改账，也未写台账。
- K9 卡面 named_L=511 与当前 name 列复算 513/526 不符（PANEL 亦记 513）；本卡只按派卡口径用第 5 列做 grade 基线，named 仅作模拟附记。
- 0051BAB0 的环③ caller 004DAEF3 接收者 `ecx=[[esi+0x694]+0x69C]` 是二跳子对象，类未钉死；slot0x5C 129 处调用中无 Infantry 外部点。本行退 [静态推断]，未声称缺任一外部证据即可重闭。
- 005B3A00 返回 `0xA8E3A8 + ([ecx+0xAC]<<5)`（32B 表项地址），返回地址在行5 未再使用；台账 S12/[未证]/sub_。该调用不构成析构语义，本卡不把它计入环④。
- 外部已证被调中 004D55C0 StopMoving、0041BEA0 GetMapCoords、005657A0 TryGetCellAt 的 coverage conflict=1；grade 第 5 列仍为 [已证]，本卡按派卡口径只读第 5 列，conflict 状态如实附记。
- RTTI vt-8=0x7EB050=0x410230 是函数指针（本卡未进一步钉死其源码名）；COL 只在 vt-4=0x7EB054。K9 的 vt-8 读法已撤回。
- +0x6C4/+0x6DB/+0x6DC/+0x68D/+0x68E/+0x2A8/+0x5E0/+0x6E4 均为字节级偏移描述，不冒充 YRpp 官方字段名；状态值 0x1F/0x21 超出 Mission 0..31 的部分不命名为枚举成员。
- 未采用任何仅凭 vftable 槽归属的 [已证]；槽只用于定位 entry/被调目标，语义由字段写、真实 caller 实参、已证被调三方独立闭合。