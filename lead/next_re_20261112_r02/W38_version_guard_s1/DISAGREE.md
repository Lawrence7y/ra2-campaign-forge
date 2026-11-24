# DISAGREE.md · W38 / S1 与 W36 方案（及任务书前提）的出入

> 卡：`W38_version_guard_s1`｜纯离线只读｜2026-11-13
> 依据：`W36_b_line_kickoff\B_LINE_PLAN.md`（尤其 §3.1 / §4-S1）、`W36\DISAGREE.md` D1–D10、`W36\UNCOVERED.md` U1–U21、`docs\re\NEXT_RE_TASKS_20261112.md` L272–L287、本卡 `EVIDENCE\`。
> 口径同 `VERSION_GUARD_CONTRACT.md` §0。**本卡不迁就前提**：逐条登记冲突、给出「为什么未采纳 W36 原样」的理由，以及后续卡应如何引用。
> **红线**：本卡未写「已实现版本守卫」、未把「51/51 全绿」写成「行为正确」、未接线、未写生产代码。

## 1 · 与 W36 §4-S1 的冲突（逐条）

| # | W36 原样 | 本卡做法 | 是否采纳 | 为什么 |
|---|---|---|---|---|
| **D-W38-1** | S1 交付 `TARGET_IDENTITY.md` + `GUARD_MATRIX.csv`（+`DISAGREE.md`/`UNCOVERED.md`）；**CSV**、命令级矩阵、共 3–4 个文件 | 交付 `VERSION_GUARD_CONTRACT.md` + `WRITE_ENTRY_AUDIT.tsv` + `ACCEPTANCE.md` + `EVIDENCE\` + `DISAGREE.md` + `UNCOVERED.md`；**TSV** | **未采纳文件名/格式** | W38 卡是**直接指令**，明写「交付（只写这个目录）」并逐一列出 6 项；文件名与格式以直接卡为准。语义上 `VERSION_GUARD_CONTRACT.md` ⊇ `TARGET_IDENTITY.md`（判据/决策/降级/机器可检结构），`WRITE_ENTRY_AUDIT.tsv` ⊇ `GUARD_MATRIX.csv`（穷举写点而非 6 行命令）。用 TSV 而非 CSV 是因为单元格内大量含逗号/分号（如 `NO-IDENTITY; …`），CSV 需额外转义，TSV 可直接机读（`gen_write_audit.py` 断言每行恰 6 列）。W36 的列「`file:line` / 现有判据 / 是否调用 `identity()` / 判定 / 原因码」被拆进 TSV 的 `file:line`/`guarded`/`missing` 与契约 §4 决策表、§5 原因码、§6 结构。 |
| **D-W38-2** | 验收 #1：`GUARD_MATRIX.csv` **每个写入口一行，至少覆盖 6 个命令级入口**（`ra2forge install` / `uninstall` / `build --install` / `ra2opt apply` / `restore` / `seed --verify`）；验收 #2 要求 `ra2opt\optimize.py:112-133` 与 `v11\install.py:1140-1143` 引用行 + `apply()` 缺口行 | TSV = **43 个 v11 直接写点 + 25 个 `[CALLER]` 间接入口 + 9 个 `XCHAIN:` ra2opt 补充行 + 2 个零写/说明行 = 79 行**；`install.py:1140-1143` 有引用行；`XCHAIN:GAP-ROW` 明写 `FINAL_RULING.md §4-2: apply() 全函数体不调用 identity()` | **未采纳「6 行命令级矩阵」原样；部分采纳 W36 的 ra2opt 覆盖** | W38 卡的硬产出是「**穷举** v11 里所有会写游戏目录或写文件的入口」，并点名 `install.py` 安装/备份/替换/清单/seal、`uninstall`、`builder.py --csf-out/--mapselmd`、`verify.py`、`csf.py`/`mapselmd.py`。**6 行命令级矩阵证明不了「没有漏掉未守卫写点」**：它会整体漏掉 `build --csf-out` 直写任意路径（`builder.py:434-437`）、`cli.py:283 example` 写用户给定路径、以及所有 `_stage_*` 原语调用点。因此改为写点级穷举。ra2opt 是**另一条工具链 / 另一个版本线**，不属于 v11 的 14 个模块；把它混进 v11 穷举表会混淆版本口径（W36 D1/D4 已强调 v10/v11 与 `ra2opt` 分列）。为保留 W36 验收 #1/#2，本卡用**明确前缀 `XCHAIN:`** 的 9 行附在表尾，并在 `EVIDENCE\tsv_legend.md` 声明「不计入 v11 穷举」。 |
| **D-W38-3** | `W36\UNCOVERED.md` U2：把「S1 在 `BASELINE.json` 里重新实算 `gamemd.exe` / `ddraw.dll` / `ra2md.mix` / `langmd.mix` 的 SHA-256 + 字节数 + 绝对路径」派给 S1 | 本卡**不产出** `BASELINE.json`，不写任何真实哈希；契约只给 `baselineEntry` 的 **schema + 取值方式**，全部真实值标 `[待运行验证]` | **未采纳** | ① W38 卡交付清单固定为 6 项，不含 `BASELINE.json`；② 已确立事实「本机存在多个物理副本，且 `db264305…` 基线本身含 `.detour` 段，**不能当干净零售金标准**」⇒ 选哪一份物理副本作为目标必须 **Lead 定谳**，本卡无权裁决；③ 若本卡写入真实哈希，极易被后续卡误读为「已定谳基线 / 版本守卫已具备」，违反 W36 D4 与本卡红线；④ 契约把 `provenance.is_clean_retail_gold` 写成 `const:false`、`adjudicated` 写成 `const:true`，正是把「不得当金标准」做成机检约束。最小下一证据：S2 在自己的写域实算并请 Lead 签发，见 `UNCOVERED.md` U-W38-1。 |
| **D-W38-4** | W36 §3.1.2 同一节内部两处口径：L157「与 `BASELINE.json` 逐字段比对，**任一项不符即 `UNKNOWN`**」；L164 接线要求「`MISMATCH` → 拒绝写入并输出原因码」 | 契约 §3 消解为：**L1 任一不可读/缺失 ⇒ `UNKNOWN`**；**已读判据与声明的 `baseline_id` 正向冲突 / 原始字节窗口不符 ⇒ `MISMATCH`**；**无任何条目全字段吻合且无正向冲突 ⇒ `UNKNOWN`**；两者**都拒绝一切写** | **消解口径冲突（非简单采纳任一句）** | W38 卡要求「`KNOWN_GOOD` / `UNKNOWN` / `MISMATCH` **三态**下每个写入口分别允许/拒绝什么」，必须给确定的状态机；若「任一项不符即 UNKNOWN」则 `MISMATCH` 永远不可达，决策表第 3 列失去意义。本卡按「证据不足 vs 正向冲突」划分，保留 RE-N09 L278「未知镜像、**已被其他补丁覆盖或入口窗不符**均拒绝」的两类原因，且两者都零写入。S2 若采用别的划分须在 `DISAGREE.md` 登记。 |
| **D-W38-5** | W36 §4-S1：「**不写代码**、不跑脚本、不启动游戏」；§5 纪律「未运行任何回归/构建/校验脚本」 | 本卡在 `EVIDENCE\` 写了 8 个**只读审计/规格自检脚本**并运行，收集完整 stdout + exit code（`ast_scan` / `grep_scan` / `facts_check` / `callgraph_scan` / `ra2opt_scan` / `gen_decision_table` / `shape_check` / `gen_write_audit`） | **未采纳「不跑脚本」原样** | W38 卡明写「`EVIDENCE\`（**grep/ast 脚本 + 完整 stdout + exit code**）」「用 grep/ast 辅助，并把检索式写进 EVIDENCE」「机器可检形式：给出一个**可断言的结构**」。不跑脚本就无法交付 stdout/exit code，也无法自证 43 个写点穷举。限定：这些脚本**只读** v11 / `ra2opt/` / 文档，只写 `W38_version_guard_s1\` 内文件，**不是生产代码**、不改 `ra2forge/`、不写 `ra2youli/`、不启动游戏、不 attach、git 只读、不跑任何 `regress_dlc_v*.py` / `build` / `install` / `verify`。 |
| **D-W38-6** | W36 验收 #4：「**五类判据**各有一行失效风险与是否可作放行依据，PE 时间戳 / `RA2MD.INI` 结构 / 关键文件存在性三行标不得单独放行」 | 契约 §2 给 **13 条判据**：W36 的 5 类 + W38 卡点名的 `SizeOfImage`/节表特征、`ddraw.dll` 身份，另补 C08–C13；C03/C05/C06/C07/C10 均标「不得单独放行」 | **未采纳「五类」原样（采纳为子集）** | W38 卡判据清单**至少覆盖 7 项**，明列「镜像 SHA-256、`.text` 段哈希、PE 时间戳、`SizeOfImage`/节表特征、`RA2MD.INI` 结构特征、关键文件存在性、`ddraw.dll` 身份」。只写 5 类会漏掉 2 项硬要求。W36 的 5 类全部保留并逐条给「取值方式/判别力/失效风险/成本」。 |
| **D-W38-7** | W36 §4-S1 成本「1 个工作单元，**无回归脚本改动、不写代码**」，交付不含 `ACCEPTANCE.md` | 本卡新增 `ACCEPTANCE.md`（12 条可机检断言设计）与 `EVIDENCE\` 规格数据/自检 | **未采纳「无验收断言设计」部分** | W38 卡单列「单元化验收（不做实现，只做『能被机检』的检查设计）：**至少 6 条可执行断言**，每条写输入/期望/失败信息」。本卡给 12 条且明确全部 `[待运行验证]`，未实现、未改既有 51 例判据、未动 `W21`–`W37`。 |

## 2 · 与任务书/既有转述的前提出入（承接 W36 D1–D10，本卡复核）

| # | 前提 | 本卡复核 | 等级 | 处置 |
|---|---|---|---|---|
| **D-W38-8** | 「版本守卫已具备」/「`identity()` 已接进写入口」 | `ra2opt\game.py:104-124` 有 `identity()`，但 `ra2opt\optimize.py:112-325` `apply()` **函数体内调用数 = 0**（`EVIDENCE\ra2opt_scan.stdout.txt` §3 `[本次实测]`）；`identity()` 只在 `audit.py:109` / `optimize.py:344 status()` 被调用。**v11 全包更弱**：`KNOWN_GAMEMD`/`text_section_sha256`/`SizeOfImage`/`ddraw.dll`/`force_unknown` grep 命中均 0（`grep_scan.stdout.txt` §2），唯一守卫是 `install.py:1140` 的 `gamemd.exe` 存在性、`uninstall` 的 `game.is_dir()`（`install.py:2184`）。 | `[本次实测]` + `[本次读码]` | **不写「已实现版本守卫」**（W36 D4 成立且本卡进一步量化为「v11 零调用」）。注意 v11 里的 `_read_package_identity()`（`install.py:457`）/ `_write_package_identity()`（`builder.py:189`）是 **PKG-IDENT01 包身份**，与构建身份是不同命名空间，不可误读为守卫。 |
| **D-W38-9** | 「v11 回归 51/51 PASS ⇒ 行为/守卫正确」 | 本卡只读 `W34\out\SUMMARY.txt`（`cases: 51 passed: 51 failed: 0` / `462 passed / 0 failed`），**未复跑**；`W34\UNCOVERED.md` U9 明写沙箱内 `gamemd.exe` 是 inert 占位、从不执行 `[转引]`。 | `[转引]` + `[待运行验证]` | 全卡仅以 `[转引]` + `[待运行验证]` 引用；**不得**写成「行为正确」「守卫已具备」「回归全绿 ⇒ 行为正确」（RE-N09 L287、任务书 L374、`PROJECT_DIRECTION.md` L30 `[转引]`）。 |
| **D-W38-10** | 「`ra2forge\` 是 0.4 版 / v10 是当前最高包」 | 仓库 `ra2forge\` = 11 个 `.py`、`TOOL_VERSION="0.4"`（`install.py:262`）、`__version__="0.3.0"`（`__init__.py:9`）；v10 = 13 个 `.py`；**v11 = 14 个 `.py**（+`mapselmd.py`）、`TOOL_VERSION="1.0"`、`__version__="0.3.0"`（`facts_check.stdout.txt` §1–§3 `[本次实测]`）。 | `[本次实测]` | 沿用 W36 D1/D2/D3：写「v11（当前最高包，`TOOL_VERSION=1.0`）」；`0.4` = `TOOL_VERSION` 不是 `__version__`；两字段不混写。 |
| **D-W38-11** | 「`db264305…` 是干净零售金标准」 | `ra2opt\__init__.py:25` 原文「官方 1.001 版本…**含第三方 Detours 段（`.detour`）**」`[本次读码]`；W36 §3.1.1/§3.1.3 同 `[转引]`。 | `[本次读码]` + `[转引]` | 契约 §5 R8 与 schema `provenance.is_clean_retail_gold: const false` 双重约束；`has_detour_section=true` 本身**不**构成 `MISMATCH`，只有与基线 `provenance` 冲突才构成。 |

## 3 · 已核对、无分歧（留痕，避免后续重复核验）

1. v11 = 14 个 `.py`、仓库基线 = 11 个 `.py`；`MAPSELMD.OFFICIAL.INI` = 5,573 B（`facts_check.stdout.txt` §5）`[本次实测]`。
2. `verify.py` **零写**：AST 无任何写点，`verify.py:111` docstring「Never writes, never deletes」；`callgraph_scan.stdout.txt` §4 把 `verify.py` 列入 8 个零写模块 `[本次实测]`。
3. `package_files()`（`install.py:702-723`）返回 `BATTLEMD98.INI` + 可选 `MAPSELMD.INI` + `*.MAP` + `expandmd98.mix`，**不含 `ra2md.csf`**（与 W30 `UNCOVERED.md` §2 一致）`[本次读码]`。
4. `build --install` 走 `cli.py:312 → install_package()`，与独立 `install` 共用同一前置守卫 `[本次读码]`。
5. `W36\DISAGREE.md` D1–D10 全部沿用，本卡未发现需要推翻者；D4/D5 由本卡进一步量化。
6. 本卡未启动游戏、未 attach、未写 `ra2youli`、未改仓库 `ra2forge/`、未动 `W21`–`W37`、git 全程只读；唯一写域 `W38_version_guard_s1\`（见 `UNCOVERED.md` §4 隔离自证）。

## 4 · 处置原则

- 以上均为**范围 / 格式 / 口径 / 归因**的精度修正，**不改变 RE-N09 的目标与通过条件**，也不否定 W21–W36 的既有交付。
- 与 W38 直接卡冲突时以**直接卡**为准；与 W36 方案冲突时逐条写明「未采纳原样 + 理由」，并在能兼顾时保留 W36 意图（如 `XCHAIN:` 行保留其 ra2opt 覆盖、TSV 保留其 `install.py:1140` 引用行与 `apply()` 缺口行）。
- B 线起点仍是「补写入口接线 + 划清离线/真机边界」，不是「在已具备的版本守卫之上加功能」。
