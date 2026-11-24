# SAFETY · W15 RE-N04e

run_id `NEXT_RE_20261112_R02` ｜ 2026-11-13 04:33–04:48（Asia/Shanghai）

## 授权口径（卡面）
允许：启动 `ra2youli\gamemd.exe`、只读 `ReadProcessMemory`、`OpenThread`+`GetThreadTimes`、
枚举窗口与线程、发消息/点控件（仅导航/选图/开局）、采样段要求零输入。
禁止：SuspendThread / StackWalk64 / MiniDump / 断点 / 注入 / 写目标进程内存 / 改 exe/dll/hook；
禁止增删改 `ra2youli` 文件（配置还原除外，为卡面要求）。

## 实际执行（两趟 attempt + 一次观察者救援）

| 动作 | 方式 | 合规 |
|---|---|---|
| 实例锁 | 开工 owner=W15-tick-cpu-subagent（attempt2 由探针自动认领）；收尾恢复 owner=lead | ✔ |
| 启动残留检查 | attempt1/2 开工前 `list_gamemd()` 均 0；attempt1 收尾后 0、attempt2 收尾后 0 | ✔ |
| 游戏启动 | WMI `Win32_Process.Create`（父=WmiPrvSE，脱离代理进程树） | ✔ |
| 读内存 | 仅 `ReadProcessMemory`（0x0010|0x0400），12 个已解码地址 + 代码签名 0x55DE4F 校验通过 | ✔ |
| 线程 CPU | 仅 `OpenThread(THREAD_QUERY_INFORMATION=0x40)` + `GetThreadTimes` + `QueryThreadCycleTime`；全部只读 | ✔ |
| 上下文切换 | 仅 `NtQuerySystemInformation(SystemProcessInformation)` 只读 + Toolhelp tid 校验 | ✔ |
| UI 导航 | PostMessage BM_CLICK（SinglePlayer→Skirmish→ChooseMap→UseMap→StartGame）+ LB_SETCURSEL(265)；**开局置前为最后一次输入** | ✔ |
| 采样段输入 | 探针构造保证零发送；观察者覆盖窗 `GetLastInputInfo` 0 变化 | ✔（焦点瞬态见 TICK_COST §8，非输入） |
| 进程优先级 | 探针/观察者 `BELOW_NORMAL_PRIORITY_CLASS`，不与游戏抢 CPU | ✔ |
| 关闭实例 | WM_CLOSE → taskkill(无 /F) → taskkill /F（attempt2 实际走到 taskkill /PID 与 /F，均 rc=0） | ✔（授权例外） |

## 禁止项核对
- 未发生：SuspendThread、StackWalk64、MiniDump、调试器附加、断点、DLL/代码注入、
  `WriteProcessMemory`、exe/dll 修改、hook、`ra2youli` 目录内任何增删改（还原拷贝除外）。
- 线程句柄访问权仅 `THREAD_QUERY_INFORMATION`；无 `SUSPEND_RESUME`/`SET_CONTEXT`。

## 分离与自愈（attempt2 教训落实）
- 探针与观察者均由 WMI 启动，父进程=WmiPrvSE，**脱离代理进程树**；代理会话结束不影响其生命周期。
- attempt1 崩溃（探针 bug，非游戏/环境）：`finally` 自愈链完整执行——停观察者→关闭自启动实例
  （taskkill /F /PID 31576）→残留核对 0→`RA2MD.INI`/`ddraw.ini`/`RA2MD.INI.benchbak` 逐字节还原并
  sha256 实算自证→写 `kind=meta_end`（exit_code=1）→恢复锁 owner=lead。全过程游戏无孤儿、无配置残留。
- attempt2 收尾自愈链同样完整执行（TICK_COST §8、CONFIG_RESTORE.md）。
- 观察者救援（t≈119–125 s）：仅删除本卡写域内的陈旧 `watcher_stop.json` 并 WMI 重启观察者进程，
  未触碰游戏进程；救援进程由探针收尾的 stop 文件正常退出（等待 0.0 s，非孤儿）。

## 遗留风险
- 无。两趟收尾后 `gamemd` 残留均 0；锁 owner=lead（`purpose=W15 RE-N04e 探针收尾自愈：恢复 owner=lead`）。
