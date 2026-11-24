# W69 · B 线第一次正式 V2 判定 · `LIVE_RESULT_V2.md`

> 执行者 **Hy4**（W69，**不是 Lead**）｜卡目录 `lead\next_re_20261112_r02\W69_bline_v2_collect\`
> `STARTED.txt` 在**读任何文件之前**写入：`2026-11-14T00:45:27+08:00`（ISO + `Hy4` + `lock per trip`）；`HEARTBEAT.txt` 每 10 分钟后台心跳（`pwsh-109ffea366044d1e`）+ 每阶段手动追加，实测 `TICK=1 @00:58:38`、`TICK=2 @01:08:38`。
> 真机窗口：`2026-11-14T00:53:08+08:00 ~ 01:07:58+08:00`（4 趟，约 15 分钟）；收尾 `01:09:28`。全程约 24 分钟，在 140 分钟时间盒内，**未触发**「90 分钟只完成 A 臂两趟」的降级条件。
> **Lead 只看落盘产物**：本文所有数值可回对 `out\*.ndjson` / `out\*_result.json` / `out\screen_*.png` / `out\cmd_*.log` / `out\w69_run.ndjson` / `out\b_compare_v2.json`。
> 依据：`W68_criterion_discrete_fix\CRITERIA_SPEC_V2.md`（**FROZEN `2026-11-14T00:33:05.3748807+08:00`，W68b/Hy4 权威版**）、`tool_b_stats_v2.py`（**逐字节副本，零改动**）、`W62_bline_new_criteria\tool_c_writeaudit.py`（逐字节副本，零改动）。采集层 `tools\w69_collect.py` 是 `W65_bline_live_collect\tools\w65_collect.py` 的**本卡派生副本**（路径重定向、`owner=w69`），**未直接调用别卡脚本**。

---

## 0 · 一句话结论（严格口径）

`[本次实测]` **用未修改的 FROZEN V2 工具 `tool_b_stats_v2.py --compare` 对新采集四趟数据判定：`verdict = SAME_DISTRIBUTION`**（`reason=within_noise_band`，`out\b_compare_v2.json`，工具 exit 0）。这是 B 线**第一个有效的正式 V2 判定**。

> **口径声明（必须照写）**：`SAME_DISTRIBUTION` **不等于**「等价性成立」。正确表述：
> **「在 V2 判据、n≈8000/趟、该场景、该观测量集合下，未检出装包导致的行为分布差异」**。
> （任务卡给定名义量 `n≈8000/趟`；**本卡实测每趟 ≈10,200 行，均超过 ≥8000 目标**，见 §1。）
>
> **不得**写「B 线等价性成立」，**不得**写「装包无影响」，**不得**签发任何等价/不等价结论。签发权在 Lead；本卡只交付「原始产物 + 退出码 + 判据逐字输出」。

- 无一趟失败；`errors=[]` / `read_fail=0` / `residual_own_pid=0` / 逐趟 `IDENTICAL_TREE=true` / 四个 `trip.exit.txt` 全为 `0`。
- 同臂噪声 `N_ks` 远小于 `N_max=0.30`，**未**触发 `UNDETERMINABLE(noise_band_unstable)`；**未**截断、**未**补齐、**未**重采样、**未**事后调阈值、**未**重跑凑数。
- 与 W65 的关系：W65 的 `SHIFT_DETECTED` **维持原样**（触发项为采样时长伪差异）；W68 对 W65 数据的 V2 重算**只是诊断性重算、不是结论**；本卡用 V2 **重新采集**给出第一个正式判定。三件事互不覆盖。

---

## 1 · 四趟逐趟状态（`[本次实测]`）

| 趟 | 臂 | 包 | 锁（前→占→放） | 自启 pid | 进图 | 采样行数 | dframe 点 | read_fail | 残留 | 逐字节还原 | 退出码 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A1 | A（不装包） | — | lead→**w69**→lead | 39452 | `SOV01UMD.MAP` | **10,241** | 10,240 | 0 | 0 | `IDENTICAL_TREE=true` | 0 |
| A2 | A（不装包） | — | lead→**w69**→lead | 23400 | `SOV01UMD.MAP` | **10,219** | 10,218 | 0 | 0 | `IDENTICAL_TREE=true` | 0 |
| B1 | B（装 v15 包） | v15 **append**，install rc=0 / verify rc=0 | lead→**w69**→lead | 38140 | `SOV01UMD.MAP` | **10,217** | 10,216 | 0 | 0 | `IDENTICAL_TREE=true` | 0 |
| B2 | B（装 v15 包） | v15 **append**，install rc=0 / verify rc=0 | lead→**w69**→lead | 39596 | `SOV01UMD.MAP` | **10,235** | 10,234 | 0 | 0 | `IDENTICAL_TREE=true` | 0 |

- 四趟均 ≥ 8000 点（实测 10,217–10,241 行/趟）；合并臂 A = 20,460 行 / 20,459 dframe 点，B = 20,452 行 / 20,451 dframe 点（`n_a`/`n_b` 见 `b_compare_v2.json`）。
- **入口与 W55b/W63/W65 完全一致**：主菜单 `GUI:SinglePlayer` → `GUI:NewCampaign` → `GUI:CampaignMenu` → 屏幕坐标 **(210, 285) 苏联徽章** → 进第一关。四趟 `after_badge_counters` / `counters_at_ingame` 全为 `SOV01UMD.MAP` / `stage_idx=0` / `end_of_game=0` / `skip_map_select=0` / `battle_idx=1`。
- **两臂同一干净沙箱起点**：`sandbox_base` = `ra2youli` 只读字节副本 → 用 v15 `uninstall` 统一清掉既存 v0.3（`verify` 报 `manifest_present=false`）→ 每趟各自 `robocopy` 出全新沙箱。
- **B 臂包**：`W60_battlemd_inplace\ra2forge_patched_v15\` 工具链从**与 W65 逐字节相同的** `designs\w69_design.json` 构建 **append 路线**包（仅 `BATTLEMD98.INI` + `W65M1.MAP` / `W65M2.MAP` / `expandmd98.mix`，**无 `BATTLEMD.INI` 就地改写**）。`sandbox_base\BATTLEMD.INI` 中 `[SOV1] Scenario=SOV01umd.MAP` 逐字未变 ⇒ **两臂确实进了同一张官方图**（任务卡「若你认为必须验 inplace，另开卡，别在本卡混」—— 本卡沿用 W65 取舍，见 `DISAGREE.md` D1）。
- **采样**：6 ms cadence、每趟 75 s 墙钟，四趟同一（`out\cadence.json`）；`t` 为实测单调时间，V2 工具只用 `frame` 差分。
- **采集字段与 W65 全同**：`frame` ← `[0xA8ED84]`；`Scen* = *(DWORD*)0xA8B230`；`map_name` ← `Scen+0x125C`（260 B C 串）；`stage_idx` ← `+0x35A0`(WORD)；`end_of_game` ← `+0x34AC`(BYTE)；`skip_map_select` ← `+0x34B0`(BYTE)；`battle_idx` ← `+0x34CC`(DWORD)；`ui_controls` ← 可见控件 id 集合（`EnumWindows/EnumChildWindows`）。全部 `ReadProcessMemory(PROCESS_VM_READ|PROCESS_QUERY_INFORMATION)` 只读。
- **每趟 2 张截图**（战役菜单 + 局内），共 8 张；每趟记录 pid / 锁 / 退出码于 `out\<tag>_result.json`、`out\trip_<tag>.{stdout,exit}.txt`、`out\w69_run.ndjson`。

| 趟 | 战役菜单截图 (SHA-256) | 局内截图 (SHA-256) |
|---|---|---|
| A1 | `screen_A1_campaign_menu.png` `8b9b03b84d559e90…4aca79ec1b` | `screen_A1_ingame.png` `6c15f2b7e36a5fd7…42388d59e2` |
| A2 | `screen_A2_campaign_menu.png` `8b9b03b84d559e90…4aca79ec1b` | `screen_A2_ingame.png` `087125ba9dad5ea1…1f96b40b80e` |
| B1 | `screen_B1_campaign_menu.png` `b27b2319382934b6…41b0660d1e2` | `screen_B1_ingame.png` `02a4e5a9fd77961a…4322bfcd9b93e` |
| B2 | `screen_B2_campaign_menu.png` `b5b13a14b7200306…d7e72b1cb6` | `screen_B2_ingame.png` `f4ae28b963231778…8315e34545` |

（完整 64 位哈希见 `out\w69_run.ndjson` 的 `step=screenshot` 行。A1/A2 菜单截图哈希相同是菜单画面确定性所致，非复制产物。）

---

## 2 · 合并臂与 dframe 描述统计（`[本次实测]`）

`dframe` = 相邻 `frame` 一阶差分；`frame` 为 32 ms 定拍计时器（≈31.25 计数/s）。6 ms 采样下 `dframe ∈ {0,1}`，≈77% 为 0 / ≈23% 为 1。

| 趟 | frame 首..末 | Δframe | P(dframe=1) | Q(p10,p25,p50,p75,p90) | CV |
|---|---|---|---|---|---|
| A1 | 48..2392 | 2344 | 0.2289 | 0,0,0,0,1 | 1.8354 |
| A2 | 48..2392 | 2344 | 0.2294 | 0,0,0,0,1 | 1.8328 |
| B1 | 51..2394 | 2343 | 0.2293 | 0,0,0,0,1 | 1.8331 |
| B2 | 67..2411 | 2344 | 0.2290 | 0,0,0,0,1 | 1.8347 |
| A = A1∪A2 | — | — | 0.2291 | 0,0,0,0,1 | 143.0925 |
| B = B1∪B2 | — | — | 0.2292 | 0,0,0,0,1 | 141.0648 |

- 合并臂各含 **1 个拼接边界伪差**（A1 末帧→A2 首帧、B1→B2），系 `A=A1∪A2` 逐行拼接、`dframe` 跨边界计算的必然产物；两臂各一个、对称存在，与 FROZEN 工具自检 `_merge()` 语义一致，本卡**未做任何剔除**。它解释合并臂 `CV≈143/141` 的异常大值，对 KS 贡献量级 ≈1/20000。
- **行数不等**：A 合并臂 20,460 行 vs B 合并臂 20,452 行（差 8 行）。按旧 v1「值→计数」多重集判等，这 8 行差足以再次触发 `SHIFT_DETECTED(discrete_or_ui_mismatch)`（W65 的失效机理）；**V2 用占比归一化后，同样的行数差不再触发离散腿** —— 这正是 §3 逐字段 `T_f=0 / p=1` 的原因，也是本卡作为「修正后首次正式判定」的意义。

补充量（`out\w69_descriptive_stats.json`，`tools\w69_report.py` 逐字复刻 FROZEN KS 公式，不 import 别卡脚本）：`N_ks_arm_A=0.0004928496281072503`、`N_ks_arm_B=0.0003056703368277125`、`D_ks_cross_arm_recomputed=4.8878244293464976e-05`、`J_ui=1.0`。**权威判定仍以 `out\b_compare_v2.json` 为准。**

---

## 3 · V2 判据逐字段统计（`[本次实测]`，`out\b_compare_v2.json`）

工具：`out\b_compare_v2.json` 由**未修改**的 `tools\tool_b_stats_v2.py`（W68b 权威版，`B-W68B-V2-1`）以下列命令产出：

```bash
python tools\tool_b_stats_v2.py --compare ^
  --arm-a out\A_merged.ndjson --arm-b out\B_merged.ndjson ^
  --noise-a1 out\A1.ndjson --noise-a2 out\A2.ndjson ^
  --noise-b1 out\B1.ndjson --noise-b2 out\B2.ndjson ^
  --out out\b_compare_v2.json
```
`COMPARE_V2_EXIT=0`（`out\b_compare_v2.exit.txt`）。合并臂行数 `n_A_rows=20460`、`n_B_rows=20452`（**未截断、未补齐**）。

### 3.1 每字段占比 / 检验量 / p 值（V2 工具 `discrete_fields` 原样输出）

| 字段 | `p_A`（占比） | `p_B`（占比） | `per_value_delta` | `T_f_tvd` = `D_disc` | `N_disc` | `p_value` | `p_method` | 逐字段 `verdict` |
|---|---|---|---|---|---|---|---|---|
| `map_name` | `{"SOV01UMD.MAP": 1.0}` | `{"SOV01UMD.MAP": 1.0}` | `{"SOV01UMD.MAP": 0.0}` | **0.0** | **0.0** | **1.0** | `exact_single_category_degeneracy` | `no_shift_detected` |
| `stage_idx` | `{"0": 1.0}` | `{"0": 1.0}` | `{"0": 0.0}` | **0.0** | **0.0** | **1.0** | `exact_single_category_degeneracy` | `no_shift_detected` |
| `end_of_game` | `{"0": 1.0}` | `{"0": 1.0}` | `{"0": 0.0}` | **0.0** | **0.0** | **1.0** | `exact_single_category_degeneracy` | `no_shift_detected` |
| `skip_map_select` | `{"0": 1.0}` | `{"0": 1.0}` | `{"0": 0.0}` | **0.0** | **0.0** | **1.0** | `exact_single_category_degeneracy` | `no_shift_detected` |
| `battle_idx` | `{"1": 1.0}` | `{"1": 1.0}` | `{"1": 0.0}` | **0.0** | **0.0** | **1.0** | `exact_single_category_degeneracy` | `no_shift_detected` |

- 每字段 `value_set_A == value_set_B`（`value_sets_equal=true`）；`thresholds_used` 逐字段均为 `{"N_max":0.3,"D_floor":0.05,"alpha":0.05,"perm_iters":2000,"seed":20261113}`。
- `p_method = exact_single_category_degeneracy`：五字段在 A∪B 合并池均为**单值**，任何重分下 `T_perm ≡ T_obs ≡ 0` ⇒ `p_f = 1.0`（**精确**，非近似）。`[静态推断]` 该读数信息量极低，只说明「值集与占比相同」，**不能反推行为等价**（W68 `UNKNOWNS.md §2` 已声明；见本卡 `UNKNOWNS.md` U1）。
- `max_N_disc = 0.0`、`discrete_shifted_fields = []`、`discrete_unstable_fields = []` ⇒ B-1 不命中、B-2 离散腿不命中。

### 3.2 连续腿与总体读数（`[本次实测]`）

| 量 | 实测值 | 冻结常量/规则 |
|---|---|---|
| `n_a` / `n_b`（dframe 点） | 20459 / 20451 | `n_min=30` ⇒ B-0 不命中 |
| 同臂重复数 | A=2, B=2 | `n_noise_min=2` ⇒ B-0 不命中 |
| **`N_ks`（A 臂同臂 KS 噪声）** | **0.0004928496281072503** | `N_max=0.30` ⇒ **B-1 不命中**（噪声带极稳） |
| `N_ks`（B 臂，补充复算） | 0.0003056703368277125 | 同 ≪ 0.30（补充量，非工具字段） |
| `D_ks` | 4.8878244293464976e-05 | — |
| `p_value` | 1.0 | `perm_iters=2000`, `seed=20261113`, `alpha=0.05` |
| `J_ui` | 1.0 | `theta_ui=0.95` |
| `delta_Q` | 0.0 | `qs=[0.10,0.25,0.50,0.75,0.90]`；`Q_A=Q_B=[0,0,0,0,1]` |
| `cv_A` / `cv_B` | 143.0925 / 141.0648 | 拼接边界伪差所致，见 §2 |
| **`verdict`** | **`SAME_DISTRIBUTION`** | `reason=within_noise_band` |

工具输出的判定句（`out\b_compare_v2.json` 的 `detail` 字段，**原句**）：

```
D_ks=0.000049 <= max(N_ks=0.000493, D_floor=0.05) and p=1.000000 >= alpha
```

判定顺序复核（不擅自改）：B-0 未命中 → B-1 未命中（`N_ks=0.000493 ≪ 0.30`，`discrete_unstable=[]`）→ B-2 未命中（`shifted=[]`、`J=1.0 ≥ 0.95`）→ **B-3 命中 `SAME_DISTRIBUTION`** 并短路返回；B-4/B-5 未求值。本卡不代为求值、不改写判定。

---

## 4 · V2 的 gate 原句（逐字抄录）

> 任务卡要求「把 V2 的 gate 原句抄进报告」。本卡所用**权威 V2**（W68b/Hy4，FROZEN `00:33:05`）的工具输出**没有**单独的 `gate` 字符串字段，其 gate 由规格 §2.3 逐字段判定 + §2.4 判定规则表构成；该工具另在 `detail` 中输出自己的判定句（已在 §3.2 逐字抄录）。为避免遗漏，下面把**权威版 gate 原句**与**并发归档版 `B-2v2` gate 原句**一并逐字抄录并明确标注，供 Lead 对照。

### 4.1 本卡实际执行的权威 gate（W68b `CRITERIA_SPEC_V2_COPY.md` §2.3 / §2.4，逐字）

`§2.3 可比量定义（V2，替换 FROZEN §2.1 第 106 行）` 中的可比量与逐字段判定：

```
- 每臂按**行数**归一化：`p_S(f) = { v : count_S(v) / n_S }`，`n_S = len(rows_S)`（**行数**，非 `dframe` 长度；离散字段每行一个取值）。
- 值域取并集 `U_f = keys(p_A(f)) ∪ keys(p_B(f))`，缺失键占比记 `0.0`（不使用 `Counter` 判等）。
- **检验量（与顺序无关）**：`T_f = TVD(p_A, p_B) = 0.5 * Σ_{v∈U_f} |p_A(v) − p_B(v)|`，取值 `[0,1]`。
- **同臂噪声带**：`N_disc(f) = max( TVD(p_{A1}(f), p_{A2}(f)), TVD(p_{B1}(f), p_{B2}(f)) )`，其中 `A1/A2`、`B1/B2` 为同臂两条独立噪声轨迹（若某臂未提供噪声轨迹，该臂分量记 `0.0`）。
- **置换 p 值**：`pool = [f 的按行取值 ; A 全部] ++ [f 的按行取值 ; B 全部]`，长度 `n_A + n_B`；固定 `seed`，重分 `perm_iters` 次，每次按**真实** `(n_A, n_B)` 切分（**不补齐、不截断、不重采样到相等**），重算 `T_perm`；`p_f = ( count(T_perm ≥ T_f − ε) + 1 ) / (perm_iters + 1)`，`ε = 1e-12`。与 FROZEN `permutation_pvalue` 同构（`:130-145`）。
- **逐字段判定**：
  - `D_disc(f) := T_f`
  - 若 `N_disc(f) > N_max` ⇒ 该字段噪声带不稳定 ⇒ 整体 `UNDETERMINABLE(noise_band_unstable)`
  - 若 `D_disc(f) <= max(N_disc(f), D_floor)` **且** `p_f >= alpha` ⇒ `no_shift_detected`
  - 否则 ⇒ `shift_detected`
```

`### §2.4 判定规则表（V2，事先声明；顺序短路不变）`：

```
| 序 | 条件 | 输出 |
|---|---|---|
| B-0 | `n_A < n_min` 或 `n_B < n_min`，或同臂重复数 < `n_noise_min`，或字段缺失/无法解析 | `UNDETERMINABLE(reason=insufficient_sample)` |
| B-1 | `N_ks > N_max` **或** `∃f: N_disc(f) > N_max` | `UNDETERMINABLE(reason=noise_band_unstable)` |
| B-2 | `∃f: shift_detected(f)` **或** `J < theta_ui` | `SHIFT_DETECTED(reason=discrete_or_ui_mismatch)` |
| B-3 | `D_ks <= max(N_ks, D_floor)` **且** `p >= alpha` | `SAME_DISTRIBUTION(reason=within_noise_band)` |
| B-4 | `D_ks > N_ks * k_ratio` **且** `p < alpha` | `SHIFT_DETECTED(reason=ks_beyond_noise)` |
| B-5 | 其余 | `UNDETERMINABLE(reason=grey_zone)` |
```

以及 §2.4 末尾的口径原句：

```
> `SAME_DISTRIBUTION` 的准确含义仍是「**在本判据、本观测量、本样本量下未检出分布差异**」，**不是**"行为等价已成立"，**更不是**"B 线等价性已成立"。
```

常量表（`§3 常量表（一律未改动）`）：`n_min=30`、`n_noise_min=2`、`N_max=0.30`、`alpha=0.05`、`k_ratio=2.0`、`D_floor=0.05`、`perm_iters=2000`、`seed=20261113`、`theta_ui=0.95`、`qs=[0.10,0.25,0.50,0.75,0.90]` —— **本卡未改任何一个数值**（工具 `b_compare_v2.json` 的 `spec` 字典原样回显上述值）。

### 4.2 并发归档版（GLM，`EVIDENCE\concurrent_GLM\CRITERIA_SPEC_V2.md` §3.3）的 `B-2v2` gate 原句 —— **逐字抄录，但本卡未使用**

```
### §3.3 判定规则 B-2v2（替换 v1 B-2；其余腿不动）

| 序 | 条件 | 输出 |
|---|---|---|
| B-2v2-离散 | `D_disc > max(N_disc, D_floor)` **且** `p_disc < alpha` | `SHIFT_DETECTED(reason=discrete_or_ui_mismatch)` |
| B-2v2-否则 | 其余情况 | **离散腿不触发**，落到 B-3（连续腿原样决定）。"过带但不显著 / 显著但未过带"**不静默通过**，由 B-5 灰区如实报告 |
```

对应工具（`EVIDENCE\concurrent_GLM\tool_b_stats_v2.py`，`B-W68-2`）内嵌的 `gate` 字符串原句：`B-2v2: D_disc > max(N_disc, D_floor) AND p_disc < alpha`。
**说明**：该版本于本卡启动后被并发写入 W68 根目录（后归档）；`CONCURRENT_WRITER_NOTE.md §4` 指定权威版为 W68b。本卡**不使用**归档版工具/规格，仅按任务卡要求把这句 gate 原句抄录备查。两版口径实质一致、对 W65 数据结论一致（`CONCURRENT_WRITER_NOTE.md §2`）。详见 `DISAGREE.md` D0。

---

## 5 · 判据 C（安装期零越界写入，`[本次实测]`）

用逐字节副本 `tools\tool_c_writeaudit.py --audit` 对 **B 臂装包快照**跑一次（`--phase audit`，离线、不取锁、不启动游戏）：从同一 `sandbox_base` 复制出惰性沙箱 → 与 B1/B2 **同一条** v15 `install` 命令（rc=0）→ `uninstall`（rc=0），取 `S_pre / S_post / S_uninst` 三份全树快照；`D` 由**包内容 + 事先写死的引擎白名单**构造（不是从运行时写集反推）。产物 `out\c_audit_{before,after,uninst,declared}.json`、`out\c_audit_B_arm.json`、`out\cmd_*.log`。

| 项 | 结果 |
|---|---|
| `W`（写入集） | `BATTLEMD98.INI`, `W65M1.MAP`, `W65M2.MAP`, `expandmd98.mix`, `ra2forge_install.json`, `ra2forge_install.json.seal`（6 项，全部 `added`；`modified=[]`, `removed=[]`） |
| 声明写集 `D` | 同 6 项 ⇒ **C-1 `W ⊆ D` = true**、**C-2 `out_of_scope_writes=[]` = true** |
| 受保护文件 | **C-3 `protected_all_equal=true`**（641 个装前已存在文件逐条哈希留证） |
| 卸载还原 | **C-4 `restore.equal=true`**、**C-5 `residual_outside_whitelist=[]`** ⇒ 逐字节净零 |
| C-6 | `null`（append 路线，非 inplace，不适用） |
| **`verdict`** | **PASS**，`failed_checks=[]`，工具 exit **0** |

工具自检（`b_selftest_v2.json`，权威 V2 副本）：`V2_SELFTEST_PASS=True`，`ce_A=SAME_DISTRIBUTION`（缺陷已修）/ `ce_B=SHIFT_DETECTED`（检出力保留）/ `ce_C=SAME_DISTRIBUTION`；三例全 PASS，exit 0。**合成对照，不是真机结论。**

---

## 6 · 真机纪律（`[本次实测]`，逐项可回对）

| 红线 | 本卡 |
|---|---|
| 取锁/放锁，**lock per trip** | 每趟前读 `.game_instance.lock`，要求 `owner=lead` 且 `gamemd` 活体 0，否则等待；取锁写 `owner=w69`；**每趟结束（finally，无论成败）**写回 `owner=lead` + 状态。`w69_run.ndjson` 记录 4 组 `lock_before → lock_claimed → lock_released`，趟间锁文件始终 `owner=lead`，**从未跨趟长期持锁**（与 W70 一致） |
| 不写 `ra2youli` | 只作 `robocopy` 只读源 + 全树哈希目标；PRE/POST 全树 **647 文件 / 1,989,215,270 B**，added/removed/modified **全 0**，`IDENTICAL_TREE=True` → `REAL_DIR_PROOF.txt` |
| 不 `taskkill` 用户进程 | `pre_launch_guard` 每趟确认 0 个 gamemd；只关闭本趟 WMI 自启 pid（39452/23400/38140/39596），`WM_CLOSE` → `taskkill /PID <own>` → `/F`；`residual_own_pid=0`，收尾 `gamemd residual=[]` |
| 启动前沙箱可写配置字节副本 + 哈希，收尾逐字节还原并实算自证 | 每趟启动前字节复制**全部根级文件**（A 419 / B 425 个）+ 全树哈希 manifest；收尾按 PRE/POST 差异逐文件还原并**重算全树哈希**，四趟 `IDENTICAL_TREE=true`（游戏仅改动 `SOV01UMD.sav`，已从 `pristine_<tag>` 字节副本还原）。见 `out\restore_proof_*.json` |
| 只读采集 | `OpenProcess(PROCESS_VM_READ\|PROCESS_QUERY_INFORMATION)` + `ReadProcessMemory`；`EnumWindows/EnumChildWindows`；`PIL.ImageGrab`。**无写内存 / 断点 / 挂线程 / 注入 / 改 exe** |
| 桌面预检 | 每趟 WMI 启动后即刻 `step0_desktop_precheck`：`WinSta0\Default`、EnumWindows 369 / 20 可见、ImageGrab OK 2560×1440，`pass=true` |
| 不直接调用别卡脚本 | `w65_collect.py` / `w65_report.py` / 两个 FROZEN 工具**全部先逐字节复制到本卡**（`TOOL_HASHES.json` 逐文件 sha256 自证 `ALL_BYTE_IDENTICAL=True`），本卡只运行自己的副本；`ra2forge`(v15) 与两个已指定工具按任务卡授权调用 |
| 只写本卡目录 / git 只读 | 所有产物在 `W69_bline_v2_collect\`；无 commit、未改他卡交付物 |

### 6.1 权威 V2 工件一致性（并发写入冲突处置，`[本次实测]`）

W68 根目录在本卡启动后被并发覆盖过两次（`00:45:12` spec、`00:46:19` tool）。本卡在 `~00:48` 复制到的 `CRITERIA_SPEC_V2_COPY.md` / `tools\tool_b_stats_v2.py` 与 `CONCURRENT_WRITER_NOTE.md §4` 给出的**权威 W68b sha256 完全一致**：

| 工件 | 权威 sha256（`CONCURRENT_WRITER_NOTE.md §4`） | 本卡副本 | 一致 |
|---|---|---|---|
| `CRITERIA_SPEC_V2.md` | `7364E700B07B1881…773FB14F7270` | `7364E700B07B1881…773FB14F7270` | ✅ |
| `tool_b_stats_v2.py` | `B419959A4F4CFA3…4DF94DC6FBE` | `B419959A4F4CFA3…4DF94DC6FBE` | ✅ |

`LEAD_VERIFY_W68B.md` 所载 FROZEN `00:33:05` 亦对应此 W68b 版。详见 `DISAGREE.md` D0 / `UNKNOWNS.md` U7。

---

## 7 · 未主张 / 分级标注

- **不写**「B 线等价性成立」「装包无影响」「等价性成立」——明确禁止。
- **不写**「检出装包导致的分布差异」；本卡判定为 `SAME_DISTRIBUTION`，含义严格限定为 §0 口径句。
- **不签发**任何等价/不等价结论；签发权在 Lead。本卡是执行者，只交付「原始产物 + 退出码 + 判据逐字输出」。
- `[本次实测]`：四趟逐趟状态/点数/pid/锁/残留/还原；每字段占比/TVD/p；`b_compare_v2.json` 全部数值；C 审计 PASS；真目录 PRE/POST 全树零改动；V2 自检 PASS；桌面预检；install/verify/uninstall 退出码。
- `[本次读码]`：`CRITERIA_SPEC_V2.md §2.3/§2.4/§3`、`tool_b_stats_v2.py`、`tool_c_writeaudit.py`、`w45_dual_track.py` 采集骨架、`CONCURRENT_WRITER_NOTE.md`、`LEAD_VERIFY_W68B.md`、v15 `BATTLEMD98.INI` append 语义。
- `[静态推断]`：合并臂拼接边界伪差对 KS 影响量级 ≈1/n；五字段单值退化使离散腿信息量极低；append 不改写 `[SOV1]` 故两臂同图。
- `[转引]`：W65 的 `SHIFT_DETECTED`（触发项为采样时长伪差异）；W68 的诊断性重算（不是结论）；W62 常量表；W55b/W63 入口与偏移定义。
- `[待运行验证]`：见 `UNKNOWNS.md`。
