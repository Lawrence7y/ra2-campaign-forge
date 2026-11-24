# CRITERIA_SPEC.md — W62 / RE-N09 — **FROZEN**

> 卡：`W62_bline_new_criteria`｜执行者：Hy4｜纯离线（**I launched 0 / attached 0**）
> 冻结时间戳：**2026-11-13T23:25:30+08:00**（`HEARTBEAT.txt` 同刻记录）
> 状态：**FROZEN — 判据已事先声明。代码 `tool_c_writeaudit.py` / `tool_b_stats.py` 在本次冻结之后实现，且不得事后调整下列任何阈值、白名单、样本量下限或判定规则（项目 §3.4 / §0.1 纪律；W55b `LEAD_VERIFY_W55B.md` §2.2 明确禁止事后加白名单）。**
> 依据：`REVIEW\LEAD_VERIFY_W55B.md` §4（Lead 定方向 C+B）、`REVIEW\LEAD_VERIFY_W59.md` §5（观测锚点）、`W55b_equivalence_rerun\out\analysis.json`（旧判据失效数值）、`W45_b_line_equivalence\tools\w45_dual_track.py`（只读采集层）、`W60_battlemd_inplace\ra2forge_patched_v15\`（装包引擎）、`W60_battlemd_inplace\s5_cases.py`（inplace 用例格式）。
>
> **本卡交付的是「判据 + 被验证过的判据工具」，不是结论。不得写「B 线等价性已成立」。**
> C 证明的是**安装期非侵入性/零越界写入（不干扰）**；B 给出的是**可观测行为的分布比较规格**。二者措辞必须区分（Lead `LEAD_VERIFY_W55B.md` §4 表）。

---

## §0 顺序与分级纪律

1. 判据（本文件）→ 代码（两个 tool_*.py）→ 运行（EVIDENCE/）。**顺序不可反**。
2. 分级：`[本次实测]` 本卡真跑出来的；`[本次读码]` 本卡读过的上游代码/文档；`[静态推断]` 由读码推出的、未在本卡实测的；`[转引]` 引自 REVIEW/W55b 等上游；`[待运行验证]` 需后续真机卡。
3. 纯离线红线：不启动 `gamemd.exe`、不 attach、不读活进程内存、**不取 `.game_instance.lock`**。本卡所有"装包"都是 v15 CLI 对**合成沙箱目录**的纯文件操作（沙箱在本卡 `EVIDENCE/sandbox/` 内，`gamemd.exe` 是 inert placeholder，永不执行）。
4. 只写本卡目录；`ra2forge`/`ra2opt`/`ra2bench`/`W21`–`W61` 只读；`git` 只读。

---

## §1 判据 C — 非侵入性 / 零越界写入（本次实测）

### §1.1 观测量：全树快照

对沙箱根目录 `G` 做快照 `S = { relpath : (size, sha256, mtime_ns) }`，`relpath` 为相对 `G` 的 POSIX 风格路径，覆盖所有普通文件（含子目录内），不含目录项本身。
取三次：`S_pre`（装前）、`S_post`（装后）、`S_uninst`（卸载后）。

- **写入集** `W = diff(S_pre, S_post)`：定义为 `{added} ∪ {modified} ∪ {removed}`。
  - `added`：post 有、pre 无；
  - `modified`：两边都有但 `sha256` 或 `size` 不同（`mtime_ns` 仅作附加记录，**不单独触发 modified**，避免时钟噪声）；
  - `removed`：pre 有、post 无。
- **回装前判定**：比较 `S_pre` 与 `S_uninst`，只用 `relpath + size + sha256` 三项（`mtime_ns` **不参与**，因卸载还原必然重写 mtime；此点事先声明）。

### §1.2 事先声明的「声明写集」`D`（独立于 v15 运行时行为）

`D` **不得**由被测的 v15 运行时输出反推（否则是自己证明自己）。`D` 由**包内容** + **规范白名单**构造：

1. **包成员映射**：包目录 `P` 内的文件，按 `install.package_files()` 语义 `[本次读码]`（`install.py:760-793`）取 `{BATTLEMD.INI | BATTLEMD98.INI, MAPSELMD.INI?, ra2md.csf?, *.MAP*, expandmd98.mix?}`，每个文件名 `n` 映射为 `game/<n>`，并入 `D`。
2. **引擎派生白名单（事先声明，固定）**：
   - `ra2forge_install.json`（install record，`install.py:375`）
   - `ra2forge_install.json.seal`（seal，`cli.py:96`）
   - 对 `D` 中每个在 `S_pre` 已存在的目标 `n`：`<n>.ra2forge.bak`（备份槽，`install.py:14`）
   - 对 inplace 用例：`BATTLEMD.INI.ra2forge.bak`（官方文件备份，`s5_cases.py:155`）
3. **inplace 声明内改写**：当且仅当包内含 `BATTLEMD.INI` 且不含 `BATTLEMD98.INI`（`resolve_integration.py:928-933` `inplace_requested()`），`BATTLEMD.INI` 属 `D` 且被标记为 **DECLARED-REWRITE**（声明内改写官方文件）。此时 `BATTLEMD.INI` **不**进入 §1.3 的受保护集合。

> 设计要点：`D` 只认"包名 + 事先写死的派生名"。任何 v15 实际写到 `D` 之外的路径，都会成为 `W \ D` 非空 ⇒ FAIL。

### §1.3 受保护文件集合 `P_prot`（必须逐字节未变）

`P_prot` = `S_pre` 中存在、且匹配下列任一、且**不在 `D` 中**的文件：

- 精确名：`gamemd.exe`、`ddraw.dll`、`RA2MD.INI`
- 通配：`*.MIX`、`*.CSF`、`*.INI` 中除 `BATTLEMD.INI`（inplace 声明内）以外、且装前已存在的**其它**官方文件
- `USERMAP1.MAP` 等装前已存在的用户/官方样本文件（本卡沙箱自带）

**判据 C-PROT**：`W` 中任何 `modified`/`removed` 元素若 ∈ `P_prot` ⇒ FAIL。装后对 `P_prot` 每个文件复算 `sha256`，必须与 `S_pre` 相等并逐条留证。
（注意：包新写入的 `expandmd98.mix` 在 `S_pre` 不存在，属 `added` 且 ∈ `D`，不受此条约束 —— 这正是"声明内新增"与"越界改写官方 MIX"的区分。）

### §1.4 判定规则（事先声明，代码只实现此表）

| 编号 | 条件 | 判定 |
|---|---|---|
| C-1 | `W ⊆ D`（逐项，`W \ D = ∅`） | 通过项 |
| C-2 | `W \ D ≠ ∅` | **FAIL**，列出全部越界路径 |
| C-3 | `P_prot` 任一文件装后 sha256 ≠ 装前 | **FAIL** |
| C-4 | 卸载后 `S_uninst` 与 `S_pre` 在 `relpath+size+sha256` 上完全相等 | 通过项 |
| C-5 | 卸载后仍有非白名单残留 | **FAIL**，列出残留 |
| C-6 | inplace 用例：`.bak` 在位且字节 == 装前 `BATTLEMD.INI`；卸载后 `.bak` 被消费、`BATTLEMD.INI` 还原为装前字节 | 通过项（否则 FAIL） |

**C 用例集（本次都要真跑）**：
- `C-A` 普通包（append route，包内 `BATTLEMD98.INI`）：验证 C-1..C-5。
- `C-B` **battlemd:inplace** 包（包内 `BATTLEMD.INI`，feature_set `battlemd.mode=inplace`）：验证 C-1..C-6，重点验证"官方 `BATTLEMD.INI` 被改写"是 **DECLARED-REWRITE** 而非越界，且 `.bak` 可逐字节还原。
- `C-NEG` **负对照**：在 `S_post` 之上注入一个清单外写入（合成 `S_bad`），审计工具必须判 `FAIL` 且准确列出该越界项。此用例验证**判据实现本身能抓越界**，而非只放过合规用例。

> `C-NEG` 是纯快照级 fixture（不改 v15、不碰真沙箱），与 B 的正/负对照同等地位：**正负对照必须都有**。

### §1.5 引擎自身运行产生文件的白名单（事先声明）

卸载后允许残留白名单 = **空集**（`∅`）。即要求 v15 install→uninstall 生命周期对合成沙箱**逐字节净零**。若实测出现残留，如实判 C-5 FAIL 并写入 `UNKNOWNS.md`，**不事后加白名单**。

---

## §2 判据 B — 可观测行为等价：观测规格 + 离线可跑统计判据

### §2.1 可比量定义（NDJSON 行 schema，采集层留给后续真机卡）

每行一个采样点（`[待运行验证]` 真机由 `ReadProcessMemory` + `EnumWindows/EnumChildWindows` 只读采集，复用 `w45_dual_track.py` 采集层 `[本次读码]`）：

```json
{"t": 0.006, "frame": 2400, "map_name": "ECH01.MAP", "stage_idx": 0,
 "end_of_game": 0, "skip_map_select": 0, "battle_idx": 1,
 "ui_controls": [101, 102, 205]}
```

字段来源 `[转引 REVIEW\LEAD_VERIFY_W59.md §5 / 任务卡]`：
- `frame` ← `[0xA8ED84]`
- `Scen* = *(DWORD*)0xA8B230`；`map_name` ← `Scen+0x125C`；`stage_idx` ← `+0x35A0`(WORD)；`end_of_game` ← `+0x34AC`；`skip_map_select` ← `+0x34B0`；`battle_idx` ← `+0x34CC`
- `ui_controls` ← `EnumWindows/EnumChildWindows` 的可见控件 id 集合

**轨迹级派生量**：
- `dframe` = 相邻 `frame` 的一阶差分序列（长度 `n-1`）。
  **事先声明为何用 `dframe` 而非 raw `frame`**：帧号是进程启动以来的单调计数器，跨运行绝对起点不可比；W55b 的教训（`LEAD_VERIFY_W55B.md` §2.1，`[转引]`）是"对齐到同一帧仍不能消除非确定性"，因此这里把观测量**归一为增量分布**，避免起点/挂钟偏移污染统计量。
- "帧号轨迹的分位数" = `dframe` 的经验分位数向量 `Q = quantile(dframe, qs)`。
- "稳定性" = `dframe` 的变异系数 `CV = std/mean`（总体标准差，ddof=0）。
- 离散字段序列：`map_name`、`stage_idx`、`end_of_game`、`skip_map_select`、`battle_idx` 各自按行取值 → 用**多重集（值→计数）**比较，不做连续统计。
- `ui_controls`：逐行集合的 Jaccard 均值 `J`。

### §2.2 噪声带（同臂两次运行，事先声明）

- 每臂需 **2 条同臂独立轨迹**：`A1`（噪声基线 1）、`A2`（噪声基线 2）；`A` 为 A1∪A2 合并用于跨臂比较的主样本（**事先声明**：合并而非只用一条，避免用单条轨迹冒充分布）。`B` 同理需 `B1`/`B2`（本卡合成数据两臂都给 2 条）。
- **噪声带** `N_ks = KS(dframe(A1), dframe(A2))`（同臂 KS 距离）。
- **噪声带上界** `N_max`：若 `N_ks > N_max` ⇒ 同臂自身已不可复现 ⇒ **判 `UNDETERMINABLE`**（直接吸收 W55b §2.1 的"N 不可稳定"教训，不许用不可稳的噪声带去做 `D>N`）。

### §2.3 跨臂统计量（事先声明）

- `D_ks = KS(dframe(A), dframe(B))`（两样本 ECDF 最大差，标准两样本 KS 统计量）。
- **置换检验 p 值**：H0 = A/B 同分布。把 `A∪B` 合并，固定 seed 随机重分 2000 次，统计 `|KS_perm| ≥ D_ks` 的比例（+1 校正：`(count+1)/(iters+1)`）。
- 分位数区间：`Q(A)`、`Q(B)` 各自向量，报告其最大绝对差 `ΔQ`；`ΔQ` **只作报告量，不单独触发判定**（避免多比较事后挑阈值）。
- 离散字段：任一字段多重集不相等 ⇒ 直接 `SHIFT_DETECTED`。
- `J < θ_ui` ⇒ 直接 `SHIFT_DETECTED`。

### §2.4 判定规则（**冻结，不许事后调**）

按顺序短路，命中即返回：

| 序 | 条件 | 输出 |
|---|---|---|
| B-0 | `n_A < n_min` 或 `n_B < n_min`，或同臂重复数 < `n_noise_min`，或字段缺失/无法解析 | `UNDETERMINABLE(reason=insufficient_sample)` |
| B-1 | `N_ks > N_max` | `UNDETERMINABLE(reason=noise_band_unstable)` |
| B-2 | 任一离散字段多重集不等，或 `J < θ_ui` | `SHIFT_DETECTED` |
| B-3 | `D_ks ≤ max(N_ks, D_floor)` **且** `p ≥ α` | `SAME_DISTRIBUTION` |
| B-4 | `D_ks > N_ks * k_ratio` **且** `p < α` | `SHIFT_DETECTED` |
| B-5 | 其余（灰区） | `UNDETERMINABLE(reason=grey_zone)` |

**输出词表固定为** `SAME_DISTRIBUTION` / `SHIFT_DETECTED` / `UNDETERMINABLE`。
`SAME_DISTRIBUTION` 的准确含义 = "**在本判据、本观测量、本样本量下未检出分布差异**"，**不是**"行为等价已成立"，**更不是**"B 线等价性已成立"。

### §2.5 冻结常量表（代码必须逐字对应，写进 `tool_b_stats.py` 的 `SPEC` 常量）

| 常量 | 值 | 含义 |
|---|---|---|
| `n_min` | `30` | 每臂 `dframe` 样本点下限 |
| `n_noise_min` | `2` | 同臂独立轨迹条数下限 |
| `N_max` | `0.30` | 同臂 KS 噪声带上界 |
| `alpha` | `0.05` | 置换检验显著性 |
| `k_ratio` | `2.0` | 跨臂/同臂 KS 比阈值 |
| `D_floor` | `0.05` | KS 分辨率下限 |
| `perm_iters` | `2000` | 置换次数 |
| `seed` | `20261113` | 置换 RNG 种子（可复现） |
| `theta_ui` | `0.95` | UI Jaccard 下限 |
| `qs` | `[0.10,0.25,0.50,0.75,0.90]` | 分位数网格 |

### §2.6 正/负对照（**事先声明预期，本卡必须真跑**）

| 用例 | 构造 | **事先声明的期望输出** |
|---|---|---|
| `B-POS` 正对照 | `A1/A2/B1/B2` 的 `dframe` 全部来自同一离散分布；离散字段序列相同；`ui_controls` 相同 | `SAME_DISTRIBUTION` |
| `B-NEG` 负对照 | `B` 的 `dframe` 分布**明显平移**（且 `battle_idx` 取不同值） | `SHIFT_DETECTED` |

工具自检通过条件（事先声明）：`B-POS == SAME_DISTRIBUTION` **且** `B-NEG == SHIFT_DETECTED`；任一不符 ⇒ 工具自检 **FAIL**，本卡如实报告，不调阈值补救。
**这两组是合成 NDJSON（`[本次实测]` 指"工具在合成数据上真跑过"），不是真机采集，不构成任何真机等价性结论。**

---

## §3 与旧判据的关系（防误读）

- 旧判据：`D > N`（存档 `CONTENTS` 整流字节差）。`[转引 W55b analysis.json]`：`N_A=1,339,784`、`N_B=1,316,737`、`N_stable=false`、跨臂 `D∈[1,319,300 .. 1,321,641]` ⇒ `D` 与 `N` 同量级且 `N` 不可稳 ⇒ **数学失效**。
- 本判据 **B 不再使用存档字节**，改用§2.1 的可观测量分布；**C 不使用任何跨运行内容比较**，只比较"装包写了哪些路径"这一确定性观测量。
- 本卡**不重做** W55b 等价性判定，也**不签发**任何等价/不等价结论。

## §4 冻结签名

- 冻结时刻：`2026-11-13T23:25:30+08:00`
- 冻结顺序：本文件写毕 → 才实现 `tool_c_writeaudit.py` / `tool_b_stats.py` → 才运行 → 才写 EVIDENCE/。
- 任何运行后对 §1.2 白名单、§2.5 常量、§2.4 规则表的修改，都视为违反 §3.4，必须另开卡声明。
