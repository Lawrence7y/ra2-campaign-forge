# E1 第一步：地图版本隔离实验（2026-10-20 17:3x）

## 目的

Notion 裁决1：「E1 跑之前，先在同一次清屏条件下用两张图各裸起一次，10 分钟就能彻底锁死『地图无关』——这是把 B 的信息量并进 E1，不另起趟。」

## 实验设计

两个载体 **88 件，唯一差异是 `XMP29U2.MAP`**，其余 87 件逐字节相同（实测 sha256 全同）：

| 载体 | 地图 | 来源 |
|:--|:--|:--|
| `arm_a` | `XMP29U2.MAP` = `0add791d`（311,822 B） | L1 趟用的 spawnfix8 |
| `arm_b` | `XMP29U2.MAP` = `9e33585c`（324,234 B） | T55k 成功趟用的 spawnfix10lite |

启动方式：`subprocess.Popen([gamemd.exe], cwd=<carrier>)`，**无任何 creationflags**，与 harness `qc151_trip.py:1099` 同构。
探针：`boot_window_probe.py`（每秒枚举本进程可见窗口 + 三法交叉判定存活）。

## 结果

| 组 | 存活 | 窗口标题 | 窗口尺寸 |
|:--|:--|:--|:--|
| `arm_a`（spawnfix8 `0add791d`） | **12 s 仍存活**（`final_alive=True`） | `Yuri's Revenge` | 1707×960 |
| `arm_b`（spawnfix10lite `9e33585c`） | **12 s 仍存活**（`final_alive=True`） | `Yuri's Revenge` | 1707×960 |

两组均未出现 `Red Alert 2` 696×287 的 csf 错误框，均未自行退出。

## 结论

**地图版本无关（本地证伪「spawnfix8 导致启动失败」）**。

L1 趟的 t=5.188s 进程自行退出 + `Red Alert 2` 696×287 弹窗，**不能归因于 spawnfix8 地图**。
结合此前 5 组无干预实验（裸起 / 加 Esc / 完整 `_focus_foreground` 序列 / DPI 感知 / 窗口枚举），
可归因范围收缩为 **14:45–15:33 那个 harness 运行窗口的环境态**。

## 尚未覆盖（E1 第二步）

本实验**未复现** harness 完整趟的任何一步：没有 `--fullscreen` 全屏切换、没有前台焦点抢占序列、
没有 6 个大窗遮挡的桌面状态、没有导航点击。因此**不能**排除「全屏切换失败」或「前台遮挡」这两条假设。

E1 第二步（真机 harness 完整趟）仍是必要的，需用户在场。

## 复现

```powershell
cd D:\Project\ra2-campaign-forge\scratch\boot_probe
python boot_window_probe.py --carrier arm_a --timeout 20 --label map_sf8_0add791d
python boot_window_probe.py --carrier arm_b --timeout 20 --label map_sf10lite_9e33585c
```
