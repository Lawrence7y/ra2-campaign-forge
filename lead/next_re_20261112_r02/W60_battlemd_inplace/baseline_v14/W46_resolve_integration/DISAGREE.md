# DISAGREE.md · W46 / S4：与 W42/W43/W38 契约的冲突与取舍

> 逐条登记「本卡实现」与「上游只读契约」之间的张力，取舍一律服从 Lead 裁决（D1–D5）。
> 契约原文**不就地修改**；本卡只登记差异与理由。分级同 `INTEGRATION.md` §0。

---

## D-W46-1 · W42-S2 §6 C3「守卫优先」与 W46 的两条独立 opt-in 通道

**上游**：`FEATURE_SUBSET_CONTRACT.md` §6 规定 `classify() → guard_state` 是 `resolve(F, S)` 的**前置输入**，`effective_writes = S1_DECISION_TABLE[guard_state][entry] ∩ plan.write_set`；`guard_state` 完全由 W38-S1 `classify()` 决定，输入不含 feature-set（C1）。

**本卡取舍**：v14 把 `classify()` 留在 v13 的 `--version-guard` opt-in 通道**原样不动**，另开 `--feature-set` 通道跑 `resolve()`；后者用**注入**的 `guard_state`（默认 `KNOWN_GOOD`，可 `--guard-state` 改），并在 `guard_state ≠ KNOWN_GOOD` 时按 §6 C3 零写拒绝（exit 29，plan 完整保留）。

**理由 `[静态推断]`**：
1. 若把 W38-S1 守卫设为默认启用，v13 的 82 例（沙箱 `gamemd.exe` 是 inert 文本、非 PE `[转引]`）会全部落 `UNKNOWN` 拒绝，且「不开新开关时逐字节相同」立不住 —— 这正是 `LEAD_DECISIONS_W42.md` D2-补 已批准的结论，本卡不翻案。
2. W46 是**集成卡**，任务是「把 `resolve()` 串进写路径」，不是「启用身份守卫」。把两者捆在一起会扩大改动面到 `version_guard.py`（本卡已证该文件与 v13 逐字节相同，`S4_8f`）。
3. 「feature 不改 guard_state」不变式仍被遵守：`S4_3f` 机检 `guard_state_unchanged_by_s2=True`、注入 `UNKNOWN` 不被任何 `s2ReasonCode` 改写。

**未解决部分**：两条通道**叠加**（同时传 `--feature-set` 与 `--version-guard`）时的门禁先后顺序未写专门回归用例，登记在 `UNCOVERED.md` U-W46-6。代码结构上 `_s3_guard_gate()` 先于 `RI.install_resolve()`（`install.py:install_package()` 首段 `[本次读码]`），即 S1 身份门在前、S2 耦合/对账门在后，与 W42 §6 C3「守卫优先」一致。

---

## D-W46-2 · W42-S2 §3.3「LEAVE = 不写、不备份、不删、不 adopt」与 v13 ORPHAN-FIX01 的删除

**上游**：`FEATURE_SUBSET_CONTRACT.md` §3.3 把 LEAVE 定义为「严格零写：不写、不备份、不删、不 adopt」，并明确它**不同于** v11 `action="unchanged"` 的 adopt 语义；§3.3 边界 3 把「二次安装/升级/orphan/legacy 的子集联动」移交 S3。

**冲突 `[本次读码]`**：v13 `install.py:_plan_orphans()` / `_execute_orphan_plan()` 在「上一版清单登记、这一版包里没有」时会**删除**该我方文件（`mode="remove"` / `"remove_absent"`）。若 plan 把该文件名标成 LEAVE（本版不 ship 它），字面上就与「LEAVE 不删」冲突。

**本卡取舍 `[静态推断]`**：把这类删除建模为独立的 **`ORPHAN_CLEANUP:<mode>`** actual action，**不算 LEAVE**：
- `reconcile_install()` 中该行 `planned_action=LEAVE`、`actual_action=ORPHAN_CLEANUP:remove`，仅当 `second_install.verdict == SUBSET_UPGRADE` 且 mode ∈ {remove, remove_absent, restore, missing} 时 `consistent=true`；
- `snapshot_leave_files()` 把这些名字从 LEAVE 字节快照中**排除**（它们不是零写的 LEAVE 行）；
- 断言明确写「这是上一版我方登记文件的退出，**不是** adopt 一个第三方文件」（`S4_5e` 机检该行 note 与 `orphan_cleanup`）。

**理由**：LEAVE 保护的语义核心是「不 adopt 未登记的第三方文件、不写不属于本包的文件」；删除**我自己上一版登记并投放**的文件恰是 W21 `original_absent` / over-restore 陷阱的正解（W21 `DISAGREE.md:17-24` `[转引]`），不是 LEAVE 要防的行为。把它显式建模而非让写后复核静默失败，是对 W42 §3.3 边界 3 的落地。

**未解决部分**：v13 `orphan.mode="changed"`（文件被外部改过）仍走 v13 的 `risks` 严格拒绝，本卡未改；`UNCOVERED.md` U-W46-3 登记卸载侧未对账。

---

## D-W46-3 · W42-S2 §4.2 四集合「由 `files[]` 派生」与 v13 清单字段的并行

**上游**：`FEATURE_SUBSET_CONTRACT.md` §4.2 要求 `install_write_set` / `backup_set` / `uninstall_delete_set` / `uninstall_restore_set` **由 `files[]` 派生，不得独立填写**；§7 G4 要求 `feature_set_id` 进 manifest、digest/seal/清单/备份/卸载同步。

**本卡取舍**：`resolve_integration.py` **不重算**这四集合（v13 `feature_subset.build_plan_from_files()` 已实现且 `S3_2/S3_7/S3_17` 机检，本卡未改该文件）。W46 新增的对账层读的是 `plan.files[]` 与 **v13 真实 steps**，产出的是 `planned_game_dir_write_set` / `actual_game_dir_write_set`（**新字段名**，故意不与 S2 四集合同名，避免制造第二份真相）。

- `feature_set_id` 确实写进了清单（`S4_2i`），满足 §7 的 G4 要求；`package_digest` 仍由 v13 `package_digest_from_steps(steps)` 计算，**未**改成 `plan.digest_inputs`（后者是 S2 的规划期合成摘要，含 `guard_state`，与真实落盘字节无关）。
- 理由 `[静态推断]`：若把清单的 `package_digest` 换成规划摘要，会破坏 82 例里依赖 `expected_digest()` 的断言（`regress_dlc_v13.py:192-211` `[本次读码]`）以及 seal 的既有语义，属于「削弱 v13」；本卡纪律禁止。

**未解决部分**：`uninstall_delete_set` / `uninstall_restore_set` 仍未回灌到 `uninstall()`（U-W46-3），故 §4.2/§7 的「卸载集合与 `shipped()` 同步」在**执行层**仍是 v13 清单驱动，不是 plan 驱动。已登记为 G-8 部分完成。

---

## D-W46-4 · W42-S2 §4.1 F5 / Lead D5.2：`battlemd:inplace` 的「契约允许」与「本卡拒绝」

**上游**：`FEATURE_SUBSET_CONTRACT.md` §4.1 F5 把 `battlemd:inplace` 列为 `PASS*` 组合（`BATTLEMD.INI=R`、备份、卸载 RESTORE），但注明「实现/回滚属 S3 且需 Lead 定谳」；`ACCEPTANCE_S2.md` B4 也把它列为 `[待运行验证]` 的期望。**Lead D5.2（20:30）裁决：暂不实现**。

**本卡取舍**：**纯规划器保留表达力**（`feature_subset.py` 与 v13 逐字节相同，`resolve` 子命令 exit 0，`S4_7a..c`），但**写入口明确拒绝**（`BATTLEMD_INPLACE_REFUSED` / exit 25，`S4_7h..l`）。即：F5 在 **plan 层**仍 PASS，在 **write 层**被拒。

**理由 `[转引]`**：D5.2 原文「产品路线（借官方入口 vs 绕过菜单）用户尚未拍板」；W27/W39/W44 已把它当诊断变体用过，属产品化包装。本卡服从裁决，不擅自实现，也不从规划器里删掉该模式（删掉会扩大将来放行时的改动面）。

**与 B4 的关系**：B4 是 W42 的断言设计，`[待运行验证]`；本卡用 `S4_7` 证明「当前明确拒绝」，**不**声称 B4 已通过。若 Lead 将来放行，按 `MODE_RESERVATIONS.change_surface`（4 文件）改动后 B4 才进入实现范围。

---

## D-W46-5 · W43 `S3_IMPLEMENTATION.md` §0 红线 2 / `LEAD_VERIFY_W43.md` §5 红线

**上游**：「不得把回归全绿写成行为正确」「82/82 只证明文件层 plan/guard 行为」。

**本卡取舍**：`INTEGRATION.md` §0 红线 2、§4 末段、§6 均原样承接该口径，把 90/90 明确限定为「文件层计划→实际写入→清单/seal 在离线夹具下符合断言」；`INTEGRATION.md` §5 保留完整差距表并**新增** G-14/G-15/G-16 三条本卡自己发现的差距；`UNCOVERED.md` 逐条列出「本卡没有声称的事」。

**一处如实更正 `[本次实测]`**：W43 的纪律复核写「`gamemd.exe`/`game.exe` 进程数 **0**」。本卡执行期间在本机**多次**实测到 `gamemd.exe`（如 PID 32588 / 2080，路径均属 `W45_b_line_equivalence\sandbox_A1\`），有时为 0、有时被 W45 以新 PID 重启。本卡**不**沿用「进程数 0」的恒称措辞，改为「W46 launched 0 / attached 0、逐次观察留痕、观察到的进程属 W45 且未触碰」（`EVIDENCE\game_proc.txt` + `game_proc_history.json`）。这不是与 W43 的结论冲突，而是**不同时刻的盘面事实**；写死「0」在本卡会是假陈述。

---

## D-W46-6 · W42-S2 §4.3 / W38-S1 §1.2 A7：报告文件路径归属

**上游**：`FEATURE_SUBSET_CONTRACT.md` §4.3 规定 `csf_out_path` 落在游戏目录内 ⇒ 改贴 `E1` 交 S1；W38-S1 `ACCEPTANCE.md` A7 要求路径归属用 `realpath + commonpath` 判定。

**本卡取舍**：W46 新增的两类报告（`--plan-report` / `--resolve-plan-out`）**根本不允许**落在游戏目录内 —— `RI.validate_report_paths()` 在 `install_resolve()` 最前面（**任何写之前**）用 `commonpath` 判定并 `exit 30` 拒绝，而不是「改贴 E1 后允许写」。

**理由 `[静态推断]`**：报告是本卡的审计产物，不是包内容；在游戏目录里放一个清单未登记的文件正是 W21 orphan 风险的来源。W43 的 `guard_report.json` 也规定「落在 `--guard-report` 指定路径（本卡沙箱，**不在游戏目录**）」（`S3_IMPLEMENTATION.md` §3.1 `[转引]`），本卡与之对齐。这与「游戏目录内 `csf_out` 改贴 E1」不是同一类写点：后者是**产品产物**，前者是**审计产物**。

---

## D-W46-7 · `regress_dlc_v14.py` 的 `V12_ROOT` 命名与「82 例逐字保留」

**上游**：W43 的 `regress_dlc_v13.py` 里 `V12_ROOT` 其实指向 v13 包（历史别名，为让 57 个继承用例的调用点不动）。

**本卡取舍**：复制后把 `V12_ROOT` 改指向 **v14 包**，但**保留变量名**；`V9_ROOT..V7_ROOT` 等别名链、`Case` 类、57+25 个用例函数体、`s3_cases.py` 全部**一字未改**。为让 `S3_19/S3_20/S3_22` 仍能读到 `G.CARD/TRACK_B_gates.json` 与 `G.CARD/s1_revision/`，把 W43 的这 3 个文件作**只读参考副本**带进本卡根目录（未改 W43 原件）。

**理由 `[静态推断]`**：改名会让 82 例的调用点全变，违反「不得削弱 v13 的 82 例」；带副本而不是改 `s3_cases.py` 的路径，是为了让 `S3_*` 用例源码与 W43 **逐字节相同**（`APPLY.md` §1.5）。D5.3 裁决的「运行时权威 = v13 `data/`」在 v14 中仍是 `ra2forge_patched_v14\ra2forge\data\`（与 v13 逐字节相同），本卡的 `s1_revision/` 只是给回归用例读的只读参考，不构成第二份运行时真相。

---

## 汇总表

| 编号 | 冲突对象 | 取舍 | 服从的裁决 |
|---|---|---|---|
| D-W46-1 | W42 §6 C1/C3 | 两条独立 opt-in；`guard_state` 仍注入，不默认启用守卫 | D2-补 |
| D-W46-2 | W42 §3.3 LEAVE | orphan 清理建模为 `ORPHAN_CLEANUP`，不算 LEAVE | W21 over-restore 结论 |
| D-W46-3 | W42 §4.2 / §7 | 用新字段名做对账，不改 v13 digest/seal/四集合 | 「不得削弱 82 例」 |
| D-W46-4 | W42 §4.1 F5 / B4 | plan 层可表达，write 层明确拒绝 | **D5.2** |
| D-W46-5 | W43 红线 | 承接「回归全绿 ≠ 行为正确」；如实更正进程数口径 | W43 §0/§5 |
| D-W46-6 | W42 §4.3 / A7 | 审计报告禁止落游戏目录（exit 30） | W43 guard_report 口径 |
| D-W46-7 | W43 harness 命名 | 保留历史别名 + 只读参考副本，82 例源码不动 | 本卡纪律 |
