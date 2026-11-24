# NIGHTWATCH RUN LOG（GOAL-3T 无人值守轮 2026-11-02 夜 → 11-03 09:00）

> 用户令（2026-11-02 23:2x）：**「继续，直到明天早上九点前，请持续任务」**。
> 本文件是夜巡唯一常规写点；台账只在收尾轮追加（夜巡运行体**不写台账**）。

## 行格式（追加式，不改已有行）

```
- <ISO时间> | BOOT=<BOOT_TIME> | up=<h>h | tickdiff=<ms> | anchors=<n/15> | gamemd=<0|PID> | flows=<n> | status=OK|ALERT
```

- `ALERT` 行独立成行，前缀 `[ALERT]`，说明事实即可；**夜巡不自行修复、不杀进程、不重启**。
- 时间轴：`python -I -c "import ctypes,datetime;print(ctypes.windll.kernel32.GetTickCount64(), datetime.datetime.now().isoformat(timespec='seconds'))"`。
- 判 BOOT：`Get-CimInstance Win32_OperatingSystem | Select -Expand LastBootUpTime`；
  BOOT_TIME=2026-11-02T21:59:16 ⇒ BOOT#7；若变化 ⇒ ALERT（新 BOOT/重启）。
- 锚复验：对 `lead/codex_round_20261030/LEADER_battle/frozen_recheck_v4d_pre.txt` 15 行逐条 sha256。
- 进程：`Get-Process gamemd,game -ErrorAction SilentlyContinue`（空=0）。
- 在飞：`ListWorkflowRuns` 的 running/pending 计数。

## 停止条件

- 本地时间 ≥ **2026-11-03 09:00:00** ⇒ 追加一行 `# NIGHTWATCH ENDED <ISO时间>`，调用 **CronPauseSelf**，结束。

## 收尾（有人轮）

- [ALERT] 2026-11-03T09:21:15 | **BOOT 变更**：夜巡基线 BOOT#7（2026-11-02T21:59:16）已不存在；
  实测 LastBootUpTime=**2026-11-03T08:54:17**（BOOT#8），uptime≈20 min，冷启动。
  TICK64_ms=1,273,828 vs UPTIME_ms=1,275,567（同期实测，差 1.7 s，量级正常）。
  ⇒ D-12① 中以 BOOT#7 为基线的全部选项作废；BOOT#7 存活窗口内本会话零发射。
- 在飞工作流：0（ListWorkflowRuns 全 completed/stopped，无 running/pending）。
- 游戏进程：0（gamemd/game/ra2loader/YURI 均无）。
- 冻结锚：15/15 sha256 全等（`lead/codex_round_20261030/LEADER_battle/frozen_recheck_v4d_pre.txt`）。
- 夜巡期间实际产出：仅 T5 判档器复查一棒（2026-11-02T23:26，31 档全 PASS）。
  **无其他唤醒记录**——每 20 分钟唤醒自动化 `automation-f217d4a3` 自 2026-11-01T16:43 起
  lifecycleStatus=paused，整夜未运行；RUN_LOG 无逐拍行。夜巡「持续值守」事实未发生，如实登记不补造。

# NIGHTWATCH ENDED 2026-11-03T09:21:15
