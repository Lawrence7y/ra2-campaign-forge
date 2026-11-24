# S3_IMPLEMENTATION.md · W43 / B 线（RE-N09）S3：实现 + 回归

> 卡：`W43_b_line_s3`｜切片 **S3：实现 + 离线回归**｜2026-11-13（Asia/Shanghai）
> 工作目录：`D:\Project\ra2-campaign-forge`｜**纯离线**：未启动 `gamemd.exe`、未 attach、未写 `ra2youli`、未改仓库 `ra2forge/`、未动 `W21`–`W42` 任何目录、`git` 全程只读。
> **本卡只到「实现 + 离线回归」**。真机行为等价性验证（安装态/执行态/行为态）**不在本卡范围**，属 S4/S5。
> 上游（消费，不重造）：`REVIEW\LEAD_DECISIONS_W42.md`（4 项裁决，全是硬约束）、`REVIEW\LEAD_SIGNOFF_BATCH_W38_W41_W42.md`、`W38_version_guard_s1\`（S1 契约 + 80 行写入口盘点）、`W42_b_line_s2\`（S2 契约 + 17 条断言 + R-B 判定程序）、`W41_csf_install\ra2forge_patched_v12\`（当前最高包，回归 57/57，Lead 复跑）。
> 新包：`W43_b_line_s3\ra2forge_patched_v13\`（自 v12 派生）。

---

## 0 · 结论分级与红线

| 标记 | 本卡口径 |
|---|---|
| `[本次实测]` | 本卡亲自运行的脚本/命令直接取得（回归 82/82、SHA-256 对照表、stdout / exit code、git scoped 快照、进程数、源文件 delta） |
| `[本次读码]` | 逐行读 v12 的 `cli.py` / `builder.py` / `csf.py` / `install.py` / `mapselmd.py` + W38/W42 契约原文得到的代码事实 |
| `[静态推断]` | 由多项读码/实测事实组合推出的规范与工程判定 |
| `[转引]` | 来自 W36 / W38 / W40 / W42 / FINAL_RULING / Lead 裁决的既有结论，本卡未独立复算 |
| `[待运行验证]` | 须真机/实算才能定谳；本卡未做 |

**红线**

1. **本卡不得写「B 线已完成」或「守卫已具备」**。本卡交付的是**离线实现 + 离线回归**：`resolve()`、csf 完整性门禁、G3 警告通道、版本守卫接线（**opt-in**）、`TRACK_B_gates.json` 各自在离线夹具下可机检通过；它们不等于真机行为正确，也不等于守卫在所有部署中已默认启用。
2. **不得把回归全绿写成行为正确**。`82/82 PASS` 只证明文件层计划/守卫/兼容行为在离线夹具下符合断言；沙箱内 `gamemd.exe` 是 inert 占位（W34 `UNCOVERED.md` U9 `[转引]`），从不执行。
3. 与 W38/W42 契约冲突处逐条登记在 `DISAGREE.md`，取舍遵守 Lead 的 4 项裁决。
4. 「契约完备 ≠ 能力已具备」的旧口径在本卡转为：「离线实现完备 ≠ 真机行为已验证」。

---

## 1 · 总体形态（[本次实测] + [本次读码]）

`ra2forge_patched_v13/` = `ra2forge_patched_v12/` 的**最小增量派生**：

| 类别 | 文件 | 说明 |
|---|---|---|
| **修改（4）** | `ra2forge/builder.py` | 仅改 `_csf_out_ownership_guard` 的错误理由串（W29 启动失败 → W40 UI `MISSING:'…'`）；默认构建产物零改动 |
| | `ra2forge/cli.py` | 新增 4 个 opt-in 开关 + `resolve` / `guard-check` 两个子命令 + E2b→E1 预检；所有 legacy 分支默认路径不变 |
| | `ra2forge/csf.py` | 改 `assert_complete_csf` 理由串（保留 `PARTIAL` 关键字以兼容 57 例）+ 封死 `append_or_set_label(create_if_missing=True)` 造最小 CSF 的真实缺口 |
| | `ra2forge/install.py` | 新增 `_s3_guard_gate`（E1/E3 接线）与 `install_package/uninstall` 的 opt-in `version_guard` 形参 + 修正 `CSF_NAME` 注释中的错误理由 |
| **新增（5）** | `ra2forge/s3_contract.py` | 裁决常量、E1 修订允许清单、K1–K12、WRITE_ENTRY_AUDIT HIGH/CRITICAL 覆盖表 |
| | `ra2forge/version_guard.py` | W38-S1 `classify()` 实现 + 决策表门禁 + `guard_report.json` + 退出码 20/21/22/23 |
| | `ra2forge/feature_subset.py` | W42-S2 `resolve()` 实现（本次首个） |
| | `ra2forge/data/E1_KNOWN_GOOD.json` | D1 修订后的 E1 允许清单（运行时可读） |
| | `ra2forge/data/guard_decision_table.json` | D1 同步后的 21 格决策表（运行时可读） |

`out/V13_SOURCE_DELTA.json` 是上述 delta 的机检副本（`[本次实测]`）。

**向后兼容（硬证据）**：`out/SHA256_COMPAT_V13_V12.txt` 对**同一 design、不启用任何新开关**的 v12 / v13 构建产物逐一给出 SHA-256：

```
files: 8  identical: 8  different: 0
VERDICT: IDENTICAL
```

8 个产物：`BATTLEMD98.INI` / `BUILD_REPORT.txt` / `CP1.MAP` / `CP2.MAP` / `INSTALL.txt` / `expandmd98.mix` / `ra2forge_package.json` / `story.md`。另有 `out/SHA256_COMPAT.txt`（继承的 CSF_INST5，v13 vs v11 只读参考，同样 MATCH）——两张表互为交叉印证。

**为什么所有新能力必须 opt-in（关键设计取舍）** `[静态推断]`：W38-S1 §3 步骤 2 规定「无已定谳 `BASELINE.json` ⇒ `UNKNOWN` + `NO_ADJUDICATED_BASELINE`」，§4 规定 `UNKNOWN`/`MISMATCH` 下 `ALL_GAME_DIR_WRITES` 拒绝。若把守卫设为默认启用：① v12 的 57 例（沙箱 `gamemd.exe` 是 `INERT PLACEHOLDER - NEVER EXECUTED` 文本、非 PE）会全部落入拒绝；② 构建产物按 §4 E2a 会被要求打 `UNKNOWN` 标签 ⇒ 破坏「不启用新开关时逐字节相同」。故 S1 判据以 `--version-guard <fixture.json>` **显式接入**写入口，默认路径零改动。详见 `DISAGREE.md` D-W43-1、`UNCOVERED.md` U-W43-1。

---

## 2 · 五件事逐条落地

### D1 · 修订 S1 的 E1 允许清单，加入 `ra2md.csf`，同步 `guard_decision_table.json`

**落点（[本次实测]）**
- `s1_revision/E1_KNOWN_GOOD.json`：`allowed_targets_before = [*.MAP, BATTLEMD98.INI, MAPSELMD.INI, expandmd98.mix]`（4 类）→ `allowed_targets_after` 加入 `ra2md.csf`；`added: ["ra2md.csf"]`；`guard_shape: completeness_integrity_gate`；`not: [drop_ban, startup_failure_rule]`。
- `s1_revision/guard_decision_table.json`：W38 21 格决策表的**同步修订副本**。保持 `schema_version="w38-s1-1"`、`cells` 仍恰 21 格、其余 20 格与 W38 逐字节相同；仅在 `E1/KNOWN_GOOD` 的 `allow[]` 追加一个机检同步 token（`E1_KNOWN_GOOD.json` 的 `guard_decision_table_sync_token` 字段即该值），使「`ra2md.csf` 成为登记的 E1 目标」可被机检而不破坏 W38 的 `writeEntryPolicy.additionalProperties:false` schema。
- 两份修订副本同时写入 `ra2forge_patched_v13/ra2forge/data/`，供运行时消费（`S3_19h` 断言二者字节相同）。
- `APPLY.md` 给出相对路径补丁（对 `W38_version_guard_s1/VERSION_GUARD_CONTRACT.md §4 E1` 与 `W38_version_guard_s1/EVIDENCE/guard_decision_table.json`）+ 校验 + 回滚。**因纪律禁止改 W38 目录，修订以「同一补丁内的相对路径补丁 + 修订副本」交付，不就地改写 W38**；取舍见 `DISAGREE.md` D-W43-2。
- 运行时常量 `s3_contract.E1_KNOWN_GOOD_TARGETS` / `e1_target_allowed()`（`S3_19i`）。

**理由按裁决写（[转引·签发]）**：W40 A/E 双证散装 `ra2md.csf` 覆盖 `langmd.mix` 内同名文件且值驱动 UI 渲染；W40 A 证「合法即启动」（115 B 最小 CSF 19.34 s 正常进主菜单）；W40 D 证「只有坏魔数」才 `Unable to initialize 'ra2.csf'` 且不启动 ⇒ 守卫正确形态是**完整性门禁**而非禁止投放；W41 v12 回归 57/57（Lead 复跑）。**理由中不含「最小 CSF 会启动失败」**。

**附带落实**：csf 投放带完整性门禁（见 §2.2），门禁理由已按 D1 改对，并把 v12 三处错误的旧理由串（`csf.py` `assert_complete_csf`、`builder.py` `_csf_out_ownership_guard`、`install.py` `CSF_NAME` 注释）全部改正。

### D2 · csf 完整性门禁（拒绝「只含我方标签」的最小 CSF，对应 B8）

**门禁理由（正确）**：防「官方 UI 文本全变 `MISSING:'…'`」的**可用性灾难**；**不是**「防启动失败」。W40 A 最小 CSF 正常启动、W40 D 只有坏魔数才不启动。常量 `s3_contract.CSF_INTEGRITY_GATE_REASON` 明写此取舍，`S3_20d/e/f` 机检。

**四层门禁（[本次读码] + [本次实测]）**

| 层 | 位置 | 行为 |
|---|---|---|
| resolve 层（B8 / K4） | `feature_subset.resolve()` | `csf.base != "official_full_clone"` 或 `official_label_count < official_full_min(5211)` ⇒ `coupling_passed=false` + `MINIMAL_CSF_REFUSED` + 零写；detail 点名 `official_full_clone` / 5211 / 正确理由 |
| 原语层（**真实缺口封堵**） | `csf.append_or_set_label()` | `create_if_missing=True` 且目标不存在 ⇒ 抛 `CsfIncompleteError`（`MINIMAL_CSF_REFUSED` + 正确理由），**零字节**；v12 会从零造 1 标签最小 CSF。`S3_9` 用 v12（只读参考）与 v13 对拍证明 |
| 产物写入层 | `csf.assert_complete_csf()` / `write_csf(require_complete=True)` | v12 已有，本卡改正错误理由串并保留 `PARTIAL` 关键字（兼容 CSF_INST1c） |
| 构建层 | `builder._emit_csf_artifacts()` | v12 已全部走 `require_complete=True`，本卡未改其门禁结构，仅改 `_csf_out_ownership_guard` 错误理由 |

> `[本次读码]`：v12 **已**有 `assert_complete_csf` 与 `require_complete`；W42 签发 §3 事实 1 所说「v11 无完整克隆门禁」对 v11 成立，对 v12 不成立。**真实仍开的缺口**是低层原语 `append_or_set_label(create_if_missing=True, require_complete=False)` 仍能从零造最小 CSF；本卡封死它，且 57 例无一依赖该组合（`regress_dlc_v13.py` 全文 grep `create_if_missing` 仅出现在负例注释与 `S3_9`）。此差异如实登记于 `DISAGREE.md` D-W43-3。

### D3 · `resolve()` 实现（消费 S2 feature-set → 确定性文件子集）

**落点**：`ra2forge/feature_subset.py`（`resolve()` / `shipped()` / `validate_g4()` / `build_plan_from_files()`），CLI 子命令 `python -m ra2forge resolve --feature-set F.json --sandbox S.json`（stdout 纯 JSON，可机检）。

- `shipped(F)` 是纯函数（§3.2）；`FILE_UNIVERSE(F)` 穷举 5 个固定游戏目录候选 + 逐个 `maps.map_files[i]` + 清单/seal 两行元数据。
- `action()`：CREATE（ABSENT，`original_absent=true`，卸载 **DELETE**）/ REPLACE（PRESENT，建 `.ra2forge.bak`，卸载 **RESTORE**）/ **LEAVE**（严格零写、不备份、不删、**不 adopt**；与 v11 `action="unchanged"` 的 adopt 语义不同，`install.py:1290-1301` `[本次读码]`）。
- 四个集合（`install_write_set` / `backup_set` / `uninstall_delete_set` / `uninstall_restore_set`）**由 `files[]` 派生**，不得手填；`validate_g4()` 检测 `G4_METADATA_DESYNC`（B16）。
- `guard_state` 由夹具注入、完全不由 feature-set 决定（§6 C1）；`UNKNOWN`/`MISMATCH`/`DIR_INVALID` ⇒ `wrote_game_dir=false`、`effective_game_dir_write_bytes=0`，但 `files[]` 计划集合完整保留供 `guard_report.json`（B14）。
- 输出是 S2 `$defs/fileSubsetPlan` 的**超集**：新增 `warnings[]` / `install_summary[]` / `reason_codes[]` / `manifest{}` 等（D3 要求 `warnings[]`，而 S2 schema 未含该字段且 `additionalProperties:false`）。**不改 S2 上游 schema**，扩展登记于 `DISAGREE.md` D-W43-4。
- **三个题面负例全部被拒（[本次实测] S3_8/S3_10/S3_11）**：B8 `MINIMAL_CSF_REFUSED`、B9 `MAPSELMD_NOT_FULL_CLONE`、B10 `CSF_WITHOUT_BATTLEMD` / `CSF_LABEL_UNBOUND`×2；均 `coupling_passed=false` + `install_write_set=[]` + `effective_game_dir_write_bytes=0` + `guard_state` 不变。

### D4 · G3 警告通道（csf + MAPSELMD 开、BATTLEMD98.INI 显式关闭）

**落点**：`feature_subset.resolve()` 的 `warnings[]` + `install_summary[]`（`s3_contract.G3_WARNING_CODE = "G3_MID_COUPLING_NOTICE"`）。

- 触发条件 `[静态推断]`：`csf.mode == clone_append` ∧ `mapselmd.mode == clone_append` ∧ `"BATTLEMD98.INI" ∉ shipped(F)`（即 `battlemd.mode != "append"`，文件被显式关闭/改投 `BATTLEMD.INI`）。
- 警告对象：`{code, severity:"warning", machine_checkable:true, hard_reject:false, features, missing_file, message, verdict}`；`message` 点名「没有 `BATTLEMD98.INI` 指向 A1，`MAPSELMD` 推进无从触发」。
- **不做硬拒绝**：`warnings[]` 独立通道，不写 `coupling_violations[]`、不置 `coupling_passed=false`。`S3_21` 用一个**通过**的规划夹具（`battlemd.mode="inplace"` + `description_ref="csf_label"`，K2/K3 强耦合满足）证明 `coupling_passed=true` 且警告可见于安装摘要；另用字面 `battlemd.mode="off"` 证明警告仍机检可见。
- 三对强耦合（CSF↔`BATTLEMD98.INI`、地图↔MIX、地图↔`MAPSELMD`）**保留硬拒绝**（`S3_21h` 对 W42 `coupling_rules.json` 的 K2/K6–K10 机检）。
- 与 S2 `B10a`/K2 在 `battlemd=off` 时的张力如实登记于 `DISAGREE.md` D-W43-5。

### D5 · `TRACK_B_gates.json` 独立工件

**落点**：`W43_b_line_s3/TRACK_B_gates.json`（生成器 `EVIDENCE/gen_s3_artifacts.py`，stdout + exit 已留档）。

- `adjudicated: true`（R-B 轨的 G1–G6 判定程序已执行并登记）但 **`is_clean_retail_gold: false`**（硬约束）。
- `baseline_json_schema_extended: false` / `baseline_json_entry_added: false` ⇒ **未扩 `BASELINE.json` schema**；W38-S1 `provenance.is_clean_retail_gold: const false` 保持（`S3_22k` 对只读 W38 schema 机检）。
- 写清「由哪份物理副本」（`physical_copy`：账面 C01/C02/C08/C07 值 + `abs_path_binding_required` + 多副本歧义约束，全部标 `[转引]`，本卡**未实算任何真实游戏二进制哈希**）与「哪条程序」（`procedure.track="R-B"`，P0–P6 逐步 status，`source = W42_b_line_s2/BASELINE_ADJUDICATION.md §2/§3/§4`）。
- `gates` 恰 G1–G6，全部 `UNKNOWN`（G1 外部零售介质本卡无、纯离线），`overall_verdict="UNDETERMINED"`、`retail_oracle_eligible=false` ⇒ 不写「是金标准」。
- D2 附带：`detour_classification.default/applied_value = "westwood_native"`，`.detour` `Characteristics=0xC0000040` **无执行位**，D1–D5 字节判据照留，且明确「原生 ≠ 干净零售金标准」。

---

## 3 · 还要做的事（逐条）

### 3.1 版本守卫接线（[本次实测] S3_23 / S3_24）

| 项 | 落点 | 结果 |
|---|---|---|
| `install` 的 `gamemd.exe` 检查**升级为身份判定** | `install.py:install_package()` 首行 `_s3_guard_gate("E1", game, version_guard)`；`version_guard.classify()` 实现 W38-S1 §3（L0 C06/C13 → L1 C01/C02/C04/C08/C13 全字段精确相等 → `KNOWN_GOOD`/`UNKNOWN`/`MISMATCH`/`DIR_INVALID`） | `UNKNOWN` ⇒ exit 20 零写；`MISMATCH` + `TEXT_SHA_MISMATCH` ⇒ exit 21 零写；`CRITERION_MISSING`（C02/C04 不可读）⇒ 不得沉默放行；`KNOWN_GOOD` ⇒ 放行（`S3_23l`） |
| `uninstall` 补守卫 | `install.py:uninstall()` 首行 `_s3_guard_gate("E3", ...)`（v12 只有 `game.is_dir()`） | `S3_23k`：exit 20、零写 |
| 退出码 | `20/21/22/23`（W38-S1 R11，与 v12 的 0–10 不冲突） | `S3_23` |
| `--force-unknown` | 只读降级专用（R5），写入 `guard_report.json` 的 `force_unknown_used` + `FORCE_UNKNOWN_READONLY_ONLY`，**不得放行写入** | `S3_23i/j` |
| `guard_report.json` | 落在 `--guard-report` 指定路径（本卡沙箱，**不在游戏目录**），`wrote_game_dir:false`（§6.1 不变式 7） | `S3_23c/d/g/j/m` |
| 每次重算（R9） | `classify()` 无缓存，每次 `guard_write_entry()` 重新 `collect_l0/collect_l1` + 新 `observed_at` | 代码结构；`S3_23` 连续 5 次调用各自产生新报告 |
| **HIGH/CRITICAL 覆盖** | `s3_contract.WRITE_ENTRY_COVERAGE`：E1（39 行，含 `install.py:1140-1143` / `1955-1981` / `2045-2047` / `builder.py:434-437` / `csf.py:410-475`）、E3（16 行，含 `install.py:2184` / `2340` / `2474` / `_uninstall_legacy` 全部）、E2b→E1（9 行，含 `cli.py:140-146`）；合计 **64 行** | `S3_23o` 机检 `rows>=50` 且三组齐全 |
| 未覆盖 | `ra2opt` XCHAIN 10 行（独立包、不在 v13 内）显式列为 `XCHAIN_ROWS_OUT_OF_SCOPE`，不隐藏 | `S3_23p`；`UNCOVERED.md` U-W43-3 |

`[静态推断]`：在两个**顶层入口函数**设门禁即可覆盖审计表全部 HIGH/CRITICAL 后代行，因为 `_stage_and_replace` / `_stage_text_and_replace` / `_write_step` / `_rollback` / `_execute_orphan_plan` / `_uninstall_legacy` 都是仅从这两个函数可达的私有辅助（`WRITE_ENTRY_AUDIT.tsv` `[CALLER]` 行印证）。

### 3.2 `--csf-out` 路径归属守卫（[本次实测] S3_24）

- v12 已有 `_csf_out_ownership_guard`（默认拒绝 + `--allow-csf-out-in-game` 显式放行 + 目标身份检查），本卡**保留其行为**，仅修正错误理由（`S3_24a/b/c`）。
- S3 追加：`cli._s3_precheck_csf_out()` 在 `--version-guard` 启用时，对 `realpath` + `commonpath` 落在游戏目录内的 `csf_out` **改贴 `E1`**（`entry_id="E2b->E1"`，W38-S1 §1.2 / A7 / K12），先跑 S1 身份判定再允许写；`UNKNOWN` ⇒ exit 20、`guard_report.json` 记 `E2b->E1` + `wrote_game_dir:false`、游戏目录零写、连包输出目录都不创建（`S3_24e/f/g`）。
- resolve 层 B15 对应：`files[]` 中该写点 `write_entry="E1"`，`reason_codes` 含 `CSF_OUT_INSIDE_GAME_DIR_DEFERRED_TO_S1`，`S3_16` 机检。

### 3.3 回归（[本次实测]）

命令：`python -B -X utf8 regress_dlc_v13.py`（工作目录 `W43_b_line_s3`）

```
cases: 82  passed: 82  failed: 0
assertions: 714 passed / 0 failed
exit: 0
inherited v12 cases: 57
S3 cases: 25
```

- **57 例逐例保留**（`CASES` 字典原样，`P0/V1-6/P1-4/C1-2/T4/S1-8/F0-7/U1-6/R0-2/CSF1-6/MS1-6/CSF_INST1-6` 全部对 v13 重跑通过）。
- **17 条 S2 断言的可机检部分**：`S3_1`…`S3_18` 一一对应 B1–B17（B17 为契约形状自检；另 `S3_18i/j` 验证 `resolve` CLI 子命令）。
- 其余 `S3_19`–`S3_25` 覆盖 D1/D2/D3/D4、版本守卫接线、csf-out 归属、v13↔v12 SHA-256 兼容。
- 逐例日志：`out/<case>.log`（命令 + 原始 stdout/stderr + exit code + 逐项判据）；汇总 `out/SUMMARY.txt`；`out/SHA256_COMPAT.txt` + `out/SHA256_COMPAT_V13_V12.txt`；`out/V13_SOURCE_DELTA.json`。
- `EVIDENCE/regress_full.stdout.txt` + `EVIDENCE/regress_full.exit.txt`。

**不得把 82/82 写成行为正确**：这些是文件层/计划层/离线夹具层断言；真机引擎是否采用散装 `ra2md.csf` / `MAPSELMD.INI` 至今 `[待运行验证]`（W30/W34 `UNCOVERED.md` `[转引]`）。

### 3.4 向后兼容（[本次实测]）

`out/SHA256_COMPAT_V13_V12.txt`：8 个产物 **8/8 MATCH / VERDICT: IDENTICAL**（SHA-256 全文见该文件）。`S3_25c` 另证两侧均不产出 `ra2md.csf` / `MAPSELMD.INI`（开关关闭）。源文件 delta 仅 4 改 + 5 增、无删除（`S3_25f/g`）。

---

## 4 · 与 S1 / S2 契约的对应表

| S1 锚点（W38） | 本卡落点 | 机检用例 |
|---|---|---|
| §1.2 写入口 E1–E6 / 路径归属规则 | `_s3_precheck_csf_out` E2b→E1；`WRITE_ENTRY_COVERAGE` | S3_16 / S3_24 / S3_23o |
| §2 C01/C02/C04/C08/C13 判据 | `version_guard._pe_l1()` 固定 PE 口径 + `collect_l0/l1`；夹具可注入 evidence | S3_23 |
| §3 `classify()` 步骤 0–5 | `version_guard.classify()` | S3_23a/l、S3_20 |
| §4 三态×7 入口决策表 / 跨态不变式 | `s1_revision/guard_decision_table.json`（21 格，D1 同步）；`guard_write_entry()` | S3_19e/f/g、S3_15 |
| §5 R1/R3/R5/R9/R11 | R1 全判据、R3 零写、R5 `--force-unknown` 只读、R9 每次重算、R11 退出码 20/21 | S3_23 |
| §6.1 `guardVerdict` / `guardReport` schema | `version_guard._verdict()` / `guard_report.json` | S3_23c/d/g/j/m |
| `ACCEPTANCE.md` A1/A2/A3/A7 | S3_23（MISMATCH/UNKNOWN/force）、S3_24（A7） | 同上 |
| `WRITE_ENTRY_AUDIT.tsv` HIGH/CRITICAL 64 行 | `s3_contract.WRITE_ENTRY_COVERAGE` | S3_23o |
| **S1 §4 E1 允许清单（修订）** | `s1_revision/E1_KNOWN_GOOD.json` + 同步决策表 | S3_19 |

| S2 锚点（W42） | 本卡落点 | 机检用例 |
|---|---|---|
| §2 featureSet / schema（只读） | `resolve()` 直接消费 `EVIDENCE/fixtures.json`；S3 输出为 schema 超集 | S3_1–S3_18、S3_18b–g |
| §3.2 `shipped(F)` 纯函数 | `feature_subset.shipped()` | S3_2/S3_5/S3_7 |
| §3.3 CREATE/REPLACE/LEAVE + `original_absent` | `resolve()` 的 `files[]` | S3_1/S3_2/S3_3/S3_4 |
| §3.4 耦合拒绝先于写 | `resolve()` 在拒绝时 `install_write_set=[]`、bytes=0 | S3_8/S3_10/S3_11 |
| §4.2 四集合由 `files[]` 派生 | `build_plan_from_files()` + `validate_g4()` | S3_2/S3_7/S3_17 |
| §4.3 写点标签 E1/E2b | `write_entry` 字段；B15 改贴 E1 | S3_16 |
| §5 K1–K12 | `_check_coupling()` 全 12 条 | S3_8/S3_10–S3_14/S3_16/S3_17 |
| §6 C1–C7 组合规则 | `guard_state` 注入且不被 S2 改变；非 KNOWN_GOOD 零写 | S3_15/S3_16 |
| §7 G4 全局事务公式 | `digest_inputs` / `manifest.package_digest` / `feature_set_id` / `validate_g4()` | S3_17 |
| `ACCEPTANCE_S2.md` B1–B17 | `S3_1`…`S3_18` | 见 §3.3 |
| `BASELINE_ADJUDICATION.md` R-B P0–P6 / G1–G6 | `TRACK_B_gates.json` | S3_22 |

---

## 5 · 差距表：仍有哪些没做（**必须保留**）

> 本卡是「实现 + 离线回归」，以下均**未达成 / 未验证**。不得据 82/82 推断它们已完成。

| # | 差距 | 状态 | 归属 |
|---|---|---|---|
| G-1 | **真机行为等价性**：散装 `ra2md.csf` / `MAPSELMD.INI` 是否被引擎采用、官方 UI 是否真的显示我方文本、战役推进是否真触发 | `[待运行验证]`，本卡纯离线、未启动游戏 | S4/S5 |
| G-2 | **版本守卫默认未启用**：S1 判据已接线但需 `--version-guard` 显式开启；无已定谳 `BASELINE.json` 时若默认启用会拒绝一切安装 | 已实现为 opt-in，取舍见 `DISAGREE.md` D-W43-1 | S4 + Lead 签发 `BASELINE.json` |
| G-3 | **`BASELINE.json` 实算 / Track A 签发**：W42 `BASELINE_ADJUDICATION.md` 的 P0–P5 未执行，本卡未计算任何真实游戏二进制哈希 | 未做；仅产出 R-B 独立工件 | Lead 另立卡 |
| G-4 | **C07/C09/C10/C11/C12 L2/L3 判据与原始字节窗口**：`classify()` 只实现 L0+L1（C01/C02/C04/C08/C13 + C06）；ddraw/MIX 条目/组件集合/写前 N 字节窗口未接入运行时 | 未做 | S4 |
| G-5 | **ra2opt XCHAIN 写入口**：`optimize.apply()` / `backup.restore()` / `safewrite` / `cddraw` / `pe` / `appcompat` 等 10 行未接线（独立包，不在 v13 内） | 显式列为 `XCHAIN_ROWS_OUT_OF_SCOPE` | 另卡 |
| G-6 | **E4（`verify --fix` / seal 自愈）**：v12/v13 `verify` 仍严格只读；E4 一旦实现须按 §4 重新注册写入口 | 未做 | 另卡 |
| G-7 | **`resolve()` 与实际 install/builder 的端到端串接**：本卡 `resolve()` 产出计划并可机检，但**未**把计划集合回灌到 `package_files()` / 安装事务 / 清单 / seal / 卸载；二者仍是并列能力 | 未做（本卡范围仅「实现 resolve()」） | S4 |
| G-8 | **二次安装 / 升级 / orphan / legacy 的子集联动**：S2 §3.3 边界 3 明确移交 S3，但本卡 `resolve()` 只规约首次安装 + 卸载往返 | 未做 | S4 |
| G-9 | **`battlemd:inplace` 真机实现/回滚**：仅在纯规划层作为夹具使用（不写真实文件）；S2 §4.1 F5 注明需 Lead 定谳 | 未做 | Lead + S4 |
| G-10 | **安装/卸载内容级校验**：MAPSELMD/CSF 的 verify 内容级校验（W34 U7 `[转引]`）仍缺 | 未做 | S4 |
| G-11 | **退出码 20/21/22/23 与 v12 现有 CLI 的完整集成审计**：本卡仅在新 opt-in 分支使用；`--force` / `--allow-content-conflict` / `--adopt-legacy` / `--legacy` 不改变 `guard_state` 的**全组合**未逐一实测（仅文档与部分用例） | 部分验证 | S4 |
| G-12 | **多副本 / `.detour` 字节判据 D1–D5 实算**：本卡保留程序、默认 `westwood_native`，但未实算任何副本字节 | 未做（程序已在 `TRACK_B_gates.json` 登记） | Lead |
| G-13 | **S1 修订合入 W38 目录**：因纪律禁止改 W21–W42，修订以相对路径补丁 + 副本交付，尚未就地应用到 `W38_version_guard_s1/` | 未做（待 Lead 决定是否合入） | Lead |

**结论口径**：B 线到本卡为止新增了「离线可机检的实现与回归」，**不是**「B 线已完成」，**不是**「守卫已具备」，**不是**「回归全绿 ⇒ 行为正确」。

---

## 6 · 纪律复核（[本次实测]）

- 纯离线：`gamemd.exe`/`game.exe` 进程数 **0**（`EVIDENCE/game_proc.txt`）；未 attach；沙箱内 `gamemd.exe` 仅 inert 文本占位。
- 未写 `ra2youli/`（仅 `READ` 其 `ra2forge_install.json` 到沙箱，与 v12 回归一致）、未改仓库 `ra2forge/`、未动 `W21`–`W42`（scoped `git status --porcelain` 仅显示开工前既有的 `??` 行，无 ` M`，见 `EVIDENCE/git_scoped_after.txt`）、`git` 全程只读。
- 唯一写域：`lead\next_re_20261112_r02\W43_b_line_s3\`。
- 分级：全文按 §0 口径标注；5,211 标签 / 5,573 B / `074ccccd…` / `db264305…` 等均按来源标 `[转引]`。
- 冲突取舍：`DISAGREE.md`；未覆盖与不确定项：`UNCOVERED.md`；补丁/校验/回滚：`APPLY.md`；证据：`EVIDENCE\`（脚本 + stdout + exit code）。
