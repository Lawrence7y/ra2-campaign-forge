# W10 SAFETY —— 授权边界与实际操作清单

- run_id：`NEXT_RE_20261112_R02`；卡：W10 CRLF 单变量验证（只到地图列表）
- 授权：用户已授予全部动作与自行裁决（见 `USER_AUTHORIZATION_20261112.md`）。
  本卡在其下只执行：启动自装游戏实例、只读内存观测、窗口枚举/消息/控件、
  优雅关闭自启动实例、配置逐字节还原自证。

## 允许且已执行

| 动作 | 实现 | 说明 |
|---|---|---|
| 启动 gamemd.exe | W7.launch_game()（WMI 分离启动） | pid=7568，launcher_pid=31456，归属=wmi_child_parent_pid |
| 只读进程内存 | OpenProcess(VM_READ \| QUERY_INFORMATION) + ReadProcessMemory | 仅 itemdata 指针缓冲（768B）与代码签名 5B（0x55DE4F） |
| 枚举窗口/控件 | EnumWindows/EnumChildWindows + SendMessageTimeoutW | 列表 ListBox=29497018；LB_GETITEMDATA / LB_SETCURSEL 均为列表控件消息 |
| 控件点击 | BM_CLICK（PostMessageW） | GUI:SinglePlayer → GUI:Skirmish → GUI:ChooseMap |
| 优雅关闭 | WM_CLOSE → taskkill(无 /F) → taskkill /F 兜底 | 实际路径：WM_CLOSE 后 6s 内未退，两级 taskkill 结束（收尾步骤见 RUNLOG） |

## 禁令执行情况（全部未触碰）

- 未用 SuspendThread / StackWalk64 / MiniDump / 断点 / 注入。
- 未写目标进程内存（0 次写；RPM 只读）。
- 未改 gamemd.exe / ddraw.dll（收尾 verify_only 哈希与基线一致）。
- 未删除或改名 `ra2youli` 内任何文件；H1 载体 `ra2youli\[2]0LoadBench_U0800_H1.yrm`
  run 前后 SHA-256 均 = `afb18a33…2925861`（untouched=true），还原由 Lead 负责。
- 未开局（未点击 GUI:StartGame）、未抓栈、未抓屏。
- 写域仅 `lead\next_re_20261112_r02\W10_crlf_verify\`；全仓未做递归列举/写。

## 实例互斥锁

- 开工：`.game_instance.lock` owner=lead（lead_free）→ 改为 owner=w10_crlf_verify_subagent。
- 启动前 `Get-Process gamemd`（探针内 list_gamemd）残留 = 0，未杀任何他人进程。
- 收尾：恢复 owner=lead（purpose 记 W10 done），lock_restored=true。

## 守卫（S0，全过）

- 残留进程 0；RA2MD.INI / ddraw.ini / RA2MD.INI.benchbak / gamemd.exe / ddraw.dll
  五文件哈希与基线全 match；H1 载体大小/哈希 = 315,706 B / `afb18a33…` match。
- 代码签名 0x55DE4F（mov al,[0xa83d49]）match —— 地址基线有效。
- ra2youli 清单 648 项（before/after 一致，diff added/changed/removed 均空）。
