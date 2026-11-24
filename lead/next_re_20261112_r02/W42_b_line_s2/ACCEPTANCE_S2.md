# ACCEPTANCE_S2.md · W42 / S2 · 可机检断言设计

> 卡：`W42_b_line_s2`｜**只做「能被机检」的检查设计，不做实现**。
> 下列 **17 条**（B1–B17）是交给 **S3+ 回归脚本**执行的规格。除 B17（结构自检，本卡已跑）外全部 `[待运行验证]`；本卡**未运行**任何一条涉及文件投放 / 卸载 / 构建的断言，未写生产代码、未接线、未新增回归脚本。
> 术语 / 分级 / 红线同 `FEATURE_SUBSET_CONTRACT.md` §0。输入与期望的机器可读形态见 `FEATURE_SUBSET.schema.json` `$defs/acceptanceCase` 与 `EVIDENCE\fixtures.json`。

## 0 · 执行前置（所有断言共用）`[静态推断]`

| 项 | 规约 |
|---|---|
| 隔离载体 | 所有 fixture 复制到**本卡/S3+ 自己的写域**；**禁止**指向真实 `ra2youli`、禁止写仓库 `ra2forge/`、禁止动 `W21`–`W41`。 |
| 游戏进程 | 全程 `gamemd.exe` / `game.exe` 进程数 **0**；沙箱内 `gamemd.exe` 只能是 inert 占位（W34 `UNCOVERED.md` U9 `[转引]`），不得启动游戏、不得 attach。 |
| 零写判定 | 对夹具游戏目录做 `sha_tree()` 前后逐字节快照（含隐藏文件、`.ra2forge-stage.<hex>`、`.ra2forge.bak`、`.seal`）；**字节级相同**才算零写入。只比文件名/退出码不够。 |
| `guard_state` | 断言用的 `guard_state` 是**注入的夹具值**（`KNOWN_GOOD`/`UNKNOWN`/`MISMATCH`），不是真机实算；`BASELINE.json` 条目是夹具，`adjudicated=true`、`provenance.is_clean_retail_gold=false`（W38-S1 §6.1）。 |
| 结论口径 | 每条「期望」必须可机检（退出码 / 报告字段 / 字节快照 / JSON schema 断言），不写「应该」「看起来」。**不得**据此写「行为正确」「回归全绿 ⇒ 引擎行为正确」（RE-N09 L287）。 |
| 动作记号 | `C`=CREATE / `R`=REPLACE / `L`=LEAVE；「卸载后」列 = `DELETE` / `RESTORE` / `NOOP`。 |

### 0.1 标准沙箱初始态（夹具常量）

| 代号 | `present_files` | `absent_files` | `guard_state` |
|---|---|---|---|
| **S0** | `BATTLEMD.INI`（`official_loose`, 2,733 B，`[转引·题面本次实测]`） | `BATTLEMD98.INI`, `*.MAP`×n, `expandmd98.mix`, `ra2md.csf`, `MAPSELMD.INI` | `KNOWN_GOOD` |
| **S1'** | S0 ∪ `expandmd98.mix`（`user_file`） | 其余同 S0 减去该 mix | `KNOWN_GOOD` |
| **S2'** | S0 ∪ `MAPSELMD.INI`（`user_file`, 非我方登记） | 其余同 S0 减去该 INI | `KNOWN_GOOD` |
| **SU** | 同 S0 | 同 S0 | `UNKNOWN` |
| **SM** | 同 S0 | 同 S0 | `MISMATCH` |

> S0 的三条「原本没有散装 `MAPSELMD.INI` / `ra2md.csf`、有散装官方 `BATTLEMD.INI` 2,733 B」是题面已签发背景 `[转引·本次实测]`，本卡**未独立复核真机**，只用作夹具常量。其余文件名在真机上的初始态未实测（`UNCOVERED.md` U-W42-6）——断言用**显式夹具态**，不臆造真机。

### 0.2 标准 feature-set（夹具常量）

| 代号 | `features`（`schema_version="w42-s2-1"`、`kind="feature_set"`） |
|---|---|
| **F0** | 5 个 feature 全 `off` |
| **F1** | `maps=sideload{map_files:[A.MAP,B.MAP]}`, `battlemd=append{ids:[...],description_ref:"raw"}`, `mix=repack{source_map_set:[A.MAP,B.MAP]}`, `csf=off`, `mapselmd=off` （G1 最小可运行包） |
| **F2** | F1 + `csf=clone_append{base:"official_full_clone",labels:["RA2F:00000001"],official_label_count:5211}`, 且 `battlemd.description_ref="csf_label"` （G2） |
| **F3** | F1 + `mapselmd=clone_append{base:"official_full_clone",stages:[S1,S2],official_stage_count:14,official_size_bytes:5573,bundled_official_sha256:"074ccccd…"}` （G3） |
| **F4** | F2 ∪ F3（全开，5 面齐全） |

---

## B1 · 全关（默认态）：零写、逐字节兼容 `[待运行验证]`

- **输入**：`F0` + `S0`，`guard_state=KNOWN_GOOD`。
- **期望**：① `coupling_passed=true`；② `FILE_UNIVERSE` 8 行全部 `L`、`original_absent=false`、`uninstall.action=NOOP`、`remove_backup_slot=false`；③ `install_write_set=[]`、`backup_set=[]`、`uninstall_delete_set=[]`、`uninstall_restore_set=[]`、`digest_inputs=[]`；④ `effective_game_dir_write_bytes=0`；⑤ 构建产物与「关闭开关的 v11」逐字节相同（W36 §4-S2 验收 #2 `[转引]`）；⑥ 游戏目录前后 `sha_tree()` 完全一致。
- **失败信息**：`B1 FAIL: all-off feature set wrote or planned a write; files=<...> bytes=<n> — default must be byte-identical to v10/v11`

## B2 · G1 最小可运行包：CREATE ⇒ 卸载 DELETE `[待运行验证]`

- **输入**：`F1` + `S0`。
- **期望**：`shipped={A.MAP,B.MAP,expandmd98.mix,BATTLEMD98.INI}`；`A.MAP/B.MAP/expandmd98.mix/BATTLEMD98.INI` = `C` 且 `original_absent=true`；`BATTLEMD.INI`/`ra2md.csf`/`MAPSELMD.INI` = `L`；`backup_set=[]`；`uninstall_delete_set` = 上述 4 文件 + 清单 + seal；`uninstall_restore_set=[]`；**卸载后目录逐字节 == S0**（无残留 `.bak`、无残留我方 INI/MIX/MAP）；`digest_inputs` 恰 4 行。
- **失败信息**：`B2 FAIL: G1 CREATE files not deleted on uninstall (over-restore?); residual=<names> original_absent=<flags>`

## B3 · REPLACE ⇒ 备份 ⇒ 卸载 RESTORE `[待运行验证]`

- **输入**：`F1` + `S1'`（`expandmd98.mix` PRESENT `user_file`）。
- **期望**：`expandmd98.mix` = `R`、`original_absent=false`、`backup_slot="expandmd98.mix.ra2forge.bak"`、`uninstall.action=RESTORE`；其余 3 个 = `C`；`backup_set` 恰 1 个槽；卸载后 `expandmd98.mix` **逐字节还原为 S1' 的用户字节**且槽被删除，其余 C 文件被 DELETE；目录 == S1'。
- **失败信息**：`B3 FAIL: REPLACE not restored byte-exact from .ra2forge.bak; got_sha=<h> want_sha=<h> slot_left=<bool>`

## B4 · `battlemd:inplace`：官方 `BATTLEMD.INI` 走 REPLACE/RESTORE `[待运行验证]`

- **输入**：`F1` 但 `battlemd.mode="inplace"` + `S0`。
- **期望**：`BATTLEMD.INI` = `R`（PRESENT 2,733 B）→ 备份 `BATTLEMD.INI.ra2forge.bak` → 卸载 RESTORE 且还原后 SHA == 官方 2,733 B 原值；`BATTLEMD98.INI` = `L`（因为本组合不产它）；地图/MIX = `C`；卸载后 == S0。
- **失败信息**：`B4 FAIL: inplace battlemd did not REPLACE+RESTORE official BATTLEMD.INI; action=<a> restored_sha=<h>`

## B5 · G2 CSF 组：`ra2md.csf` 必须进子集且 `Description=` 改标签 `[待运行验证]`

- **输入**：`F2` + `S0`。
- **期望**：`shipped` = F1 的 4 个 ∪ `ra2md.csf`；`ra2md.csf` = `C`、`original_absent=true`、卸载 `DELETE`；`BATTLEMD98.INI` = `C` 但 `new_sha` 与 F1 的**不同**（`builder.py:131-137` 把 `Description=` 改为 `RA2F:<8hex>` `[本次读码]`）；`csf_patch.json` 出现在包目录产物；卸载后 == S0。**契约要求 `ra2md.csf` 进清单/seal/备份/卸载**（v11 现状不具备，见契约 §9）。
- **失败信息**：`B5 FAIL: csf enabled but ra2md.csf absent from shipped/manifest, or INI Description= not rebound; in_shipped=<b> in_manifest=<b> ini_sha_changed=<b>`

## B6 · G3 战役推进组：`MAPSELMD.INI` CREATE ⇒ DELETE `[待运行验证]`

- **输入**：`F3` + `S0`。
- **期望**：`MAPSELMD.INI` = `C`、`original_absent=true`、卸载 `DELETE`；`stages[]` 每个 `Scenario` ∈ `{A.MAP,B.MAP}`；包目录追加 `MAPSELMD.INI`；卸载后 == S0。
- **失败信息**：`B6 FAIL: mapselmd stage not wired into file subset or not deleted on uninstall; unresolved_scenarios=<...>`

## B7 · 全开 F4：完整 5 面清单 + 元数据联动 `[待运行验证]`

- **输入**：`F4` + `S0`。
- **期望**：`shipped` = `{A.MAP,B.MAP,expandmd98.mix,BATTLEMD98.INI,ra2md.csf,MAPSELMD.INI}`；`BATTLEMD.INI` = `L`（唯一 LEAVE 的非元数据行）；其余全 `C`；`install_write_set` 6 个 + 清单 + seal；`backup_set=[]`；`digest_inputs` 恰 6 行；`feature_set_id(F4) ≠ feature_set_id(F1)`；卸载后 == S0。
- **失败信息**：`B7 FAIL: all-on subset incomplete; shipped=<...> digest_lines=<n> feature_set_id=<id>`

---

## B8 · 【负例 1｜题面】最小 CSF（只有我方标签）必须被拒绝 `[待运行验证]`

- **输入**：`F2` 变体 → `csf.mode="clone_append"`、`csf.base="minimal"`、`csf.labels=["RA2F:00000001"]`、`csf.official_label_count=1`（即产出的 `ra2md.csf` 只含我方 1 个标签）+ `S0`。
- **期望**：① `coupling_passed=false`，② `reason_codes` 含 `MINIMAL_CSF_REFUSED`；③ `install_write_set=[]`、`effective_game_dir_write_bytes=0`；④ `ra2md.csf` **零写**（目录前后 `sha_tree()` 一致）；⑤ 失败说明必须点名「官方全文克隆 + 5,211 标签」判据，不得笼统写「CSF 错误」；⑥ `guard_state` 仍为 `KNOWN_GOOD`（不被 S2 拒绝改变）。
- **依据**：W30 `CSF_CAPABILITY.md:41-45`、W34 D4「最小文件会让官方全挂」`[转引]`；契约 §5 K4。**v11 现状不拒绝**（`csf.py:442-466` `create_if_missing=True`，`builder.py:431-437` `[本次读码]`）⇒ 本断言是**契约新增门禁**，S3 实现前必然 FAIL。
- **失败信息**：`B8 FAIL: minimal CSF (only our labels) was accepted; base=<v> official_label_count=<n> writes=<bytes> — expected MINIMAL_CSF_REFUSED + zero writes`

## B9 · 【负例 2｜题面】`MAPSELMD` 非完整克隆必须被拒绝 `[待运行验证]`

- **输入**：`F3` 变体 → `mapselmd.mode="clone_append"`、`mapselmd.base="partial_or_minimal"`、`official_stage_count=2`、`official_size_bytes=400`（只含我方追加 stages 的最小文件）+ `S0`。
- **期望**：① `coupling_passed=false`；② `reason_codes` 含 `MAPSELMD_NOT_FULL_CLONE`；③ `install_write_set=[]`、`effective_game_dir_write_bytes=0`；④ `MAPSELMD.INI` 零写；⑤ 说明点名 14 官方阶段 / 5,573 B / bundled SHA `074ccccd…` / 1..7 键 / `Scenario=`；⑥ `guard_state` 不变。
- **依据**：W34 D4；`mapselmd.validate_official_base()` `mapselmd.py:142-184`、`OFFICIAL_SIZE=5573`、`:60-62` `[本次读码]`；契约 §5 K5。**该门禁 v11 构建期已具备**，本断言验证它也被接入 S2 的 feature 层。
- **失败信息**：`B9 FAIL: partial/minimal MAPSELMD.INI accepted; stages=<n> size=<b> — expected MAPSELMD_NOT_FULL_CLONE + zero writes`

## B10 · 【负例 3｜题面】开启 `csf` 但未开启其耦合项必须被拒绝 `[待运行验证]`

- **输入**：三个子例分别跑：
  - (a) `csf=clone_append`（合法完整克隆）+ `battlemd=off` + `S0`；
  - (b) `csf=clone_append` + `battlemd=append{description_ref:"raw"}` + `S0`；
  - (c) `battlemd=append{description_ref:"csf_label"}` + `csf=off` + `S0`。
- **期望**：三例全部 `coupling_passed=false`、零写、目录 `sha_tree()` 一致；`reason_codes` 分别为 `CSF_WITHOUT_BATTLEMD` / `CSF_LABEL_UNBOUND` / `CSF_LABEL_UNBOUND`；说明必须点名 W36 §3.3.2「`BATTLEMD98.INI` × `ra2md.csf` = 强」及 W30 `MISSING:RA2F:...` 后果；`guard_state` 不变。
- **依据**：题面「强耦合对 CSF↔`BATTLEMD98.INI`」；契约 §5 K2/K3；`builder.py:131-137` `[本次读码]`。
- **失败信息**：`B10 FAIL: csf/battlemd strong pair split was accepted; variant=<a|b|c> codes=<...> writes=<bytes> — expected REJECT_AND_EXPLAIN`

## B11 · 互斥：`battlemd.mode` 同时 `append`+`inplace` 必须被拒绝 `[待运行验证]`

- **输入**：`F1` 变体 → `battlemd.mode=["append","inplace"]`（schema 允许该输入形态）+ `S0`。
- **期望**：`coupling_passed=false`、`reason_codes` 含 `BATTLEMD_MODE_CONFLICT`、零写；说明「单值枚举，两模式不可同时」；`guard_state` 不变。
- **失败信息**：`B11 FAIL: dual battlemd modes accepted; mode=<...> — expected BATTLEMD_MODE_CONFLICT`

## B12 · 强耦合：地图↔MIX 拆开必须被拒绝 `[待运行验证]`

- **输入**：(a) `maps=sideload, mix=off`；(b) `maps=off, mix=repack`；(c) `maps=sideload, mix=repack` 但 `mix.source_map_set=[A.MAP]` ≠ `maps.map_files=[A.MAP,B.MAP]`。均 `+ S0`。
- **期望**：全拒；`reason_codes` 分别 `MAPS_WITHOUT_MIX` / `MIX_WITHOUT_MAPS` / `MIX_MAP_SET_MISMATCH`；零写；说明点名 `builder.py:143-147` `_verify_mix_contents` 恰含地图 0 INI `[本次读码]`。
- **失败信息**：`B12 FAIL: map/mix strong pair split accepted; variant=<a|b|c> codes=<...>`

## B13 · 强耦合：地图↔`MAPSELMD` 拆开 / `Scenario` 悬空必须被拒绝 `[待运行验证]`

- **输入**：(a) `mapselmd=clone_append`（合法完整克隆）+ `maps=off`；(b) `mapselmd` 的 `stages[].Scenario="GHOST.MAP"` ∉ `maps.map_files`。均 `+ S0`。
- **期望**：全拒；`reason_codes` = `MAPSELMD_WITHOUT_MAPS` / `MAPSELMD_SCENARIO_UNRESOLVED`；零写；说明点名 W34 `MAPSELMD_SPEC.md:150-158` `[转引]`。
- **失败信息**：`B13 FAIL: map/mapselmd strong pair split or unresolved Scenario accepted; variant=<a|b> codes=<...>`

## B14 · 与 S1 组合：`UNKNOWN`/`MISMATCH` 下 feature 全开也必须零写 `[待运行验证]`

- **输入**：`F4`（全开）+ `SU`（`guard_state=UNKNOWN`）；再跑 `F4` + `SM`（`MISMATCH`）。
- **期望**：两次均 ① `coupling_passed=true`（F4 本身合法，计划集合照常产出）；② `fileSubsetPlan.files[]` **完整保留** 5 面计划（供 `guard_report.json` 记录「计划但被拒」）；③ `wrote_game_dir=false`；④ `effective_game_dir_write_bytes=0`；⑤ 游戏目录前后 `sha_tree()` 完全一致（含 stage 临时名、`.bak`、清单、seal）；⑥ 报告带 `guard_state=UNKNOWN`/`MISMATCH` 与 S1 的 `reason_codes`；⑦ **feature 未改变 `guard_state`**。
- **依据**：W38-S1 §4 跨态不变式、§6.1 不变式 1、`ACCEPTANCE.md` A1/A3 `[转引]`；契约 §6 C1/C3。
- **失败信息**：`B14 FAIL: feature set overrode guard verdict or wrote game dir under UNKNOWN/MISMATCH; state=<s> bytes=<n> planned_files=<n>`

## B15 · E2b 路径归属：`csf-out` 落在游戏目录内 ⇒ 交 S1 `E1` 全流程 `[待运行验证]`

- **输入**：`F2` + `csf_out_path="<S0.game_dir>\ra2md.csf"`（realpath 落在游戏目录内）+ `SU`。
- **期望**：`files[]` 里该写点 `write_entry` 标为 **`E1`**（不是 `E2b`）；`reason_codes` 含 `CSF_OUT_INSIDE_GAME_DIR_DEFERRED_TO_S1`；零写；说明引用 W38-S1 §1.2 路径归属规则 / `ACCEPTANCE.md` A7；`KNOWN_GOOD` 夹具下则必须先完成 L1 重算 + C12 才允许写。
- **失败信息**：`B15 FAIL: csf-out inside game dir not reclassified to E1; entry=<e> state=<s> writes=<n>`

## B16 · G4 全局事务：子集变化 ⇒ digest/seal/清单/备份/卸载同步变化 `[待运行验证]`

- **输入**：同一沙箱 `S0`，依次跑 `F1`、`F2`、`F3`、`F4`，各取 `digest_inputs` / `feature_set_id` / seal 摘要 / `backup_set` / `uninstall_delete_set`。
- **期望**：① 四者 `digest_inputs` 两两不等；② `feature_set_id` 两两不等且都写进 manifest；③ 每次的 `install_write_set` / `backup_set` / `uninstall_delete_set` / `uninstall_restore_set` 与 `files[]` **派生一致**（不得手填不一致）；④ 只改一个文件而其余元数据不变 ⇒ `G4_METADATA_DESYNC` 拒绝；⑤ 每轮卸载后目录 == S0。
- **依据**：W36 §3.3.3 G4、`install.py:682-695`/`:658-679` `[本次读码]`；契约 §7。
- **失败信息**：`B16 FAIL: subset change did not propagate to digest/seal/manifest/backup/uninstall; f1_digest=<h> f2_digest=<h> manifest_has_fsid=<b>`

## B17 · 契约机器结构自检（本卡已跑的静态断言）`[本次实测]` / `[待运行验证]`（S3 引用）

- **输入**：`FEATURE_SUBSET.schema.json`、`EVIDENCE\coupling_rules.json`、`EVIDENCE\fixtures.json`（均由本卡 `EVIDENCE\s2_shape_check.py` **只读**加载）。
- **期望**：① schema 是合法 JSON、`$defs` 齐全、`oneOf` 覆盖 5 类实例；② `$defs/guardState` 枚举 == W38-S1 的 4 态、`$defs/writeEntry` == `E1`–`E6`；③ `s2ReasonCode` 与 W38-S1 `guardVerdict.reason_codes` **无交集**（正交）；④ `coupling_rules.json` 恰 12 条 K1–K12、每条 `on_violation="REJECT_AND_EXPLAIN"`、含 `MINIMAL_CSF_REFUSED` / `MAPSELMD_NOT_FULL_CLONE` / `CSF_WITHOUT_BATTLEMD` 三个题面负例码；⑤ `fileAction` 恰 `CREATE/REPLACE/LEAVE` 三值，`plannedFile` 的 CREATE⇒`original_absent=true`+`DELETE`、REPLACE⇒`RESTORE`、LEAVE⇒`NOOP` 三条不变式存在；⑥ `fileSubsetPlan` 的 `guard_state≠KNOWN_GOOD ⇒ effective_game_dir_write_bytes=0` 不变式存在；⑦ **schema 层不强制耦合**（`featureSet` 无语义 `allOf`），保证 3 个负例输入可表达；⑧ 全部 fixture 实例通过形状校验。
- **本卡实测**：`EVIDENCE\s2_shape_check.py` 输出 `TOTAL FAILURES: 0`、exit 0（见 `EVIDENCE\s2_shape_check.stdout.txt` / `exit_codes.txt`）。**该自检只证「本卡规格自洽」，不证任何未来 resolver / 守卫实现**。
- **失败信息**：`B17 FAIL: contract schema/coupling-rule invariant violated; check=<name> expected=<v> got=<v>`

---

## 覆盖矩阵（断言 ↔ 契约 ↔ 上游）

| 断言 | 契约章节 | 上游 |
|---|---|---|
| B1 | §2.2(b)/§4.1 F0 | W36 §4-S2 验收 #2、W30/W34「关闭时逐字节相同」 |
| B2/B3/B4 | §3.3 CREATE/REPLACE/LEAVE、§4.1 F1/F5/F6 | W21 `original_absent`、W36 §3.4.1(a) |
| B5/B6/B7 | §4.1 F2/F3/F4、§9 差距表 | W30 G-4、W34 D4 |
| **B8** | §5 K4 | **题面负例 1** + W30/W34 D4 |
| **B9** | §5 K5 | **题面负例 2** + W34 D4 |
| **B10** | §5 K2/K3 | **题面负例 3** + W36 §3.3.2 强耦合、G2 |
| B11 | §2.2(c)/§5 K1 | 题面「`inplace` 与 `append` 不可同时」 |
| B12/B13 | §5 K6–K10 | W36 §3.3.2 强耦合三格、G1/G3 |
| B14/B15 | §6 C1/C3/C5、§4.3 | W38-S1 §4 决策表 / A1 / A3 / A7 / R9 |
| B16 | §7 | W36 §3.3.3 G4、`install.py:682-695` |
| B17 | §2.3/§5/§6 | W38-S1 §6.1 / `ACCEPTANCE.md` A6 |

> **再次声明**：B1–B16 是**断言设计**，本卡未执行；B17 的自检只针对本卡 JSON 规格与自身隔离，不证明任何游戏行为、不证明 resolver 已实现、不证明版本守卫已具备。安装态/执行态/行为态三态证据属 S4/S5。
