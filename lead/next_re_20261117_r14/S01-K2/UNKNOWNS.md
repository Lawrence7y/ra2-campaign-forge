# S01-K2 · UNKNOWNS（诚实登记，不臆造）

| # | 问题 | 现状 | 为何不定 | 建议下一步 |
|---|---|---|---|---|
| U1 | "局内"的精确判据（≠mode==5） | 静态证 mode 写值域 ⊇{0,3,4,5}（写点见 `mode_writes.txt`）；mode==5 覆盖遭遇战设置/局内/暂停三态 | 三态共用 mode 5，静态无法从 mode 单独区分；需真机联合 `frame(0xA8ED84)` 递增 + `PlayerHouse(0xA83D4C)` + 对象 update 状态 | 真机（需当轮授权）在三态各采样 mode+frame+objects 联合判定 |
| U2 | 暂停/最小化/失焦时是否停止帧更新 | 已定位候选标志 `0xA83D48`/`0xA83D49`/`0xA8ECD0`/`0x8B41C0`（`framepred_full_disasm.txt` 0x55D059–0x55D080、0x55D123–0x55D135；`xref_all.txt` 各有 6–9 个写点）；FrameDraw 也读写 `0x8B41C0`(@0x48CB2E) | 这些字节的"暂停/失焦"语义是**据名+分支位置推断**，未做该类自己的写点+读点双支撑（纪律 4）；且失焦时 frame 是否仍 inc 需真机 | 追 `0xA83D48`/`0xA8CD0` 写点所在函数，确认由 WM_KILLFOCUS/WM_SIZE 触发；真机验证暂停时 frame 是否停 |
| U3 | 32ms 地板是否等于固定 Sleep(32) | 实测：`0x55E160` 用 `timeGetTime` 环 + `Sleep(remaining)` 动态补足（`push esi; call [Sleep]`），`0x55D360` 另有 `Sleep(500)`/`Sleep(10)` 的等待态循环（mode 0/5→500，其他→10）；目标 FPS 存 `0xA8B558` | "固定 Sleep(32)"是过度简化；实际是目标帧间隔环 + 剩余时间 Sleep，且有两套计时器环（0x887328../0x887348..） | 静态已足够定"限速机制存在"；精确 31.247 vs 32 的差属真机 timer 量化，不在静态卡复算 |
| U4 | `0x55CFD0` FramePredicate 的 786B 全部分支语义 | 已逐条打前 127 行（`framepred_full_disasm.txt` 0x500 全量落盘）；确认它处理 mode/失焦标志翻牌 + FPS 环记录 + 调用 `0x72DFB0`/`0x69BB40`/`0x685670`/`0x69BAB0`/`0x7241A0` | 完整语义需逐个辅助函数；本卡定位是"骨架调用顺序"，不下钻每个 helper（跨 S09/S07 写域） | 交 S09/S16 卡细化 helper；本卡只定"每 tick 必调 #4 + 条件调 #2" |
| U5 | 网络 per-tick 调用是否存在 | 主循环 4 个内层 site + 外层链中**未见明确网络栈调用**；`0x887368`（网络会话？）仅门控 `0x7241A0` | "未见"不等于"不存在"（纪律 18）；网络可能在 `0x7241A0`/`0x6C87F0` 内部或事件驱动，非每 tick 顶层 | S18（网络卡）追 `0x7241A0`/`0x6C87F0` 内部调用链 |
| U6 | `0xA8ED84` 的其余 9 个写点语义 | 本卡确认主写点 `0x55DE7E/0x55DE81`（inc+写回）；`xref_all.txt` frame 段另有 9 个写点未逐个溯源 | 本卡只需"帧计数在 PerFrameUpdate 递增"这一结论；其余写点可能是关卡切换重置，不影响骨架 | 若需"frame 单调性"结论，逐写点回溯寄存器语义（纪律 A） |
| U7 | LogicClass 的 GetSize / sizeof | vtable 0x7E1900 30 槽无 `B8 imm32 C3`；v[11] 是数据、v[12] 是构造链；无堆分配双点 | 容器类非 AbstractClass 族，槽契约不适用；无 second channel（纪律 1） | 若必须定 size，另找静态实例 `0x87F778` 的 memset/init 范围（非 new 分配），作单通道 `[静态推断]` |
