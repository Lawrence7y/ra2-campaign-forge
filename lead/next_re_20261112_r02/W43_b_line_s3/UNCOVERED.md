# UNCOVERED.md · W43 / S3 未覆盖、不确定与移交项

> 与 `S3_IMPLEMENTATION.md §5 差距表` 互补：这里登记**证据边界、夹具口径、未逐一实测的组合、以及明确移交 S4/S5/Lead 的项**。
> 分级同 `S3_IMPLEMENTATION.md §0`。**本卡不写「B 线已完成 / 守卫已具备 / 行为正确」。**

---

## U-W43-1 · 版本守卫默认未启用（最重要，见 DISAGREE D-W43-1）

`--version-guard` 是 **opt-in**。默认 `install` / `uninstall` / `build` 不跑 S1 身份判定，与 v12 逐字节相同。原因：无已定谳 `BASELINE.json` ⇒ 按 W38-S1 §3 必落 `UNKNOWN` ⇒ 拒绝一切游戏目录写入，会破坏 57 例与向后兼容；且 `BASELINE.json` 须由 Lead 定谳后签发（W42 `BASELINE_ADJUDICATION.md §4` `[转引]`）。

**未验证**：默认部署下的守卫行为（因为没有默认守卫）；Lead 签发真实 `BASELINE.json` 后把开关转为默认的行为变化需重新回归。

## U-W43-2 · `BASELINE.json` 实算 / Track A 未做

本卡**未计算任何真实游戏二进制的 SHA-256**，未枚举真机候选副本，未执行 W42 `BASELINE_ADJUDICATION.md` 的 P0–P5。`TRACK_B_gates.json` 中的 `C01/C02/C08/C07` 账面值全部标 `[转引]`（来源是 W42 §1.2 / `FINAL_RULING.md` / `ra2opt/__init__.py`），仅供对账，**不是本卡实测**。P6 的 G1–G6 只登记状态，全部 `UNKNOWN`，总判定 `UNDETERMINED`。

`BASELINE.json` schema 未扩展、未新增任何 `baselineEntry`（`S3_22d` 机检）。

## U-W43-3 · ra2opt XCHAIN 写入口（10 行）未接线

`WRITE_ENTRY_AUDIT.tsv` 行 72–80 的 `XCHAIN:` 行属于独立包 `ra2opt\`（`optimize.apply` / `backup.restore` / `backup.seed` / `safewrite.write_bytes` / `cddraw.install` / `launcher.write_launcher` / `inifile.IniFile.save` / `pe.set_laa` / `pe.set_stack_reserve` / `appcompat.set_layer`），**不在 v13 包内**。本卡显式列为 `s3_contract.XCHAIN_ROWS_OUT_OF_SCOPE`（`S3_23p` 机检 10 行），不隐藏、不声称已覆盖。

## U-W43-4 · S1 L2/L3 判据与 C12 原始字节窗口未接入运行时

`version_guard.classify()` 实现的是 **L0（C06 + C13） + L1（C01 全文 SHA / C02 `.text` SHA / C04 节表+SizeOfImage / C08 字节数 / C13 绝对路径）**，与 W38-S1 §3 步骤 0–5 对齐。以下**未实现**：

| 判据 | 状态 |
|---|---|
| C03 `TimeDateStamp` | `_pe_l1()` 读出并放在 evidence 中，仅描述、不参与精确匹配（符合「不得单独放行」） |
| C05 `RA2MD.INI` 结构 | 未采集 |
| C07 `ddraw.dll` 身份 / VS_VERSION_INFO | 未采集 |
| C09 MIX 内关键条目哈希 | 未采集 |
| C10 散装 CSF / MAPSELMD 全长哈希 | 未采集（csf 完整性门禁在 resolve/原语层实现，非 S1 C10） |
| C11 `components()` 集合 | 未采集 |
| C12 写前原始字节窗口 | **未接入**：`guardVerdict.byte_windows_ok` 在 `KNOWN_GOOD` 时置 `true`，但不是由真实窗口比对得出 |

`--csf-out` 归属守卫的 S3 预检虽按 E1 全流程接线，但 C12 的实际窗口比对属 S4。

## U-W43-5 · 未逐一实测的 flag 组合（W38-S1 A8）

契约 §4 跨态不变式要求 `--force` / `--allow-content-conflict` / `--adopt-legacy` / `--legacy` / `--drop-legacy-battlemd` **均不得改变 `guard_state`**。本卡代码层保证（守卫在这些 flag 之前运行、且 flag 不进入 `classify()` 输入集合），但**回归只实测了 `--force-unknown`（S3_23i/j）与继承 57 例里的 `--force`/`--allow-content-conflict`/`--adopt-legacy` 在「守卫关闭」下的行为**。守卫开启时叠加上述每一个 flag 的全组合未逐一跑，`[待运行验证]`，移交 S4。

## U-W43-6 · `resolve()` 与 install/builder 未端到端串接

本卡 `resolve()` 是**纯函数**：消费 feature-set + 沙箱初始态 ⇒ 产出确定性 `fileSubsetPlan`（含 CREATE/REPLACE/LEAVE、`original_absent`、四集合、digest、warnings）。它**没有**把计划回灌到：
- `install.package_files()`（仍返回 v12 的固定集合）
- 安装事务 / 清单 `ra2forge_install.json` / seal / 备份槽 / 卸载集合
- `builder` 的产物开关

即「feature-set 决定写哪些文件」在**计划层**已实现并可机检，但**执行层**仍是 v12 的整包事务（W36 §3.3.1 `[转引]`）。端到端串接属 S4。

## U-W43-7 · 二次安装 / 升级 / orphan / legacy 的子集联动

W42 `FEATURE_SUBSET_CONTRACT.md §3.3` 边界 3 把「二次安装/升级/orphan/legacy 的子集联动」移交 S3；本卡 `resolve()` 只规约**首次安装 + 卸载往返**（与 S2 §3.3 明示范围一致）。这些场景 `[待运行验证]`，移交 S4。差距表 G-8。

## U-W43-8 · `battlemd:inplace` 只在纯规划层

`S3_4`（B4）与 `S3_21`（D3）用 `battlemd.mode="inplace"` 作**规划夹具**（`resolve()` 不写真实文件、不启动游戏）。v12/v13 的 builder 仍只产 `BATTLEMD98.INI`，`BATTLEMD.INI` 是 legacy 名（`install.py:709-712` 提示「旧包请重建」）。S2 §4.1 F5 注明该模式的实现/回滚需 Lead 定谳（`DISAGREE.md` D-W42-8 / `UNCOVERED.md` U-W42-5 `[转引]`）；本卡**未实现**其构建/回滚。

## U-W43-9 · 安装/卸载/verify 的内容级校验

`MAPSELMD` 侧 `validate_official_base()`（v11 `mapselmd.py:142-184`）在**构建期**已实现；CSF 侧本卡在 resolve/原语层实现。**安装期 / 卸载期 / verify 期**对散装 `ra2md.csf` / `MAPSELMD.INI` 的内容级完整克隆校验仍缺（W34 U7 `[转引]`）。`verify` 在 v13 仍严格只读、无 E4。

## U-W43-10 · 真机行为等价性（S4/S5，不在本卡）

| 未定谳事实 | 来源 |
|---|---|
| 散装 `ra2md.csf` 是否覆盖 `langmd.mix` 内同名并被引擎采用 | W30/W34 `UNCOVERED.md` `[转引]` + W40 A/E 真机五臂 `[签发]`（本卡未复跑） |
| 散装 `MAPSELMD.INI` 是否被引擎采用、战役推进是否真触发 | W34 `UNCOVERED.md` `[转引]` |
| 官方 UI 在完整克隆 + 我方标签下是否真的渲染我方文本 | W40 E 臂 `[签发]`，本卡未复跑 |
| 官方 5,211 标签 / `MAPSELMD.INI` 5,573 B / `074ccccd…` 在真 `ra2youli` 上的实测值 | `[转引·待运行验证]`；本卡只用 W42 夹具常量 |
| 多副本 / `.detour` D1–D5 字节判据实算 | `[待运行验证]`，程序保留在 `TRACK_B_gates.json` |

本卡**未启动游戏、未 attach、未写 `ra2youli`**，进程数 0（`EVIDENCE/game_proc.txt`）。沙箱 `gamemd.exe` 是 inert 文本占位。

## U-W43-11 · 夹具口径（防止把夹具读成实算）

`ACCEPTANCE_S2.md §0` 允许注入夹具 `guard_state` / `BASELINE.json` 条目。本卡：
- `resolve()` 的 `guard_state` 全部为**注入夹具值**（`KNOWN_GOOD`/`UNKNOWN`/`MISMATCH`），不是真机实算（`S3_15`）。
- `version_guard.classify(evidence=...)` 的 L1 判据在 `S3_23` 中为**注入的离线夹具**（`source="injected_fixture"`，代码里显式标注），不是从真实 PE 读取；真实路径 `collect_l1(injected=None)` 会读盘并解析 PE，但**本卡回归未在真实 PE 上跑过**。
- `TRACK_B_gates.json` 的账面哈希全部 `[转引]`，本卡未实算。
- `fixtures.json` 的 S0/S1'/S2'/SU/SM 是 W42 夹具常量；「真 `ra2youli` 原本没有散装 `MAPSELMD.INI`/`ra2md.csf`、有官方散装 `BATTLEMD.INI` 2,733 B」是题面已签发背景 `[转引]`，本卡未独立复核真机。

## U-W43-12 · 退出码与 CLI 集成审计

W38-S1 R11 预留的 `20/21/22/23` 本卡仅在**新 opt-in 分支**使用（`S3_23`/`S3_24` 实测 20、21；22/23 代码存在但未触发实测）。与 `build --install` 路径的组合、以及 `guard-check` 子命令的完整退出码矩阵未逐一实测。

## U-W43-13 · S1 修订尚未合入 W38

见 `DISAGREE.md D-W43-2` / 差距表 G-13。`s1_revision/` 与 `APPLY.md` 是补丁 + 副本，**W38 目录未被修改**（纪律要求）。是否合入由 Lead 决定。

## U-W43-14 · 结论口径

再次声明：**82/82 PASS 只证离线文件层/计划层断言**，不证：
- 引擎行为正确 / 真机行为等价；
- 守卫已默认具备；
- B 线已完成。

安装态 / 执行态 / 行为态三态证据属 S4/S5。
