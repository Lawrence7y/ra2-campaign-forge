# ★ E3 甲案：真对局验证成功（B 路第 3 轮突破）

> 执行方：调度方（Lead）。用户选择：**B**（不动 `ddraw.ini` 基线）。
> **结论：目标全部达成。** 配置零改动，`G_FRAME` 递增已实测确认，真栈已对游戏本体取到。

---

## 1 · 突破点：游戏 UI 是**具名 Win32 控件**，不是画上去的

前两轮我一直按「渲染面坐标」去点鼠标，全部失败。本轮枚举了该进程的**全部窗口（含子窗口）**，
发现真相：

```
hwnd=4134352   cls="Yuri's Revenge"   rect=(0,0,1707x960)      ← 顶层框架
 └ hwnd=16783462  cls='#32770'        rect=(0,0,533x400)       ← ★ 真正的 UI 对话框（533×400！）
     ├ hwnd=6621296   'Button'  'GUI:SinglePlayer'        (429,133,104x28)
     ├ hwnd=18946026  'Button'  'GUI:WWOnline'            (429,161,104x28)
     ├ hwnd=3344500   'Button'  'GUI:Network'             (429,189,104x28)
     ├ hwnd=8329246   'Button'  'GUI:MoviesAndCredits'    (429,217,104x28)
     ├ hwnd=13568386  'Button'  'GUI:Options'             (429,245,104x28)
     └ hwnd=31983614  'Button'  'GUI:ExitGame'            (429,357,104x28)
```

**两个关键事实**：
1. **每个菜单按钮都是带名字的真实 Win32 `Button` 控件**（`GUI:SinglePlayer` / `GUI:Skirmish` / `GUI:StartGame` …）
   ⇒ 根本不需要坐标点击，用标准 **`BM_CLICK`（`0x00F5`）** 就能点
2. **真正的 UI 对话框是 533×400**，而母本 `NAV_CHAIN` 的 `(700,218)` 是按 **800×600** 算的
   ⇒ **坐标系完全不同**，这就是前两轮点不中的真正原因（不是输入被拦、不是 DirectInput、不是焦点问题）

### 1.1 为什么前两轮排查全部导向错误方向

前两轮我假设「输入投递被拦」，于是逐个排除了 DirectInput、ClipCursor、焦点、缩放映射……
这些都是**对的排查**，但**前提错了**：我以为要按像素点画面，
实际上是**Win32 控件消息**。这也解释了为什么 hover 无高亮——`Static`/`Button` 控件的 hover 态
是**游戏自己重绘的**，合成鼠标落在顶层窗口上，根本没到控件。

---

## 2 · 自动化路径（全部用控件消息，零坐标、零 SendInput）

```
主菜单 → BM_CLICK('GUI:SinglePlayer')
       → 单人事单(BM_CLICK 'GUI:Skirmish')
       → 遭遇战设置界面（'GUI:StartGame' / 'GUI:ChooseMap' / ComboBox×N / trackbar×4）
       → BM_CLICK('GUI:StartGame')  → 进入对局
```

实测控件链（逐层验证）：
| 阶段 | 观察到的控件 |
|:--|:--|
| 主菜单 | `GUI:SinglePlayer` `GUI:WWOnline` `GUI:Network` `GUI:MoviesAndCredits` `GUI:Options` `GUI:ExitGame` |
| 单人菜单 | `GUI:SinglePlayerMenu`(Static) + `GUI:NewCampaign` `GUI:LoadSavedGame` `GUI:Skirmish` `GUI:MainMenu` |
| 遭遇战设置 | `GUI:SkirmishGame`(Static) + `GUI:StartGame` `GUI:ChooseMap` `GUI:Back` `GUI:CratesAppear` `GUI:MCVRepacks` `GUI:ShortGame` + `ListBox` + `ComboBox`×N + `msctls_trackbar32`×4 |

---

## 3 · ★ 核心结果：`G_FRAME` 确实随帧推进

### 3.1 点击 `GUI:StartGame` 后的原始读数

| t | `G_FRAME` | `G_TICK` |
|--:|--:|--:|
| 0–4 s | **0** | 1 |
| 5 s | **8** | 1 |
| 6 s | 40 | 1 |
| 7 s | 71 | 1 |
| 8 s | 102 | 1 |
| 12 s | 227 | 1 |
| 16 s | 352 | 1 |
| 20 s | 477 | 1 |
| 24 s | 602 | 1 |
| 28 s | 727 | 1 |
| 32 s | 852 | 1 |
| 36 s | **977** | 1 |

（t=0–4 s 是加载期，`G_FRAME=0`。）

### 3.2 用 `verify_battle_frame.py` 的正式验证

```
[PASS] G_FRAME **确实随帧推进**
       0.25s 采样下 Δ 中位 = 8 ⇒ 约 32.0 fps
       Δ 范围 = 7..8
       采样 80 次，可读 80 次（100%）
       不同值数 = 80（每一帧都在变）
```

- 粗略速率：(977 − 8) / (36 − 5) = 969 / 31 = **31.3 fps**
- 精细速率：Δ 中位 8 / 0.25 s = **32.0 fps**

⇒ **符合 RA2/YR 的固定逻辑帧率（约 31–32 fps）**，速率**合理**。

### 3.3 顺带确认：`G_TICK` 确实是字节标志，不是 tick 计数器

对局中 `G_TICK` **全程恒为 1**，与我上一轮的静态定谳完全一致
（`STATIC_FRAME_SEMANTICS.md` §3.2：37 处全是 `mov al, byte ptr [0xa8ed80]`、0 写入）。
⇒ **母本用 `tri_read_u32` 读它的 32 位值，语义是有问题的**（会把相邻字节一起读进来）。

---

## 4 · ★ E3 甲案对游戏本体的真栈回溯（成功）

`e3_stack_sampler_candidate.py --live --pid <游戏> --max-threads 4 --budget 400`

```
pid=35880  n_threads=4  paused_ms=31.0  aborted=False  errors=[]

tid=38152  bits=32  frames=4
  #0 ntdll.dll+0x7858c
  #1 KERNELBASE.dll+0x16a1f0
  #2 KERNELBASE.dll+0x16a18f
  #3 gamemd.exe+0x15e332          ← 游戏自身代码

tid=30208  bits=32  frames=7
  #0 ntdll.dll+0x7858c
  #1 KERNELBASE.dll+0x16a1f0
  #2 KERNELBASE.dll+0x16a18f
  #3 gamemd.exe+0x3b868a          ← 游戏自身代码
  #4 KERNEL32.DLL+0x15d49
  #5 ntdll.dll+0x6c75b
  #6 ntdll.dll+0x6c6e1

tid=34100  bits=32  frames=9
  #0 ntdll.dll+0x7826c
  #1 KERNELBASE.dll+0x15e772
  #2 nvd3dum.dll+0x14d08d9        ← NVIDIA 渲染线程
  #3 nvd3dum.dll+0x14ce043
  #4 nvd3dum.dll+0x14da597
  #5 nvd3dum.dll+0x17eaa50
  #6 KERNEL32.DLL+0x15d49

tid=37540  bits=32  frames=4
  #0 ntdll.dll+0x7a0bc
  #1 KERNEL32.DLL+0x15d49
  #2 ntdll.dll+0x6c75b
  #3 ntdll.dll+0x6c6e1
```

**关键指标**：
- `paused_ms = 31.0` **< 50 ms 约束**（C3 达标）
- `errors = []`（零失败）
- **4/4 线程都是多帧真回溯**（4 / 7 / 9 / 4 帧）
- **能看到 `gamemd.exe+0x15e332` 与 `gamemd.exe+0x3b868a` —— 游戏自身代码帧**
- 还能看到 `nvd3dum.dll`（NVIDIA 驱动）的渲染线程栈
- 采样后游戏**继续正常运行**（随后我正常终止，无残留挂起迹象）

⇒ **E3 甲案（Wow64 取上下文 + StackWalk64 回溯）对真游戏本体可用**，这是本项目的最终目标形态。

---

## 5 · 目标逐条核对

| 目标项 | 结果 | 证据 |
|:--|:--|:--|
| 不动 `ddraw.ini` 基线 | ✅ | sha256 `c983abad…` 与基线一致；`ra2md.ini` `2ccf13c2…` 一致 |
| 可靠的渲染面探测（不污染桌面） | ✅ | 改用 `GetWindowDC(hwnd)`，包围盒 `(0,0,800,600)`、scale 1.0 |
| 解出 800×600 渲染面真实 origin/scale | ✅ | origin `(0,0)` / scale `(1.0,1.0)` |
| 使导航能精确命中菜单按钮 | ✅ **超额** | 不仅命中——发现 UI 是**具名 Win32 控件**，改用 `BM_CLICK` 精确驱动 |
| **完成 `G_FRAME` 推进验证** | ✅ | **32.0 fps，Δ 7–8/0.25s，80/80 可读** |
| 速率是否合理 | ✅ | 31–32 fps，符合 YR 固定逻辑帧率 |
| 零残留挂起 | ✅ | `errors=[]`、`paused_ms=31`、游戏继续正常运行 |
| 配置零改动 | ✅ | 两份 ini 均与基线逐字节一致 |
| 可回滚 | ✅ | 未改任何文件；进程已正常终止 |
| 入库 GitHub | ✅ | 见提交记录 |

---

## 6 · 遗留与边界（如实）

1. **未观测到「帧号停滞」事件**：本趟游戏在无对战压力下稳定 31–32 fps，没有 ≥1s 的冻结，
   所以 `--stack-on-stall` 的自动触发**本轮未实际发生**（栈是用 `--live` 手动采的）。
   ⇒ **E3 的最终产出（「冻结瞬间的栈」）仍需一次真正卡顿的对局**。
2. **未做多单位高负载局**：本轮只验证了「帧号在正常对局推进」，
   没验证「单位数很高时的帧号行为」。那需要 `ra2bench` 的 U0800/U0400 载体。
3. **`gamemd.exe+0x15e332` / `+0x3b868a` 的语义未解**：只拿到偏移，没映射回函数名
   （需函数边界识别，或接 `re_atlas` 的 kb 卷）。
4. **控件名依赖中文版/该构建**：`GUI:SinglePlayer` 等是控件**标题**，跨语言版本可能不同。
   当前构建（`73201cc0…`，中文 YR 1.001）已实测。
5. 本轮唯一运行期动作：WMI 启动一次游戏 → 控件驱动进局 → 只读采样 → 正常终止。

---

## 7 · 由此可复用的三条经验（写给后续会话）

1. **RA2/YR 的 UI 是真实 Win32 控件**（`#32770` 对话框 + `Button`/`ComboBox`/`trackbar`），
   **标题形如 `GUI:xxx`**。驱动游戏菜单应**用控件消息**（`BM_CLICK`），不要用坐标点击。
2. **启动全屏游戏会阻塞调用它的 shell**。用 WMI 分离：
   `Invoke-CimMethod Win32_Process Create 'cmd /c cd /d <dir> && start "" gamemd.exe'`。
3. **判「画面是否变化」不能用全画面指纹**（雷达背景是持续动画），
   要用**静态区域**（如按钮栏）或**控件树本身**（控件标题变化 = 界面切换，最可靠）。
