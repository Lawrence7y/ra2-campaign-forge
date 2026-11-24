# W65 · RUNLOG.md（时间线 + 退出码）

> 执行者 Hy4｜所有时间 Asia/Shanghai（+08:00）｜`STARTED.txt` 写于 **读任何文件之前**。
> **Lead 验收口径：只看落盘原始产物与退出码**。本文件只是索引，权威数据在 `out\`。

## 时间线

| 时刻 | 阶段 | 动作 | 产物 / 退出码 |
|---|---|---|---|
| 23:41:55 | 启动 | 建卡目录 + `STARTED.txt`（ISO + `Hy4` + `lock per trip`）+ `HEARTBEAT.txt` | `STARTED.txt`, `HEARTBEAT.txt` |
| 23:41:56 | 启动 | 后台 10 分钟心跳任务 `pwsh-7d10d9ce1cb1486f`（追加 `BEAT_UTC=…`） | `HEARTBEAT.txt` |
| 23:42–23:53 | 离线读码 | 先读 FROZEN `CRITERIA_SPEC.md`；再读 `tool_b_stats.py`、`tool_c_writeaudit.py`、`W45\w45_dual_track.py`、`HANDOFF.md`、W63 `E2E_RESULT.md` / design / feature_set、W55b `RUN_SUMMARY.txt`、W62 EVIDENCE、W60 v15 | — |
| 23:53 | 离线 | 物理复制 W45 骨架到本卡（`tools\w45_skeleton_copied.py` 未改留证 + `tools\w65_collect.py` 待改）；写派生采集器、`designs\w65_design.json` | `tools\*.py`, `designs\*.json` |
| 23:53:49 | 离线 | `py_compile` collector / design JSON 校验 | `compile_exit=0`, `design_exit=0` |
| 23:54:05 | prep | `--phase prep`：真目录 PRE 全树清单 → robocopy 到 `sandbox_base` → v15 `uninstall` 清 v0.3 → `verify`（`manifest_present=false`）→ v15 build append 包 | `PREP_EXIT=0`；`out\prep.stdout.txt`, `out\real_pre.json`, `out\sandbox_base_pre.json`, `out\pkg\W65Bline\*` |
| 23:54:44 | audit | `--phase audit`：惰性沙箱上真实 v15 install/uninstall → 三份快照 → `tool_c_writeaudit.py --audit` | `AUDIT_EXIT=0`；`verdict=PASS`, `out_of_scope=[]`, `protected_all_equal=true`, `failed_checks=[]`；`out\c_audit_B_arm.json` |
| 23:55 | 离线 | `tool_b_stats.py --compare` **管道冒烟测试**（临时目录合成 6 个 NDJSON，非证据） | `compare_exit=0`, `SAME_DISTRIBUTION`（仅验管道字段/参数） |
| 23:56:25 | **A1** | 锁 lead→w65；桌面预检 PASS；pid 18184；苏联徽章；`SOV01UMD.MAP` 局内；6 ms × 75 s | `TRIP_A1_EXIT=0`；10,084 行 / 10,083 dframe；`read_fail=0`；`IDENTICAL_TREE=true`；锁→lead |
| 23:58:49 | A1 收尾 | WM_CLOSE→taskkill own pid→残留 0→`SOV01UMD.sav` 字节还原→实算自证 | `out\A1_result.json`, `out\restore_proof_A1.json`, `out\A1.ndjson` |
| 23:59:20 | **A2** | 同上流程（进图需额外 RETURN 重试） | `TRIP_A2_EXIT=0`；10,029 行 / 10,028 dframe；`read_fail=0`；`IDENTICAL_TREE=true`；锁→lead |
| 00:02:37 | A2 收尾 | — | `out\A2_result.json`, `out\A2.ndjson` |
| 00:02:50 | **B1** | 锁 lead→w65；v15 append `install` rc=0 / `verify` rc=0；pid 22784；同图 `SOV01UMD.MAP` | `TRIP_B1_EXIT=0`；10,023 行 / 10,022 dframe；`read_fail=0`；`IDENTICAL_TREE=true`；锁→lead |
| 00:05:11 | B1 收尾 | — | `out\B1_result.json`, `out\B1.ndjson`, `out\cmd_B1_install.log`, `out\cmd_B1_verify_pre.log` |
| 00:05:22 | **B2** | 同上；pid 34992 | `TRIP_B2_EXIT=0`；10,206 行 / 10,205 dframe；`read_fail=0`；`IDENTICAL_TREE=true`；锁→lead |
| 00:07:53 | B2 收尾 | 四趟全部结束 | `out\B2_result.json`, `out\B2.ndjson` |
| 00:08:57 | finalize | 真目录 POST 全树清单 vs PRE | `FINALIZE_EXIT=0`；`IDENTICAL_TREE=True`, added/removed/modified=0/0/0；`REAL_DIR_PROOF.txt`, `out\REAL_DIR_PROOF.json` |
| 00:09 | 统计 | 合并臂 + 描述统计（`tools\w65_report.py`）；`tool_b_stats.py --compare` | `REPORT_EXIT=0`, `COMPARE_EXIT=0`；`out\A_merged.ndjson`, `out\B_merged.ndjson`, `out\w65_descriptive_stats.json`, `out\b_compare.json` |
| 00:09–00:15 | 交付 | 写 `LIVE_RESULT.md` / `UNKNOWNS.md` / `DISAGREE.md` / `RUNLOG.md`；向 parent 发早期发现 + 最终结果 | 本文及同目录文件 |

总用时约 **34 分钟**（时间盒 140 分钟内完成全部四趟，未触发「90 分钟只完成 A 臂」的降级条件）。

## 全部退出码（可回对 `out\*.exit.txt`）

| 文件 | 内容 |
|---|---|
| `out\prep.exit.txt` | `PREP_EXIT=0` |
| `out\audit.exit.txt` | `AUDIT_EXIT=0` |
| `out\trip_A1.exit.txt` | `TRIP_A1_EXIT=0` |
| `out\trip_A2.exit.txt` | `TRIP_A2_EXIT=0` |
| `out\trip_B1.exit.txt` | `TRIP_B1_EXIT=0` |
| `out\trip_B2.exit.txt` | `TRIP_B2_EXIT=0` |
| `out\finalize.exit.txt` | `FINALIZE_EXIT=0` |
| `out\report.exit.txt` | `REPORT_EXIT=0` |
| `out\b_compare.exit.txt` | `COMPARE_EXIT=0` |

> 注：退出码 0 表示**工具/阶段正常结束**，不表示判据结论为 `SAME_DISTRIBUTION`。`tool_b_stats.py --compare` 的 `--compare` 分支恒 `return 0`（`tool_b_stats.py:424`），判定词在 `out\b_compare.json` 的 `verdict` 字段。

## 关键原始产物索引

```
W65_bline_live_collect\
├── STARTED.txt / HEARTBEAT.txt / REAL_DIR_PROOF.txt
├── LIVE_RESULT.md / UNKNOWNS.md / DISAGREE.md / RUNLOG.md
├── designs\w65_design.json
├── tools\w45_skeleton_copied.py   (W45 骨架未改副本，provenance)
├── tools\w65_collect.py           (本卡派生采集器，路径重定向)
├── tools\w65_report.py            (描述统计 + 补充 KS 复算，不 import 别卡)
├── sandbox_base\                  (两臂共同干净起点，v0.3 已卸载)
└── out\
    ├── A1.ndjson A2.ndjson B1.ndjson B2.ndjson        ← 4 份真机 NDJSON
    ├── A_merged.ndjson B_merged.ndjson                 ← SPEC §2.2 合并臂
    ├── A?_result.json / restore_proof_*.json / pristine_*\
    ├── screen_{A1,A2,B1,B2}_{campaign_menu,ingame}.png  ← 每趟 2 张
    ├── cmd_*.log                                      ← robocopy / uninstall / verify / install / audit
    ├── c_audit_{before,after,uninst,declared}.json + c_audit_B_arm.json
    ├── b_compare.json / b_compare.stdout.txt          ← FROZEN 判定
    ├── w65_descriptive_stats.json / cadence.json
    ├── real_pre.json / REAL_DIR_PROOF.json
    └── w65_run.ndjson                                 ← 全阶段事件日志（锁/截图/采样/关闭）
```

## 锁状态（最终）

`.game_instance.lock` = `owner=lead`（`00:07:53.680+08:00` 由 B2 的 `finally` 写回）；`out\w65_run.ndjson` 记录 4 组 `lock_before(owner=lead) → lock_claimed(owner=w65) → lock_released(owner=lead)`；`gamemd` 残留 0。

## 心跳

后台任务每 600 s 追加一行 `BEAT_UTC=… AGENT=Hy4 TICK=n`；各阶段另有 `PHASE_UTC=…` 手动追加。见 `HEARTBEAT.txt`。
