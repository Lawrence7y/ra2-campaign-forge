# SAFETY.md —— W7 RE-N03 安全约束落地与核对

- run_id: `NEXT_RE_20261112_R02`；生成时刻：2026-11-13（本地）
- 覆盖：T1 三趟正式运行（run1/2/3）+ 1 趟被误杀的存档运行（`out\archive_rejected\run1_modegate_rejected.*`）

## 1. 授权边界逐条落地

| 约束 | 落地方式 | 核对 |
|:--|:--|:--|
| 只允许启动 `ra2youli\gamemd.exe` | WMI `Win32_Process.Create` 分离启动（`cmd /c cd /d … && start gamemd.exe`），launcher pid 归属判定 `wmi_child_parent_pid` | ✅ 三趟全部 `wmi_child_parent_pid` |
| 只读 `ReadProcessMemory` | `OpenProcess(PROCESS_VM_READ|QUERY_INFORMATION)`，12 个登记地址每拍 `ReadProcessMemory`；无任何写进程内存调用 | ✅ 代码无写路径 |
| 枚举窗口/线程 | `EnumWindows`/`EnumChildWindows`/`GetWindowThreadProcessId`（tid 取返回值，W6 已修语义） | ✅ |
| 发送窗口消息/点击控件 | `BM_CLICK`（PostMessage）+ `LB_GETCOUNT/LB_GETITEMDATA/LB_SETCURSEL` + `WM_CLOSE` 收尾 | ✅ |
| 禁 SuspendThread/StackWalk64/MiniDump/断点/注入/hook | 本卡未引入 W3/r2/stackwalker，代码不含上述任何调用 | ✅ 零挂起、零抓栈、零转储 |
| 禁改 exe/dll | 启动前哈希守卫 5 文件（与 PRE_LAUNCH_BASELINE.tsv 一致），收尾 verify-only 复核 | ✅ 三趟全 match |
| 不杀别人进程 | 启动前 `gamemd` 残留 >0 即 GuardStop 停手（本三趟启动前残留均为 0）；taskkill 只对自己记录的 pid | ✅ |
| 实例互斥锁 | `.game_instance.lock` 开工接管 owner=W7-load-baseline-subagent；每趟开工复检 owner∈{lead,self} | ✅（收尾恢复见 §3） |
| 写域仅 W7_load_baseline | 产出全部落在 `W7_load_baseline\`；对 `ra2youli` 只做启动/只读/还原（还原 = 卡片要求的配置复原） | ✅ |

## 2. 进程关闭顺序（每趟独立收尾）

1. `WM_CLOSE` → 游戏窗口（三趟均在 6s 内未自行退出）
2. `taskkill /PID <pid>`（无 /F，优雅）
3. `taskkill /F /PID <pid>`（强制兜底）
4. 收尾后 `gamemd` 残留核对 = **0**（三趟全部）

无挂起类操作 ⇒ 无挂起预算/残留挂起项（与 W6 的 SuspendThread 预算无关，本卡不适用）。

## 3. 收尾自证（三趟独立）

| 趟 | 收尾后残留 | RA2MD.INI 还原 | ddraw.ini 还原 | RA2MD.INI.benchbak | gamemd.exe/ddraw.dll 复核 |
|:--|:--|:--|:--|:--|:--|
| run1 | 0 | 字节一致 + 哈希一致 | 字节一致 + 哈希一致 | 字节一致 + 哈希一致 | 未改动 = True/True |
| run2 | 0 | 同 | 同 | 同 | 同 |
| run3 | 0 | 同 | 同 | 同 | 同 |

明细见 `CONFIG_RESTORE.md` 与 `out\run{1,2,3}_meta.json` 的 `restore_rows` / `residual_after`。

## 4. 扰动面

- 每拍 12 次 RPM（30ms 周期，~400 次/s）——只读，未观测到任何读失败/读延迟引发的异常。
- 导航只发控件消息（BM_CLICK / LB_*），未发送键盘事件（本卡无 Esc 实验）。
- StartGame 后一次 `force_foreground`（ALT 技巧置前）；三趟 win_foreground 全程 True（run1 3167/3167 拍）。
