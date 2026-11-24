# SAFETY.md —— RE-N04 W12 可重复性能基线（安全与授权边界）

- run_id: `NEXT_RE_20261112_R02`；卡片 RE-N04；代理：`W12-perf-baseline-subagent`
- 授权来源：`lead\next_re_20261112_r02\USER_AUTHORIZATION_20261112.md`（用户授予全部动作与自行裁决）+ 本卡任务书

## 实际执行的动作（全部在授权清单内）

| 动作 | 授权依据 | 实况 |
|:--|:--|:--|
| 启动 `ra2youli\gamemd.exe`（WMI 分离启动，cmd `start`） | 卡片明确允许 | R1–R4 各 1 次 + R1 首趟中断尝试，共 5 次启动，全部本代理自启 |
| `ReadProcessMemory` 只读采样（12 地址 @30/250 ms） | 卡片明确允许 | OpenProcess 权限仅 `PROCESS_VM_READ\|QUERY_INFORMATION`（0x0010\|0x0400） |
| 枚举窗口/控件（EnumWindows/EnumChildWindows） | 卡片明确允许 | 仅导航与地图列表读取 |
| 发送窗口消息 / BM_CLICK 点控件 | 卡片明确允许 | 仅菜单导航按钮与 WM_CLOSE 收尾 |
| `force_foreground`（Alt-托底置前，StartGame 后一次） | W7 已验证实现 | 仅启动阶段；采样段零置前 |
| 收尾 `WM_CLOSE` → `taskkill`（无 /F）→ `taskkill /F` | W1/W7 已验证收尾链 | 只对**自己启动的 pid**；逐趟残留=0 |

## 未做（红线遵守）

- 无 SuspendThread / StackWalk64 / MiniDump / 断点 / 注入 / 写目标进程内存。
- 未改 gamemd.exe / ddraw.dll / 任何 exe/dll/hook（仅有只读哈希验证）。
- 未删除/改名/新增 `ra2youli` 内任何文件：每趟启动前后全目录 inventory 对比
  （`written_back` 字段，四趟 added/removed/changed 均空，清单 647 项不变）。
- 未 git 写操作；未全仓递归列举（inventory 仅限 `ra2youli\`）。
- 采样段零人工干预：不按键、不切窗、不进菜单、不抓栈（win_foreground 全程 True 佐证）。
- 每趟启动前 `gamemd` 残留检查：若非 0 则停手不杀（本卡五次开工检查均为 0，未触发）。

## 实例互斥锁

- 路径：`lead\next_re_20261112_r02\.game_instance.lock`
- 开工：owner 从 `lead` 接管为 `W12-perf-baseline-subagent`（手工 + 每趟探针自检；
  非本代理且非 lead 时停手——check_lock 守卫）。
- 收尾：全部趟次结束后恢复 `owner=lead`（见 RUNLOG 末行）。

## 写域

- 仅 `lead\next_re_20261112_r02\W12_perf_baseline\`（本文件与 `out\`）+ 实例锁（卡片授权例外）。
- 唯一越域写为零；`baseline_pre_launch\` 等其它目录只读。

## 风险与遗留

- 游戏为独占全屏路径（ddraw windowed=false），置前动作在 StartGame 后执行一次（W7 同款），
  采样段内若系统抢占焦点会体现在 `win_foreground`（本卡四趟全程 True，未发生）。
- R4 低速回退门未触发；该逻辑只在本卡保留于探针参数中，未产生任何写副作用。
