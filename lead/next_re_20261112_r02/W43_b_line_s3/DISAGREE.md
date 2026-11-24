# DISAGREE.md · W43 / S3 与 W38 / W42 契约的冲突与取舍

> **总原则**：Lead 的 4 项裁决（`REVIEW\LEAD_DECISIONS_W42.md` D1–D4）**全部遵守**；以下条目只登记「契约字面 / 内部两处表述 / 交付形态」与本卡实现之间的张力，并写明取舍依据。**不翻案、不改上游文件、不扩 `BASELINE.json` schema**。
> 分级同 `S3_IMPLEMENTATION.md §0`。

---

## D-W43-1 · 「版本守卫接线」与「默认零改动 / 57 例保留」的冲突（最重要）

**冲突**
- W38-S1 §3 步骤 2：`BASELINE.json` 无 `adjudicated=true` 条目 ⇒ `UNKNOWN` + `NO_ADJUDICATED_BASELINE`；§4：`UNKNOWN`/`MISMATCH` 下 E1/E2b(游戏目录)/E3/E4/E6 一律 `ALL_GAME_DIR_WRITES` 拒绝、零写入；§4 E2a 还要求 `UNKNOWN` 产物打标签。
- W43 任务卡要求：「把 S1 的判据接到实际写入口」**且**「不启用新开关时，构建产物与 v12 逐字节相同」**且**「保留 v12 的 57 例」。
- `[本次读码]`：57 例的沙箱 `gamemd.exe` = `INERT PLACEHOLDER - NEVER EXECUTED\n`（`make_golden()`，见 `regress_dlc_v13.py`），不是 PE；`collect_l1()` 会判 C02/C04 不可读 ⇒ `UNKNOWN`。若守卫默认启用，57 例的每一次 install/uninstall 都会被拒绝，且 `BUILD_REPORT.txt` 需加 `UNKNOWN` 标签 ⇒ 逐字节兼容不成立。

**取舍（[静态推断]）**：把 S1 判据**接线**到真实写入口，但做成 **opt-in**（`--version-guard <fixture.json>`）——默认路径与 v12 完全一致（8/8 SHA-256 MATCH、57/57 通过）。理由：
1. 任务卡要的是「判据接到入口」，不是「改变默认行为」；后者会直接违反同卡的两条硬要求。
2. W38-S1 自己也规定 `BASELINE.json` 须由 **Lead 定谳后**才可写入、未定谳前 `guard_state` 应落 `UNKNOWN`（`BASELINE_ADJUDICATION.md §4` `[转引]`）。在 Lead 未签发基线的盘面上把守卫设成默认拒绝，等于把整个工具变成不可安装。
3. Lead 的 4 项裁决均未要求「默认启用」。

**代价（如实登记）**：默认部署下守卫**未启用**；`UNCOVERED.md` U-W43-1、`S3_IMPLEMENTATION.md` 差距表 G-2 明写。本卡**不写「守卫已具备」**。

---

## D-W43-2 · D1「在同一补丁内修订 S1」与「不动 W21–W42」纪律的冲突

**冲突**
- Lead D1 + `LEAD_SIGNOFF_BATCH_W38_W41_W42.md §2` 改动授权：「S3 在**同一个补丁内**修订 S1 的 `E1 KNOWN_GOOD` 允许清单，并同步 `guard_decision_table.json`」。
- 本卡纪律：「不动 `W21`–`W42`」「只写 `W43_b_line_s3\`」。W38 的 `VERSION_GUARD_CONTRACT.md` 与 `EVIDENCE/guard_decision_table.json` 都在 W38 目录内，不能就地改写。

**取舍**：修订以**同一交付包内的相对路径补丁 + 修订副本**形式提交：
- `s1_revision/E1_KNOWN_GOOD.json`（修订后的允许清单，`added:["ra2md.csf"]`）
- `s1_revision/guard_decision_table.json`（21 格同步副本，仅 E1/KNOWN_GOOD `allow[]` 加同步 token）
- `APPLY.md` 给出对 `W38_version_guard_s1/VERSION_GUARD_CONTRACT.md §4 E1` 与 `EVIDENCE/guard_decision_table.json` 的**精确相对路径补丁**（含校验与回滚），由 Lead 决定是否合入。
- 同时把两份副本写入 `ra2forge_patched_v13/ra2forge/data/`，使 v13 **运行时实际消费**修订结果（`S3_19h` 机检字节相同）。

**未做**：未就地修改 W38 任何文件（差距表 G-13）。这不违背 D1 的实质（允许清单已修订、决策表已同步、同一补丁内交付），但**交付形态**与「直接改 S1 文件」的字面不同，故登记。

---

## D-W43-3 · 「v11/v12 会造最小 CSF」与 v12 已有完整性门禁的口径差

**冲突**
- W42 签发 §3 事实 1 / W43 任务卡：`append_or_set_label(create_if_missing=True)`（`csf.py:442-466`）+ `builder.py:431-437` **会生成只含我方标签的最小 CSF**，是「真实缺口」，且「v11 无完整克隆门禁、5211 常量 grep 零命中」。
- `[本次读码]`：**v12（W41）已新增** `csf.assert_complete_csf()`、`write_csf(require_complete=True)`、`append_or_set_label(require_complete=True)`，`builder._emit_csf_artifacts()` 生产路径全部走 `require_complete=True`；`OFFICIAL_CSF_LABEL_COUNT = 5211` 常量存在；Lead 签发 §1 也确认「v12 完整性门禁」成立。所以「v11 现状」对 v12 **不成立**。

**取舍**：
1. 不否认 W42/任务卡的结论，但把「缺口」精确定位为**低层原语**：`append_or_set_label(create_if_missing=True, require_complete=False)` 在目标缺失时仍能从零造 1 标签最小 CSF；这是 v12 与 v11 共同保留的真实缺口。本卡在 `csf.py` 中封死它（`S3_9` 用 v12 只读参考与 v13 对拍证明），并在 `resolve()` 的 K4 层做 B8 门禁。
2. **不改** `append_or_set_label` 的默认语义（W30 的 CSF1–6 低层单元用例故意构造最小 CSF，`create_if_missing` 默认 False、无一依赖 True），以保住 57 例。
3. v12 三处**错误理由**（`csf.py:700-703`「game refuses to start」、`builder.py:479-480`「break game startup」、`install.py:386-388` 注释）按 D1 全部改正为「官方 UI 文本全变 `MISSING:'…'`」；`assert_complete_csf` 保留 `PARTIAL` 关键字以兼容 `CSF_INST1c`。

这属于「按实际语义重述」：Lead 在 `LEAD_SIGNOFF_BATCH... §1` 已预告「W41 交付文档里若沿用旧理由，后续引用时按本条改口」。

---

## D-W43-4 · `resolve()` 输出形状必须扩展 S2 的 `fileSubsetPlan` schema

**冲突**
- W42 `FEATURE_SUBSET.schema.json` 的 `$defs/fileSubsetPlan` 是 `additionalProperties:false`，**不含 `warnings[]`**；其 `oneOf` 只允许 5 类实例。
- Lead D3 硬性要求「输出一条**可机检的 warning（进 `warnings[]`）**，并在安装摘要里可见」；B16 要求 `feature_set_id` 写进 manifest；B14 要求 `files[]` 计划保留。
- 契约本身 §6 C2 也说 `fileSubsetPlan` 同时带 `guard_state` 和 `coupling_violations`，但 schema 未给 `warnings`。

**取舍**：`resolve()` 输出为 **`fileSubsetPlan` 的严格超集**，新增 `warnings[]` / `install_summary[]` / `reason_codes[]` / `deferred_to_s1_reason_codes[]` / `manifest{}` / `effective_install_write_set[]` / `shipped[]` / `guard_state_unchanged_by_s2` / `detour_classification`。所有 S2 必需字段保持原名原类型不变（B1–B7、B14 的机检断言直接读这些字段）。**不修改 W42 的只读 schema**（纪律禁止 + 无授权扩展），也不把输出伪装成 schema 实例。

若后续要恢复「输出严格通过 S2 schema 校验」，须由 Lead 授权在 S2 schema 增加 `warnings` 等字段；本卡只登记，不擅自扩上游 schema。

---

## D-W43-5 · W42 内部 K12 语义矛盾 + D3 与 B10a/K2 的重叠

### (a) K12：`REJECT_AND_EXPLAIN` vs「交给 S1，不自行放行」

- `EVIDENCE/coupling_rules.json` 的 K12 写 `on_violation: "REJECT_AND_EXPLAIN"`，`reason_code: CSF_OUT_INSIDE_GAME_DIR_DEFERRED_TO_S1`。
- 但 `FEATURE_SUBSET_CONTRACT.md §4.3` 写「本卡**不改写 S1 结论**，只给出 reason code 表明『交给 S1 判』」、§6 C5 写「K12 只做『交给 S1』，**不自行放行**」、`ACCEPTANCE_S2.md B15` 期望 F2 计划集合照常产出、仅 `guard_state` 主导零写。

**取舍**：按 §4.3 / §6 C5 / B15 实现为 **DEFER_TO_S1**：`files[]` 中该写点 `write_entry="E1"`、`reason_codes` 与 `deferred_to_s1_reason_codes` 都记该码，**不置 `coupling_passed=false`**（不新增耦合违规），零写由 `guard_state=UNKNOWN` 的 S1 决策表产生。`S3_16f` 机检「K12 不在 `coupling_violations` 中且 `coupling_passed=true`」。这与 K12 的 `on_violation` 字段字面不一致，如实登记。

### (b) D3 警告条件与 S2 K2/B10a 强耦合硬拒绝的重叠

- Lead D3：「csf 与 `MAPSELMD` 同时开启、而 `BATTLEMD98.INI` 被显式关闭时」产出**警告，不做硬拒绝**；理由提到「只装 CSF 修文案」是合法用途。
- S2 `ACCEPTANCE_S2.md B10a` / K2：「`csf=clone_append` + `battlemd=off` ⇒ `CSF_WITHOUT_BATTLEMD` **硬拒绝**」；D3 自己又写「只有题面点名的 3 对强耦合（**CSF↔`BATTLEMD98.INI`**、地图↔MIX、地图↔`MAPSELMD`）保留硬拒绝」。

**取舍（遵守 D3）**：D3 的「不补硬拒绝」针对 **G3 中强度边（`csf × mapselmd`）**，而不是撤销既有强耦合 K2。故：
1. K2/K6–K10 三对强耦合**全部保留硬拒绝**（`S3_21h` 机检 W42 `coupling_rules.json`）。
2. G3 只走 `warnings[]`，**绝不**自行拒绝（`S3_21b/g`）。
3. 「`BATTLEMD98.INI` 被显式关闭」操作化为 **`"BATTLEMD98.INI" ∉ shipped(F)`**，即 `battlemd.mode ∈ {off, inplace}`。用一个 `battlemd.mode="inplace"` + `description_ref="csf_label"` 的**纯规划**夹具（K2/K3 满足）证明「警告 + 不硬拒绝」；字面 `battlemd.mode="off"` 时警告仍机检可见，K2 的独立硬拒绝照常触发（`S3_21i/j`）。
4. `battlemd:inplace` 仅用于**规划层夹具、不写真实文件**；S2 §4.1 F5 注明其实现/回滚需 Lead 定谳，本卡不越界（差距表 G-9）。

若 Lead 的本意是「`battlemd=off` 时连 K2 也不得硬拒绝」，则与 B10a 及 D3 自述的「3 对强耦合保留硬拒绝」直接冲突，需 Lead 二次裁决；本卡按「4 项裁决优先 + 不擅自撤销既有强耦合」处理。

---

## D-W43-6 · `FILE_UNIVERSE` 行数：B1 的「8 行」与 §4.2 的显式列表

- `ACCEPTANCE_S2.md B1` 写「`FILE_UNIVERSE` **8 行**全部 `L`」；`FEATURE_SUBSET_CONTRACT.md §4.2` 的显式列表为 `BATTLEMD98.INI, BATTLEMD.INI, <each maps.map_files[i]>, expandmd98.mix, ra2md.csf, MAPSELMD.INI, ra2forge_install.json, ra2forge_install.json.seal`——其中 `*.MAP` 是**变长**展开。
- 本卡按 §4.2 逐文件展开：`F0`（无 `map_files`）= **7 行**，`F1`–`F4`（2 个 `.MAP`）= **9 行**。`B2` 期望「`A.MAP/B.MAP` 各自为 `C`」也要求逐文件展开，与「8 行」不能同时成立（8 行更像把 `*.MAP` 当作 1 个 glob 行来数）。

**取舍**：按 §4.2 与 B2 的**逐文件**语义实现，`S3_1c`/`S3_2` 断言「全部行 LEAVE / 每个 `.MAP` 单独一行」而不硬编码 8。差异仅计数，不改变任何动作语义；如实登记，不改上游断言。

---

## D-W43-7 · `produced_by_feature` 对元数据行的取值

- `$defs/plannedFile` 要求 `produced_by_feature ∈ {maps,battlemd,mix,csf,mapselmd}` 且 `additionalProperties:false`；但清单 `ra2forge_install.json` / seal 属 `game_dir_metadata`，不由 5 个 feature 中任何一个产出。
- 本卡给元数据行填确定性哨兵 `"maps"`，并在 `feature_subset._owner()` 注释中说明。这是为满足只读 schema 形状的**折中**，不代表元数据归 `maps` 所有；元数据行由 `shipped(F)≠∅` 触发（`metadata(F)`，§3.2）。未改上游 schema。

---

## D-W43-8 · `original_absent` 对 LEAVE 行

- `$defs/plannedFile` 的 `original_absent` 描述写「true ⟺ 沙箱初始态没有该名字的原版」，按此描述，S0 中 ABSENT 的 `ra2md.csf`/`MAPSELMD.INI` 在 F0（全 `off`）下应记 `true`。
- 但 `ACCEPTANCE_S2.md B1` 明确要求 F0 下「8 行全部 `L`、**`original_absent=false`**」。
- 本卡按 **B1**（可机检断言）实现：`original_absent = (action == "CREATE")`，REPLACE/LEAVE 一律 `false`；schema 的 `allOf` 只约束 CREATE⇒true、REPLACE⇒false，对 LEAVE 无 `const` 约束，故不冲突。取舍登记备查。

---

## 汇总：4 项裁决遵守情况

| 裁决 | 遵守情况 |
|---|---|
| **D1** 修 S1 E1 允许清单 + 同步决策表 | ✅ `s1_revision/` + v13 data + `APPLY.md` 补丁；理由 4 条按 W40 A/E/A/D 写对；csf 门禁理由改对 |
| **D2** `.detour` = `westwood_native` | ✅ `s3_contract.DETOUR_CLASSIFICATION_DEFAULT`、`version_guard` verdict、`TRACK_B_gates.json` 三处一致；`0xC0000040` 无执行位如实记录 |
| **D3** G3 不补硬拒绝，改 `warnings[]` 警告 | ✅ 警告通道、`machine_checkable:true`、`hard_reject:false`、安装摘要可见；3 对强耦合保留硬拒绝 |
| **D4** 维持 `is_clean_retail_gold: const false`，第二轨放独立工件 | ✅ `TRACK_B_gates.json`：`adjudicated:true` / `is_clean_retail_gold:false` / `baseline_json_schema_extended:false`；W38 schema 未动 |
