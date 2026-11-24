# W69 · `RUNLOG.md`（时间线 + 退出码 + 产物索引）

> 执行者 Hy4（非 Lead）｜所有时间 Asia/Shanghai（+08:00）｜`STARTED.txt` 写于**读任何文件之前**。
> **Lead 验收口径：只看落盘原始产物与退出码**。本文件只是索引，权威数据在 `out\` 与 `LIVE_RESULT_V2.md`。

## 时间线

| 时刻 | 阶段 | 动作 | 产物 / 退出码 |
|---|---|---|---|
| 00:45:27 | 启动 | 建卡目录 + `STARTED.txt`（ISO + `Hy4` + `lock per trip`）+ `HEARTBEAT.txt` | `STARTED.txt`, `HEARTBEAT.txt` |
| 00:45:2x | 启动 | 后台 10 分钟心跳任务 `pwsh-109ffea366044d1e`（追加 `BEAT_UTC=… TICK=n`） | `HEARTBEAT.txt` |
| 00:45–00:49 | 离线读码 | 先读 FROZEN `CRITERIA_SPEC_V2.md` / `tool_b_stats_v2.py` / `tool_c_writeaudit.py` / W65 `LIVE_RESULT.md`·`DISAGREE.md`·`RUNLOG.md`·`w65_collect.py`·`w65_report.py`·design / W70 / `LEAD_VERIFY_W65.md` / `LEAD_VERIFY_W68B.md` / W68 `DEFECT_PROOF.md` / v15 包 / 锁文件 | — |
| ~00:48 | 离线 | **逐字节复制** 6 个工件进本卡 + 逐文件 sha256 自证；复制 `w65_collect.py`→`w69_collect.py` 并改路径/`owner=w69`；`py_compile` 4 个脚本 + design JSON 校验 | `TOOL_HASHES.json`, `CRITERIA_SPEC_V2_COPY.md`, `tools\*`, `designs\w69_design.json`；`PY_COMPILE_EXIT=0`, `DESIGN_EXIT=0` |
| 00:49:5x | 离线（首次） | 对当时复制到的工具跑 `--selftest --out DIR` **失败**：`FileNotFoundError: …\tools\EVIDENCE\ce_A\A.ndjson` | `out\b_selftest_v2.stdout.txt`（失败记录，非证据） |
| 00:49–00:51 | 离线查证 | **发现 W68 并发写入冲突**：根目录 spec/tool 于 `00:45:12`/`00:46:19` 被从 GLM 版（`B-W68-2`, 22280 B）覆盖为 W68b 版（`B-W68B-V2-1`, 20787 B）。读 `CONCURRENT_WRITER_NOTE.md` 确认权威版 sha256；核对我方副本 sha 与权威值**完全一致**；读权威工具全部 495 行、权威 spec §2.3/§2.4 | 早期发现已 `send_message` 报 parent |
| 00:51 | 离线 | 复制合成对照 `ce_A/ce_B/ce_C` 到本卡 `tools\EVIDENCE\`；权威 V2 工具 `--selftest --out FILE` → **PASS**；`--compare` 管道冒烟（合成 `ce_A`） | `out\b_selftest_v2.json`（`V2_SELFTEST_PASS=True`）, `out\b_selftest_v2.exit.txt=0`, `out\_smoke_compare.*`（**非证据**） |
| 00:52:04 | prep | `--phase prep`：真目录 PRE 全树清单 → robocopy `sandbox_base` → v15 `uninstall` 清 v0.3 → `verify`（`manifest_present=false`）→ v15 **append** build | `PREP_EXIT=0`；`out\real_pre.json`(647 文件/1,989,215,270 B), `out\sandbox_base_pre.json`, `out\pkg\W65Bline\*`, `out\cadence.json` |
| 00:52:37 | audit | `--phase audit`：惰性沙箱上真实 v15 install/uninstall → 三份快照 → `tool_c_writeaudit.py --audit` | `AUDIT_EXIT=0`；`verdict=PASS`, `out_of_scope=[]`, `protected_all_equal=true`, `failed_checks=[]`；`out\c_audit_*.json` |
| 00:53:08 | **A1** | 锁 lead→**w69**；桌面预检 PASS；pid 39452；苏联徽章；`SOV01UMD.MAP`；6 ms × 75 s | `TRIP_A1_EXIT=0`；10,241 行 / 10,240 dframe；`read_fail=0`；`IDENTICAL_TREE=true`；锁→lead |
| 00:56:43 | A1 收尾 | WM_CLOSE→taskkill own pid→残留 0→`SOV01UMD.sav` 字节还原→实算自证→删沙箱 | `out\A1_result.json`, `out\restore_proof_A1.json`, `out\A1.ndjson`, 2 张截图 |
| 00:57:00 | **A2** | 同上（进图需额外 RETURN 重试） | `TRIP_A2_EXIT=0`；10,219 行 / 10,218 dframe；`read_fail=0`；`IDENTICAL_TREE=true`；锁→lead |
| 01:00:33 | A2 收尾 | — | `out\A2_result.json`, `out\A2.ndjson` |
| 01:00:42 | **B1** | 锁 lead→**w69**；v15 append `install` rc=0 / `verify` rc=0；pid 38140；同图 `SOV01UMD.MAP` | `TRIP_B1_EXIT=0`；10,217 行 / 10,216 dframe；`read_fail=0`；`IDENTICAL_TREE=true`；锁→lead |
| 01:04:16 | B1 收尾 | — | `out\B1_result.json`, `out\B1.ndjson`, `out\cmd_B1_install.log`, `out\cmd_B1_verify_pre.log` |
| 01:04:23 | **B2** | 同上；pid 39596 | `TRIP_B2_EXIT=0`；10,235 行 / 10,234 dframe；`read_fail=0`；`IDENTICAL_TREE=true`；锁→lead |
| 01:07:58 | B2 收尾 | 四趟全部结束 | `out\B2_result.json`, `out\B2.ndjson` |
| 01:08:20 | 统计 | `tools\w69_report.py` 合并臂 + 描述统计；`tools\tool_b_stats_v2.py --compare` | `REPORT_EXIT=0`, `COMPARE_V2_EXIT=0`；`out\A_merged.ndjson`, `out\B_merged.ndjson`, `out\w69_descriptive_stats.json`, **`out\b_compare_v2.json` → `verdict=SAME_DISTRIBUTION` / `reason=within_noise_band`** |
| 01:09:25 | finalize | 真目录 POST 全树清单 vs PRE | `FINALIZE_EXIT=0`；`IDENTICAL_TREE=True`, added/removed/modified=0/0/0；`REAL_DIR_PROOF.txt`, `out\REAL_DIR_PROOF.json` |
| 01:09–01:1x | 交付 | 写 `LIVE_RESULT_V2.md` / `UNKNOWNS.md` / `DISAGREE.md` / `RUNLOG.md`；向 parent 发最终结果 | 本文及同目录文件 |

总用时约 **24 分钟**（时间盒 140 分钟内完成全部四趟，**未触发**「90 分钟只完成 A 臂两趟」降级条件）。

## 全部退出码（可回对 `out\*.exit.txt`）

| 文件 | 内容 |
|---|---|
| `out\prep.exit.txt` | `PREP_EXIT=0` |
| `out\audit.exit.txt` | `AUDIT_EXIT=0` |
| `out\trip_A1.exit.txt` | `TRIP_A1_EXIT=0` |
| `out\trip_A2.exit.txt` | `TRIP_A2_EXIT=0` |
| `out\trip_B1.exit.txt` | `TRIP_B1_EXIT=0` |
| `out\trip_B2.exit.txt` | `TRIP_B2_EXIT=0` |
| `out\report.exit.txt` | `REPORT_EXIT=0` |
| `out\b_compare_v2.exit.txt` | `COMPARE_V2_EXIT=0` |
| `out\b_selftest_v2.exit.txt` | `SELFTEST_EXIT=0` |
| `out\finalize.exit.txt` | `FINALIZE_EXIT=0` |

> 注：退出码 0 表示**工具/阶段正常结束**，不表示判据结论为 `SAME_DISTRIBUTION`。`tool_b_stats_v2.py` 的 `--compare` 分支恒 `return 0`，判定词在 `out\b_compare_v2.json` 的 `verdict` 字段。

## 关键原始产物索引

```
W69_bline_v2_collect\
├── STARTED.txt / HEARTBEAT.txt / REAL_DIR_PROOF.txt
├── LIVE_RESULT_V2.md / UNKNOWNS.md / DISAGREE.md / RUNLOG.md
├── TOOL_HASHES.json               ← 6 工件逐字节副本 sha256 自证 + 权威 W68b sha 复核
├── CRITERIA_SPEC_V2_COPY.md       ← 权威 FROZEN V2 spec 逐字节副本（gate 原句来源）
├── designs\w69_design.json        ← W65 design 逐字节副本（append 路线，保证同构）
├── tools\
│   ├── w69_collect.py             ← W65 采集器派生副本（路径重定向 / owner=w69）
│   ├── w69_report.py              ← 描述统计 + 补充 KS 复算（不 import 别卡脚本）
│   ├── tool_b_stats_v2.py         ← FROZEN V2 工具逐字节副本（零改动）
│   ├── tool_c_writeaudit.py       ← FROZEN C 工具逐字节副本（零改动）
│   └── EVIDENCE\ce_A,B,C\        ← 合成对照 fixtures（供 --selftest，非真机证据）
├── sandbox_base\                  ← 两臂共同干净起点（v0.3 已卸载，[SOV1] 官方图未变）
└── out\
    ├── A1.ndjson A2.ndjson B1.ndjson B2.ndjson    ← 4 份真机 NDJSON（各 ≈1.37 MB）
    ├── A_merged.ndjson B_merged.ndjson            ← 合并臂（未截断/未补齐）
    ├── b_compare_v2.json / .stdout.txt / .exit.txt← **FROZEN V2 正式判定**
    ├── b_selftest_v2.json / .stdout.txt / .exit.txt ← V2 工具自检（合成，PASS）
    ├── w69_descriptive_stats.json / cadence.json / w69_run.ndjson
    ├── A?_result.json / restore_proof_*.json / pristine_manifest_*.json / pristine_*\
    ├── screen_{A1,A2,B1,B2}_{campaign_menu,ingame}.png  ← 每趟 2 张（共 8 张）
    ├── cmd_*.log                  ← robocopy / uninstall / verify / install / audit
    ├── c_audit_{before,after,uninst,declared}.json + c_audit_B_arm.json  ← C 判据
    ├── real_pre.json / REAL_DIR_PROOF.json / finalize.stdout.txt
    ├── _smoke_compare.json / _smoke_compare.stdout.txt  ← **非证据** CLI 管道冒烟（合成 ce_A）
    └── selftest_v2\               ← 空目录（首次失败 selftest 遗留，**非证据**）
```

> **`_smoke_compare.*` 与 `selftest_v2\` 均为离线管道冒烟/失败遗留，不是真机证据，不参与任何判定**；权威判定只认 `b_compare_v2.json`。

## 锁状态（最终）

`.game_instance.lock` = `owner=lead`（`01:07:57.631+08:00` 由 B2 的 `finally` 写回）；`out\w69_run.ndjson` 记录 4 组 `lock_before(owner=lead) → lock_claimed(owner=w69) → lock_released(owner=lead)`，趟间锁文件始终 `owner=lead`，**从未跨趟长期持锁**；`gamemd` 残留 `[]`（finalize 与 pwsh 复核均 0）。

## 心跳

后台任务每 600 s 追加一行 `BEAT_UTC=… AGENT=Hy4 TICK=n PHASE=heartbeat`；实测 `TICK=0 @~00:49`、`TICK=1 @00:58:38`、`TICK=2 @01:08:38`。各阶段另有 `PHASE_UTC=…` 手动追加。见 `HEARTBEAT.txt`。收尾时 `job_kill` 关闭该后台任务（不影响已落盘心跳行）。
