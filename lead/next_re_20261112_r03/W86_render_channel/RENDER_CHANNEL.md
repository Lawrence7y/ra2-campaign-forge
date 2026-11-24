# W86 · 渲染呈现观测通道可行性定谳（离线卡）

> run_id `NEXT_RE_20261112_R03` / card `W86_render_channel` / 执行：subagent w86-render / 2026-11-14
> 收口依据：`lead\next_re_20261112_r03\RULING_GPT61SOL.md` §Q3（仪器裁决，已完整读取并逐条对答）
> 对象：`gamemd.exe` (73201cc0…67476) + cnc-ddraw `ddraw.dll` (85e0f7d5…03a9) + `ddraw.ini` (c983abad…f9d52)，全部只读复制进本卡 `bin\` 后分析，哈希逐一核对一致。
> 纪律：全程未启动游戏、未附加进程、未注入、未修改 ra2youli 任何文件。

## 0 · 一句话总判决

| 候选 | 判决 | 通道语义层级 |
|---|---|---|
| ① ETW（D3D9 provider 为主） | **① 可立即真机验** | 提交层（Present 调用 Start/Stop），可下探内核提交/显示层 |
| ② cnc-ddraw 内部结构（RPM 只读轮询） | **① 可立即真机验** | cnc-ddraw 限帧放行层（present 上游节流；时间戳序列） |
| ③ DWM / D3DKMT / GetPresentStatistics | **③ 不可行（作为该进程帧率仪器）**，DWM 节奏仅可作 T 参照 | — |

**一句话**：旧结论「渲染侧观测必须注入/调试器」被本卡**否证**——cnc-ddraw 的限帧状态全局（含每帧更新的上一帧时刻时间戳）与 D3D9 运行时 ETW 打点，两条都是进程外只读通道，均可在现有授权内直接真机验证。

---

## 1 · 前置定谳：生效 maxfps 与实际后端（裁决硬要求，先钉死）

### 1.1 生效 maxfps = 60（否证「全局 -1 生效」假设）

证据链（三段独立）：

1. **[本次实测]** `bin\ddraw.ini`（哈希同原件）逐行实读：`[ddraw]` L31 `maxfps=-1`；**`[gamemd]` 段存在**（L355-359：`tshack=true` / `maxfps=60` / `minfps=-1`）。cnc-ddraw 按可执行文件名匹配段，`gamemd.exe` → `[gamemd]`。
2. **[静态读码]** maxfps 解析函数 `0x1001EF70` 内部结构证明「per-exe 段优先 + `[ddraw]` fallback」双段机制真实存在于代码（见 1.3）。
3. **[静态读码]** `.rdata` 内嵌的出厂默认 ini 模板自带 `[gamemd]` 段（`...evenge.[gamemd].nonexclusive=f…`，VA 0x1004B72F）——exe 名段匹配是 cnc-ddraw 自身的设计，非本机 ini 特例。

**结论：本机 gamemd 生效 maxfps=60，渲染被限帧；「渲染计数与逻辑钟 31.25/s 解耦」的前提成立，任何拿 `[0xA8ED84]` 当帧率的换算依然全部作废（r02 结论不变）。**

### 1.2 实际后端 = 动态加载的 D3D9（裁决「不预设 D3D9 Present」已回答）

**[静态读码]** `ddraw.dll` 侦察（`scripts\_w86_ddraw_recon.py`，stdout 留档 `evidence\recon_stdout.txt`）：

- 导入表**无** d3d9.dll 静态导入；`.rdata` 含 `"d3d9.dll"`（VA 0x10048194）、`"Direct3DCreate9On12"`（0x100481A0）、`"Direct3DCreate9"`（0x100481B4）→ `LoadLibraryA + GetProcAddress` 动态加载。
- `ddraw.ini` L50 `renderer=direct3d9` → D3D9 路径在运行时被选择。
- **含义**：cnc-ddraw 的 present 最终落在进程内 `d3d9.dll!IDirect3DDevice9::Present` ⇒ D3D9 运行时 ETW 打点（候选1）与 cnc-ddraw 限帧状态（候选2）都有**可恢复的目标显示链路**，按裁决判据不判 ③。
- 附带发现：`ddraw.dll` 有 `.detourc/.detourd` 节（Microsoft Detours，cnc-ddraw 自带 hook 框架，`hook=4`），与本项目无关，仅记录。
- `[未证]`（留给真机试采）：当前 `windowed=false`+`fullscreen=false` 下 D3D9 设备是独占全屏还是窗口化交换链——ETW 试采的 DxgKrnl 事件会直接暴露真实模式。

### 1.3 maxfps 解析链（逐指令证据）

```
0x1001E171  b9 98 82 04 10   mov ecx, 0x10048298      ; ecx = "maxfps" 键名（实测 str 0x10048298="maxfps"）
0x1001E169  83 ca ff         or edx, 0xffffffff       ; edx = -1（默认值）
0x1001E176  e8 f5 0d 00 00   call 0x1001EF70          ; ini 取整（per-exe 段 → fallback [ddraw]）
0x1001E17D  a3 e8 94 05 10   mov [0x100594E8], eax    ; ★ 解析结果存 .data 全局 0x100594E8
```

相邻键同一序列（`0x1001E15D`-`0x1001E19B`）：`boxing→0x100594E4(默认0)`、`maxfps→0x100594E8(默认-1)`、`vsync→0x100594EC(默认1)`、`adjmouse→0x100594F0(默认1)`——字符串 VA→内容已实测（`boxing`/`maxfps`/`vsync`/`adjmouse`）。

---

## 2 · 候选 1：ETW 通道 —— 判决 ① 可立即真机验

### 2.1 在机实测（[本次实测]，2026-11-14 Administrator 会话）

| 项 | 实测结果 |
|---|---|
| `Microsoft-Windows-DxgKrnl` | 在机，GUID `802EC45A-1E99-4B83-9920-87C98277BA9D`，712 个事件 |
| `Microsoft-Windows-D3D9` | **在机**，GUID `783ACA0A-790E-4D7F-8451-AA850511C6B9`，10 个事件 |
| D3D9 EventID 1 | Task=**Present**, Opcode=**win:Start**, payload `pSwapchain, Flags` |
| D3D9 EventID 2 | Task=**Present**, Opcode=**win:Stop**, payload `Result` |
| D3D9 EventID 9 | Task=GetPresentStats（`PresentCount, PresentRefreshCount, SyncRefreshCount, SyncQPCTime`） |
| DxgKrnl Present 关键字 | **`Present = 0x8000000`** 在 keyword 表实测存在 |
| DxgKrnl 关键显示事件 | 184(Present,v1: hContext,hWindow,VidPnSourceId,FlipInterval,Flags,ReturnStatus)、469/470(PresentQueuePacket Start/Stop, SubmitSequence)、171/172/173(PresentHistory Start/Info/Stop)、116/259/386(MMIOFlip 系)、1068(BltQueueCompleteIndirectPresent: **FrameQpcDisplayTime**)、505(VSyncHwFlipQueueLogUpdate: FrameNumber,**CompletionTimeStamp**) |
| 工具 | `wpr.exe` 在机（system32）、`logman.exe` 在机、`tracerpt.exe` 在机；**`xperf` 缺、`wpa` 缺** |
| 权限 | Administrator（实测 `IsInRole=True`）；内核 ETW 会话需管理员——满足，条件写明 |

### 2.2 裁决三问的预答与真机判据（试采必须逐条回答，答不出即停）

1. **事件归属 gamemd**：D3D9 provider 事件由进程内 `d3d9.dll` 发出，ETW 标准事件头携带 PID——**进程级归属成立**（`[静态推断-中]`：ETW 事件头含 PID 是平台标准行为，本机实采须复核：过滤 `ProcessId == <gamemd pid>` 后事件数应随游戏启停对称涨落）。**注意**：`pSwapchain` 可用于区分交换链，若 cnc-ddraw 创建主交换链 + 缩放辅助表面，须按 pSwapchain 分组后再判读。
2. **语义分层（不得混称）**：
   - D3D9 **EventID 1 = Present 调用进入（提交层）**；EventID 2 = 调用返回（含 present 内阻塞耗时，Start/Stop 配对可得单次调用时长）——**报告措辞只能是「提交间隔」**。
   - DxgKrnl 184 / 469 = 内核提交层；116/259/386 MMIOFlip = 显示调度层；1068 `FrameQpcDisplayTime` / 505 `CompletionTimeStamp` = **实际显示层**（窗口化+DWM 合成路径才有意义）。
   - **Present ≠ 画面内容更新**：cnc-ddraw 可能持续提交相同内容，稳定提交节奏不得写成「画面流畅」（裁决原文照录）。
3. **事件/缓冲丢失**：`logman stop` 输出含 lost-events 计数；`tracerpt`/解析脚本须统计会话丢包字段；有效分析区间要求零相关丢失（裁决预算原文）。

### 2.3 最小可跑命令序列（Lead 真机批执行，`experiment\exp_etw_short.cmd`）

```
:: 起会话（管理员）：D3D9 全部 + DxgKrnl Present 关键字
logman create trace W86P -ow -o %W86%\etl\W86P.etl ^
  -p {783ACA0A-790E-4D7F-8451-AA850511C6B9} 0xffffffff 5 ^
  -p {802EC45A-1E99-4B83-9920-87C98277BA9D} 0x8000000 4 ^
  -nb 128 1024 -ets
:: 跑游戏（正常启动 gamemd.exe，勿动 ddraw.ini）→ 采 2-5 分钟 →
logman stop W86P -ets          :: stop 输出必须存档（含丢失计数）
tracerpt %W86%\etl\W86P.etl -o %W86%\etl\W86P.xml -of XML
:: 判读：XML 过滤 ProcessId==gamemd 且 EventID==1 的 SystemTime 差分 =
::      提交间隔中位/p95/p99 + 每分钟超 max(50ms,3T) 次数（T=16.7ms）
```

不开启调用栈、CPU 采样、调度器全量与无关 provider（裁决护栏原文）。若 D3D9 事件中 gamemd PID 零命中 ⇒ 该后端无可恢复链路，判 ③ 并停。

---

## 3 · 候选 2：cnc-ddraw 内部结构通道 —— 判决 ① 可立即真机验（本卡主成果）

### 3.1 方法论更正（对 r02 失败判据的定位）

r02 的失败判据是「**绝对地址 + 线性扫描 `inc [abs]`**」找不到渲染帧计数。本卡证明这不是「无计数」，而是**方法不匹配**：cnc-ddraw 的限帧状态全部是 `.data` 绝对全局，但更新形态是 `mov [abs], eax`（写）与 `call rel32`（调用），r02 只扫了 `inc`；且线性 sweep 在数据嵌入处失步漏指令（本卡 caller 扫描也复现了该坑：0x10019481 处实有 `call 0x10006880`，线性 sweep 报 0）。改用**原始字节搜索 + 上下文反汇编**后全链 3 步打通（脚本 3 份 + stdout 全留档于 `scripts\`、`evidence\`）。

### 3.2 限帧全链（[静态读码]，地址全部给三值：文件偏移/RVA/VA，ImageBase 优先基址 0x10000000）

**(a) 解析与存储**（见 1.3）：maxfps → `.data 0x100594E8`（RVA 0x594E8 / off 0x53000 段内）。

**(b) 限帧参数初始化 `sub_10006880`**（VA 0x10006880；调用点 `0x10019481: e8 fa d3 fe ff  call 0x10006880`，启动/设置应用路径）：

```
0x10006880  55                push ebp
0x10006881  8b ec             mov ebp, esp
0x10006883  51                push ecx
0x10006884  a1 e8 94 05 10    mov eax, [0x100594E8]        ; maxfps
0x1000688C  8b 0d 48 ee 05 10 mov ecx, [0x1005EE48]        ; 参考上限（启动时 0x10015E83 写死 60: c7 05 48 ee 05 10 3c 00 00 00）
0x10006892  66 0f 13 05 30 f1 05 10  movlpd [0x1005F130], xmm0   ; 清零 interval(double)
0x1000689A  c7 05 28 f1 05 10 00 00 00 00  mov [0x1005F128], 0    ; 清零 interval(ms)
0x100068A4  85 c0             test eax, eax
0x100068A6  78 11             js 0x100068B9                ; maxfps<0 → 用参考上限60
0x100068A8  83 3d ec 94 05 10 00  cmp [0x100594EC](vsync), 0
0x100068AF  74 0a             je 0x100068BB                ; vsync off → 上限=maxfps
0x100068B5  3b c1             cmp eax, ecx
0x100068B7  72 02             jb 0x100068BB                ; vsync on 且 maxfps<60 → 保持 maxfps
0x100068B9  8b c1             mov eax, ecx                 ; 否则钳到 60
0x100068BB-0x100068C5: 0<eax<=1000 才有效
0x100068C9  f3 0f 10 05 a0 f9 04 10  movss xmm0, [0x1004F9A0]   ; 1000.0（实测常量）
0x100068D8  f3 0f 5e c1       divss xmm0, xmm1             ; 1000/有效fps = 秒
0x100068E1  f3 0f 59 05 a4 f9 04 10  mulss xmm0, [0x1004F9A4]   ; ×10000.0（实测常量）
0x100068F3  a3 30 f1 05 10    mov [0x1005F130], eax        ; 64位 interval(0.1ms 单位)
0x10006903  a3 28 f1 05 10    mov [0x1005F128], eax        ; ★ interval(ms) = int(1000/fps)
```

**(c) 每帧门闸 `sub_10006AE0`（present 路径限帧）**：

```
0x10006AFA  a1 e8 94 05 10    mov eax, [0x100594E8]        ; maxfps
0x10006B02  78 1d             js 0x10006B21                ; maxfps<0 → 不做本限帧
0x10006B04  83 3d ec 94 05 10 00  cmp [0x100594EC](vsync), 0
0x10006B0B  0f 84 3e 01 00 00 je 0x10006C4F                ; vsync off → timeGetTime 限帧路径
0x10006B15  3b 05 48 ee 05 10 cmp eax, [0x1005EE48]
0x10006B1B  0f 82 2e 01 00 00 jb 0x10006C4F                ; maxfps<60 → 同上
        （vsync on 且 maxfps>=60 → 0x10006B21 起走 waitable-timer/QPC 支路，句柄在 [0x1005F138]）
0x10006C4F  8b 0d 28 f1 05 10 mov ecx, [0x1005F128]        ; interval(ms)
0x10006C55  85 c9             test ecx, ecx
0x10006C57  0f 84 33 01 00 00 je 0x10006D90                ; 0 → 不限帧，直接过
0x10006C5D  8b 15 38 f1 05 10 mov edx, [0x1005F138]        ; timer 句柄
0x10006C65  0f 84 fb 00 00 00 je 0x10006D66                ; 无句柄 → timeGetTime+Sleep 支路
0x10006C85  ff 15 44 e2 03 10 call [0x1003E244]            ; WaitForSingleObject(handle, 2×interval)
…（waitable timer 支路：SetWaitableTimer [0x1003E0EC] / QPC [0x1003E254]）
0x10006D66  ff 15 e8 e3 03 10 call [0x1003E3E8]            ; ★ now = timeGetTime()
0x10006D6C  8b 15 20 f1 05 10 mov edx, [0x1005F120]        ; ★ 上一帧放行时刻 last_t
0x10006D7A  2b ca             sub ecx, edx                 ; elapsed = now - last_t
0x10006D7C  a3 24 f1 05 10    mov [0x1005F124], eax        ; cur_t = now
0x10006D81  3b ce             cmp ecx, esi
0x10006D83  73 0b             jae 0x10006D90               ; elapsed >= interval → 放行
0x10006D87  03 d6             add edx, esi                 ; Sleep(interval - elapsed)
0x10006D8A  ff 15 f0 e0 03 10 call [0x1003E0F0]            ; ★ Sleep() —— 阻塞式限帧
```

IAT 槽位实测：`0x1003E3E8=WINMM!timeGetTime`、`0x1003E0F0=KERNEL32!Sleep`、`0x1003E244=KERNEL32!WaitForSingleObject`、`0x1003E0EC=KERNEL32!SetWaitableTimer`、`0x1003E254=KERNEL32!QueryPerformanceCounter`。

**(d) ★ 观测主全局：`[0x1005F120]`（RVA 0x5F120）每帧写入，共 3 处写入点**：

```
0x1001B00C  39 3d 28 f1 05 10  cmp [0x1005F128], edi       ; interval != 0 门控
0x1001B014  ff 15 e8 e3 03 10  call [0x1003E3E8]           ; timeGetTime
0x1001B01A  a3 20 f1 05 10     mov [0x1005F120], eax       ; ★ 写 last_t
（同形态：0x1001CD4B/0x1001CD51 与 0x1001D2D0/0x1001D2D2，三条渲染路径 d3d9/opengl/gdi 各一）
```

三处写入点紧跟 FPS 浮点统计（`0x1001AFF8-0x1001B004`）与 `EnterCriticalSection(0x1005EEF0)`——`[静态推断-中]`：分别是三条 renderer 的 present 完成簿记，d3d9 路径对应其一；确切是哪一条、写入在 present 前还是后，真机对照可一锤定音（见最小实验判据）。

### 3.3 观测协议（非注入，与 A 线既有 RPM 读 `[0xA8ED84]` 同类）

- 句柄：`OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ)`——只读，不改目标、无代码进入目标。
- **ddraw.dll DllCharacteristics=0x0140 → DYNAMICBASE（ASLR）开启 [静态读码]**：运行时 VA = 实际模块基址 + RVA；基址用 `EnumProcessModules`/Toolhelp 快照从外部枚举取得（同只读类操作）。
- 轮询 `ddraw_base+0x5F120`（last_t，dword）≈1kHz：**值变化一次 = cnc-ddraw 放行一帧**；变化值序列的差分 = 真实帧推进间隔序列。同时读 `+0x594E8`(maxfps,应=60)、`+0x5F128`(interval,应=16)、`+0x5EE48`(参考上限,应=60) 做自洽校验。
- **语义纪律（裁决）**：该通道测的是「cnc-ddraw 限帧放行层节拍」——它是 D3D9 Present 提交的**上游**节流闸。措辞必须为「限帧放行间隔」，不得写成「显示帧时间」。若游戏线程被 `EnumChildWindows+Sleep(30)` 阻塞，放行间隔会拉长 ⇒ 它对 A 线想测的「卡顿」**有真实灵敏度**；但它测不到 GPU/显示末端（那是候选1 的 DxgKrnl 显示层事件补位）。
- 与 ETW 互补关系：候选2 = 便宜的连续通道；候选1 = 一次性定谳「提交/显示」分层语义与内容更新疑点的仪器。推荐**两者同场景各采一段**互相校准（放行间隔 vs 提交间隔）。

### 3.4 最小实验脚本

`experiment\exp_rpm_framebeat.py`（Lead 真机批执行）：attach 指定 PID → 枚举模块定位 ddraw.dll 基址 → 校验 4 个全局自洽 → 1kHz 轮询 last_t → 按**裁决预注册指标**出报告：有效显示间隔的中位/p95/p99 + 每分钟超过 `max(50 ms, 3T)`（T=16 ms ⇒ 50 ms）的间隔次数 + 有效时长与样本数。脚本只读、不启动游戏（游戏由 Lead 单独启动后传入 PID）。

### 3.5 证据分级汇总

| 断言 | 等级 |
|---|---|
| maxfps 解析存 0x100594E8；键名/常量/IAT 槽位内容 | `[静态读码]`（capstone 输出留档） |
| 生效 maxfps=60 | `[本次实测]`(ini) + `[静态读码]`(双段 getter) |
| [0x1005F120] 每帧更新（3 写入点、interval 门控） | `[静态读码]` 写入点 + `[静态推断-中]`「每帧一次」语义 |
| 放行间隔可作卡顿灵敏仪器 | `[静态推断]`，真机 ABBA 后升级 |
| d3d9 路径对应哪个写入点 / 门闸在 Blt 还是 Flip vtable | `[未证]` |

---

## 4 · 候选 3：win32/DWM 通道 —— 判决 ③ 不可行（作为该进程帧率仪器）

逐个否证：

1. **`DwmGetCompositionTimingInfo`**：返回的是 **DWM 全局合成节奏**（ composition frame 信息，按 VidPn/桌面计），无进程归属参数；它测的是 DWM 的合成拍，不是 gamemd 的帧率。全屏独占情形 **DWM 不参与**，该 API 与游戏呈现完全脱钩；窗口化情形它只给系统合成节奏。**可用残余价值**：作裁决要求的 **T 参照**（参考间隔）与 ETW 试采时的显示端旁证——①级辅助用法，不是帧率仪器。
2. **`D3DKMT*`（D3DKMTGetPresentStats / D3DKMTQueryStatistics / D3DKMTWaitForVerticalBlankEvent 等）**：`D3DKMTGetPresentStats` 需要 **hDevice**（进程内 D3D 设备句柄，跨进程无效）；`WaitForVerticalBlankEvent` 是同步原语不是统计查询。从外部进程拿不到目标进程的设备句柄 ⇒ **须注入/挂进目标进程才能调用** = ②类代价（违背本卡非注入前提），作为候选 3 判 ③。
3. **`IDirect3DSwapChain9::GetPresentStatistics`**（D3D9 provider EventID 9 的来源）：同理必须持有效 swapchain 接口指针 ⇒ 只能在目标进程内调用 = 注入域。且 D3D9 文档层面对 FSE/部分 swap effect 支持有限。判 ③。
4. **交叉印证**：r02 `LEAD_FINDING_counter_is_32ms_timer.md` §4 已判「D3D9 query 帧统计不可行」——本卡维持该否证并补全机制（句柄进程内绑定是根因）。

**判决：③ 不可行（非注入前提下无进程级帧率通道）；DwmGetCompositionTimingInfo 降格保留为 T 参照工具。**

---

## 5 · 对裁决 Q3 的逐条对答（结论收口）

| 裁决要求 | 本卡回答 |
|---|---|
| 不预设 D3D9 Present 可用 | 已静态钉死后端：d3d9.dll 动态加载 + renderer=direct3d9（§1.2）；可恢复链路存在，不判 ③ |
| 事件归属三问 | 预答 + 试采判据写死（§2.2），答不出即停 |
| submit/complete/displayed 不可混称 | 三层语义表（§2.2），候选2 通道措辞定为「限帧放行间隔」 |
| Present ≠ 画面内容更新 | 全文照录纪律；提交/放行节奏稳定 ≠ 画面流畅 |
| ABBA 扰动校准 + 独立画面参照 | 本卡离线不做采集；两份最小实验脚本已内嵌指标与对照要求，扰动预算（0.5pp / 10% / 1次每分 / 零丢失）写入脚本文档头；**无独立画面参照时试采只产「开启 ETW 时的节奏」，不得闭合「原本是否卡」** |
| 指标预注册 | 中位/p95/p99 + 每分钟超 max(50ms,3T) 次数 + 有效时长/样本数，已写入 exp 脚本输出 |

## 6 · 前人工作引用（不重复劳动声明）

- r02 两路静态扫描失败：本卡**引用其失败判据**（`inc [abs]` 法 + 线性 sweep 漏检）并定位为方法不匹配，未重做绝对地址 inc 扫描。
- 「`[0xA8ED84]` 是 32ms 定拍、测不了卡顿」「D3D9 query 帧统计不可行」：引用，不重证。
- 帧推进函数 `0x55D360` / `0x608070` UI 路径：引用为「放行间隔会被 UI 阻塞拉长」的机制背景。

## 7 · 推荐下一步（最小实验，按序）

1. **候选2 试采**（最便宜）：`exp_rpm_framebeat.py` attach 正在跑的 gamemd，60–240 s，验证 last_t 差分节奏 ≈16–17 ms、自洽校验 4 全局、看菜单/失焦时放行间隔拉长形态。
2. **候选1 ETW 短试采**：`exp_etw_short.cmd` 2–5 分钟，回答裁决三问；与候选2 同场景各一段互校。
3. ABBA ≥5 区组扰动校准 + 独立画面参照到位后，才允许按裁决把 ETW 纳入 A 线正式仪器。
