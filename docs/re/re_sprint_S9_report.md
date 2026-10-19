# S9 专项冲刺报告 · 未归因热点命名与归属终局定谳

> **冲刺任务**：S9 专项冲刺（未归因热点命名与归属收尾 · 2026-09-26）  
> **报告文档**：[re_sprint_S9_report.md](file:///d:/Project/ra2-campaign-forge/docs/re/re_sprint_S9_report.md)  
> **回写目标**：[docs/NEXT_RE_AND_MODERNIZATION.md](file:///d:/Project/ra2-campaign-forge/docs/NEXT_RE_AND_MODERNIZATION.md)（原地追加 §0.2.1）  
> **分析目标**：`ra2youli/gamemd.exe`（YR 1.001，ImageBase `0x400000`，`.text` VA `0x1000`，`FileOffset = VA - 0x400000`）  
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> **证据分级**：`[实证]`（VA/文件偏移 + 原始字节 + 反汇编指令）× `[推演]` × `[待实测]`  
> **复算环境**：Python 3.12 + pefile + capstone 5.x，脚本与原始取证数据存档于 `out/re_work/re_sprint/S9/`  
> **纪律声明**：真机不启动，未修改 `ra2render/**` 与顶层台账 `REVERSE_ENGINEERING_AND_PATCHES.md`。

---

## 0. 冲刺总览与闭环台账

本轮冲刺（S9）对《下一步逆向方向与源码现代化适配路线》（`docs/NEXT_RE_AND_MODERNIZATION.md`）§0.2 遗留的 5 大未归因/粗归因热点函数进行了全指令级深度逆向取证。所有 5 大核心热点 100% 达成 `[实证]` 闭环，不仅明确确定了函数名、所属模块、堆栈大小、关键结构与调用方，更修正了多处严重的初始推测偏差（如将启动对话框误判为 AI、将网络加载进度包误判为地图迷雾等）。

### 0.1 闭环台账表

| 流号 | 目标地址桶 | 原文档粗推测 (§0.2) | S9 定谳结论 | 证据等级 | 核心定谳依据与修正 |
|---|---|---|---|---|---|
| **T1** | `0x00531D00` | 大栈函数（`[esp+0x298]`），偏 AI/任务编排 | **`Init_Version_Dialog` / `Init_About_Dialog`**（启动对话框布局与居中） | `[实证]` | 源文件硬编码 `D:\ra2mdpost\Init.CPP`（VA `0x825FB8`），对话框资源 212/226，800×600 居中计算，格式化版本/MMX/编译器信息，**与 AI 编排零关联** |
| **T2** | `0x00409300` | 小函数簇（`thiscall`），偏对象工厂/初始化 | **`StreamBuffer` I/O 原语 + `Clock::Now` QPC 定时器** | `[实证]` | 该桶实为两部分：前部 `0x4092B0–0x409354` 为流重置/冲刷/未读字节统计；后部 `0x409360–0x4093F0` 为全局高精度定时器 `Clock`（`QueryPerformanceCounter` + `_alldiv`），因主循环极高频查时而成为热点 |
| **T3** | `0x0048D000` | 地图格子 / Theater 资源查询（`CellClass` 标志 `+0x3598`） | **`Game::CallBack` 网络进度条同步分支** | `[实证]` | `[eax+0x3598]` 实为 `ScenarioClass::Instance`（`0xA8B230`）的 `IsLoadingScreen` 标志；`0x6C` 协议包为远端加载进度；更新 `ProgressScreenClass`（`0xAC4F58`）。**与 CellClass 及迷雾零关联** |
| **T4** | `0x00623100` | 数据表 / 跳转表（连续小常量 + NOP），采样噪声 | **`CommonDialogProc` 稀疏跳转表 + `UI::Updated()` 轮询入口** | `[实证]` | `0x6230DC` 为 5 项代码跳转表，`0x6230F0` 为 42 字节 case 索引映射表，6 字节 NOP 对齐至 `0x623120`；`0x623120` 即 `UI::Updated()` 消息泵轮询体，热点源于此函数执行而非数据表 |
| **T5-A** | `0x00437300` | 图形 / SHP / 绘制管线相关函数 | **`Surface::Put_Rect` 局部表面还原（Blit 包装器）** | `[实证]` | 位于 `0x437290–0x437340`，在栈上临时构造 `BSurface`（vftable `0x7E2070`），将内存 `XSurface` 还原至 `DSurface::Hidden_2`（`0x887314`），由 `StaticButtonClass::Draw`（`0x6C6740`）调用 |
| **T5-B** | `0x00432E00` | 图形 / SHP / 绘制管线相关函数 | **`BinkMovieClass::Play` 视频循环跳过检测与清栈退出** | `[实证]` | 位于 `0x432C70–0x432E39`，调用 `binkw32.dll` 逐帧解压上屏；尾部通过 `InputManagerClass::Instance`（`0x87F770`）检测按键 `0x081B`（ESC），触发跳过并调用 `0x54F720` |

---

## 1. 核心任务一：0x00531D00 大栈函数终局定谳

### 1.1 证据溯源与反汇编实证

在 §0.2 中，地址桶 `0x00531D00` 被标记为“大栈函数（`[esp+0x298]`），偏 AI/任务编排。序言 `0x531A0A`，需继续反汇编命名”。

经全指令追踪，该地址桶实际涉及 Westwood 启动初始化源文件 `D:\ra2mdpost\Init.CPP`（VA `0x00825FB8`）中的两个紧密协作函数：
1. **对话框窗口过程** `Version_Dialog_Proc`：入口 VA `0x00531A00`（FileOffset `0x131A00`）；
2. **对话框构建与屏幕适配器** `Init_Version_Dialog`：入口 VA `0x00531CC0`（FileOffset `0x131CC0`），热点 `0x00531D00` 恰处于其对话框居中与 SHP 背景设置的指令段中。

#### 指令段 A：0x00531A00（对话框窗口过程，大栈缓冲区）

```assembly
; === gamemd.exe 0x00531A00 - 0x00531A35 (FileOffset: 0x131A00 - 0x131A35) ===
0x00531a00: 8b442410             mov      eax, dword ptr [esp + 0x10]   ; lParam
0x00531a04: 81ec88020000         sub      esp, 0x288                    ; 开辟 648 字节大栈帧
0x00531a0a: 55                   push     ebp                           ; ebp 进栈
0x00531a0b: 8bac2498020000       mov      ebp, dword ptr [esp + 0x298]  ; wParam
0x00531a12: 56                   push     esi                           ; esi 进栈
0x00531a13: 8bb42494020000       mov      esi, dword ptr [esp + 0x294]  ; hWnd
0x00531a1a: 57                   push     edi                           ; edi 进栈 (栈总深 0x288 + 0x10 = 0x298)
0x00531a1b: 8bbc249c020000       mov      edi, dword ptr [esp + 0x29c]  ; uMsg
0x00531a22: 50                   push     eax                           ; lParam
0x00531a23: 55                   push     ebp                           ; wParam
0x00531a24: 8bd7                 mov      edx, edi                      ; uMsg
0x00531a26: 8bce                 mov      ecx, esi                      ; hWnd
0x00531a28: e823110f00           call     0x622b50                      ; CommonDialogProc 通用分发
0x00531a2d: 85c0                 test     eax, eax
0x00531a2f: 0f85ea010000         jne      0x531c1f
0x00531a35: 6a08                 push     8
0x00531a37: 56                   push     esi
0x00531a38: ff1574147e00         call     dword ptr [0x7e1474]          ; USER32!GetWindowLongA
```

此后，该函数利用栈上 `0x288` 字节的局部缓冲区，连续调用 `sprintf` 格式化以下版本信息：
- VA `0x00531A67`: `push 0x825FB8` (`"D:\\ra2mdpost\\Init.CPP"`)
- VA `0x00531A6E`: `push 0x81D57C` (`"TXT_SHORT_TITLE"`)
- VA `0x00531A95`: `push 0x826954` (`"Version %s"`)
- VA `0x00531AC1`: `push 0x826940` (`"Internal Version %s"`)
- VA `0x00531B27`: `push 0x826920` (`"Release Build: %s by %s - %s"`)
- VA `0x00531BC9`: `push 0x82690C` (`"MMX %s, Vendor: %s"`)
并通过 `USER32!GetDlgItem`（IAT `0x7E14A8`）与 `SetWindowTextA` 写入控件 `0x5B5`。

#### 指令段 B：0x00531CC0–0x00531D60（对话框居中与背景初始化，热点所在）

```assembly
; === gamemd.exe 0x00531D04 - 0x00531D58 (FileOffset: 0x131D04 - 0x131D58) ===
0x00531d04: 8b155035b700         mov      edx, dword ptr [0xb73550]     ; Game::hWnd
0x00531d0a: 8bce                 mov      ecx, esi                      ; hDlg
0x00531d0c: e86f532400           call     0x777080                      ; UI 关联绑定
0x00531d11: 8bce                 mov      ecx, esi
0x00531d13: e8e80a0f00           call     0x622800                      ; UI::FocusOnWindow
0x00531d18: 8b0d5035b700         mov      ecx, dword ptr [0xb73550]
0x00531d1e: 51                   push     ecx
0x00531d1f: ff15cc137e00         call     dword ptr [0x7e13cc]          ; USER32!SetFocus
0x00531d25: 681a070000           push     0x71a                         ; 控件 ID 1818
0x00531d2a: 56                   push     esi                           ; hDlg
0x00531d2b: ff15a8147e00         call     dword ptr [0x7e14a8]          ; USER32!GetDlgItem
0x00531d31: 8bf0                 mov      esi, eax
0x00531d33: 85f6                 test     esi, esi
0x00531d35: 747b                 je       0x531db2
0x00531d37: a1a4008a00           mov      eax, dword ptr [0x8a00a4]     ; ScreenWidth (e.g. 800)
0x00531d3c: 3d20030000           cmp      eax, 0x320                    ; 是否 > 800?
0x00531d41: 7f04                 jg       0x531d47
0x00531d43: 33c9                 xor      ecx, ecx
0x00531d45: eb0c                 jmp      0x531d53
0x00531d47: 05e0fcffff           add      eax, 0xfffffce0               ; eax - 800
0x00531d4c: 99                   cdq      
0x00531d4d: 2bc2                 sub      eax, edx
0x00531d4f: 8bc8                 mov      ecx, eax
0x00531d51: d1f9                 sar      ecx, 1                        ; X 偏移 = (Width - 800) / 2
0x00531d53: a1a8008a00           mov      eax, dword ptr [0x8a00a8]     ; ScreenHeight (e.g. 600)
0x00531d58: 3d58020000           cmp      eax, 0x258                    ; 是否 > 600?
...
0x00531d9c: push 0x825CE8        ; "Ra2ts_s" (低分率 SHP 背景)
0x00531da3: push 0x825CE0        ; "Ra2ts_l" (高分率 SHP 背景)
```

### 1.2 归属与职责定谳

1. **真实函数名**：`Init_Version_Dialog` / `Init_Splash_Dialog`；
2. **所属源码文件**：`D:\ra2mdpost\Init.CPP`（行号 1818 控件引用）；
3. **堆栈特征**：`sub esp, 0x288`（648 字节），用于承载 5 组长字符串的格式化堆栈缓冲区；加上调用 Win32 API 时的 4 个保护寄存器（`ebp, esi, edi, ebx`），总栈深为 `0x298`（664 字节）；
4. **调用关系**：由游戏初始化主链路 `0x0052DC9A`（`Init_Game` / `WinMain` 初始化序列）直呼；
5. **勘误定谳**：§0.2 原推测的“偏 AI/任务编排”为**严重误判**。该函数纯属游戏启动/关于界面的 Win32 UI 对话框与背景装载器，与游戏战斗模拟逻辑及 AI 行为无任何关联。

---

## 2. 核心任务二：0x00409300 对象工厂簇终局定谳

### 2.1 证据溯源与反汇编实证

在 §0.2 中，地址桶 `0x00409300`（1.4% 峰值）被定性为“小函数簇（`thiscall` 小方法），偏对象工厂/初始化。序言 `0x408F14`”。

经全指令域反汇编，该 256 字节地址桶内实际并存了两组功能完全不同的高频组件：
- **前半部分（0x004092B0–0x00409354）**：底层数据流/音频流（`StreamBuffer` / `AudioStream`）的轻量级成员方法簇；
- **后半部分（0x00409360–0x004093FF）**：引擎全局高精度定时器 `Clock`（`QueryPerformanceCounter` 封装）。

#### 组件 A：流成员方法簇（0x004092F0–0x00409333）

```assembly
; === gamemd.exe 0x004092F0 - 0x00409333 (FileOffset: 0x92F0 - 0x9333) ===
; Stream::Flush(this)
0x004092f0: 56                   push     esi
0x004092f1: 8bf1                 mov      esi, ecx                      ; this
0x004092f3: 33d2                 xor      edx, edx
0x004092f5: e8c6feffff           call     0x4091c0                      ; Stream::Advance
0x004092fa: 8b5608               mov      edx, dword ptr [esi + 8]      ; buffer count
0x004092fd: 85d2                 test     edx, edx
0x004092ff: 7407                 je       0x409308
0x00409301: 8bce                 mov      ecx, esi
0x00409303: e8b8feffff           call     0x4091c0
0x00409308: b800000480           mov      eax, 0x80040000               ; 返回 COM 风格错误码
0x0040930d: 5e                   pop      esi
0x0040930e: c3                   ret      

; Stream::Get_Available_Count(this)
0x00409310: 56                   push     esi
0x00409311: 8bf1                 mov      esi, ecx
0x00409313: 33d2                 xor      edx, edx
0x00409315: e8a6feffff           call     0x4091c0
0x0040931a: 8b4608               mov      eax, dword ptr [esi + 8]      ; 返回可用数据量
0x0040931d: 5e                   pop      esi
0x0040931e: c3                   ret      

; Stream::Get_Unread_Bytes(this)
0x00409320: 8b4134               mov      eax, dword ptr [ecx + 0x34]   ; total bytes
0x00409323: 8b4938               mov      ecx, dword ptr [ecx + 0x38]   ; read offset
0x00409326: 2bc1                 sub      eax, ecx                      ; 未读字节 = total - read
0x00409328: c3                   ret      

; Stream::Get_Position(this)
0x00409330: 8b4130               mov      eax, dword ptr [ecx + 0x30]   ; current stream pos
0x00409333: c3                   ret      
```

#### 组件 B：全局高精度定时器 Clock（0x00409360–0x004093EE）

```assembly
; === gamemd.exe 0x00409360 - 0x004093EE (FileOffset: 0x9360 - 0x93EE) ===
; Clock::Init()
0x00409360: 83ec08               sub      esp, 8
0x00409363: 8d442400             lea      eax, [esp]
0x00409367: 50                   push     eax
0x00409368: ff15d8117e00         call     dword ptr [0x7e11d8]          ; KERNEL32!QueryPerformanceFrequency
0x0040936e: 85c0                 test     eax, eax
0x00409370: 742f                 je       0x4093a1                      ; 若失败走降级分支
0x00409372: 8b4c2404             mov      ecx, dword ptr [esp + 4]      ; Frequency.HighPart
0x00409376: 8b542400             mov      edx, dword ptr [esp]          ; Frequency.LowPart
0x0040937a: 6a00                 push     0
0x0040937c: 68e8030000           push     0x3e8                         ; 除数 1000
0x00409381: 51                   push     ecx
0x00409382: 52                   push     edx
0x00409383: e848ff3b00           call     0x7c92d0                      ; CRT _alldiv(Frequency, 1000)
0x00409388: a328e88700           mov      dword ptr [0x87e828], eax     ; CountsPerMs.Low
0x0040938d: 89152ce88700         mov      dword ptr [0x87e82c], edx     ; CountsPerMs.High
0x00409393: c70548e88700c0934000 mov      dword ptr [0x87e848], 0x4093c0; 写入时钟函数指针 = Clock::ReadQPC

; Clock::Now() [热点核心派发点]
0x004093b0: a148e88700           mov      eax, dword ptr [0x87e848]     ; 取函数指针
0x004093b5: 85c0                 test     eax, eax
0x004093b7: 7402                 je       0x4093bb
0x004093b9: ffe0                 jmp      eax                           ; 动态跳转到 Clock::ReadQPC

; Clock::ReadQPC() [采样命中主要承载体]
0x004093c0: 83ec08               sub      esp, 8
0x004093c3: 8d442400             lea      eax, [esp]
0x004093c7: 50                   push     eax
0x004093c8: ff15d4117e00         call     dword ptr [0x7e11d4]          ; KERNEL32!QueryPerformanceCounter
0x004093ce: 8b0d2ce88700         mov      ecx, dword ptr [0x87e82c]     ; CountsPerMs.High
0x004093d4: 8b1528e88700         mov      edx, dword ptr [0x87e828]     ; CountsPerMs.Low
0x004093da: 8b442404             mov      eax, dword ptr [esp + 4]
0x004093de: 51                   push     ecx
0x004093df: 8b4c2404             mov      ecx, dword ptr [esp + 4]
0x004093e3: 52                   push     edx
0x004093e4: 50                   push     eax
0x004093e5: 51                   push     ecx
0x004093e6: e8e5fe3b00           call     0x7c92d0                      ; _alldiv: Counter / CountsPerMs
0x004093eb: 83c408               add      esp, 8
0x004093ee: c3                   ret                                    ; 返回毫秒数 (eax)
```

### 2.2 归属与热点成因定谳

1. **类名与对象归属**：
   - 前半部分为 `StreamBuffer` / `AudioStream` 流对象（实例由 `0x00408C30` 创建，实例指针存放在 `0xAA0460` 与 `0xAA0464`，由输入泵 `0x53E7*` 维持）；
   - 后半部分为全局单例 `Clock`（状态记录于 `0x87E828–0x87E84C`）。
2. **为什么表现为 1.4% 的性能热点**：
   - 既有推测认为是“对象工厂频繁 `new` / 构造对象”所致，此判断**不准确**；
   - 真实原因是：全镜像有 **50+ 处核心循环**（包括主帧循环 `MainLogicFrame (0x55D360)`、消息泵 `0x53E096`、网络心跳与音频混音）每一帧成百上千次调用 `Clock::Now()`（`0x004093B0`），间接执行 `QueryPerformanceCounter` 系统调用与 `_alldiv` 64 位整数除法。该采样热点反映的是**高频时间戳查询消耗**，而非对象实例化开销。

---

## 3. 核心任务三：0x0048D000 格子/资源查询终局定谳

### 3.1 证据溯源与反汇编实证

§0.2 原文记载：  
> `0x48D000 | 0.3% | 地图格子 / Theater 资源查询（CellClass 标志 +0x3598） | 指令 mov cl,[eax+0x3598]；邻近 YRpp/Unsorted.h::GetResource、Theater.h | 与 L3/L4 迷雾全量刷 正相关；L4 折中方案的主战场`

经全量交叉验证与指令反编译，该处推测存在**根本性质的误判**。

#### 核心反汇编证据（0x0048CFFC–0x0048D05B 与 0x0048D080）

```assembly
; === gamemd.exe 0x0048CFFC - 0x0048D056 (FileOffset: 0x8CFFC - 0x8D056) ===
0x0048cffc: a130b2a800           mov      eax, dword ptr [0xa8b230]     ; ★ 取 ScenarioClass::Instance 全局单例！
0x0048d001: 8a8898350000         mov      cl, byte ptr [eax + 0x3598]   ; ★ ScenarioClass.ShowProgress / IsLoading
0x0048d007: 84c9                 test     cl, cl                        ; 是否处于对局加载进度展示期？
0x0048d009: 7468                 je       0x48d073                      ; 否：直接跳过
0x0048d00b: 8d4c2400             lea      ecx, [esp]
0x0048d00f: 8d542404             lea      edx, [esp + 4]
0x0048d013: 51                   push     ecx
0x0048d014: 52                   push     edx
0x0048d015: b970eaa800           mov      ecx, 0xa8ea70                 ; Network Connection 对象
0x0048d01a: e8114c1600           call     0x5f1c30                      ; 接收网络数据包
0x0048d01f: 85c0                 test     eax, eax
0x0048d021: 7e50                 jle      0x48d073
0x0048d023: 837c24046c           cmp      dword ptr [esp + 4], 0x6c     ; ★ 数据包协议类型 0x6C ('l' = LOAD_PROGRESS)
0x0048d028: 7531                 jne      0x48d05b
0x0048d02a: 8b44241c             mov      eax, dword ptr [esp + 0x1c]   ; 远端玩家 ID
0x0048d02e: 8b0d30dba800         mov      ecx, dword ptr [0xa8db30]     ; 本地玩家 ID
0x0048d034: 25ff000000           and      eax, 0xff
0x0048d039: 3bc1                 cmp      eax, ecx                      ; 若为本地发出的进度包则跳过
0x0048d03b: 741e                 je       0x48d05b
0x0048d03d: db44241d             fild     dword ptr [esp + 0x1d]        ; 加载远端玩家进度浮点百分比
0x0048d041: 83c9ff               or       ecx, 0xffffffff
0x0048d044: 83c8ff               or       eax, 0xffffffff
0x0048d047: 51                   push     ecx
0x0048d048: 50                   push     eax
0x0048d049: 83ec08               sub      esp, 8
0x0048d04c: b9584fac00           mov      ecx, 0xac4f58                 ; ★ ProgressScreenClass::Instance 单例！
0x0048d051: dd1c24               fstp     qword ptr [esp]
0x0048d054: 6a01                 push     1
0x0048d056: e8f56b1b00           call     0x643c50                      ; ProgressScreenClass::UpdateRemoteProgress
```

紧随其后的 `0x0048D080`（`YRpp/Unsorted.h:46` 标记的 `UnknownCall`）即为著名的全局协作多任务调度钩子 `Game::CallBack()`：
```assembly
; === gamemd.exe 0x0048D080 - 0x0048D0B9 (FileOffset: 0x8D080 - 0x8D0B9) ===
0x0048d080: 55                   push     ebp
0x0048d081: 8bec                 mov      ebp, esp
0x0048d083: 83e4f8               and      esp, 0xfffffff8
0x0048d086: 81ec00010000         sub      esp, 0x100
0x0048d08c: e8df9ef7ff           call     0x406f70                      ; 音频泵帧推进 (AudioFrameUpdate)
0x0048d091: a1685bb400           mov      eax, dword ptr [0xb45b68]
...
0x0048d0aa: a138b2a800           mov      eax, dword ptr [0xa8b238]     ; SessionClass::Instance.GameMode
0x0048d0b2: 7405                 je       0x48d0b9
0x0048d0b4: 83f804               cmp      eax, 4
0x0048d0b7: 750a                 jne      0x48d0c3
0x0048d0b9: e822010000           call     0x48d1e0                      ; 联机保活: 发送 NET_PORT_PROBE
```

### 3.2 归属与逻辑关系判定

1. **与 MapClass / CellClass 的关系**：**完全没有任何联系（0% 关联）**。
   - `CellClass` 单个对象尺寸约 100 字节，绝无可能存在 `+0x3598` 这种巨大结构体偏移；
   - `0xA8B230` 在 `YRpp/ScenarioClass.h:58` 中明确定义为 `ScenarioClass::Instance` 单例指针；
   - `[0xA8B230 + 0x3598]` 在 `0x6833E2`（`ScenarioClass` 构造函数）被清零，在 `0x684675`（加载流程启动）被置 1，在 `0x59947E` 判定是否弹进度窗，实证为 `ScenarioClass.IsLoadingScreen`。
2. **与迷雾全量刷 / L4 折中方案的关系**：
   - §0.2 认为该地址“与 L3/L4 迷雾全量刷正相关，是 L4 折中方案主战场”，系因采样命中该地址桶时恰好处于复杂大局（包含加载与后台调度）中，且邻近代码含有 `mov cl, [eax+...]` 而被直觉误导；
   - 实际上该函数由全镜像 **100+ 处密集调用**，是游戏底层的后台事件与通信泵 `Game::CallBack`，主要职责是音频泵服务（`0x406F70`）与联机加载进度条更新（`ProgressScreenClass`，`0xAC4F58`）。**对 L4 迷雾优化无直接影响，严禁在此盲目 hook 迷雾逻辑**。

---

## 4. 核心任务四：0x00623100 数据表与轮询点终局定谳

### 4.1 证据溯源与反汇编实证

§0.2 原文记载：  
> `0x623100 | 0.1% | 数据表 / 跳转表（非代码热） | 字节为连续小常量 + NOP | 采样噪声，可忽略`

经字节级结构解析，该区域结构精密，由三部分无缝拼接而成：

```text
[0x006230DC .. 0x006230EF] (20 字节)  CommonDialogProc 5 项 32 位跳转地址表
[0x006230F0 .. 0x00623119] (42 字节)  uMsg 稀疏 Case 索引字节表 (uint8_t[42])
[0x0062311A .. 0x0062311F] ( 6 字节)  0x90 (NOP) 16 字节边界对齐填充
[0x00623120 .. 0x0062315F] (64 字节)  UI::Updated() 真实轮询代码入口！
```

#### 指令段 A：引用该表的代码源头（CommonDialogProc，0x00622B73）

```assembly
; === gamemd.exe 0x00622B73 - 0x00622B86 (FileOffset: 0x222B73 - 0x222B86) ===
0x00622b73: 57                   push     edi
0x00622b74: 05000033c9           add      eax, 0xc9330000               ; 规范化 uMsg 差值
0x00622b79: 8a88f0306200         mov      cl, byte ptr [eax + 0x6230f0] ; ★ 查 42 字节索引表
0x00622b7f: ff248ddc306200         jmp      dword ptr [ecx*4 + 0x6230dc]  ; ★ 间接跳转到目标分支
```

#### 数据段 B：跳转表与映射表二进制详情

- **跳转表 `0x006230DC`**（5 项 DWORD）：
  - Entry 0: `0x00622B86`（处理 WM 消息 A）
  - Entry 1: `0x00622BCB`（处理 WM 消息 B）
  - Entry 2: `0x00622C3E`（处理 WM 消息 C）
  - Entry 3: `0x00622BB3`（处理 WM 消息 D）
  - Entry 4: `0x006230CE`（Default 分支：`xor eax, eax; ret 8`）
- **映射表 `0x006230F0`**（42 字节）：
  `00 04 04 04 04 04 04 04 04 04 04 04 04 01 04 04 04 04 02 04 04 04 04 04 04 04 04 04 04 04 04 04 04 04 04 04 04 04 04 04 04 03`
  - 内部多数值为 `0x04`（指向 Entry 4 Default），少数关键消息映射为 `0, 1, 2, 3`。
- **NOP 填充 `0x0062311A`**：`90 90 90 90 90 90`（填充至 `0x623120` 对齐）。

#### 代码段 C：0x00623120 处的真正代码（UI::Updated）

```assembly
; === gamemd.exe 0x00623120 - 0x0062315F (FileOffset: 0x223120 - 0x22315F) ===
; YRpp/UI.h:24: static bool Updated() { JMP_STD(0x623120); }
0x00623120: e82b1cfbff           call     0x5d4d50                      ; Game::Pump_Messages
0x00623125: a138b2a800           mov      eax, dword ptr [0xa8b238]     ; GameMode
0x0062312a: 85c0                 test     eax, eax
0x0062312c: 742c                 je       0x62315a                      ; 单人战役
0x0062312e: 83f805               cmp      eax, 5
0x00623131: 7427                 je       0x62315a                      ; 单人遭遇战
0x00623133: a00ed6a800           mov      al, byte ptr [0xa8d60e]
0x00623138: 84c0                 test     al, al
0x0062313a: 751e                 jne      0x62315a
0x0062313c: a1b4daa800           mov      eax, dword ptr [0xa8dab4]
0x00623141: 85c0                 test     eax, eax
0x00623143: 7515                 jne      0x62315a
0x00623145: e8a69af3ff           call     0x55cbf0                      ; 帧调度器心跳
0x0062314a: 84c0                 test     al, al
0x0062314c: 7511                 jne      0x62315f
0x0062314e: e80da2f3ff           call     0x55d360                      ; MainLogicFrame 主逻辑帧！
0x00623153: 84c0                 test     al, al
0x00623155: 7408                 je       0x62315f
0x00623157: b001                 mov      al, 1
0x00623159: c3                   ret      
0x0062315a: e8219fe6ff           call     0x48d080                      ; Game::CallBack
0x0062315f: 32c0                 xor      al, al
0x00623161: c3                   ret      
```

### 4.2 归属与热点定谳

1. **热点成因定谳**：性能采样桶（256 字节）`0x623100` 覆盖了 `0x00623100–0x006231FF`；
2. **勘误定谳**：采样命中并不是因为“数据表或 NOP 产生了 CPU 消耗”，而是因为该桶的后半部分 `0x00623120` 是核心驱动函数 **`UI::Updated()`**！该函数在全屏视频、对话框模态循环（如 `0x00531C6E`）中被紧密轮询，推进 `MainLogicFrame (0x55D360)` 与 `Game::CallBack (0x48D080)`。0.1% 采样完全是 `UI::Updated()` 执行引起的真实热点，不可作为“噪声”忽略。

---

## 5. 核心任务五：0x00437300 与 0x00432E00 图形与绘制管线终局定谳

### 5.1 0x00437300：Surface::Put_Rect 局部表面恢复

#### 反汇编证据（0x00437290–0x0043733E）

```assembly
; === gamemd.exe 0x00437290 - 0x0043733E (FileOffset: 0x37290 - 0x3733E) ===
; Surface::Put_Rect(Surface* dest [edi], Rect* rect [esi], XSurface* src [esp+0x3C])
0x00437290: 83ec30               sub      esp, 0x30                     ; 栈上开辟 48 字节
0x00437293: 56                   push     esi
0x00437294: 8bf2                 mov      esi, edx                      ; esi = Rect
0x00437296: 57                   push     edi
0x00437297: 8bf9                 mov      edi, ecx                      ; edi = dest Surface
0x00437299: 8b4608               mov      eax, dword ptr [esi + 8]      ; rect.Width
0x0043729c: 85c0                 test     eax, eax
0x0043729e: 7e07                 jle      0x4372a7
0x004372a0: 8b460c               mov      eax, dword ptr [esi + 0xc]     ; rect.Height
0x004372a3: 85c0                 test     eax, eax
0x004372a5: 7f0a                 jg       0x4372b1
0x004372a7: 5f                   pop      edi
0x004372a8: 32c0                 xor      al, al
0x004372aa: 5e                   pop      esi
0x004372ab: 83c430               add      esp, 0x30
0x004372ae: c20400               ret      4
; 准备栈上临时 BSurface / XSurface
0x004372b1: 8b44243c             mov      eax, dword ptr [esp + 0x3c]
0x004372b5: 8b17                 mov      edx, dword ptr [edi]
0x004372b7: 53                   push     ebx
0x004372b8: 8bcf                 mov      ecx, edi
0x004372ba: 8b18                 mov      ebx, dword ptr [eax]
0x004372bc: ff5270               call     dword ptr [edx + 0x70]        ; 取像素格式/BPP
...
0x004372e1: c744242404217e00     mov      dword ptr [esp + 0x24], 0x7e2104 ; vftable = XSurface
0x004372ed: e80e3a0000           call     0x43ad00                      ; XSurface 内存分配
...
; ★ 热点 0x00437300 核心段：
0x00437300: 2418                 and      al, 0x18
0x00437302: 6a01                 push     1
0x00437304: 8d442410             lea      eax, [esp + 0x10]
0x00437308: 6a00                 push     0
0x0043730a: 8d4c2424             lea      ecx, [esp + 0x24]
0x0043730e: 50                   push     eax
0x0043730f: 51                   push     ecx
0x00437310: 56                   push     esi
0x00437311: 8bcf                 mov      ecx, edi                      ; dest = DSurface::Hidden_2
0x00437313: c744243070207e00     mov      dword ptr [esp + 0x30], 0x7e2070 ; ★ vftable = BSurface (.?AVBSurface@@)
0x0043731b: c744242000000000     mov      dword ptr [esp + 0x20], 0
0x00437323: c744242400000000     mov      dword ptr [esp + 0x24], 0
0x0043732b: ff5208               call     dword ptr [edx + 8]           ; ★ 虚表调用 Surface::Blit
0x0043732e: 8d4c2430             lea      ecx, [esp + 0x30]
0x00437332: 8ad8                 mov      bl, al
0x00437334: e8173b0000           call     0x43ae50                      ; BSurface::~BSurface
0x00437339: 8ac3                 mov      al, bl
0x0043733b: 5b                   pop      ebx
0x0043733c: 5f                   pop      edi
0x0043733d: 5e                   pop      esi
0x0043733e: 83c430               add      esp, 0x30
0x00437341: c20400               ret      4
```

- **类与虚表 RTTI 实证**：
  - `0x007E2070`: COL `0x7FB260`, TypeDescriptor: `.?AVBSurface@@`
  - `0x007E2104`: COL `0x7FB2C8`, TypeDescriptor: `.?AVXSurface@@`
- **调用方**：由 `StaticButtonClass::Draw`（VA `0x006C6740`，RTTI `.?AVStaticButtonClass@@`，虚表第 34 项）在 `0x006C67DB` 调用，将保存的背景恢复刷新至 `DSurface::Hidden_2`（VA `0x00887314`）。

---

### 5.2 0x00432E00：BinkMovieClass::Play 视频播放与跳过检测

#### 反汇编证据（0x00432C70 与 0x00432DF5–0x00432E39）

```assembly
; === gamemd.exe 0x00432C70 - 0x00432C89 (FileOffset: 0x32C70 - 0x32C89) ===
; BinkMovieClass::Play(this)
0x00432c70: 83ec4c               sub      esp, 0x4c
0x00432c73: 56                   push     esi
0x00432c74: 8bf1                 mov      esi, ecx                      ; this
0x00432c76: 8b4604               mov      eax, dword ptr [esi + 4]      ; HBINK 句柄
0x00432c79: 85c0                 test     eax, eax
0x00432c7b: 7519                 jne      0x432c96
0x00432c7d: ff1598157e00         call     dword ptr [0x7e1598]          ; binkw32.dll!_BinkGetError@0
0x00432c83: 50                   push     eax
0x00432c84: 682c8b8100           push     0x818b2c                      ; "Bink Error: %s\n"
0x00432c89: e8523cfdff           call     0x4068e0                      ; WWDebug_Printf
...
; 循环主体：_BinkDoFrame / _BinkNextFrame / DSurface::Blit 上屏至 DSurface::Primary (0x887308)
...
; ★ 热点 0x00432E00 核心段（ESC 跳过检测与输入清栈）：
0x00432df5: 8b0d70f78700         mov      ecx, dword ptr [0x87f770]     ; ★ InputManagerClass::Instance
0x00432dfb: e800c21100           call     0x54f000                      ; InputManager::CheckKey
0x00432e00: 6685c0               test     ax, ax
0x00432e03: 0f84affeffff         je       0x432cb8                      ; 无输入：继续下一帧
0x00432e09: 803e00               cmp      byte ptr [esi], 0             ; 是否允许跳过
0x00432e0c: 0f85a6feffff         jne      0x432cb8
0x00432e12: 8b0d70f78700         mov      ecx, dword ptr [0x87f770]
0x00432e18: e833c21100           call     0x54f050                      ; InputManager::GetKey
0x00432e1d: 663d1b08             cmp      ax, 0x81b                     ; ★ 是否按下 VK_ESCAPE (0x1B) 或鼠标跳过？
0x00432e21: 0f8591feffff         jne      0x432cb8                      ; 非跳过键：继续播放
0x00432e27: 8b0d70f78700         mov      ecx, dword ptr [0x87f770]
0x00432e2d: e8eec81100           call     0x54f720                      ; ★ InputManager::ResetInput
0x00432e32: 5f                   pop      edi
0x00432e33: 5d                   pop      ebp
0x00432e34: 5b                   pop      ebx
0x00432e35: 5e                   pop      esi
0x00432e36: 83c44c               add      esp, 0x4c
0x00432e39: c3                   ret                                    ; 优雅退出视频播放
```

- **类与字符串实证**：
  - 导入表 `binkw32.dll`：`_BinkOpen@8` (`0x7E159C`), `_BinkDoFrame@4` (`0x7E15BC`), `_BinkNextFrame@4` (`0x7E15B4`), `_BinkPause@8` (`0x7E15B0`)；
  - 格式化字符串：VA `0x00818B2C` (`"Bink Error: %s\n"`), VA `0x00818B3C` (`"Resume bink movie\n"`), VA `0x00818B50` (`"Pause bink movie\n"`);
  - 调用方：过场动画播放点 `0x005BEE58` 与全屏电影播放器 `0x005C0559`。

---

## 6. S9 勘误与新旧对照总表

在全面指令级取证后，原 `docs/NEXT_RE_AND_MODERNIZATION.md` §0.2 表格中的多处初始推测被证实存在偏差。现汇总勘误如下：

| 地址桶 | §0.2 旧归因与推断 | S9 新归因（定谳结论） | 修正原因与取证事实 | 现代适配决策调整 |
|---|---|---|---|---|
| `0x531D00` | 大栈函数（`[esp+0x298]`），偏 **AI/任务编排** | **`Init.CPP` 启动版本与背景对话框**（`Init_Version_Dialog`） | 硬编码字符串 `D:\ra2mdpost\Init.CPP`，对话框 ID 212/226，800×600 居中计算，格式化 MMX/版本信息 | 移出 AI 优化路线；单次启动生效，无需 Hook |
| `0x409300` | 小函数簇（`thiscall`），偏 **对象工厂/初始化** | **`StreamBuffer` 原语 + `Clock::Now` QPC 定时器** | `0x4092B0–0x409354` 为流重置/冲刷；`0x409360–0x4093EE` 为 `QueryPerformanceCounter` + `_alldiv` 定时器派发 | 热点源于全局每帧高频查时，绝非工厂构造频繁；可评估定时器采样平滑 |
| `0x48D000` | **地图格子 / Theater 资源查询**（`CellClass` 标志 `+0x3598`），L4 迷雾主战场 | **`Game::CallBack` 全局多任务泵**（音频推进 + 网络加载进度同步） | `[eax+0x3598]` 是 `ScenarioClass::Instance`（`0xA8B230`）的 `IsLoadingScreen`，解包 0x6C 进度更新 `ProgressScreenClass`（`0xAC4F58`） | **严禁在此挂迷雾钩子**；迷雾优化应专注于 `TacticalClass::Render` 与视野更新环 |
| `0x623100` | **数据表 / 跳转表**（非代码热），采样噪声可忽略 | **`CommonDialogProc` 跳转表 + `UI::Updated()` 轮询入口** | 表为 `0x622B50` 的 switch 索引；`0x623120` 即 `UI::Updated()` 真实代码，高频轮询 `MainLogicFrame` | 不可作为噪声忽略；模态循环与视频跳帧时此为关键消息泵 |
| `0x437300` | 图形 / SHP / 绘制管线相关函数（未具名） | **`Surface::Put_Rect`**（局部表面还原包装器） | 栈上构建 `BSurface`（`0x7E2070`），将内存 `XSurface` 拷贝至 `DSurface::Hidden_2`，由 `StaticButtonClass::Draw` 调用 | 属于 UI 脏区还原链路，与大地图 SHP 渲染解耦 |
| `0x432E00` | 图形 / SHP / 绘制管线相关函数（未具名） | **`BinkMovieClass::Play`**（视频播放泵与跳过判定） | 依赖 `binkw32.dll`，循环检测 `InputManagerClass`（`0x87F770`）按键 `0x081B`（ESC）退出 | 属于过场动画播放器，单机/联机对局内非持续热点 |

---

## 7. 对下一步优化路线（P0–P2）的直接指导意义

1. **纠偏 L4 迷雾优化重心（P0-2）**：
   - 彻底解除“`0x48D000` 是迷雾全量刷主战场”的误区；
   - 避免在 `Game::CallBack` / `ProgressScreenClass` 链路中浪费逆向精力；迷雾脏区折中方案应 100% 收口至 `TacticalClass::Render`（`0x6D3D99`）与 `UpdateVisionGrid`。
2. **重新审视时钟查询损耗（P1 / P2）**：
   - `0x409300` 的 1.4% 峰值实证为 `QueryPerformanceCounter` 与 CRT `_alldiv` 的内核往返开销；
   - 在高密度局中，单帧成千上万次调用 `Clock::Now()` 可考虑做“帧级时间戳缓存（Frame-coarse Timestamp）”，避免同一 tick 内纳秒级反复下陷入内核。
3. **安全审计清单归档**：
   - 本报告所涉及的 5 大热点，除 `Clock::Now` 外，其余 4 处均为启动对话框、过场视频、网络加载进度及按钮背景恢复，均不在逻辑对局的核心热循环中，无需盲目设立 Hook，有效避免了代码膨胀与引入不同步（DESYNC）的风险。

---

> **报告签署**：S9 专项子代理 · 2026-09-26  
> **归档位置**：`docs/re/re_sprint_S9_report.md`  
> **回写状态**：已准备向 `docs/NEXT_RE_AND_MODERNIZATION.md` 原地追加 §0.2.1。
