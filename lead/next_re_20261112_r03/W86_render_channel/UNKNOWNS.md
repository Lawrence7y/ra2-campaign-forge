# UNKNOWNS · W86

| # | 未知项 | 当前等级 | 如何闭合 |
|---|---|---|---|
| U1 | `[0x100594EC]` 键名语义 | 已证为 "vsync"（字符串 VA 0x100482A0 实测内容），ini L35 `vsync=false` → 走 timeGetTime+Sleep 支路 | 已闭合 |
| U2 | 三处 `[0x1005F120]` 写入点（0x1001B01A/0x1001CD51/0x1001D2D2）哪条对应 d3d9 renderer；写入发生在 present 前还是后 | `[静态推断-中]` | 真机：放行节奏对照 D3D9 ETW EventID1 时间轴即可一锤定音 |
| U3 | 门闸 `sub_10006AE0` 属于 Blt/Flip/BltFast 哪个 COM vtable 实现 | `[未证]`（线性 sweep 失步导致 caller 搜索不可靠） | 真机栈采样，或修好 sweep 后分段重扫 |
| U4 | 当前 `windowed=false`+`fullscreen=false` 下 D3D9 交换链是独占全屏还是窗口化（DWM 是否参与） | `[未证]` | ETW 试采：DxgKrnl 184/1068 是否出现即见分晓 |
| U5 | D3D9 ETW 事件头 PID 归属、缓冲丢失率在本机的实测值 | `[静态推断-中]` / `[未证]` | 裁决三问试采（exp_etw_short.cmd） |
| U6 | `sub_1001EF70`（maxfps getter）中 `0x1004729C`/`0x10048688` 两个字符串常量的确切内容（推断为段名模板/ddraw 段名） | `[静态推断]` | 一次性 strings 解码即可，非关键 |
| U7 | waitable-timer 支路（vsync=true 或 maxfps>=60 时）的 `[0x1005F138]` 句柄创建细节（0x10017AD0 经 GetProcAddress 动态调用） | `[未证]` | 本配置（vsync=false, maxfps=60）不走该支路，可缓 |
| U8 | `[0x1005F120]` timeGetTime 值 49.7 天回绕 | 理论已知 | 单局时长内无影响，记录在案 |
| U9 | last_t 轮询（1kHz RPM）对窗口线程的扰动量化 | `[未证]` | 按裁决 ABBA ≥5 区组 + 独立画面参照（真机批） |
