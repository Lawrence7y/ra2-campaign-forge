# SAFETY · W18 RE-N04g（HexBay B′ 臂）

run_id `NEXT_RE_20261112_R02` ｜ 2026-11-13 05:35–05:40（Asia/Shanghai）

## 授权边界（卡面 + USER_AUTHORIZATION_20261112.md）

**允许**：启动 `ra2youli\gamemd.exe`、只读 `ReadProcessMemory`、`OpenThread`+`GetThreadTimes`/`QueryThreadCycleTime`、枚举窗口与线程、发消息/点控件（仅导航/选图/开局阶段；采样段零输入）。
**禁止（全程未触碰）**：SuspendThread / StackWalk64 / MiniDump / 断点 / 注入 / 写目标进程内存 / 改 exe / dll / hook；增删改 `ra2youli` 文件（配置还原除外，为卡面要求）。

## 实例互斥锁

- 开工：`owner=lead` 可认领 → 探针 S0 认领 `owner=W18-load-HexBay-subagent`（05:35:04）。
- 收尾：探针 finally 恢复 `owner=lead`（05:39:57，meta.lock_restored=True）。
- 启动前 `Get-Process gamemd` 残留 = 0；探针 GuardStop 二次复核 = 0。

## 进程树隔离

- 探针本体：由代理经 **WMI `Win32_Process.Create`** 启动（cmd_pid=39692），父为 WmiPrvSE，脱离代理进程树。
- 游戏（pid=44120）：由探针经 WMI 启动（launcher cmd_pid=5736，归属判定 `wmi_child_parent_pid`）。
- 观察者（load_hexbay_ui_watch.py）：另起独立 WMI 进程（cmd_pid=44404），退出等待 0.01 s，非孤儿。

## 只读访问证明

- `OpenProcess(VM_READ|QUERY_INFORMATION)` 仅读：12 地址 RPM 逐拍读 40,881 拍，读失败 0。
- 线程仪器：`OpenThread(THREAD_QUERY_INFORMATION)` + GetThreadTimes + QueryThreadCycleTime，窗口线程失败 0。
- 代码签名探针 @0x55DE4F：`a0493da800` 匹配（地址基线有效）。

## 输入纪律

- 采样段（05:35:43.77 首个 frame>0 起 240.006 s）**零按键、零切窗、零干预**：观察者 212 次局内扫描 `distinct_last_input=1`；采样 40,002 拍 `win_foreground` 全 True（40002/40002）。
- 导航期仅 GUI 按钮点击（SinglePlayer / Skirmish / ChooseMap / UseMap / StartGame）与 `LB_SETCURSEL`，无键入。
- 误干预记录：**0 次**。

## finally 自愈链（探针内置，已执行）

1. 停观察者（watcher_stop.json，观察者 0.01 s 退出）
2. 关线程句柄 / 进程句柄
3. 关游戏：WM_CLOSE(hwnd=32116528) → taskkill(无/F) → taskkill(/F) → 最终存活=False
4. 残留核对 = 0
5. 配置逐字节还原 + 实算自证（见 CONFIG_RESTORE.md）
6. `timeEndPeriod(1)`
7. 写 `kind=meta_end`
8. 恢复锁 `owner=lead`

## 目标进程退出方式

WM_CLOSE 后游戏未自行退出 → taskkill 优雅终止（rc=0）→ 仍存活 → taskkill /F（rc=0）。全程未使用任何内存写入或调试接口。
