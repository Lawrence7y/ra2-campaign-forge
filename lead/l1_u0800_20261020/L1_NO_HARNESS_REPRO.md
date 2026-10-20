# L1 无 harness 干预复现实验报告（2026-10-20 16:4x）

## 实验设置

载体：`scratch/boot_probe/arm_a/` = `_src_L1_sf8_20261020` 的逐字节副本（88 件，含 spawnfix8 `XMP29U2.MAP` = `0add791d`）
exe：`gamemd.exe`（sha256 `73201cc0…f67476`，全程未变）
启动方式：`subprocess.Popen([exe], cwd=carrier)`，无 creationflags —— 与 harness `qc151_trip.py:1099` **同构**

## 实验结果

| # | 实验 | 动作 | 结果 |
|:--|:--|:--|:--|
| 1 | `boot_lifetime_probe.py` | 裸起，仅轮询存活 | **STILL_ALIVE_AT_TIMEOUT**（25s 不退出），`exc_changed=false` |
| 2 | `boot_esc_probe.py` | 裸起 + t=4.5/9.0s 各发一次 Esc | **STILL_ALIVE_AT_TIMEOUT**（25s），Esc 非致死因子 |
| 3 | `boot_window_probe.py` | 裸起 + 每秒枚举窗口 | **存活 22s**；窗口标题 `Yuri's Revenge`，尺寸 **1707×960** |
| 4 | `boot_focus_probe.py` | 裸起 + 完整 `_focus_foreground` 序列（ShowWindow(SW_RESTORE)→BringWindowToTop→AttachThreadInput+SetForegroundWindow→ALT 兜底） | **存活 15s**，`fg_is_ours=True`（第 1 次即拿到前台） |
| 5 | DPI 感知下裸起 | `SetProcessDPIAware()` 后启动 | **存活 6s+**，窗口 **2560×1440**（与 T55k 成功趟同尺寸） |

**结论：同一载体、同一启动方式、同一焦点/按键序列，无 harness 干预时游戏完全正常，进程不退出。**

## 与 L1 趟现场的对照

| 维度 | 无干预实验 | L1 趟现场 |
|:--|:--|:--|
| 进程存活 | 25s+ 不退出 | **t=5.188s 死亡**（`stab_rect_series` 第 9 点 `pid_alive=false`） |
| 窗口标题 | `Yuri's Revenge` | `Red Alert 2` |
| 窗口尺寸 | 1707×960（无 DPI）/ **2560×1440**（有 DPI） | **696×287** |
| 窗口位置 | (0,0) | **(935,578)** |
| `except.txt` | 未变 | 未变（`new_exception_count=0`） |
| 前台窗口 | 仅游戏自身 | **另有 6 个大窗**：ZCode 2582×1390、WorkBuddy 1941×1243、设置 1848×1221、设置 1870×1233、ChatGPT 1232×1440、Windows 输入体验 2560×1440 |

## 判读

1. **载体与 exe 无罪**：实验 1–5 全部用 L1 的同一份载体与同一 exe，游戏正常跑到 25s。
2. **Esc 无罪**：实验 2 显式复现 harness 的 Esc 纪律（t=4.5s / 9.0s），进程照常存活。
3. **焦点序列无罪**：实验 4 完整复现 `_focus_foreground` 三步，`fg_is_ours` 一次成功，进程照常存活。
4. **DPI 不是致死因素**，但**强烈影响窗口尺寸**：无 DPI → 1707×960；有 DPI → 2560×1440。L1 趟的 696×287 与两者都不同。
5. 因此 L1 的 696×287 + `Red Alert 2` 标题 + t=5.188 死亡，**只能由 harness 运行时的额外因素造成**，而不是载体/游戏/按键/焦点/DPI 中的任何单一因素。

## 仍未定谳的因素（按可能性排序）

1. **并发实例**：L1 趟启动时是否还有另一个 gamemd 在跑（导致焦点/单实例锁/显示模式竞争）。
   - 可查：`LAUNCH/launches = 1`（脚本只起一次），但**不排除外部已有实例**。
   - 现状：我这边已 `tasklist` 确认零 gamemd 残留，但 15:28 当时的现场无法回溯。
2. **显示模式切换失败**：6 个前台大窗占据桌面，cnc-ddraw 切换独占全屏失败 → 退化为 696×287 窗口 → RA2 在非预期显示模式下退出。
   - 支持证据：696×287 恰是 800×600 的 0.87 倍缩放；L1 的窗口位置 (935,578) 是桌面中部。
3. **`Red Alert 2` 标题 vs `Yuri's Revenge` 标题**：这是两套不同的窗口创建路径。RA2 模式下（非 YR 模式）窗口标题是 `Red Alert 2`。这说明 L1 趟启动时游戏可能走了 **RA2 而非 YR** 的启动分支。
   - 值得查：`gamemd.exe` 是否根据某个 INI 键/命令行/注册表选择 RA2/YR 模式。

## 建议的下一步实验（需真机，用户在场）

- **E1**：在桌面**无遮挡**条件下（关闭 ZCode/ChatGPT/WorkBuddy/设置等大窗）用 L1 同款载体跑一次 harness L1 趟，看是否复现 t≈5s 死亡。
- **E2**：若 E1 通过 → 确认「前台遮挡 → 全屏切换失败 → 进程退出」链条，修法是 harness 起趟前最小化其他窗口（`_focus_foreground` 已删掉了 minimize_others，见 `qc151_trip.py:1412-1413` 注释）。
- **E3**：若 E1 仍失败 → 抓 `gamemd.exe` 的退出码与 WER 报告（`GetExitCodeProcess` 已在 `_pid_alive_check` 里做过，但 `alive_seconds` 没记退出码值），并用 `procdump -e` 抓退出瞬间的转储。

## 复现脚本位置

`D:\Project\ra2-campaign-forge\scratch\boot_probe\`
- `boot_lifetime_probe.py`（存活时长 + except 差异）
- `boot_esc_probe.py`（Esc 变量隔离）
- `boot_window_probe.py`（窗口形态 + 存活）
- `boot_focus_probe.py`（`_focus_foreground` 三步复现）
