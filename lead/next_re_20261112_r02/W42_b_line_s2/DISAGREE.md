# DISAGREE.md · W42 / S2 与 W36 / W38（及题面）的出入

> 卡：`W42_b_line_s2`｜纯离线只读｜2026-11-13
> 依据：`W36_b_line_kickoff\B_LINE_PLAN.md`（§3.3 / §4-S2）、`W36\DISAGREE.md` D1–D10、`W36\UNCOVERED.md` U1–U21、`W38_version_guard_s1\VERSION_GUARD_CONTRACT.md` / `DISAGREE.md` D-W38-1…11 / `UNCOVERED.md` U-W38-1…15 / `ACCEPTANCE.md` A1–A12、`FINAL_RULING.md` §5、`NEXT_RE_TASKS_20261112.md` L83-89、本卡 `EVIDENCE\`。
> 口径同 `FEATURE_SUBSET_CONTRACT.md` §0。**本卡不迁就前提**：逐条登记冲突、给「为什么未采纳原样」的理由、给后续卡应如何引用。
> **红线**：本卡未写「已实现能力」、未把「契约完备」写成「能力已具备」、未接线、未写生产代码。

---

## 1 · 与 W38-S1（直接上游契约）的冲突

| # | W38-S1 原样 | 本卡做法 | 是否采纳 | 为什么 / 后续怎么引用 |
|---|---|---|---|---|
| **D-W42-1** | §4 决策表 `E1` `KNOWN_GOOD` 行：`允许…**`*.MAP` / `BATTLEMD98.INI` / `MAPSELMD.INI` / `expandmd98.mix` 原子替换**…`；`拒绝：任何未登记目标文件` | S2 契约 §3.2 在 `csf.mode=clone_append` 时把 **`ra2md.csf`** 纳入 `shipped()` / 清单 / 备份 / 卸载 | **未采纳该枚举为封闭集**；**上报 Lead，属跨卡冲突** | `ra2md.csf` **不在** W38-S1 §4 E1 的 4 类允许清单里，按 `拒绝：任何未登记目标文件` 的字面会被拒。而 S2 直接卡把 `ra2md.csf` 列为 5 个改造面之一、且要求映射表覆盖「安装时写哪些、备份哪些、卸载时删哪些/还原哪些」。`[本次读码]` 复核 v11 `install.py:702-723` `package_files()` 确不含它（W30 `UNCOVERED.md` §2 / W38 G-4 `[转引]`）。**两卡对不上**：S2 契约要求投放的文件，在 S1 决策表字面下是「未登记目标」。本卡**无权改上游 S1**（纪律：不动 W38），因此：① 契约里把该冲突显式挂 `reason_code=CSF_OUT_INSIDE_GAME_DIR_DEFERRED_TO_S1` 之外的 K11/`G4_METADATA_DESYNC` 路径；② 在 `UNCOVERED.md` U-W42-1 列为 **Lead/S3 必须先消解的前置**——要么 S1 §4 E1 允许清单扩到 `ra2md.csf`（需 Lead 签发 S1 修订），要么 `csf` feature 在 S1 修订前保持 `off`。**不得**静默当作「已允许」。 |
| **D-W42-2** | §0 红线 3 / §5 R8 / schema `baselineEntry.provenance.contains_native_detour`：`db264305…` 含 **Westwood Detours，原生**，`has_detour_section=true` 本身不构成 `MISMATCH` | 本卡 `BASELINE_ADJUDICATION.md` P4 采信「原生」为**待字节验证的命题**，给 D1–D5 五条判据 + `detour_classification` 三值 | **部分采纳（不采纳「直接当已定谳事实」）** | 题面明确「它是 Westwood Detours，属原生，不是污染」，W38 主契约同口径；但同一批上游里 `W38\DISAGREE.md` D-W38-11、`FINAL_RULING.md §5.1:105,111`、`ra2opt\__init__.py:25` 都写「**第三方 Detours 段** / 已被第三方追加过」。**这是上游内部措辞冲突**（见 D-W42-13）。题面要的是「判定程序，不是结论」⇒ 本卡不靠文档措辞直接放行，而是把「原生 vs 第三方注入」做成可复算判据；结论三值由 Lead 跑完 P4 再填。同时保留 W38 R8 的**不变式**：`.detour` 属原生仍**不**改变「不能当干净零售金标准」。 |
| **D-W42-3** | §6.1 `baselineEntry.provenance.is_clean_retail_gold` 是 `const:false`；§3 硬规则 `db264305… provenance 必须显式写「含原生 .detour 段，非干净零售金标准」` | 本卡把「金标准」拆成 **R-A `TARGET_BASELINE`** 与 **R-B `RETAIL_ORACLE`** 两轨；Track B 的定谳结果**不进** `baselineEntry` | **采纳 `const:false`，但补了角色拆分** | 题面要「从候选副本中判定一份是『干净零售金标准』的可执行程序」。若照字面把结果写进 `baselineEntry`，会**违反** S1 schema 的 `const:false`。故本卡给六门 G1–G6 判据，输出落在**另立工件** `TRACK_B_gates.json`；在 Lead 拿到外部零售介质之前，预期输出 `UNDETERMINED`（`FINAL_RULING.md §5.1` 已裁「oracle 需求至今未被满足」`[转引]`）。若 Lead 确实需要把它写进 `BASELINE.json`，须走 **S3 schema 扩展**，本卡不擅自放宽 `const:false`（`UNCOVERED.md` U-W42-4）。 |
| **D-W42-4** | §5 R11：退出码 `20/21/22/23` 是 **S2 预留提案**；`UNCOVERED.md` U-W38-8 要求「S2 接线前核对全部退出码表，必要时改号」 | 本卡**不占用** 20–23，也不为耦合拒绝分配正式码；`s2ReasonCode` 与 S1 `guardVerdict.reason_codes` 正交 | **未采纳「S2 定谳退出码」** | 直接卡把 W42 定为「纯离线、只出契约与可机检断言、不写生产代码」，接线/CLI/退出码定谳属 S3+。本卡只在 `UNCOVERED.md` U-W42-12 列为待办，并在契约 §6 C7 写明「20–23 归 S1 守卫专用，本卡不占用、不改号」。S3 分配 S2 拒绝码时必须保持两套命名空间不混。 |
| **D-W42-5** | `UNCOVERED.md` U-W38-9：`E4`（`verify --fix` / seal 自愈）具体命令与文件子集「未设计」，归 S3 | 本卡 §4.3 只把 `E4` 列为**未来注册后**才可写的写点标签，不设计其文件子集 | **采纳（无分歧，留痕）** | 与直接卡「不写生产代码 / 契约先行」一致；S2 不越界设计 E4。 |

---

## 2 · 与 W36（切片计划 / 耦合矩阵）的冲突

| # | W36 原样 | 本卡做法 | 是否采纳 | 为什么 |
|---|---|---|---|---|
| **D-W42-6** | §4-S2 目标写 `FEATURE_SWITCH_CONTRACT.md`；验收 #2 要「每条开关有 `default=off`、回退态与**关闭时与 v10/v11 逐字节相同的检查命令**」；目标还含「命中/成本/失败记录格式」 | 交付 `FEATURE_SUBSET_CONTRACT.md` + `FEATURE_SUBSET.schema.json` + `ACCEPTANCE_S2.md` + `BASELINE_ADJUDICATION.md`；B1 给「全关零写 + 逐字节兼容」的**可机检断言规格**，不给可执行 shell 命令；**未给遥测记录格式** | **文件名/格式以直接卡为准；遥测格式未交付** | ① 直接卡明写「交付（只写这个目录）」并逐一列出 6 项，沿用 W38 D-W38-1 的处置原则（直接卡 > 方案）；② 直接卡是「只出契约与可机检断言、不写生产代码」，跑 `build` 比字节会写盘，故给断言规格而非命令；③ 「命中/成本/失败记录格式」（W36 §4-S2 / RE-N09 L283 / `UNCOVERED.md` U20）**不在**直接卡 S2 交付清单里，本卡不擅自扩范围，列入 `UNCOVERED.md` U-W42-13 归 S3。 |
| **D-W42-7** | §3.3.3 **G3 战役推进组 = `{*.MAP, MAPSELMD.INI, BATTLEMD98.INI}` 必须一起动**；§3.3.2 矩阵里 `MAPSELMD.INI`×`BATTLEMD98.INI` 标「**中**」、`*.MAP`×`BATTLEMD98.INI` 标「中」 | 本卡 §5 只把 W36 矩阵里标「**强**」的三格（CSF↔`BATTLEMD98.INI`、地图↔MIX、地图↔`MAPSELMD`）升格为**硬拒绝**；「中/弱」边不升格，只记入 G1–G4 组约束 | **部分采纳（不采纳「G3 全边硬拒绝」）** | 直接卡点名的强耦合对**恰好是** W36 矩阵的三个「强」格，且要求「开启了 A 但没开必须的 B ⇒ 拒绝」。若把 W36 的「中」边也升格硬拒绝，会与直接卡的「强耦合对」清单不一致、并拒掉本应合法的组合（如 `mapselmd`+`maps` 但 `battlemd=off` 究竟算不算合法，题面未定谳）。取舍：**硬拒绝只覆盖三对「强」格**；G3 里 `BATTLEMD98.INI` 的联动放进 §7 G4 元数据公式与 `UNCOVERED.md` U-W42-2，请 **Lead 定谳**是否补一条硬规则。W36 §3.3.3 的「必须一起动」作为**组约束**保留，不删除。 |
| **D-W42-8** | §3.3.1：`package_files()`（`v11\install.py:702-723`）**固定返回** `BATTLEMD98.INI`（必需）+ 可选 `MAPSELMD.INI` + `*.MAP` + `expandmd98.mix`；`BATTLEMD.INI` 是 legacy 名（`install.py:709-712` 提示「旧包请重建」） | 本卡 `battlemd.mode` 允许 `append` \| `inplace`（题面示例要求），`inplace` ⇒ 产出 `BATTLEMD.INI` | **采纳「v11 现状」为事实，但契约按直接卡扩展模式** | 题面示例 `battlemd:{mode: append\|inplace, ids:[...]}` 且要求「能表达互斥」⇒ 契约必须能表达两种模式。但这**不是 v11 能力**：v11 只产 `BATTLEMD98.INI`，`inplace` 的落地/备份/回滚（`_uninstall_legacy()` 的 `BATTLEMD.INI.ra2forge.bak` 分支、`WRITE_ENTRY_AUDIT.tsv` 行 47–51 `[转引]`）属 legacy 且**未与 feature-set 联动**。契约 §4.1 F5 标 `PASS*`，§9 差距表标「能力不具备 / 需 Lead 定谳」，`ACCEPTANCE_S2.md` B4 标 `[待运行验证]`。**不得**写成「v11 已支持 inplace」。 |
| **D-W42-9** | §3.3.1 / W30 `UNCOVERED.md` §2：`ra2md.csf` **不在** `package_files()` / 备份 / 卸载 | 契约 §3.2 在 `csf.mode=clone_append` 时把 `ra2md.csf` 纳入 `shipped()` 并要求进清单/seal/备份/卸载 | **采纳「现状事实」，不采纳「契约跟着现状缩」** | 这正是「**契约完备 ≠ 能力已具备**」的落点：直接卡把 `ra2md.csf` 列为改造面之一并要求映射表覆盖它，故契约**要求**纳入；同时在 §9 差距表明确标注 v11 不具备、实现属 S3。与 D-W42-1（S1 E1 允许清单未含它）合并上报。 |

---

## 3 · 与题面示例 / 既有措辞的精度修正

| # | 原样 | 本卡 | 等级 | 处置 |
|---|---|---|---|---|
| **D-W42-10** | 题面 feature 示例 `csf:{mode: clone_append\|none, ...}`、`mapselmd:{mode: clone_append, ...}` — 关闭用 `none` | 统一用 `off`（5 个 feature 一致），`$defs/csfFeature` 注释「`'off'` == 题面示例的 `none`」 | `[静态推断]` | 机器可读化时的**命名归一**，不改语义；避免 5 个 feature 出现 `off`/`none` 两套关闭词导致 `all_off` 判定歧义。S3 若必须对齐题面字面，可在 resolver 里做别名，但 `feature_set_id` 必须归一。 |
| **D-W42-11** | 题面「能表达互斥（如 `battlemd.mode=inplace` 与 `append` 不可同时）」 | 单值 enum 天然互斥；**额外**允许 `mode` 为长度 ≥2 的数组作为「可拒绝的输入形态」+ K1 `BATTLEMD_MODE_CONFLICT` | `[静态推断]` | 若 schema 层直接禁止数组，则「不可同时」只由类型系统保证、无法作为**可机检输入**表达。`FEATURE_SUBSET.schema.json` 故意**只校验形状**、把语义拒绝放 `coupling_rules.json`，使 3 个题面负例（最小 CSF / 非完整 MAPSELMD / 开 CSF 未开耦合项）都能作为合法输入被 resolver 拒绝。这是与 W38-S1「schema `allOf` 直接编码不变式」不同的**刻意取舍**：S1 编的是**输出**不变式（`guardVerdict`），本卡编的是**输入**形状；输入侧不编码语义是为了负例可表达。 |
| **D-W42-12** | 「最小 CSF / 非完整 MAPSELMD 必须被拒绝」在 W30/W34 是**设计警告**（W34 D4「最小文件会让官方全挂」、W30 `CSF_CAPABILITY.md:41-45`「必须克隆官方全文后追加」），且 `MAPSELMD` 侧 v11 **已实现** `validate_official_base()` | 本卡把两条升格为 **§5 硬拒绝规则**（`MINIMAL_CSF_REFUSED` / `MAPSELMD_NOT_FULL_CLONE`）+ 题面负例断言 B8/B9 | `[本次读码]` + `[静态推断]` | 不对称之处必须写清：`MAPSELMD` 侧门禁 v11 **已具备**（`mapselmd.py:142-184`）；`CSF` 侧 v11 **不具备**——`append_or_set_label(create_if_missing=True)`（`csf.py:442-466`）+ `builder.py:431-437` 会生成只含我方标签的最小 CSF，`5211` 常量在 v11 中 grep **零命中**（本卡 `[本次读码]`）。因此 B8 在 **S3 实现前必然 FAIL**，这是**契约新增门禁**而非「已具备能力」。W34/W30 的措辞被本卡当作**依据**，不当作「已实现」的证据。 |
| **D-W42-13** | `W38\DISAGREE.md` D-W38-11 / `FINAL_RULING.md §5.1` / `ra2opt\__init__.py:25`：`.detour` 是「**第三方** Detours 段」、基线「不是干净零售件」 | 题面 + W38 `VERSION_GUARD_CONTRACT.md:22` / §5 R8 / schema 字段 `contains_native_detour`：`.detour` 是「**Westwood Detours，原生**」 | `[转引]` + `[本次读码]` | **上游内部措辞冲突，本卡不替 Lead 选边**。处置：① 以**直接卡**（W42）+ **被消费的主契约**（W38 `VERSION_GUARD_CONTRACT.md`）为准 ⇒ 按「原生」建模；② 在 `BASELINE_ADJUDICATION.md` P4-D5 把三处措辞并列、要求以**字节证据**（跨副本一致性 / `.text` 完整性 / 零售介质对照）定谳 `detour_classification`；③ **两派措辞对「不能当干净零售金标准」的结论一致**，故本卡不翻案，Track B 仍预期 `UNDETERMINED`。S3 引用时须连带本条，不得只摘一侧。 |

---

## 4 · 已核对、无分歧（留痕，避免后续重复核验）

1. v11 = 14 个 `.py`、`TOOL_VERSION="1.0"`（`install.py:388`）；`package_files()` 返回 `BATTLEMD98.INI` + 可选 `MAPSELMD.INI` + `*.MAP` + `expandmd98.mix`，**不含 `ra2md.csf`**（`install.py:702-723`）`[本次读码]`。
2. `original_absent` / over-restore 语义：`install.py:1360-1368`（plan）+ `:2335-2370`（uninstall DELETE 而非 RESTORE）；W21 `DISAGREE.md:17-24` `[转引]` `[本次读码]`。
3. `action` 三态 `unchanged`/`created`/`replaced`（`install.py:1290-1348`）；`unchanged` 会 **adopt** 未登记同字节文件并在后续卸载删除 ⇒ **不等于** S2 的 `LEAVE`（严格零触碰）`[本次读码]`。
4. `MAPSELMD.INI` 完整性：`OFFICIAL_SIZE=5573`、`OFFICIAL_SHA256=074ccccd…`、14 阶段（`ALL01-07`+`Sov01-07`）、`validate_official_base()` 查 14 段 / 1..7 键 / `Scenario=` / ≥1000 B（`mapselmd.py:54-72,142-184`）`[本次读码]`。
5. `package_digest_from_steps()` 由 steps 计算、seal 绑定清单（`install.py:682-695,658-679`）⇒ W36 G4 成立 `[本次读码]`。
6. `verify.py` 零写、`build --csf-out` 直写任意路径（`builder.py:434-437`）`[转引]`（W38 §7 / `WRITE_ENTRY_AUDIT.tsv` 行 11–13）。
7. W38 §4 决策表 21 格、`guardState` 4 态、`writeEntry` E1–E6、退出码 20–23：`EVIDENCE\guard_decision_table.json` `[本次读码]` 复核 `cells.length=21`、三态 × 七入口无重复。
8. `W34\out\SUMMARY.txt` `51/51 PASS` 为 `[转引]` + `[待运行验证]`，本卡未复跑，未据此写任何能力结论。

---

## 5 · 处置原则

- 以上均为**范围 / 格式 / 口径 / 归因 / 措辞**的精度修正与冲突登记，**不改变 RE-N09 的目标与通过条件**，也不否定 W21–W38 的既有交付。
- 与 **W42 直接卡**冲突 ⇒ 以直接卡为准（沿用 W38 D-W38-1 处置原则）；与 **W36 方案**冲突 ⇒ 逐条写明「未采纳原样 + 理由」，能兼顾时保留 W36 意图（G1–G4 组约束、三对强耦合、关闭态字节兼容全部保留）。
- **唯一需要 Lead 先裁决才能进 S3 的前置**：D-W42-1（S1 §4 E1 允许清单 vs `ra2md.csf`）、D-W42-7（G3「中」边是否补硬规则）、D-W42-13（`.detour` 措辞分歧的字节定谳）。三者见 `UNCOVERED.md`。
- B 线起点仍是「补写入口接线 + 划清离线/真机边界」，不是「在已具备的能力之上加开关」。
