# UNCOVERED.md · W38 / S1 未覆盖与不确定项

> 卡：`W38_version_guard_s1`｜纯离线只读｜2026-11-13
> 口径同 `VERSION_GUARD_CONTRACT.md` §0。按影响排序；每项给「是什么 / 为什么没做 / 最小下一证据 / 归属」。
> 本卡**只出契约与盘点**，不实现、不接线、不实算真实基线、不跑回归/构建/安装/校验、不启动游戏。下列项目均**未闭环**。

## 1 · 本卡方法学边界（最重要）

| # | 未覆盖 | 原因 | 最小下一证据 | 归属 |
|---|---|---|---|---|
| **U-W38-1** | **未产出 `BASELINE.json` 真实基线；未实算任何游戏二进制 SHA-256**（`gamemd.exe` / `ddraw.dll` / `ra2md.mix` / `langmd.mix` / `MAPSELMD.INI` / `ra2md.csf` 均未哈希） | W38 卡交付清单固定为 6 项，不含 `BASELINE.json`；且「本机多个物理副本 + `db264305…` 含原生 `.detour`」⇒ 选哪一份当目标须 **Lead 定谳**，本卡无权裁决（见 `DISAGREE.md` D-W38-3）。任务书 L79 明写「后续执行前仍须重新比对」`[转引]` | S2 在自己的写域实算「完整 SHA-256 + 字节数 + 绝对路径 + 节表 + `.text` SHA + `provenance`」，与任务书 L83-85、`FINAL_RULING.md` §5 三方比对后请 Lead 签发；本卡契约 §6.1 已给 `baselineEntry` schema | S2 / Lead |
| **U-W38-2** | **未复跑 `regress_dlc_v11.py`**（盘上 `W34\out\SUMMARY.txt` = `51/51 PASS, 462/462` 仅 `[转引]` + `[待运行验证]`）；未跑 `build` / `install` / `uninstall` / `verify` / `git apply --check` | 纪律「纯离线、不动 `W21`–`W37` 任何目录、不写生产代码」；跑这些会在其 `sandbox\`/`out\` 写盘 | `[待运行验证]`：S2/S3 在新写域复跑并核对 `cases/passed/assertions/exit` 四元组；**不得**据 51/51 写「行为正确」 | S3 / 后续执行卡 |
| **U-W38-3** | **未对任何 `gamemd.exe` 实跑 PE 解析**（C02 `.text` SHA、C04 `SizeOfImage`/节表、C03 时间戳均为**取值方式规格**，非实测值） | 本卡不改镜像副本、不建沙箱实验（S1 只出契约）；`ra2opt\pe.py` 的解析逻辑仅 `[本次读码]` 引用 | S2 在卡内副本上跑 `pe.read()` / `text_section_sha256()`，固定 PE 解析口径并留 stdout；对 `db264305…` 的 `.detour` 段做反例校验 | S2 |
| **U-W38-4** | **未做「改镜像副本」沙箱实验**（A1–A5/A7–A9/A11/A12 全部是断言设计，本卡一条未执行） | W38 卡明写「不做实现，只做能被机检的检查设计」；A1 等需 S2 接线后才可能运行 | `[待运行验证]`：S2+ 在隔离沙箱用 inert `gamemd.exe` 占位 + 卡内副本改字节，逐条跑 `ACCEPTANCE.md` 并留零写前后 `sha_tree()` 快照 | S2+ |
| **U-W38-5** | **未逐行通读 `ra2opt` 全部 17 个模块**（只补充审计了写点、`identity()` 调用点、`apply()` 函数体） | W38 卡硬范围是 **v11 的 14 个模块**；ra2opt 只是为保留 W36 验收 #1/#2 的 `XCHAIN:` 补充（9 行） | W36 `UNCOVERED.md` U5 仍有效：S3 补 ra2opt 逐写入口 `file:line`，并实测 `restore_roundtrip`（`FINAL_RULING.md` §4 第 3 条「完整回滚从未实测」`[转引]`） | S3 |
| **U-W38-6** | **未读 `W35_mapselmd_live\out\` 产物内容**（沿用 W36 U4） | 未签发产物不得当事实；纪律不动 `W21`–`W37` | Lead 复核 W35 `out\` 与缺失的 `REAL_DIR_PROOF.txt` 后再决定是否签发 | Lead / C 线 |

## 2 · 契约本身待定谳项 `[静态推断]`，需 Lead / S2 裁决

| # | 未覆盖 | 为什么没定 | 最小下一证据 | 归属 |
|---|---|---|---|---|
| **U-W38-7** | **`MISMATCH` 与 `UNKNOWN` 的边界**：契约 §3 规定「无已定谳基线 / 判据不可读 / 无条目全字段吻合 ⇒ UNKNOWN；已读判据与声明 `baseline_id` 正向冲突 ⇒ MISMATCH」。W36 §3.1.2 内部两处口径不一致（见 `DISAGREE.md` D-W38-4） | 本卡只能给**确定状态机**以保证三态决策表可达，不能替 Lead 定谳语义 | Lead 签发「优先级：W38 直接卡三态 > W36 方案措辞」；若改判据，S2 在 `DISAGREE.md` 登记 | Lead / S2 |
| **U-W38-8** | **退出码 20/21/22/23 是 S2 预留提案**，本卡未验证与未来 CLI 旗标是否冲突 | 本卡不改 CLI、不写生产代码；v11 现有 0–10 已被占用（`install.py:405-416`、`cli.py:27` `[本次读码]`） | S2 接线前核对全部退出码表，必要时改号并同步 `ACCEPTANCE.md` | S2 |
| **U-W38-9** | **`E4`（`verify --fix` / seal 自愈）的具体修复命令、文件子集、与 G-1 复合故障残留对的关系未设计** | 当前 v11 `verify.py` 零写，E4 是空集；W38 卡只要求「verify 是否含任何写动作」 | S3 定谳 G-1 二选一（`recover` 安全子命令 / `manual-only`），再把 E4 注册进 §4 决策表 | S3 |
| **U-W38-10** | **`RA2MD.INI` 结构特征（C05）的「节/键集合」具体清单未枚举**；`ra2opt\inifile.py` 的解析边界未实测 | C05 不参与身份判定，只作配置兼容/逐字节还原检查；本卡只给取值方式 | S2 在真机基线副本上跑 `IniFile.load()` 并固定「节名/键名/类型」快照格式 | S2 |
| **U-W38-11** | **`ddraw.dll` 身份（C07）的 VS_VERSION_INFO 解析与 `components()` 启发式未在真实目录验证** | 纯离线、不碰真实游戏目录 | S2 在卡内副本上跑 `game.ddraw_version()` / `components()`，验证「官方 ddraw vs cnc-ddraw」判别力 | S2 |
| **U-W38-12** | **C09（`ra2md.mix`/`langmd.mix` 条目哈希）、C10（CSF/MAPSELMD 全长哈希）的「哪个 MIX、哪条条目」口径未固定**；散装 vs MIX 内同名哪个生效**未真机定谳**（W30 `UNCOVERED.md` §1、W34 U1/U8 `[转引]`） | 属 L2 描述项，且真机行为未定谳，不能当 L1 放行依据 | S4/S5 真机对照；S2 固定哈希口径 | S4 → S5 |
| **U-W38-13** | **非 Windows / `WinError 32` 句柄锁 / `SIGINT` / 自定义异常 / `_uninstall_legacy()` 部分子分支 / `backup="keep"` 槽语义**：本卡只列写点，未实测任何故障分支 | W38 卡范围是「契约与盘点」，不是故障注入 | 沿用 W26 `UNCOVERED.md` §1–§5 `[转引]`；S3 补用例设计 | S3 |
| **U-W38-14** | **`file:line` 引用的漂移**：全部基于当前盘面本地只读副本（W26 `UNSEAL_FIX.md:4` 附近 `main@3872ef6` `[转引]`），未验证其它工作树/分支 | 纯离线只读，未切分支 | 后续卡引用前用 `EVIDENCE\ast_scan.py` 重跑核对 | 各执行卡 |
| **U-W38-15** | **改动量 / 工期**：只给「S1=契约+盘点」的范围，未做代码级估算 | 本卡只出方案、不写代码 | 各执行卡动工前自行估算并记入 `RUNLOG.md` | 各执行卡 |

## 3 · 承接既有卡片、本卡未重做的缺口（`[转引]`，不重复核验）

- G-1 复合故障残留「新清单 + 旧 seal」对无自愈子命令（`W26\UNCOVERED.md:10-11`）→ S3。
- G-2 清单/digest/seal 无信任链、不抗恶意（`W23\VERIFY.md:10-14`）→ 另立项。
- G-3 真 `ra2youli` 既存 v0.3 旧包未卸载、逐字节还原从未在真实目标演示（`HANDOFF.md` §9.3、`PAUSE_STATE_20261113.md` §5）→ **用户裁决**；本卡未触碰。
- G-4 `ra2md.csf` 未纳入 `package_files()` / 备份 / 卸载（W30 `UNCOVERED.md` §2）→ S2 → S3；本卡 `[本次读码]` 复核 `install.py:702-723` 确认仍不含。
- G-5 `MAPSELMD.INI` whole-file：foreign 文件 definite conflict **永不释放**、`--allow-content-conflict` 也不放行（`install.py:1375-1390`）→ S2/S3。
- G-6 `verify` 无内容级校验（W34 U7）→ S3。
- G-8 `ra2opt restore` 完整回滚从未实测、`apply` 身份门未接（`FINAL_RULING.md` §4 第 2/3 条）→ 本卡 `[本次实测]` 确认 `apply()` 内 `identity()` 调用数 0；回滚实测仍待 S3。
- U6/U7/U9 散装覆盖、函数级对拍、按 tick 对照、跨进程存读档/联机 → S4 → S5。
- `REVIEW\LEAD_STATUS_W25_incomplete.md` 的归因、W26 对 W25 的勘误：沿用 W36 D6/D7，本卡不重算。

## 4 · 本卡自身的隔离自证 `[本次实测]`

**已做**

- 开工前 / 收尾后各一次只读 `git status --porcelain -- ra2forge/ ra2youli/ 'lead/next_re_20261112_r02/W21*'`，两次输出一致，均为 `?? lead/next_re_20261112_r02/W21_dlc_orphan/`（`EVIDENCE\git_before.txt` / `git_after.txt`，exit 0）。`ra2forge/`、`ra2youli/` 无改动；`W21*` 那行是**开工前既有**未跟踪目录，非本卡产生。
- `Get-Process -Name gamemd,game,gamemd.exe,ra2md,ra2youli` → `GAME_PROC_COUNT=0`（`EVIDENCE\game_proc.txt`）。
- 最终版 `EVIDENCE` 脚本 exit code 全为 0（`EVIDENCE\exit_codes.txt`）；`gen_write_audit.py` 首次因 `[CALLER` 过滤式笔误 exit 1、修正后重跑 exit 0，**两次均如实留档**。脚本对 v11 / `ra2opt/` **只读**（`Path.read_text` / `read_bytes` / `ast.parse`），无 `open(...,'w')`、无 `os.replace`、无删除。
- 唯一写域 `lead\next_re_20261112_r02\W38_version_guard_s1\`；未改仓库 `ra2forge/`、未写 `ra2youli/`、未动 `W21`–`W37` 任何目录、git 全程只读、未启动游戏、未 attach。
- `EVIDENCE\shape_check.py` 对契约 JSON 结构自检 `TOTAL FAILURES: 0`（只证**本卡规格自洽**，不证未来守卫实现）。

**未做 / 纪律约束**

- 未实算任何游戏二进制哈希（U-W38-1）、未复跑任何回归（U-W38-2）、未做改镜像副本实验（U-W38-4）、未 read 活进程内存、未复核 W35 `out\` 产物（U-W38-6）。
- 未写生产代码、未接线 `identify_target()`、未实现 `--force-unknown`、未改既有 51 例判据。
- 未把「51/51 全绿」「shape_check 全绿」写成「行为正确」或「版本守卫已具备」。

## 5 · 给下一卡（S2）的最小输入清单

1. `VERSION_GUARD_CONTRACT.md` §2 判据清单、§3 判定算法、§4 决策表、§5 降级策略、§6 机器可检结构。
2. `WRITE_ENTRY_AUDIT.tsv` + `EVIDENCE\tsv_legend.md`：43 直接写点 / 25 间接入口 / 9 XCHAIN / 2 零写行，逐行 `guarded` / `missing` / `risk`。
3. `ACCEPTANCE.md` A1–A12（输入 / 期望 / 失败信息），尤其 A1（`.text` 不同 ⇒ 拒绝 + 零写）、A3（`--force-unknown` 只读降级）、A7（`--csf-out` 落游戏目录按 E1）。
4. `EVIDENCE\guard_contract_schema.json`、`EVIDENCE\guard_decision_table.json`（21 格 = 3 态 × 7 写入口）、`EVIDENCE\guard_contract_example.json`。
5. `DISAGREE.md` D-W38-1…11（不得继承的旧前提）、本 `UNCOVERED.md` U-W38-1…15。
6. 需 S2 自己补的：`BASELINE.json` 实算 + Lead 定谳（U-W38-1）、`identify_target()` 接线、退出码 20–23 核对（U-W38-8）、A1–A12 回归实现。
