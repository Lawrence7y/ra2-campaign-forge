# RC-4 尾窗可观测性：主窗口锚点、单例清零时序、收尾禁令面

> **卡片**：GOAL-3T 第 §342 轮（离线，零真机）
> **写域**：`lead/goal2_rc4_trigger_20261022/**`
> **纪律**：只读磁盘。未启动游戏、未写 `ra2youli/**`、未改任何母本、未动 harness。
> **证据分级**：`[实证]`（磁盘字节 + 断言） / `[推演]` / `[待实测]`，永不升格。
> **脚本**：`_window_anchor.py`（五组断言 F1–F5，全绿才 EXIT=0）
> **产物**：`WINDOW_ANCHOR_OUTPUT.txt`

---

## §0 三句话结论

1. **主窗口有了不靠标题猜的句柄来源。** `0x007775C0` 就是窗口类 `"Yuri's Revenge"` 的 `WndProc`（`RegisterClassA` 现场 `0x00777CA5` 前一条 `mov [esp+0x28], 0x7775c0`），该窗口由 `CreateWindowExA` 创建（IAT `0x007E14D4`），**hwnd 写入全局 `[0x00B73550]`**（`0x00777CD6`）。`[实证]`

2. **★ 上一轮建议的「方案 D」在结构上不可行，本轮撤回。** `WM_DESTROY` 块内 `[0x887368]=0`（`0x00777803`）与 `[0xB73550]=0`（`0x0077780E`）**在同一个基本块，相隔 11 字节，中间只有一条 `mov eax,[0xa8edd8]`**。⇒ 「轮询到单例为 0 就去驱动窗口」时，**窗口句柄已同时被清零**，没有可驱动的对象。`[实证]`

3. **但拿到了一个更好的判据：`[0x00A8EDD8]` 是引擎自己的退出状态机。** 引擎退出路径 `0x006BE0CF` 用 `PostMessageA` 向 `[0xB73550]` 投 `Msg=2`（**WM_DESTROY，不是 WM_CLOSE**），随后在 `0x006BE0DC` 起的等待环里 `cmp [0xa8edd8], edi / je`。该环每轮调用 `0x005D4D50`（消息泵：`IsDialogMessageA` + `TranslateAcceleratorA` + `TranslateMessage`）。⇒ **`[0xA8EDD8]` 是「已进尾窗」的现成、无副作用、可 RPM 读的探针。** `[实证]`

---

## §1 主窗口身份（F1/F2）

### §1.1 窗口类注册现场

`0x00777C30` 起是一个窗口创建函数（`sub esp,0x38` / 4 个 callee-saved push），中间填 `WNDCLASSA`（`WNDCLASSA` 大小 0x28，`[esp+0x20]` 起）：

| `[esp+…]` | 字段 | 值 | 来源 |
|---|---|---|---|
| `+0x24` | `style` | `3`（`CS_VREDRAW|CS_HREDRAW`） | `0x00777C71` |
| `+0x28` | **`lpfnWndProc`** | **`0x007775C0`** | `0x00777C79` |
| `+0x34` | `hInstance` | `esi`（函数入参 this） | `0x00777C89` |
| `+0x38` | `hIcon` | `[0xB7354C]`（`LoadIconA` 结果） | `0x00777C8D` |
| `+0x3C` | `hCursor` | `[0xB73548]`（`LoadCursorA` 结果） | `0x00777C91` |
| `+0x48` | **`lpszClassName`** | **`0x00849F48`** = `"Yuri's Revenge"` | `0x00777C9D` |

`0x00777CA5 call [0x7E14D8]` = **`RegisterClassA`**。`[实证]`

### §1.2 窗口创建

```
0x00777CC0  push 0x2CA0000        ; dwStyle
0x00777CC5  push 0x849F48         ; lpWindowName = "Yuri's Revenge"
0x00777CCA  push 0x849F48         ; lpClassName  = "Yuri's Revenge"
0x00777CCF  push ebx              ; hWndParent = NULL
0x00777CD0  call [0x7E14D4]       ; CreateWindowExA
0x00777CD6  mov [0xB73550], eax   ; ★ 主窗口句柄落全局
```

IAT 解析（按导入目录，**RVA 口径**，见 §5 坑 1）：

| 槽 | 符号 |
|---|---|
| `0x007E14D4` | `USER32.dll!CreateWindowExA` |
| `0x007E14D8` | `USER32.dll!RegisterClassA` |
| `0x007E14AC` | `USER32.dll!PostMessageA` |
| `0x007E1394` | `USER32.dll!DefWindowProcA` |
| `0x007E14F4` | `USER32.dll!IsDialogMessageA` |
| `0x007E14F8` | `USER32.dll!TranslateAcceleratorA` |
| `0x007E14BC` | `USER32.dll!TranslateMessage` |

⇒ **`[0x00B73550]` 是主窗口句柄的唯一权威来源。** 这比 harness 现行的 `find_main_window`（`EnumWindows` + `w>200` + `visible`）确定性高得多：后者会枚举到所有顶层窗口，`>200` 只是启发式；而 `[0xB73550]` 是创建者亲手存的。`[实证]`

---

## §2 单例与 hwnd 同时清零（F3）—— 撤回方案 D 的依据

### §2.1 WM_DESTROY 块原文

```
0x007777F3  mov  ecx, [0x887368]      ; 单例
0x007777F9  cmp  ecx, ebx             ; ebx==0（0x7775C8 的 xor ebx,ebx）
0x007777FB  je   0x777809
0x007777FD  mov  eax, [ecx]           ; vtable
0x007777FF  push 1
0x00777801  call [eax]                ; v[0](this, 1) = deleting dtor
0x00777803  mov  [0x887368], ebx      ; ★ 单例 = 0
0x00777809  mov  eax, [0xA8EDD8]      ; ★ 中间唯一一条
0x0077780E  mov  [0xB73550], ebx      ; ★ 主窗口 hwnd = 0
0x00777814  cmp  eax, ebx
0x00777816  je   0x777822
0x00777818  mov  [0xA8EDD8], 2        ; 退出状态 → 2
0x00777822  pop  edi ; pop esi ; xor eax,eax ; pop ebx ; pop ecx ; ret 0x10
```

### §2.2 为什么这否掉了方案 D

上一轮（§341 §4）建议：「**兜底：`WM_CLOSE` 后轮询 `[0x887368]`，一旦为 0 立刻驱动**」。

磁盘字节给出的顺序是：单例清零 → (11 字节后) → hwnd 清零。两者**在同一次消息处理里、同一个基本块内**，中间没有任何 `ret`/`jmp`/`call`。因此：

- 任何「读到单例 == 0」的时刻，`[0xB73550]` **必然已经是 0**（或即将在本轮指令流内变 0，中间只隔一条 `mov`+`mov`，无法插入外部动作）。
- 而且 `WM_DESTROY` 是窗口销毁链路的一环：即使 `[0xB73550]` 还有值，`IsWindow(hwnd)` 也已为假。
- ⇒ **「清 0 后再驱动窗口」这条路不存在。** 撤回。

**★ 这不影响 `WM_CLOSE` 本身有效**：`WM_CLOSE` 仍能到达 `WM_DESTROY`（`0x777A80` 跳表里 `0x10` 走 default `0x7779B9` → `DefWindowProcA` → 销毁窗口 → `WM_DESTROY`）。撤回的只是「清 0 后再驱动」这个**兜底时序**，不是「发 `WM_CLOSE`」。

### §2.3 那 18% 到底靠什么

三条事实拼起来：

1. 引擎自己的退出路径在投完 `WM_DESTROY` 后进入 `0x006BE0DC` 的等待环，**每轮调 `0x005D4D50`（消息泵）**。
2. 该泵在 `0x005D4DBC` 读单例，**紧跟 `test ecx,ecx / je`**——是**带闸消费**。
3. 崩溃链的四个宿主 `0x4A8960 / 0x6ABD30 / 0x6403A0 / 0x654320` 各只有 1–2 个 E8 调用者，且这些调用者**不在**上面那个消息泵里（`0x5D4D50` 的调用链只走 `0x53E770`/`0x49F740`/`0x724200`）。

⇒ **尾窗内「GUI 记录更新再命中一次」不是泵本身发起的，而是尾窗里其他仍在跑的路径发起的**，并且那些路径**不带零闸**（崩溃站点 30 个里宿主 `0x654320` 两侧无闸）。这与 18% 的形状吻合：尾窗长度由退出流程决定，而尾窗里是否有某个不带闸的路径跑到，取决于运行期状态。`[推演]`（机制 `[实证]`，归因 `[推演]`）

---

## §3 `[0x00A8EDD8]` 作为尾窗判据（F4）

### §3.1 引擎退出路径原文

```
0x006BE0B6  mov  [0xA8EDD8], edi      ; edi==1（0x006BE08C mov edi,1）
0x006BE0BC  mov  ecx, 0xA83D10
0x006BE0C1  call 0x720770
0x006BE0C6  call 0x406D40
0x006BE0CB  push ebx                  ; wParam = 0
0x006BE0CC  push ebx                  ; lParam = 0
0x006BE0CD  push 2                    ; ★ Msg = 2 = WM_DESTROY
0x006BE0CF  mov  ecx, [0xB73550]      ; ★ 主窗口
0x006BE0D5  push ecx                  ; hWnd
0x006BE0D6  call [0x7E14AC]           ; PostMessageA
0x006BE0DC  call 0x5D4D50             ; 消息泵（IsDialogMessageA 等）
0x006BE0E1  cmp  [0xA8EDD8], edi      ; ★ 还等于 1 就继续泵
0x006BE0E7  je   0x6BE0DC
0x006BE0E9  xor  esi, esi             ; 退出环结束
```

### §3.2 状态机语义

| `[0xA8EDD8]` | 含义 | 写入点 |
|---|---|---|
| `1` | 退出流程已启动、正在等 `WM_DESTROY` 处理完 | `0x006BE0B6`（edi=1） |
| `2` | `WM_DESTROY` 已处理完 | `0x00777818`（仅当原值 ≠ 0 时写） |

`0x00777814 cmp eax, ebx / je 0x777822` —— 只有**原来非 0** 才写 `2`；原来就是 0（例如 `WM_CREATE` 没成功、单例从未建立）则**保持 0**。这解释了 `0x7777C3`（`new` 失败分支写单例 0）那条路径为什么不会把状态机推进到 2。

### §3.3 为什么这是可用探针

- **只读、无副作用**：一个 u32，`ReadProcessMemory` 即可。
- **不需要猜窗口**：不依赖 `EnumWindows` 启发式。
- **语义明确**：`1→2` 的跳变**恰好**是 `WM_DESTROY` 执行完的时刻，也就是「单例已清零、尾窗开始」的同一时刻。
- **★ 但它不能在跳变后救场**：跳变后 hwnd 已清零（§2）。它的价值在**事后归因**——判定「这趟到底有没有进过尾窗」，从而把「0 新异常」拆成「没进尾窗」vs「进了尾窗但没命中」。

⇒ 这是一个**把 18% 的分母说清楚**的工具，不是一个提高命中率的工具。这个区分是本轮最重要的诚实边界。

---

## §4 对 harness 收尾禁令面的影响（供裁决 #1/#3）

### §4.1 两条禁令写死在源码里

| 位置 | 原文 | 影响 |
|---|---|---|
| `qc151_trip.harness3_u8.py:47` | `` - `taskkill` **非本卡自己 `Popen` 的 pid**（★ 只杀 `self.launch_pid`） `` | 挡住 A8 修复（按载体路径清扫 loader 子进程 gamemd） |
| `qc151_trip.harness3_u8.py:1493` | `★ **不改**游戏内存、不注入、**不发消息到窗口过程**。` | 挡住 #3 修复（发 `WM_CLOSE`） |

⇒ **A8 与 #3 都不是工程量问题，而是「需要先改一条铁律」。** 这一点此前登记时没有明确：两项都被描述成「harness 改动 + 补丁副本」，但真正的闸门是**禁令文本本身**，而禁令是外部裁定（`QC141:171`）写进来的。

### §4.2 但存在一个已开先例的合规通道

`qc151_trip.harness3_u8.py:349` 已有先例：`--allow-loader` 被明确写成「§1 禁止面的**唯一**例外通道，且**不是**解禁」——双键（`--allow-loader` + `--trip-id`）、默认关、留痕、S-4 降级为 WARN。

⇒ **若 Lead 裁决要做 #3，正确的形态不是「悄悄发 `WM_CLOSE`」，而是照 `--allow-loader` 的样子再开一个双键通道**（例如 `--graceful-exit` + `--trip-id`），默认关、留痕、`--measure=0` 等价。这样禁令文本改成「除两个已登记例外」，而不是被绕过。

**A8 更适合走另一条道**：A8 的清扫目标是**本趟自己创建的载体目录下的进程**，身份锚点是路径而非 pid，且已有 `QueryFullProcessImageNameW` 先例（`u8_v1v2_probe.py:196-220`）。它争的不是「能不能杀别人的进程」，而是「本趟创建的载体里的子进程算不算本趟自己的」——这是**定义问题**，不是禁令豁免问题。建议裁决时把两者拆开。

---

## §5 本轮踩到的两个坑

1. **导入目录所有字段都是 RVA，不是 VA。** `ImageDirectoryEntryToData` 的语义是 RVA；`opt+0x68` 给的 `ImportDirectoryRVA=0x7955C0`，我第一版直接当 VA 传给 `va2off`，落进 `.detour` 段，一路 `unpack_from` 到文件尾外抛 `struct.error`。**修正=先加镜像基数 `0x400000`**。这与上一轮 `SectionHeader.VirtualAddress` 是 RVA 的坑**同源但不同处**——那处是段表，这处是导入目录，两处都得加。`[实证]`

2. **`capstone.disasm` 从任意偏移起解会错位。** 直接对 `0x007777F0` 起解，第一版输出 `add dword ptr [eax], eax` / `retf` 这种垃圾——因为 `0x007777F3` 才是指令边界。**修正=从确定的边界起解**（本件全部从 `mov ecx,[0x887368]` 这条已知指令的地址起）。这与 `NEWCRASH` §229「禁单次 `disasm()` 全段结论」同源。

---

## §6 诚实边界

- **F4 的 `[0xA8EDD8]` 值域只静态确认了 0/1/2 三个写入**；运行期是否被别处改写（例如 `.data` 里另有别名）**未普查**。做探针前应补一次全段立即数扫描。
- **§2.3 的归因是排除法**：我证明了消息泵带闸、崩溃链接点不带闸、且崩溃链接点不在泵里；但**没有**直接观测到「尾窗里到底是哪条路径命中了站点」。坐实需 dmp 或断点。
- **`[0xB73550]` 的写入点已穷举 = 3 处，全在同一个函数内**（`0x00777C30` 起的主窗口创建函数）：`0x00777CD6`（主分支 `CreateWindowExA` 后写）、`0x00777D7E`（次分支 `0x777CB6 je 0x777D56` 后另一次 `CreateWindowExA` 再写）、`0x0077780E`（`WM_DESTROY` 清零）。⇒ 「`WM_DESTROY` 后为 0」在**不重建窗口**的前提下成立；重建必走同一函数、必再写。**这条已从「未穷举」收口为「3 处、可枚举」。** 备注：`0x00777D7E` 之前那次 `CreateWindowExA` 的 `dwStyle=0x82000000`、类名同为 `"Yuri's Revenge"`，是否 `WS_POPUP` 形态的子窗未判定，但它接同一 `[0xB73550]` 槽，属同一窗口对象族。
- **`WM_CLOSE` 走 default 这条**本轮未复验，沿用 `crash_site.json lifecycle.msg_cases["0x10"].map_index=5 → 0x7779B9` 的既有记载（该记载本身是 `[实证]`）。
- **本件不改变待裁七项的方向**，只把第 3 项（改不改 `WM_CLOSE`）的**可行性边界**收窄了：收尾改造仍值得做（把 0 提到 >0），但「尾部窗口内主动驱动」这条**不能靠轮询单例触发**，得改成「在 `WM_CLOSE` 之后、状态机还等于 1 的期间主动驱动」——而那段时间窗口还活着，是**唯一可行的驱动窗**。

---

## §7 【§343 追加 · 勘误】default 出口不是直接调 `DefWindowProcA`

> append-only，不删除 §2.2 与 §6 的任何原文。本节更正其中一句机制描述。

### §7.1 原文错在哪

§2.2 末段写：「`WM_CLOSE` 本身仍有效（跳表 `0x10`→default `0x7779B9`→`DefWindowProcA`→销毁→`WM_DESTROY`）」，
§6 末条也沿用。**「→`DefWindowProcA`」这一步是跳过的**：`0x7779B9` 并不直接调它。

### §7.2 实际链路（逐条反汇编）

```
0x007779B9  mov  edx, [esp+0x20]        ; lParam
0x007779BD  mov  ecx, [esp+0x1c]        ; wParam
0x007779C1  push edx / push ecx / push eax(msg) / push edi(hwnd)
0x007779C3  mov  ecx, [0x87F770]        ; ★ 游戏自己的某对象
0x007779CB  call 0x54F790               ; ★ 游戏自己的窗口过程（不是系统默认）
0x007779D0  test eax, eax
0x007779D2  je   0x7779DD               ; 返回 0 ⇒ 继续往下
0x007779D4  ... ret 0x10                ; 返回非 0 ⇒ 直接返回
0x007779DD  cmp  eax, 0x286             ; 特殊消息（WM_MOUSEACTIVATE 之外的自定义）
0x007779E6  jne  0x777A64
   ...（0x286 分支）
0x00777A70  call [0x7E1394]             ; ★ 才是 USER32!DefWindowProcA
0x00777A76  ... ret 0x10
```

**关键**：`0x54F790` 是**独立的游戏窗口过程**，有自己的消息分派：

| 内部分派表 | 覆盖 msg | 备注 |
|---|---|---|
| `0x54FB4C`（6 项） | `0x100..0x105` | `WM_KEYDOWN`/`WM_KEYUP`/`WM_CHAR` 等 |
| `0x54FB64`（8 项） | `0x202..0x209` | `WM_LBUTTONDBLCLK` 等 |

**两张表都不含 `WM_CLOSE`（0x10）**，因此 `WM_CLOSE` 在 `0x54F790` 内走 `0x54FB3D` 收尾
（`pop`×4 / `xor eax,eax` / `add esp,0x10` / `ret 0x10`）**返回 0**，然后才由外层
`0x7779DD` 继续判断 `0x286`，不走该分支即落到 `0x777A64` 的 `DefWindowProcA`。

⇒ **结论方向不变**：`WM_CLOSE` 最终确实到达 `DefWindowProcA`，因而走默认销毁语义。
但中间**多了一层游戏自己的窗口过程**，且该层对 `WM_CLOSE` 明确返回 0 表示「不处理」。
这个层次在 §342 里被抹平了，会影响任何「在 `WM_CLOSE` 路径上挂钩子」的设计。

### §7.3 附带的正面收获：分派表读法（§342 未自记的坑）

`0x007776AE jmp dword ptr [edx*4 + 0x777A80]` 的两级表**不能按 msg 号直接索引**：

```
0x0077769A  lea  ecx, [eax - 1]      ; ★ 先减 1（eax = msg）
0x0077769D  cmp  ecx, 0x13           ; msg-1 > 0x13 ⇒ 越界
0x007776A0  ja   0x7779B9            ; 越界直接走 default
0x007776A6  xor  edx, edx
0x007776A8  mov  dl, byte [ecx + 0x777A98]   ; ★ byte 索引表
0x007776AE  jmp  dword [edx*4 + 0x777A80]    ; ★ dword 目标表
```

修正后语义自洽（本件首读直接按 msg 号索引，得到 `msg 0x01→0x7777F3` 即「WM_CREATE 跳进销毁块」，
明显不可能），真值为：

| msg | 索引 | 目标 | 语义 |
|---|---|---|---|
| `0x01` WM_CREATE | 0 | `0x0077778D` | 创建单例 |
| `0x02` WM_DESTROY | 1 | `0x007777F3` | 销毁单例 + 清 hwnd |
| `0x03` | 2 | `0x007777CE` | — |
| `0x0F` | 3 | `0x007776B5` | — |
| `0x14` WM_ACTIVATE | 4 | `0x00777781` | — |
| 其余（含 **`0x10` WM_CLOSE**） | 5 | `0x007779B9` | default |

⇒ **本次独立复验了 §6「`WM_CLOSE` 走 default」这条，且是逐条指令复算，不是引用既有记载。**

### §7.4 退出状态机的第二入口

`[0xA8EDD8]` 写入点穷举后**恰好 2 处**（`0x006BE0B6` 写 `edi`=1、`0x00777818` 写 2），
但**投递 `WM_DESTROY` 的路径有两条**：

| 路径 | 投递点 | 特点 |
|---|---|---|
| A | `0x006BE0D6` | 无 `hwnd==0` 保险 |
| B | `0x006BEC78` | ★ 多带 `test eax,eax / je`（`hwnd==0` 时跳过整个等待环） |

两条都在投递前把 `[0xA8EDD8]` 置 1、投递后进 `0x005D4D50` 等待环。
⇒ 「`[0xA8EDD8]==1` 表示已进退出流程」这条**对两条路径都成立**，探针可靠性不依赖走哪条。

### §7.5 §343 新增断言

`_dispatch_verify.py`（**13 条断言，EXIT=0**）+ `_dispatch_negctl.py`（索引表左移一格 ⇒ 2 条 FAIL，负控转红）：

| # | 断言 |
|---|---|
| E1 | `lea ecx,[eax-1]` 先减 1；索引 byte 读 `0x777A98`；目标 dword 读 `0x777A80` |
| E2 | WM_CREATE→`0x77778D`、WM_DESTROY→`0x7777F3`、WM_CLOSE→`0x7779B9` |
| E3 | msg 1..0x14 的索引全部落在目标表前 6 项内（无越界） |
| E4 | `0x77761A call [0x7E1394]` = `DefWindowProcA`（IAT 解析）；**default 出口 `0x7779B9` 不直接调它**（调 `0x54F790`） |
| E5 | `[0xA8EDD8]` 写入点恰好 2 处，VA 集合 = `{0x006BE0B6, 0x00777818}` |
| E5b | 第二退出路径 `0x006BEC78` 同样 `PostMessageA` 投 Msg=2，且多带 `hwnd==0` 保险 |

### §7.6 对 #3 裁决的影响（新增一条约束）

若走 `WM_CLOSE` 路线，**不能假设「发过去就等于系统默认销毁」**：
`0x54F790` 这层会先看到 `WM_CLOSE` 并返回 0。当前它返回 0（「不处理」）所以照常下传，
但这是**运行期行为**、不是硬契约；若将来该层对 `WM_CLOSE` 返回非 0（`0x7779D2 je` 不成立），
窗口就不会被销毁、`WM_DESTROY` 不会来、RC-4 尾窗**根本不会形成**。
⇒ 收尾改造若依赖 `WM_CLOSE`，**必须同时检测「尾窗是否真的形成」**——而这正好是本件 §3 的
`[0xA8EDD8]` 能给的。两项应一起做，不能只做一半。
