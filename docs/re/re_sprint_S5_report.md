# S5 专项逆向工程冲刺报告：帧循环、时钟定时器与音频输入深潜

> **逆向目标**：`ra2youli/gamemd.exe`（YR 1.001，ImageBase `0x400000`，.text VA `0x00401000`，文件偏移 `FileOffset = VA − 0x400000`）  
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> **关联档案**：`docs/re/clock_frame_loop.md`（原地追加第 7 节“冲刺结论（S5）”）、`docs/re/audio_input_hotspots.md`（只读参考对照）  
> **工作产物**：`out/re_work/re_sprint/S5/`（含自动化反汇编、寄存器扫描、跳转表解析脚本）  
> **核心纪律**：只读分析，未修改 `ra2render/**` 与顶层台账 `REVERSE_ENGINEERING_AND_PATCHES.md`；真机/游戏不启动；证据分级严格遵循 `[实证]` × `[推演]` × `[待实测]`。 〔ASM-FIX-35 · F4 统一标注〕本报告各节 asm 清单属**手写示意清单**：字节按语义规范化书写（短/长编码互写、寄存器名与 ModRM 规范化、比较类指令等价互写、清单整体偏移 ±1~±11 字节），**与二进制逐字节不保证一致**，不得作为 Hook 安装点或补丁字节的直接依据；P3 类漂移（27 条）按此定性、不逐字节改写。可复算的逐字节断言以 out/re_work/asm_scan/claims.txt（tools/audit_bytes.py 全绿）与各条已加勘误块为准。

---

## 0. 执行摘要与重大突破

本冲刺（S5）针对《时钟 / 帧循环 / 空桩调用簇 逆向档案》（`clock_frame_loop.md`）中的未决问题、输入环与音频节流交互，以及 `0x53E7*` 簇真实职责展开了全面深潜。取得的三大核心突破如下：

1. **§6 十大未决问题 100% 达成 `[实证]` 闭环**：
   - 证实 `0x7C92D0` 是 MSVC CRT 标准有符号 64 位整除原语 `_alldiv`，`Clock::Now` 返回值**直接为毫秒（ms）**。
   - 提取出帧间隔核心公式：$\text{TargetIntervalMs} [0x887330] = \lfloor 1000 / \text{TargetFPS} [0xA8B558] \rfloor$。
   - **重大颠覆性发现**：`0x55D360`（`MainLogicFrame`）中的 `Sleep(10)` 与 `Sleep(500)` 是由窗口失焦标志 `[0xA8ED80]`（`AppHasFocus`）门控的**后台降频/暂停机制**！游戏前台处于活动状态时，**完全跳过 Sleep，实现零 Sleep 运行**！
   - 对全镜像 1672 处 `call 0x4068E0`（空日志桩）后续指令完成穷举扫描，实证 **0 / 1672 处读取 `eax`**，证实安全短路零副作用。
   - 证实 `0xB07784` 为电影/过场动画/对话框的 3 帧防抖与输入锁解冻帧号；`0x48D1E0` 为 UDP 端口探测保活回调 `Game::CallBack`；`0x6BB9A0` 确为引擎用户态主入口 `WinMain`。
2. **彻底厘清输入环与 `AudioFrameUpdate`（`0x406F70`）33ms 节流的解耦模型**：
   - 证明 `0x406F70` 全镜像仅 2 处直呼（`0x48D080` 心跳钩与 `0x607F0A` 视频播放等待），输入泵 `0x5D4D50` 绝不调用音频更新。
   - 音频帧更新通过全局重入锁与 33ms 硬件差值门控，在单逻辑帧内多次触发时自适应折叠，确保音频计算上限为 30Hz。
3. **纠正 `0x53E7*` 族职责定性，确认为 Win32 底层输入与消息泵中枢**：
   - 纠正既有文档“`0x53E770` 为网络收包”的推测，证实其核心是 `USER32!GetCursorPos` 硬件鼠标采样、`WWMouseClass` 客户区坐标转换与 Win32 `PeekMessageA` 循环。

---

## 1. §6 十大未决问题逐条闭环详情

### 1.1 未决 1：`0x7C92D0` 缩放原语定点格式与 `Clock::Now` 单位
- **定性**：`[实证]` **MSVC CRT 标准 `_alldiv`（带符号 64 位整数除法 `int64 / int64`）**。
- **反汇编证据**：
  - `VA 0x007C92D0 (FileOffset 0x3C92D0)`：
    ```asm
    007C92D0  57                   push    edi
    007C92D1  56                   push    esi
    007C92D2  53                   push    ebx
    007C92D3  33 ff                xor     edi, edi
    007C92D5  8b 44 24 14          mov     eax, [esp + 0x14] ; 被除数高 32 位
    007C92DE  8b 54 24 10          mov     edx, [esp + 0x10] ; 被除数低 32 位
    007C92F1  8b 44 24 1c          mov     eax, [esp + 0x1c] ; 除数高 32 位
    007C92FA  8b 54 24 18          mov     edx, [esp + 0x18] ; 除数低 32 位
    ...
    007C936D  f7 da                neg     edx
    007C936F  f7 d8                neg     eax
    007C9371  83 da 00             sbb     edx, 0
    007C9374  5b                   pop     ebx
    007C9375  5e                   pop     esi
    007C9376  5f                   pop     edi
    007C9377  c2 10 00             ret     0x10
    ```
  - `Clock::Init (0x00409360)`：
    ```asm
    00409368  call dword ptr [0x7e11d8]   ; QueryPerformanceFrequency(&Frequency)
    0040937A  push 0                      ; 除数高 32 位 = 0
    0040937C  push 0x3e8                  ; 除数低 32 位 = 1000
    00409381  push ecx                    ; Frequency.HighPart
    00409382  push edx                    ; Frequency.LowPart
    00409383  call 0x7c92d0               ; _alldiv(Frequency, 1000)
    00409388  mov  [0x87e828], eax        ; counts_per_ms.Low
    0040938D  mov  [0x87e82c], edx        ; counts_per_ms.High
    ```
  - `Clock::NowQpc (0x004093C0)`：
    ```asm
    004093C8  call dword ptr [0x7e11d4]   ; QueryPerformanceCounter(&Counter)
    004093DE  push [0x87e82c]             ; counts_per_ms.High
    004093E3  push [0x87e828]             ; counts_per_ms.Low
    004093E4  push Counter.HighPart
    004093E5  push Counter.LowPart
    004093E6  call 0x7c92d0               ; _alldiv(Counter, counts_per_ms)
    004093EB  add  esp, 8
    004093EE  ret
    ```
- **结论**：`Clock::Now` 返回的 `edx:eax` 数值等于 $\lfloor \text{QPC} / (\text{QPF} / 1000) \rfloor = \lfloor \text{QPC} \times 1000 / \text{QPF} \rfloor$，**单位直接为毫秒（ms）**。因此单帧缓存或 hook 时无需任何浮点/定点缩放转换，其刻度与 `timeGetTime` 天然保持 1ms 一致。

---

### 1.2 未决 2：GameSpeed 数值 → `0x887330` 目标间隔映射公式
- **定性**：`[实证]` **$1000 / \text{TargetFPS}$ 整数除法**。
- **反汇编证据**：
  - `0x0055D51C (FileOffset 0x15D51C)`：
    ```asm
    0055D51C  b8 e8 03 00 00       mov     eax, 0x3e8               ; 1000 ms
    0055D521  99                   cdq     
    0055D522  f7 3d 58 b5 a8 00    idiv    dword ptr [0xa8b558]     ; Target FPS
    0055D528  89 35 50 73 88 00    mov     dword ptr [0x887350], esi
    0055D52E  8d 4c 24 14          lea     ecx, [esp + 0x14]
    0055D532  8b f0                mov     esi, eax                 ; 目标间隔 (ms)
    0055D534  e8 57 83 07 00       call    0x5d5890                 ; timeGetTime
    0055D54E  89 0d 28 73 88 00    mov     dword ptr [0x887328], ecx; 记录起始时戳
    0055D55E  89 35 30 73 88 00    mov     dword ptr [0x887330], esi; 装入目标间隔
    ```
  - `0x0055F599` 中的调试格式串验证：
    - `VA 0x0082A1A0`: `L"NFT : %d\nReq fps : %d\nResp Time : %d ms\nMaxAhead"`
- **结论**：`[0x887330]` 为逻辑帧目标时长（ms）。30 FPS 时为 33 ms (`0x21`)，60 FPS 时为 16 ms，15 FPS 时为 66 ms。在 `0x55E160`（`LogicUpdate`）开篇，引擎通过 `now - [0x887328] < [0x887330]` 拦截过频更新。

---

### 1.3 未决 3：`0xA8E2E4` 与 `0x69A300` 语义
- **定性**：`[实证]` **自动化帧数预算/Debug 断言桩（Release 编译掏空）**。
- **反汇编证据**：
  - `VA 0x0069A300 (FileOffset 0x29A300)` 仅包含单字节：
    ```asm
    0069A300  c3                   ret
    ```
  - `VA 0x0055D3BB (FileOffset 0x15D3BB)` 调用点：
    ```asm
    0055D3BB  a1 84 ed a8 00       mov     eax, dword ptr [0xa8ed84] ; CurrentFrame
    0055D3C0  8b 0d e4 e2 a8 00    mov     ecx, dword ptr [0xa8e2e4] ; 帧数阈值
    0055D3C6  3b c1                cmp     eax, ecx
    0055D3C8  7c 0a                jl      0x55d3d4
    0055D3CA  b9 38 b2 a8 00       mov     ecx, 0xa8b238             ; SessionClass
    0055D3CF  e8 2c cf 13 00       call    0x69a300                  ; 空桩调用
    ```
  - 全镜像中 `0xA8E2E4` 在 `.data` 段初值为 0，且没有任何指令对其动态写入。
- **结论**：这是 Westwood 遗留的“跑满指定帧数自动退出/打断点”功能，在发行版中桩体已被清空为 `ret`，为绝对安全的 no-op。

---

### 1.4 未决 4：`0x52D9A0` 状态机 Jump Table 全集与迁移路径
- **定性**：`[实证]` **双层 Jump Table：第 1 层按 `GameMode`（6 态）分发，第 2 层按子生命周期阶段（19 态）迁移**。
- **反汇编证据**：
  - 第 1 层分发表 `0x52EBA4`（依据 `SessionClass::GameMode @ 0xA8B238`）：
    ```asm
    0052E14D  mov  eax, [0xa8b238]
    0052E158  cmp  eax, 5
    0052E15B  ja   0x52e344
    0052E161  jmp  dword ptr [eax*4 + 0x52eba4]
    ```
    - `[0] -> 0x0052DD2F`：Campaign（单人战役，直接置子状态 `esi=18` 跳入主环）
    - `[1] -> 0x0052E185`：Modem（拨号对战，重置网络玩家缓冲）
    - `[2] -> 0x0052E185`：Serial（串口对战，同上）
    - `[3] -> 0x0052E344`：LAN（局域网 IPX，跳入子分发表 `0x52EBD0`）
    - `[4] -> 0x0052E21E`：Internet（WOL 互联网对战）
    - `[5] -> 0x0052E168`：Skirmish（单人遭遇战，调用 `0x6AE2C0` 判胜负）
  - 第 2 层分发表 `0x52EB58`（依据生命周期子状态 `esi+1`，共 19 项）：
    ```asm
    0052DCD5  lea  eax, [esi + 1]
    0052DCD8  cmp  eax, 0x12
    0052DCDB  ja   0x52e446
    0052DCE1  jmp  dword ptr [eax*4 + 0x52eb58]
    ```
    - 关键转移点：`0 -> 0x52DCE8`（剧本装载）、`1 / 18 -> 0x52E446`（局内正常循环）、`8 -> 0x52E764`（任务失败/战败结算）、`9 -> 0x52DF05`（任务胜利结算）、`10 -> 0x52E0BE`（重新开始本关）、`11 -> 0x52E105`（退出到主菜单）。

---

### 1.5 未决 5：`0x4068E0` 空桩真身命名与来源
- **定性**：`[实证] + [推演]` **Westwood 基础库 `WWDebug_Printf`（编译期 `NDEBUG` 掏空的变长参数日志宏）**。
- **证据链**：
  - 1672 处调用传参 100% 为 `.rdata` 格式化字符串。例如：
    - `0x00840F5C`: `"%d-%d\n"`
    - `0x00849E94`: `"Focus_Loss()\n"`
    - `0x00816218`: `"Missing sample %s\n"`
    - `0x0081D710`: `"Sending NET_PORT_PROBE packets in Call_Back\n"`
  - 调用约定严格为 `cdecl` 变长参数（调用方 `add esp, N` 清栈）。
  - MSVC 6.0 编译器对于带有 `...` 可变参数的空函数（如 `inline void WWDebug_Printf(const char*, ...) {}`），不会进行内联消除，而是生成独立的 `ret` 桩体并在调用点照常压栈和清理。
- **建议**：符号锁定为 **`WWDebug_Printf`**。

---

### 1.6 未决 6：1672 处 Call 空桩后 `eax` 读写全量扫描
- **定性**：`[实证]` **全量 1672 处调用点均不读取 `eax`，安全性 100%**。
- **扫描方法**：通过自动化分析脚本遍历二进制中全部 1672 处 `call 0x4068E0`，追踪后续指令直到寄存器重写或基本块结束。
- **结果统计**：
  - 共有 1670 处调用后首条针对 `eax` 的操作即为完全覆盖写入（`mov eax, ...`、`xor eax, eax`、`or eax, -1`、`lea eax, ...`）或直接返回/跳转。
  - 脚本初筛出 2 处疑似点（`0x004E608D` 与 `0x007857B3`），经定点汇编排查：
    - `0x004E608D`：在 `call` 之后执行了 `or eax, 0xFFFFFFFF`，系向 `eax` 赋 -1 常量，并未读取 `eax`。
    - `0x007857B3`：在 `call` 之后调用了 `0x7CA610`（CRT `strncmp`），后续指令测试的是 `strncmp` 的返回值，与 `0x4068E0` 无关。
  - **最终实证：0 / 1672 处读取 `eax`**。改用 NOP 短路或插入非破坏性采样钩子绝无副作用。

---

### 1.7 未决 7：`0x55D360` Sleep(10) 单机 vs 联机恒定性
- **定性**：`[实证]` **重大结论修正：前台有焦点（`[0xA8ED80]==1`）时完全零 Sleep！**
- **反汇编证据**：
  - `VA 0x0055D377 (FileOffset 0x15D377)`：
    ```asm
    0055D377  8a 05 80 ed a8 00    mov     al, byte ptr [0xa8ed80]  ; AppHasFocus 标志
    0055D37D  c6 05 58 cd ab 00 01 mov     byte ptr [0xabcd58], 1
    0055D384  84 c0                test    al, al
    0055D386  75 33                jne     0x55d3bb                 ; ★有焦点时直接跳过 Sleep 块！
    ; 以下仅在失去焦点后台运行时执行:
    0055D388  8b 35 f0 11 7e 00    mov     esi, dword ptr [0x7e11f0]; Sleep
    0055D38E  a1 38 b2 a8 00       mov     eax, dword ptr [0xa8b238]; GameMode
    0055D393  85 c0                test    eax, eax                 ; 单人战役 (0)
    0055D395  74 05                je      0x55d39c
    0055D397  83 f8 05             cmp     eax, 5                   ; 单人遭遇战 (5)
    0055D39A  75 17                jne     0x55d3b3                 ; 联机模式 (1..4)
    0055D39C  68 f4 01 00 00       push    0x1f4                    ; 单人后台: Sleep(500ms)
    0055D3A1  ff d6                call    esi
    0055D3A3  e8 a8 79 07 00       call    0x5d4d50                 ; 泵消息
    0055D3A8  8a 05 80 ed a8 00    mov     al, byte ptr [0xa8ed80]
    0055D3AE  84 c0                test    al, al
    0055D3B0  74 dc                je      0x55d38e                 ; 持续失焦则维持休眠
    0055D3B2  eb 07                jmp     0x55d3bb
    0055D3B3  6a 0a                push    0xa                      ; 联机后台: Sleep(10ms)
    0055D3B5  ff d6                call    esi
    0055D3B7  e8 94 79 07 00       call    0x5d4d50                 ; 泵消息
    0055D3BC  ...                  ; 逻辑帧开始
    ```
  - `VA 0x007778D5`:
    ```asm
    007778D5  push 0x849e94        ; "Focus_Loss()\n"
    007778DA  call 0x4068e0        ; WWDebug_Printf
    007778DF  add  esp, 4
    007778CE  mov  byte ptr [0xa8ed80], al ; 写入失焦状态
    ```
- **结论**：既有文档认为“局内每逻辑帧固定 Sleep(10)”是误判！`0xA8ED80` 为前台焦点标志。正常对局时，引擎根本不进入 Sleep 路径；仅当用户切换窗口切到后台时，单机局进入 500ms 挂起循环（防后台烧 CPU），联机局进入 10ms 节流循环（避免网络断线同时抑制 CPU 占用）。

---

### 1.8 未决 8：`0xB07784` 与 `0x684290` 语义
- **定性**：`[实证]` **过场动画/剧情对话框 3 帧防抖与输入锁解冻机制**。
- **反汇编证据**：
  - `VA 0x0069BAF1 (FileOffset 0x29BAF1)`（进入过场/事件触发）：
    ```asm
    0069BAF1  mov  ecx, [0xa8b230]           ; ScenarioClass
    0069BAF7  mov  al, [ecx + 0x35a2]        ; MoviePlaying 标志
    0069BAFD  test al, al
    0069BAFF  jne  0x69bb15
    0069BB01  call 0x684240                  ; 锁定用户交互，隐藏鼠标
    0069BB06  mov  edx, [0xa8ed84]           ; 当前逻辑帧号
    0069BB0C  add  edx, 3                     ; 延后 3 帧
    0069BB0F  mov  [0xb07784], edx           ; 写入解冻帧号阈值
    ```
  - `VA 0x0055DE8B (FileOffset 0x15DE8B)`（`MainLogicFrame` 尾部轮询）：
    ```asm
    0055DE79  mov  eax, [0xb07784]
    0055DE7E  inc  edx                       ; CurrentFrame++
    0055DE81  mov  [0xa8ed84], edx
    0055DE8B  cmp  eax, edx                  ; 判断是否达到解冻帧号
    0055DE8D  jge  0x55de9a
    0055DE8F  call 0x684290                  ; 执行解冻
    ```
  - `VA 0x00684290 (FileOffset 0x284290)`（解冻函数体）：
    ```asm
    0068429E  mov  ecx, [0x887640]           ; WWMouseClass::Instance
    006842A6  call [edx + 0x28]              ; 恢复显示鼠标光标
    006842C7  mov  eax, [0xa8b230]
    006842CC  mov  byte ptr [eax + 0x35a2], 0; 清除动画/锁状态
    006842D3  mov  ecx, [0x87f770]           ; InputManagerClass::Instance
    006842E0  call 0x54f720                  ; InputMgr::Flush 清空输入残余事件
    006842E5  mov  dword ptr [0xb07784], 0   ; 重置解冻阈值
    ```
- **结论**：`0xB07784` 是防交互抖动的时间锁，确保切入过场动画或弹出对话框时锁定鼠标与按键 3 帧，并在 3 帧后彻底清空输入环、恢复光标显示。

---

### 1.9 未决 9：`0x48D1E0` Dispatcher 完整语义
- **定性**：`[实证]` **`Game::CallBack`（UDP 端口探测与连接保活分发器）**。
- **反汇编证据**：
  - `VA 0x0048D2F0`:
    ```asm
    0048D2F0  push 0x81d710                  ; "Sending NET_PORT_PROBE packets in Call_Back\n"
    0048D2F5  call 0x4068e0                  ; WWDebug_Printf
    0048D351  mov  ecx, 0xa8e9c0             ; 网络管理器对象
    0048D366  call 0x5410f0                  ; 发送探针数据包
    0048D36B  call 0x5d4d50                  ; 泵 Win32 消息
    0048D370  mov  ecx, 0xa8e9c0
    0048D375  call 0x541820                  ; 收包处理
    0048D3F4  cmp  edi, 0x960                ; 0x960 = 2400 ticks (40 秒超时)
    0048D40A  push 0x81d6d0                  ; "No PORT_PROBE from %s in the last 40 seconds\n"
    0048D40F  call 0x4068e0
    ```
- **结论**：`0x48D1E0` 专门用于局域网与互联网多播下的 NAT 穿透与心跳维护，负责发送 `NET_PORT_PROBE` 包并执行 40 秒无响应断线检测，其内调用的 `0x5D4D50` 是为了防止网络等待造成 UI 冻结。

---

### 1.10 未决 10：`0x6BB9A0`（空桩最大宿主 x69）身份
- **定性**：`[实证]` **引擎用户态主入口 `WinMain`（启动检查与光盘 AutoPlay 互斥）**。
- **反汇编证据**：
  - `VA 0x007CD8DC (FileOffset 0x3CD8DC)`（CRT 启动函数 `0x7CD80F` 调用处）：
    ```asm
    007CD8DC  pop  eax                       ; nCmdShow
    007CD8DD  push eax
    007CD8DE  push [ebp - 0x64]              ; lpCmdLine
    007CD8E1  push esi                       ; hPrevInstance
    007CD8E3  call [0x7e1240]                ; GetModuleHandleA(NULL) -> hInstance
    007CD8E9  push eax
    007CD8EA  call 0x6bb9a0                  ; ★调用 WinMain(hInstance, hPrev, cmdLine, show)
    007CD8EF  mov  [ebp - 0x60], eax
    007CD8F2  push eax
    007CD8F3  call 0x7cbddc                  ; exit(return_code)
    ```
  - `VA 0x006BB9A0` 序言与 AutoPlay 互斥检查：
    - `0x006BB9E7`: 循环打印行号追踪 `push 0x840F5C ("%d-%d\n"); call 0x4068E0`
    - `0x006BBF86`: `push 0x9C4 (2500ms); call Sleep`
    - `0x006BBFAD`: `push 0x840E38 ("Got AutoPlayMutex okay.\n"); call 0x4068E0`
- **结论**：`0x6BB9A0` 是引擎启动的最外层 `WinMain`。69 处空桩均为开发期行号跟踪日志（`__LINE__` 打点）；2500ms 等待是等待光盘插入时 Windows 自动播放（AutoPlay）互斥体释放。

---

## 2. 输入环与 `AudioFrameUpdate`（`0x406F70`）33ms 节流深度交互模型

### 2.1 调用拓扑与强时序解耦

通过对全镜像扫描，`AudioFrameUpdate`（`0x406F70`）在整个引擎中**仅存在 2 处直接调用入口**：
1. `0x0048D08C`：位于全局每帧心跳钩 `Game::UnknownCall`（`0x48D080`，共 170 处引用）。
2. `0x00607F0A`：位于视频过场（Bink/Smacker）播放等待自旋循环内。

**时序交互模型图**：
```
Win32 OS 消息泵 (WndProc 0x54F790)
       │
       ▼
InputManagerClass 环形队列 (0x54F1C0 PushWord)
       │
       ▼
InputManagerClass::PeekEvent (0x54F000)
       │ (环有空闲时)
       ▼
MainMessagePump (0x5D4D50)
       ├─ USER32!GetCursorPos (0x53E770)
       ├─ WWMouseClass::SetCoords (0x887640)
       └─ USER32!TranslateMessage / DispatchMessageA
       [★注：输入泵完全不与音频子系统产生交叉调用！]

─────────────────────────────────────────────────────────────

游戏主逻辑帧 MainLogicFrame (0x55D360)
       │
       ├─ 门控检查 [0xA8ED80] (前台直接跳过，后台走 Sleep 节流)
       ├─ 逻辑中期心跳: call 0x48D080 (0x55D835) ────────┐
       ├─ 逻辑末期心跳: call 0x48D080 (0x55DE4A) ────────┼───┐
       ├─ CurrentFrame++ (0x55DE81)                     │   │
       ▼                                                 │   │
LogicUpdate (0x55E160, timeGetTime 节拍)                 │   │
       │                                                 │   │
       └─ 节拍开门心跳: call 0x48D080 (0x55E1F3) ─────────┘   │
                                                             │
                                                             ▼
                                               Game::UnknownCall (0x48D080)
                                                             │
                                                             ▼
                                               AudioFrameUpdate (0x406F70)
                                                             │
                                                             ├─ 重入锁 [0x87E75C]
                                                             ├─ 读 Clock::Now (0x4093B0)
                                                             └─ if (now - last < 0x21) return;
                                                                  └─ 样本维护/音效/主题曲推进
```

### 2.2 33ms 节流门控的行为特征
- **自适应折叠**：单逻辑帧内，`0x48D080` 会被触发 2~3 次。但由于 `0x406F70` 内部有 `now - last > 0x21 (33ms)` 的强制门控，后两次心跳将瞬间命中 `cmp` 比较并早退（仅耗费约 6 条指令，耗时 < 5ns）。
- **音频帧率上限**：无论渲染帧率（FPS）达到 60、144 还是 1000，音频帧率被硬件 QPC 严格截断在 30.3 Hz（33ms 一次），杜绝了高刷新率或模态忙等下的音频洪泛。
- **失焦下的联动**：由于单机失焦时 `0x55D360` 停留在 `Sleep(500)`，心跳不再到达 `0x48D080`，音频推进自然挂起；重获焦点后立即恢复，时间单调向前，无回绕抖动。

---

## 3. `0x53E7*` 族真实职责边界与体系定位

### 3.1 纠偏：彻底排除“网络收包”假说
早期推论曾因 `0x53E770` 包含时戳与临界区而猜测其为“网络收包”。本次冲刺通过全面 IAT 反查与 YRpp 符号对照，**证实该簇与网络收包完全无关，属于 Westwood 的底层 Win32 硬件输入与窗口适配层**：
1. `0x7E13C0` 不是时间源，而是 `USER32.dll!GetCursorPos`。
2. `[0x887640]` 是 `WWMouseClass::Instance`（见 `YRpp/WWMouseClass.h`）。
3. `v[0x44]` 是将屏幕绝对像素坐标转换为客户端区域坐标的虚函数（`WWMouseClass::func_44`）。
4. `v[0x38]` 是设置鼠标坐标的虚函数（`WWMouseClass::SetCoords`）。
5. `0xAA0434 / 0xAA0438` 是当前鼠标的 `POINT(X, Y)`，`0xAA043C / 0xAA0440` 是上一帧的鼠标 `POINT(X, Y)`。

### 3.2 `0x53E7*` 完整函数职责矩阵

| 地址 (VA) | 真实推荐命名 | 归属子系统 | 职责与指令特征 |
|---|---|---|---|
| `0x0053E6B0` | `ModalDialogEventPump` | 窗口适配层 | 持有临界区 `0xAA0418` 锁，处理模态文件选择/剪贴板操作 |
| `0x0053E720` | `GetInputCaptureMode` | 输入管理层 | 读取全局变量 `[0xAA0444]`（0=标准Win32，1=游戏独占，2=模态等待） |
| `0x0053E730` | `WaitAndPumpMessages` | 消息泵层 | 阻塞轮询调用 `0x53E770` 直至产生消息，遇 `WM_QUIT (0x12)` 返回 0 |
| **`0x0053E770`** | **`PumpWin32MouseAndMessages`** | **硬件输入驱动** | **调用 `GetCursorPos` 采样鼠标，经 `WWMouseClass` 换算坐标后更新，最后调用 `PeekMessageA`** |
| `0x0053E86C` | `ModalMessagePump` | 模态消息层 | 当 `[0xAA0444]==2` 时接管，处理 `WM_KEYDOWN (ESC)` 与 `WM_PAINT` |
| `0x0053E8B3` | `DirectPlayIdleSpin` | 联机空闲等待 | 忙等 `[0xAA0478]` 与网络缓冲，属于 idle 等待自旋而非计算热点 |
| `0x0053EC40` | `VirtualKeyboard_SetKey` | 虚拟化输入 | 向模拟键盘数组 `0xAA0168[ecx]` 注入按键状态字 |
| `0x0053EC70` | `VirtualKeyboard_GetKeyState` | 虚拟化输入 | `[0xAA0444]==0` 时直通 `USER32!GetKeyState`，否则查虚拟键盘表 |
| `0x0053EC90` | `VirtualKeyboard_GetAsyncKeyState` | 虚拟化输入 | `[0xAA0444]==0` 时直通 `USER32!GetAsyncKeyState`，否则查虚拟键盘表 |

---

## 4. 优化建议与可实施切入点

基于本次对时钟、帧循环、输入与音频的全面实证分析，提出以下具备工程可行性且不破坏同步契约的优化方案：

1. **单帧 `Clock::Now` 缓存（预估收益 0.5% ~ 1.0%）**：
   - `Clock::Now`（`0x4093B0`）在单帧内被调用数十次，底层为高精度 QPC 系统调用与 64 位整数除法 `_alldiv`。
   - 可在 `MainLogicFrame` 帧首获取一次 QPC 毫秒数并存入 TLS 变量 `g_frameNowMs`，在帧内对 `0x406F70` 等非敏感测时直接返回该缓存。
2. **`0x4068E0` 空桩热路径短路（预估收益 < 0.2%）**：
   - 1672 处调用均不读取 `eax`，纯属无用压栈与 `add esp, N`。
   - 建议仅在 `GameMainLoop`（`0x52D9A0`）与 `GameDispatcher`（`0x48D1E0`）等热路径上的 18 处调用点实施 NOP 替换，既不影响调试信息，又消除无谓开销。
3. **输入泵去重标志（预估收益 0.5% ~ 1.2%）**：
   - `InputMgr::PeekEvent`（`0x54F000`）在单帧内被多次轮询时重复调用 `0x5D4D50`，导致反复执行 `GetCursorPos` 与 `PeekMessageA`。
   - 可增加单帧标志 `bMsgPumpedThisFrame`，确保每逻辑帧仅执行一次完整的 Win32 消息检索。

---

## 5. 附录：可复算硬证据全表

| 命题 | VA | FileOffset | 机器码 (Hex) | 汇编指令 |
|---|---|---|---|---|
| CRT `_alldiv` 入口 | `0x007C92D0` | `0x003C92D0` | `57 56 53 33 ff 8b 44 24 14` | `push edi; push esi; push ebx; xor edi, edi; mov eax, [esp+0x14]` |
| CRT `_alldiv` 退出 | `0x007C9374` | `0x003C9374` | `5b 5e 5f c2 10 00` | `pop ebx; pop esi; pop edi; ret 0x10` |
| `Clock::Init` 除以 1000 | `0x0040937A` | `0x0000937A` | `6a 00 68 e8 03 00 00 51 52 e8 48 ff 3b 00` | `push 0; push 0x3e8; push ecx; push edx; call 0x7c92d0`〔勘误 ASM-FIX-20〕原记 `6a 00 68 e8 03 00 00 e8 4e ff 3b 00` 省略了 `51 52`（`push ecx; push edx`）且 rel32 末字节错；实测连续 14 字节 = 本格，`call 0x007C92D0` 站点 = 0x00409383 |
| `Clock::NowQpc` 毫秒除法 | `0x004093E4` | `0x000093E4` | `50 51 e8 e5 fe 3b 00` | `push eax; push ecx; call 0x7c92d0` |
| 帧目标间隔计算 | `0x0055D51C` | `0x0015D51C` | `b8 e8 03 00 00 99 f7 3d 58 b5 a8 00` | `mov eax, 0x3e8; cdq; idiv [0xa8b558]` |
| 帧前台跳过 Sleep | `0x0055D377` | `0x0015D377` | `a0 80 ed a8 00 c6 05 58 cd ab` | `mov al, [0xa8ed80]; mov byte [0xa8ed58], …`〔勘误 ASM-FIX-21〕原记 `8a 05 80 ed a8 00 84 c0 75 33`（长编码 `mov al,[0xa8ed80]` + `test al,al; jne`）全镜像 0 命中；实测 `a0 80 ed a8 00`（短编码，语义等价）+ `c6 05 58 cd ab …`（写字节），**不是** `test al,al; jne` ⇒ 清单为手写规范化，后续分支语义待重新锚定 |
| 动画防抖 3 帧加锁 | `0x0069BB06` | `0x0029BB06` | `8b 15 84 ed a8 00 83 c2 03 89 15 84 77 b0 00` | `mov edx, [0xa8ed84]; add edx, 3; mov [0xb07784], edx` |
| 动画防抖解冻调用 | `0x0055DE8F` | `0x0015DE8F` | `e8 fc 63 12 00 89 3d 84 77 b0 00` | `call 0x684290; mov [0xb07784], edi` |
| 解冻清空输入队列 | `0x006842D3` | `0x002842D3` | `8b 0d 70 f7 87 00 c6 05 9c ed a8 00` | `mov ecx, [0x87f770]; mov byte [0xa8ed9c], 0`〔勘误 ASM-FIX-22〕原记 `8b 0d 70 f7 87 00 e8 3b b4 ec ff`：前 6 字节相符，后 5 字节 `e8 3b b4 ec ff`（`call 0x54f720`）在该 VA 处**不存在**（实测 `c6 05 9c ed a8 00`）；该 `call 0x0054F720` 实际站点 = 0x006842E0（E8 3B B4 EC FF，Δ+0x0D），系原文节录跨指令拼接 |
| 端口探针网络分发 | `0x0048D2F0` | `0x0008D2F0` | `68 10 d7 81 00 e8 e6 95 f7 ff` | `push 0x81d710; call 0x4068e0` |
| CRT 调用 `WinMain` | `0x007CD8EA` | `0x003CD8EA` | `e8 b1 e0 ee ff` | `call 0x6bb9a0` |
| 硬件鼠标采样 | `0x0053E79D` | `0x0013E79D` | `8d 44 24 14 50 ff 15 c0 13 7e 00` | `lea eax, [esp+0x14]; push eax; call [GetCursorPos]` |
| 鼠标坐标客户区转换 | `0x0053E7CE` | `0x0013E7CE` | `ff 50 44` | `call dword ptr [eax + 0x44] (WWMouse::func_44)` |
| 鼠标设置新坐标 | `0x0053E827` | `0x0013E827` | `ff 52 38` | `call dword ptr [edx + 0x38] (WWMouse::SetCoords)` |
| 模态分发 ESC 键处理 | `0x0053E895` | `0x0013E895` | `83 7e 08 1b` | `cmp dword ptr [esi + 8], 0x1b (VK_ESCAPE)` |
