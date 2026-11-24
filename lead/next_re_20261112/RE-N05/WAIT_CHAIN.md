# RE-N05 · WAIT_CHAIN.md（四位置逐个的调用契约与等待条件）

> run_id `NEXT_RE_20261112_R01`。**本轮零真机**：只读磁盘 PE 字节与既有 JSON；未启动游戏、未 attach、未 ReadProcessMemory 活游戏进程、未 SuspendThread/ResumeThread/StackWalk64/MiniDump/断点/注入/部署/taskkill，未执行任何 git 写操作。写域仅 `lead/next_re_20261112/RE-N05/`。
> 证据索引：`EVIDENCE/stdout_step1.txt`（EXITCODE=0，地址归一）、`stdout_disasm.txt`（EXITCODE=0，四位置反汇编 + IAT/导出/重定位）、`stdout_step4b.txt` / `stdout_step5b.txt` / `stdout_step6.txt` / `stdout_step7.txt` / `stdout_args.txt` / `stdout_waitapi.txt`（均 EXITCODE=0），`stdout_interrupted_draft.txt`（前次半成品，EXITCODE=0，仅用于对照纠错）。
> 等级：`[本次实测]`=命令+原始输出+退出码；`[本次读码]`=文件:行；`[静态推断]`=VA/RVA/文件偏移/字节；`[转引]`=来源:行；`[待运行验证]`=需真机且本轮禁止。

## 0 · 通用判据（本卡全部位置共用）

1. `[本次读码]` `lead/re_d13_ruling_20261112/e3_stackwalker.py:225-241`：`walk()` 调真 `dbghelp!StackWalk64`，把 `sf.AddrPC.Offset` 逐帧写入 `frames`，顺序**由内向外**。第 0 帧是当前 EIP；**其余帧的 AddrPC 是返回地址**（`call` 之后的下一条），不是"当时正在执行的阻塞指令"。
2. `[本次实测]` 四个目标在 JSON 中都不是栈顶帧（14412 是 `#3`/`#6`；40500 是 `#1`/`#2`/`#3`），故全部按**返回地址**处理；`stdout_step1.txt:268-309`。
3. `[本次实测]` 边界确认用两条独立方法交叉：
   - 整段 `.text`（gamemd 4,060,045 B / ddraw 245,849 B）从节首做 capstone `skipdata` 线性扫描，得到**指令起点 bitmap**；
   - 从**可信函数边界**做严格无间隙前向解码，确认目标地址恰为一条指令起点（`stdout_step6.txt:15-16, 42-43, 67-68`，三处 `target IS an instruction start: True`；ddraw 见 `stdout_disasm.txt:183-196`）。
   不采用"往回退到看起来像指令开头"。
4. `[本次实测]` 四个量分开：RVA / 首选 VA(`ImageBase+RVA`) / 运行期 VA(`实际基址+RVA`) / 文件偏移(节表 `rawptr`)。gamemd 基址 `0x400000` 且 `RELOCS_STRIPPED`；ddraw 基址 `0x547B0000` 且 ASLR。全表见 `MODULE_BINDING.md` §2。
5. `[本次实测]` 磁盘 PE 里 ddraw 的 `0x100xxxxx` 是**首选 VA**：`call [0x10053A68]` 的 imm32 在 RVA `0x22B02` 有 type-3 HIGHLOW 重定位，运行期该操作数变为 `[0x54803A68]`（`stdout_disasm.txt:201-206`）。

## 1 · 位置 A：`gamemd.exe+0x13EB1C`（pid 40500，最外层帧）

**地址四元组** `[本次实测]` `stdout_step1.txt:322-331`：RVA `0x0013EB1C` / 首选 VA `0x0053EB1C` / 运行期 VA `0x0053EB1C` / 文件偏移 `0x0013EB1C`；目标字节 `8B D8 83 3D 44 04 AA 00 01 ...`。

### 1.1 返回地址还是执行点
`[本次实测]` **返回地址**。`stdout_disasm.txt:43-48` / `stdout_step6.txt:32-33`：目标处 `8B D8 = mov ebx, eax`，前一条且**恰好结束于** `0x13EB1C` 的指令是 `0x0053EB16 FF 15 84 14 7E 00 = call dword ptr [0x7E1484]`。目标不在任何栈顶帧中（40500 event #0 是 `#2`，event #1 是 `#3`）。

### 1.2 所属函数
`[本次实测]` `stdout_step6.txt:12-37`：函数起始是 **FPO（省略帧指针）风格** `RVA 0x0013E770`（首选/运行 VA `0x0053E770`，FOFF `0x0013E770`），前有 14 字节 `0x90` 对齐填充；开头 `83 EC 34 / A1 44 04 AA 00 / 53 55 56 57` = `sub esp,0x34; mov eax,[0xAA0444]; push ebx/ebp/esi/edi`。从该起点严格解码 254 条指令无间隙直达目标。
- 函数收尾：目标后的 `ret 0xC`（`0x53EBAD`、`0x53EBF1`，`stdout_disasm.txt:58-59`）⇒ 该包装函数自身是 **stdcall 3 参数 / 12 字节，被调方清理**；这与它调用的 `PeekMessageA`（5 参数 / 20 字节）是**两层不同契约**，不能混。
- 是否与其它路径共享：`[静态推断]` 该函数体内读全局 `[0xAA0444]`（`0x53E773`、`0x53EB1E`）并在 `0x53EAF6` 调 `LeaveCriticalSection`（IAT `0x7E11EC`，`stdout_args.txt:24`），是带会话模式分支的**输入/消息泵包装**；`[转引]` `docs/re/audio_input_hotspots.md:535` 与 `docs/re/re_sprint_S14_report.md:19` 称其为 `WW_PeekMessageA` / `PumpWin32MouseAndMessages`，`[0xAA0444]` 为 0=实时/1=录制/2=回放的会话状态。本轮只复核到"该全局被读、有模式分支"，**未证**三种模式的运行期取值。
- ⚠ 自我纠错：`stdout_disasm.txt:25-29` 曾把 `0x53D330`（标准 `push ebp;mov ebp,esp`）误选为所属函数；`stdout_step5b.txt:61-62` 证明 `0x53D330..0x53E770` 之间存在多条 `ret`，那个"最近序言"属于**前一个函数**。正确起点是 `0x53E770`。详见 `DISAGREE.md` §3。

### 1.3 前一条调用 / 调用约定 / 实参布局
`[本次实测]` `stdout_args.txt:249-262`、`stdout_disasm.txt:48-55`：
- 直接目标是**间接 IAT 调用** `call [0x007E1484]`；`resolve_abs` = **IAT → `USER32.dll!PeekMessageA`**（`stdout_disasm.txt:52`；IAT VA `0x7E1484` / RVA `0x3E1484`，文件初值 `0x004100E2` 是导入名表 RVA，非代码地址）。
- 调用约定：`__stdcall`，5 个 dword 参数 / 20 字节，被调方清理（调用后无 `add esp,0x14`）。
- push 顺序（`stdout_args.txt:249-258`，右→左）：
  `0x53EB01 mov eax,[esp+0x50]`；`0x53EB05 mov ecx,[esp+0x4C]`；`0x53EB09 mov edx,[esp+0x48]`；
  `push eax`(arg5 `wRemoveMsg`) → `push ecx`(arg4 `wMsgFilterMax`) → `push edx`(arg3 `wMsgFilterMin`) → `mov eax,[esp+0x14]; push eax`(arg2 `hWnd`) → `push esi`(arg1 `lpMsg`) → `call`。
  即 `PeekMessageA(lpMsg=esi, hWnd=<栈值>, wMsgFilterMin=edx, wMsgFilterMax=ecx, wRemoveMsg=<栈值>)`。`[静态推断]` 具体数值需运行期栈；`[转引]` `lead/goal3t_nightwatch_20261102/swarm_20261104/P02/REPORT.md:94` 称该处是 `PM_NOREMOVE` 探针，本轮**未独立证明** `wRemoveMsg` 值。
- 返回值使用：`[本次实测]` `0x53EB1C mov ebx,eax`（保存 BOOL）→ `cmp dword ptr [0xAA0444],1; jne 0x53EBE8` → `cmp ebx,ebp; je 0x53EBE8`（`stdout_step6.txt:33-36`）：返回值被当作"**有消息**"标志，并且只在录制模式分支继续处理消息。

### 1.4 下游 API 与正常返回条件
`[本次实测]` IAT → `USER32!PeekMessageA`。`[静态推断]` Win32 契约：`PeekMessageA` **不阻塞**；有匹配消息返回 `TRUE`（`PM_REMOVE` 时同时移除），无消息**立即**返回 `FALSE`；它是轮询 API，不是 `GetMessageA`/`MsgWaitForMultipleObjects` 这类等待 API。`[本次实测]` `stdout_waitapi.txt` 显示 gamemd 全导入表**没有** `GetMessageA` / `WaitMessage` / `MsgWaitForMultipleObjects`。
⇒ 该返回地址本身不能解释"线程等待"；40500 事件中它下面紧接的 `DDRAW+0x22B06` 说明调用被 **cnc-ddraw 的 PeekMessageA 钩子**接管（见 §4）。真正落在 `ntdll+0x786ac` / `win32u+0x11ac` 的原因**静态不能定谳**（可能是 USER32 内部消息系统调用快照、钩子内 `SendMessage` 重入、或垫片层等待），`[待运行验证]`。

### 1.5 上游入口 / 上下文
`[本次实测]` `stdout_step7.txt:10-11`：whole-`.text`（4,060,045 B）直接 `call rel32` 命中函数起点 `0x13E770` = **0**；全文件 4 字节绝对 VA `0x0053E770` 命中 = **0**。扫描范围/编码/反例见 `stdout_step7.txt` 与 `stdout_waitapi.txt`。⇒ **静态可达性未定**：该 FPO 函数很可能经函数指针/虚表/寄存器间接到达，本轮未找到注册点。
`[转引]` `docs/re/re_sprint_S5_report.md:390` / `docs/re/ARCHITECTURE_ATLAS.md:1911` 称调用者是 `InputMgr::PeekEvent (0x54F000)` 与主消息泵 `0x5D4D50`；本轮未复核，**不采信为已证**。
`[静态推断]` 上下文：输入/消息泵与会话录制回放中枢，**不是**战斗专属、不是退出清理专属；正常对局与菜单都可能经过。

---

## 2 · 位置 B：`gamemd.exe+0x207F17`（pid 14412 `#3` / pid 40500 event#2 `#3`）

**地址四元组** `[本次实测]` `stdout_step1.txt:332-341`：RVA `0x00207F17` / 首选 VA `0x00607F17` / 运行期 VA `0x00607F17` / FOFF `0x00207F17`；字节 `8B 44 24 1C 8B 8C 24 E4 00 00 00 40 3B C1 89 44`。

### 2.1 返回地址还是执行点
`[本次实测]` **返回地址**。`stdout_step6.txt:56-57`：前一条恰结束于目标的是 `0x00607F11 FF 15 F0 11 7E 00 = call dword ptr [0x7E11F0]`，再前一条 `0x607F0F 6A 1E = push 0x1E`。

### 2.2 所属函数
`[本次实测]` `stdout_step6.txt:39-62`、`stdout_step5b.txt:13-35`：所属函数是 **FPO 风格**的 `RVA 0x00206800`（VA `0x00606800`，FOFF `0x00206800`），起点字节 `51 53 55 8B 6C 24 10 56 57 55 FF 15 EC 14 7E 00`（`push ecx/ebx/ebp; mov ebp,[esp+0x10]; push esi/edi; push ebp; call [0x7E14EC]=USER32!GetParent`）。从该起点严格解码 **1598 条指令无间隙**直达目标。
- 该起点是可信边界的**独立证据**：`0x606800` 被作为 `lpEnumFunc` 传给 `USER32!EnumChildWindows`，在文件中以 4 字节立即数出现 **6 次**（`stdout_step7.txt:14`：`0x2071C3`、`0x2071D3`、`0x208145`、`0x208239`、`0x208338`、`0x20834B`），其中至少 4 处随后就是 `call [0x7E14E4]`/`call ebx` = `EnumChildWindows`（`stdout_step7.txt:22, 49, 64, 73`）。⇒ 它是**共享的子窗口枚举回调**，不是只服务一条路径。
- `[静态推断]` 大小：至少 `0x207F17−0x206800 = 0x1717` 字节；线性区间内有 5 条条件 `ret`/`ret 8`（`0x207128`、`0x20719F`、`0x2071BD`、`0x2071CE`、`0x2071DE`，`stdout_step6.txt:44`），说明**函数精确边界/大小不能仅靠线性反汇编定谳**（多出口 + 可能的相邻小函数）；`ret 8` 与 `WNDENUMPROC(HWND,LPARAM)` 的 2 参数 stdcall 契约一致。此项列入 `UNKNOWNS.md`。

### 2.3 前一条调用 / 调用约定 / 实参布局
`[本次实测]` `stdout_disasm.txt:320-336`（IAT 汇总）、`stdout_args.txt:289-296`：
- `call [0x007E11F0]` → **IAT → `KERNEL32.dll!Sleep`**（`stdout_args.txt:290`；`stdout_step4b.txt:130`：`0x7E11F0 -> KERNEL32.dll!Sleep`）。
- `__stdcall`，**1** 个 dword 参数 / 4 字节，被调方清理；实参 `push 0x1E` = **30 ms**。
- 返回值：`Sleep` 返回 `VOID`；`[本次实测]` 目标处 `mov eax,[esp+0x1C]` 立刻覆盖 EAX，返回值未被使用。
- 循环：`[本次实测]` `0x607F1B mov ecx,[esp+0xE4]; inc eax; cmp eax,ecx; mov [esp+0x1C],eax; jl 0x6076ED`（`stdout_args.txt:291-296`）⇒ 每次迭代 `Sleep(30)`，上限由 `[esp+0xE4]` 给出。[静态推断] 这是**带超时的轮询/等待循环**，不是消息/对话框等待 API；循环上限的运行期值静态未知。

### 2.4 下游 API 与正常返回条件
`[静态推断]` `Sleep(30)` 的正常返回条件是**内核定时器到期（≥30 ms；受时钟粒度与调度影响可更长）**；不需要消息、事件或互斥量唤醒，也不创建/置位等待对象；无失败返回值。其内核路径 `KERNELBASE!SleepEx` → `ntdll!NtDelayExecution` 与栈中 `ntdll+0x7858c ← KERNELBASE+0x16a1f0 ← KERNELBASE+0x16a18f ← gamemd+0x207F17` 吻合（`stdout_step1.txt:272-278`）。
`[本次实测]` `stdout_waitapi.txt`：四个调用点**没有** `WaitForSingleObject`/`WaitForMultipleObjects`/`MsgWaitForMultipleObjects`/事件/互斥量/临界区等待 API；gamemd 虽导入 `WaitForSingleObject(0x7E11DC)`、`WaitForMultipleObjects(0x7E113C)`、`CreateEventA/SetEvent/ResetEvent/CreateMutexA/EnterCriticalSection`，但 IAT 槽与四个 call 点都不匹配。

### 2.5 上游入口 / 上下文
`[本次实测]` `stdout_step7.txt:13-14, 19-23`：`0x606800` 的直接 call xref = 0（符合"回调由 USER32 反向调用"），但作为 `push 0x606800` 立即数在 6 处注册；`0x6071C8` 处 `call [0x7E14E4] = EnumChildWindows(hWnd=ecx, lpEnumFunc=0x606800, lParam=1)`。
`[静态推断]` 上游 = `USER32!EnumChildWindows` 的回调分派：14412 栈中 `USER32+0x74775 ← USER32+0x3505d` 正是 USER32 内部调用回调的两层。上下文归类：**窗口/子控件枚举与 UI 状态管理**（同区域还用 `IsWindowVisible`、`IsWindowEnabled`、`EnableWindow`、`InvalidateRect`），更像**对话框/窗口管理**而非战斗逻辑主循环，也非退出清理专属；`[待运行验证]` 需要同时刻画面/游戏状态才能定谳。

---

## 3 · 位置 C：`gamemd.exe+0x20833F`（pid 14412，最外层帧 `#6`）

**地址四元组** `[本次实测]` `stdout_step1.txt:342-351`：RVA `0x0020833F` / 首选 VA `0x0060833F` / 运行期 VA `0x0060833F` / FOFF `0x0020833F`；字节 `B2 01 8B CE E8 98 EE FF FF 6A 00 68 00 68 60 00`。

### 3.1 返回地址还是执行点
`[本次实测]` **返回地址**。`stdout_step6.txt:82-83`：前一条恰结束于目标的是 `0x0060833D FF D3 = call ebx`。

### 3.2 所属函数
`[本次实测]` `stdout_step6.txt:64-89`、`stdout_step5b.txt:37-59`：函数起始 **FPO/thiscall 风格** `RVA 0x00208070`（VA `0x00608070`，FOFF `0x00208070`），前有 5 字节 `0x90` 对齐填充 + 前一函数 `5E 59 C3`；开头 `83 EC 0C / 53 / 55 / 8B E9 / 57` = `sub esp,0xC; push ebx; push ebp; mov ebp,ecx; push edi`（**`this` 在 ECX**）。严格解码 251 条指令无间隙直达目标；收尾 `0x608370 C3 = ret`（`stdout_disasm.txt:95`，cdecl/thiscall，调用方清理），大小约 `0x300` 字节。
- `[静态推断]` 线性区间内 4 条条件 `ret`（`0x2080D3`、`0x2081A5`、`0x20825F`、`0x2082BD`）⇒ 多出口函数；精确大小以 `0x608370` 的 `ret` 为界是 CFG 级推断，标 `[静态推断]`。
- 是否与其它路径共享：`[本次实测]` 直接 call xref = 0、绝对 VA dword = 0（`stdout_step7.txt:77-78`）；`mov ebp,ecx` 表明是 C++ 成员函数，静态可达性未定（很可能经虚表/函数指针间接到达）。

### 3.3 前一条调用 / 调用约定 / 实参布局
`[本次实测]` `stdout_args.txt:314-318` / `stdout_step4b.txt:135`：
- `0x60832F 8B 1D E4 14 7E 00 = mov ebx, dword ptr [0x7E14E4]` → IAT **`USER32.dll!EnumChildWindows`**；`0x60833D FF D3 = call ebx` 是**寄存器间接调用**，槽位即 `0x7E14E4`（RVA `0x3E14E4`）。
- `__stdcall`，**3** 个 dword 参数 / 12 字节，被调方清理（调用后无 `add esp,0xC`）。push 顺序（右→左）：
  `push 1`（`lParam=1`）→ `push 0x606800`（`lpEnumFunc` = §2 的回调）→ `push esi`（`hWnd`）→ `call ebx`。
  即 `EnumChildWindows(hWnd=esi, lpEnumFunc=0x606800, lParam=1)`。
- 返回值：`[静态推断]` 返回 `BOOL`；目标之后 `mov dl,1; mov ecx,esi; call 0x6071E0`（`stdout_step6.txt:83-85`）未立即读 EAX，后续 `0x608352 mov eax,[esp+0xC]` 也不是该返回值 ⇒ 返回值被忽略/未立即使用。且栈帧是**返回地址**，说明该调用当时尚未返回（回调仍在执行）。
- 同一函数在 `0x608350` 又调一次 `EnumChildWindows(esi, 0x606800, 0)`，中间夹 `call 0x6071E0`，随后 `EnableWindow(esi, al&0xFF)` 与 `InvalidateRect(esi,0,0)`（`stdout_args.txt:322-334`）⇒ **枚举 → 改状态 → 再枚举 → 重绘** 的两遍 UI 处理。

### 3.4 下游 API 与正常返回条件
`[静态推断]` `EnumChildWindows` 正常返回条件 = **枚举完所有子窗口且回调均返回 TRUE**（回调返回 FALSE 时提前结束）；它本身**不阻塞**，但同步执行回调，回调内若有 `Sleep(30)` 轮询循环（§2）会显著拉长这次调用。栈中 `USER32+0x74775` / `USER32+0x3505d` 与 USER32 的回调分派一致。

### 3.5 上游入口 / 上下文（回答"战斗/对话框/退出？"）
`[本次实测]` `stdout_step7.txt:77-78`：whole-`.text` 直接 call 命中 `0x208070` = 0；全文件绝对 VA `0x00608070` dword = 0 ⇒ **静态可达性未定**。
`[静态推断]` 依据该函数体内的 API 组合（`IsWindowVisible` `0x7E14E0`、`IsWindowEnabled` `0x7E14E8`、`EnableWindow` `0x7E14A0`、`InvalidateRect` `0x7E149C`、两次 `EnumChildWindows`、`USER32!GetParent` 经回调、`0x750920` 一次带 `1.0f` 参数的调用），它属于**窗口/对话框 UI 状态切换**（启用/禁用子窗口并重绘），**不是战斗主循环专属，也不是退出清理专属的静态证据**。任务卡问"对应战斗、对话框还是退出"：静态只支持"对话框/窗口管理类路径"，无法判定该次事件究竟处于战斗、对话框还是退出；`[待运行验证]` 需同一时刻的游戏状态标签/画面/帧边沿。

---

## 4 · 位置 D：`ddraw.dll+0x22B06`（pid 40500 event#0 `#1` / event#1 `#2`）

**地址四元组** `[本次实测]` `stdout_step1.txt:352-361`：RVA `0x00022B06` / 首选 VA `0x10022B06` / **运行期 VA `0x547D2B06`** / **FOFF `0x00021F06`**（`.text` vaddr `0x1000`、rawptr `0x400`，故 `FOFF = RVA − 0xC00`）；字节 `8B F0 85 F6 74 14 FF 75 18 8B 4D 08 FF 75 14 FF`。

### 4.1 返回地址还是执行点
`[本次实测]` **返回地址**。`stdout_disasm.txt:199` / `stdout_args.txt:372-373`：前一条恰结束于目标的是 `0x10022B00 FF 15 68 3A 05 10 = call dword ptr [0x10053A68]`；目标 `8B F0 = mov esi,eax`。`STALL_CAPTURE_SUCCESS.md:74` 把它称"停滞点"是**措辞错误**：它是 call 的返回地址，线程当时在**被调用者内部**。

### 4.2 所属函数（包装 / 真实现边界）
`[本次实测]` `stdout_disasm.txt:184-196, 226-267` / `stdout_args.txt:343-386`：
- 函数起始：标准序言 `RVA 0x00022AA0`（首选 VA `0x10022AA0`，**运行 VA `0x547D2AA0`**，FOFF `0x00021EA0`），前有 9 字节 `int3` 填充；`55 / 8B EC / 83 E4 F8 / 51 / 56`。严格解码 43 条指令无间隙直达目标。
- 结束：`RVA 0x00022B26 FOFF 0x00021F26 C2 14 00 = ret 0x14`（`stdout_disasm.txt:209`），后跟 `int3` 填充与下一函数 `0x10022B30`。⇒ 函数大小 `0x22B29 − 0x22AA0 = 0x89` 字节。
- **边界**：这个 `0x10022AA0..0x10022B26` 是 **cnc-ddraw 的包装/钩子函数**；被它 `call [0x10053A68]` 转发的才是**真实现**（`USER32!PeekMessageA`）。`[本次实测]` 22 个导出函数无一覆盖 RVA `0x22B06`（最近的是 ord 5 `DDInternalLock` RVA `0x6860`、ord 20 `GameHandlesClose` RVA `0x5F1B0`，`stdout_disasm.txt:518-520`）⇒ 它不是导出、也不是 COM vtable 方法。

### 4.3 前一条间接调用：槽位、初始化赋值、运行期目标
`[本次实测]` `stdout_disasm.txt:199-206, 463-488` / `stdout_step4b.txt:152-209, 212-213`：
- 指令 `FF 15 68 3A 05 10`；imm32 位于 **RVA `0x22B02`，有 type-3 HIGHLOW 重定位** ⇒ 运行期操作数为 `[0x54803A68]`（首选 `[0x10053A68] + delta 0x447B0000`）。
- 槽位 `0x10053A68` → **RVA `0x00053A68`，`.data`，FOFF `0x00051268`**，**不是 IAT 槽**（`resolve_abs` 明确 `NO`，`stdout_disasm.txt:467`）。
- **静态初始化赋值**：槽内 dword 初值 `0x1002786A`（`stdout_disasm.txt:204`），且该槽自身也有 type-3 HIGHLOW 重定位 ⇒ 运行期变成 `0x547D786A`。该值对应 **RVA `0x0002786A` = `FF 25 74 E3 03 10 = jmp dword ptr [0x1003E374]`**，而 `0x1003E374` 的 IAT 名是 **`USER32.dll!PeekMessageA`**（`stdout_step4b.txt:192, 213`）。同一张 thunk 表还依次指向 `GetClientRect` / `SetWindowLongW` / `SetCursor` / `SendMessageA` / `DefWindowProcA` …（`stdout_step4b.txt:191-208`）。
- **赋值点搜索范围**：对整份 411,648 B 文件做 4 字节 LE 模式 `68 3A 05 10` 精确搜索，命中 4 处（`stdout_disasm.txt:490-516`）：3 处是 `call [0x10053A68]` 指令（RVA `0x76FB`、`0x16BE1`、`0x22B00`），1 处是 `.data` 的 hook 描述表；**未发现** `mov [0x10053A68], reg/imm` 形式的运行期写入 ⇒ 静态只支持"槽由 `.data` 初值 + 加载器重定位得到"，**不能证明**运行期 hook 安装器（如 MinHook）是否把槽覆写为 trampoline，`[待运行验证]`。
- `[本次实测]` hook 描述表（`.data` RVA `0x5400C..0x54064`，`stdout_step4b.txt:152-181`）：
  ```
  RVA 0x5400C..0x54014  ASCII "PeekMessageA"
  RVA 0x5402C          0x10022AA0   ← 本包装函数起始
  RVA 0x54030          0x10053A68   ← 原函数指针槽
  RVA 0x54040..0x54048 ASCII "GetMessageA"
  RVA 0x54060          0x10022A40   ← GetMessageA 钩子
  RVA 0x54064          0x10053A98   ← 对应槽
  RVA 0x54074..        "GetWindowPlacement" / "SetWindowPlacement" / "roundWindow"
  ```
  这是一张**钩子描述/注册表**，不是 COM vtable。与之相邻的字符串直接给出符号级名称。

### 4.4 调用约定、实参布局、隐藏 `this`
`[本次实测]` `stdout_args.txt:367-386`：
- 包装函数 `__stdcall`，**5 个 dword 参数 = 20 字节**，`ret 0x14` ⇒ **被调方清理 20 字节**。
- 参数来自 `[ebp+8]`/`[ebp+0xC]`/`[ebp+0x10]`/`[ebp+0x14]`/`[ebp+0x18]`；`0x22AD7 mov esi,[ebp+0xC]`。
- push 顺序（右→左）：`push [ebp+0x18]` → `push [ebp+0x14]` → `push [ebp+0x10]` → `push esi(=[ebp+0xC])` → `push [ebp+8]` → `call [slot]`。
  ⇒ 转发给真实现的 5 个参数依次是：`lpMsg=[ebp+8]`、`hWnd=[ebp+0xC]`、`wMsgFilterMin=[ebp+0x10]`、`wMsgFilterMax=[ebp+0x14]`、`wRemoveMsg=[ebp+0x18]`，即 **`PeekMessageA` 的 5 参数契约**。
- **没有隐藏 `this`**：`[ebp+8]` 是 `LPMSG lpMsg`，不是接口指针；函数内没有 `mov ecx,[ebp+8]` 作为 COM `this` 的用法。`0x22B0F mov ecx,[ebp+8]` 只出现在**返回后处理分支**，是把 `lpMsg` 作为 fastcall 风格首参传给内部 helper `0x100225C0`（3 个 push + `add esp,0xC`，cdecl/`__fastcall` 混合），不是 COM this。
- **不是任何 DirectDraw 接口方法**：`[本次实测]` 该 DLL 的 22 个导出、`0x10022AA0` 的唯一 dword 引用在 `.data` hook 表（非 vtbl）、没有任何 `IDirectDrawSurface*` 槽号证据；`[静态推断]` `IDirectDrawSurface::Blt` 作为 COM 方法应是 `this + 5 显式参数 = 6 个栈 dword = ret 0x18`，与本处 `ret 0x14`（5 个）**形状就不符**。

### 4.5 返回值使用
`[本次实测]` `stdout_args.txt:373-386`：`mov esi,eax`（保存真 `PeekMessageA` 的 BOOL）→ `test esi,esi; je 0x10022B20`；若 TRUE 则 `push [ebp+0x18]/[ebp+0x14]/[ebp+0x10]; mov ecx,[ebp+8]; call 0x100225C0; add esp,0xC`（对取到的 MSG 做后处理）→ `mov eax,esi` 原样返回 → `ret 0x14`。
`[本次实测]` 包装内其它调用：`0x22AC1 call [0x1003E0E0] = KERNEL32!InterlockedExchange(0x1005EFEC, 0)`，`0x22AE8 call [0x1003E3E8] = WINMM!timeGetTime` 并把结果存到 `[0x1005F09C]`（`stdout_args.txt:354, 365`；IAT 解析见本轮 `pwsh` 实算，亦见 `stdout_step4b.txt` 的 IAT 段）。**"取消息时间戳 + 原子标志 + 消息后处理"是消息钩子语义，不是 Blt 语义。**

### 4.6 下游 API 与正常返回条件
`[本次实测]` 下游 = `USER32.dll!PeekMessageA`（经 `.data` 槽 → `jmp [IAT 0x1003E374]` thunk）。`[静态推断]` 正常返回：**非阻塞**，有匹配消息 TRUE、无消息立即 FALSE。40500 两个事件的栈顶 `ntdll+0x786ac` / `win32u+0x11ac ← USER32+0xc7f51` 是 USER32 消息路径的系统调用快照；**PeekMessageA 本身不会造成长时间等待**，`[待运行验证]` 才能判定当时是瞬时快照、钩子内重入 `SendMessage`、还是垫片层等待。

### 4.7 上游入口
`[本次实测]` 直接调用者是 gamemd `0x53EB16 call [IAT 0x7E1484]`（位置 A）：40500 栈中 `DDRAW+0x22B06` 紧贴在 `gamemd+0x13EB1C` 之上。磁盘 gamemd IAT `0x7E1484` 的名字是 `USER32!PeekMessageA`；要让控制流落到 `0x10022AA0`，运行期该 IAT 槽必须被改写（或被 detour）到 cnc-ddraw 的钩子。
`[本次实测]` `stdout_disasm.txt:218-223`：包装函数 `0x10022AA0` 的 **直接 call xref = 0**，绝对 VA dword 仅 1 处（`.data` hook 表 RVA `0x5402C`），印证它是通过**运行期 hook 安装**被调用的。
`[待运行验证]` 需一次只读 IAT/槽值采样来确认 `0x7E1484` 与 `0x10053A68` 的运行期值；本轮零真机，不做。

### 4.8 ★ 符号级确认做到什么程度 / 复核 `STALL_CAPTURE_SUCCESS.md:54-97` 的「推为 Blt」

**做到的（静态，版本已对齐）**：
1. `[本次实测]` `ra2opt/vendor/cnc-ddraw-7.1.0.0.zip` 内 `ddraw.dll` 与 `ra2youli/ddraw.dll` **逐字节相同**（411,648 B / SHA-256 `85e0f7d5…`，`stdout_step4b.txt:215-217`）⇒ 版本匹配的**二进制**在仓库里；PDB 路径 `C:\Users\Nutzer\source\repos\cnc-ddraw\bin\ReleaseXP\ddraw.pdb`（`stdout_step1.txt:149`），文件内含 UTF-16LE `7.1.0.0`（FOFF 389628 / 390004，`stdout_step5b.txt:70`）。
2. `[本次实测]` `.data` hook 表把 `0x10022AA0` **显式标为 `"PeekMessageA"` 的钩子**，并给出其原函数槽 `0x10053A68`；槽内初值跳到 `USER32!PeekMessageA` 的 IAT thunk。
3. `[本次实测]` 5 参数 + `ret 0x14` + `timeGetTime` 时间戳 + 消息后处理，与 `PeekMessageA` 契约逐项吻合；上层 gamemd 的 call 也是 `PeekMessageA`。
4. `[转引]` `lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md:2028` 已有 "cnc-ddraw **fake_PeekMessageA**（ddraw.dll+0x22AA0）" 的同名标注（本轮不靠它定谳，仅作旁证）。

**没做到的（必须明说）**：
- `[本次实测]` 仓库内**无版本匹配的 cnc-ddraw C/C++ 源码、无匹配 `.pdb`/`.map`**：`stdout_step5b.txt:75-108` 给出搜索范围（11 个显式列出的文件 + 本轮 `glob` 工具实跑的 `**/*.{c,cpp,h,hpp,cc,cxx,pdb,map,def,idb,i64}` 共 1283 条路径、`**/*ddraw*` 共 126 条路径）、编码（ASCII 大小写不敏感 + UTF-16LE 精确）、正例（`cnc-ddraw` 41 命中 / `PeekMessageA` 21 命中）、反例（`ZZZ_NO_SUCH_TOKEN_9F3C` 0 命中）。vendor zip 25 项里只有 `ddraw.dll`/`ddraw.ini`/`config.exe`/GLSL，**无源码无 PDB**（`stdout_step4b.txt:218-219`）。
- ⇒ **静态证据只支持**：「`0x22B06` 是 cnc-ddraw 对 `USER32!PeekMessageA` 的钩子包装（运行期函数名惯例 `fake_PeekMessageA`）内 `call [0x10053A68]` 的返回地址」。
- **符号级确认还需要 Y**：(a) 与 `7.1.0.0` 匹配的 cnc-ddraw **源码或 `ddraw.pdb`**（能把 `0x10022AA0` 映射到编译期符号、给出 hook 安装代码与 `fake_PeekMessageA` 定义）；(b) 一次**运行期只读**观测：`gamemd` IAT `0x7E1484`、`ddraw` 槽 `0x54803A68` 的实际值，确认 hook 已安装、槽是否被 MinHook trampoline 覆写。两者都属 `[待运行验证]`，交 RE-N06。

**对 `STALL_CAPTURE_SUCCESS.md:54-97` 判据链逐条复核**：

| # | 原判据 | 本轮复核 | 结论 |
|---|---|---|---|
| 1 | `0x22B06` 紧跟 `call [0x10053A68]` ⇒ StackWalk64 返回地址语义 | `[本次实测]` `stdout_disasm.txt:199-200` 字节 `FF 15 68 3A 05 10` + 目标 `8B F0`；边界由整段线性扫描与严格前向解码双重确认 | **成立** |
| 2 | 调用前压了 5 个参数 | `[本次实测]` `stdout_args.txt:367-372` 五条 push 完全一致 | **成立** |
| 3 | 函数以 `ret 0x14` 收尾 ⇒ 恰好 5 个 dword | `[本次实测]` `stdout_args.txt:386 C2 14 00` | **成立** |
| 4 | "DirectDraw 里 5 参数的标准方法是 `Blt(LPRECT, LPDIRECTDRAWSURFACE, LPRECT, DWORD, LPDDPBLITFX)`" ⇒ 本处是 Blt | `[静态推断]` COM `Blt` 需 `this` + 5 显式参数 = **6** 个栈 dword ⇒ `ret 0x18`；本处 `ret 0x14` 且 `[ebp+8]` 是 `LPMSG` 不是接口指针、无 vtable 槽、无 `IDirectDrawSurface` 材料；`.data` hook 表直接写 `"PeekMessageA"`；槽初值跳到 `USER32!PeekMessageA` IAT | **不成立，且是决定性错误** |
| 5 | `0x22b06` 不在 22 个导出内 | `[本次实测]` `stdout_disasm.txt:518-520`，22 个导出无一覆盖 | **成立** |
| 6 | 第二次停滞 `win32u+0x11ac ← USER32+0xc7f51` ⇒ Blt 内部进到 GDI/win32u 路径 | `[静态推断]` 该组合与 USER32 消息 API 的内核路径一致，且外层是 `gamemd+0x13EB1C`（`PeekMessageA` 调用点）；仅凭 win32u 不能判 GDI 渲染分支 | **不成立 / 证据不足** |
| 7 | 边界声明"在 cnc-ddraw 内部，不是原版 DirectDraw" | `[本次实测]` 成立 | **成立**，但原报告结论"阻塞在 Blt 的包装实现里"随之作废 |
| 8 | 报告用 `0x10022af3…` 与 `[0x10053A68]` 作地址 | `[本次实测]` 这是**首选 VA**；该趟实际基址 `0x547B0000`，运行期 VA 应为 `0x547D……` / `[0x54803A68]`；`LEAD_INDEPENDENT_CHECKS.md:40` 也已指出 | **混用 VA/RVA，错** |

`[转引]` `STALL_CAPTURE_FINAL.md:104-109` 进一步把两条栈签名写成"一趟 `Blt`、一趟消息等待 ⇒ 至少两条不同成因路径"：**双重错误**（Blt 定性错 + 不同签名推不同根因的逻辑错）。

---

## 5 · 等待对象、唤醒方与失败路径（第三步）

`[本次实测]` `stdout_waitapi.txt`：**四个调用点解析出的 API 是 `PeekMessageA` / `Sleep(30)` / `EnumChildWindows` / `PeekMessageA`（经 hook），没有任何事件、互斥量、临界区、信号量、可等待计时器或 `WaitForSingleObject`/`MsgWaitForMultipleObjects` 等待调用**。搜索范围 = 两镜像完整导入表（gamemd 372 条导入项，其中 369 条具名 / ddraw 247 条，`stdout_waitapi.txt:13-14`）+ 四位置的 capstone 解码结果；反例校验 = 同一枚举能命中 `Sleep`/`PeekMessageA`/`EnumChildWindows`，零命中不是扫描器失效。

| 对象 | 创建 / 置位 / 复位 / 销毁 | 应当唤醒它的线程/事件 | 失败路径 | 等级 |
|---|---|---|---|---|
| **线程消息队列**（`PeekMessageA` 读取，位置 A/D） | 线程创建窗口/消息队列时建立；`PostMessageA`/`SendMessageA`/输入/计时器/`WM_*` 置位；`PM_REMOVE` 取走或 `PeekMessageA` 读后丢弃即复位；线程退出时销毁 | 任意向该线程队列投递消息的线程、硬件输入、`SetTimer`/`KillTimer`（gamemd 导入 `0x7E1494`/`0x7E148C`）、窗口焦点变化 | `PeekMessageA` 无消息即返回 FALSE（**正常**）；若长时间停在 USER32/win32u 内部，则可能是钩子重入 `SendMessage` 或垫片等待，`[待运行验证]` | `[静态推断]` + `[本次实测]`(IAT) |
| **内核定时器**（`Sleep(30)`，位置 B） | 每次 `Sleep` 由内核建立一次性定时器；到期置位；无显式复位/销毁；`Sleep` 返回 VOID 无失败返回 | 时钟中断/调度器（不需外部线程） | 无失败返回；实际时长受 `timeBeginPeriod(1)` 等时钟粒度影响可 >30 ms | `[静态推断]` |
| **子窗口枚举回调**（`EnumChildWindows`，位置 C/B） | 由 `EnumChildWindows` 同步枚举；每个子窗口触发一次回调 `0x606800`；回调返回 FALSE 提前结束 | 调用线程自身（同步，无外部唤醒） | 回调内 `Sleep(30)` 轮询循环会拉长；若轮询上限很大则表现为"卡住" | `[静态推断]` |
| **临界区 / 事件 / 互斥量**（**不在四位置**） | gamemd 导入 `InitializeCriticalSection(0x7E11F4)`/`Enter(0x7E11E8)`/`Leave(0x7E11EC)`/`CreateEventA(0x7E1168)`/`SetEvent(0x7E1234)`/`ResetEvent(0x7E1178)`/`CreateMutexA(0x7E1248)`/`ReleaseMutex(0x7E1198)`/`WaitForSingleObject(0x7E11DC)`/`WaitForMultipleObjects(0x7E113C)`；`0x53EAF6` 有 `LeaveCriticalSection` | 拥有者线程释放 / 其它线程 `SetEvent` | 静态未定位到这些槽在四个位置的调用者 | `[本次实测]` 仅导入/同函数旁证，`[静态推断]` 非本栈等待对象 |

---

## 6 · 两条栈签名的关系（明确"捕获路径不同"还是"上游状态不同"）

`[本次实测]` 逐帧比对（`stdout_step1.txt:268-309`）：

| 来源 | 栈（内→外） | 本轮静态对应 |
|---|---|---|
| 14412 event#0 `t=471.266 frame=15042`，`picked_by=only_tid`，`paused_ms=0.0` | `ntdll+0x7858c` ← `KERNELBASE+0x16a1f0` ← `KERNELBASE+0x16a18f` ← **`gamemd+0x207F17`** ← `USER32+0x74775` ← `USER32+0x3505d` ← **`gamemd+0x20833F`** | `Sleep(30)` 轮询循环（位置 B），外层 `EnumChildWindows`（位置 C） |
| 40500 event#0 `t=347.047 frame=11152`，`picked_by=most_gamemd_frames`，`paused_ms=94.0` | `ntdll+0x786ac` ← **`DDRAW+0x22B06`** ← **`gamemd+0x13EB1C`** | cnc-ddraw `PeekMessageA` 钩子（位置 D） ← gamemd `PeekMessageA` 调用（位置 A） |
| 40500 event#1 `t=351.594 frame=11231`，`paused_ms=78.0` | `win32u+0x11ac` ← `USER32+0xc7f51` ← **`DDRAW+0x22B06`** ← **`gamemd+0x13EB1C`** | 同上，多一层 USER32/win32u |
| 40500 event#2 `t=354.938 frame=0`（报告称游戏已退出），`paused_ms=63.0` | `ntdll+0x7858c` ← `KERNELBASE+0x16a1f0` ← `KERNELBASE+0x16a18f` ← **`gamemd+0x207F17`** | **与 14412 的内 4 帧完全相同**（同一 `Sleep(30)` 位置） |

**结论（按任务卡"只写候选"）**：
1. `[本次实测]` 40500 **自己就同时包含两种签名**：event#2 与 14412 的 `gamemd+0x207F17` 前四帧逐帧相同；event#0/#1 是 `DDRAW+0x22B06` 消息钩子路径。因此"14412 走 USER32 消息等待、40500 有事件走 DDRAW"这种把两趟整体对立的描述不成立。
2. `[本次实测]` 两趟的**捕获策略不同**：14412 是 `--only-tid` 单线程、只 1 个事件、`paused_ms=0.0`、3493/3493 全可读；40500 是全线程 27 线程按 `most_gamemd_frames` 挑线程、`paused_ms=63/78/94 ms`、1792/3991 可读（`stdout_step1.txt:269-309`；`STALL_CAPTURE_SUCCESS.md:43-50`、`STALL_CAPTURE_FINAL.md:64-69` 转引）。这首先解释的是**捕获路径/被选中线程/采样时机不同**。
3. `[转引]` `STALL_CAPTURE_SUCCESS.md:32` 与 `STALL_CAPTURE_FINAL.md:89` 记载 40500 event#2 时 `frame=0`、游戏已退出；14412 的事件发生在 `frame=15042` 且之后 229 s 未推进（但该 229 s 是统计推断、非逐样本已证，`STALL_CAPTURE_FINAL.md:92-94`）。⇒ **同一个 RVA 签名可以对应完全不同的上游状态**（局内长停 vs 退出后），这正是任务书第 6 步 RE-N06 要求的"相同 RVA 也可能来自不同上游状态"（`docs/re/NEXT_RE_TASKS_20261112.md:218`）。
4. ⇒ **在拿到上游状态证据之前只写"候选"**：不能推导为两个独立根因，也不能写成机制已确认。`[转引]` `docs/re/NEXT_RE_TASKS_20261112.md:65` "两个栈签名不同，也只说明捕获路径不同；尚不能推出存在两个独立根因" 与本轮结论一致；`STALL_CAPTURE_FINAL.md:104-109` 的"至少两条不同成因路径"应降级为候选。
5. `[待运行验证]` 最有区分力的下一观测：同一事件同时记录 ① 游戏状态标签（LOADING/IN_TACTICAL/PAUSED/MENU/SCORE_SCREEN/EXITING）② 画面 ③ 帧/tick 边沿 ④ 窗口焦点 ⑤ 被采线程的 TID 与选择依据 ⑥ `0x7E1484`/`0x54803A68` 的 IAT/槽运行期值；按 RE-N06 一次只改一个变量做对照。

---

## 7 · 带证据的调用图（静态，箭头 = 调用方向）

```
[上游：静态可达性未定] ──(虚表/函数指针? 待运行验证)──> gamemd 0x53E770  (FPO, 3-arg stdcall, ret 0xC)
                                                      │ 读 [0xAA0444] 会话模式
                                                      │ 0x53EB16  push×5 ; call [IAT 0x7E1484]
                                                      ▼
                              [磁盘 IAT 名 = USER32!PeekMessageA]
                              [运行期被 cnc-ddraw hook 接管 → 0x547D2AA0]  ← [待运行验证]
                                                      │
                                                      ▼
   ddraw 0x547D2AA0  fake_PeekMessageA 包装 (RVA 0x22AA0, ret 0x14 = 5 参数)
     ├─ 0x22AC1 InterlockedExchange(0x1005EFEC, 0)         [原子 once 标志]
     ├─ 0x22AE8 timeGetTime() → [0x1005F09C]                [消息时间戳]
     ├─ 0x22B00 push×5 ; call [0x54803A68]                  ← 0x22B06 是这条的返回地址
     │            └─ 槽 0x53A68 初值 0x1002786A → jmp [IAT 0x1003E374] = USER32!PeekMessageA
     └─ 0x22B08 若 TRUE → helper 0x100225C0(ECX=lpMsg, 3 push, cdecl) → 原样返回 BOOL

[上游：静态可达性未定] ──> gamemd 0x608070 (FPO, thiscall: ECX=this, ret)
                              │ IsWindowVisible / IsWindowEnabled / EnableWindow
                              │ 0x60833D push 1, push 0x606800, push esi ; call ebx
                              ▼
                     USER32!EnumChildWindows(HWND, WNDENUMPROC=0x606800, LPARAM)
                              │ (USER32+0x74775 / +0x3505d 回调分派)
                              ▼
                     gamemd 0x606800 回调 (FPO, 6 处注册, ret 8 出口)
                              │ GetParent / 遍历 / 循环计数器 [esp+0xE4]
                              │ 0x607F0F push 0x1E ; 0x607F11 call [IAT 0x7E11F0] = Sleep(30)
                              ▼                      ← 0x607F17 是这条的返回地址
                     KERNELBASE!SleepEx → ntdll!NtDelayExecution
                              │ 0x607F29 jl 0x6076ED (回到循环, 每次 Sleep 30ms)
```

图例：所有 VA 为**首选 VA**；ddraw 运行期需加 `0x447B0000`（如 `0x10022AA0 → 0x547D2AA0`）。四位置均标 `RVA / 首选 VA / 运行期 VA / FOFF` 于 `MODULE_BINDING.md` §2 与本文件各节首。
