# UNCOVERED.md · W42 / S2 未覆盖与不确定项

> 卡：`W42_b_line_s2`｜纯离线只读｜2026-11-13
> 口径同 `FEATURE_SUBSET_CONTRACT.md` §0。按影响排序；每项给「是什么 / 为什么没做 / 最小下一证据 / 归属」。
> 本卡**只出契约、schema、可机检断言设计、判定程序**，不实现 `resolve()`、不接线、不实算真实基线、不跑回归/构建/安装/校验、不启动游戏。下列项目均**未闭环**。

---

## 1 · 需 Lead 先裁决才能进 S3 的前置（最高优先）

| # | 未覆盖 | 为什么没定 | 最小下一证据 | 归属 |
|---|---|---|---|---|
| **U-W42-1** | **W38-S1 §4 `E1` `KNOWN_GOOD` 允许清单与 S2 契约冲突**：S1 只列 `*.MAP` / `BATTLEMD98.INI` / `MAPSELMD.INI` / `expandmd98.mix` 四类，`拒绝：任何未登记目标文件`；S2 契约要求 `csf` 开启时投放 `ra2md.csf`（题面把 `ra2md.csf` 列为 5 个改造面之一） | 两卡字面不一致；纪律禁止本卡改上游 W38，且 S2 纯契约无权修订 S1 决策表 | Lead 二选一签发：① 修订 W38-S1 §4 `E1` 允许清单（并同步 `guard_decision_table.json` 的 `allow` 字段）纳入 `ra2md.csf`；② 在修订前把 `csf` feature 固定为 `off`。**未签发前 S3 不得实现 csf 投放** | **Lead**（`DISAGREE.md` D-W42-1） |
| **U-W42-2** | **G3 组里 `BATTLEMD98.INI` 的联动强度未定谳**：W36 §3.3.3 说 G3「必须一起动」含 `BATTLEMD98.INI`，但 §3.3.2 矩阵标「中」；题面只点名三对「强」耦合 | 直接卡与 W36 的耦合清单粒度不一致，本卡不擅自扩大硬拒绝集（否则会拒掉题面未定谳的组合） | Lead 定谳：是否给 `mapselmd.enabled ⇒ battlemd.enabled` 补一条硬拒绝规则（K9′）。补则同步 `coupling_rules.json` 与 `ACCEPTANCE_S2.md` B13；不补则在 `PATCH_CONTRACT.md` 版本矩阵注明「中强度，仅告警」 | **Lead / S3**（`DISAGREE.md` D-W42-7） |
| **U-W42-3** | **`.detour` 段来源定性（原生 Westwood Detours vs 第三方注入）未在字节层定谳**；三处上游措辞互相冲突（题面 + W38 主契约「原生」 vs W38 `DISAGREE.md` D-W38-11 / `FINAL_RULING.md §5.1` / `ra2opt\__init__.py:25`「第三方」） | 题面要「判定程序，不是结论」；本卡纯离线、不实算哈希、不枚举真机全部副本 | 按 `BASELINE_ADJUDICATION.md` P0–P4 跑：全副本绝对路径枚举 → 固定 PE 口径取 L1 → 跨副本 `.detour` raw bytes 比对 → 零售介质对照（G1）→ 填 `detour_classification ∈ {westwood_native, third_party_injected, undetermined}`。**禁止以文档措辞替代字节证据** | **Lead**（`DISAGREE.md` D-W42-13） |
| **U-W42-4** | `RETAIL_ORACLE`（干净零售金标准）是否可定谳、以及若定谳后应落在哪个工件 | W38-S1 schema `baselineEntry.provenance.is_clean_retail_gold` 是 `const:false`，禁止任何 `BASELINE.json` 条目自称金标准；题面却要「判定一份是干净零售金标准」 | 按 `BASELINE_ADJUDICATION.md` P6 六门 G1–G6 逐门给 `PASS/FAIL/UNKNOWN`；当前预期 `UNDETERMINED`（无外部零售介质，L89）。若 Lead 要求把结果写进 `BASELINE.json`，须先走 **S3 schema 扩展**并登记为何放宽 `const:false` | **Lead / S3**（`DISAGREE.md` D-W42-3） |

## 2 · 契约本身待定谳项 `[静态推断]`

| # | 未覆盖 | 为什么没定 | 最小下一证据 | 归属 |
|---|---|---|---|---|
| **U-W42-5** | **`battlemd.mode=inplace` 的落地与回滚语义未定谳**：产出文件名、是否复用 v11 `_uninstall_legacy()` 的 `BATTLEMD.INI.ra2forge.bak` 分支、与 `BATTLEMD98.INI` 是否互斥共存 | 题面只要求「能表达互斥」；v11 只产 `BATTLEMD98.INI`，`BATTLEMD.INI` 是 legacy 名（`install.py:709-712` 提示旧包请重建） | S3 给 `inplace` 的 `shipped()` / 备份槽 / 卸载 RESTORE 三元组契约，并在隔离沙箱用 `BATTLEMD.INI` 2,733 B 夹具复现 `ACCEPTANCE_S2.md` B4 | **S3 + Lead**（`DISAGREE.md` D-W42-8） |
| **U-W42-6** | **真 `ra2youli` 初始态只覆盖题面已签发的三条**（无散装 `MAPSELMD.INI`、无散装 `ra2md.csf`、有官方 `BATTLEMD.INI` 2,733 B）；`BATTLEMD98.INI` / `*.MAP` / `expandmd98.mix` 的真机初始态**未实测** | 纯离线、不写 `ra2youli`；断言用**显式夹具态** `S0`/`S1'`/`S2'`，不臆造真机 | 真机只读枚举（需授权）后回填 `sandboxInitialState`；在此之前所有断言的初始态都是**夹具常量** | S4/S5 / Lead |
| **U-W42-7** | **二次安装 / 升级 / orphan / legacy 的子集联动未设计**：`install.py:1697-1710` `remove_absent` 分支（上一版我们创建、这一版替换）、`_uninstall_legacy()`（`WRITE_ENTRY_AUDIT.tsv` 行 47–51）、`backup="keep"` 槽 | 直接卡 S2 聚焦首次安装 + 卸载往返；W38 U-W38-13 已把这些故障分支归 S3 | S3 补「feature 子集变化 + 既有清单」的 orphan/rollback 断言，沿用 W26 `UNCOVERED.md` §1–§5 | S3（承 W38 U-W38-13） |
| **U-W42-8** | **CSF 官方全文的完整性阈值口径未定谳**：`5211` 标签来自 W38 C10 / W36 §3.1.1 `[转引]`，v11 代码里 grep **零命中**；「全文 SHA / 标签数 / 魔数」哪种做门禁未定 | 属 L2 描述项且真机行为未定谳；本卡不实算哈希 | Lead/S3 在真机基线副本上抽 `ra2md.csf` 全文 SHA-256 + `num_labels`，固定口径后回填 `csfFeature.official_full_min`（当前默认 5211 是 `[转引·待运行验证]`） | Lead / S3（承 W38 U-W38-12） |
| **U-W42-9** | **散装 `ra2md.csf` / `MAPSELMD.INI` 是否真覆盖 MIX 内同名并被引擎加载**（端到端） | W30 `UNCOVERED.md` §1 / W34 U1/U8 已自标 `[待运行验证]`；本卡只判文件层子集 | S4/S5 真机对照（W36 U6）；本卡 `ACCEPTANCE_S2.md` 全部断言**不**声称「投放后引擎会采用」 | S4 → S5 |
| **U-W42-10** | **W36 G1–G4「中/弱」耦合边只记为组约束，未做逐边可执行检查** | 题面只要求覆盖三对强耦合 + 三个负例；逐边穷举会超出直接卡范围 | S3 若需要，把 W36 §3.3.2 全 5×5 矩阵逐格给 `requires/mutex/alignment` 断言 | S3 |
| **U-W42-11** | **`feature_set_id` 的具体生成规则**（哈希口径 / 是否含 `csf_out_path` / 是否含 `guard_state`）未定 | 只定「任何子集变化 ⇒ id 变化」与「必须写进 manifest」两条不变式（§7）；具体算法属实现 | S3 定 `feature_set_id = sha256(canonical_json(features))` 并给反例（两个不同子集不得同 id） | S3 |
| **U-W42-12** | **S2 拒绝的退出码未定谳**；`s2ReasonCode` 如何与 W38-S1 R11 的 `20/21/22/23` 共存未设计 | 直接卡「不写生产代码 / 不接线」；W38 U-W38-8 把退出码核对派给 S2 | S3 接线前核对 v11 现有 0–10（`install.py:405-416`、`cli.py:27`）+ S1 20–23，给 S2 耦合拒绝分配**不冲突**的码段，两套命名空间不混 | S3（承 W38 U-W38-8） |
| **U-W42-13** | **per-feature 命中 / 成本 / 失败记录格式（遥测）未交付** | W36 §4-S2 目标含此项、RE-N09 L283 / `PROJECT_DIRECTION.md` L38 要求；但**不在** W42 直接卡的 6 项交付清单里，本卡不擅自扩范围 | S3 给 `telemetryRecord` schema（feature / hit / cost / failure / timestamp），并保持 `默认关` 语义 | S3（承 W36 U20） |
| **U-W42-14** | **内容级 verify 规则未设计**：安装后 `MAPSELMD.INI` 仍完整（14 段 / Scenario 可解析）、`ra2md.csf` 仍含 5,211 官方标签、回滚后「确实还原成合法文件」 | W34 U7 / W36 G-6 已归 S3；本卡只在构建期门禁（K4/K5）与断言 B9 里涉及 | S3 给 `verify` 只读内容级规则（不得削弱既有 5 项语义与 51 例判据） | S3（承 G-6 / W38 U-W38-13） |

## 3 · 本卡方法学边界（未做，如实登记）

| # | 未覆盖 | 原因 | 最小下一证据 |
|---|---|---|---|
| **U-W42-15** | **`ACCEPTANCE_S2.md` B1–B16 全部 `[待运行验证]`，本卡一条未执行**；未跑 `build` / `install` / `uninstall` / `verify` / `regress_dlc_v*.py` / `git apply --check` | 直接卡「纯离线、只出契约与可机检断言、不写生产代码」；跑这些会在其 `out\` / `sandbox\` 写盘，且需 S3 先实现 `resolve()` | S3 在新写域实现后逐条跑，核对 `{rejected, expected_files, uninstall_final_state, zero_game_dir_writes}` 与 `sha_tree()` 前后快照 |
| **U-W42-16** | **未产出 `BASELINE.json`、未实算任何游戏二进制 SHA-256、未枚举真机全部 `gamemd.exe` 副本** | 承接 W38 U-W38-1；题面明说「不必实际算哈希，但要给 Lead 可直接执行的步骤与判据」 | `BASELINE_ADJUDICATION.md` P0–P6 由 Lead 执行；本卡只给程序 |
| **U-W42-17** | **未逐行通读 `ra2opt` 全部模块**；只复核 `ra2opt\__init__.py:19-27`（`KNOWN_GAMEMD`）、`pe.py`/`game.py` 的引用位置来自 W38 `[转引]` | W42 卡硬范围是 v11 的 14 个 `.py` 与「feature→文件子集」；ra2opt 逐写入口盘点属 W38 / W36 U5 | W36 U5 仍有效：S3 补 ra2opt 逐写入口 `file:line` 与 `restore_roundtrip` 实测 |
| **U-W42-18** | **未复核 `W35_mapselmd_live\out\` 产物内容**（承 W36 U4 / W38 U-W38-6） | 未签发产物不得当事实；纪律不动 W21–W41 | Lead 复核后再决定是否可作真机证据 |
| **U-W42-19** | **`file:line` 引用漂移**：全部基于当前盘面本地只读副本（W26 `UNSEAL_FIX.md:4` 附近 `main@3872ef6` `[转引]`） | 未切分支验证 | 各执行卡动工前用只读 grep 复核 |
| **U-W42-20** | **改动量 / 工期**：未做代码级估算 | 本卡不写代码 | 各执行卡自行估算并记入 `RUN_LOG.md` |

## 4 · 承接既有卡片、本卡未重做的缺口（`[转引]`）

- **G-1** 复合故障残留「新清单 + 旧 seal」对无自愈子命令（`W26\UNCOVERED.md:10-11`）→ S3。
- **G-2** 清单/digest/seal 无信任链、不抗恶意（`W23\VERIFY.md:10-14`）→ 另立项；本卡 §7 只做「同步变化」，**不承诺抗恶意**。
- **G-3** 真 `ra2youli` 既存 v0.3 旧包（`fe3bdf62…`）未卸载，逐字节还原从未在真实目标演示 → **用户裁决**，本卡未触碰。
- **G-4** `ra2md.csf` 未纳入 `package_files()` / 备份 / 卸载（W30 `UNCOVERED.md` §2）→ S2 契约要求纳入，实现属 S3（U-W42-1）。
- **G-5** `MAPSELMD.INI` whole-file：foreign 文件 definite conflict **永不释放**、`--allow-content-conflict` 也不放行（`install.py:1375-1390`）→ S3；本卡 `S2'` 夹具只用于 REPLACE 类断言，**未**设计 foreign MAPSELMD 冲突分支（U-W42-7）。
- **G-6** `verify` 无内容级校验（W34 U7）→ S3（U-W42-14）。
- **G-8** `ra2opt restore` 完整回滚从未实测、`apply` 身份门未接（`FINAL_RULING.md §4` 第 2/3 条）→ S3。
- W38 `UNCOVERED.md` U-W38-1…15、W36 `UNCOVERED.md` U1–U21：除 U-W38-1（本卡以 `BASELINE_ADJUDICATION.md` 给程序）、U-W38-8（本卡 U-W42-12 登记）外，其余沿用原归属，本卡不重算。
- 退出码 20–23、E4 `verify --fix`、C05/C09/C10/C11 真实取值、`RA2MD.INI` 结构快照：均属 W38 U-W38-8…12，归 S3/S4。

## 5 · 本卡自身的隔离自证 `[本次实测]`

**已做**
- 开工前 / 收尾后各一次只读 `git status --porcelain`，输出见 `EVIDENCE\git_before.txt` / `git_after.txt`（`lead/next_re_20261112_r02/` 整体为未跟踪目录，本卡写域在其下，未改 `ra2forge/` / `ra2youli/` / `W21`–`W41`）。
- 只读 `Get-Process` 游戏进程计数 → `GAME_PROC_COUNT=0`（`EVIDENCE\game_proc.txt`）。
- `EVIDENCE\s2_shape_check.py` 对本卡 JSON 规格做**形状自检**，`TOTAL FAILURES: 0`、exit 0（`EVIDENCE\s2_shape_check.stdout.txt` / `exit_codes.txt`）。**只证规格自洽，不证任何 resolver / 守卫 / 引擎行为**。
- 唯一写域 `lead\next_re_20261112_r02\W42_b_line_s2\`；脚本对 v11 / `ra2opt/` / 上游卡片**只读**（`json.load` / `read_text`），无 `open(...,'w')` 写游戏目录、无 `os.replace`、无删除。

**未做 / 纪律约束**
- 未实算任何游戏二进制哈希（U-W42-16）、未复跑任何回归（U-W42-15）、未做改镜像副本实验、未 read 活进程内存、未 attach。
- 未写生产代码、未实现 `resolve()` / `identify_target()`、未接线、未改 v11 既有 51 例判据、未改 CLI、未动 `BASELINE.json`。
- 未把「契约完备」「shape_check 全绿」「51/51 全绿」写成「能力已具备」或「行为正确」。

## 6 · 给下一卡（S3）的最小输入清单

1. `FEATURE_SUBSET_CONTRACT.md`（feature 模型 / `shipped()` / CREATE-REPLACE-LEAVE / `original_absent` / §5 耦合 / §6 与 S1 组合 / §7 G4 公式 / §9 差距表）。
2. `FEATURE_SUBSET.schema.json`（`$defs`：featureSet / sandboxInitialState / fileSubsetPlan / couplingRuleSet / acceptanceCase）。
3. `EVIDENCE\coupling_rules.json`（K1–K12 机器可读）、`EVIDENCE\fixtures.json`（F0–F4 / S0 / S1' / S2' / SU / SM 夹具）。
4. `ACCEPTANCE_S2.md` B1–B17（输入 / 期望 / 失败信息），尤其 **B8/B9/B10 三个题面负例** 与 B14（S1 组合零写）。
5. `BASELINE_ADJUDICATION.md` P0–P6（给 Lead 执行，不属 S3 实现）。
6. `DISAGREE.md` D-W42-1…13、本 `UNCOVERED.md` U-W42-1…20。
7. **S3 动工前必须先拿到 Lead 对 U-W42-1 / U-W42-2 / U-W42-3 / U-W42-4 的裁决**，否则 `csf` 投放与 `.detour` 定谳无依据。
