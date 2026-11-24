# INTEGRATION.md · W46 / B 线（RE-N09）S4：`resolve()` ↔ install/builder 端到端串接

> 卡：`W46_resolve_integration`｜切片 **S4：集成 + 离线回归**｜2026-11-13（Asia/Shanghai）
> 工作目录：`D:\Project\ra2-campaign-forge`｜**纯离线**：未启动游戏、未 attach、未写 `ra2youli`、未改仓库 `ra2forge/`、未动 `W21`–`W45`、`git` 全程只读（scoped 快照 `EVIDENCE\git_scoped_after.txt`，` M` 行 **0**）。
> 上游（消费，不重造）：`REVIEW\LEAD_VERIFY_W43.md`、`W43_b_line_s3\S3_IMPLEMENTATION.md` 差距表 **G-1..G-13**、`W43_b_line_s3\ra2forge_patched_v13\`（当前最高包，回归 82/82，Lead 复跑）、`W42_b_line_s2\FEATURE_SUBSET_CONTRACT.md` + `ACCEPTANCE_S2.md`（17 条）、`REVIEW\LEAD_DECISIONS_W42.md`（D1–D5，含 **D5.1 K2 硬拒绝**、**D5.2 `battlemd:inplace` 暂缓**、**D5.3 S1 权威版本归属 v13 `data/`**）。
> 新包：`W46_resolve_integration\ra2forge_patched_v14\`（自 v13 派生）。

---

## 0 · 结论分级与红线

| 标记 | 本卡口径 |
|---|---|
| `[本次实测]` | 本卡亲自运行的命令/脚本直接取得：`python -B -X utf8 regress_dlc_v14.py` 的 90/90、807 断言、exit 0；`out\SHA256_COMPAT_V14_V13.txt` 的 8/8 MATCH；`out\V14_SOURCE_DELTA.json`；逐例 stdout/exit；git scoped 快照；进程观察 |
| `[本次读码]` | 逐行读 v13 的 `feature_subset.py` / `install.py` / `builder.py` / `cli.py` / `verify.py` + W42/W43 契约原文得到的代码事实 |
| `[静态推断]` | 由多项读码/实测事实组合推出的集成规范与工程判定（本卡新增的语义） |
| `[转引]` | W36 / W38 / W40 / W42 / W43 / FINAL_RULING / Lead 裁决的既有结论，本卡未独立复算 |
| `[待运行验证]` | 须真机/实算才能定谳；本卡未做 |

**红线**

1. **本卡不得写「B 线已完成」**。本卡只做 `resolve()` 与 install/builder 的**离线集成 + 离线回归**；真机行为等价性（G-1）由 **W45** 负责，与本卡无关。
2. **不得把回归全绿写成行为正确**。`90/90 PASS` 只证明文件层「计划 → 实际写入 → 清单/seal」在离线夹具下符合断言；沙箱内 `gamemd.exe` 是 inert 占位 `[转引]`（W34 `UNCOVERED.md` U9）。
3. **不得削弱 v13 的 82 例与 `verify.py` 语义**：82 例逐例保留并重跑通过；`verify.py` / `feature_subset.py` / `csf.py` / `s3_contract.py` / `version_guard.py` / `mapselmd.py` / 两份 `data/*.json` 与 v13 **逐字节相同**（`S4_8f` 机检）。
4. **`battlemd:inplace` 不实现**（D5.2）；只在 plan 层留可表达位置，并在写入口**明确拒绝**（§4）。
5. **不启用任何新开关时构建产物与 v13 逐字节相同**：`out\SHA256_COMPAT_V14_V13.txt` 8/8 MATCH / VERDICT IDENTICAL（`S4_8a..d`）。
6. **纯离线口径如实**：`[本次实测]` 本卡执行期间在本机多次观察到 `gamemd.exe` 进程（如 PID 32588、2080，路径均属 `W45_b_line_equivalence\sandbox_A1\`），有时为 0、有时被 W45 以新 PID 重启；**全部属 W45 真机卡**。多次观察都与「本卡 launched 0 / attached 0、未触碰」一致（`EVIDENCE\game_proc.txt` + `game_proc_history.json` 逐次留痕）。不沿用 W43「进程数 0」的恒称措辞，也不把 W45 的进程记到本卡头上。

---

## 1 · 总体形态（[本次实测] + [本次读码]）

`ra2forge_patched_v14/` = `ra2forge_patched_v13/` 的**最小增量派生**：

| 类别 | 文件 | 说明 |
|---|---|---|
| **修改（3）** | `ra2forge\builder.py` | 加 `feature_set/sandbox_state/guard_state/plan_report/resolve_plan_out` 五个 opt-in 形参；`build()` 在**第一个输出字节之前**跑 `resolve()`；plan 驱动 `MAPSELMD.INI`/`ra2md.csf` 的可选产物；写后逐文件对账；不启用时 `eff_* == 调用者原开关`，默认路径逐字节 v13 |
| | `ra2forge\cli.py` | `build` / `install` 新增 5 个 opt-in 开关 + `ResolveIntegrationRefused` 的独立退出码分支；`resolve` 子命令与 v13 **完全不变**（纯规划器仍可表达 `inplace`） |
| | `ra2forge\install.py` | `preinstall_plan()` 加 `feature_plan` 形参（包子集门禁 + 只读派生对账）；`install_package()` 在写盘前跑 `resolve()`、执行有序门禁、幂等重放短路、写后复核、把对账写进清单/seal；加常量 `INTEGRATION_MODE_TAG` |
| **新增（1）** | `ra2forge\resolve_integration.py` | 集成层：`MODE_SUPPORT` / `MODE_RESERVATIONS` / `SECOND_INSTALL_SEMANTICS` / `RECONCILIATION_RULES` / 退出码表 / `run_resolve()` / `install_resolve()` / `build_resolve()` / `filter_package_files()` / `reconcile_install()` / `classify_second_install()` / `detect_plan_orphans()` / `check_install_gates()` / `snapshot_leave_files()` / `check_post_write()` / `build_effective_switches()` / `build_reconcile()` / `write_plan_report()` / `validate_report_paths()` |

`out\V14_SOURCE_DELTA.json`（`[本次实测]`）：`changed = [builder.py, cli.py, install.py]`、`added = [resolve_integration.py]`、`removed = []`。**无删除、无 wholesale 重写**；`verify.py` 与纯规划器 `feature_subset.py` 未被触碰（`S4_8e/f`）。

**为什么仍然必须 opt-in（[静态推断]）**：v13 的 82 个回归用例沙箱里 `gamemd.exe` 是 `INERT PLACEHOLDER` 文本、非 PE `[转引]`；W38-S1 §3 规定「无已定谳 `BASELINE.json` ⇒ UNKNOWN ⇒ 零写拒绝」。若把守卫或新 plan 门禁设为默认启用，① 82 例全落拒绝；② §0 红线 5 的「逐字节相同」立不住。故 v14 全部新行为挂在 `--feature-set <FS.json>` 上，默认路径零改动。W46 的 plan 门禁与 W38-S1 的 `--version-guard` 是**两条独立 opt-in 通道**，互不覆盖（见 `DISAGREE.md` D-W46-1）。

---

## 2 · 三项落地

### 2.1 `resolve()` 串进真实写路径（差距表 **G-7**）

`[本次读码]` v13 的 `resolve()` 只由 `python -m ra2forge resolve` 子命令和一个纯规划用例消费；`install.py:preinstall_plan()` 从 `package_files()` 直接取包目录文件，`builder.py:build()` 由 `--mapselmd` / `--csf-out` 开关决定可选产物，二者与 plan 是**并列能力**（`S3_IMPLEMENTATION.md` §5 G-7 原文）。

v14 的接法（**两端都先跑 `resolve()`，再写**）：

| 端 | 落点 | 行为 |
|---|---|---|
| `install` | `install.py:install_package()` 首段 → `RI.install_resolve()` | 写盘前 `derive_install_sandbox_state(game, F)` **只读扫描真实游戏目录**得到 `present_files/absent_files`，再 `feature_subset.resolve(F, S)`；plan 的 `shipped()` 经 `RI.filter_package_files()` 成为 `preinstall_plan()` 的**唯一合法包子集**；`RI.reconcile_install()` 把 plan 的每一行 CREATE/REPLACE/LEAVE 映射到 v13 的真实 step action |
| `build` | `builder.py:build()` 开头 → `RI.build_resolve()` | 在 `out.mkdir()` **之前**跑 `resolve()`（build 无游戏目录 ⇒ 用标注为 `synthetic:true` 的 W42-S2 §0.1 S0 注入夹具，`[静态推断]`）；`RI.build_effective_switches()` 让 plan **驱动** `MAPSELMD.INI` / `ra2md.csf` 的产出（不再需要 `--mapselmd` / `--csf-out`），并在写前拒绝「开关要产、plan 标 LEAVE」的组合 |
| 两端 | `RI.check_install_gates()` / `RI.check_post_write()` / `RI.build_reconcile()` | 计划 vs 实际**逐文件对账**，不一致即拒绝 |

**「计划与实际写入必须一致；不一致即拒绝」的三道门（[本次实测] S4_1/S4_2/S4_3）**

1. **写前 · 包子集门**（`filter_package_files`）：`{package game-dir members}` 必须 **==** `plan.shipped()`。多一个 `EXTRA.MAP`、少一个 `MAPSELMD.INI`、或 plan 标 LEAVE 却仍在包里 ⇒ `PLAN_ACTUAL_MISMATCH` / **exit 24**，零写（`S4_3a..c` 用 `sha_tree()` 前后逐字节快照证明）。
2. **写前 · 逐文件对账**（`reconcile_install`）：`plan.files[]` 每一行产出 `{name, layer, planned_action, actual_action, write_bytes, consistent, note}`。`RECONCILIATION_RULES` 规定：CREATE ⇒ `created`；REPLACE ⇒ `replaced`（已有清单时才允许零写的 `unchanged`）；LEAVE ⇒ `LEAVE_SKIPPED`（无 step、不备份、不删、**不 adopt** —— W42-S2 §3.3 边界 1 `[转引]`）。`verdict=MATCH` 才放行。
3. **写后 · 字节级复核**（`check_post_write`，在清单 `_stage_text_and_replace` **之前**）：每个已落盘文件的 `sha256` 必须等于清单将记录的值；所有 LEAVE 行 `snapshot_leave_files()` 前后 SHA-256 相同；实际写集 == 对账写集。任一不符 ⇒ 抛 `OSError`，落入 v13 既有的 `_rollback()` 事务，清单不落盘（`install.py` 原 journal 结构未改）。

**对账产物（机检断言读到）**

- `--plan-report <path>.json`：完整 `plan_reconciliation`（`rows[]` 逐文件 + `verdict` + planned/actual 写集 + `second_install` + `orphan_cleanup`），且该路径**不得落在游戏目录内**（`validate_report_paths()`，W38-S1 §1.2 / ACCEPTANCE A7 `[转引]`；`S4_3i..k` 证 exit 30 + 零写）。
- `--resolve-plan-out <path>.json`：**早于所有门禁**持久化原始 plan，所以「被拒绝」也留有「计划但被拒」的证据（`S4_3f` 用它证 `guard_state=UNKNOWN` 下 plan 完整保留、`effective_game_dir_write_bytes=0`）。
- 清单 `ra2forge_install.json` 内嵌 `plan_actual_reconciliation`（逐文件 rows 的紧凑副本）、`feature_set_id`、`plan_mode`、`second_install`；`verify.py` 只读既有字段，新增键不改变其语义（`S4_2i`）。
- build 端：包内 `ra2forge_plan_reconciliation.json` + `BUILD_REPORT.txt` 增一行 plan 证据（`S4_1h/i`）。

**实测覆盖（[本次实测]）**：`S4_1` 19 断言（F1/F2/F3 plan 驱动构建、两种写前 mismatch、全关 F0 与 G1 基线互斥）、`S4_2` 13 断言（fresh install 的 9 行对账、LEAVE 字节不变、默认路径无 plan 键）、`S4_3` 11 断言（四种拒绝 + 字节级零写）。

### 2.2 二次安装 / orphan / legacy 联动（差距表 **G-8**）

`[转引]` W42-S2 §3.3 边界 3 明确把「二次安装/升级/orphan/legacy 的子集联动」移交 S3，而 W43 的 `resolve()` 只规约首次安装 + 卸载往返（`S3_IMPLEMENTATION.md` §5 G-8）。v14 把它定谳为**数据**（`resolve_integration.SECOND_INSTALL_SEMANTICS`，`S4_4i` 机检）：

#### 【二次安装语义定谳】

> **同一包重复安装 = 幂等重放（`IDEMPOTENT_REPLAY`），不是拒绝，也不是静默重写。**
> 判定条件：`package_id` 相同 ∧ `feature_set_id` 相同 ∧ 每个已登记文件字节未漂移。
> 语义：`resolve()` **照常先跑**、plan **照常产出**、逐文件对账 **照常做**，但**游戏目录零字节写入**（连 `ra2forge_install.json` / `.seal` 都不刷新，`installed_at` 不变）。
> 任何 drift / orphan ⇒ **拒绝**，绝不用重放覆盖漂移。
> 依据 `[静态推断]`：v13 的「同 id 再装」走 `upgrade` 分支会把每个字节相同的文件记成 `action="unchanged"` 并**重写清单**（`install.py:1356-1367, 2117-2161` `[本次读码]`）——那既不是幂等（清单字节变了），又会在「字节相同但未登记」时触发 adopt 警告。v14 选择把它收敛成显式的零写重放。

| verdict | 触发 | 语义 | 机检 |
|---|---|---|---|
| `FRESH` | 无清单 | 按 plan 执行 CREATE/REPLACE；LEAVE 严格零写、不 adopt | `S4_2j` |
| `IDEMPOTENT_REPLAY` | 同 `package_id` + 同 `feature_set_id` | **零游戏目录写入**；plan/对账仍产出 | `S4_4a..h` |
| `SUBSET_UPGRADE` | 同 `package_id` + **不同** `feature_set_id` | 执行新 plan；旧清单里被新 `shipped()` 丢弃的文件经 v13 `ORPHAN-FIX01` 退出，并登记进对账 | `S4_5a..i` |
| `LEGACY_PRE_PLAN` | 有清单但**无** `feature_set_id`（v13 或更早，如 W22 `--adopt-legacy` 记录） | 不可与 plan 直接对账 ⇒ 必须 `--adopt-legacy` 显式声明继任；否则 **exit 28** 零写 | `S4_6d..i` |
| `DIFFERENT_PACKAGE` | `package_id` 不同 | v13 `PKG-IDENT01` **exit 3** 保持，plan 绝不释放该身份门 | `S4_6k/l` |

`[本次实测]` `S4_4e`：`sha_tree(game)` 在二次安装前后**逐字节相同**（含清单/seal）；`S4_4d`：报告 `game_dir_file_writes=0`、`effective_game_dir_write_bytes=0`、`actual_game_dir_write_set=[]`；`S4_4g`：4 个 REPLACE 行映射到零写 `unchanged`；`S4_4h`：两个元数据行是 `REPLAY_NOOP`。

#### orphan 联动

- **磁盘上有未被清单记录的我方文件**（`detect_plan_orphans`）：byte-identical 到包成员，或带 `Generated by RA2 Campaign Forge` 标记。`[本次读码]` v13 会把它 `action="unchanged"` **adopt 为 ours** 并警告「later uninstall WILL DELETE it」（`install.py:1358-1367`）。v14 的 plan 路径**拒绝**（`ORPHAN_PLAN_REFUSED` / **exit 27**），零写（`S4_6a..c`）。处置：`uninstall --legacy`、手工移除，或对 legacy 记录用 `--adopt-legacy`。
- **子集缩小时的 orphan 清理**（`[静态推断]` 关键取舍）：v13 `_plan_orphans()` 会删除「上一版清单登记、这一版包里没有」的**我方**文件。这与 W42-S2 的 LEAVE「不删」字面冲突。v14 明确把它建模为 **`ORPHAN_CLEANUP:<mode>`**（`reconcile_install` 行 `actual_action`），只在 `SUBSET_UPGRADE` 下 `consistent=true`，并从 `snapshot_leave_files()` 的 LEAVE 快照中排除——即：**LEAVE 仍严格零写，被删的是上一版我方登记文件，不是 LEAVE 的第三方文件**。`[本次实测]` `S4_5e`：`MAPSELMD.INI` 行 `planned_action=LEAVE` / `actual_action=ORPHAN_CLEANUP:remove` / `consistent=True`，文件确被移除且清单 `removed_orphans[]` 留痕。

#### legacy 联动

- 两层门，顺序明确（[静态推断]）：**v13 身份门在前**（无 `package_id` 且无 `--adopt-legacy` ⇒ `PackageIdentityBlocked` exit 4），**W46 plan 门在后**（有 `package_id` 但无 `feature_set_id` ⇒ `LEGACY_PLAN_RECONCILE_REQUIRED` exit 28）。`--adopt-legacy` 同时解除两层。
- `[本次实测]` `S4_6d..i`：v13 风格默认安装产出无 `feature_set_id` 的清单 → plan 安装 exit 28 且 `sha_tree` 不变 → 加 `--adopt-legacy` 后 exit 0，新清单得到 `feature_set_id`、`plan_legacy_adopted=true`、`second_install=LEGACY_PRE_PLAN`、对账 `MATCH`。
- 与 W22 `--adopt-legacy` 的关系：不改写 v13 的 `adopt_legacy` 实现（`install.py:1271-1314` `[本次读码]` 原样保留），只在 plan 路径上增加「pre-plan 记录必须显式继任」这一条。

### 2.3 `battlemd:inplace` 暂不实现，但 plan 层留位（差距表 **G-9** / 裁决 **D5.2**）

`[转引]` Lead D5.2：`battlemd:inplace` **暂缓**（产品路线未拍板；W27/W39/W44 已把它当诊断变体用，属产品化包装而非新技术风险）。`[转引]` W42-S2 §4.1 F5 允许该模式但注明需 Lead 定谳。

v14 的做法（**不实现写侧，但把改动面封死**）：

1. **纯规划器不动**：`feature_subset.py` 与 v13 **逐字节相同**（`S4_8f`）。它仍能表达 `inplace`：`shipped()` 返回 `BATTLEMD.INI`、`resolve()` 产出该行 `REPLACE` / `original_absent=false` / `backup_slot=BATTLEMD.INI.ra2forge.bak` / `uninstall=RESTORE`（`S4_7a/b`）；`python -m ra2forge resolve` 子命令 exit 0（`S4_7c`）。**这就是「plan 层可表达的位置」**。
2. **预留槽位是数据**：`resolve_integration.MODE_RESERVATIONS["battlemd:inplace"]` 含 `status="DEFERRED"`、`authority=LEAD_DECISIONS_W42 D5.2`、`plan_layer_slot{shipped_target, plan_action_when_present, original_absent, backup_slot, uninstall_action, write_entry, expressible_by, not_expressible}`、`activation_gate`、`change_surface`（**恰 4 个文件**的封闭清单）、`explicit_refusal_reason_code/exit_code`。该块随每次 `run_resolve()` 一并写进 `plan.integration.plan_layer_reservations`，`--resolve-plan-out` 可机检（`S4_2k`、`S4_7d..g`）。
3. **写入口明确拒绝**：`RI.check_inplace_mode()` 是**唯一**的拒绝点，`run_resolve()` 调用它；`install --feature-set <inplace>` 与 `build --feature-set <inplace>` 均 ⇒ `BATTLEMD_INPLACE_REFUSED` / **exit 25**，错误串点名 D5.2、预留槽位、改动面文件数，且 **零写**（`S4_7h..k` 用 `sha_tree` 与「无 `BATTLEMD.INI.ra2forge.bak`、无输出目录」证明）。`S4_7l` 直接 import `run_resolve()` 证明该拒绝发生在集成层而非纯规划层。

`[静态推断]` 将来 Lead 放行时，改动面 = `MODE_SUPPORT` 翻 `SUPPORTED` + 摘掉 `check_inplace_mode` + `builder.py` 增加 `BATTLEMD.INI` 就地产物 + `cli.py` 暴露 mode；`install.py` 的 `_write_step()` 已具备 REPLACE/backup/RESTORE 能力，**无需改事务结构**。本卡已用断言把「当前明确拒绝」钉死（`S4_7d/h/k/l`），避免将来静默放行。

---

## 3 · 计划 vs 实际对账：机检形态（[本次实测]）

`out\S4_2.log` / `out\S4_1.log` 内有完整命令 + 原始 stdout + exit + 逐项判据。对账数据结构（`--plan-report` 的 `plan_reconciliation`）：

```json
{
  "schema_version": "w46-s4-1",
  "integration_id": "W46-S4-resolve-integration",
  "phase": "install",
  "feature_set_id": "W46-S4-F1",
  "verdict": "MATCH",
  "rows": [
    {"name":"BATTLEMD98.INI","layer":"game_dir","planned_action":"CREATE",
     "actual_action":"created","write_bytes":382,"consistent":true},
    {"name":"BATTLEMD.INI","layer":"game_dir","planned_action":"LEAVE",
     "actual_action":"LEAVE_SKIPPED","write_bytes":0,"consistent":true},
    {"name":"ra2forge_install.json","layer":"game_dir_metadata",
     "planned_action":"CREATE","actual_action":"MANIFEST_OR_SEAL_WRITE",
     "write_bytes":0,"consistent":true}
  ],
  "planned_game_dir_write_set": ["BATTLEMD98.INI","CP1.MAP","CP2.MAP","expandmd98.mix"],
  "actual_game_dir_write_set":  ["BATTLEMD98.INI","CP1.MAP","CP2.MAP","expandmd98.mix"],
  "effective_game_dir_write_bytes": <sum>,
  "second_install": {"verdict":"FRESH", ...},
  "orphan_cleanup": {}
}
```

| 判据 | 用例 | 结果 |
|---|---|---|
| plan 每行 `consistent=true`，`verdict=MATCH` | S4_2b/c、S4_1b/c、S4_5d、S4_6i | PASS |
| planned 写集 == actual 写集（4 个 CREATE） | S4_2d | PASS |
| LEAVE 行 `LEAVE_SKIPPED` / `write_bytes=0` / 官方 `BATTLEMD.INI` SHA 前后相同 | S4_2f/g、S4_1e | PASS |
| 包里多一个 plan 未授权文件 ⇒ exit 24 + `sha_tree` 零写 | S4_3a..c | PASS |
| build 端 emitted game 子集 == `plan.shipped()` | S4_1d、S4_1k/n | PASS |
| 对账写进清单（9 行紧凑副本） | S4_2i | PASS |
| 门禁拒绝时原始 plan 仍保留（planned but denied） | S4_3f | PASS |
| 写后字节级复核（落盘 sha / LEAVE 快照 / 写集一致） | S4_2、S4_5 全链路 | PASS |

**退出码表（W46/S4 新增，仅 opt-in 分支使用；v13 的 0–10 与 W38-S1 的 20/21/22/23 均未改动）**

| exit | reason_code | 含义 |
|---|---|---|
| 24 | `PLAN_ACTUAL_MISMATCH` | plan 与实际写入/包子集不一致，零写 |
| 25 | `BATTLEMD_INPLACE_REFUSED` | D5.2 暂缓模式明确拒绝，零写 |
| 26 | `RESOLVE_COUPLING_REFUSED` | `resolve()` 耦合拒绝（K1–K12 / B8/B9/B10），零写 |
| 27 | `ORPHAN_PLAN_REFUSED` | 未登记我方文件，零写 |
| 28 | `LEGACY_PLAN_RECONCILE_REQUIRED` | pre-plan 清单需 `--adopt-legacy`，零写 |
| 29 | `RESOLVE_GUARD_ZERO_WRITE` | 注入 `guard_state≠KNOWN_GOOD`，plan 保留但零写 |
| 30 | `PLAN_REPORT_INSIDE_GAME_DIR` | 报告路径落在游戏目录内（W38 A7），零写 |
| 31 | `PLAN_INPUT_UNREADABLE` | `--feature-set` / `--sandbox-state` 不可读 |

---

## 4 · 向后兼容与回归（[本次实测]）

命令：`python -B -X utf8 regress_dlc_v14.py`（工作目录 `W46_resolve_integration`）

```
cases: 90  passed: 90  failed: 0
assertions: 807 passed / 0 failed
exit: 0
inherited v13 cases: 82
S4 cases: 8
```

- **82 例逐例保留**：`P0/V1-6/P1-4/C1-2/T4/S1-8/F0-7/U1-6/R0-2/CSF1-6/MS1-6/CSF_INST1-6`（57 例） + `S3_1..S3_25`，全部对 v14 重跑通过；`s3_cases.py` 与 v13 **逐字节相同**（只把 `G.CARD` 指向本卡根目录，为此把 W43 的 `TRACK_B_gates.json` 与 `s1_revision/` 两份只读参考副本一并带入本卡，见 `APPLY.md`）。
- **S4_1..S4_8**：8 例 / 93 条断言，覆盖 §2.1/§2.2/§2.3 + SHA-256 兼容 + 源码 delta + `__pycache__` 卫生。
- **逐例日志**：`out\<case>.log`（90 份，命令 + 原始 stdout/stderr + exit + 逐项判据）；汇总 `out\SUMMARY.txt`。
- **SHA-256 对照**：`out\SHA256_COMPAT_V14_V13.txt` —— 8 产物 **8/8 MATCH / VERDICT: IDENTICAL**（`BATTLEMD98.INI` / `BUILD_REPORT.txt` / `CP1.MAP` / `CP2.MAP` / `INSTALL.txt` / `expandmd98.mix` / `ra2forge_package.json` / `story.md`）。另 `out\SHA256_COMPAT_V13_V12.txt`（继承 S3_25，v14 vs v12 仍 8/8 MATCH）与 `out\SHA256_COMPAT.txt`（继承 CSF_INST5）互为交叉印证。
- **源码 delta**：`out\V14_SOURCE_DELTA.json` —— 3 改 + 1 增 + 0 删；`S4_8f` 机检 `verify.py` 等 8 个文件与 v13 逐字节相同；`S4_8g` 机检 v14 包内**无 `__pycache__` / `*.pyc`**（W43 的卫生问题未重复）。
- `EVIDENCE\regress_full.stdout.txt` + `EVIDENCE\regress_full.exit.txt`（`0`）。

**不得把 90/90 写成行为正确**：这些是文件层/计划层/离线夹具层断言；散装 `ra2md.csf` / `MAPSELMD.INI` 是否被引擎采用、官方 UI 是否真显示我方文本，至今 `[待运行验证]`（W30/W34 `UNCOVERED.md` `[转引]`，W45 负责）。

---

## 5 · 仍存差距（**必须保留**）

> 本卡是「离线集成 + 离线回归」。以下均**未达成 / 未验证**；不得据 90/90 推断已完成。

| # | 差距 | 状态 | 归属 |
|---|---|---|---|
| G-1 | **真机行为等价性**：散装 `ra2md.csf`/`MAPSELMD.INI` 是否被引擎采用、官方 UI 是否真的显示我方文本、战役推进是否真触发 | `[待运行验证]`，本卡纯离线 | **W45** |
| G-2 | 版本守卫默认未启用（仍需 `--version-guard`） | 未改，v13 原样 | S5 + Lead 签发 `BASELINE.json` |
| G-3 | `BASELINE.json` 实算 / Track A 签发 | 未做（本卡未计算任何真实游戏二进制哈希） | Lead 另立卡 |
| G-4 | C07/C09/C10/C11/C12 的 L2/L3 判据与原始字节窗口未接入运行时 | 未做 | S5 |
| G-5 | `ra2opt` XCHAIN 10 行写入口未接线（独立包，不在 v14 内） | 未做，仍显式登记为 out-of-scope | 另卡 |
| G-6 | E4（`verify --fix` / seal 自愈）仍严格只读 | 未做 | 另卡 |
| **G-7** | **`resolve()` ↔ install/builder 端到端串接** | **本卡已落地（离线文件层）**：plan 消费、逐文件对账、写后复核、清单/seal 内嵌；**install 事务的回滚/备份/卸载结构仍复用 v13，未重写** | 已完成（离线）；真机行为见 G-1 |
| **G-8** | **二次安装 / orphan / legacy 子集联动** | **本卡已定谳并实现**（§2.2）；但**卸载（uninstall）侧尚未按 plan 的 delete/restore 集合做逐文件对账** —— v13 `uninstall()` 仍按清单 `files[]` 自行判定，`plan` 未回灌到 E3 | 部分完成；卸载侧对账属下一卡 |
| **G-9** | **`battlemd:inplace` 真机实现 / 回滚** | **未实现（D5.2 暂缓）**；本卡只留出 plan 层预留槽 + 明确拒绝断言 | Lead + S5 |
| G-10 | 安装/卸载内容级校验（MAPSELMD/CSF 的 verify 内容级校验，W34 U7 `[转引]`） | 未做 | S5 |
| G-11 | 退出码 20/21/22/23 与 v12 现有 CLI 的完整集成审计 | 本卡新增 24–31 独立码段并机检不冲突（`S4_4j`），但 W38-S1 的 20–23 与 `--force` / `--allow-content-conflict` / `--adopt-legacy` / `--legacy` 的**全组合**仍未逐一实测 | 部分验证，S5 |
| G-12 | 多副本 / `.detour` 字节判据 D1–D5 实算 | 未做 | Lead |
| G-13 | S1 修订合入 W38 目录 | 未做（D5.3 裁决：运行时权威 = v13 `data/`，W38 原文留作历史） | Lead |
| **G-14（本卡新增）** | **build 侧 F0（全关）与内建 G1 基线互斥**：`resolve()` 层 F0 是「零游戏目录写」的合法计划，但 `builder.py` 的 design-driven 构建**总是**产出 `BATTLEMD98.INI` + `*.MAP` + `expandmd98.mix` ⇒ plan 未授权 ⇒ **exit 24 拒绝**（`S4_1r/s`）。这是明确的、机检的拒绝，不是静默产全包；要让 F0 能驱动 build，需要 build 支持「空游戏目录包」，属新能力 | 已显式拒绝 + 断言；未实现 F0 构建 | S5 |
| **G-15（本卡新增）** | **build 写后不一致的清理**：已知不一致在 `build_subset_gate` 于第一次写之前拒绝（零输出）；若写后复核仍不一致，报错并**保留本卡沙箱内 package dir 供检查**（不写游戏目录），未做自动 rmtree（避免误删用户既有目录） | 已知限制，已登记 | S5 |
| **G-16（本卡新增）** | **`guard_state` 仍为注入夹具**：`derive_install_sandbox_state()` 只读扫描真实游戏目录的 present/absent，但 `guard_state` 是 `--guard-state` 注入值 / 默认 `KNOWN_GOOD`，**W38-S1 `classify()` 未在此处运行**。故本卡不证明「身份守卫已普遍启用」（与 `LEAD_VERIFY_W43.md` §3 事实 2 的结构性限制一致） | 未做，已登记 `UNCOVERED.md` U-W46-1 | Lead + S5 |

**结论口径**：B 线到本卡为止新增了「**离线可机检的 `resolve()` ↔ 写路径集成**」，**不是**「B 线已完成」，**不是**「守卫已具备」，**不是**「回归全绿 ⇒ 行为正确」。真机行为等价性由 **W45** 负责。

---

## 6 · 纪律复核（[本次实测] + [本次读码]）

- **纯离线**：未启动游戏、未 attach。`[本次实测]` 本卡执行期间在本机多次观察到 `gamemd.exe`（如 PID 32588 / 2080，路径 `W45_b_line_equivalence\sandbox_A1\gamemd.exe`），属 W45 卡、非本卡启动/触碰；有时为 0、有时被 W45 以新 PID 重启。多次观察下本卡均 launched 0 / attached 0（`EVIDENCE\game_proc.txt` + `game_proc_history.json`）。沙箱内 `gamemd.exe` 仅 inert 文本占位 `[转引]`。
- 未写 `ra2youli/`（只 READ 其 `ra2forge_install.json` 作兼容夹具，与 v13 回归一致）、未改仓库 `ra2forge/`、未动 `W21`–`W45`、未改 `verify.py`；`git` 全程只读（`EVIDENCE\git_scoped_after.txt`：3 行 `??`，**0 行 ` M`**）。
- 唯一写域：`lead\next_re_20261112_r02\W46_resolve_integration\`。
- 分级：全文按 §0 口径标注；5,211 标签 / 5,573 B / `074ccccd…` / W40 五臂结论 / D5.2 裁决均按来源标 `[转引]`。
- 冲突取舍：`DISAGREE.md`；未覆盖与不确定项：`UNCOVERED.md`；补丁/校验/回滚：`APPLY.md`；证据：`EVIDENCE\`（脚本 + stdout + exit + 索引）。
- 交付卫生：v14 包与整卡**无 `__pycache__` / `*.pyc`**（`S4_8g` 机检 + 全卡扫描）。
