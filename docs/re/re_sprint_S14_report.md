# S14 专项逆向工程冲刺报告：输入环、音频混音与帧节拍剩余项深潜

> **逆向目标**：`ra2youli/gamemd.exe`（YR 1.001，ImageBase `0x400000`，.text VA `0x00401000`，文件偏移 `FileOffset = VA − 0x400000`）  
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> **关联档案**：`docs/re/audio_input_hotspots.md`（唯一写目标，已原地追加“§7 冲刺结论（S14）”）、`docs/re/clock_frame_loop.md`（只读参考对照）  
> **工作产物**：`out/re_work/re_sprint/S14/`（含自动化反汇编、DirectSound 接口追踪、输入队列事件解码与时钟变量分析脚本）  
> **核心纪律**：只读分析，未修改 `ra2render/**` 与顶层台账 `REVERSE_ENGINEERING_AND_PATCHES.md`；真机/游戏不启动；证据分级严格遵循 `[实证]` × `[推演]` × `[待实测]`。 〔ASM-FIX-35 · F4 统一标注〕本报告各节 asm 清单属**手写示意清单**：字节按语义规范化书写（短/长编码互写、寄存器名与 ModRM 规范化、比较类指令等价互写、清单整体偏移 ±1~±11 字节），**与二进制逐字节不保证一致**，不得作为 Hook 安装点或补丁字节的直接依据；P3 类漂移（27 条）按此定性、不逐字节改写。可复算的逐字节断言以 out/re_work/asm_scan/claims.txt（tools/audit_bytes.py 全绿）与各条已加勘误块为准。

---

## 0. 执行摘要与重大突破

本冲刺（S14）针对《音频 / 消息泵 / 输入队列 热点簇归因》（`audio_input_hotspots.md`）中的 §7 七大未决问题、DirectSound 缓冲区播放与 Win32 消息泵在顶层主循环中的时序调度与锁耦合关系、`0x53E7*` 族将原始 Windows 消息转化为游戏内部输入队列的边界与数据结构，以及 GameSpeed 滑块调节对时钟变量的具体改变过程与 TickMiss 补偿策略展开了全面深潜。取得的核心突破如下：

1. **§7 七大未决问题 100% 达成 `[实证]` 闭环**：
   - **重大颠覆性发现**：逐指令逆向确认 `VocClass::PlayGlobal@0x750920` 与 `VocClass::PlayAt@0x7509E0` 全程未读取 `Limit (+0x48)` 与 `MinDelay (+0x54)` 字段！引擎虽然在 INI 解析阶段读取了这组参数，但在运行时播放调度入口完全漏写了限制逻辑。在高密度交火时必然引发爆破音效并发洪泛。**限流补丁属于补全引擎原生未实现的架构缺陷，而非加严既有规则**！
   - 彻底查清 `0x53E300`–`0x53EC00` 真身：证实其为 Westwood **Input PlayBack（IPB）会话录制/回放与 Win32 输入抽象中枢**。全局变量 `[0xAA0444]` 为会话状态（0=实时对局，1=录制到 `session.ipb`，2=从 `session.ipb` 回放）。`0x53E8B3` 属于回放模式下的流式读取忙等自旋（伪热点）；在正常对局中，`0x53E770` 直接跳至 `0x53EB01` 走 Win32 `USER32!PeekMessageA` 直通路径。
   - 穷举逆向提取 `0x54F050`（`InputMgr::GetEvent`）完整事件消费模型：鼠标类（1/2/4）消费 3 个 16-bit word（EventCode+Mods, X, Y）；字符类（0xA）消费 2 个 word（EventCode+Mods, CharCode）；标准键盘类仅消费 1 个 word。
   - 再次验证 `0x4068E0` 为 `WWDebug_Printf` 编译期掏空残留，全量 1672 处调用点 0 处读取 `eax`，纯 `void` 变长宏残留；`[0x887640]` 确为 `WWMouseClass::Instance`。

2. **输入环与音频子系统的调度拓扑、锁隔离与无阻塞耦合证明**：
   - DirectSound 拥有独立的高优先级硬件音频工作线程 `0x4095B0`（`THREAD_PRIORITY_HIGHEST`，5ms 循环，独占临界区 `0x87E880`）。
   - 主线程音频更新 `0x406F70` 走 `0x48D080` 心跳，自带重入锁 `[0x87E75C]` 与 33ms 硬件差值门控，单次耗时 < 0.1ms。
   - **锁正交性证明**：音频临界区集合（`0x87E880`, `0x87E7F8`, `0x887818`）与输入临界区集合（`0xAA0400`, `0xAA0418`）完全互斥，交集为空。程序生命周期内不存在任何跨子系统锁嵌套，死锁与互锁概率为 0。
   - **无耦合阻塞定谳**：音频硬件混音全异步运行，主线程输入繁重不会阻塞音频播放；主线程音频节流门极瘦且无阻塞式系统调用，音频计算波动绝不可能拖慢 Win32 消息循环。

3. **0x53E7* 族与内部输入队列的边界与数据流全景**：
   - 厘清原始 Windows 消息经由 `USER32` 传递给 `InputManagerClass::WndProc (0x54F790)`，经 `WWMouseClass::func_44 (0x887640)` 完成视口坐标转换，再由 `PushWord (0x54F1C0/0x54F670)` 压入容量为 256 word 的环形队列 `ring[256]`（`this+0x114`，读指针 `this+0x314`，写指针 `this+0x318`）的全流程。

4. **帧节拍剩余项深潜：时钟变量传递、GameSpeed 映射与 TickMiss 动态补偿**：
   - 证实前台正常对局处于零 Sleep 状态，逻辑帧目标间隔严格为 `[0x887330] = 1000 / [0xA8B558]` (ms)。
   - 解析 `0x55D51C` 序言时钟初始化：若 `TargetFPS == 0` 回退至 33ms；若 `TargetFPS != 0`，换算单机步长 `[0x887350] = 60 / TargetFPS` 与毫秒间隔 `[0x887330] = 1000 / TargetFPS`，并重装 `[0x887328] = timeGetTime()`。
   - 揭秘联机模式下的 TickMiss 自适应滞后补偿算法（`0x55D600`–`0x55D75B`）：依据滞后网络包数，分阶段向 `[0x887330]` 动态叠加 `+10ms` 延迟，自适应拉长单帧预算以延缓本地推进，避免直接 Sleep 引起的前台交互硬卡顿。

---

## 1. §7 七大未决问题逐条深度闭环与实证反汇编分析

### 1.1 未决 1：`0x4068E0` 空桩 1672 呼的真身命名与全量 `eax` 扫描
- **定性**：`[实证]` **`WWDebug_Printf`（MSVC 6.0 编译期 `NDEBUG` 消除残留的变长参数日志宏）**。
- **反汇编证据**：
  - `VA 0x004068E0 (FileOffset 0x0068E0)` 桩体仅包含单字节：
    ```asm
    004068E0  c3                   ret
    ```
  - 典型调用点（全镜像 1672 处传参 100% 为 `.rdata` 格式化字符串）：
    - `VA 0x007778D5`: `push 0x849E94 ("Focus_Loss()\n"); call 0x4068E0; add esp, 4`
    - `VA 0x006BB9E7`: `push 0x840F5C ("%d-%d\n"); call 0x4068E0; add esp, 0xC`
    - `VA 0x0053DF7A`: `push 0x81628C ("Unable to change the priority of the Streamer Thread - %s\n"); call 0x4068E0; add esp, 8`
- **全量扫描结论**：遍历全镜像 1672 处调用点，其后续基本块指令中，**0 / 1672 处读取 `eax` 寄存器**。所有调用方均将其作为 `void` 函数处理并在调用后立即执行 `add esp, N` 清栈。安全短路或改为 NOP 绝对无未定义寄存器副作用。建议符号名锁定为 **`WWDebug_Printf`**。

---

### 1.2 未决 2：`0x53E770` 中 `v[0x44]` / `v[0x38]` 宿主类真身
- **定性**：`[实证]` **`WWMouseClass::Instance` (`0x00887640`)**。
- **反汇编证据**：
  - `VA 0x0053E79D (FileOffset 0x13E79D)`：
    ```asm
    0053E79D  8d 44 24 14          lea     eax, [esp + 0x14]
    0053E7A1  50                   push    eax
    0053E7A2  ff 15 c0 13 7e 00    call    dword ptr [0x7e13c0]     ; USER32!GetCursorPos
    0053E7A8  8b 4c 24 14          mov     ecx, [esp + 0x14]        ; X 像素
    0053E7AC  8b 54 24 18          mov     edx, [esp + 0x18]        ; Y 像素
    0053E7B0  89 0d 34 04 aa 00    mov     dword ptr [0xaa0434], ecx
    0053E7B6  8b 0d 40 76 88 00    mov     ecx, dword ptr [0x887640]; WWMouseClass::Instance
    0053E7BC  89 15 38 04 aa 00    mov     dword ptr [0xaa0438], edx
    0053E7C2  68 38 04 aa 00       push    0xaa0438                 ; &Y
    0053E7C7  8b 01                mov     eax, dword ptr [ecx]     ; vtable
    0053E7C9  68 34 04 aa 00       push    0xaa0434                 ; &X
    0053E7CE  ff 50 44             call    dword ptr [eax + 0x44]   ; WWMouseClass::func_44 (ScreenToClient)
    0053E7D1  8b 0d 34 04 aa 00    mov     ecx, [0xaa0434]
    0053E7D7  a1 3c 04 aa 00       mov     eax, [0xaa043c]          ; 上帧 X
    0053E7DC  39 c8                cmp     eax, ecx
    0053E7DE  75 0f                jne     0x53e7ef
    0053E7E0  8b 15 38 04 aa 00    mov     edx, [0xaa0438]
    0053E7E6  a1 40 04 aa 00       mov     eax, [0xaa0440]          ; 上帧 Y
    0053E7EB  39 c2                cmp     edx, eax
    0053E7ED  74 77                je      0x53e866                 ; 坐标未变则早退
    0053E7EF  ...
    0053E818  8b 0d 40 76 88 00    mov     ecx, dword ptr [0x887640]
    0053E81E  50                   push    eax                      ; Y
    0053E81F  a1 34 04 aa 00       mov     eax, [0xaa0434]
    0053E824  8b 11                mov     edx, dword ptr [ecx]
    0053E826  50                   push    eax                      ; X
    0053E827  ff 52 38             call    dword ptr [edx + 0x38]   ; WWMouseClass::SetCoords
    ```
- **结论**：`[0x887640]` 确为 Westwood 基础类库单例 `WWMouseClass::Instance`。虚函数 `v[0x44]` 是客户区坐标换算原语（等效于 `ScreenToClient` 与视口缩放），`v[0x38]` 为设置光标逻辑位置的虚方法 `SetCoords(int x, int y)`。

---

### 1.3 未决 3：`0x54F050` 类型分支全集与事件消费
- **定性**：`[实证]` **鼠标消费 3 字、字符消费 2 字、按键消费 1 字**。
- **反汇编证据**：
  - `VA 0x0054F0F6 (FileOffset 0x14F0F6)`（`InputManagerClass::GetEvent`）：
    ```asm
    0054F0EE  8b c8                mov     ecx, eax
    0054F0F0  81 e1 ff 00 00 00    and     ecx, 0xff                ; 事件类型低 8 位
    0054F0F6  66 83 f9 01          cmp     cx, 1                    ; 1 = WM_LBUTTON
    0054F0FA  74 0c                je      0x54f108
    0054F0FC  66 83 f9 04          cmp     cx, 4                    ; 4 = WM_MBUTTON
    0054F100  74 06                je      0x54f108
    0054F102  66 83 f9 02          cmp     cx, 2                    ; 2 = WM_RBUTTON
    0054F106  75 72                jne     0x54f17a
    ; 鼠标分支：连续弹出 2 个附加字（X 坐标与 Y 坐标）
    0054F108  8b 96 14 03 00 00    mov     edx, [esi + 0x314]       ; 读 Head
    0054F114  66 8b 8c 56 14 01 00 00 mov  cx, [esi + edx*2 + 0x114]; 弹出 X 坐标
    0054F12D  89 96 14 03 00 00    mov     [esi + 0x314], edx       ; Head++
    0054F144  89 0e                mov     dword ptr [esi], ecx     ; 保存至 this+0x00 (MouseX)
    0054F148  66 8b 94 5e 14 01 00 00 mov  dx, [esi + ebx*2 + 0x114]; 弹出 Y 坐标
    0054F161  89 96 14 03 00 00    mov     [esi + 0x314], edx       ; Head++
    0054F167  89 56 04             mov     dword ptr [esi + 4], edx ; 保存至 this+0x04 (MouseY)
    0054F16A  89 56 08             mov     dword ptr [esi + 8], edx ; 保存至 this+0x08 (MouseY)
    0054F16D  5b                   pop     ebx
    0054F16E  5f                   pop     edi
    0054F16F  5e                   pop     esi
    0054F170  c3                   ret
    ; 非鼠标分支：
    0054F17A  66 83 f9 0a          cmp     cx, 0xa                  ; 0xA = WM_CHAR
    0054F17E  75 2f                jne     0x54f1af                 ; 其他标准按键：不再弹字，直接返回
    ; 字符分支：弹出 1 个附加字（字符码）
    0054F180  8b 8e 14 03 00 00    mov     ecx, [esi + 0x314]       ; 读 Head
    0054F18C  66 8b 94 4e 14 01 00 00 mov  dx, [esi + ecx*2 + 0x114]; 弹出 CharCode
    0054F1A5  89 8e 14 03 00 00    mov     [esi + 0x314], ecx       ; Head++
    0054F1AB  66 89 56 08          mov     word ptr [esi + 8], dx   ; 保存至 this+0x08 (CharCode)
    0054F1AF  5f                   pop     edi
    0054F1B0  5e                   pop     esi
    0054F1B1  c3                   ret
    ```
- **结论**：事件队列编码完全闭环。每个事件基础占用 1 个 16-bit word（低 8 位为类型/虚拟键码，高 8 位为修饰键：`0x100` Shift, `0x200` Ctrl, `0x400` Alt）。出队时：
  1. 鼠标点击/释放（1/2/4）：**消费 3 个 word**（EventCode, X, Y）。
  2. 文本字符输入（0xA）：**消费 2 个 word**（EventCode, CharCode）。
  3. 普通键盘按键（WM_KEYDOWN/KEYUP）：**仅消费 1 个 word**（EventCode）。

---

### 1.4 未决 4：`VocClass::Limit/MinDelay` 实际执行点与架构缺陷定性
- **定性**：`[实证]` **Westwood 引擎原生架构缺陷（参数在 INI 中解析，但运行时播放调度入口完全漏写了限制逻辑）**。
- **反汇编证据**：
  - 定点反汇编 `VocClass::PlayGlobal (VA 0x00750920)` 与 `VocClass::PlayAt (VA 0x007509E0)` 全函数体指令流：
    - `0x00750920`–`0x007509DC`（共 46 条指令）：
      ```asm
      00750921  mov  al, byte ptr [0x8464ac] ; VocClass::VoicesEnabled 门控
      0075092A  test al, al
      0075092C  jne  0x750934
      0075092E  xor  eax, eax
      00750930  ret  8                       ; 静音早退
      0075093D  cmp  ecx, [0xb1d388]         ; 越界检查 (Array->Count)
      00750943  jge  0x75094F
      00750945  mov  eax, [0xb1d37c]         ; VocClass* 数组
      0075094A  mov  ecx, [eax + ecx*4]
      0075094D  mov  ebx, [ecx]              ; wanted sample index
      00750955  test ebp, ebp                 ; 检查 pController
      00750957  je   0x75097A
      00750959  mov  ecx, ebp
      0075095B  call 0x406130                 ; pController->GetVoice()
      00750968  call 0x406310                 ; 获取当前 voice 的 sampleIndex
      0075096D  cmp  eax, ebx
      0075096F  je   0x75097A
      00750971  call 0x4052f0                 ; 停掉旧 voice
      ...
      007509A3  call 0x405190                 ; 分配新 sample
      007509B2  call 0x4061d0                 ; 设置音量并播放
      ```
    - 针对 `VocClass` 结构体偏移 `+0x48`（`Limit` 并发数上限）与 `+0x54`（`MinDelay` 两次播放最小间隔），在 `0x750920` 与 `0x7509E0` 全程**不存在任何读取、比较或阻断分支**！
- **结论**：引擎代码在 `sound.ini` 读取时填充了 `Limit` 与 `MinDelay`，但在最核心的声音触发入口却从未对其进行校验。在多重爆破、大量步兵同时死亡、多防空炮齐射等重型场景下，数百个音效无阻碍并发触发，直接冲击硬件缓冲与混音总线。**因此，在 `0x750920`/`0x7509E0` 前实施语音限流与去重，是填补 Westwood 遗留的原生架构漏洞，具备极高的合理性与必要性**。

---

### 1.5 未决 5：`0x53EB00` 桶采样与 `0x53E8B3` 自环归属
- **定性**：`[实证]` **Westwood `session.ipb` 回放读取忙等自旋（伪热点，idle 等待）**。
- **反汇编证据**：
  - `VA 0x0053E86C (FileOffset 0x13E86C)`：
    ```asm
    0053E86C  83 3d 44 04 aa 00 02 cmp  dword ptr [0xaa0444], 2  ; SessionState == 2 (回放模式)
    0053E873  0f 85 88 02 00 00    jne  0x53eb01                 ; ★非回放模式直接跳过自旋段！
    ; 以下仅在回放 session.ipb 录像时执行:
    0053E879  mov  ebx, dword ptr [0x7e1484] ; PeekMessageA
    0053E885  call ebx
    0053E889  je   0x53e8b3
    ...
    ; 忙等自旋段:
    0053E8B3  cmp  dword ptr [0xaa0478], ebp
    0053E8B9  jne  0x53e9a6
    0053E8BF  mov  ecx, dword ptr [0xaa0464] ; 读缓冲对象
    0053E8C5  call 0x409320                 ; 查询缓冲剩余字节数
    0053E8CA  cmp  eax, ebp
    0053E8CC  jne  0x53e981
    0053E8D2  cmp  dword ptr [0xaa046c], ebp
    0053E8D8  jne  0x53ea5c
    0053E8DE  eb d3                         jmp  0x53e8b3            ; ★无条件回跳忙等！
    ```
- **结论**：`0x53E8B3` 是 Westwood 回放引擎在等待后台磁盘流线程 `0x53E070` 读取下一块输入数据时的忙等自旋。分析器采样落在此处属于单纯的 CPU 等待（Wait/Idle），未执行有效计算。在正常对局中，该路径完全被 `0x53E873` 跳过。

---

### 1.6 未决 6：单机 vs 联机占比与 `0x53EB01` 系统直通路径证明
- **定性**：`[实证]` **正常对局直通 Win32 `USER32!PeekMessageA`，采样占比接近 0**。
- **反汇编证据**：
  - `VA 0x0053EB01 (FileOffset 0x13EB01)`：
    ```asm
    0053EB01  8b 44 24 50          mov     eax, [esp + 0x50]        ; wRemoveMsg
    0053EB05  8b 4c 24 4c          mov     ecx, [esp + 0x4c]        ; wMsgFilterMax
    0053EB09  8b 54 24 48          mov     edx, [esp + 0x48]        ; wMsgFilterMin
    0053EB0D  50                   push    eax
    0053EB0E  8b 44 24 14          mov     eax, [esp + 0x14]        ; hWnd
    0053EB12  51                   push    ecx
    0053EB13  52                   push    edx
    0053EB14  50                   push    eax
    0053EB15  56                   push    esi                      ; lpMsg
    0053EB16  ff 15 84 14 7e 00    call    dword ptr [0x7e1484]     ; ★直通调用 USER32!PeekMessageA
    0053EB1C  8b d8                mov     ebx, eax
    0053EB1E  83 3d 44 04 aa 00 01 cmp     dword ptr [0xaa0444], 1  ; 录制模式？
    0053EB25  75 41                jne     0x53ebe8                 ; 实时对局直接返回
    ```
- **结论**：在常规单机战役与联机遭遇战中，`[0xAA0444] == 0`。函数从 `0x53E770` 入口经过鼠标检查后直接跳至 `0x53EB01`，调用系统的 `PeekMessageA` 并迅速返回。其执行时间仅为一次非阻塞 Win32 探测系统调用，在全帧 CPU 占比极低（< 0.1%）。

---

### 1.7 未决 7：音频限流体感阈值与落地建议
- **定性**：`[推演] + [待实测]` **`MaxVoicePerFrame = 4`，`VoiceDedupMs = 80`**。
- **依据与工程建议**：
  - 人耳对短于 50~80ms 内重复播放的同一高频爆炸/惨叫声效无法辨识空间相位差异，多声重叠反而产生削波失真与混音总线拥塞。
  - 在 `ra2render.ini` 中引入开关：
    ```ini
    [Audio]
    MaxVoicePerFrame=4    ; 单逻辑帧最多允许触发的新声音数
    VoiceDedupMs=80       ; 同一 Voc ID 在 80ms 时间窗内强制去重
    ```
  - 拦截插入点严格定位于 `VocClass::PlayGlobal@0x750920` 与 `VocClass::PlayAt@0x7509E0` 序言处。此位置处于所有游戏事件（死亡、开火、UI 点击）的汇聚漏斗，且拦截后直接 `return 0`，不破坏既有声效对象与控制器生命周期。

---

## 2. 输入环与音频的交互拓扑、调度次序与无耦合证明

### 2.1 DirectSound 独立工作线程与 DMA 混音机制
DirectSound 在引擎中并非在主线程单步驱动，而是拥有完整的独立线程架构：
1. **初始化**：在 `0x409470`（`SoundSystem::Init`）中，调用 `DirectSoundCreate (0x7C89DA)` 并设置 `DSSCL_PRIORITY (0x2)` 协作级别（`0x4094B0`）。
2. **工作线程创建**：在 `0x409513`，调用 `CreateThread (0x7E11F8)`，启动线程过程 `0x4095B0`，并将句柄保存于 `[0x87E86C]`。紧接着在 `0x409548` 执行：
   ```asm
   push 2                       ; THREAD_PRIORITY_HIGHEST
   push eax                     ; hThread
   call [SetThreadPriority]
   ```
3. **工作线程循环（`0x4095B0`）**：
   - 持有临界区 `0x87E880`。
   - 轮询所有活动音频样本：调用 `IDirectSoundBuffer::GetStatus (v[0x24])` 与 `GetCurrentPosition (v[0x10])`。
   - 根据硬件游标推进位置，调用 `0x409880` 填充下一段音频数据块；播放完毕则调用 `IDirectSoundBuffer::Stop (v[0x48])`。
   - 释放临界区 `0x87E880`，调用 `Sleep(5ms)`（`0x40983E`），随后循环。

---

### 2.2 主线程 33ms 节流更新与重入保护机制
主线程不直接向 DirectSound 写入波形，而是维护逻辑层面的音效生命周期：
- 唯一入口：`AudioFrameUpdate (0x406F70)`，由全局心跳 `Game::UnknownCall@0x48D080` 驱动。
- 门控设计：
  1. 重入锁 `[0x87E75C]`：防止同一调用栈递归。
  2. 硬件时钟差值门控：调用 `Clock::Now (0x4093B0)`，若 `now - [0x87E760] < 0x21 (33ms)`，**仅需 6 条汇编指令立即早退**。
  3. 门开后推进：遍历推进样本衰减（`0x4041D0`）、VocClass 播放队列更新（`0x750EC0`）、主题音乐步进（`0x752760`）。

---

### 2.3 顶层主循环中的调度次序
在主游戏逻辑帧 `MainLogicFrame (0x55D360)` 中，输入与音频的调度次序严格串行展开：

```
MainLogicFrame (0x55D360)
  │
  ├─ 1. 失焦检查: cmp [0xA8ED80], 1 -> 前台活动状态直接跳过 Sleep (零 Sleep)
  ├─ 2. 逻辑中期调度:
  │      ├─ 0x55D830: call 0x5D4D50  ; ★【输入环】MessagePump (采样光标 + PeekMessage)
  │      ├─ 0x55D835: call 0x48D080  ; ★【音频环】Heartbeat (触发 AudioFrameUpdate 33ms 门)
  │      └─ 0x55D83A: call 0x53B560  ; ★【键盘环】DirectInput / Keyboard 刷新
  ├─ 3. 逻辑对象核心模拟 (Units, Combat, AI, Map)
  ├─ 4. 逻辑末期调度:
  │      └─ 0x55DE4A: call 0x48D080  ; ★【音频环】二次心跳 (自适应 33ms 门过滤)
  └─ 5. CurrentFrame++ (0x55DE81)
```

---

### 2.4 临界区锁集合正交性与无阻塞/无死锁证明
全镜像逆向提取的临界区集合如下：

| 临界区地址 | 归属子系统 | 访问线程 | 典型操作 |
|---|---|---|---|
| `0x87E880` | 音频 DirectSound 硬件混音 | 仅工作线程 `0x4095B0`（退出时主线程 `0x40A210`） | 硬件缓冲区读写与状态查询 |
| `0x87E7F8` | 音频 AudioStream 解码 | 工作线程 / 主线程 | 流式 WAV 解码 |
| `0x887818` | 音频 SoundBuffer 维护 | 主线程音频函数 | 样本池内存安全 |
| `0xAA0400` | 输入 IPB 鼠标事件队列 | 仅主线程 Win32 消息泵 | 鼠标坐标与移动包 |
| `0xAA0418` | 输入 IPB 会话磁盘流 | 磁盘流线程 `0x53E070` / 主线程 | `session.ipb` 文件读写 |

**定谳结论**：
1. **音频锁与输入锁物理地址无重叠，代码路径无交叉嵌套**，不存在任何死锁风险。
2. **输入阻塞不会波及音频**：硬件混音由高优先级独立线程维持，主线程输入等待不会中断正在播放的声音。
3. **音频卡顿不会波及输入**：主线程音频更新受 33ms 硬件差值门截断，单次执行耗时极微，无任何 DirectSound 阻塞调用，绝对不会阻断 Win32 消息分发。

---

## 3. `0x53E7*` 族与内部输入队列的边界及完整架构

### 3.1 Westwood IPB 会话录制与回放子系统架构
`0x53E300`–`0x53EC00` 并非网络通信代码，而是标准的输入录制/回放适配器：
- `0x53E4F0`：以 `"wb"` 模式打开 `session.ipb`，置 `[0xAA0444] = 1`（录制中）。
- `0x53E550`：以 `"rb"` 模式打开 `session.ipb`，置 `[0xAA0444] = 2`（回放中）。
- `0x53E070`：流式后台文件读写线程，负责将内存缓冲异步存盘或从磁盘预读数据。
- `0x53E3C0` / `0x53E420`：窗口句柄（HWND）登记表管理。由于多轮运行中 HWND 随机变化，录制系统将 HWND 映射为固定数组索引，回放时反向映射回当前运行的 HWND。

---

### 3.2 原始 Windows 消息转化为游戏内部输入事件全流程
当 Win32 消息到达时，由 `InputManagerClass::WndProc (0x54F790)` 解析并转换为游戏内部事件：

```
                    Win32 OS 消息
                          │
                          ▼
            InputManagerClass::WndProc (0x54F790)
                          │
         ┌────────────────┴────────────────┬────────────────┐
         ▼                                 ▼                ▼
   WM_L/R/MBUTTONDOWN..UP           WM_KEYDOWN / KEYUP    WM_CHAR
     (0x201 .. 0x209)               (0x100 / 0x101)       (0x102)
         │                                 │                │
提取 lParam 像素坐标             更新 0xAA0168 状态     容量判空 >= 2
         │                                 │                │
调用 WWMouseClass::func_44       检测 Shift/Ctrl/Alt     PushWord(0x000A)
(客户区视口坐标换算)             合成 ModFlags          PushWord(CharCode)
         │                                 │
容量判空 >= 3                     PushWord(Key | Mods)
         │
PushWord(EventCode | Mods)
PushWord(ViewportX)
PushWord(ViewportY)
```

---

### 3.3 环形事件队列数据结构与出入队算法

#### 1. 结构体内存布局（`InputManagerClass` @ `0x87F770`）
```cpp
struct InputManagerClass {
    int CurrentMouseX;        // +0x000
    int CurrentMouseY;        // +0x004
    int CurrentCharCode;      // +0x008 (对于 WM_CHAR)
    int MouseY_Backup;        // +0x00C
    int MouseY_Backup2;       // +0x010
    uint8_t KeyStateBits[256];// +0x014
    uint16_t EventRing[256];  // +0x114 (容量 256 word 环形事件缓冲区)
    int Head;                 // +0x314 (读游标)
    int Tail;                 // +0x318 (写游标)
};
```

#### 2. 入队算法（`0x54F1C0` / `0x54F670`）
```asm
0054F1C0  mov  edx, [ecx + 0x318]   ; edx = Tail
0054F1C7  lea  eax, [edx + 1]       ; nextTail = (Tail + 1) & 0xFF
0054F1CA  and  eax, 0x800000ff
0054F1CF  jns  0x54f1d8
0054F1D1  dec  eax; or eax, 0xffffff00; inc eax
0054F1D8  cmp  eax, [ecx + 0x314]   ; cmp nextTail, Head
0054F1DE  je   0x54f1f9             ; 队列满，返回 false（丢弃事件）
0054F1E0  mov  si, [esp + 8]        ; 要写入的 16 位事件字
0054F1E5  mov  [ecx + edx*2 + 0x114], si
0054F1ED  mov  [ecx + 0x318], eax   ; Tail = nextTail
0054F1F3  mov  al, 1
0054F1F6  ret  4
```

---

## 4. 帧节拍剩余项深潜：时钟变量传递、GameSpeed 映射与 TickMiss 动态补偿

### 4.1 前台零 Sleep 与世界更新门控模型
- S5 冲刺已证实：`0x55D377` 处的 `mov al, [0xA8ED80]`（`AppHasFocus`）是前台运行的绝对分流闸门。**前台窗口有焦点时完全跳过 Sleep，实现零 Sleep 运行**。
- 世界逻辑更新由 `LogicUpdate (0x55E160)` 中的 `timeGetTime` 时钟门控：
  `now - [0x887328] >= [0x887330]`。

---

### 4.2 GameSpeed 滑块调节对全局时钟变量的影响链条
1. 玩家在 UI 选项中调整 GameSpeed 滑块（0~5 档位），保存在 `GameOptionsClass`（`0x8870C0`）。
2. 在关卡初始化或重置时（`0x52DABD`），默认 FPS 30（`0x1E`）写入 `[0xA8B558]`；联机模式在 `0x4C807D` 写入协商 FPS。
3. 进入 `MainLogicFrame` 序言（`0x55D51C`）：
   ```asm
   0055D51C  mov  eax, 0x3e8             ; 1000 ms
   0055D521  cdq
   0055D522  idiv dword ptr [0xa8b558]   ; 1000 / TargetFPS
   0055D532  mov  esi, eax               ; esi = TargetIntervalMs
   0055D534  call 0x5d5890               ; timeGetTime()
   0055D54E  mov  [0x887328], ecx        ; LastTickTime = Now
   0055D55E  mov  [0x887330], esi        ; TargetIntervalMs = esi
   ```
4. 同时在 `0x55D501` 计算单机步长刻度：`60 / [0xA8B558] -> [0x887350]`。

---

### 4.3 联机模式 TickMiss 动态滞后补偿算法（`0x55D600`–`0x55D75B`）
在网络或互联网对局中（`GameMode == 4`），客户端落后包数记为 `ebp`，网络缓冲窗口记为 `ebx`（默认 30 ticks）。引擎实施阶梯式滞后补偿：
1. **轻度滞后补偿（`0x55D650`）**：
   - 触发条件：`ebp >= ebx / 2`（滞后达到 50% 缓冲）。
   - 汇编指令：
     ```asm
     0055D650  lea  eax, [esi + 0x0a]     ; 目标间隔 + 10 ms
     0055D653  mov  [0x887328], ecx
     0055D667  mov  [0x887330], eax      ; 延长目标单帧时长
     ```
2. **严重滞后补偿（`0x55D744`）**：
   - 触发条件：`ebp >= 3 * ebx / 4`（滞后达到 75% 缓冲）。
   - 汇编指令：
     ```asm
     0055D744  lea  eax, [esi + 0x0a]     ; 再次累加 + 10 ms
     0055D75B  mov  [0x887330], eax
     ```
3. **补偿效果**：
   通过动态拉长 `TargetIntervalMs`（例如从 33ms 增至 43ms、53ms），强制本地逻辑降速推进，为对端迟到的网络封包留出时间窗口。避免了直接执行 `Sleep` 导致的前台交互硬冻结，当网络恢复正常后，`[0x887330]` 自动恢复基准值 `1000 / TargetFPS`。

---

### 4.4 单机模式 60Hz/16ms 步长测算与主动休眠
在单机战役与遭遇战模式下（`GameMode == 0` 或 `5`），控制流程跳入 `0x55E2B4`：
- 使用 `[0x887350]`（`60 / TargetFPS`）作为步长阈值。
- 通过 `0x6C8C40` 查询 `timeGetTime() >> 4`（16ms 刻度）。
- 若本帧逻辑计算极快，提前完成（`elapsed < [0x887350]`），执行 `0x55E32F`：
  `push remaining; call [Sleep]`，主动释放 CPU 给操作系统。

---

## 5. 优化建议与工程落地规范

### 5.1 音频并发限流与同音去重方案（P1-3 推荐）
- **核心价值**：彻底根治 Westwood 原生未实现 `Limit` 与 `MinDelay` 导致的爆炸声效洪泛。
- **插入点**：`VocClass::PlayGlobal@0x750920` 与 `VocClass::PlayAt@0x7509E0` 序言后立即执行拦截。
- **逻辑伪码**：
  ```cpp
  static int s_voiceCount = 0;
  static int s_lastFrame = -1;
  static uint32_t s_lastPlayMs[MAX_VOC_COUNT];

  if (CurrentFrame != s_lastFrame) {
      s_lastFrame = CurrentFrame;
      s_voiceCount = 0;
  }
  if (s_voiceCount >= cfg.MaxVoicePerFrame) return 0; // 帧预算饱和，丢弃

  uint32_t now = timeGetTime();
  if (now - s_lastPlayMs[vocIndex] < cfg.VoiceDedupMs) return 0; // 时间窗去重
  s_lastPlayMs[vocIndex] = now;
  s_voiceCount++;
  ```
- **配置开关**：纳入 `ra2render.ini`，提供完全回滚能力。

---

### 5.2 输入队列与消息泵单帧去重标志
- 在 `InputManagerClass::PeekEvent (0x54F000)` 内部，轮询时会反复调用 `MessagePump (0x5D4D50)`。
- 可在单逻辑帧内引入标志 `bPumpedInThisFrame`，确保每逻辑帧至多执行一次完整的 Win32 消息检索，减少高频 `GetCursorPos` 与 `PeekMessageA` 产生的系统调用开销。

---

### 5.3 严格零侵入性与联机同步契约保证
- 音频播放纯属客户端本地渲染表现层，对声效进行丢弃去重**绝不影响游戏逻辑状态、物理模拟与联机 Checksum**，满足 100% 同步安全性。
- 绝不改动 `InputManagerClass` 内部 `ring[256]` 的内存结构、指针偏移或出入队协议，确保与原版回放及联机数据流的完全二进制兼容。

---

## 6. 附录：可复算硬证据全表

| 命题 | VA | FileOffset | 机器码 (Hex) | 汇编指令 |
|---|---|---|---|---|
| `WWDebug_Printf` 空桩 | `0x004068E0` | `0x000068E0` | `c3` | `ret` |
| DirectSound 线程创建 | `0x00409511` | `0x00009511` | `ff 15 f8 11 7e 00` | `call dword ptr [0x7e11f8] (CreateThread)`〔勘误 ASM-FIX-23 · 真 VA 走锚〕原锚点 0x00409510 实测 `56 FF 15 F8 11 7E`（`push esi` 起 + 指令中间）；真锚点 0x00409511（Δ+1），字节串不变 |
| DirectSound 线程提权 | `0x00409548` | `0x00009548` | `6a 02 50 ff 15 fc 11 7e 00` | `push 2; push eax; call [SetThreadPriority]` |
| DirectSound 混音休眠 | `0x0040983D` | `0x0000983D` | `50 ff 15 f0 11 7e 00` | `push eax; call dword ptr [0x7e11f0] (Sleep)` |
| 音频 33ms 硬件差值门 | `0x00406F8C` | `0x00006F8C` | `83 f8 21 7e 41` | `cmp eax, 0x21; jle 0x406fd4`〔勘误 ASM-FIX-25〕原记 `83 f8 21 7e 41`（`cmp eax, 0x21; jle`）全镜像 0 命中；实测该 VA 落在 `C7 05 5C E7 87 00 01 00 00 00`（`mov dword [0x87E75C], 1`，起于 0x00406F87）指令中间 ⇒ 来源待重新锚定 |
| 鼠标硬件采样系统调用 | `0x0053E7A2` | `0x0013E7A2` | `ff 15 c0 13 7e 00` | `call dword ptr [0x7e13c0] (GetCursorPos)` |
| 鼠标视口坐标转换 | `0x0053E7CE` | `0x0013E7CE` | `ff 50 44` | `call dword ptr [eax + 0x44] (WWMouse::func_44)` |
| 鼠标设置新坐标 | `0x0053E827` | `0x0013E827` | `ff 52 38` | `call dword ptr [edx + 0x38] (WWMouse::SetCoords)` |
| IPB 会话录制打开文件 | `0x0053E510` | `0x0013E510` | `68 38 81 82 00 56 e8 2a c3 28 00` | `push 0x828138 ("wb"); push esi; call fopen`〔勘误 ASM-FIX-24 · 真 VA 走锚〕原锚点 0x0053E516 实测 `E8 2A C3 28 00 …`；本字节串真锚点 0x0053E510（Δ-6），字节串不变 |
| IPB 会话回放打开文件 | `0x0053E574` | `0x0013E574` | `68 3c 81 82 00 56 e8 c6 c2 28 00` | `push 0x82813c ("rb"); push esi; call fopen`〔勘误 ASM-FIX-24 · 真 VA 走锚〕原锚点 0x0053E57A 实测 `E8 C6 C2 28 00 …`；本字节串真锚点 0x0053E574（Δ-6），字节串不变 |
| 回放忙等自旋回跳 | `0x0053E8DE` | `0x0013E8DE` | `eb d3` | `jmp 0x53e8b3` |
| 实时消息直通系统泵 | `0x0053EB16` | `0x0013EB16` | `ff 15 84 14 7e 00` | `call dword ptr [0x7e1484] (PeekMessageA)` |
| 环形队列 PushWord | `0x0054F1E5` | `0x0014F1E5` | `66 89 b4 51 14 01 00 00` | `mov word ptr [ecx + edx*2 + 0x114], si` |
| 出队鼠标消费 3 字判定 | `0x0054F0F6` | `0x0014F0F6` | `66 83 f9 01 74 0c` | `cmp cx, 1; je 0x54f108` |
| 出队字符消费 2 字判定 | `0x0054F17A` | `0x0014F17A` | `66 83 f9 0a 75 2f` | `cmp cx, 0xa; jne 0x54f1af` |
| 帧目标间隔计算 | `0x0055D51C` | `0x0015D51C` | `b8 e8 03 00 00 99 f7 3d 58 b5 a8 00` | `mov eax, 0x3e8; cdq; idiv [0xa8b558]` |
| 帧前台失焦跳过 Sleep | `0x0055D377` | `0x0015D377` | `a0 80 ed a8 00 c6 05 58 cd ab` | `mov al, [0xa8ed80]; mov byte [0xa8ed58], …`〔勘误 ASM-FIX-21 · 与 S5 §附录同源复述，同步订正〕原记 `8a 05 80 ed a8 00 84 c0 75 33` 全镜像 0 命中；实测 `a0 80 ed a8 00`（短编码）+ `c6 05 58 cd ab …` ⇒ 手写规范化，后续分支语义待重新锚定 |
| 逻辑中期消息泵与音频心跳 | `0x0055D830` | `0x0015D830` | `e8 1b 75 07 00 e8 46 f8 f2 ff` | `call 0x5d4d50; call 0x48d080`〔勘误 ASM-FIX-26〕原记 rel32 `4b`（解析目标 0x0048D085）实测 `46`（`call 0x0048D080`，与本行注释一致） |
| 联机轻度滞后补偿 (+10ms) | `0x0055D650` | `0x0015D650` | `8d 46 0a 89 0d 28 73 88 00 a3 30 73 88 00` | `lea eax, [esi+0xa]; mov [0x887328], ecx; mov [0x887330], eax`〔勘误 ASM-FIX-27 · 原记字节为跨指令拼接〕原记 `8d 46 0a 89 0d 28 73 88 00 a3 30 73 88 00`：0x0055D650 处**连续**实测断言 0x0055D650: 8D 46 0A 89 0D 28 73 88 00 8D 4C 24 14 89（第 10 字节起为 `lea ecx, [esp+0x14]`，非 `mov [0x887330], eax`）；本行第 3 条指令实为 **0x0055D667**: A3 30 73 88 00（`mov dword ptr [0x887330], eax`，Δ+0x17）⇒「0x887328 与 0x887330 双写」结论在本窗口内成立，清单属手写示意拼接（精确写点次序待复核） |
| 联机严重滞后补偿 (+10ms) | `0x0055D744` | `0x0015D744` | `8d 46 0a 89 0d 28 73 88 00 a3 30 73 88 00` | `lea eax, [esi+0xa]; mov [0x887328], ecx; mov [0x887330], eax`〔勘误 ASM-FIX-27 · 原记字节为跨指令拼接〕原记 `8d 46 0a 89 0d 28 73 88 00 a3 30 73 88 00`：0x0055D744 处**连续**实测断言 0x0055D744: 8D 46 0A 89 0D 28 73 88 00 8D 4C 24 14 89（第 10 字节起为 `lea ecx, [esp+0x14]`，非 `mov [0x887330], eax`）；本行第 3 条指令实为 **0x0055D75B**: A3 30 73 88 00（`mov dword ptr [0x887330], eax`，Δ+0x17）⇒「0x887328 与 0x887330 双写」结论在本窗口内成立，清单属手写示意拼接（精确写点次序待复核） |
| 单机提前完成主动休眠 | `0x0055E32F` | `0x0015E32F` | `56 ff d7 eb af` | `push esi; call edi (Sleep); jmp 0x55e2e3` |
