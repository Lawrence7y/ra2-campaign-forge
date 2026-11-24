# P02 · 焦点旗标睡眠自旋：循环不是死锁而是「失焦等待环」——泵内 DispatchMessageA 可送达激活沿；「快进」命名被字节否定

**日期**：2026-11-04 · 编号 P02（swarm_20261104）
**性质**：只读静态反汇编。零真机、零启动、零改动母本（SHA256 校验 PASS 后全程只读）。
**证据分级**：[字节] = 本文亲跑亲读；[推导] = 字节 + 形态推断；[推测] = 明写猜测。

---

## 0. 现场自证

| 项 | 值 | 命令 |
|---|---|---|
| SHA256 | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`（与冻结件一致） | `python -I -X utf8 probe1_scene.py` |
| eng.coverage | `(99.99837567729335, 1394120, 66)` = 覆盖率 99.9984% / **1,394,120 insns** / 66 处重同步（capstone 静默停止已规避） | 同上 |
| 真机零占用 | gamemd.exe / ra2loader.exe / YURI.exe 均无运行任务 | `tasklist //FI "IMAGENAME eq gamemd.exe"`（另两同名查法）→ `信息: 没有运行的任务匹配指定标准。` |

---

## 1. 结论

1. **[字节] 主循环等待块对 GameMode∈{0,5}（Campaign=0 / Skirmish=5）是无界「失焦等待环」**：每轮 `Sleep(500)` + 泵 + 旗标重查，旗标仍 0 则回环（唯一回边 0x55D3AE→0x55D38D）。不是死锁：泵内有 `DispatchMessageA`，激活沿可达 WndProc、旗标可被写 1、环自解。
2. **[字节] 泵 0x5D4D50 判定为真消息泵**：0x5D4E47 `call dword ptr [0x7E14C0]`，IAT 解析 = **USER32!DispatchMessageA**；前有 0x5D4E40 TranslateMessage、过滤链 IsDialogMessageA/TranslateAcceleratorA。队列模式 [0xAA0444] 静态初值 0（BSS），mode 1/2 仅当 `_fsopen(path,"wb"/"rb",0x40)` 成功才置位（文件型事件通道，非局内常态）——**mode 0 下每条真消息都被分派，WM_ACTIVATEAPP 无阻碍到达 WndProc**。
3. **[字节] hwnd==0 时泵完全短路**：0x5D4D5A `test eax,eax` / 0x5D4D5E `je 0x5D4E66` 直接 ret，**连泵计数器 0xAA0430 都不加**（inc 在 je 之后）。hwnd==0 ⇒ 激活沿永不被取用 ⇒ 旗标永不可置 1 ⇒ 等待环与 WinMain 两个忙等环（0x6BDD03/0x6BDD2E，纯自旋无 Sleep）静态完备不可出——这是唯一「真死锁」形态，只发生在窗口已建前/已毁后。
4. **[字节] hwnd [0xB73550] 全镜像恰 3 写者**：0x777CD6 / 0x777D7E（CreateWindowExA 两分支，全屏门 [0x89F978] 选支）建窗写入；0x77780E（WndProc 销毁路径）清 0 并同块清 CCToolTip 单例 [0x887368]、exitstate→2。局内正常期 hwnd≠0。
5. **[字节] 时间量级**：GameMode=0/5 被困时循环周期 ≈ 0.500–0.516 s ⇒ **≈2 次/秒**。冻结 21.156 s ⇒ **42–43 次连续读到 0**（21.156/0.500=42.3；15.6ms 粗分辨率下 21.156/0.516≈41.0 → 41–42）。观测区间映射：2.56 s≈5–6 轮、24.73 s≈49–50 轮，全部落在 k×0.5 s 量化格上，无矛盾。GameMode=3/4 的 Sleep(10) 支**不构成循环**（单发后直落帧体），不可能由此产生秒级冻结。
6. **[字节+推导] 概率评估**：逐轮翻转概率不是抛硬币——旗标只在 `WM_ACTIVATEAPP(wParam≠0)` 被取用并分派时翻转（唯一写者 0x7778CE）。无外部激活者时 **P(翻转)=0/轮** ⇒ 困住是确定性、时长无上限；观测的 2.56–24.73 s 分布 = 「失焦→复焦」的外部延迟（他窗关闭、系统 UI 抢还焦点、SetForegroundWindow 等）。强行 Poisson 建模 λ≈0.07/s 属 [推测]。
7. **[字节] 文档冲突裁决**：**r063a 对，clock_frame_loop.md 的「快进」命名错（机制半对）**。0xA8ED80 全镜像恰 46 处引用=45R+1W，唯一写式 0x7778CE 由 WM_ACTIVATEAPP 激活沿驱动，引擎自证字符串 `Focus_Restore()/Focus_Loss()/Focus gained/Focus lost`；「快进」无任何输入路径支撑。机制侧「=1 时跳过 Sleep 块」字面对，但跳过的是**整块（含两处泵调用）**，不是「跳 Sleep 但仍在泵」——这使「快进」读法双重错误。且 clock_frame_loop.md 自己 477 行已有 [实证] 勘误行（AppHasFocus）与 r063a 一致——冲突实为该文档内部新旧标签未同步。
8. **[字节，两文档皆缺的新发现] 等待块结构错误**：clock_frame_loop.md §3.2 伪码（216–217 行）把等待写成单发 `if(!flag){Sleep(500);Pump;}`，漏了 0x55D3A7 重查 + 0x55D3AE 回边。字节裁定：GameMode∈{0,5} 时是**等焦点的无界循环**；这正是「长期困住」的字节根基，也是冻结 2.56–24.73 s 的唯一形态学来源。

---

## 2. 证据

### 2.1 MainLogicFrame 头部逐字节（probe1，亲跑）

```
0055D360 a0a0e9a800        mov al,[0xA8E9A0]          ; InGame
0055D36B 84c0              test al,al
0055D371 0f84580b0000      je 0x55DECF ── pop edi/esi/ebp; mov al,1; pop ebx;
                                          add esp,0x1b4; ret @0x55DEDB   [字节，冻结出口①]
0055D377 a080eda800        mov al,[0xA8ED80]          ; 焦点旗标
0055D37C c60558cdab0001    mov byte [0xABCD58],1      ; 「帧处理中」闩（任务伪码未列）
0055D383 84c0              test al,al
0055D385 7534              jne 0x55D3BB               ; 旗标=1 → 跳过 0x55D387–0x55D3BA 整块
0055D387 8b35f0117e00      mov esi,[0x7E11F0]         ; IAT=KERNEL32!Sleep（本probe解析PASS）
0055D38D a138b2a800        mov eax,[0xA8B238]         ; GameMode   ←循环顶
0055D392 85c0              test eax,eax
0055D394 7405              je 0x55D39B                ; ==0 Campaign → Sleep(500) 支
0055D396 83f805            cmp eax,5
0055D399 7517              jne 0x55D3B2               ; !=5 → Sleep(10) 支
                                                      ; ==5 Skirmish 落入 500 支
0055D39B 68f4010000        push 0x1F4
0055D3A0 ffd6              call esi                   ; Sleep(500)
0055D3A2 e8a9790700        call 0x5D4D50              ; 泵
0055D3A7 a080eda800        mov al,[0xA8ED80]
0055D3AC 84c0              test al,al
0055D3AE 74dd              je 0x55D38D                ; ★唯一回边：旗标仍0 → 回循环顶
0055D3B0 eb09              jmp 0x55D3BB
0055D3B2 6a0a / ffd6       push 0xA; call esi         ; Sleep(10)
0055D3B6 e895790700        call 0x5D4D50              ; 泵
（0x55D3BB 直落帧体，无回跳 —— Sleep(10) 支单发，loop_backedges 仅一条 0x55D3AE→0x55D38D）
```
原始字节抽查 `0x55D377..0x55D390` = `a080eda800 c60558cdab0001 84c0 7534 8b35f0117e00 a138b2a800`。
inc 块复核：`0x55DE73 8b1584eda800 (mov edx,[0xA8ED84])` / `0x55DE7E 42 (inc edx)` / `0x55DE81 891584eda800 (mov [0xA8ED84],edx)`。

### 2.2 泵 0x5D4D50 全解（probe2/probe5，G-83 边界=分支闭包+ret 扫描）

边界：从 0x5D4D50 的前向闭包 max=0x5D4E6E，闭包内**恰 1 个 ret（0x5D4E6D）**，0x5D4E6E-6F 为 nop 填充，下一函数 0x5D4E70。

```
005D4D50 a15035b700        mov eax,[0xB73550]         ; hwnd
005D4D58 85c0 / 0f8402010000 test; je 0x5D4E66      ; hwnd==0 → 直接 ret
005D4D64..77 8b1d3004aa00/43/891d3004aa00             ; 泵计数 [0xAA0430]++（hwnd!=0 才执行）
005D4D7D e8ee99f6ff        call 0x53E770              ; 包装A：mode0=PM_NOREMOVE 探针
005D4D82 0f84dc000000      je 0x5D4E66                ; 无消息 → 泵结束
005D4D8A/90/96 8b1df4147e00/8b3df8147e00/8b2dbc147e00 ; ebx/edi/ebp = IAT
005D4DA6 e88599f6ff        call 0x53E730              ; 包装B：PM_REMOVE 取消息（WM_QUIT→0 退出）
005D4DB7 e884a9ecff        call 0x49F740              ; 0xBEEF 内部消息特判→MapViewOfFileEx
005D4DEA ffd3              call ebx                   ; IsDialogMessageA 过滤链 [0xABFC94/0xABFCA0]
005D4E18 ffd7              call edi                   ; TranslateAcceleratorA 链 [0xABFCBC/0xABFCC8]
005D4E31/35 ffd0           call eax                   ; [0xABFD34] 回调（全镜像仅 1 读 ⇒ 恒 NULL，跳过）
005D4E40 ffd5              call ebp                   ; TranslateMessage
005D4E47 ff15c0147e00      call dword [0x7E14C0]      ; ★ USER32!DispatchMessageA
005D4E59 e81299f6ff        call 0x53E770              ; 再探
005D4E60 0f8536ffffff      jne 0x5D4D9C               ; 还有消息 → 循环
005D4E6D c3                ret
```
IAT 亲解：`0x7E14C0→USER32!DispatchMessageA`、`0x7E14BC→TranslateMessage`、`0x7E14F4→IsDialogMessageA`、`0x7E14F8→TranslateAcceleratorA`、`0x7E1484→PeekMessageA`、`0x7E14D4→CreateWindowExA`、`0x7E14D8→RegisterClassA`、`0x7E13C0→GetCursorPos`、`0x7E11E8/EC→Enter/LeaveCriticalSection`。
全镜像直呼泵者 43 处（probe3 E8 扫描），MLF 内 2 处 = 0x55D3A2（等待环）/0x55D3B6（单发支），帧体另有 0x55D830。

**包装 0x53E770 队列模式**（决定激活沿可达性，probe6）：
- `[0xAA0444]` 23 处引用；写者 6：0x53E527(=1)、0x53E59D(=2)、0x53E67A(=0)、0x53E958/0x53EAD8(=0 复位)、0x53E2BD(=esi 动态)。
- 置 1/置 2 的前置都是 `call 0x7CA845(esi, 0x828138="wb" / 0x82813C="rb")` 返回非零，而 0x7CA845=`push 0x40; …; call 0x7CA814`——`_fsopen(path,mode,_SH_DENYNO=0x40)` 形态 [推导]。文件打不开（常态）⇒ mode 保持 BSS 初值 0。
- mode 0 路径：0x53EB16 PeekMessageA(**PM_NOREMOVE** 探针) → 0x53EB25 `cmp [0xAA0444],1; jne 0x53EBE8` 直接带「有消息」返回 → 包装 B 0x53E740-4F 以 PM_REMOVE 循环取到 → 主泵 Translate+**Dispatch**。mode 2 路径（0x53E879 起）只对 WM_PAINT 分派（0x53E89B `cmp eax,0xF` → 0x53E8A1 dispatch）并吞掉其余真消息 + 合成内部事件——**若运行期处于 mode 2，激活沿会被吞**；但置位条件（"rb" 文件可打开）在正常局内不成立 [推导]。

### 2.3 旗标唯一写者链条（probe4 逐字节复钉，与 r063a T2 全同）

```
0077782B 3d05020000        cmp eax,0x205              ; WM_RBUTTONUP 上界
0077783C 83f81c            cmp eax,0x1C               ; ★ WM_ACTIVATEAPP
0077783F 745f              je 0x7778A0                ; 唯一入写路径
007778A0 3b3d5035b700      cmp edi,[0xB73550]         ; 门① 参数hwnd==主窗
007778AC 8b44241c          mov eax,[esp+0x1C]         ; wParam
007778B4 0f95c1            setne cl                   ; 新值=(wParam!=0)
007778B9 8a1580eda800      mov dl,[0xA8ED80]          ; 旧值
007778BF 3bd1/0f8482000000 cmp; je 0x777949           ; 门② 新旧相同→不写（状态沿去重）
007778C9 0f95c0            setne al
007778CE a280eda800        mov byte [0xA8ED80],al     ; ★★ 全镜像唯一写式
007778D3 755b              jne 0x777930               ; 激活沿→
00777930 e8ebfaffff        call 0x777420              ; Focus_Restore 处理器
00777935 68f89e8400        push 0x849EF8              ; "Focus gained\n"
00777942 c605a0008a0001    mov byte [0x8A00A0],1
```
字符串亲读：0x849E94=`'Focus_Loss()\n'`、0x849ECC=`'Focus_Restore()\n'`、0x849EF8=`'Focus gained\n'`、0x849F08=`'Focus lost\n'`、0x849F48=`"Yuri's Revenge"`。
WndProc 头 0x7775C0（`51 8b0d28768800 53 33db 56 3bcb 57 7457`），注册点 0x777C79 `c7442428 c0757700`（WNDCLASS.lpfnWndProc），0x777CA5 `call [0x7E14D8]=RegisterClassA`。
旗标全普查（probe3）：**46 处 = 45 读 + 1 写**；读形消费簇含 WM_PAINT 门 0x7776C1（`803d80eda80001 cmp byte[0xA8ED80],1`）、LogicUpdate 门 0x55E204、DDraw 焦点函数 0x759A83/0x759AAB 等。

### 2.4 hwnd 生命周期（probe3/probe4）

| 写点 | 字节 | 语义 |
|---|---|---|
| 0x777CD6 | `a35035b700` ← 0x777CD0 `call [0x7E14D4]`（CreateWindowExA） | 建窗支 A（全屏门 [0x89F978]@0x777CAB 选支） |
| 0x777D7E | `a35035b700` ← 0x777D78 `call [0x7E14D4]` | 建窗支 B（`6a08` dwExStyle=8，窗口化） |
| 0x77780E | `891d5035b700`（ebx=0） | 销毁路径：同块 `mov [0x887368],ebx`（清 CCToolTip 单例）、读 exitstate 0xA8EDD8 → 写 2。[「WM_DESTROY」标签=推导] |

⇒ 生命周期：WinMain boot（注册函数 0x777C30 的 E8 直呼 0x6BD9CF/0x6BDB0C，r063a T3 在案）建窗写入 → 局内全程 ≠0 → 窗口销毁时清 0。**hwnd==0 ⟺ 建窗前/已毁**，此时泵短路（§2.2），激活沿通道死。

### 2.5 WinMain 忙等环（r063a T4.1 复钉）

```
006BDD03 e84870f1ff   call 0x5D4D50     ←┐
006BDD08 a080eda800   mov al,[0xA8ED80]  │ 纯忙等（无 Sleep，100% CPU）
006BDD0D 84c0/74f2    test; je 0x6BDD03 ─┘
006BDD2E e81d70f1ff   call 0x5D4D50     ←┐ 同构第二环
006BDD38 74f2         je 0x6BDD2E      ─┘
```

### 2.6 时间量级算式

```
GameMode∈{0,5}（Campaign=0 / Skirmish=5，写值点 0x48CF94(ebx=0)/0x52E10F(5) 亲钉）：
  T_iter = Sleep(500) + T_pump(空队列≈µs) + 开销
         ≈ 0.500–0.516 s（0.516 = 15.6ms 调度量化上限；timeBeginPeriod(1) 常驻时取下限）
  f ≈ 1/T ≈ 1.94–2.00 次/秒

  21.156 s → N = 21.156 / 0.500 = 42.3 → 42–43 轮连续读到 0
             （15.6ms 粗分辨率：21.156/0.516 ≈ 41.0 → 41–42；合并：42±1）
  2.56  s → 5–6 轮；24.73 s → 49–50 轮 —— 全部落在 k×0.5 s 格上

GameMode=3/4（LAN=3@0x52DD7F / Internet=4@0x52DD61）：Sleep(10) 单发、无回边 → 不可能秒级冻结

概率：P(第 k 轮退出) = P(WM_ACTIVATEAPP(TRUE) 在第 k 轮被分派)。
  无激活者 ⇒ P=0（确定性困住，时长无上限）；
  观测有限时长 ⇒ 每次冻结对应一次外部复焦。Poisson 拟合 [推测]：λ≈1/13.6s，P(T>t)=e^(−λt)。
```

### 2.7 真机判别式（零真机，本节为交付判据；全部只读）

**A. 冻结中单点采样**（调试器/外部读取）：
| VA | 本路径成立时的期望 |
|---|---|
| [0xA8ED80] | ==0（=1 则不可能滞留环内，0x55D3AC je 必出） |
| [0xA8B238] | ∈{0,5}（=3/4 则本环不构成，冻结另有原因） |
| [0xB73550] | !=0（==0 → 泵短路死锁变体） |
| [0xAA0430] | 隔 2 s 两次采样增量 ≈4（每轮 +1，0x5D4D77）；冻结 ⇒ 泵没在跑 |
| [0xA8ED84] | 两次采样不变（CurrentFrame 冻结） |
| [0xABCD58] | ==1（0x55D37C 入口闩，环内无人清） |
| [0xA8ED81] | ==1 ⇒ 发生过 SC_MINIMIZE（旁证失焦路径） |
| [0x8A00A0] | =1 ⇒ 至少走过一次焦点沿后继 |
| [0xAA0444] | ==0（≠0 且==2 ⇒ 激活沿会被包装吞掉，另案） |

**B. 栈签名**（x32dbg 暂停看栈）：镜像内最近返回地址 = **0x55D3A2**（Sleep 返回址，正睡时恰在 KERNEL32!Sleep 帧之上）或 **0x55D3A7**（泵返回址）——两值轮流出现即等待环坐实。

**C. 行为学（无注入）**：
- C1 冻结中点击游戏窗口（用户激活）→ ≤1 迭代（≈0.5 s）解冻 ⇒ 成立。
- C2 无用户操作版：外部进程 `SetForegroundWindow(FindWindowA(NULL,"Yuri's Revenge"))` → 解冻 ⇒ 成立且证明激活沿经泵分派。
- C3 冻结中 `GetForegroundWindow()` ≠ 游戏 hwnd ⇒ 失焦态坐实（本环的前提）。
- C4 反证：若采样点 [0xA8ED80]==1 且 EIP 不在 0x55D38D–0x55D3B2 ⇒ 冻结不在本环，另找。

---

## 3. 与本仓既有记载的对账

| 记载 | 本次裁定 | 依据 |
|---|---|---|
| `re_atlas/evidence/r063a_flag_writer_closure.md`：0xA8ED80=焦点旗标，唯一写者 0x7778CE，45R+1W | **确认，逐字节一致** | probe3 普查 46=45R+1W；probe4 复钉 0x77782B–0x777942 全链、字符串锚、注册点 |
| `docs/re/clock_frame_loop.md:86/215/433`：「快进/跳过 Sleep 标志」「非快进」 | **命名错，机制半对**（见下） | 写者唯一且为激活沿；引擎自证 Focus 字符串；无快进输入路径 |
| `docs/re/clock_frame_loop.md:477`（[实证] 勘误行）：「0xA8ED80 为 AppHasFocus…Sleep(500)=单机暂停、Sleep(10)=联机后台保活，仅失焦后台生效」 | **确认，与 r063a 及本次字节一致** | 0x55D394/0x55D399 分支值 = Campaign/Skirmish vs LAN/Internet（0x52DD61=4、0x52DD7F=3、0x52E10F=5、0x48CF94=ebx(0)） |
| `docs/re/clock_frame_loop.md:86`「=1 时 0x55D360 跳过 Sleep 块」 | **字面成立但须加严**：跳过的是整块 0x55D387–0x55D3BA = 两处 Sleep + **两处泵调用**；「跳 Sleep 但仍在泵」的读法被 `jne 0x55D3BB` 否定 | 0x55D385 `7534` |
| `docs/re/clock_frame_loop.md:26`（§0.8）「0x55D360 的 Sleep(10) 是固定值」 | **以偏概全**：Sleep(10) 支仅 GameMode∉{0,5} 且单发；Campaign/Skirmish 走 Sleep(500) 循环。该行与本 doc 477 行也自相矛盾 | §2.1 字节 |
| `docs/re/clock_frame_loop.md:216–217` §3.2 伪码（单发等待） | **结构错误（新裁决）**：漏 0x55D3A7 重查 + 0x55D3AE 回边，GameMode∈{0,5} 为无界等待环 | §2.1；loop_backedges 恰 1 条回边 |
| `docs/re/clock_frame_loop.md:88`：GameMode 571 处引用 | 本次普查 **570 处**（差 1，未归因；不影响结论） | probe3 |
| 任务基线：MainLogicFrame 3 ret（0x55D877/0x55DEC7/0x55DEDB） | 亲见 0x55D877（probe5）、0x55DEDB（本次）；0x55DEC7 未亲见（基线在案，诚实账注明） | §2.1/§4 |
| r063a T4.1/RA4：WinMain 自旋环、泵计数 7 组写者、主泵 hwnd==0 不加计数 | 全部复钉一致（写者集 0x432CDD/0x5D4D77/0x5DC459/0x759210/0x759A3F/0x775A7F/0x77F925） | probe3/probe4 |
| 基线：0x7E11F0=Sleep、0x7E1530=timeGetTime | 解析 PASS | probe1 |

---

## 4. 诚实账（没做的 / 样本薄的 / 可能错的 / 冲突的）

1. **零真机**：§2.7 判别式全部未真机执行（铁律 1），只有静态推导背书。
2. **泵包装 mode-1 细节粗读**：0x53E770 的合成事件段（0x53EA19–0x53EBE3，内部事件队列 [0xAA0368]→memcpy 0x1C 仿 MSG）只走读未闭合；[0xAA0368] 生产者未普查；mode 1/2 的启用方（哪个功能去 `_fsopen` 该文件）未追调用者。「mode 1/2 非局内常态」为 [推导]（依据 "wb"/"rb" + 0x40=_SH_DENYNO 形态与 BSS 初值 0），非 [字节]。
3. **[0xAA0444] 运行期实际值未观测**：若真机上出现 mode==2 窗口期，激活沿会被包装吞掉（0x53E8A7 丢弃环），本环退化为死锁——已列入判别式 A 的加读项。
4. **0x49F740 的 0xBEEF→MapViewOfFileEx 通道**投递方未追；ESC 处理块 0x53E8E0–0x53E97C 只粗读。
5. **0x77780E 的「WM_DESTROY」标签**是 [推导]（写点字节本身 [字节]；由清 CCToolTip 单例 + exitstate→2 的伴随行为推断，未逐槽验证跳转表 0x777A80 的 idx）。
6. **GameMode 引用计数 570 vs 台账 571 差 1** 未归因（口径或台账笔误）。
7. **MainLogicFrame 第三个 ret 0x55DEC7 未亲见**（本 ask 不需要，基线在案）；MLF 其余调用者（0x608206/0x60D407/0x62314E/0x623D72/0x624271，clock_frame_loop.md:209 记载）未逐一验证。
8. **Poisson 概率模型（λ≈0.07/s）为 [推测]**：观测冻结样本集未在本次掌握，均值 13.6 s 为两点近似。
9. **「冻结 2.56–24.73 s 且无用户操作」的现场归因**：本环只能解释「失焦期间」的冻结（前提 [0xA8ED80]==0 ∧ GameMode∈{0,5} ∧ hwnd≠0）。若冻结发生时窗口实际保有焦点（判别式 A 反例），本环不成立，须另查 0x55E160 节拍路径或 bail 环（r063a T5.1 的判读表已给出分流）。本次只做机制与量级判定，未做现场归因。
10. 与既有台账无未解决冲突；clock_frame_loop.md 内部矛盾（86/215/433 旧标签 vs 477 勘误行）已裁定，未改其文件（写域纪律）。

---

## 5. 复算入口

全部脚本在本目录（`lead/goal3t_nightwatch_20261102/swarm_20261104/P02/`），只读 gamemd.exe，只写本目录：

```bash
cd lead/goal3t_nightwatch_20261102/swarm_20261104/P02
python -I -X utf8 probe1_scene.py        # 覆盖率自证 + MLF 头部逐字节 + 回边 + IAT 抽查
python -I -X utf8 probe2_pump.py         # 泵 0x5D4D50：闭包边界 + ret 扫描 + 43 处调用者   （约 3 min）
python -I -X utf8 probe3_sweep.py        # 六全局访存普查（旗标46/CurrentFrame1007/hwnd197/GameMode570…）（约 3 min）
python -I -X utf8 probe4_r063a_verify.py # r063a 写链复钉 + 字符串锚 + WinMain 忙等环 + 包装主体
python -I -X utf8 probe5_pump_tail.py    # 包装尾段 + IAT 补解 + LogicUpdate/0x55D88E 上下文（约 2 min）
python -I -X utf8 probe6_qmode.py        # 队列模式 [0xAA0444] 写者普查 + 写点上下文          （约 2 min）
```
输出件：`probe3_out.txt` / `probe4_out.txt` / `probe5_out.txt` / `probe6_out.txt`（probe1/probe2 走 stdout）。
共享引擎：`../ra2tool.py`（SHA256 断言 + 重同步线性解码，禁 `md.disasm(blob,va)` 全镜像扫——G-23）。
