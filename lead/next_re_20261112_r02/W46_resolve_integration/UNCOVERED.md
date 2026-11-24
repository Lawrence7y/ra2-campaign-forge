# UNCOVERED.md · W46 / S4：未覆盖 / 不确定 / 结构性限制

> 与 `INTEGRATION.md` §5「仍存差距」互补：这里登记的是**本卡口径下的不确定性、未验证项与结构性限制**，避免把离线文件层的绿写成能力具备。
> 分级同 `INTEGRATION.md` §0。

---

## U-W46-1 · `guard_state` 仍是注入夹具，W38-S1 `classify()` 未在本卡运行 `[静态推断]` `[转引]`

`RI.derive_install_sandbox_state(game, F)` 会**只读扫描真实游戏目录**得到 `present_files` / `absent_files` 及每个文件的 SHA-256（这是本卡「install 先跑 resolve()」的输入真实性来源），但 `guard_state` 取 `--guard-state` 注入值或默认 `KNOWN_GOOD`；`RI.default_build_sandbox_state()` 更明确标注 `synthetic:true`（W42-S2 §0.1 S0 夹具）。

- W38-S1 `version_guard.classify()` **没有**在 W46 的集成路径里被调用；那条通道仍是 v13 的 `--version-guard <fixture.json>` opt-in，本卡未改。
- `[转引]` `LEAD_VERIFY_W43.md` §3 事实 2 / `LEAD_DECISIONS_W42.md` D2-补已记录同一结构性限制：**测试沙箱里的 `gamemd.exe` 是 inert 占位文本、非 PE，所以身份守卫在标准夹具里永远无法正向通过**。本卡不翻案、不绕过。
- 因此 `S4_3d..f` 证的是「注入 `UNKNOWN` ⇒ plan 完整保留 + 零写拒绝（exit 29）」，**不是**「守卫已验证」「守卫已普遍启用」。
- 真实镜像上的守卫正向通过、`BASELINE.json` 实算仍属 G-2/G-3，Lead 另立卡。

## U-W46-2 · 真机行为等价性完全不在本卡 `[转引]` `[待运行验证]`

本卡只证明「plan → 实际写入 → 清单/seal」在**离线夹具的文件层**一致。以下均未验证，且**不得**据 90/90 推断：

- 散装 `ra2md.csf` 是否覆盖 `langmd.mix` 内同名文件并被引擎采用（W30/W34 `UNCOVERED.md` `[转引]`）；
- 官方 UI 文本是否真的显示我方 `RA2F:` 标签（W40 A/E 双证 `[转引]`，属真机）；
- `MAPSELMD.INI` 的战役推进是否真触发；
- 安装态 / 执行态 / 行为态三态证据。

**归属 W45**（本卡任务书明确：真机行为等价性由 W45 负责）。本卡不得写「B 线已完成」。

`[本次实测]` 本卡执行期间在本机**多次**观察到 `gamemd.exe` 进程（如 PID 32588 / 2080，路径 `W45_b_line_equivalence\sandbox_A1\gamemd.exe`），属 W45 卡；有时为 0、有时被 W45 以新 PID 重启。多次观察下本卡均 launched 0 / attached 0、未触碰。这也是本卡不沿用 W43「进程数 0」恒称措辞、而是逐次留痕的原因（`EVIDENCE\game_proc.txt` + `game_proc_history.json`）。

## U-W46-3 · 卸载（E3）侧尚未按 plan 集合逐文件对账 `[静态推断]`

G-8 的「二次安装 / orphan / legacy 联动」在本卡已定谳并实现于**安装侧**；但 `uninstall()`（v13 `install.py:2269+`）仍按清单 `files[]` 自行决定 DELETE / RESTORE / NOOP，**`resolve()` 的 `uninstall_delete_set` / `uninstall_restore_set` 没有回灌到 E3**。

- 本卡**未改** `uninstall()` / `_uninstall_legacy()` 任何一个字节（`S4_8f` 机检 `install.py` 是 3 个改动文件之一，但改动全部集中在 `preinstall_plan()` / `install_package()`；卸载函数体保持原样，`[本次读码]`）。
- 影响：plan 的卸载语义仍是「计划层正确、执行层沿用 v13 清单驱动」。二者在首次安装 + 卸载往返下等价（W43 82 例覆盖），但**没有**本卡新增的逐文件 plan-vs-actual 对账。
- 归属：下一卡（S5）。

## U-W46-4 · F0（全关 plan）与 build 的 G1 基线互斥 `[静态推断]` `[本次实测]`

`resolve()` 层 F0 是合法的「零游戏目录写」计划（W42-S2 §4.1 F0、ACCEPTANCE_S2 B1）。但 `builder.py:build()` 的 design-driven 构建**无条件**产出 `BATTLEMD98.INI` + `*.MAP` + `expandmd98.mix`（`builder.py:119-165` `[本次读码]`），plan 未授权这些文件 ⇒ `build_subset_gate` **exit 24 拒绝**，且 `S4_1r/s` 机检零输出。

- 这是**明确的、机检的拒绝**，不是静默产全包；但也不是「F0 能驱动 build」。
- 要让 F0 驱动 build，需要新增「空游戏目录包」能力（包里没有 `BATTLEMD98.INI` 时 `package_files()` 目前会抛 `FileNotFoundError`，`install.py:762-767` `[本次读码]`）。本卡未做。
- 注意：F0 在 **install** 侧的语义同样是「拒绝」（包子集门 24）而非「零写通过」——因为包里确实有 G1 文件。若将来要支持 F0 零写安装，需上述空包能力一并落地。

## U-W46-5 · build 写后不一致不自动清理输出目录 `[静态推断]`

`RI.build_effective_switches()` 在**第一次写之前**拒绝所有已知不一致（包/开关/plan 冲突、F0、空 description 的 CSF 计划）⇒ 零输出（`S4_1p..s`）。`RI.build_reconcile()` 是**写后**的第二次逐文件复核；若它仍报 `MISMATCH`，则抛 exit 24 并**保留本卡沙箱内的 package dir 供检查**，不做 `shutil.rmtree`。

- 理由：`out_dir` 可能指向用户既有目录，自动删除有误删风险；且该目录**不在游戏目录内**（E2a），不构成 G-1 的真机风险。
- 本卡的实测中写后 `MISMATCH` **从未出现**（所有 8 个 S4 用例与 82 个继承用例的 build 对账均 `MATCH`），故该分支只由代码结构保证、未由失败注入实测。
- 归属：S5（若要「拒绝即零输出」的严格不变式，需在此处加受限清理）。

## U-W46-6 · 新增退出码 24–31 未与 v13/W38 的**全组合**逐一实测 `[静态推断]`

`S4_4j` 机检新码段全部 ≥ 24、与 v13 的 0–10 和 W38-S1 的 20/21/22/23 不重叠；`S4_3` / `S4_6` / `S4_7` 逐一实测了 24/25/26/27/28/29/30。但以下组合**未逐一实测**：

- `--feature-set` × `--version-guard`（两条 opt-in 通道叠加时的门禁顺序）；
- `--feature-set` × `--force` / `--allow-content-conflict` / `--adopt-legacy` / `--legacy` 的全组合（仅 `--adopt-legacy` 在 `S4_6g..i` 实测）；
- `--feature-set` × `--install`（`build --install` 链式调用）仅由代码结构保证（`cli.py` 已传 kwargs），**未写专门回归用例**；
- `--force-unknown` 与 W46 门禁的交互。

对应 W43 差距表 G-11（部分验证）。本卡未削弱任何 v13 门禁：v13 的 `InstallBlocked` / `PackageIdentityBlocked` / `VersionGuardBlocked` 分支在 `cli.py` 中仍排在 `ResolveIntegrationRefused` 之前或并列，`[本次读码]`。

## U-W46-7 · `verify.py` 语义未被削弱，但**新增清单字段未做长期兼容实测** `[静态推断]`

`S4_2i` 证 opt-in 安装写出的清单含 `feature_set_id` / `plan_actual_reconciliation` / `plan_mode` / `second_install` / `plan_legacy_adopted`；`S4_8f` 证 `verify.py` 与 v13 逐字节相同（只检查必需字段、不拒绝未知键，`[本次读码]` `verify.py:185-215`）。

- 未实测：v13 的 `verify` / `uninstall` 读 v14 opt-in 清单时的**全部**行为（v13 工具根本不认识这些字段，但按代码结构会忽略）。
- 未实测：seal 的 canonical 摘要在含新字段的清单上仍自洽（本卡 opt-in 安装后 `check_post_write` + `write_install_seal` 均通过，但跨版本 `verify` 未跑）。
- 归属：S5。

## U-W46-8 · `--sandbox-state` 显式覆盖的真实性与 `sandbox_id` `[静态推断]`

`install --sandbox-state <sb.json>` 允许调用者**覆盖**从真实游戏目录派生的初始态。本卡回归**未使用该开关**（`S4_*` 全部走派生路径，只有 `S4_7` 的纯规划器用例用 S0 夹具）。

- 若显式 `sandbox-state` 与磁盘真实状态不符，`resolve()` 会按错误的 present/absent 产出 CREATE/REPLACE，随后 `filter_package_files()` 与 `reconcile_install()` 会与真实 steps 冲突 ⇒ exit 24 拒绝（结构上安全），但**该路径未写专门回归用例**。
- 该开关的定位是「W42-S2 §0 的注入夹具通道」，不是生产推荐路径；文档已标注。
- 归属：S5（补一条负例）。

## U-W46-9 · 转引常量未独立复算 `[转引]`

本卡沿用但未独立复算：`5211` 官方标签数、`5573` B 官方 `MAPSELMD.INI`、`074ccccd…` bundled SHA、`2733` B 官方散装 `BATTLEMD.INI`、W40 五臂（A/E 覆盖与 UI 渲染、A 19.34 s 合法即启动、D 坏魔数才失败）、W27/W39/W44 的就地改写诊断变体、`.detour` `Characteristics=0xC0000040` 无执行位、`westwood_native` 默认。全部来自 W42/W43/W40/Lead 裁决，按 `[转引]` 标注，本卡未实算任何真实游戏二进制哈希（`BASELINE.json` 仍是 `[待运行验证]`）。

---

## 汇总：本卡**没有**声称的事

- ❌ 没有声称「B 线已完成」「守卫已具备」「回归全绿 ⇒ 行为正确」。
- ❌ 没有声称真机引擎会采用散装 `ra2md.csf` / `MAPSELMD.INI`。
- ❌ 没有声称 `battlemd:inplace` 已实现（D5.2 明确暂缓）。
- ❌ 没有声称卸载侧已按 plan 对账、F0 能驱动 build、或新退出码全组合已验证。
- ❌ 没有声称本机恒为「gamemd/game 进程数 0」（多次观察到 W45 的进程，逐次留痕）。
- ✅ 只声称：在**离线夹具的文件层**，`resolve()` 已串进 install/builder 真实写路径，逐文件计划/实际对账可机检，二次安装/orphan/legacy 语义已定谳，`inplace` 明确拒绝且 plan 层留位，默认路径与 v13 逐字节相同。
