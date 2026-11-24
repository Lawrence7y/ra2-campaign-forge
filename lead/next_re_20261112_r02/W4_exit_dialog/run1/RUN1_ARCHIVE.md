# RUN1_ARCHIVE.md —— 第 1 趟真机原始记录说明

- run_id: `NEXT_RE_20261112_R02` / W4；第 1 趟时间(UTC) `2026-11-12T15:52:57`–`15:54:11`
- pid=`16052`，launcher_pid=`36408`，is32=True，map=`[8] Proving Grounds`（index=265），窗口 tid=`37264`
- 退出码 `2`（GuardStop：游戏在 ① 后直接退出），残留进程 0，配置逐字节还原

## 做了什么

按任务卡优先级尝试 ① `Alt+F4`（真实 `keybd_event`，前置 `force_foreground` 成功）。
触发前已完成 D0 阴性对照（正常局内，平静、无交火）。

## 观察证据

- 触发后 1.3 s 枚举本 pid 顶层窗口/子控件：**空**（游戏进程已退出）。
- `GetExitCodeProcess` → `exit_code = 0`（干净退出），`alive = False`。
- 无 Windows 对话框、无 `Yes/No` 按钮、无新顶层窗口 ⇒ **对话框根本没出现**。
- D0 栈（4 帧，usable=True）：`ntdll+0x7858c → KERNELBASE+0x16a1f0 → KERNELBASE+0x16a18f → gamemd+0x15e332`；
  `frame=964`，`g1..g4` 全 0（G4=0），`mode=5`，`A8E9A0=1`，`ABCD58=1`，`exitstate=0`；
  `prev_count=0 / resume_ret=1 / held=9.111ms / stackwalk_false:0`。
- 退出前最后读数与退出码见 `out/run1/exit_readings.json`（若存在）与本目录 `RUNLOG.md`。

## 结论与处置

按任务卡「游戏直接退出：记录退出前最后读数与退出码，**不要重启补测**（除非还没拿到 D0）」，
本趟 D0 已取得，故本趟**未重启、未伪造 D1/D2**，判「未能触发」。
②③ 两条路径因进程在 ① 即死亡而**未能在同一实例内执行**，这是本卡决定串行补跑的原因
（完整理由见根目录 `VERDICT.md §0.1`，依据「全部动作与自行裁决」+「可重跑一次并说明」）。

## 归档清单

- 本目录 `RUN1_ARCHIVE.md` + 从根目录复制的 5 份 MD（运行时原样）
- `out/run1/`：13 个文件（D0.json、prelaunch.json、baseline_14412.json、frame_stable.json、
  ui_baseline.json、triggers.json、exit_readings.json、restore_verify.json、run_meta.json、
  summary.json、stdout.txt、console.txt、sentinels.ndjson），逐字节未改动
- `out/_pre_run3_stale/`：**混合目录**，含本卡前两趟的旧 out 根文件副本，
  以及**并行代理另跑的一趟真机**（pid 13260，约 00:01 本地，同样记录 Alt+F4 直接退出 exit=0）。
  该目录文件不作为本卡判档依据，仅作并发留痕；判档只用 `out/*.json`（run3 / pid 4856）。
