# SAFETY.md —— W9 H1 载体装入后分层复测

run_id：`NEXT_RE_20261112_R02`　日期：2026-11-13　执行者：`w9_h1_layering_subagent`

## 授权与禁令遵守

- 授权：启动 `ra2youli\gamemd.exe`、只读 `ReadProcessMemory`、枚举窗口/线程、发送窗口消息/点击控件（用户已在任务卡授予全部动作与自行裁决）。
- 遵守的禁令：全程**未**使用 SuspendThread / StackWalk64 / MiniDump / 断点 / 注入 / 写目标进程内存；**未**改 exe/dll/hook；**未**删除或改名 `ra2youli` 任何文件；未抓栈（frame 停推期间只记录 mode/win_foreground/控件文字）。
- 写域：仅 `lead\next_re_20261112_r02\W9_h1_layering\`；`ra2youli` 与其他目录只读（游戏运行时自身写回除外，见 CONFIG_RESTORE.md）。
- `git`：零写操作。
- PowerShell 操作 `ra2youli` 下含 `[` `]` 文件名一律 `-LiteralPath`（两趟守卫哈希核对因此全部命中，无静默 null）。

## 实例互斥锁

- 开工前锁 `owner=lead` → 无 gamemd 残留 → 改写 `owner=w9_h1_layering_subagent`（2026-11-13T01:43:28+08:00）。
- 每趟启动前 `Get-Process -Name gamemd` 核对残留 = 0（两趟均 0）；脚本内 `list_gamemd()` 双保险，遇残留即 GuardStop 停手不杀。
- 脚本内 `check_lock()`：owner 必须为 lead 或本代理，否则停手。
- 收尾将恢复 `owner=lead`（见 RUNLOG 收尾记录）。

## 实例与进程

- 单实例：两趟各启动一个 gamemd.exe（pid 42396 / 7568，WMI 分离启动，`wmi_child_parent_pid` 归属确认）。
- 关闭方式：`WM_CLOSE` 优雅优先 → `taskkill`（无 /F）→ `taskkill /F` 兜底；两趟最终残留 0。
- 未触碰他人进程；无进程悬挂。

## 目标进程观测

- 只读 `ReadProcessMemory`（OpenProcess `VM_READ|QUERY_INFORMATION`），读取地址全部来自 Lead 交叉解码确认表（ADDR，见 meta）；代码签名守卫（0x55DE4F = `mov al,[0xa83d49]`）两趟均通过，地址基线有效性自证。
- LB_GETITEMDATA 返回的指针一律以 RPM 读取（不跨进程传本地指针，规避 64→32 位 SendMessage 缓冲指针 AV 风险；LB_GETTEXT 传缓冲指针的方式因此弃用）。

## 文件完整性

- H1 载体 `[2]0LoadBench_U0800_H1.yrm`：两趟收尾后均复验 SHA-256 = `e3acc130…d9e39`（untouched=True）——Lead 的装入件未被本卡触碰，还原责任仍在 Lead。
- `gamemd.exe` / `ddraw.dll`：两趟收尾 SHA-256 与基线一致（verify-only）。
- ra2youli 清单 648 → 648（两趟 before/after 自比）。
