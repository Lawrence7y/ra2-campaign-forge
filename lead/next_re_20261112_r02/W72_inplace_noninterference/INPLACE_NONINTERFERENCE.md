# W72 · inplace 非干扰性补缺口 · `INPLACE_NONINTERFERENCE.md`

> 执行者 **Hy4**（W72，**不是 Lead**）｜卡目录 `lead\next_re_20261112_r02\W72_inplace_noninterference\`
> `STARTED.txt` 在**读任何文件之前**写入：`2026-11-14T01:14:10.8569520+08:00`（ISO + `Hy4` + `lock per trip`）；`HEARTBEAT.txt` 手动逐阶段更新（01:14 / 01:24 / 01:33 / 01:37 / 01:41 / 01:43）。
> 离线窗口 01:14–01:25（工具/沙箱/脚本，不占锁）；真机窗口 **01:25:44–01:40:49**（4 趟，约 15 分钟）；收尾 01:42:35。全程约 29 分钟，在 130 分钟时间盒内。
> **Lead 只看落盘产物**：本文所有数值可回对 `out\*.ndjson` / `out\*_result.json` / `out\*_map_check.json` / `out\B?_inplace_proof.json` / `out\screen_*.png` / `out\cmd_*.log` / `out\ini_diff.json` / `out\c_audit_B_arm.json` / `out\b_compare_v2.json` / `REAL_DIR_PROOF.txt`。
> 依据：`work\criteria_frozen\tool_b_stats_v2.py`（W68b/Hy4 权威版，sha `B419959A…`，**零改动**）、`work\criteria_frozen\CRITERIA_SPEC_V2.md`（sha `7364E700…`）、`work\criteria_frozen\tool_c_writeaudit.py`（W62，逐字节副本）。**判据权威性锚在卡内副本的内容指纹，不锚在 W68 根目录路径**（`work\criteria_frozen\SHA256_PROOF.json`）。采集层 `tools\w72_collect.py` 是 W69 采集器的**本卡派生副本**（路径重定向、`owner=w72`、inplace 构建/断言），**未直接调用别卡脚本**。

---

## 0 · 一句话结论（严格口径）

`[本次实测]` 用**未修改**的 FROZEN V2 工具 `tool_b_stats_v2.py --compare` 对本卡新采集的四趟数据判定：

> **`verdict = SAME_DISTRIBUTION`**（`reason=within_noise_band`，`out\b_compare_v2.json`，工具 exit 0）。

**口径声明（照写）**：`SAME_DISTRIBUTION` 只能表述为：

> **「在 V2 判据、该场景、该观测量集合下，未检出 inplace 改写 `BATTLEMD.INI` 所导致的行为分布差异」**。

- **不写**「B 线等价性成立」，**不写**「inplace 无影响」，**不写**「等价性成立」。
- **不签发**任何等价/不等价结论；签发权在 Lead。本卡只交付「原始产物 + 退出码 + 判据逐字输出」。
- **必须写明离散侧退化**（§6 限制 1）：五个离散字段在本场景全部是单值 ⇒ `TVD≡0`、`p≡1`，**判别力全在连续量（帧时序）**，不得拿「离散 0 差异」当强度（`REVIEW\LEAD_VERIFY_W68B.md` §7；W68b/GLM 两版共同自评）。

---

## 1 · 覆盖缺口与设计（Lead 已定，不重新论证）

| 项 | W65/W69 的 B 线 | 产品路线 | 本卡 W72 |
|---|---|---|---|
| 装包方式 | **append**：新增 `BATTLEMD98.INI`，`[SOV1]` 原样不动 | **inplace**：改写官方散装 `BATTLEMD.INI`（W60 实现、W63/W70 真机三关链贯通） | **inplace** |
| 两臂同图手段 | 不改写 `[SOV1]` ⇒ 天然同为 `SOV01UMD.MAP` | `Scenario=` 指向新战役图 | 让 inplace **把 `[SOV1] Scenario=` 改写成官方自己那张图** |

**自变量隔离（本卡核心）**：

- **A 臂**：沙箱不装包 ⇒ 官方 `[SOV1] Scenario=SOV01umd.MAP` 天然指向官方苏联第一关。
- **B 臂**：沙箱装 **v15 inplace 包**，但 `Scenario=SOV01UMD.MAP`（就地改写，**引擎按文件名大小写不敏感匹配，加载的仍是同一张官方图**）。
- ⇒ 两臂**玩同一张图**；被隔离出来的自变量是「**`BATTLEMD.INI` 被 inplace 机制改写过（`.bak` 在位、清单记录 `original_sha256`）**」。
- ⇒ 这把「改写这个官方文件本身是否会扰动行为」从 W65/W69 的 append 结论之外单独隔离出来。

**成败前提（先核）**：四趟 `Scen+0x125C` 必须都是 `SOV01UMD.MAP`。本卡在**进图时 + 每一行 NDJSON + 采样后**三处都做了硬断言（不符即 `RuntimeError` 使本趟失败），实测四趟全部通过（§4）。

**两臂同一起点（离线统一处置，不占锁）**：
1. `sandbox_base` = `ra2youli` 只读字节副本（647 文件 / 1,989,215,270 B）。
2. 用 v15 `uninstall --json` 统一清掉真目录既存旧 v0.3 包（`ra2forge_install.json` / `BATTLEMD98.INI` 453 B），`verify` 报 `manifest_present=false`，两臂一致。
3. 移除真目录既存的**无主孤儿** `BATTLEMD.INI.ra2forge.bak`（241 B，W27 期诊断备份）—— **仅从沙箱副本移除**，否则 `inplace_preflight` 以 exit 34 `INPLACE_BACKUP_ORPHAN` 拒绝；字节副本留证于 `work\orphan_bak_backup\`，`out\orphan_bak_handling.json`。**`ra2youli` 从未写入**。
4. 断言 `sandbox_base\BATTLEMD.INI` == bundled 官方样板 sha `7e40691a…`（2733 B）。

**包构造**：`designs\w72_design.json`（2 张 inert 地图）+ `designs\w72_feature_set.json`（`battlemd.mode=inplace`, `scenario=SOV01UMD.MAP`, `maps=sideload` + `mix=repack` 满足 K6/K7/K8 耦合，`csf=off`, `mapselmd=off`）→ `v15 build --feature-set` exit 0。包内含 `BATTLEMD.INI`、**不含** `BATTLEMD98.INI`（inplace 模式隔离，`RI.inplace_requested()` 判定成立）。

> **诚实说明（不掩盖）**：v15 `builder` 对任何 design 都会无条件产出 `*.MAP` + `expandmd98.mix`，`install.package_files()` 也会把它们复制进游戏目录。因此 B 臂相对 A 臂在文件系统层面**还多了** `W72M1.MAP` / `W72M2.MAP` / `expandmd98.mix` / `ra2forge_install.json` / `.seal` / `.bak`。这些是**惰性包产物**：`Scenario` 指向官方图，包内地图永不加载；且与 W65/W69 append 包的同类产物属同一类，W69 已在同一观测量集合上判 `SAME_DISTRIBUTION`。所以「唯一自变量」是**行为层面**的隔离，不是文件系统字节层面的绝对唯一。详见 `DISAGREE.md` D1 / `UNKNOWNS.md` U2。

---

## 2 · 实际 INI diff（1 行，逐字节）

`out\ini_diff.json`、`out\BATTLEMD.INI.before` / `.after`、`out\cmd_prep_build_v15_inplace.log`：

| 项 | 改写前（bundled 官方样板 / 真目录） | 改写后（包内 `BATTLEMD.INI`） |
|---|---|---|
| 字节数 | **2733 B** | **2733 B** |
| SHA-256 | `7e40691a3480b1e5ffe6d1cdfccb83f67da4447157607ec3ecb5d2278acf0791` | `919a50b25b2a5d6b8f141bd64a7097c4dec2586905c2afcc0f08c2728647ce1a` |
| 行数 / CRLF | 146 / 145（0 bare LF） | 146 / 145（0 bare LF） |
| **逐行 diff 行数** | — | **1 行** |

```
L55
  - Scenario=SOV01umd.MAP
  + Scenario=SOV01UMD.MAP
```

其余 **145 行逐字节相同**：`[Battles]` 列表、12 个 debug 段、全部注释、`CD=2` / `FinalMovie=` / `Description=DESC:SOV1` 一字未动。

**选了哪种写法、为什么**：任务卡预设「值与原值相同或等价」，并警告若 v15 预检拒绝「改写后值与原值相同」则改用「等价但不同的写法」。本卡**预先采用等价但不同的写法**：`scenario = "SOV01UMD.MAP"`（全大写，即引擎 `Scen+0x125C` 的实测形态）。

- **为什么不用字节完全相同的 `SOV01umd.MAP`**：`[本次读码]` `battlemd_inplace.rewrite_sov1()` 不拒绝幂等（`idempotent` 只记录），`inplace_preflight()` 也不检查 scenario 值；但 `install.py:1386` 的「字节与包内一致但未记账」ADOPT 分支与 `resolve_integration.SECOND_INSTALL_SEMANTICS` 的 `IDEMPOTENT_REPLAY` 语义会让**字节完全相同**的改写走「无写」路径 ⇒ 不生 `.bak`、manifest 不记 `original_sha256`，**C-6 / 自变量都不成立**。所以必须用字节不同、语义等价的写法。
- **等价性依据**：Windows/引擎按文件名大小写不敏感匹配；A 臂官方 `SOV01umd.MAP` 在 W69/W70 实测 `0x125C` 读作 `SOV01UMD.MAP`（`W70\out\T2_OFFICIAL.json` 明确记 `observed_0x125C=SOV01UMD.MAP` / `matches_official_sov1=true`）。本卡四趟 `0x125C` 全部 `SOV01UMD.MAP`（§4），直接实证两臂同图。
- **明说结论范围**：**改写后值与原值不是字节完全相同**（差 1 行大小写），但**引擎加载的地图完全相同（语义等价，引擎不加载差异）**。因此本卡测的是「**写了但内容等价**」，**与「写了不同内容」（例如把 `Scenario` 指向另一张图）是两种情形**，结论范围必须相应收窄（§6 限制 2）。

---

## 3 · C 判据（安装期零越界写入）

`W62_bline_new_criteria\tool_c_writeaudit.py --audit` 的**卡内逐字节副本**（`work\criteria_frozen\tool_c_writeaudit.py`，sha `3C5CBDB7…`），对 **B 臂 inplace 装包生命周期**的三份全树快照离线跑一次（惰性沙箱、不取锁、不启动游戏）：`out\c_audit_{before,after,uninst,declared}.json` → `out\c_audit_B_arm.json` / `out\c_audit_verdict.json`。

`D` **事先由包内容 + 固定引擎白名单构造**（不是从运行时写集反推）：

```
D = {BATTLEMD.INI, BATTLEMD.INI.ra2forge.bak,
     W72M1.MAP, W72M2.MAP, expandmd98.mix,
     ra2forge_install.json, ra2forge_install.json.seal}
inplace = True ; declared_rewrite = ["BATTLEMD.INI"]
```

| 检查 | 结果 |
|---|---|
| `W`（装后写集） | `modified=["BATTLEMD.INI"]`；`added=["BATTLEMD.INI.ra2forge.bak","W72M1.MAP","W72M2.MAP","expandmd98.mix","ra2forge_install.json","ra2forge_install.json.seal"]`；`removed=[]` |
| **C-1 `W ⊆ D`** | **true** |
| **C-2 `out_of_scope_writes`** | **`[]`** |
| **C-3** 受保护文件哈希全等 | **`protected_all_equal=true`**，`protected_touched=[]`（装前 640 个文件逐条留证，见 `c_audit_B_arm.json`） |
| **C-4 / C-5** 卸载逐字节净零 | `restore.equal=true`，`missing=[] residual=[] changed=[]`，`residual_outside_whitelist=[]` |
| **C-6 inplace** | **true**；`bak_present_post_install=true`、`bak_consumed_after_uninstall=true`、`target_sha_restored=true` |
| **`BATTLEMD.INI` 分类** | **`DECLARED-REWRITE (not out-of-scope)`**（`inplace_proof.classified_as`），`declared_rewrite=["BATTLEMD.INI"]`，**不是越界** |
| `.bak` 在位 | **是**；`out\c_audit_bak_proof.json` 实算 `bak_sha256 == official_sha256 == 7e40691a…`（2733 B 官方原字节） |
| **`verdict`** | **PASS**，`failed_checks=[]`，工具 exit **0**（`out\cmd_tool_c_writeaudit_audit.log`） |

> 说明：冻结工具 `--audit` 模式不接受 `bak_bytes_*` 参数，故报告里 `bak_bytes_equal_to_pre_official: null`（工具按 `is not False` 判为通过）；本卡另用 `out\c_audit_bak_proof.json` **实算**字节相等作为独立补证，未改动冻结工具。
> 真机两趟 B1/B2 也各自断言了 `.bak` 在位 + `original_sha256` 等于官方样板 + `post_install_sha256` 与磁盘一致（`out\B?_inplace_proof.json`）。

---

## 4 · 四趟读数（`[本次实测]`，照 W69 口径）

| 趟 | 臂 | 包 | 锁（前→占→放） | 自启 pid | 进图 `0x125C` | 采样行数 | dframe 点 | read_fail | 残留 | 逐字节还原 | 退出码 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A1 | A（不装包） | — | lead→**w72**→lead | 34896 | `SOV01UMD.MAP` | **10,308** | 10,307 | 0 | 0 | `IDENTICAL_TREE=true` | 0 |
| A2 | A（不装包） | — | lead→**w72**→lead | 17788 | `SOV01UMD.MAP` | **10,320** | 10,319 | 0 | 0 | `IDENTICAL_TREE=true` | 0 |
| B1 | B（装 v15 **inplace** 包） | install rc=0 / verify rc=0，`.bak`+`original_sha256` 断言通过 | lead→**w72**→lead | 3188 | `SOV01UMD.MAP` | **10,287** | 10,286 | 0 | 0 | `IDENTICAL_TREE=true` | 0 |
| B2 | B（装 v15 **inplace** 包） | install rc=0 / verify rc=0，`.bak`+`original_sha256` 断言通过 | lead→**w72**→lead | 3372 | `SOV01UMD.MAP` | **10,301** | 10,300 | 0 | 0 | `IDENTICAL_TREE=true` | 0 |

- **四趟均 ≥ 8000 点**（实测 10,287–10,320 行/趟），全部 `errors=[]`。合并臂 A = 20,628 行 / 20,627 dframe 点，B = 20,588 行 / 20,587 dframe 点（`n_a` / `n_b` 见 `b_compare_v2.json`）。**未截断、未补齐、未重采样、未事后调阈值、未重跑凑数**。
- **同图成败前提已核**：四趟 `out\<tag>_map_check.json` 的 `distinct_map_names` 均为 `{"SOV01UMD.MAP": <全部行>}`，`all_rows_expected=true`；`after_badge_counters` / `counters_at_ingame` / `counters_after_sampling` 亦全为 `SOV01UMD.MAP`。⇒ **两臂确实同图，比较有效**。
- **入口与 W55b/W63/W65/W69 完全一致**：主菜单 `GUI:SinglePlayer` → `GUI:NewCampaign` → `GUI:CampaignMenu` → 屏幕坐标 **(210, 285) 苏联徽章** → 进第一关。四趟 `stage_idx=0` / `end_of_game=0` / `skip_map_select=0` / `battle_idx=1` 全程恒定。
- **采样**：6 ms cadence、每趟 75 s 墙钟，四趟同一（`out\cadence.json`）；`t` 为实测单调时间，V2 工具只用 `frame` 差分。
- **采集字段与 W69 全同**：`frame` ← `[0xA8ED84]`；`Scen* = *(DWORD*)0xA8B230`；`map_name` ← `Scen+0x125C`（260 B C 串）；`stage_idx` ← `+0x35A0`(WORD)；`end_of_game` ← `+0x34AC`(BYTE)；`skip_map_select` ← `+0x34B0`(BYTE)；`battle_idx` ← `+0x34CC`(DWORD)；`ui_controls` ← 可见控件 id 集合（`EnumWindows/EnumChildWindows`）。全部 `ReadProcessMemory(PROCESS_VM_READ|PROCESS_QUERY_INFORMATION)` 只读。
- 每趟 2 张截图（战役菜单 + 局内），共 8 张；每趟记录 pid / 锁 / 退出码于 `out\<tag>_result.json`、`out\trip_<tag>.stdout.txt`、`out\w72_run.ndjson`。

### 4.1 帧时序描述统计（`out\w72_descriptive_stats.json`）

`dframe` = 相邻 `frame` 一阶差分；6 ms 采样下 `dframe ∈ {0,1}`（≈77% 为 0 / ≈23% 为 1）。

| 趟 | frame 首..末 | Δframe |
|---|---|---|
| A1 | 48..2391 | 2343 |
| A2 | 47..2391 | 2344 |
| B1 | 48..2391 | 2343 |
| B2 | 47..2390 | 2343 |

合并臂 `Q_A=Q_B=[0,0,0,0,1]`、`delta_Q=0.0`；`cv_A=143.7401` / `cv_B=143.6620`（各含 1 个拼接边界伪差，两臂对称存在，与 FROZEN 工具自检 `_merge()` 语义一致，本卡未做任何剔除）。补充复算：`N_ks_arm_A=0.00016744402131241287`、`N_ks_arm_B=0.0003096111407908664`、`D_ks_cross_arm_recomputed=0.00039292067959084687`、`J_ui=1.0`。**权威判定仍以 `out\b_compare_v2.json` 为准。**

---

## 5 · V2 gate 原句 + 判定

工具：`out\b_compare_v2.json` 由**未修改**的 `work\criteria_frozen\tool_b_stats_v2.py`（W68b 权威版 `B-W68B-V2-1`，sha `B419959A…`）产出：

```bash
python work\criteria_frozen\tool_b_stats_v2.py --compare ^
  --arm-a out\A_merged.ndjson --arm-b out\B_merged.ndjson ^
  --noise-a1 out\A1.ndjson --noise-a2 out\A2.ndjson ^
  --noise-b1 out\B1.ndjson --noise-b2 out\B2.ndjson ^
  --out out\b_compare_v2.json
```

`COMPARE_V2_EXIT=0`（`out\b_compare_v2.exit.txt`）。合并臂 `n_a=20627` / `n_b=20587`（未截断、未补齐）。

### 5.1 权威 gate 原句（逐字抄录，`work\criteria_frozen\CRITERIA_SPEC_V2.md:89-99`）

```
| 序 | 条件 | 输出 |
|---|---|---|
| B-0 | `n_A < n_min` 或 `n_B < n_min`，或同臂重复数 < `n_noise_min`，或字段缺失/无法解析 | `UNDETERMINABLE(reason=insufficient_sample)` |
| B-1 | `N_ks > N_max` **或** `∃f: N_disc(f) > N_max` | `UNDETERMINABLE(reason=noise_band_unstable)` |
| B-2 | `∃f: shift_detected(f)` **或** `J < theta_ui` | `SHIFT_DETECTED(reason=discrete_or_ui_mismatch)` |
| B-3 | `D_ks <= max(N_ks, D_floor)` **且** `p >= alpha` | `SAME_DISTRIBUTION(reason=within_noise_band)` |
| B-4 | `D_ks > N_ks * k_ratio` **且** `p < alpha` | `SHIFT_DETECTED(reason=ks_beyond_noise)` |
| B-5 | 其余 | `UNDETERMINABLE(reason=grey_zone)` |

> 与 FROZEN §2.4 的差异**仅**：B-1 增加对离散噪声带的同款 `N_max` 检查（复用 `N_max`，不新增阈值）；B-2 把「多重集不等」换成 §2.3 的逐字段检验结论。B-0/B-3/B-4/B-5 与输出词表逐字不变。
> `SAME_DISTRIBUTION` 的准确含义仍是「**在本判据、本观测量、本样本量下未检出分布差异**」，**不是**"行为等价已成立"，**更不是**"B 线等价性已成立"。
```

常量表（§3，**一律未改动**）：`n_min=30`、`n_noise_min=2`、`N_max=0.30`、`alpha=0.05`、`k_ratio=2.0`、`D_floor=0.05`、`perm_iters=2000`、`seed=20261113`、`theta_ui=0.95`、`qs=[0.10,0.25,0.50,0.75,0.90]` —— `b_compare_v2.json` 的 `spec` 字典原样回显。

### 5.2 工具输出判定句（`b_compare_v2.json` 的 `detail` 字段，**原句**）

```
D_ks=0.000393 <= max(N_ks=0.000167, D_floor=0.05) and p=0.923538 >= alpha
```

### 5.3 逐字段与连续腿（`[本次实测]`）

| 量 | 实测值 | 冻结常量/规则 |
|---|---|---|
| `n_a` / `n_b`（dframe 点） | 20627 / 20587 | `n_min=30` ⇒ B-0 不命中 |
| 同臂重复数 | A=2, B=2 | `n_noise_min=2` ⇒ B-0 不命中 |
| **`N_ks`（A 臂同臂 KS 噪声）** | **0.00016744402131241287** | `N_max=0.30` ⇒ **B-1 不命中** |
| `D_ks` | 0.00039292067959084687 | — |
| `p_value` | 0.9235382308845578 | `perm_iters=2000`, `seed=20261113`, `alpha=0.05` |
| `J_ui` | 1.0 | `theta_ui=0.95` |
| `delta_Q` | 0.0 | `Q_A=Q_B=[0,0,0,0,1]` |
| `max_N_disc` | 0.0 | `discrete_shifted_fields=[]`、`discrete_unstable_fields=[]` |
| **`verdict`** | **`SAME_DISTRIBUTION`** | `reason=within_noise_band` |

五字段 `map_name` / `stage_idx` / `end_of_game` / `skip_map_select` / `battle_idx` 在 A∪B 合并池均为**单值**（`SOV01UMD.MAP` / `0` / `0` / `0` / `1`）⇒ `T_f_tvd=0.0`、`D_disc=0.0`、`N_disc=0.0`、`p_value=1.0`、`p_method=exact_single_category_degeneracy`、逐字段 `no_shift_detected`。

判定顺序复核（不擅自改）：B-0 未命中 → B-1 未命中（`N_ks ≪ 0.30`，`discrete_unstable=[]`）→ B-2 未命中（`shifted=[]`、`J=1.0 ≥ 0.95`）→ **B-3 命中 `SAME_DISTRIBUTION`** 并短路返回；B-4/B-5 未求值。本卡不代为求值、不改写判定。

工具自检（`out\v2_selftest.json`，**同一份字节不变的权威 V2 副本**）：`V2_SELFTEST_PASS=True`（`ce_A=SAME_DISTRIBUTION` / `ce_B=SHIFT_DETECTED` / `ce_C=SAME_DISTRIBUTION`），exit 0。**合成对照，不是真机结论。**（第一次自检因冻结工具把合成 fixture 解析为「工具文件同目录 `EVIDENCE\ce_*`」而报 `FileNotFoundError` exit 1；本卡把 W68 的 `ce_A/ce_B/ce_C` **NDJSON fixture 数据**（非脚本）复制到卡内 `work\criteria_frozen\EVIDENCE\` 后重跑同一工具得 exit 0。`--compare` 走显式路径参数，**与该自检失败无关**，第一次即 exit 0。两次尝试均如实记录在 `out\compare_summary.json` 的 `selftest_attempts`。）

---

## 6 · 三条限制（结论口径）

1. **离散侧退化，判别力全在连续量。** 本场景（官方苏联第一关、不动 UI）五个离散字段全部是单值 ⇒ `TVD≡0`、`p≡1`（`p_method=exact_single_category_degeneracy`，精确而非近似），**离散侧读数几乎无信息量**，只说明「值集与占比相同」，**不能反推行为等价**。真正判别力落在连续量（帧时序 `dframe`）上，**不得拿「离散字段 0 差异」当强度**。这是 W68b / GLM 两版的共同自评（`REVIEW\LEAD_VERIFY_W68B.md` §7、§8 末段；`CRITERIA_SPEC_V2.md` §6 第 2 条 `常量字段上检验退化`）。本卡 `N_ks=0.000167`、`D_ks=0.000393`、`p=0.923538` 全部来自连续腿。

2. **本卡测的是「写了但内容等价」，不是「写了不同内容」。** `[SOV1] Scenario=` 由 `SOV01umd.MAP` 改写为 `SOV01UMD.MAP` —— **仅大小写差异，引擎按文件名大小写不敏感匹配，加载的地图与原值完全相同（引擎不加载差异）**；四趟 `0x125C` 全为 `SOV01UMD.MAP` 实证两臂同图。因此本卡只回答「**就地改写官方 `BATTLEMD.INI` 这一动作（含 `.bak` 在位、清单记录 `original_sha256`）是否扰动可观测行为分布**」，**不覆盖**「把 `Scenario` 指向另一张图 / 改写不同内容」的情形（那正是 W63/W70 三关链的用途）。**结论范围必须相应收窄**，不得外推到「inplace 改写任意内容都不扰动」。

3. **单一场景 / 单一观测量集合 / 单一时长的未检出，不等于普遍无影响。** 只在「V2 判据、官方苏联第一关、不动 UI、6 ms cadence × 75 s、n≈10,300 行/趟、`frame` + 五离散字段 + 可见控件 id」这一组条件下未检出差异；**未覆盖**其它战役场景、长时程/稀有事件、UI 交互、存档/网络等非本观测量集合、以及未被观测的内部状态。另外 B 臂相对 A 臂在文件系统层面还多了惰性包产物（`W72M1.MAP` / `W72M2.MAP` / `expandmd98.mix` / manifest / seal / `.bak`，见 §1 诚实说明），故「唯一自变量」是行为层面的隔离，不是字节层面的绝对唯一；`DISAGREE.md` D1、`UNKNOWNS.md` U2/U3 登记。

---

## 7 · 真机纪律（逐项可回对）

| 红线 | 本卡 |
|---|---|
| **一趟一锁**（`w72`→`lead`），不跨趟长期持锁 | 每趟前读 `.game_instance.lock`，要求 `owner=lead` 且 `gamemd` 活体 0，否则等待；取锁写 `owner=w72`；**每趟结束（finally，无论成败）**写回 `owner=lead` + 状态。`out\w72_run.ndjson` 记录 4 组 `lock_before → lock_claimed → lock_released`；趟间锁文件始终 `owner=lead`。收尾复核 `owner=lead`（`REAL_DIR_PROOF.txt`）。**离线 prep/audit/compare/finalize 全程未取锁**。 |
| **不写 `ra2youli`** | 只作 `robocopy` 只读源 + 全树哈希目标；PRE/POST 全树 **647 文件 / 1,989,215,270 B**，added/removed/modified **全 0**，`IDENTICAL_TREE=True` → `REAL_DIR_PROOF.txt`。五个锚点（`gamemd.exe` / `ddraw.dll` / `RA2MD.INI` / `BATTLEMD.INI` / `ra2md.mix`）PRE==POST 逐条实算。 |
| **不 blanket `taskkill`** | `pre_launch_guard` 每趟确认 0 个 gamemd；只关闭本趟 WMI 自启 pid（34896 / 17788 / 3188 / 3372）：`WM_CLOSE` → `taskkill /PID <own>` → `/F /PID <own>`；`residual_own_pid=0`，收尾 `gamemd residual=[]`（`out\finalize.json`）。 |
| **启动前沙箱可写配置字节副本 + 哈希，收尾逐字节还原并实算自证** | 每趟启动前字节复制**全部根级文件**（A 418 / B 424 个）+ 全树哈希 manifest；收尾按 PRE/POST 差异逐文件还原并**重算全树哈希**，四趟 `IDENTICAL_TREE=true`（游戏仅改动 `SOV01UMD.sav`，已从 `out\pristine_<tag>` 字节副本还原）。见 `out\restore_proof_*.json`。 |
| **只读采集** | `OpenProcess(PROCESS_VM_READ|PROCESS_QUERY_INFORMATION)` + `ReadProcessMemory`；`EnumWindows/EnumChildWindows`；`PIL.ImageGrab`。**无写内存 / 断点 / 挂线程 / 注入 / 改 exe**（`gamemd.exe` PRE=POST `73201cc0…`）。 |
| **桌面预检** | 每趟 WMI 启动后即刻 `step0_desktop_precheck`：`WinSta0\Default`、EnumWindows 365 / 20 可见、ImageGrab OK 2560×1440，`pass=true`。 |
| **不得直接调用别卡脚本** | `w69_collect.py` / `w69_report.py` / 两个 FROZEN 工具**全部先逐字节复制到本卡**（`work\criteria_frozen\SHA256_PROOF.json` 逐文件 sha 自证；权威 V2 工具/规格与 Lead 签发值逐位一致），本卡只运行自己的副本；`ra2forge`(v15) 作为工具链按任务卡授权调用。 |
| **只写本卡目录 / git 只读** | 所有产物在 `W72_inplace_noninterference\`；无 commit、未改他卡交付物、未改 v15 工具链。 |

### 7.1 权威 V2 工件一致性（并发覆盖防护）

本会话 W68 根目录已被并发覆盖过两次。本卡**先复制到卡内再核对 sha**（Lead `W69\INSTRUCTION_FROM_LEAD.md` §3 通用规则）：

| 工件 | Lead 签发 sha256 | 卡内副本 | 一致 |
|---|---|---|---|
| `CRITERIA_SPEC_V2.md` | `7364E700B07B188135998FBCDF751724759397952F893E85EE9D773FB14F7270` | 同 | ✅ |
| `tool_b_stats_v2.py` | `B419959A4F4CFA357CFD84F24341BE613FFEF1556E1FEB8DCAEF84DF94DC6FBE` | 同 | ✅ |

**运行时只用 `work\criteria_frozen\` 的副本**，根目录不可信。GLM 版（`B-W68-2`，sha `62B0C275…`）**未进入判定路径**。

---

## 8 · 分级标注与产物清单

- `[本次实测]`：四趟逐趟状态/点数/pid/锁/残留/还原；四趟 `0x125C` 全图核验；1 行 INI diff 与两侧哈希；C 审计 PASS（含 C-1..C-6、DECLARED-REWRITE 分类、`.bak` 字节相等）；`b_compare_v2.json` 全部数值；V2 自检 PASS；真目录 PRE/POST 全树零改动；桌面预检；install/verify/uninstall 退出码。
- `[本次读码]`：`battlemd_inplace.rewrite_sov1()` / `resolve_integration.inplace_preflight()` / `builder.py` inplace 分支 / `feature_subset` K1–K12 / `install.py` ADOPT 分支 / `CRITERIA_SPEC_V2.md` §2.3/§2.4/§3/§6 / `tool_c_writeaudit.py` / W63 `w63_offline.py` / W69 采集骨架。
- `[静态推断]`：大小写差异不改变引擎加载的地图（已被四趟 `0x125C` 实测印证）；合并臂拼接边界伪差对 KS 影响量级 ≈1/n；包内地图惰性不加载。
- `[转引]`：W65/W69 append 路线与 `SAME_DISTRIBUTION`；W63/W70 inplace 三关链；W68b/GLM 两版离散退化自评；W70 `T2_OFFICIAL.json` 的 `0x125C` 读数；W62 常量表。
- `[待运行验证]`：见 `UNKNOWNS.md`。

**`out\` 主要产物**：`A1/A2/B1/B2.ndjson`（+ `A_merged` / `B_merged`）、`<tag>_result.json` / `<tag>_map_check.json` / `B?_inplace_proof.json`、8 张 `screen_*.png`、`cmd_*.log`（21 份，含 install / verify / uninstall / build / audit / compare）、`ini_diff.json` + `BATTLEMD.INI.before/.after`、`c_audit_{before,after,uninst,declared}.json` / `c_audit_B_arm.json` / `c_audit_verdict.json` / `c_audit_bak_proof.json`、`b_compare_v2.json` + `.exit.txt` + `.stdout.txt`、`b_compare_v2` 相关 `compare_summary.json`、`v2_selftest.json`、`w72_descriptive_stats.json`、`restore_proof_*.json`、`real_pre.json` / `finalize.json`、`cadence.json`、`w72_run.ndjson`。
