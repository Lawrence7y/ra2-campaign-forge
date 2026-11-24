# EQUIVALENCE_RESULT_V2.md · W55b / B 线行为等价性重跑

> 卡 `W55b_equivalence_rerun`｜run_id `NEXT_RE_20261112_R02`｜模型 `Hy4`
> 时间：2026-11-13 22:30–23:20（Asia/Shanghai），4 趟真机，含离线改造共计 < 50 min
> 写域：仅 `lead\next_re_20261112_r02\W55b_equivalence_rerun\`；真 `ra2youli\` 全程只读（robocopy 源 + 哈希枚举）
> 分级：`[本次实测]` / `[本次读码]` / `[静态推断]` / `[转引]` / `[待运行验证]`
> 原始证据：`out\`（`.SAV`、`*_result.json`、`w55b_dual_track.ndjson`、`screen_*.png`、`cmd_*.log`、`cfb_compare.json`、`stream_matrix.json`、`analysis.json` 等）

---

## 0 · 一句话结论

> **总判定：`仍不可判`。**

- W54 `SAVE_DETERMINISM.md` §5.3 的**四条硬前置**：**1 达成、2 达成、3 部分（按题面允许退化）、4 达成**。
- **frame 对齐首次跑通**：四趟真机全部在 `frame == 2400` 进门限、全部冻结在 **`frame_frozen = 2408`**，实测对齐精度 **0 拍**（max−min = 0，远优于规格 §3.4 的 ≤1 拍）。W45 的 `2404/2408/2441/2412` 漂移已被消除。
- 但**按 frame 对齐并不能使 `CONTENTS` 平面确定化**：同帧、同臂、两次独立运行（A1 vs A2、B1 vs B2）的 `CONTENTS` 整流仍分别有 **1,339,784 / 1,316,737** 个差异字节（≈ 整流长度的 96%）。噪声基线 `N` 本身巨大且两臂不一致（`N_A ≠ N_B`）。
- 跨臂差异 `D` = **1,319,300 … 1,321,641** 字节，**全部 ≤ N**。按 W45 `EQUIVALENCE_SPEC.md` §2.4，只有 `D > N` 才可把差异归因于装包；此处差异落在噪声带内 ⇒ **既不能判等价，也不能判不等价**。
- 按规格 §3.7：任一可比量不可判 ⇒ 总判定只能是「无法判定 / 仍不可判」。

**明确不写的三句话**：
- ❌「四趟都进图、都在 frame 2408 存档 ⇒ 行为等价」
- ❌「`D` 与 `N` 同量级 ⇒ 装包无影响」
- ❌「元数据平面白名单掩码后 0 差异 ⇒ 存档等价」

---

## 1 · 与 W45 结论的关系

| 项 | W45 `EQUIVALENCE_RESULT.md` | 本卡 W55b |
|---|---|---|
| 总判定 | **不可判** | **仍不可判**（未推翻） |
| 存档点 frame | 2404 / 2408 / 2441 / 2412（漂移 37 拍） | **2408 / 2408 / 2408 / 2408（0 拍）** |
| 同 frame 同臂 `CONTENTS` 噪声基线 N | **从未被测过** | **已测：N_A=1,339,784 B，N_B=1,316,737 B** |
| `CONTENTS` 比较坐标系 | raw file 绝对偏移（**错**） | **CFB 具名 stream（题面纠正）** |
| 白名单 | 未事先声明 | **开跑前声明**（W54 30 region / 68 B，副本 sha256 `dad972c4…`） |
| 不可判原因 | 「噪声基线不成立 + 未对齐 + 白名单未声明」 | 「**对齐已达成、N 已测，但 N≫0 且 D≤N**」 |

⇒ 本卡把 W45 的不可判**从「测量链没搭好」推进到「测量链搭好了，但被测对象本身在现有粒度下不可分辨」**，是一个新的、更硬的结论，不是重复。逐条分歧见 `DISAGREE.md`。

---

## 2 · W54 §5.3 四条硬前置逐条对照

| # | 前置（W54 §5.3） | 状态 | 实测证据 |
|---|---|---|---|
| **1** | `frame == N` 门限对齐存档点（脚本化「等 frame==N 再存」） | **达成** | `tools/w55b_dual_track.py`：`FRAME_GATE_N=2400`，6 ms 轮询 `read_counters()`，命中即 `key_nowait(VK_ESCAPE)`；四趟 `frame_gate.frame_at_gate` 全 = 2400，`alignment.frame_frozen` 全 = 2408，`gate_miss=false`。事先策略见 `ALIGNMENT_STRATEGY.md`。 |
| **2** | 每臂 ≥2 份同 frame 同臂存档（共 ≥4），重测 `CONTENTS` 平面噪声基线 N | **达成** | 4 趟各 1 份**去重后独立**存档：A1/A2（同 frame 2408）、B1/B2（同 frame 2408）⇒ A=2、B=2、总 4。`out\save_dedup.json` 记录去重；N 已实测（见 §4）。 |
| **3** | `CONTENTS` 语义/解压后比较口径；解不出块结构则退化为「按 frame 对齐后的整流 sha256」 | **部分**（按题面允许的退化口径执行） | `tools/w55b_cfb_compare.py::try_contents_structure` 对 8 份 `CONTENTS` 做了 2 种块遍历 × 5 个起点 = 10 次尝试/份，**全部失败**（`out\contents_structure.json`，例如 `u16_unc_u16_cmp_LCW_LZO @0` 得 `(11925, 0)` 无法起步；`u32_len_payload @0` 第 2 块崩）。与 W54 §4.4 一致 ⇒ **明说「未解出块结构」**，退化为整流 sha256 比较并输出逐 stream 差异表。**未**把结构解析成功当作结论。 |
| **4** | （可选）FAT/DIFAT 整体从 raw 比较中排除，统一改用按具名 stream 比较 | **达成** | `cfb_compare.json` 的 `coordinate_space="cfb_named_stream"`，`container_excluded=["FAT","DIFAT","miniFAT"]`；比较器 `import` W54 `step2_cfb.py` 的 `CFB` 类（截断驱动段后 `exec`，不触碰 W45 文件），按 15 个具名 stream 逐一流比较。**并用 W45 的 4 份参考存档复现了 W54 的验证结果**：掩码后元数据平面 `A1_vs_A2 / B1_vs_B2 / A1_vs_B1 / A2_vs_B2` 全部 `diff_bytes=0`（`out\whitelist_crosscheck.json`）。 |

**额外发现（不改变上表状态，但必须报告）**：W54 的「平面元数据视图」掩码后对 W55b 新存档残留 67–176 个差异字节。经定位（`out\metadata_plane_residual_analysis.json`），根因是 `Scenario Description`（32–38 B）与 `\x05SummaryInformation`（380–388 B）两个流**长度随引擎生成的存档名变化**，把 W54 那个「把 14 个非 CONTENTS 流拼接成一条 3576 B 平面」的视图整体位移 ⇒ 后续本相同的流被错开，产生伪差异。**按具名 stream 比较则 13/15 个流掩码后 0 差异**，只有上述两个变长流不同。`Start Time`/`Last Save Time`/`Play Time` 三个墙钟流掩码后 **0 差异** ⇒ W54 白名单在其适用范围内确实有效。本卡**未**事后扩白名单（规格 §1.4/§3.4/§0.1 禁止），而是如实登记为新发现的非确定源。见 `DISAGREE.md` D-W55b-2。

---

## 3 · 真机执行与纪律自证 `[本次实测]`

| 项 | 结果 |
|---|---|
| 桌面预检 | 独立预检 `pass=true`：`WinSta0` / `Default` / `Default`，EnumWindows 443/21、ImageGrab OK 2560×1440；**每趟** WMI 启动后 ≤2 s 的 `step0_desktop_precheck` 四趟全 `pass=true`（EnumWindows 433–437 / 可见 20–21）。`out\desktop_precheck.json` / `precheck_desktop.png` / ndjson |
| 单实例锁 | 开工前 `owner=lead`；每趟取 `owner=w55b`（`run_id=NEXT_RE_20261112_R02`）；**收尾还原 `owner=lead`** 并写明「所有实例已关闭、配置已逐字节还原、投放文件已清理」。最终锁文件已复核 |
| 活体真机卡 | 开跑前 `Get-Process gamemd` = 0；W57/W58/W59 为离线卡（DISPATCH §2），未启动游戏 |
| 启动 / 关闭 | 四趟 WMI `Win32_Process.Create`；**只 `taskkill` 本卡启动的 pid**（`LAUNCHED_PIDS={15288,3280,22500,13232}`）；收尾 `residual=[]`，`Get-Process gamemd` = 0。**未** `taskkill` 任何用户进程 |
| 写域 | 只写 `W55b_equivalence_rerun\`；`git` 未调用、无 commit；未动 W21–W58（仅只读 W43 的 `ra2forge` CLI，用 `-B` 且产物输出到 W55b） |
| 不写 `ra2youli` | 一律 `robocopy /E /COPY:DAT /DCOPY:DAT /R:1 /W:1` 到 `sandbox_*`；四趟 `cmd_<tag>_robocopy_run.log` rc=1（成功） |
| 配置基线 / 还原 | `out\config_baseline.json`（13 个可写配置，字节副本 `cfgbase_*` + sha256）；四趟 `finally` 逐字节还原 4 个配置并 `restore_all_match=True`；`REAL_DIR_PROOF.txt` 实算：`IDENTICAL_TREE=True`、13 文件 `byte_identical=True`、`ALL_TRIP_RESTORE_MATCH=True` |
| 真目录零改动 | PRE/POST 全树 `647 / 1,989,215,270 B / 277`，`added=0 removed=0 changed=0`；4 个关键哈希 PRE=POST=基线 |
| 投放清理 | 四份 `.SAV` 投放物每趟 `drops_removed`；`phase finalize` 删除 4 个 `sandbox_<tag>`，仅保留 `sandbox_base`（基线证据） |
| 预算 | 4 趟真机 ≈ 14 min（143/172/224/222 s），总卡 < 50 min ≤ 150 min |
| 原始记录 | `out\w55b_dual_track.ndjson` 共 **284** 行（含 prep + 4 趟），`dual_track_results.json`（合并 4 趟）、4 份 `*_result.json` |

### 3.1 四趟执行摘要

| 趟 | 臂 | pid | `frame@gate` | `frame_frozen` | Δgate→frozen | gate_miss | errors | 存档 | size | sha256[:8] |
|---|---|---:|---:|---:|---:|---|---|---|---:|---|
| A1 | A | 15288 | 2400 | **2408** | +8 | false | `[]` | `SAVE5802.SAV` | 1,397,190 | `27c20543` |
| A2 | A | 3280 | 2400 | **2408** | +8 | false | `[]` | `SAVE76DA.SAV` | 1,393,306 | `a2abc91a` |
| B1 | B | 22500 | 2400 | **2408** | +8 | false | `[]` | `SAVE30A5.SAV` | 1,367,309 | `4ece4944` |
| B2 | B | 13232 | 2400 | **2408** | +8 | false | `[]` | `SAVE4221.SAV` | 1,368,269 | `95e6bb18` |

- Δgate→frozen = +8 **四趟完全一致**（与 W45 记录的同臂 +8 偏移吻合），这正是「对齐键取冻结帧值」能成立的原因：门限在菜单打开**之前**，帧仍推进，条件可达；菜单打开后帧冻结，之后所有存档动作不再改帧。
- **实际达成的对齐精度：四份存档 `frame_frozen` 全为 2408，max−min = 0 拍**（规格 §3.4 要求 ≤1 拍）。**没有被排除的未对齐样本**（`analysis.json` `n_unaligned_saves=0`），因此不存在「把没对齐的样本当对齐样本」的情形。
- 每趟尝试了同一冻结菜单内 2 次存档（slot 0/1、不同名字），但引擎四趟都复用同一个生成文件名并产出**字节相同**的第二个文件；`out\save_dedup.json` 按 sha256 去重为 4 份独立样本，**没有把重复文件冒充独立样本**（若冒充会造出假的 `N=0`）。详见 `UNKNOWNS.md` U-W55b-3。

### 3.2 次要可比量（沿用 W45 判据，仅作上下文）

| 量 | A1 | A2 | B1 | B2 |
|---|---:|---:|---:|---:|
| `scen_filename` | `SOV01UMD.MAP` | 同 | 同 | 同 |
| `scen_battle_idx` | 1 | 1 | 1 | 1 |
| `battle_cnt` | 14 | 14 | 15 | 15 |
| `rate_cps` | 31.22904 | 31.14709 | 31.16279 | 31.25420 |
| `intervals_ge64ms` | 3 | 2 | 2 | 1 |
| `delta_frame_ge2` | 0 | 0 | 0 | 1 |
| `read_fail` | 0 | 0 | 0 | 0 |
| Esc 必需控件 | 6/6 | 6/6 | 6/6 | 6/6 |
| `verify` pre/post | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| `install_rc` / `manifest_present` | — / false | — / false | 0 / true | 0 / true |

- `battle_cnt` 的 `B−A = 1 = k`（`BATTLEMD98.INI` 的 `15=RA2F1` 事先算出，白名单 W2）⇒ 安装态门禁通过，`verify` 不计入行为结论。
- 定时器仍含 `≥64 ms` 间隔与一次 `Δframe≥2`（B2），与 W45 同类噪声；本卡**不**据此改判，也不事后放宽阈值。

---

## 4 · 数据表：每份存档 × 逐 stream 差异字节数

比较口径：**CFB 具名 stream**；「差异字节数」= 掩码后相对参考 `save_A1_s0_SAVE5802` 的差异字节数（W54 白名单 30 region / 68 B，副本 `out\whitelist_applied.json`，sha256 `dad972c4622d4f573…`，与 W54 原件逐字节一致）。完整矩阵见 `out\stream_matrix.json` / `out\CFB_COMPARE_TABLE.md` / `out\cfb_compare.json`。

### 4.1 每份存档主表

| 存档 | 臂 | frame_frozen | size (B) | sha256[:8] | `CONTENTS` 长度 | metadata_view 长度 | 对齐 |
|---|---|---:|---:|---|---:|---:|---|
| `save_A1_s0_SAVE5802` | A | 2408 | 1,397,190 | `27c20543` | 1,381,318 | 3,562 | ✅ |
| `save_A2_s0_SAVE76DA` | A | 2408 | 1,393,306 | `a2abc91a` | 1,377,434 | 3,554 | ✅ |
| `save_B1_s0_SAVE30A5` | B | 2408 | 1,367,309 | `4ece4944` | 1,351,949 | 3,568 | ✅ |
| `save_B2_s0_SAVE4221` | B | 2408 | 1,368,269 | `95e6bb18` | 1,352,909 | 3,560 | ✅ |

（`metadata_view` 长度不同本身即是 §2 所述变长流导致的平面视图位移，不是额外非确定性。）

### 4.2 逐 stream 掩码后差异字节数（vs A1 参考）

| stream | A1 | A2 | B1 | B2 |
|---|---:|---:|---:|---:|
| `\x05SummaryInformation` | — | 82 | 78 | 20 |
| `Scenario Description` | — | 5 | 3 | 6 |
| `Start Time` | — | 0 | 0 | 0 |
| `Last Save Time` | — | 0 | 0 | 0 |
| `Play Time` | — | 0 | 0 | 0 |
| `Version` | — | 0 | 0 | 0 |
| `Internal Version` | — | 0 | 0 | 0 |
| `Executable Name` | — | 0 | 0 | 0 |
| `Player Name` | — | 0 | 0 | 0 |
| `Player Name2` | — | 0 | 0 | 0 |
| `Player House` | — | 0 | 0 | 0 |
| `Scenario Number` | — | 0 | 0 | 0 |
| `Campaign` | — | 0 | 0 | 0 |
| `GameType` | — | 0 | 0 | 0 |
| **`CONTENTS`** | — | **1,339,784** | **1,319,300** | **1,320,621** |

- **13/15 个非 CONTENTS 流掩码后 0 差异**；3 个墙钟 FILETIME 流被 W54 白名单正确掩掉。
- 两个变长流（`Scenario Description` / `\x05SummaryInformation`）的残留差异来自引擎生成的存档名，非墙钟；**未事后白名单**。
- `CONTENTS` 整流未被白名单（W54 `not_covered_deliberately`），全部差异照实计入。

### 4.3 配对判定（N / D）

| 配对 | 类型 | 掩码后元数据平面差异 | `CONTENTS` 整流差异字节 | 整流 sha 相等 |
|---|---|---:|---:|---|
| A1 vs A2 | 同 frame 同臂（**N_A**） | 140 | **1,339,784** | 否 |
| B1 vs B2 | 同 frame 同臂（**N_B**） | 162 | **1,316,737** | 否 |
| A1 vs B1 | 同 frame 跨臂（**D**） | 169 | 1,319,300 | 否 |
| A1 vs B2 | 同 frame 跨臂（**D**） | 67 | 1,320,621 | 否 |
| A2 vs B1 | 同 frame 跨臂（**D**） | 176 | 1,321,058 | 否 |
| A2 vs B2 | 同 frame 跨臂（**D**） | 152 | 1,321,641 | 否 |

- 保守噪声带 `N = max(N_A, N_B) = 1,339,784`；`D ∈ [1,319,300 ; 1,321,641]`。
- **`D ≤ N`（且 D_min < N、D_max < N）** ⇒ 按规格 §2.4 不得归因于装包；`N > 0` ⇒ 不满足规格 §3.4「等价」所需的全字节相同。
- `N_A ≠ N_B`（差 23,047 B，约 1.7%）⇒ 噪声带本身不是一个稳定常数，也支持「不可判」。

> 元数据平面那一列是 W54 的**平面拼接视图**读数，含变长流位移伪差异（§2 / `out\metadata_plane_residual_analysis.json`）；**判据用的不是它**，而是逐 stream 的 `CONTENTS` 整流比较。

---

## 5 · 判定推导（事先写死，未事后调整）

判据来自 `ALIGNMENT_STRATEGY.md` §5（写在任何真机启动之前）与 W45 `EQUIVALENCE_SPEC.md` §2.4 / §3.4 / §3.7：

| 条件 | 本卡实测 | 结论 |
|---|---|---|
| 前置 1/2/3/4 全达成？ | 1✅ 2✅ 3**部分**（题面允许退化）4✅ | 非「全达成」⇒ 已排除「等价」 |
| `N == 0` 且 `D == 0`？ | N=1,339,784，D>0 | ✗ |
| `N` 稳定且 `D > N` 可复现？ | N 不稳；D_max=1,321,641 < N | ✗ |
| 任一可比量不可判 / `D ≤ N` / 前置未全达成？ | **是** | **仍不可判** |

> 依据规格 §3.7：任一可比量不可判 ⇒ 总判定不可判。本卡不因「frame 对齐 0 拍、CFB 坐标系纠正、白名单事先声明、四趟全进图」而降级成「等价」。

**首个分歧点**：无可归因于改造的分歧点（`first_divergent_sample=null`）。跨臂差异全部落在同臂噪声带内。

**作用域限定**：即便判等价也只适用于「本机 / 本镜像 / 本配置 / 单机 / 官方 SOV01 首关路径 / 本时段 / 4 趟样本」；渲染侧、函数级 tick 对拍、干净零售金标准、联机与全战役链仍是 `[不可判/不在范围]`（沿用 W45 §4，不重述）。

---

## 6 · 给 Lead 的下一步（按成本排序）

1. **本卡已闭合的三件事**：frame 对齐策略可行（0 拍）、`CONTENTS` 平面 N 已实测、CFB 具名 stream 坐标系已验证。W45 `UNCOVERED` 的前三条硬前置不再是「没做」，而是「做了且给出了否定性结果」。
2. **要判「等价 / 不等价」，必须先让 `CONTENTS` 平面在同一 frame 上可复现**：同帧同臂两次仍有 ~1.3 MB / ~96% 差异，说明该整流含运行间状态（RNG 序列 / 单位位置 / 迷雾 / 触发计时等），只读 RPM 与 6 ms 采样无法约束。可行方向：解出 `CONTENTS` 块结构做**语义级**比较（本卡 10 种遍历全失败 ⇒ 需专门的格式逆向卡），或找到一个能把同臂噪声压到 0 的确定性设置（固定 RNG / 固定输入时序 / 暂停模拟后存档）。
3. **`CONTENTS` 结构解析**：登记为 `[待运行验证]`，见 `UNKNOWNS.md` U-W55b-1。
4. **变长存档名元数据**：若下一轮还要用「平面元数据视图」，须**开跑前**把 `Scenario Description` / `\x05SummaryInformation` 及其目录项 size 字段纳入白名单，或统一改用按具名 stream 比较（本卡已用后者）。见 `DISAGREE.md` D-W55b-2。
5. **定时器噪声**：`≥64 ms` 计数 `{3,2,2,1}`、`Δframe≥2` `{0,0,0,1}` 仍属仪器/主机噪声，需仪器开/关对照（W45 §6 第 2 条）才能定谳；本卡未放宽阈值。

---

## 7 · 交付清单与复跑

```
W55b_equivalence_rerun/
├── STARTED.txt / HEARTBEAT.txt          先于读文件建卡 + 心跳
├── ALIGNMENT_STRATEGY.md               ★ 开跑前事先声明的对齐策略 / 判据 / 白名单
├── EQUIVALENCE_RESULT_V2.md            ← 本文件
├── UNKNOWNS.md / DISAGREE.md          未定谳项 / 与 W45·W54 的分歧
├── REAL_DIR_PROOF.txt                  IDENTICAL_TREE=True + 逐文件 byte_identical
├── designs/w45_two_missions.json      固定 design（副本）
├── tools/
│   ├── w55b_desktop_precheck.py        路径重定向的预检
│   ├── w55b_real_dir_proof.py          真目录 PRE/POST + 配置字节还原自证
│   ├── w55b_dual_track.py              ★ 改造运行器（frame 门限 + 冻结帧对齐键 + 同帧补样）
│   ├── w55b_cfb_compare.py             ★ CFB 具名 stream 比较器（import W54 step2_cfb）
│   ├── w55b_metadata_diagnosis.py      平面视图残留差异定位
│   └── w55b_analyze.py                 三选一判定 → out/analysis.json
└── out/
    ├── desktop_precheck.json / precheck_desktop.png / real_dir_pre.json / real_dir_post.json
    ├── config_baseline.json / cfgbase_* / config_restore_post.json / pristine_*
    ├── whitelist_applied.json / whitelist_crosscheck.json / metadata_plane_residual_analysis.json
    ├── w45_ref/                        4 份 W45 参考存档（只读副本，用于复现 W54 验证）
    ├── pkg_v13/                       复用的 v13 包（W45 已构建，逐字节副本）
    ├── w55b_dual_track.ndjson (284 行) / w55b_dual_track_prep.ndjson / dual_track_results.json
    ├── A1/A2/B1/B2_result.json
    ├── save_*_s0_*.SAV (4 份独立) + save_*_s1_*.SAV (4 份字节相同副本)
    ├── save_dedup.json / cfb_compare.json / stream_matrix.json / contents_structure.json
    ├── CFB_COMPARE_TABLE.md / analysis.json
    ├── cmd_*.log（robocopy / uninstall / verify / install / finalize）
    └── screen_*.png（4 趟 × 战役菜单/局内/Esc/存档对话框 + 预检）
```

复跑（前提：`.game_instance.lock` = `owner=lead`、无 `gamemd` 残留、`WinSta0\Default`）：
```powershell
$py = 'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe'
$card = 'lead\next_re_20261112_r02\W55b_equivalence_rerun'
& $py -B "$card\tools\w55b_desktop_precheck.py"
& $py -B "$card\tools\w55b_dual_track.py" --phase prep
& $py -B "$card\tools\w55b_real_dir_proof.py" --phase pre
& $py -B "$card\tools\w55b_dual_track.py" --phase run --arms A1,A2,B1,B2
& $py -B "$card\tools\w55b_real_dir_proof.py" --phase post
& $py -B "$card\tools\w55b_dual_track.py" --phase finalize
& $py -B "$card\tools\w55b_cfb_compare.py"
& $py -B "$card\tools\w55b_metadata_diagnosis.py"
& $py -B "$card\tools\w55b_analyze.py"
```

---

## 8 · 分级索引

| 结论 | 等级 |
|---|---|
| 4 趟真机执行、`frame_frozen` 全 2408、`gate_miss=false`、`errors=[]`、截图/ndjson/存档落盘 | `[本次实测]` |
| 逐 stream sha256 / 差异字节数、N/D 数值、CFB 比较矩阵、白名单掩码结果、W54 4 参考验证复现 | `[本次实测]` |
| `CONTENTS` 块结构遍历全部失败、退化为整流 sha256 | `[本次实测]`（尝试）+ `[静态推断]`（与 W54 §4.4 一致） |
| 「平面元数据视图残留 = 变长流长度位移伪差异」 | `[本次实测]`（逐流/逐偏移定位）+ `[静态推断]`（归因） |
| 「同帧同臂 ~96% 差异来自运行间游戏状态」 | `[静态推断]`（未在符号级定位具体字段） |
| W45 规格阈值、W54 白名单语义、`frame` 32 ms 定拍、k=1 | `[转引]` |
| `CONTENTS` 语义级比较、确定性设置下 N 能否压到 0 | `[待运行验证]` |
