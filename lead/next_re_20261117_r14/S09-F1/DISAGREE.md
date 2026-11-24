# S09-F1 DISAGREE（与线索文档冲突，全部以本卡实测为准）

| # | 线索说法 | 本卡实测 | 裁断 |
|---|---|---|---|
| 1 | `sidebar_selection_ui.md`/`ui_command_dispatch_deep_dive.md`：注册 WndProc = `InputManagerClass::WndProc 0x54F790` | `RegisterClassA @0x777CA5` 的 WNDCLASS.lpfnWndProc=`0x7775C0`；`0x54F790` 是其下游（`call @0x7779CB`, ecx=[0x87F770]） | **线索不精确**：顶层 WndProc 是 `0x7775C0`，`0x54F790` 是 InputManager 子过程；两者都保留在链上 |
| 2 | 线索：单选路径 `ProcessClickCoords 0x692300`→`DecideAction 0x692610`→`LMBUp 0x4AB9B0` | 实测 `0x6930A0` 内 `0x692300(@0x69325E)`、`0x692610(@0x693271)`、`0x4AB9B0(@0x69328B)` 三者是**并列调用**（同属 `0x6930A0`），不是 300→610→9B0 串接 | **线索错**：三者是兄弟调用，非串行；已按实测定序 |
| 3 | 线索：框选过滤 `obj->v[78]`(可选)/`v[83]`(Select)/`0x732D00`=“已在选中组” | 实测 `0x6DA5C0` 用 `call [vft+0x2C]`(WhatAmI)、`[vft+0x138]`、`[vft+0x14C]`；`0x732D00` 只是 6B `mov al,[0xB0FE65]; ret`（全局字节） | **线索错**：虚表槽号与 0x732D00 语义均需更正；以 E10 为准 |
| 4 | 线索：`0x6DA5C0` 框选源数组 `[0xB0CEC8]` 条数 = `Tactical+0xDB0` | 完全吻合：`mov edi,0xb0cec8`、`mov eax,[ebp+0xdb0]`、`add edi,0xc`（12B 步长） | **一致**（保留，E10） |
| 5 | 线索：Cameo 绘制 `0x6A9540` 每帧全量；电力雷达 `0x63FB20` 每帧 | 实测 `0x6A9540` 入口 `tab+0x1C/0x3C` 双门（AllowedToDraw/NeedsRedraw），脏时才画 | **线索部分不确**：Cameo 有脏门，非每帧全量；本卡只取绘制入口，性能定性引用 R14_COMMON |
| 6 | 线索：Cameo 点击 `0x6AAD00` 生产事件唯一源 `0x4C6970` | 实测 `0x4C6970` 共 **9** 直调点（7@`0x6AAD00`+2@`0x6AA600`）；`0x6AAD00` 内 `cmp ebp,0x1F` 走超武分支（非 GetTechnoType） | **一致 + 精确化**（E08/E09） |
| 7 | 线索：`ui_command_dispatch_deep_dive.md`：基类 `CommandClass v[8]=0x4C9150` 抽象桩 | 实测 vtable `0x7EBE3C` v[8]=`0x4C9150` | **一致**（E09） |
| 8 | 卡正文候选假设「侧栏映射表 300 项」 | 实测每条 Tab `cmp count,0x4B`(75)，4 Tab，合计 300；Tab stride `0xF94` | **坐实但须标注口径**：核心数字报 75/条 Tab（4×75=300 总量），见 PROGRESS #2 |
| 9 | 卡正文候选「`+0xE4` 超武 SidebarImage 字段」 | 依 S16-K1 审计，`+0xE4` 是 `SidebarImage` 字符串 NUL 终结符，不是独立字段 | **回避**：本卡未把 `+0xE4` 当字段（纪律） |
