# FEATURE_SUBSET_CONTRACT.md · W42 / B 线（RE-N09）S2

> 卡：`W42_b_line_s2`｜切片 **S2：feature-set → 文件子集契约**｜2026-11-13（Asia/Shanghai）
> 工作目录：`D:\Project\ra2-campaign-forge`｜**纯离线**：未启动 `gamemd.exe`、未 attach、未写 `ra2youli`、未改仓库 `ra2forge/`、未动 `W21`–`W41` 任何目录、`git` 只读、**未写生产代码**。
> 上游（**消费，不重造**）：`W38_version_guard_s1\VERSION_GUARD_CONTRACT.md`（13 判据 / 三态×7 写入口决策表 / R1–R12 / `guardVerdict` schema）、`W38_version_guard_s1\WRITE_ENTRY_AUDIT.tsv`（80 行）、`W38_version_guard_s1\ACCEPTANCE.md`（A1–A12）、`W36_b_line_kickoff\B_LINE_PLAN.md`（S1–S5 定义、§3.3.2 耦合矩阵、§3.3.3 G1–G4）、`W38_version_guard_s1\UNCOVERED.md`（U-W38-1 移交项）。
> 交付性质：**契约 + 机器可读 schema + 可机检断言设计**。`resolve()`（feature-set → 文件子集）**尚不存在**；实现、接线、`BASELINE.json` 实算、回归用例实现均属 **S3+**。

---

## 0 · 结论分级与红线

| 标记 | 本卡口径 |
|---|---|
| `[本次实测]` | 本卡 `EVIDENCE\` 下只读脚本/命令对当前盘面直接取得并核对（`file:line`、常量值、JSON 结构自检、stdout / exit code、git 快照、进程数） |
| `[本次读码]` | 本卡逐行读 v11 的 14 个 `.py`、W36/W38/FINAL_RULING/任务书原文得到的代码事实 |
| `[静态推断]` | 由多项读码/盘面事实组合推出的契约规则与工程判定（本卡新增的规范） |
| `[转引]` | 来自 W36 / W38 / FINAL_RULING / 任务书 / 直接卡背景事实的既有结论，本卡未独立复算 |
| `[待运行验证]` | 须真机/脚本/实算才能定谳；本卡未做 |

**红线（全卡适用）**

1. **「契约完备」≠「能力已具备」**。本卡定义「一个 DLC 包改了什么 / 该写哪些文件 / 该备份还原哪些」，**不**宣称 v11 已能做到。反例中多条正是 **v11 现状做不到** 的（见 §9 差距表）：`ra2md.csf` 不在 `package_files()`（W30 `UNCOVERED.md` §2 / W38 G-4 `[转引]`）、CSF 无「完整克隆」门禁、安装期仍是整包事务（W36 §3.3.1 `[转引]`）。
2. **不得把「回归全绿 / 契约结构自检全绿」写成「行为正确」或「守卫已具备」**。W34 `51/51 PASS` 为 `[转引]` + `[待运行验证]`，本卡未复跑；沙箱 `gamemd.exe` 是 inert 占位（W34 `UNCOVERED.md` U9 `[转引]`）。
3. **feature 不改变守卫结论，只改变写点集合**。`guard_state` 完全由 W38-S1 §3 `classify()` 决定，输入里**没有** feature-set；feature-set 只能决定「计划写哪些文件」，不得影响 `KNOWN_GOOD/UNKNOWN/MISMATCH/DIR_INVALID`（§6）。
4. **卸载语义不得含糊**：`original_absent=true`（原本没有该文件）⇒ 卸载必须 **DELETE**，**绝不 RESTORE**（W21 `original_absent` / over-restore 陷阱，`W21\DISAGREE.md:17-24` `[转引]`，本卡 `[本次读码]` 复核 `install.py:2335-2370`）。
5. **散装 vs MIX 内同名哪个生效 `[待运行验证]`**（W30/W34 `UNCOVERED.md` `[转引]`）。本卡只判「文件层子集」，**不**声称投放后引擎会采用。
6. **多副本 / `.detour` 口径**：任何 BASELINE 判据必须绑定绝对路径 + 该份字节；`.detour` 的处理见 `BASELINE_ADJUDICATION.md` 与 `DISAGREE.md` D-W42-13 `[转引]`（W38 §0 红线 3/4、R8）。

---

## 1 · 与 S1 的分工（消费，不重造）

| 关注 | 归属 | 本卡如何引用 |
|---|---|---|
| 「这份字节是不是登记的那份」 | **W38-S1** | `guard_state ∈ {KNOWN_GOOD, UNKNOWN, MISMATCH, DIR_INVALID}`，直接 import 其枚举；不重新定义判据 C01–C13 |
| 「哪个写入口允许什么」 | **W38-S1 §4 决策表**（3 态 × E1–E6 = 21 格） | 本卡 §6 把 `E1/E2a/E2b/E3/E4/E5/E6` 作为**写点标签**贴到文件上；allow/deny/require/exit_code 一律以 S1 为准 |
| 「原始字节窗口 / 每次重算 / 零写不变式」 | **W38-S1 §5 R9/R10、§4 跨态不变式** | 本卡 `fileSubsetPlan` 的 `effective_game_dir_write_bytes` 不变式直接承接 |
| 「一个包改了什么」 | **本卡（S2）** | 新增 `featureSet` 模型、`resolve()` 规格、CREATE/REPLACE/LEAVE、耦合规则 |
| 「耦合联动 digest/seal/清单/备份/卸载」 | **W36 §3.3.3 G4** | 本卡 §7 给公式与校验点；`digest_inputs` 字段承接 `install.py:682-695` |

> S1 的输出 `guardVerdict` 是**本卡 resolve 的前置输入**；本卡的输出 `fileSubsetPlan` 是**S1 决策表的候选写点集合**。两者串成：`classify() → guard_state` ＋ `resolve(F, S) → plan` ⇒ `effective_writes = S1_DECISION_TABLE[guard_state][entry] ∩ plan.write_set`。

---

## 2 · feature-set 模型（`FEATURE_SUBSET.schema.json`）

### 2.1 五个改造面 `[静态推断]`（依据 W36 §3.3.1 / §3.3.2、题面「已知改造面」）

题面给的可独立开关候选：地图文件(`.MAP`) / `BATTLEMD*.INI` / `expandmd*.mix` / `ra2md.csf` / `MAPSELMD.INI`。本卡把它们固化为 **5 个 feature**，每个 `mode` **单值**；`off` = 题面示例里的 `none`/关闭（命名归一，见 `DISAGREE.md` D-W42-10）。

| feature | `mode` 取值 | 关闭 | 关键参数 | 产出的**游戏目录**文件 |
|---|---|---|---|---|
| `maps` | `off` \| `sideload` | `off` | `map_files[]`（`*.MAP` 名）、`chain[]` | `map_files[]` 逐个 |
| `battlemd` | `off` \| `append` \| `inplace` | `off` | `ids[]`、`description_ref = raw\|csf_label` | `append`→`BATTLEMD98.INI`；`inplace`→`BATTLEMD.INI` |
| `mix` | `off` \| `repack` | `off` | `source_map_set[]`（必须 == `maps.map_files`）、`target_name="expandmd98.mix"` | `expandmd98.mix` |
| `csf` | `off` \| `clone_append` | `off` | `base`、`labels[]`、`official_label_count`、`target_name="ra2md.csf"` | `ra2md.csf` |
| `mapselmd` | `off` \| `clone_append` | `off` | `base`、`stages[]`、`official_stage_count=14`、`official_size_bytes=5573`、`bundled_official_sha256` | `MAPSELMD.INI` |

`feature_set_id` 是**这个组合的稳定标识**：任何子集变化都换一个 id（W36 G4，§7）。

### 2.2 三条建模要求如何被满足

**(a) 唯一决定产出的文件子集** —— §3 的 `shipped(F)` 是纯函数：给定 `F`，返回确定的文件名集合；再叠加沙箱初始态 `S` 得到每个文件的 CREATE/REPLACE/LEAVE。无歧义、无「看情况」。

**(b) 能表达「某特性关闭」** —— 每个 feature 都有 `mode:"off"`；全 off 是合法输入（`defaults.all_off_by_default=true`），产出**空**游戏目录写集，且构建产物与关闭开关前的版本逐字节相同（W36 §4-S2 验收 #2、W30 `CSF_CAPABILITY.md:56`、W34 `MAPSELMD_SPEC.md:174-176` `[转引]`）。

**(c) 能表达互斥** —— 两处：
- **feature 内互斥**：`battlemd.mode` 是单值枚举，`append` 与 `inplace` 不能同时取。schema 额外允许 `mode` 为**长度 ≥2 的数组**作为**可拒绝的输入形态**（`FEATURE_SUBSET.schema.json` `$defs/battlemdFeature`），resolver 命中 K1 ⇒ `BATTLEMD_MODE_CONFLICT` + 拒绝。这样「不可同时」既是类型约束又是可机检的拒绝规则。
- **跨 feature 互斥/强制**：见 §5 耦合规则表（`requires` / `integrity` / `content_alignment` 三类）。

> **设计原则（重要）**：`FEATURE_SUBSET.schema.json` **只校验形状**（type/enum/required），**故意不**在 schema 层强制耦合、互斥、完整性。否则「最小 CSF」「非完整 MAPSELMD」「开 CSF 未开 battlemd」这些**负例输入将无法被表达**，resolver 也就无从拒绝。所有语义拒绝都在 §5 `couplingRuleSet`（机器可读数据）里，由 resolver 执行。见 `EVIDENCE\coupling_rules.json`。

### 2.3 与 S1 schema 的类型复用

`guardState` / `writeEntry` / `s2ReasonCode` 三个枚举在 schema `$defs` 里显式标注「IMPORTED from W38-S1」。`s2ReasonCode` 与 S1 的 `guardVerdict.reason_codes` **正交**：前者是 feature-set/耦合拒绝，后者是构建身份拒绝；resolver 可同时输出两组，但 **`guard_state` 不被任何一个 `s2ReasonCode` 改变**。

---

## 3 · 确定性映射：feature-set → 文件子集

### 3.1 物理文件全集 `[本次读码]` / `[转引]`

**游戏目录（loose）候选面**（v11 命名常量，`install.py:375-398`、`builder.py:50-51`、`mapselmd.py:54`）：

| 名字 | 归属 feature | v11 里谁产出 | 题面背景 `[转引·本次实测]`（真 `ra2youli`） |
|---|---|---|---|
| `BATTLEMD98.INI` | `battlemd:append` | `builder.py:135-138`（`BATTLE_FILE_NAME`） | 未列为既有（默认 ABSENT） |
| `BATTLEMD.INI` | `battlemd:inplace` | **legacy**，v11 `install.py:709-712` 只作「旧包请重建」提示 | **PRESENT，官方散装 2,733 B** |
| `*.MAP`（n 个） | `maps` | `builder.py:121` / `install.py:719` glob | 未列为既有（默认 ABSENT） |
| `expandmd98.mix` | `mix` | `builder.py:146`（`MIX_FILE_NAME`） | 未列为既有（默认 ABSENT） |
| `ra2md.csf` | `csf` | `builder.py:441` 包目录副本；**不在 `package_files()`** | **原本没有散装** |
| `MAPSELMD.INI` | `mapselmd` | `builder.py:495` / `install.py:716` 可选纳入 | **原本没有散装** |

**游戏目录元数据**（G4 联动，`install.py:375-398`）：`ra2forge_install.json`（清单）、`ra2forge_install.json.seal`、每个 REPLACE 文件的 `<name>.ra2forge.bak` 备份槽。

**包目录产物（E2a，不落游戏目录）**：`story.md`、`ra2forge_package.json`、`BUILD_REPORT.txt`、`INSTALL.txt`、`BATTLEMD98.INI`、`*.MAP`、`expandmd98.mix`；feature-gated 追加 `MAPSELMD.INI`、`ra2md.csf`、`csf_patch.json`（`builder.py:149-170,441-458` `[本次读码]`）。

**E2b 任意路径写点**：`csf_out_path`（`build --csf-out PATH`，`builder.py:434-437`，`WRITE_ENTRY_AUDIT.tsv` 行 11–13/18–22 标 `CRITICAL` `[转引]`）。

### 3.2 `shipped(F)` —— 纯函数 `[静态推断]`

```
shipped(F) = ∅
  ∪ (F.maps.mode     == "sideload"      ? set(F.maps.map_files)        : ∅)
  ∪ (F.battlemd.mode == "append"        ? {"BATTLEMD98.INI"}            : ∅)
  ∪ (F.battlemd.mode == "inplace"       ? {"BATTLEMD.INI"}              : ∅)
  ∪ (F.mix.mode      == "repack"        ? {"expandmd98.mix"}             : ∅)
  ∪ (F.csf.mode      == "clone_append" ? {"ra2md.csf"}                  : ∅)
  ∪ (F.mapselmd.mode == "clone_append" ? {"MAPSELMD.INI"}               : ∅)

metadata(F) = (shipped(F) ≠ ∅) ? {"ra2forge_install.json",
                                 "ra2forge_install.json.seal"} : ∅
backup(F,S) = { name + ".ra2forge.bak" | name ∈ shipped(F) ∧ name ∈ S.present_files }
```

> **契约 ≠ 现状**：`ra2md.csf` 出现在 `shipped()` 里，是 **S2 契约要求纳入安装清单/备份/卸载**；v11 `package_files()`（本卡 `[本次读码]` 复核 `install.py:702-723`）**不含它**（W30 `UNCOVERED.md` §2 / W38 G-4 `[转引]`）。实现属 S3+，见 §9。

### 3.3 `action(name, F, S)` —— CREATE / REPLACE / LEAVE `[静态推断]`，语义锚定 `[本次读码]`

```
for each name in FILE_UNIVERSE:
  if name ∉ shipped(F):                    action = LEAVE
  elif name ∈ S.present_files:             action = REPLACE
  else:                                    action = CREATE
```

| 语义 | 初始态 | 安装动作 | `original_absent` | 备份 | 卸载动作 | 依据 |
|---|---|---|---|---|---|---|
| **CREATE** | 该文件 **ABSENT** | 新建/投放（`_stage_and_replace`） | `true` | **不建用户原版备份槽** | **DELETE** 文件；若存在 `.bak` 且 `original_absent` ⇒ 一并删槽、**不还原** | W21 ORPHAN-FIX01；`install.py:1302-1303`（`action="created"`）、`:1360-1368`、`:2335-2370` `[本次读码]` |
| **REPLACE** | 该文件 **PRESENT** | 先备份到 `<name>.ra2forge.bak`（`backup="create"`/`"keep"`）再原子覆盖 | `false` | 建槽 | **RESTORE** 从 `.bak` 还原 + 删槽 | `install.py:1304-1348`、`:2377-2404` `[本次读码]` |
| **LEAVE** | 任意 | **零写**：不写、不备份、不删 | — | 不建 | **NOOP**：不删、不还原 | 本卡定义 |

**三个必须写清的边界** `[静态推断]`：

1. **LEAVE ≠ v11 的 `action="unchanged"`**。`install.py:1290-1301` 的 `unchanged` 会把一个「字节相同但未登记」的文件 **adopt 为 ours**，并警告「later uninstall WILL DELETE it」——它**不是零触碰**。S2 的 `LEAVE` 是严格「不写、不备份、不删、不 adopt」。这个差异必须进 S3 的判据，否则会误读。
2. **`original_absent` 陷阱（W21）**：题面背景中真 `ra2youli` **原本没有散装 `MAPSELMD.INI`、也没有散装 `ra2md.csf`** ⇒ 这两个 feature 一旦开启就是 **CREATE + `original_absent=true`** ⇒ 卸载 **DELETE**。若错误地走 RESTORE，会把「我们自己投放的字节」当成「用户原版」还原，残留 4 个 A 时代文件（W21 `DISAGREE.md:17-24` 的 over-restore `[转引]`）。
3. **CREATE 与二次安装的 `.bak`**：`install.py:1697-1710` 的 `remove_absent` 分支处理「上一版我们创建、这一版替换」时槽里是我们自己的字节。本卡 §3 只规约**首次安装 + 卸载往返**；二次安装/升级/orphan/legacy 的子集联动移交 S3（见 `UNCOVERED.md` U-W42-7）。

### 3.4 强耦合下「装了 A 没装 B」的判定发生在 `resolve()` 之前

`resolve(F, S)` 先跑 §5 全部 `couplingRuleSet`；**任一 `on_violation=REJECT_AND_EXPLAIN` 命中 ⇒ 直接返回 `coupling_passed=false` + `reason_codes[]`，`install_write_set=[]`、`effective_game_dir_write_bytes=0`，不产出任何文件计划**。这是「拒绝并说明」的机器形态。

---

## 4 · 确定性映射表（feature 组合 ⇒ 精确文件清单）

> 记法：`C`=CREATE / `R`=REPLACE / `L`=LEAVE。`S0` = 题面真 `ra2youli` 初始态（`BATTLEMD.INI` PRESENT 2,733 B；`BATTLEMD98.INI` / `*.MAP` / `expandmd98.mix` / `ra2md.csf` / `MAPSELMD.INI` 全 ABSENT）。`S1'` = 人为在沙箱放一份既有 `expandmd98.mix` 的初始态（用于验证 REPLACE/RESTORE）。全部为 `[静态推断]` 的**规格**，不是实测。

### 4.1 组合表（每个组合给出 `shipped`、每个文件动作、备份集、卸载集）

| # | F（简写） | 校验 | `shipped(F)`（游戏目录） | 各文件动作（S0） | 备份集 | 卸载：删 / 还原 | 包目录追加产物 |
|---|---|---|---|---|---|---|---|
| F0 | 全 `off` | PASS | `∅` | 全部 `L` | `∅` | 无 | 无（与 v10/v11 关闭态逐字节相同 `[转引]`） |
| F1 | `maps=sideload, mix=repack, battlemd=append`（**G1 最小可运行包**） | PASS | `*.MAP`×n, `expandmd98.mix`, `BATTLEMD98.INI` | `*.MAP`=C, `mix`=C, `BATTLEMD98.INI`=C, `BATTLEMD.INI`=L, `ra2md.csf`=L, `MAPSELMD.INI`=L | `∅` | DELETE 上述 3 类；RESTORE 无；`BATTLEMD.INI` 等保持 | `story.md` / `ra2forge_package.json` / `BUILD_REPORT.txt` / `INSTALL.txt` |
| F2 | F1 + `csf=clone_append`（**G2 CSF 组**，`description_ref=csf_label`） | PASS | F1 ∪ `ra2md.csf` | 追加 `ra2md.csf`=C；`BATTLEMD98.INI` 字节因 `Description=RA2F:<8hex>` 改变（`builder.py:131-137` `[本次读码]`），仍是 C | `∅` | DELETE F1 三类 + `ra2md.csf` | `+ ra2md.csf` / `+ csf_patch.json` |
| F3 | F1 + `mapselmd=clone_append`（**G3 战役推进组**） | PASS | F1 ∪ `MAPSELMD.INI` | 追加 `MAPSELMD.INI`=C | `∅` | DELETE F1 三类 + `MAPSELMD.INI` | `+ MAPSELMD.INI` |
| F4 | F2 + `mapselmd=clone_append`（全开） | PASS | 5 面齐全 + `BATTLEMD98.INI` | `BATTLEMD.INI`=L，其余全部 C | `∅` | DELETE 5 面 + `BATTLEMD98.INI` + 清单/seal | `+ ra2md.csf` / `+ csf_patch.json` / `+ MAPSELMD.INI` |
| F5 | F1，但 `battlemd:inplace` | PASS\* | `*.MAP`, `expandmd98.mix`, **`BATTLEMD.INI`** | `BATTLEMD.INI`=**R**（PRESENT 2,733 B），其余 C | `BATTLEMD.INI.ra2forge.bak` | DELETE 地图/MIX；**RESTORE `BATTLEMD.INI`** + 删槽 | 同 F1 |
| F6 | F1，初始态 `S1'`（`expandmd98.mix` PRESENT） | PASS | 同 F1 | `expandmd98.mix`=**R**，其余 C | `expandmd98.mix.ra2forge.bak` | DELETE 地图/`BATTLEMD98.INI`；**RESTORE `expandmd98.mix`** | 同 F1 |
| N1 | `csf=clone_append`, `battlemd=off` | **REJECT** | — | — | — | — | — |
| N2 | `csf=clone_append`, `base="minimal"`（最小 CSF） | **REJECT** | — | — | — | — | — |
| N3 | `mapselmd=clone_append`, `base="partial_or_minimal"` | **REJECT** | — | — | — | — | — |
| N4 | `battlemd.mode=["append","inplace"]` | **REJECT** | — | — | — | — | — |
| N5 | `maps=sideload`, `mix=off` | **REJECT** | — | — | — | — | — |
| N6 | F1，`guard_state=UNKNOWN` | PASS（耦合）⇒ **零写** | 同 F1（**planned**） | 全部降级为「计划但未执行」 | `∅` | 无 | 仅隔离沙箱产物 + `UNKNOWN` 标签 |

\* F5 的 `battlemd:inplace` 在 v11 属 legacy 名（`install.py:709-712` 会提示「旧包请重建」）；契约允许该模式，但**实现/回滚属 S3 且需 Lead 定谳**（`DISAGREE.md` D-W42-8、`UNCOVERED.md` U-W42-5）。

### 4.2 「每个 feature 组合 ⇒ 精确清单」的机检口径

`fileSubsetPlan.files[]` 是**穷举 `FILE_UNIVERSE` 每一行**的输出（含 LEAVE 行），不是只列「会写的文件」：

```
FILE_UNIVERSE = [
  "BATTLEMD98.INI", "BATTLEMD.INI", "<each maps.map_files[i]>",
  "expandmd98.mix", "ra2md.csf", "MAPSELMD.INI",
  "ra2forge_install.json", "ra2forge_install.json.seal"
]
```

对每一行必填 `{name, layer, action, original_absent, produced_by_feature, write_entry, uninstall}`。`install_write_set` = 所有 `action ∈ {C,R}` 的 `name`；`backup_set` = 所有 R 的 `.bak`；`uninstall_delete_set` = 所有 C 的 `name` + 清单/seal；`uninstall_restore_set` = 所有 R 的 `name`。**四集合由 `files[]` 派生，不得独立填写**（避免契约内部自相矛盾）。

### 4.3 写点标签（把文件贴到 S1 的 E1–E6）`[静态推断]`

| 文件层 | `write_entry` | 依据 |
|---|---|---|
| 游戏目录投放文件（C/R）、备份槽、清单、seal、孤儿清理 | `E1` | W38-S1 §4 E1 `allow: BACKUP_SLOT_WRITE, PACKAGE_FILE_REPLACE, MANIFEST_WRITE, SEAL_WRITE, ORPHAN_CLEANUP` |
| 包目录产物 | `E2a` | W38-S1 §4 E2a |
| `csf_out_path`（落在游戏目录外） | `E2b` | W38-S1 §4 E2b、`WRITE_ENTRY_AUDIT.tsv` 行 11–13 |
| 卸载的 DELETE / RESTORE / 移除清单与 seal | `E3` | W38-S1 §4 E3 |
| `verify` 只读 | `E5` | W38-S1 §4 E5；`verify.py` 零写 `[转引]` |
| 未来 `verify --fix` / seal 自愈 | `E4`（**注册后**才可写） | W38-S1 §4 E4 + U-W38-9 |

> **路径归属**：`csf_out_path` 经 `realpath` + `commonpath` 落在任何游戏目录内 ⇒ **改贴 `E1`** 并走完整 L1 重算 + C12（W38-S1 §1.2 路径归属规则、ACCEPTANCE A7 `[转引]`）。本卡不改写 S1 结论，只给出 reason code `CSF_OUT_INSIDE_GAME_DIR_DEFERRED_TO_S1` 表明「交给 S1 判」。

---

## 5 · 强耦合校验（`EVIDENCE\coupling_rules.json` 的可读版）

全部 `on_violation = REJECT_AND_EXPLAIN`（拒绝并说明）。`requires`=开启了 A 没开 B 必须拒绝；`mutex`=不可同时；`integrity`=完整克隆门禁；`content_alignment`=内容一致性。

| id | kind | 前件 | 后件（必须成立） | `reason_code` | 依据 |
|---|---|---|---|---|---|
| **K1** | mutex | `battlemd.mode` 为数组 / 同时声明 `append`+`inplace` | 单值 | `BATTLEMD_MODE_CONFLICT` | 题面「`inplace` 与 `append` 不可同时」 |
| **K2** | requires | `csf.mode=clone_append` | `battlemd.mode ≠ off` **且** `battlemd.description_ref=csf_label` | `CSF_WITHOUT_BATTLEMD` / `CSF_LABEL_UNBOUND` | W36 §3.3.2「`BATTLEMD98.INI` × `ra2md.csf` = **强**」、G2；W30 `MISSING:RA2F:...` `[转引]`；题面负例 3 |
| **K3** | requires | `battlemd.description_ref=csf_label` | `csf.mode=clone_append` 且 label 一致 | `CSF_LABEL_UNBOUND` | `builder.py:131-137` `[本次读码]` |
| **K4** | integrity | `csf.mode=clone_append` | `base=official_full_clone` ∧ `official_label_count ≥ 5211` ∧ labels 仅为我方追加 | `MINIMAL_CSF_REFUSED` | W30 `CSF_CAPABILITY.md:41-45`、W34 D4「最小文件会让官方全挂」`[转引]`；**题面负例 1**；`5211` 为 W38 C10 / W36 §3.1.1 `[转引·待运行验证]` |
| **K5** | integrity | `mapselmd.mode=clone_append` | `base=official_full_clone` ∧ `official_stage_count=14` ∧ `official_size_bytes=5573` ∧ bundled SHA 匹配 ∧ 14 段/1..7 键/`Scenario=` 齐全 | `MAPSELMD_NOT_FULL_CLONE` | W34 D4；`mapselmd.py:60-62,142-184` `[本次读码]`；**题面负例 2** |
| **K6** | requires | `maps.mode=sideload` | `mix.mode=repack`（且 `source_map_set == map_files`） | `MAPS_WITHOUT_MIX` | W36 §3.3.2「`*.MAP` × `expandmd98.mix` = **强**」、G1 |
| **K7** | requires | `mix.mode=repack` | `maps.mode=sideload` | `MIX_WITHOUT_MAPS` | `builder.py:143-147`、`_verify_mix_contents` 恰含地图 0 INI `[本次读码]` |
| **K8** | content_alignment | `mix.mode=repack` | `mix.source_map_set` 与 `maps.map_files` 逐项相等 | `MIX_MAP_SET_MISMATCH` | W36 §3.3.2 强耦合 |
| **K9** | requires | `mapselmd.mode=clone_append` | `maps.mode=sideload` | `MAPSELMD_WITHOUT_MAPS` | W36 §3.3.2「`*.MAP` × `MAPSELMD.INI` = **强**」、G3 |
| **K10** | content_alignment | `mapselmd.mode=clone_append` | 每个 `stages[].Scenario` ∈ `maps.map_files`；link/末关来自同一 `chain` | `MAPSELMD_SCENARIO_UNRESOLVED` | W34 `MAPSELMD_SPEC.md:150-158` `[转引]` |
| **K11** | requires | 任一 feature 非 off | G4：`digest_inputs` / seal / 清单 / 备份 / 卸载集合与 `shipped()` 同步 | `G4_METADATA_DESYNC` | W36 §3.3.3 G4、`install.py:682-695` `[本次读码]` |
| **K12** | requires | `csf_out_path` 落在游戏目录内 | 交由 S1 `E1` 全流程（L1 重算 + C12）；不在此处自行放行 | `CSF_OUT_INSIDE_GAME_DIR_DEFERRED_TO_S1` | W38-S1 §1.2 / A7 `[转引]` |

**「强耦合对」的取舍 `[静态推断]`**：题面点名三对 = CSF↔`BATTLEMD98.INI`、地图↔MIX、地图↔`MAPSELMD`，正好对应 W36 §3.3.2 矩阵里**标「强」的三格** `[转引]`。本卡把这三对升格为**硬拒绝**（K2/K6+K7+K8/K9+K10）。W36 矩阵中「中/弱」的边（如 `battlemd`×`mapselmd`=中、`maps`×`battlemd`=中、`csf`×`mapselmd`=中）**不**升格为硬拒绝，只记入 G1–G4 组约束供 S3 参考，取舍理由见 `DISAGREE.md` D-W42-7。

---

## 6 · 与 S1「三态 × 写入口决策表」的组合规则 `[静态推断]`

**核心不变式：feature 不改变守卫结论，只改变写点集合。**

```
resolve_full(F, S, guard_state, s1_decision_table) -> FileSubsetPlan

  1  V = W38_S1.classify(game_dir, BASELINE.json, declared_baseline_id)
        # ↑ 输入不含 F，不含 S 的 feature 字段。guard_state = V.state
  2  P = resolve(F, S)                      # §3 + §5；纯函数，与 V 无关
  3  if not P.coupling_passed:
        return P with install_write_set=[], effective_game_dir_write_bytes=0
        # 耦合拒绝先于守卫，且零写；reason_codes 是 s2ReasonCode，不改 V.state
  4  for each (entry_id, name) in P.write_entries:
        cell = s1_decision_table[guard_state][entry_id]
        effective = cell ∩ P.planned_action(name)      # allow/deny/require/exit_code 一律取 S1
  5  # 跨态不变式（W38-S1 §4 / §6.1 不变式 1）：
     if guard_state ≠ KNOWN_GOOD:
        effective_game_dir_write_bytes = 0
        wrote_game_dir = false
        # 但 P.files[]（计划集合）保留，供 guard_report.json 记录「计划但被拒」
```

**组合规则逐条**

| 规则 | 内容 |
|---|---|
| **C1 输入隔离** | `guard_state` 的输入集合 = `{game_dir, BASELINE.json, declared_baseline_id, criteria_cache}`（W38-S1 §3），**不含** `featureSet`。任何 `s2ReasonCode` 都不得写回 `guardVerdict.state`。 |
| **C2 正交输出** | `fileSubsetPlan` 同时带 `guard_state`（S1 的）和 `coupling_violations`（S2 的），两者各自独立机检。 |
| **C3 守卫优先** | `UNKNOWN`/`MISMATCH`/`DIR_INVALID` 下，S1 决策表对 `E1/E2b(游戏目录)/E3/E4/E6` 的 `ALL_GAME_DIR_WRITES` deny 生效 ⇒ **零写入**，**与 F 全开/全关无关**。F 只决定「计划写点集合」有多大。 |
| **C4 写点投影** | F 决定 `shipped()` 与每个文件的 `write_entry` 标签；S1 决定该标签在该态下 allow/deny。二者是「集合 × 决策表」的乘积，不是覆盖关系。 |
| **C5 E2b 特例** | `csf.enabled` 为真时引入 `E2b` 写点；若 `csf_out` 落在游戏目录内 ⇒ 按 W38-S1 §1.2 改贴 `E1`，走 L1 重算 + C12（A7）。K12 只做「交给 S1」，不自行放行。 |
| **C6 flag 不变** | `--force-unknown` / `--force` / `--allow-content-conflict` / `--adopt-legacy` / `--legacy` 属 W38-S1 R5/§4 跨态不变式管辖，**不得**改变 `guard_state`，也**不得**绕过 §5 耦合拒绝。 |
| **C7 退出码** | S2 耦合拒绝的退出码由 S3 定谳（`UNCOVERED.md` U-W42-12）；W38-S1 R11 预留的 `20/21/22/23` 归**守卫**专用，本卡不占用、不改号 `[转引]`。 |

> 一句话：**S1 决定「能不能写游戏目录」，S2 决定「打算写哪些文件」；后者永远不能推翻前者。**

---

## 7 · G4 全局事务公式 `[静态推断]`（依据 W36 §3.3.3、`install.py:682-695` `[本次读码]`）

```
steps        = [ {name, new_sha} for name ∈ shipped(F) ]        # 排序后
digest       = sha256( "\n".join(f"{s.name} {s.new_sha}"
                        for s in sorted(steps, key=name)) )       # install.py:682-695
manifest     = { entries: shipped(F) ∪ backup_set,
                 original_absent[] , removed_orphans[],
                 package_digest: digest, package_id }
seal         = sha256( canonical_bytes(manifest) )                 # install.py:658-679
backup_set   = { n+".ra2forge.bak" ∀ REPLACE(n) }
uninstall    = DELETE ∀ CREATE(n) + RESTORE ∀ REPLACE(n)
               + remove manifest + remove seal
```

**不变式（机检点）**：`F1 ≠ F2 ⇒ digest(F1) ≠ digest(F2) ⇒ seal(F1) ≠ seal(F2) ⇒ manifest(F1) ≠ manifest(F2) ⇒ backup_set/uninstall 动作同步变化`。即**不能只改一个文件而让其余元数据保持不变**（W36 §3.3.2 末行 `[转引]`）。`feature_set_id` 必须进入 `manifest`（否则两个不同子集可能算出同一 digest，属于 `G4_METADATA_DESYNC`）。

---

## 8 · 与 W36 §4-S2 验收、W38-S1 锚点对照

| W36 §4-S2 验收项 | 本卡落点 |
|---|---|
| #1 每个「强耦合」对给一条可执行检查 | §5 K2/K6+K7+K8/K9+K10；`ACCEPTANCE_S2.md` B3/B4/B7/B8 |
| #2 每条开关 `default=off`、回退态、「关闭时与 v10/v11 逐字节相同」 | §2.1 `off`；§4.1 F0；`EVIDENCE\coupling_rules.json` `defaults`；`ACCEPTANCE_S2.md` B1 |
| #3 G4 公式与校验点 | §7；`ACCEPTANCE_S2.md` B10 |
| #4 不改代码、不改既有 51 例判据 | 本卡纯契约；`ACCEPTANCE_S2.md` 全部 `[待运行验证]` |

| W38-S1 锚点 | 本卡引用 |
|---|---|
| §4 决策表 21 格 | §6 `s1_decision_table`、§4.3 写点标签 |
| §5 R1–R12 | §6 C1/C3/C6/C7 |
| §6.1 `guardVerdict` | schema `$defs/guardState`、`s2ReasonCode` 正交说明 |
| `ACCEPTANCE.md` A1/A3/A7 | `ACCEPTANCE_S2.md` B11/B12/B13 |
| `UNCOVERED.md` U-W38-1 | `BASELINE_ADJUDICATION.md` |

---

## 9 · 「契约完备」与「能力现状」差距表 `[本次读码]` / `[转引]`（**不得混写**）

| 契约条款 | v11 现状 | 判定 |
|---|---|---|
| `csf` 开启 ⇒ `ra2md.csf` 进 `shipped()` / 备份 / 卸载 | `package_files()` 返回 INI + `MAPSELMD.INI` + `*.MAP` + `expandmd98.mix`，**不含 `ra2md.csf`**（`install.py:702-723` `[本次读码]`；W30 `UNCOVERED.md` §2 / W38 G-4 `[转引]`） | **能力不具备**，S3 补 |
| 全 feature 独立开关 | 安装期整包事务、`package_files()` 固定返回（W36 §3.3.1 `[转引]`） | **能力不具备**，S3 补 |
| `battlemd:inplace` 模式 | v11 只产 `BATTLEMD98.INI`；`BATTLEMD.INI` 是 legacy 名且会提示「旧包请重建」（`install.py:709-712`） | **能力不具备 / 需 Lead 定谳** |
| 最小 CSF 必须被拒绝 | `csf.py:442-466` `append_or_set_label(create_if_missing=True)` + `builder.py:431-437` 会生成只含我方标签的最小 CSF；v11 **无**官方全文克隆门禁（`5211` 常量在 v11 中 grep 零命中 `[本次读码]`） | **契约新增门禁，能力不具备** |
| `MAPSELMD` 非完整克隆必须被拒绝 | `mapselmd.validate_official_base()`（`mapselmd.py:142-184`）**已实现** 14 段 / 1..7 键 / `Scenario=` / ≥1000 B；bundled SHA 校验（`:60-62,187-198`） | **能力已具备**（但只覆盖构建期；安装/卸载/verify 内容级校验仍缺，W34 U7 `[转引]` → S3） |
| 散装 `ra2md.csf`/`MAPSELMD.INI` 被引擎采用 | 端到端未真机定谳（W30/W34 `UNCOVERED.md` `[转引]`） | `[待运行验证]`，属 S4/S5 |
| 每次写入口重算 L1 / 版本守卫接线 | v11 全包 0 处构建身份判定（W38 §7 `[转引]`） | **能力不具备**，S2+ 接线 |

> **本卡交付边界**：feature 模型、确定性映射表、CREATE/REPLACE/LEAVE 与 `original_absent` 语义、耦合校验规则、与 S1 的组合规则、G4 公式、可机检断言设计。`resolve()` 实现、`BASELINE.json` 实算、退出码定谳、回归用例实现、内容级 verify、二次安装/orphan/legacy 子集联动，全部属 S3+（见 `UNCOVERED.md`）。

---

## 10 · 纪律复核

- 纯离线：未启动游戏、未 attach、未写 `ra2youli`、未改仓库 `ra2forge/`、未动 `W21`–`W41` 任何目录、`git` 全程只读（前后快照见 `EVIDENCE\git_before.txt` / `git_after.txt`）。
- 未写生产代码：`EVIDENCE\` 下仅 1 个**只读形状自检脚本**（校验本卡 JSON 结构，不实现任何 resolver / guard / 安装逻辑），其余为数据/文档。
- 唯一写域：`lead\next_re_20261112_r02\W42_b_line_s2\`。
- 分级：全文按 §0 口径标注；`51/51 PASS`、官方 5211 标签、`MAPSELMD.INI` 5573 B、`BATTLEMD.INI` 2733 B 等按来源标 `[转引]` / `[本次读码]`。
- 与 W36/W38 冲突处：`DISAGREE.md` 逐条登记取舍；未覆盖与不确定项：`UNCOVERED.md`。
