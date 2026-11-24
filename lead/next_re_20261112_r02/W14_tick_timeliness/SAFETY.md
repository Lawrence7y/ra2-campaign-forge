# SAFETY · W14 RE-N04d

## 授权
用户 2026-11-12 总授权「全部动作 + 自行裁决、不干预」（`USER_AUTHORIZATION_20261112.md`）；
本卡面再次限定允许/禁止动作清单。

## 允许动作（全部遵守）
- 启动 `ra2youli\gamemd.exe`（WMI `Win32_Process.Create` 分离启动，cmd_pid=28316→pid=2236）
- 只读 `ReadProcessMemory`（12 地址/拍，40,806 拍，全程 `read_status=ok`）
- 枚举窗口 / 发消息点控件（仅导航+选图+开局阶段：SinglePlayer/Skirmish/ChooseMap/
  LB_SETCURSEL/UseMap/置前/StartGame）
- 实例锁属性行改写（授权例外：开工 owner=W14-tick-timeliness-subagent，收尾恢复 owner=lead）

## 禁止动作（零违反）
- SuspendThread / StackWalk64 / MiniDump / 断点 / 注入 / 写目标进程内存 /
  改 exe/dll/hook：**本卡全部未使用**（连抓栈都未做——本卡高频采样不允许任何挂起）。
- 增删改 `ra2youli` 文件：零手工改动。运行期唯一变化是**游戏自身**退出时改写
  `RA2MD.INI`（见 CONFIG_RESTORE.md），探针按卡面要求逐字节还原。
- 禁 git 写：未执行任何 git 操作。

## 进程树独立（attempt2 教训的落实）
- 探针：代理经 `Invoke-CimMethod Win32_Process Create` 启动（cmd_pid=39056，
  python 子进程），父=WmiPrvSE，**不在代理进程树内**；代理结束不会杀探针。
- 观察者：探针再经 WMI 启动第二个独立进程（cmd_pid=2840→watcher python pid=44608），
  与采样器**零 GIL 争用**，且脱离探针进程树——崩溃互不牵连。
- 非孤儿证据：探针 `exit_code=0`、写了 `meta_end`；观察者 `watcher_done.txt`
  reason=stop_file、245 行；收尾后 `wait_watcher_exit` 0.02 s 即确认退出。
- 代理侧轮询全部为前台短命令（一次 Start-Sleep 130 s 超时转入后台 job，
  已用 job_output 取回并确认退出 code 0，无遗留进程持锁）。

## 采样段零输入
- 置前（04:01:44.389）是**最后一次输入动作**，StartGame 后本进程零按键/零切窗。
- 观察者 244 次扫描：`GetLastInputInfo` 在有效局内窗口内 **0 次变化**；
  `win_foreground` 40,002/40,002 全 True ⇒ 零切窗成立。
- 采样段探针进程优先级 BELOW_NORMAL（不与游戏抢 CPU），观察者同。

## 残留
- 启动前 gamemd 残留 0（探针与代理双重核对）。
- 收尾后 gamemd 残留 0；本报告成文时再次实查 = 0。

## 时间源与不干扰声明
- 时间戳全部 `perf_counter_ns`（QPC，跨进程同源），未用 GetTickCount64 做间隔计算。
- `timeBeginPeriod(1)` 只由探针/收尾 `timeEndPeriod(1)` 调用（返回 0 成功），
  不触碰游戏进程；`ReadProcessMemory` 为同步只读调用，无挂起语义。
