# W11 SAFETY —— 安全与授权记录

- run_id：`NEXT_RE_20261112_R02`；卡片：W11 `[Header]` 节单变量验证；日期：2026-11-13
- 授权基线：用户已授予全部动作与自行裁决（见 `USER_AUTHORIZATION_20261112.md`，未复核改动）。
- 执行身份：`w11_header_verify_subagent`（经 `.game_instance.lock` 实例互斥）。

## 实例互斥

| 时点 | 状态 |
|---|---|
| 开工检查 | `owner=lead`（lead_free），无其它持有者 |
| 持有 | `owner=w11_header_verify_subagent`（write_lock，purpose=W11） |
| 收尾 | `owner=lead` 已恢复（meta.lock_restored=True） |

## 启动前守卫（全过）

1. gamemd 残留进程 = 0（有残留即停手）。
2. `RA2MD.INI / ddraw.ini / RA2MD.INI.benchbak / gamemd.exe / ddraw.dll` 五件
   SHA-256 与 W7 基线逐一 match=True。
3. H1 载体核对：`ra2youli\[2]0LoadBench_U0800_H1.yrm` = 315,912 B /
   `3ce133ff53b67418918e3b3f812f79610094395a979ba27e444ad6fe873be1cb`
   （与 Lead 装入记录一致；PowerShell 侧以 `-LiteralPath` 核对，Python 侧路径直拼）。
4. 启动前 ra2youli 清单 648 项。

## 进程操作边界（全程遵守）

- 允许并执行：WMI 分离启动 `gamemd.exe`；只读 `ReadProcessMemory`（OpenProcess
  `VM_READ|QUERY_INFORMATION`）；窗口枚举；`BM_CLICK`/`LB_*` 消息与控件读取。
- 禁止且未执行：SuspendThread / StackWalk64 / MiniDump / 断点 / 注入 /
  写目标进程内存 / 改 exe、dll。开局采样为逐拍只读 + UI 控件快照；无抓栈。
- Q1 未命中 ⇒ 按任务书**未开局**（无 UseMap/StartGame），采样循环整段未进入。

## 本卡未触碰的资产

- `ra2youli` 内任何文件未删除、未改名、未写入（H1 载体收尾后哈希仍为
  `3ce133ff…873be1cb`，untouched=True；还原由 Lead 负责）。
- git 无写操作；`lead\` 下写域仅 `W11_header_verify\`（锁文件按互斥协议更新 owner 字段）。
- 未全仓递归列举；仅列出 run 目录一层与 W9/W10 交付物（只读）。

## 观察到的游戏内动作范围

- 仅菜单导航三次点击（SinglePlayer → Skirmish → ChooseMap）+ 面板快照用的
  LB_SETCURSEL；开局相关动作（UseMap/StartGame/Continue）零次。
- 收尾：WM_CLOSE → taskkill(无 /F) → taskkill /F（进程已无 UI 响应时的既定
  降级链，全部记录于 run_stdout.txt）；最终存活=False，残留=0。
