# W60_battlemd_inplace · INPLACE_MODE.md

> 卡号 **W60** ｜ 执行者 **Hy4** ｜ 基座 `W46_resolve_integration\ra2forge_patched_v14\` → 产出 `W60_battlemd_inplace\ra2forge_patched_v15\`
> **结论口径（红线）：离线实现 + 离线回归通过。** 真机验收是后续卡的事，本报告**不**写"就地改写已在真机验证"。
> **I launched 0 / attached 0，观察到的 gamemd 属其他卡、未触碰**；全程未启动 `gamemd.exe`、未 attach、未取 `.game_instance.lock`（W55b 可能持锁跑真机，本卡不介入）。
> 分级标注：`[本次实测]` / `[本次读码]` / `[静态推断]` / `[转引]` / `[待运行验证]`。
> 写域：只写本卡目录；`git` 只读、不 commit；未就地改 v10–v14、未改仓库 `ra2forge/`、未写 `ra2youli/`、未动 W21–W59 的交付物。

---

## 0 · 裁决与范围

- `[转引]` Lead `REVIEW\LEAD_RULING_D5_2_INPLACE_UNFREEZE.md`：战役菜单无法新增第 3 个徽章（`W32` + 门控 `[0xA8F7AD]` 无静态写入者）⇒ 唯一通道是「借官方入口 id」；两条子路线中 **(b) `BATTLEMD98.INI` 追加同 id 段有跨文件重复 ID**（胜者由 `FindFirstFileA` 枚举顺序决定 + MIX 回退分支可能翻盘覆写）⇒ 静默失效、不具工程可行性；**(a) 就地改写散装官方 `BATTLEMD.INI` 无重复 id 且 W27 的 D2/D3 已真机进图成功**（`REVIEW\LEAD_VERIFY_W37.md` §2.3）。裁决采纳 (a)，**解冻 D5.2**，原 `BATTLEMD_INPLACE_REFUSED` / exit 25 门由本卡为 `battlemd.mode == "inplace"` 打开。
- `[本次读码]` v14 的 D5.2 产物在 `resolve_integration.py:check_inplace_mode()`（原 L295）/ `run_resolve()`（原 L332）/ `MODE_SUPPORT`（原 L87）= DEFERRED；`feature_subset.shipped()` 早已把 `inplace` 映射为 `BATTLEMD.INI`（`feature_subset.py:49-50`），`MODE_RESERVATIONS` 明确列出 4 文件 `change_surface` 与 `plan_layer_slot`（`BATTLEMD.INI` / REPLACE / `BATTLEMD.INI.ra2forge.bak` / RESTORE）。v14 的 REPLACE/RESTORE、备份、manifest sha256、`verify` per-file 对账、orphan 规则**本来就具备**，本卡是接通而非重写。
- 本卡交付的是**能力**，不是**真机结论**。

---

## 1 · 设计

### 1.1 通道与 shipped 语义
`[本次读码]` `feature_subset.shipped(F)` **未改**：`battlemd.mode=="inplace"` ⇒ `shipped() = {"BATTLEMD.INI"}`（+ 开着 maps/mix 时的 `*.MAP` / `expandmd98.mix`）。`resolve()` 对在场文件给出 `BATTLEMD.INI = REPLACE`（`original_absent=False`、backup slot `BATTLEMD.INI.ra2forge.bak`、uninstall `RESTORE`）。这与 `MODE_RESERVATIONS.plan_layer_slot` 完全一致，本卡只是让**写入侧**消费它。

### 1.2 "就地改写"的精确语义（为什么不是"追加一个新文件"）
1. **build**：从 bundled 官方样板 `data/BATTLEMD.OFFICIAL.INI`（W27 `BATTLEMD.INI.asbuilt`，2733 B）用 `rewrite_sov1()` **逐字节改写 `[SOV1]` 段**，产出包内唯一的 `BATTLEMD.INI`（2730 B）。**不生成 `BATTLEMD98.INI`**（路线 (b)），因此包内没有第二个 battle-list 文件 ⇒ 无跨文件重复 id。
2. **install**：复用 v14 `_write_step()` 的 REPLACE 原语 —— 先把 game dir 的官方 `BATTLEMD.INI` 逐字节复制到 `BATTLEMD.INI.ra2forge.bak`，再把改写后字节落到**同一路径**。不新增任何 `BATTLEMD*.INI` 文件，不产生重复 id。
3. **uninstall**：v14 RESTORE 从 `.bak` 逐字节还原；W60 追加 `original_sha256` 校验，不一致 ⇒ `INPLACE_RESTORE_MISMATCH` 抛错（非零退出、不静默）。
4. **verify**：`entry["sha256"]` 就是 post-install SHA-256；v14 `verify` 的 per-file 磁盘 sha 对账天然检测 drift（INPLACE3 实测）。

`[静态推断]` 引擎侧：散装官方文件仍在原位、仍被 `FindFirstFileA("BATTLEMD*.INI")` 枚举到，只是 `[SOV1] Scenario=` 指向我方地图；W37 §2.2 (B) 的 MIX 回退翻盘风险因此不触发（散装文件在场）。此段为 `[转引]`+`[静态推断]`，**未经本卡真机验证**。

### 1.3 模式隔离（路线 (b) 不会被误当 inplace）
`RI.inplace_requested(plan)` 判定条件：**`shipped()` 含 `BATTLEMD.INI` 且不含 `BATTLEMD98.INI`**。append 模式的 `shipped()` 是 `BATTLEMD98.INI`，`BATTLEMD.INI` 行是 `LEAVE` ⇒ 永远不进入任何 inplace 分支（`build_effective_switches` 的 baseline、`package_files(battle_ini=)`、inplace 专属预检、manifest 新字段）。INPLACE6 实测。

### 1.4 解冻了什么 / 没削弱什么
**解冻（仅 `battlemd.mode=="inplace"` 通道）**：`check_inplace_mode()` 的 exit 25 拒绝；`MODE_SUPPORT/MODE_RESERVATIONS` 状态；`build_effective_switches` 的 build baseline；builder 的 battle-list 产物；`package_files` 的 loose 文件名；通用 content-conflict 对**该目标文件**的适用性（由更强的 `inplace_preflight` 取代）。

**保持原语义（实测）**：版本守卫（`--version-guard` opt-in 路径未动）、K1/K2/K3/K4/K5–K12（`feature_subset.py` 逐字节未改）、seal、`content-conflict` 预检（除上述目标行的特指替换；其它文件规则逐字未改）、`plan/actual` 对账、orphan/legacy 规则、`verify.py`（逐字节未改）。INPLACE5 实测 K2 仍硬拒绝（exit 26）；S4_8f 实测 `verify.py`/`feature_subset.py`/`cli.py`/guard/data 全部与 v14 逐字节相同。

### 1.5 新增的 inplace 专属守卫（**加严**，非削弱）
| 守卫 | 退出码 / reason | 触发 |
|---|---|---|
| bundled 官方样板缺失/被改 | 32 `INPLACE_BASELINE_MISSING` | `check_inplace_mode()` |
| game dir 的 `BATTLEMD.INI` 缺失或 ≠ 官方样板 SHA | 33 `INPLACE_OFFICIAL_MISMATCH` | `inplace_preflight()` |
| `.bak` 已存在但 manifest 未拥有 `BATTLEMD.INI` | 34 `INPLACE_BACKUP_ORPHAN` | `inplace_preflight()` |
| 卸载还原后 SHA ≠ manifest 记录的原 SHA | 非零（OSError `INPLACE_RESTORE_MISMATCH`） | `uninstall()` restore |

全部在**第一个文件系统写之前**（除还原校验），拒绝时零写。

---

## 2 · 改动清单（v15 相对 v14，`文件:行`）

| 文件 | 行 | 改动 |
|---|---|---|
| `ra2forge/battlemd_inplace.py` | 新增全文件（`official_bytes` 28 / `is_official` 41 / `diff_lines` 83 / `rewrite_sov1` 102） | 纯字节级 `[SOV1]` 改写器：定位段、显式写全 4 键、缺键补齐、保 CRLF/编码/其它段、幂等、逐行 diff 报告 |
| `ra2forge/data/BATTLEMD.OFFICIAL.INI` | 新增 2733 B | 官方样板，逐字节复制自 `W27_campaign_live\out\BATTLEMD.INI.asbuilt`（`[本次实测]` sha `7e40691a…`） |
| `ra2forge/resolve_integration.py` | 16-19 | docstring：DEFERRED → SUPPORTED |
| | 65-68 / 79-82 | 新退出码 32–35 与 `EXIT_CODES` 映射 |
| | 96 | `MODE_SUPPORT['battlemd']['inplace'] = "SUPPORTED"` |
| | 101-143 | `MODE_RESERVATIONS` 改 `IMPLEMENTED`（authority/reason/activation_gate/change_surface + `implementation{}`），保留既有键名兼容 `--resolve` CLI |
| | 317-345 | `check_inplace_mode()` 不再 raise 25，改为只读能力预检（32） |
| | 351-363 | `run_resolve()` docstring 更新；`check_inplace_mode()` 仍为唯一入口 |
| | 738-757 | `build_effective_switches()` baseline：inplace ⇒ `BATTLEMD.INI`，否则 `BATTLEMD98.INI` |
| | 928-990 | 新增 `inplace_requested()` / `inplace_preflight()` |
| `ra2forge/builder.py` | 127-129 | 计算 `inplace` 判定 |
| | 185-208 | inplace 分支：写 `out/BATTLEMD.INI`（改后全文），跳过 `BATTLEMD98.INI` 与 `_verify_battle_file`；else 分支保持原逻辑 |
| | 1089-1095 | `_write_build_report` artifact 行按实际存在的 battle 文件取（默认路径逐字节不变） |
| `ra2forge/install.py` | 760-790 | `package_files(..., battle_ini=None)`：可选 loose 文件名，默认 `BATTLEMD98.INI` ⇒ 旧调用点不变 |
| | 1223-1224 | 按 plan 传 `battle_ini`；计算 `inplace_target` |
| | 1377 / 1465 | step 增 `dest_size`（原文件字节数） |
| | 1412-1432 | 通用 content-conflict 对 **inplace 目标文件**豁免，由 `inplace_preflight` 取代；其它文件规则逐字未改 |
| | 2014 / 2026 | `inplace_report` 初始化 + 在**任何 strict/risk 门之前**跑 `RI.inplace_preflight()` |
| | 2208-2219 | manifest entry 增 `original_sha256` / `original_size_bytes` / `post_install_sha256` / `inplace_rewrite{}` |
| | 2282 | manifest 顶层嵌入 `inplace_rewrite` 预检报告 |
| | 2670-2680 | 卸载 RESTORE 后校验 SHA == `original_sha256`，不一致抛 `INPLACE_RESTORE_MISMATCH` |
| | 3105 | 新增 `_inplace_battle_ini(plan)` 模式隔离 helper |
| `ra2forge/verify.py` / `feature_subset.py` / `cli.py` / `s3_contract.py` / `csf.py` / `mapselmd.py` / `version_guard.py` / 其它 11 文件 / `data/` | **未改** | `[本次实测]` S4_8f 逐字节比对通过 |
| `regress_dlc_v15.py` | 由 v14 复制 + 4 处 re-point | `W43_ROOT_NAME`、`V12_ROOT→v15`、注册 `S5_CASES`、summary 文案 |
| `s4_cases.py` | `bind_s4` 加 `V14_REF_ROOT`；`case_S4_7` 全替换；`case_S4_8e/f` 改 v14→v15 delta | 适配 D5.2 解冻；**用例数不变** |
| `s5_cases.py` | 新增全文件 | 6 条新用例（见 §5.3） |
| `s3_cases.py` | 逐字节副本 | 未改 |

---

## 3 · 逐字节安全论证（`[本次实测]`）

官方样板 = `W27_campaign_live\out\BATTLEMD.INI.asbuilt`：

| 项 | 改写前 | 改写后 |
|---|---|---|
| 字节数 | **2,733 B** | **2,730 B** |
| SHA-256 | `7e40691a3480b1e5…` | `369592f06371a2e7…`（**与 W27 `BATTLEMD.INI.D2_sov1_ech01` 完全一致**） |
| 行（split keepends） | 146 | 146 |
| CRLF 行尾 | 145 | **145**（0 bare LF） |
| 编码 / BOM | ASCII 字节 / 无 BOM | 不变 |
| **逐行 diff 行数** | — | **1 行** |

唯一差异（`out\BATTLEMD.INI.diff.txt`）：

```
L55
  - b'Scenario=SOV01umd.MAP\r\n'
  + b'Scenario=ECH01.MAP\r\n'
```

- 其余 **145 行全部逐字节相同**：`[Battles]` 列表、12 个 debug 段、全部注释、`CD=2` / `FinalMovie=` / `Description=DESC:SOV1` 一字不动。
- `[本次实测]` `rewrite_sov1()` **显式写全** `CD` / `Scenario` / `FinalMovie` / `Description`（W37 §3 要求规避 `Read_INI` 缺失键行为未定谳）。该官方样板 4 键**原本齐全**，故 `keys_added = []`（报告原文写明"补了哪些键：无；官方已含 4 键"）。若输入段缺键，实现会在段内补齐并写入 `report.keys_added`。
- **幂等** `[本次实测]` `out\IDEMPOTENCE_CHECK.json`：对已改写的 2730 B 再跑 2 次，字节与 SHA 三遍完全一致（`IDEMPOTENT`）。安装层面的二次安装由 v14 `IDEMPOTENT_REPLAY`（零写）保障；孤立 `.bak` 则由 exit 34 **明确拒绝**（INPLACE4），不会二次破坏备份。
- **备份 = 原文件字节**：INPLACE1 实测 `.bak` 与官方 2733 B 原文件 `==`；INPLACE2 实测卸载还原后 `back == original` 且 SHA 三方相等（`disk / recorded original_sha256 / official`）。
- **逐字节还原校验**：uninstall RESTORE 后若 SHA ≠ `manifest.original_sha256` ⇒ `INPLACE_RESTORE_MISMATCH` 抛错、非零退出、不静默。

产物：`out\BATTLEMD.INI.before` / `.after` / `.diff.txt` / `.hashes.json` / `INPLACE_REWRITE_REPORT.json` / `IDEMPOTENCE_CHECK.json`。

---

## 4 · 高风险能力：备份丢失会怎样 / 如何检测备份被删

> 就地改写会**改动官方文件**，这是本卡最高风险能力。既有安全下限（`USER_AUTHORIZATION` §3.6 配置基线 + 逐字节还原）直接适用。

### 4.1 若 `BATTLEMD.INI.ra2forge.bak` 丢失会怎样
`[静态推断]` + `[本次读码]`（v14 `install.py` restore 分支）：
1. **uninstall 无法逐字节还原**。v14 在备份缺失时走 `warnings.append("backup ... is missing - <name> was not restored")` 并保留记录（`refused=True` 分支），**官方 `BATTLEMD.INI` 会停留在我们改写后的 2730 B 版本**。
2. 游戏里 `[SOV1] Scenario=` 仍指向我方战役，官方苏军第一关无法从磁盘自动恢复；`verify` 只会看到"已安装文件的 sha 仍匹配"（因为文件没再被改），**不会**把"回不去官方"报成错误。
3. manifest 里虽记录 `original_sha256` / `original_size_bytes`，但**没有原始字节** ⇒ 不能凭 SHA 重建文件。恢复需从游戏安装介质 / 其它未改副本重新取回 2,733 B 官方文件（或按 §3 的 diff 反向改回 L55）。这是**不可逆损失**（除非有外部副本）。
4. W60 的缓解：卸载时若发生还原，会**先校验 SHA**；但备份本身缺失时是 v14 的警告路径，不是静默成功 —— 报告里会明确写出 "was not restored"。

### 4.2 如何检测备份被删
`[本次实测]` 现有可执行的离线检测手段（**不依赖真机**）：
1. **manifest ↔ 磁盘比对**（最直接）：读取 `game\ra2forge_install.json` 中 `files[]` 里 `name=="BATTLEMD.INI"` 的 `backup` 字段与 `original_sha256`，然后：
   ```
   bak = game / "BATTLEMD.INI.ra2forge.bak"
   assert bak.is_file()                        # 缺失 => 报警
   assert sha256(bak.read_bytes()) == manifest_entry["original_sha256"]   # 被换 => 报警
   ```
   `[静态推断]` 这正是 W60 新增 `original_sha256` 字段的用途；`out\BATTLEMD.INI.before` 也提供了可离线对照的官方字节。
2. **再安装时的前向门**：`inplace_preflight()` 检查 `.bak` 是否存在、manifest 是否 owns 目标文件；孤儿 `.bak` ⇒ exit 34（INPLACE4 实测），官方文件被换 ⇒ exit 33，bundled 样板缺失 ⇒ exit 32。
3. **`verify` drift 检测**（INPLACE3 实测）：安装后有人手改 `BATTLEMD.INI` ⇒ `verify` 非零退出并报 changed。注意它检测的是**已安装文件漂移**，不是备份是否存在。
4. **orphan 规则**：`verify.py` 的 `_ORPHAN_MARKERS` 含 `.ra2forge.bak`，未由 manifest 记账的备份会被列为 orphan；`install` 的 `_plan_orphans` 在升级时清理我们自己的旧备份 ⇒ `.bak` **已纳入清单与升级清理规则，不会变孤儿**（功能清单第 6 条）。

`[待运行验证]` **诚实缺口**：W60 **没有**把"备份存在性"新增为 `verify` 子命令的断言（原因见 `DISAGREE.md` §3）。因此"备份被删"目前靠上述 1/2/4 检测，`verify` 本身只保证漂移检测。此条列入 `UNKNOWNS.md` U5。

---

## 5 · 回归结果（`[本次实测]`，完整命令行与退出码见 `out\COMMANDS.txt`）

### 5.1 既有全量套件基线（v14 原样，跑通后才动手）
```
cd ...\W60_battlemd_inplace\baseline_v14\W46_resolve_integration
python -B -X utf8 regress_dlc_v14.py
```
**用例数 90 / 通过 90 / 断言 807 passed 0 failed / 退出码 0**（`out\baseline_stdout.txt` 末行 `BASELINE_EXITCODE=0`）。
`[本次实测]` 该副本只改了 `REPO_ROOT` 一行（补偿目录深度），**用例体逐字节未改**；所有写入落在本卡 `baseline_v14\` 内，未污染 W46 卡交付物。

### 5.2 新基座全量
```
cd ...\W60_battlemd_inplace
python -B -X utf8 regress_dlc_v15.py
```
**用例数 96 / 通过 96 / 断言 835 passed 0 failed / 退出码 0**（`out\full_stdout.txt` 末行 `FULL_EXITCODE=0`）。
90 = 既有（含 S4_7/S4_8 的断言适配，用例数不变）+ **6 条新增** ⇒ 总数变化**只**来自新增用例。既有 90 例在新基座上**全绿**。

### 5.3 新增 6 例逐条结果（`s5_cases.py`）
| 用例 | 覆盖 | 断言 | 结果 |
|---|---|---|---|
| `INPLACE1` | install ⇒ 生 `.bak`、改写目标段、manifest 记录原 SHA-256 | 7 | **PASS** |
| `INPLACE2` | uninstall ⇒ **逐字节还原**（实测哈希相等） | 6 | **PASS** |
| `INPLACE3` | 安装后手改 INI ⇒ `verify` 报 drift 且退出码非零 | 5 | **PASS** |
| `INPLACE4` | 已有 `.bak` 再装 ⇒ **明确拒绝**（`INPLACE_BACKUP_ORPHAN` exit 34、零写） | 3 | **PASS** |
| `INPLACE5` | `battlemd.mode=off` + `csf` 开 ⇒ **K2 仍硬拒绝**（exit 26 `RESOLVE_COUPLING_REFUSED`） | 4 | **PASS** |
| `INPLACE6` | `BATTLEMD98.INI` 追加路线 (b) ⇒ **不被误当 inplace**（官方文件逐字节不变、无 `.bak`、manifest 无 `inplace_rewrite`） | 5 | **PASS** |

子集最终跑：`python -B -X utf8 regress_dlc_v15.py INPLACE1 … INPLACE6 S4_7 S4_8` ⇒ 8/8、47 断言、exit 0。

### 5.4 幂等 / 逐字节（`out\` 产物，非回归用例）
`[本次实测]` 2733 → 2730 B、1 行 diff、145 CRLF、三遍改写一致（详见 §3）。

---

## 6 · 未覆盖项 / 仍然 DEFERRED

1. **真机验收未做**（红线）。未启动 `gamemd.exe`、未 attach、未取锁；W55b 可能在跑真机，本卡只做离线。结论只能是"离线实现 + 离线回归通过"。
2. **备份存在性未并入 `verify` 断言**（§4.2、UNKNOWNS U5）。
3. **官方文件变体未知**：目标机 `BATTLEMD.INI` 若 ≠ bundled 2733 B 样板，exit 33 拒绝；合法变体集合 `[待运行验证]`。
4. **inplace 专属的 `IDEMPOTENT_REPLAY` / `SUBSET_UPGRADE` / `.bak` 升级清理**沿用 v14 语义并被继承用例覆盖，未用 inplace plan 单独复测（UNKNOWNS U6/U7）。
5. **引擎加载顺序 / MIX 回退 / `Description` 标签 / `Read_INI` 缺失键**：全部 `[转引]` W37，未重新反汇编、未真机验证。
6. **路线 (b) 未按裁决删除**：append 能力保留（仅模式隔离），未动 `ra2youli` 旧包 v0.3，未改 `PENDING_DECISIONS.md`（归属方合入）。
7. **非官方文件合并策略**：第三方改过的官方 `BATTLEMD.INI` 一律拒绝（exit 33），无 merge。
8. 详见 `UNKNOWNS.md` / `DISAGREE.md`。

---

## 7 · 分级标注速查
- `[本次实测]`：90/90 基线、96/96 全量、6 条新用例、2733→2730 B、1 行 diff、145 CRLF、幂等三遍、备份/还原 SHA 相等、K2/模式隔离/孤儿拒绝退出码、`verify` drift 非零、S4_8f 源码逐字节比对。
- `[本次读码]`：v14 DEFERRED 门位置、`shipped()`/REPLACE/RESTORE/manifest/verify/orphan 既有机制、W27 asbuilt 逐行结构。
- `[静态推断]`：REPLACE 到同路径 = 就地改写、散装文件在场使 MIX 回退不触发、备份丢失后果、备份被删的检测方式。
- `[转引]`：Lead D5.2 解冻裁决、W37 §2.3 两条子路线、W32 菜单封死、W27 D2/D3 真机证据（**非本卡实测**）、`arch atlas` 枚举/回退、`Description` CSF 标签语义。
- `[待运行验证]`：真机验收、官方变体、Description 解析、备份存在性自动检测、inplace 专属升级/重放、引擎加载顺序。