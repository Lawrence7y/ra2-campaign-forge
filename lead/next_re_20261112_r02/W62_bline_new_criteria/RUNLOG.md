# RUNLOG.md — W62 / RE-N09

> 执行者：Hy4｜纯离线｜**I launched 0 / attached 0**（未启动 `gamemd.exe`、未 attach、未读活进程内存、未取 `.game_instance.lock`）
> 所有原始输出/退出码在 `EVIDENCE\`；本文件是时间线索引与结论摘要。分级同 `UNKNOWNS.md`。

## 0 · 纪律顺序（可核对）

`STARTED.txt`(23:18:10) → **脚本骨架落盘** → 骨架语法校验(exit 0) → **读上游文件** → `CRITERIA_SPEC.md` **冻结**(23:25:30) → **之后**才实现两个 `tool_*.py` → 才运行 → 才写 EVIDENCE。顺序符合项目 §3.4。

## 1 · 时间线

### 23:18:10 — 建目录 / STARTED / HEARTBEAT `[本次实测]`
```
New-Item -Force W62_bline_new_criteria\ , \EVIDENCE\
STARTED.txt = "W62 STARTED: 2026-11-13T23:18:10.9342721+08:00 / agent: Hy4"
HEARTBEAT.txt = bootstrap
```
`STARTED.txt` 在**读任何项目文件之前**写完。

### 23:18 — 骨架先落盘 `[本次实测]`
写 `tool_c_writeaudit.py`（skeleton-1）、`tool_b_stats.py`（skeleton-1）、`CRITERIA_SPEC.md`/`UNKNOWNS.md`/`DISAGREE.md`/`RUNLOG.md` 骨架（占位）。
```
python -m py_compile tool_c_writeaudit.py tool_b_stats.py   → PY_COMPILE_EXIT=0
python --version                                            → Python 3.12.10
```
骨架函数体为 `NotImplementedError`，**此时还没有任何判据数值**。

### 23:18–23:25 — 读码 `[本次读码]`
- `REVIEW\LEAD_VERIFY_W59.md` 全文（字段语义 / §5 观测锚点）
- `REVIEW\LEAD_VERIFY_W55B.md` 全文（`D>N` 失效 / C+B 方向 / §2.2 白名单不完备）
- `W55b_equivalence_rerun\out\analysis.json` 全文（`N_A=1339784` / `N_B=1316737` / `N_stable=false` / `D∈[1319300,1321641]`）
- `W45_b_line_equivalence\tools\w45_dual_track.py:1-120`（Win32/RPM/EnumWindows 采集层）
- `W60_...\ra2forge_patched_v15\ra2forge\install.py`：`package_files()` 760-793、`preinstall_plan()` 1177-1256、`install_package()` 1973-2047、`_inplace_battle_ini()` 3105-3112、`PACKAGE_MANIFEST_NAME=ra2forge_package.json`(403)、`MANIFEST_NAME=ra2forge_install.json`(375)
- `...\resolve_integration.py`：`check_inplace_mode()` 317-348、`install_resolve()` 405-416、`inplace_requested()` 928-933、`inplace_preflight()` 936+
- `...\s3_cases.py:205-227`(B4)、`...\s5_cases.py:1-215`(`_inplace_fs` / `_golden_official` / INPLACE1 / INPLACE2)、`...\regress_dlc_v15.py:40-109, 188-194, 345-401, 2799-2823`
- `...\cli.py:1-180`、`...\battlemd_inplace.py:1-80`

### 23:25:30 — SPEC 冻结 `[本次实测]`
`HEARTBEAT.txt` 更新为 `phase: spec-before-code`；`CRITERIA_SPEC.md` 写入 **FROZEN** 版（§1 全部 C 规则 / §2 全部 B 规则 / §2.5 常量表 / §2.6 事先声明的正负对照期望）。**冻结后才动实现代码**。

### 23:2x — `tool_b_stats.py` 实现 + 首跑 `[本次实测]`
实现 `SPEC` 常量、`load_ndjson` / `quantile` / `ks_statistic` / `permutation_pvalue` / `jaccard_mean` / `compare_arms`（§2.4 判定表）/ `gen_synthetic` / `run_selftest`。
```
python tool_b_stats.py --selftest --out EVIDENCE
[B-POS]  expected=SAME_DISTRIBUTION actual=SAME_DISTRIBUTION pass=True
[B-NEG]  expected=SHIFT_DETECTED    actual=SHIFT_DETECTED    pass=True
[B-NEG2] expected=SHIFT_DETECTED    actual=SHIFT_DETECTED    pass=True
[B-POS]  N_ks=0.015000 D_ks=0.012484 p=0.885057 J=1.0000 reason=within_noise_band
[B-NEG]  N_ks=0.015000 D_ks=0.998752 p=0.000500 J=1.0000 reason=ks_beyond_noise
[B-NEG2] N_ks=0.015000 D_ks=0.042447 p=0.157921 J=1.0000 reason=discrete_or_ui_mismatch
TOOL_SELFTEST_PASS=True ; EXIT=0
```
> 注：一次**并行**调用时 pwsh 输出被 harness 吞掉且未留档；改为单独调用后正常，已补留 `EVIDENCE\b_selftest.stdout.txt` / `.exit.txt`。这是工具显示问题，非判据问题，如实登记。

### 23:2x — `tool_c_writeaudit.py` 实现 + C-NEG 自检两次失败→修复 `[本次实测]`
实现 `snapshot_tree` / `diff_snapshots` / `declared_write_set` / `protected_set` / `protected_hash_check` / `restore_equal` / `audit`（§1.4 判定表）/ v15 CLI 编排 / 负对照 fixture。
- 首跑 `--selftest`：`compliant_control` 误判 `FAIL`，`C_SELFTEST_EXIT=1`。
- 定位：`checks` 字典里混入"异常存在标志" `C-2_out_of_scope_writes=(not c1)`、`C-5_residual_outside_whitelist=c5`，值为 `False`（表示**无越界/无残留，是好事**）却被 `failed=[k for k,v in checks.items() if v is False]` 当成失败。
- 修复：统一为 PASS 语义 `C-2_no_out_of_scope_writes=c1`、`C-5_no_residual_outside_whitelist=(not c5)`；另清理 inplace 字节证明里 `bak_bytes_pre` 的类型隐患（原会把 sha 字符串传进 `hashlib.sha256`）。
- 修复后重跑：
```
compliant_control: verdict=PASS, checks 全 true, failed_checks=[]
injected_control : verdict=FAIL, out_of_scope_writes=["EVIL.dll","gamemd.exe"],
                   protected_touched=["gamemd.exe"],
                   failed_checks=[C-1, C-2, C-3]
tool_selftest_pass=true ; C_SELFTEST_EXIT=0
```
**这是判据工具本身的负对照**（合成快照级，不碰 v15）。

### 23:3x — C 首跑：`--run-all`（真调 v15 CLI）`[本次实测]`
```
python tool_c_writeaudit.py --run-all --out EVIDENCE 2>&1 | Tee EVIDENCE\c_audit.stdout.txt
[C-A] verdict=PASS out_of_scope=[] failed=[]
[C-B] verdict=PASS out_of_scope=[] failed=[]
[C-NEG] verdict=PASS
C_ALL_PASS=True ; C_RUNALL_EXIT=0
```
`EVIDENCE\c_audit.exit.txt = 0`。v15 六条 CLI（2×build / 2×install / 2×uninstall）`exit` 全部 `0`，原始 stdout/stderr 在 `c_audit.json → v15_cli_log`。

**C-A（普通包）**：`W.added = [BATTLEMD98.INI, CP1.MAP, CP2.MAP, expandmd98.mix, ra2forge_install.json, ra2forge_install.json.seal]`，`W.modified=[]`，`W.removed=[]`；`W ⊆ D`；7 个受保护文件哈希全等；卸载 `restore.equal=true`。
**C-B（battlemd:inplace）**：包内 `BATTLEMD.INI`（2730 B SOV1 rewrite）；`declared_rewrite=["BATTLEMD.INI"]`；`W.modified=["BATTLEMD.INI"]` 被分类为 `DECLARED-REWRITE (not out-of-scope)`；`W.added=["BATTLEMD.INI.ra2forge.bak", CP1.MAP, CP2.MAP, expandmd98.mix, ra2forge_install.json, .seal]`；`inplace_proof`：`bak_present_post_install=true`、`bak_bytes_equal_to_pre_official=true`、`bak_consumed_after_uninstall=true`、`target_sha_restored=true`；6 个受保护文件（**不含** `BATTLEMD.INI`，因它在 `D`）哈希全等；卸载 `restore.equal=true`。

### 23:3x — 独立核对 + 补留档 `[本次实测]`
```
python - <<PY ... 解析 c_audit.json 打印 C-A/C-B 关键字段 → VERIFY_EXIT=0
python tool_b_stats.py --selftest --out EVIDENCE | Tee b_selftest.stdout.txt   → EXIT=0
python tool_c_writeaudit.py --selftest --out EVIDENCE | Tee c_neg_selftest.stdout.txt → EXIT=0
git status --porcelain -- lead/.../W62_bline_new_criteria → 仅本卡目录 untracked, GIT_EXIT=0
```
只读 `git` 确认未改动 `ra2forge`/`ra2opt`/`ra2bench`/`W21`–`W61`。官方 baseline `BATTLEMD.OFFICIAL.INI` = 2733 B ✓。

## 2 · 退出码汇总（全部落 `EVIDENCE\*.exit.txt`）

| 运行 | exit | 结果 |
|---|---|---|
| 骨架 py_compile | 0 | 语法有效 |
| `tool_b_stats.py --selftest` | 0 | B-POS/B-NEG/B-NEG2 全部符合事先声明期望 |
| `tool_c_writeaudit.py --selftest`（修复后） | 0 | C-NEG 合规=PASS / 注入=FAIL |
| `tool_c_writeaudit.py --run-all` | 0 | C-A/C-B/C-NEG 全 PASS |
| 独立核对 `c_audit.json` | 0 | 关键字段与摘要一致 |
| `git status --porcelain`（只读） | 0 | 仅本卡目录 untracked |

## 3 · 本卡**未**做的事（红线核对）

- 未启动 `gamemd.exe`（沙箱内为 inert placeholder，**I launched 0 / attached 0**）、未 attach、未读活进程内存、未取 `.game_instance.lock`。
- 未改 `ra2forge`/`ra2opt`/`ra2bench`、未改 `W21`–`W61`、`git` 仅只读。
- 未重跑 W55b 等价性判定，未签发任何等价/不等价结论，**未写「B 线等价性已成立」**。
- 未事后调整 `CRITERIA_SPEC.md` 的任何阈值、白名单、样本量下限或判定规则。
