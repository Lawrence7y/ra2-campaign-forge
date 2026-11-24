# APPLY.md · W46 / S4：v13 → v14 补丁、校验与回滚

> 唯一写域：`lead\next_re_20261112_r02\W46_resolve_integration\`。
> **不就地改 W43 / W42 / W38 / W21–W45 / 仓库 `ra2forge/` / `ra2youli/`，git 只读。**
> 本卡交付的是**已应用完毕的整包 v14**（`ra2forge_patched_v14\`），本文件给出相对 v13 的改动清单、可复算校验与回滚路径。

---

## 1 · 改动清单（相对 `W43_b_line_s3\ra2forge_patched_v13\`）

`out\V14_SOURCE_DELTA.json`（`[本次实测]`）是下列 delta 的机检副本：

```
changed (3):  ra2forge/builder.py
              ra2forge/cli.py
              ra2forge/install.py
added   (1):  ra2forge/resolve_integration.py
removed (0):  —
```

`[本次实测]` `S4_8e/f` 另证以下文件与 v13 **逐字节相同**：`verify.py`、`feature_subset.py`、`csf.py`、`s3_contract.py`、`version_guard.py`、`mapselmd.py`、`data/E1_KNOWN_GOOD.json`、`data/guard_decision_table.json`，以及其余 11 个未列文件（`__init__.py`、`__main__.py`、`design.py`、`maplib.py`、`mixlib.py`、`lzo.py`、`format80.py`、`triggers.py`、`data/RA2MD.OFFICIAL.CSF`、`data/RA2MD.OFFICIAL.LABELS.txt`、`data/MAPSELMD.OFFICIAL.INI`）。

### 1.1 `ra2forge/resolve_integration.py`（新增，约 660 行）

单文件集成层，不 import `install`/`builder`（避免循环），只依赖 `feature_subset` + `s3_contract` + 标准库。核心符号：

| 符号 | 作用 |
|---|---|
| `EXIT_CODES`（24–31） | W46 独立退出码表；v13 的 0–10 与 W38-S1 的 20–23 不动 |
| `MODE_SUPPORT` / `MODE_RESERVATIONS` | D5.2 的 `DEFERRED` 状态 + `battlemd:inplace` plan 层预留槽 + 4 文件封闭改动面 |
| `SECOND_INSTALL_SEMANTICS` | 二次安装 5 verdict 的**数据化定谳** |
| `RECONCILIATION_RULES` | CREATE/REPLACE/LEAVE → 允许的 actual action |
| `ResolveIntegrationRefused` | 带 `exit_code` / `reason_code` / `plan` / `report` 的拒绝异常 |
| `run_resolve()` | **唯一**调用 `feature_subset.resolve()` 的写入口；`check_inplace_mode()` 前置拒绝 |
| `install_resolve()` / `build_resolve()` | 两端入口；前者 `derive_install_sandbox_state()` 只读扫描真实游戏目录，后者用标注 `synthetic:true` 的 W42 S0 夹具 |
| `filter_package_files()` | 写前包子集门：`{包内 game-dir 成员} == plan.shipped()` |
| `reconcile_install()` / `compact_recon()` | 逐文件 plan vs actual 行 + 清单紧凑副本 |
| `classify_second_install()` / `detect_plan_orphans()` / `check_install_gates()` | 二次安装 / orphan / legacy 判定与有序门禁 |
| `snapshot_leave_files()` / `check_post_write()` | 写前 LEAVE 字节快照、写后落盘 sha + 写集复核 |
| `build_effective_switches()` / `build_reconcile()` | plan 驱动可选产物 + build 端逐文件对账 |
| `write_plan_report()` / `write_resolve_plan_out()` / `validate_report_paths()` | 报告产物（禁止落进游戏目录，W38 A7） |

### 1.2 `ra2forge/builder.py`（改）

- `build()` 形参追加（全部带默认，位置不变）：
  `feature_set=None, sandbox_state=None, guard_state=None, plan_report=None, resolve_plan_out=None`。
- **在 `out.mkdir()` 之前**：若 `feature_set` 非空 ⇒ `RI.build_resolve()` → `RI.build_effective_switches()`，得到 `eff_csf_out` / `eff_mapselmd`。
- 把函数体内 6 处 `csf_out` / `mapselmd` 的**读取**改为 `eff_csf_out` / `eff_mapselmd`；`--csf-out` 的 W41 归属守卫改用 `eff_csf_out`（仍在任何写之前）。
- `BUILD_REPORT.txt` 增一行 `[PASS] W46/S4 plan-driven build: ...`（仅 opt-in 分支）。
- `_write_install_readme(..., mapsel_enabled=bool(eff_mapselmd))`。
- **返回 `mix_path` 前**跑 `RI.build_reconcile()`（包内写 `ra2forge_plan_reconciliation.json`，可选写 `--plan-report`）。
- `feature_set=None` 时 `eff_* == 原开关`，`check_lines` 无新增行 ⇒ 默认构建逐字节 v13（`S4_8a..d`）。

### 1.3 `ra2forge/install.py`（改）

- 常量：新增 `INTEGRATION_MODE_TAG = "W46-S4-resolve-integration-opt-in"`（紧随 `SEAL_ERA_VERSION`）。
- `preinstall_plan(..., feature_plan=None)`：
  - `package_files()` 之后调 `RI.filter_package_files()`（写前包子集门）；
  - `return` 前**只读**派生并回传 `plan_reconciliation` / `second_install` / `plan_orphans`；
  - 原有 82 例依赖的 `blockers/conflicts/risks/notices/steps/manifest/orphans/identity/package_digest` 键与取值**不变**。
- `install_package(...)` 形参追加 `feature_set, sandbox_state, guard_state, plan_report, resolve_plan_out`：
  - `_s3_guard_gate()` 之后、`preinstall_plan()` 之前 ⇒ `RI.install_resolve()`（写盘前跑 `resolve()`）；
  - 身份/冲突/风险门之后 ⇒ `RI.check_install_gates()`（guard→legacy→orphan→对账）；
  - `IDEMPOTENT_REPLAY` ⇒ **在第一次写之前短路返回**，`game_dir_file_writes=0`；
  - 写阶段开始前 `RI.snapshot_leave_files()` 取 LEAVE 字节快照；
  - 清单 `_stage_text_and_replace` **之前** ⇒ `RI.check_post_write()`（失败即落入 v13 既有 `_rollback()`）；
  - 清单追加 `feature_set_id` / `plan_actual_reconciliation` / `plan_mode` / `second_install` / `plan_legacy_adopted`（仅 opt-in 分支）；
  - 成功后写 `--plan-report`，返回 dict 追加 `status/feature_set_id/second_install/plan_reconciliation/plan_orphans/leave_files_unchanged`（默认路径返回 dict 与 v13 相同）。
- **未改**：`package_files()`、`_write_step()`、`_execute_orphan_plan()`、`_rollback()`、`write_install_seal()`、`uninstall()`、`_uninstall_legacy()`、所有 DLC-STRICT01 / ORPHAN-FIX01 / SEAL-CHAIN01 门禁结构。

### 1.4 `ra2forge/cli.py`（改）

- 模块级 `from .resolve_integration import ResolveIntegrationRefused`（该模块不 import install/builder，无循环）。
- `_w46_kwargs(args)` / `_w46_refusal()` 两个 helper。
- `build` / `install` 两个子解析器新增 5 个 opt-in 开关：`--feature-set` / `--sandbox-state` / `--guard-state` / `--plan-report` / `--resolve-plan-out`。
- `build` 分支：`build(..., **_w46_kwargs(args))` + `except ResolveIntegrationRefused` ⇒ 打印错误并返回 `exc.exit_code`；`--install` 链式调用同样传入（但 `plan_report`/`resolve_plan_out` 置 None，避免与 build 自己的报告撞路径）。
- `install` 分支：`install_package(..., **_w46_kwargs(args))` + `except ResolveIntegrationRefused`。
- **`resolve` 子命令、`guard-check`、`verify`、`uninstall` 分支完全未改**；`VERIFY_EXIT_CODES_TEXT` / `UNINSTALL_EXIT_CODES_TEXT` 常量未改。

### 1.5 回归与文档（本卡根目录，均为新增）

| 文件 | 说明 |
|---|---|
| `regress_dlc_v14.py` | 由 `W43_b_line_s3\regress_dlc_v14.py` 复制后仅改 4 处：`W43_ROOT_NAME`、`V12_ROOT` 指向 v14、新增 `V13_REF_ROOT`、绑定 `S4_CASES` + 汇总文案。**57+25=82 个用例函数体一字未改** |
| `s3_cases.py` | 从 W43 **逐字节复制**（`bind_s3` 把 `G.CARD` 指向本卡根） |
| `s4_cases.py` | 新增 8 例 `S4_1..S4_8` |
| `TRACK_B_gates.json`、`s1_revision\*.json` | 从 W43 **只读复制的参考副本**，供原封不动的 `S3_19/S3_20/S3_22` 读取（不改 W43 原件，符合 D5.3「不制造第二份需同步的真相」——这里只是把既有只读参考搬进本卡作用域，运行时权威仍是 v14 的 `data/`） |
| `INTEGRATION.md` / `APPLY.md` / `UNCOVERED.md` / `DISAGREE.md` | 本卡文档 |
| `EVIDENCE\gen_s4_evidence.py` | 只读证据生成器（输出 `git_scoped_after.txt` / `game_proc.txt` / `game_proc_history.json` / `EVIDENCE_INDEX.json`） |
| `EVIDENCE\regress_full.stdout.txt` / `.exit.txt` | 全量回归原始 stdout + exit code |
| `out\` | 90 份逐例日志 + `SUMMARY.txt` + 3 张 SHA-256 对照表 + `V14_SOURCE_DELTA.json` |

---

## 2 · 校验（可复算，全部纯离线）

```bash
# 工作目录：lead\next_re_20261112_r02\W46_resolve_integration
python -B -X utf8 regress_dlc_v14.py
# 期望：cases: 90  passed: 90  failed: 0
#       assertions: 807 passed / 0 failed
#       exit: 0
#       inherited v13 cases: 82 / S4 cases: 8

python -B -X utf8 EVIDENCE\gen_s4_evidence.py
# 重新生成 git scoped 快照 / 进程观察 / EVIDENCE_INDEX.json
```

| 校验点 | 命令 / 文件 | 期望 |
|---|---|---|
| 全量回归 | `EVIDENCE\regress_full.exit.txt` | `0` |
| 逐例日志 | `out\<case>.log` × 90 | 每份含 `[cmd]` / `[exit]` / 原始输出 / `[assert] ... PASS` |
| v14 ↔ v13 逐字节兼容 | `out\SHA256_COMPAT_V14_V13.txt` | `files: 8  identical: 8  different: 0` / `VERDICT: IDENTICAL` |
| v14 ↔ v12 交叉印证 | `out\SHA256_COMPAT_V13_V12.txt`（继承 S3_25） | `VERDICT: IDENTICAL` |
| 源码 delta | `out\V14_SOURCE_DELTA.json` | 3 改 / 1 增 / 0 删 |
| `verify.py` 等未削弱 | `S4_8f` | 8 个文件 SHA-256 与 v13 相同 |
| 交付卫生 | `S4_8g` + 全卡扫描 | 无 `__pycache__` / `*.pyc` |
| git 只读 | `EVIDENCE\git_scoped_after.txt` | ` M` 行 0；只有 `?? <card>/` 整目录行 |

`[本次实测]` 本卡亲自跑通上述全部；`EVIDENCE\EVIDENCE_INDEX.json` 给出 11 个关键交付件的 SHA-256 与回归摘要哈希。

---

## 3 · 回滚

v14 是**自包含新目录**，不覆盖任何既有包，因此回滚是目录级操作：

1. **使用回滚**：把下游（W45/S5）对 `ra2forge_patched_v14\` 的引用改回 `W43_b_line_s3\ra2forge_patched_v13\`。v13 未被改动（`git` scoped 快照 0 行 ` M`），82 例在 v13 上仍由 W43 的 `regress_dlc_v13.py` 保证。
2. **源码级回滚**（若要把 3 个改动文件还原成 v13，仅用于排错）：
   - `ra2forge_patched_v14\ra2forge\builder.py` ← `W43_b_line_s3\ra2forge_patched_v13\ra2forge\builder.py`
   - `ra2forge_patched_v14\ra2forge\cli.py` ← 同上
   - `ra2forge_patched_v14\ra2forge\install.py` ← 同上
   - 删除 `ra2forge_patched_v14\ra2forge\resolve_integration.py`
   - 删除本卡 `regress_dlc_v14.py` / `s4_cases.py` / `out\` / `EVIDENCE\` 中的 v14 产物
   - 复跑 `W43_b_line_s3\regress_dlc_v13.py` 应回到 82/82。
3. **开关级回滚（推荐）**：无需改任何文件——**不传 `--feature-set`** 即得 v13 行为（`S4_8a..d` 已证 8/8 逐字节相同）。所有新行为都是 opt-in。

> 回滚不涉及 `ra2youli`、不涉及仓库 `ra2forge/`、不涉及 W21–W45；不涉及任何游戏进程（本卡 launched 0 / attached 0）。

---

## 4 · 与上游裁决的对应

| 裁决 | v14 落点 | 机检 |
|---|---|---|
| D1（E1 允许清单加 `ra2md.csf`） | v13 `data/` 原样带入 v14，未改 | `S3_19` |
| D2（版本守卫 opt-in） | `--version-guard` 分支完全未改；W46 新增的是**另一条** opt-in | `S3_23`、`S4_8f` |
| D3 / D3-补（G3 只警告、K2 硬拒绝） | `feature_subset.py` 逐字节未改，`resolve()` 语义保持 | `S3_21`、`S4_8f` |
| D5.1（K2 硬拒绝结案） | 未触碰；最小 CSF 负例在集成层落到 `RESOLVE_COUPLING_REFUSED` exit 26 | `S4_3g/h` |
| **D5.2（`battlemd:inplace` 暂缓）** | plan 层预留槽 + 写入口明确拒绝（§2.3） | `S4_7a..l` |
| D5.3（S1 权威 = v13 `data/`） | v14 `data/` 与 v13 逐字节相同；未改 W38 原文 | `S4_8f` |
| W42 `ACCEPTANCE_S2.md` B1–B17 | 82 例中的 `S3_1..S3_25` 原样重跑 | `S3_*` |
| W43 差距表 G-7 / G-8 / G-9 | §2.1 / §2.2 / §2.3 | `S4_1..S4_7` |
