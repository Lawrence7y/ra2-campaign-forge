# W94 PROGRESS（进度与落盘记录）

> 卡：W94 批量真机矩阵运行器｜执行：subagent `w94-batchrun`｜模式：**离线实现卡**（真机锁归 W91，全程未启动游戏、未建沙箱、未注入）。
> 时间：2026-11-14 16:20–17:0x（Asia/Shanghai，Get-Date 实测）｜输出全部在 `W94_batchrun\` 内。

## 已完成（小步落盘）

| # | 时间 | 步骤 | 产物/证据 |
|---|---|---|---|
| 1 | 16:2x | 复制 W90/W88 工具链进本卡并改指向（r05→r06、W90→W94、锁 run_id→R06、锁 owner 门禁 w94*） | `work\tools\w94_lib.py`(30.2KB) `w94_common.py` `w94_offline.py` `w94_finalize.py` `exp_rpm_framebeat.py` + `work\w94_feature_set.json`；残留引用 grep 清零（除注明保留的文档字符串） |
| 2 | 16:2x | `w90_run.py` → 参数化 `w94_trip.py`：cell/trip 目录名入参、时长/节拍入参、render 通道任意格可挂、锁门禁 w94*、trip 目录防复用（fail-closed） | `work\tools\w94_trip.py`（971 行） |
| 3 | 16:3x | 全部工具脚本字节编译通过 | `py_compile` × 6 全 OK |
| 4 | 16:3x | 新写 `w94_build.py`：W85 绿几何 + W88 旋钮泛化（hunt_all/hunt_british/napowr_step/crewed），规格来自 cell spec JSON，含独立 verify + D4 归档 | `work\tools\w94_build.py` |
| 5 | 16:4x | 新写 `batch_runner.py`：矩阵校验/计划（shuffle+seed 确定性）/每趟锁双写（try/finally）/停止条件按格累计/matrix_log/`--dry-run`/`--resume`/残留停机 | `batch_runner.py` |
| 6 | 16:4x | dry-run 自测（无构建/无安装/无游戏）：6 趟计划 + 重复臂警告 + shuffle 可复现 | `EVIDENCE\dry_run_demo_console.txt` `dry_run_plan_demo.json` |
| 7 | 16:4x | 单元级离线检查：停止条件解析（4 坏形式拒）、outcome 计数器 5 例、坏矩阵 4 例拒、计划确定性、Guard 翻译、时长边界 | `EVIDENCE\unit_checks_console.txt` |
| 8 | 16:5x | 新写 `batch_analyze.py`（SUMMARY.csv/md；FILETIME 主通道口径；EIP 从归档 except 提取）+ **不启动游戏**伪造 ndjson 自测（6 趟/4 格，含 2 崩趟 + 2 个假 EIP） | `batch_analyze.py`；`EVIDENCE\make_fake_trips_selftest.py` `out\trip_*`（假数据）`SUMMARY.csv` `SUMMARY.md` `analyze_selftest_console`（见下） |
| 9 | 16:5x | 文档：矩阵字段/停止条件/崩溃处置/不做什么 + UNKNOWNS(7)/DISAGREE(6) | `BATCH.md` `examples\matrix_demo.json` `UNKNOWNS.md` `DISAGREE.md` |

## 自测真实抓到并修掉的 bug（证明自测不是走过场）

1. `batch_analyze.py` 键名错位：`anchors()` 返回 `x87e8e0_n_changes`，trip 行却读 `x87e8e0_changes` → X87E8E0 列全空。自测断言 `均值 6500` 现已命中。
2. 伪造数据量纲错（generator 侧）：CPU 消耗率 `% = sum_ms / wall_s / 10`，假数据初版差 10×（1.78 vs 17.8）——顺带复核了 W90 签字数（33.606/17.75）与公式一致。
3. `time.strftime(".%f")` 在 Windows C 运行时非法 → `now_local()` 改 `datetime.isoformat(timespec="ms")`。

## 明确未做（如实登记，不留半成品）

- **真机端到端**（build→install→trip 全链）：本卡纪律禁止启动游戏；门禁/锁/超时/残留四条真机路径为代码推演，UNKNOWNS U1/U2 已列。
- `--resume` 的"半截趟"不做数据级恢复：不完整目录整体挪 `out/aborted/`，不进汇总（见 BATCH.md §6）。
- 不做 ABBA 校准、不做地图几何推理、不做配对判定自动措辞（DISAGREE D3/D5）。

## 交接（给下一张真机卡）

1. 先跑**迷你矩阵**（1 格 1 趟）验证 U1 门禁时序；
2. `W94_FRESH=1` 建沙箱（运行器自己绝不 robocopy）；
3. 全矩阵跑完 → `batch_analyze.py` → `w94_finalize.py` 差集清场（含 real 目录 manifest 断言）；
4. 若要"容忍单次软错误"的停止语义，先解 UNKNOWNS U7 的语法问题再上矩阵。
