# L1 五趟失败根因取证（指挥官亲判，2026-10-20 16:2x）

## 结论

**台账 §303–§307 里「RA2 启动期释放磁盘空间弹窗挡住主菜单」的判读不成立，应推翻。**
真实现场是：**gamemd.exe 在启动后约 5 秒内自行退出（进程死亡）**，harness 之后 148 秒一直在对
一个已死的 PID 做窗口枚举与截图，因此抓到的画面是**桌面左上角 800×600 区域**（ZCode 窗口的一角），
不是游戏画面，也不是任何 RA2 弹窗。

## 一、进程死亡时间线（决定性证据）

数据源：`qc151_fields.json` → `WIN/stab_rect_series.items`（240 个采样点，间隔 0.56s）

| t (s) | pid_alive | rect | esc_before |
|:--|:--|:--|:--|
| 0.500 | **True** | `[935, 578, 1631, 865]`（696×287，标题 `Red Alert 2`） | 0 |
| 5.188 | **False** | `[0, 0, 0, 0]` | 1 |
| 134.141（末点） | False | `[0, 0, 0, 0]` | 2 |

- 阶段预算（`BUDGET`）：`launch` 起于 t=11.172s，`window` 阶段耗时 **148.328s**，`nav_menu` 超时 150.86s。
- 即：**进程在 window 阶段内部（启动后约 5 秒）就已死亡**，之后全部等待都是空转。
- `TERM/termination_verdict = PASS`、`identity_pid_verified = true` —— 终止链对的是一个已经退出的进程，
  这是脚本自身「PASS」的来源，不代表游戏活着。

## 二、截图为什么是双栏灰度

`capture_frame_desktop()`（`qc151_trip.py:1559`）的坐标算法：

```python
ox = (_l if (_r - _l) > 0 else 0) + FS_RENDER_ORIGIN[0]   # :1596
oy = (_t if (_b - _t) > 0 else 0) + FS_RENDER_ORIGIN[1]   # :1597
```

- 进程活着时主窗在 (935,578)，`rect` 非退化 ⇒ 抓 (935,578)-(1735,1178)。
- 进程死后 `rect_of(hwnd)` 失败/返回 0 尺寸 ⇒ **回落 `(0,0)`**，抓屏幕左上 800×600。
- 该区域实测被 `ZCode` 主窗覆盖（本机 `EnumWindows` 实测：`ZCode` rect = `(-7,-7,1714,920)`，pid 26088）。
- 因此 140 张 `navsig_nav_menu_pre_*.png` 全部 sha256 相同，画面是 ZCode 窗口的 UI 元素
  （主色 236,236,238 与 248,248,248 双栏、深色文字、按钮框），**与游戏无关**。

## 三、为什么「弹窗点名文件随机」这条观察是假的

前五趟记录的「MOUSE.SHA / BINKW32.DLL / RA2MD.IC 随机点名」来自对**上述错误截图**的人工读图。
截图既然是 ZCode 窗口，其中的文字与 RA2 完整性检查无关。旁证：

- 载体 88 个文件里，`The following files` / `modified to add` / `hard drive` / `free space`
  的 ASCII 与 UTF-16 两种编码全部搜过，唯一命中是 `launcher.txt` 里关于虚拟内存的说明书文字（无关）。
- `MOUSE.SHA` 在载体中**根本不存在**（`ls` 实测），不可能被 RA2 点名。
- D 盘空闲 405G，非空间不足。

## 四、进程为什么 5 秒退出 —— 已定位到具体错误路径

### 4.1 窗口标题是决定性线索

| | 正常启动（本机实测 3 种条件） | L1 趟现场 |
|:--|:--|:--|
| 窗口标题 | `Yuri's Revenge` | **`Red Alert 2`** |
| 窗口尺寸 | 1707×960（无 DPI）/ 2560×1440（有 DPI） | **696×287** |

`Red Alert 2` **不是游戏主窗口的标题**，而是 `gamemd.exe` 里一个**错误消息框**的标题。
二进制实测（`ra2youli/gamemd.exe`，VA `0x00840C58` 起）：

```
0x00840C58  "Unable to initialize 'ra2.csf', please reinstall Red Alert."
0x00840C94  "Keine Initialisierung von 'ra2.csf' möglich. Bitte installieren Sie Red Alert erneut."
0x00840CEA  "Initialisation de 'ra2.csf' impossible. Veuillez réinstaller Red Alert."
0x00840D34  "Red Alert 2"        ← 消息框标题
0x00840D40  "ra2md.str"
0x00840D4C  "LANGUAGE.MIX"
0x00840D5C  "LANGMD.MIX"
```

⇒ **L1 趟现场那个 696×287 的 `Red Alert 2` 窗口 = csf 初始化失败的消息框**，不是"文件被修改/释放磁盘空间"提示。
台账 §304–§307 的「游戏完整性检查弹窗 / 释放空间提示」判读全部推翻。

### 4.2 进程为什么干净退出

- Windows 事件日志 Application 在 15:20–15:40 区间**零** Application Error / WER / Application Hang 事件。
- 即 gamemd 不是崩溃，而是**主动 `ExitProcess`** —— 与"csf 初始化失败后弹框、用户不可见、随即退出"的代码路径一致。

### 4.3 已排除的候选

| 候选 | 排除依据 |
|:--|:--|
| 载体件数 | L1 与 T55k 文件集合**完全相同**（88 件，差集为空） |
| 除地图与 INI 外的载体内容 | 86 个文件逐字节相同（sha 实测） |
| `ra2.csf` / `ra2md.csf` | 两趟同 hash `91191bad…ec13`，274,057 B |
| `language.mix` / `langmd.mix` | 两趟同尺寸（52,913,656 / 84,643,206） |
| 启动器 | 两边都含 `ra2.exe` / `ra2md.exe` / `YURI.exe` / 三个 `.lcf` |
| `ddraw.ini` | 两趟同 hash `95949842…f26e`，`windowed=false` / `fullscreen=false` / `width=0` |
| Esc 按键 | 实验 2 显式复现 t=4.5s/9.0s 两次 Esc，进程 25s 存活 |
| 焦点序列 | 实验 4 完整复现 `_focus_foreground` 三步，`fg_is_ours=True`，进程存活 |
| DPI | 实验 5 `SetProcessDPIAware()` 后启动，2560×1440 正常 |
| 崩溃/异常 | `except.txt` 跑前跑后 1046 行零新增 |

### 4.4 仅剩的差异变量

| 文件 | T55k | L1 | 是否可能致 csf 失败 |
|:--|:--|:--|:--|
| `RA2MD.INI` | 1,783 B `f488cfcd…` | 1,785 B `0cc65385…` | **可疑**：2 字节差，需逐行 diff |
| `XMP29U2.MAP` | 324,234 B `9e33585c…` | 311,822 B `0add791d…` | 间接：非法地图可能让启动期就退出，但不应报 csf |

**待办**：对两份 `RA2MD.INI` 做逐行 diff（源文件相同，但载体内的两份 hash 不同 ⇒ 是**运行期回写**造成的
2 字节差异，需确认是哪个键被改写）。

## 五、对台账的影响

- §303「boot 卡在 YR 载入动画」：**部分成立**（`frame_early_01.png` 确为 YR 载入画面，t=0.719s 抓的，那时进程还活着）。
- §304「真因=游戏完整性检查弹窗」：**推翻**。
- §305/§306「88/89 件无差别、点名随机」：**推翻**（判据本身来自错误截图）。
- §307「脚本零弹窗处理、R1/R2 两条路线」：**前提失效**。加弹窗点击能力对本案**无效**，必须先解决「进程 5 秒退出」。

## 六、下一步

1. 用最小复现验证进程退出：同一载体，裸起 gamemd，记录退出码与存活时长（不依赖 harness 的窗口逻辑）。
2. 分别用 `9e33585c`（T55k 的图）与 `0add791d`（L1 的图）各起一次，隔离「地图版本」变量。
3. 若确认 spawnfix8 导致启动期退出 → 换回 spawnfix10lite 重跑 L1，或修 spawnfix8。
4. harness 侧独立缺陷（应另开项）：进程死亡后没有 fail-fast，导致 148 秒空转 + 错误截图产出 + 假「弹窗」证据链。
