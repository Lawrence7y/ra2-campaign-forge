# W20 · SAFETY.md — 授权与安全边界执行记录

## 授权来源
- 卡面 `USER_AUTHORIZATION_20261112.md`（既有）+ Lead 本卡授权：启动
  `ra2youli\gamemd.exe`、只读 `ReadProcessMemory`、`OpenThread`+`GetThreadTimes`/
  `QueryThreadCycleTime`、枚举窗口与线程、发消息/点控件（导航/选图/设置界面纯 UI 读/
  开局；采样段零输入）。
- 实例互斥锁 `lead\next_re_20261112_r02\.game_instance.lock`：开工 owner=lead →
  探针认领 owner=W20-combat-subagent → 收尾恢复 owner=lead（两次 attempt 均执行）。

## 允许动作的实际使用（attempt=2 正式趟，pid=40188）
- 启动：WMI `Win32_Process.Create`（cmd → gamemd.exe），探针与观察者均脱离代理进程树。
- 只读内存：`OpenProcess(VM_READ|QUERY_INFORMATION)` + `ReadProcessMemory`
  （12 个既有登记地址 × 100,858 拍，失败 0）。
- 线程仪器：`OpenThread(THREAD_QUERY_INFORMATION)` + `GetThreadTimes`/
  `QueryThreadCycleTime`（窗口线程 tid=34952；全线程扫在观察者进程 1Hz）。
- UI 交互（全部 PostMessage BM_CLICK，无键鼠事件）：
  `GUI:SinglePlayer` → `GUI:Skirmish` → `GUI:ChooseMap` → LB_SETCURSEL(265) →
  `GUI:UseMap` → （S2b 设置界面纯 UI 枚举 39 组合框）→ `GUI:StartGame`。
- 收尾：WM_CLOSE → taskkill（无 /F）→ taskkill /F（游戏未响应 WM_CLOSE 时按链升级）。

## 禁止项遵守情况
- 未使用 SuspendThread / StackWalk64 / MiniDumpWriteDump / DebugActiveProcess /
  断点 / DLL 注入 / CreateRemoteThread。
- 未写目标进程任何内存（无 WriteProcessMemory 调用）。
- 未修改 gamemd.exe / ddraw.dll / 任何 exe/dll/hook（开工+收尾哈希双验：unchanged=true）。
- 未增删改 `ra2youli/` 文件；例外仅卡面要求的配置还原（RA2MD.INI / ddraw.ini /
  RA2MD.INI.benchbak，见 CONFIG_RESTORE.md，逐字节自证）。
- 禁 git 写：本卡全程未触碰 git。写域仅 `W20_combat/`（+ 实例锁授权例外）。

## 采样段输入纪律
- 采样段（t=0–600.006 s）**零键鼠输入**：观察者 `GetLastInputInfo` 在其存活窗
  （t≈462–600 s）内 last_input 恒定（1 个不同值）✓；探针该窗内无任何 PostMessage/
  keybd_event 调用（代码路径与日志双证）。t∈[0,462)s 无 last_input 通道
  （观察者缺陷窗，见 RUNLOG §2/§3 与 UNCOVERED.md），但探针同窗内同样无输入调用，
  且 fg 变化两次均已记录归因。
- 两次**非本意前台变化**（均无键鼠输入、帧循环未受扰）已如实记录：
  ① t≈284.3 s 起失去前台（本代理分离观察者时 cmd 控制台弹窗所致——操作失误）；
  ② t≈445.9 s 前台自动回到游戏（坏观察者被终止时系统归还焦点），伴随一次
  96 ms 帧拍滑移（df=2 单事件）。fg=True/False 条件 CPU 差 +0.4%，帧率全程
  31.25 计数/s ⇒ 不构成测量污染源。

## 风险面
- 探针/观察者进程优先级 BELOW_NORMAL，未触碰游戏进程优先级/affinity。
- 观察者为纯只读旁路（OpenProcess QUERY_INFORMATION + 窗口枚举），无输入注入。
- 失败自愈：attempt=1 的启动失败经 finally 链完整自愈（游戏关闭、配置逐字节还原、
  锁恢复），未留下任何残留（残留在每次收尾核对 = 0）。
