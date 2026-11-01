# XVERIFY_TRIPS_20261030 · 异族对账判定书（§474 真机双批 ①②）

mimosa security_scan：**未运行**（理由：本线为纯静态离线 JSON 回读+独立重算，无项目代码改动可扫；且派单禁止真机/发射，未调用该工具）。

- 对账员：Qwen 家族（异族），核验对象=DeepSeek 家族执行线 §474 及其交付件自报读数。
- 纪律：不采信「判器/门禁全绿」，全部回读原始 `_rec.json` / `timeline.json` / `measure_w*.json` / `qc151_fields.json` 原始序列重算。
- 本线全程零真机、零游戏进程、零写退出/焦点状态；除本目录外仓库零写入（写域=本目录）。
- 脚本与原始 stdout 留档：本目录 `_xv_s01..s16*.py`（16 支）+ `_raw/s01..s16_stdout.txt`（17 个文件，含 s03b）。

## 结论摘要

**台账 §474 的 5 项主读数（同会话闩边界、绝对时钟否证、闩→退 ≈2.0 s、战斗期长停顿 0/0、units 逐秒降）中：3 项被我独立重算完整复现，2 项含实质瑕疵（闩→退 hold14 报 2.008 而原始时间戳实算 2.005；r 趟「逐秒降」有 1 个持平步）。主结论（① 31 档 × 974/941 交火期零停顿、② 边界收窄 + 绝对时钟替法被否）不被推翻；① 段引用的前提件全称句「长停顿全是终局」经我二次（正确判据）重验后亦 CONFIRMED。**
判定：**红项 2 条**（R-1 舍入伪值 3 ms；R-2 措辞 1 个持平步）；**黄项 10 条**（Y-1..Y-10：表述过强 / 免责缺失 / 口径混用 / 同批内数字不一致）。
另有 **1 条我自己判据错误导致的撤回**（R-3，见 §3 末，留档不掩盖）。
增量线索 **5 条**（§6，台账未表述），其中「关窗→hwnd 归零延迟 Δ」在 11 趟上对「闩/不闩」完美二分，是对「引擎阶段中介」说的具体化。

---

## 1. ② 早窗 3 趟 —— 逐条亲算

### (1) 同会话性与哈希 —— CONFIRMED

命令：`python lead/codex_round_20261030/XVERIFY_TRIPS_20261030/_xv_s01_trips2.py`（→ `_raw/s01_stdout.txt`）

| 趟 | 文件 | 台账声明 | 我自算 sha256 | 判定 |
|---|---|---|---|---|
| hold13 | `_rec.json` | `7e02d38f…13ed1` | `7e02d38fa1c5380a7378adb84d2615d5fb3dabab73abc016d9de8b257ec13ed1` | CONFIRMED（前8+末5 双端一致）|
| hold13 | `timeline.json` | `0cf92e49…509ff` | `0cf92e49e474349fc981756989826c642e119c509d5713ce37fd9d63805509ff` | CONFIRMED |
| hold14 | `_rec.json` | `26b6b33b…d20df` | `26b6b33bc72c000d42d7cb86f9902dd8b2c55ba1549198f23521e807d52d20df` | CONFIRMED |
| hold14 | `timeline.json` | `751df9a3…743ec` | `751df9a320c591021e0c08887bd28e585e0b1fe37fad5ba87488958e96d743ec` | CONFIRMED |
| hold15 | `_rec.json` | `be90b0ac…b5c2f` | `be90b0ac0a3263eed82013df1dc39951193e1d135e6e3dba42a08da7702b5c2f` | CONFIRMED |
| hold15 | `timeline.json` | `7dfe8bd9…5ccf5` | `7dfe8bd96191082f982c61431383822452142a3a4e5889c501a933513875ccf5` | CONFIRMED |

会话同源性（`_rec.boot_wallclock_ms_at_start`）：hold13=1793337038119 / hold14=1793337038113 / hold15=1793337038106。
**我自算极差 = 119 − 106 = 13 ms**，台账「极差 13ms」CONFIRMED。
epoch 换算（+08:00）：1793337038119 → **2026-10-30T13:10:38.119**，与 §474「本日 13:10:38 重启」CONFIRMED。
自洽性加验（台账未要求，我自跑）：每趟 `wallclock_ms_at_start − boot_ms_at_start == boot_wallclock_ms_at_start` 差 **0 ms**（三趟皆然）⇒ 该字段非硬编码，内部自洽。
对照：E5 批三趟 boot=1793256614227/130/112 → 2026-10-29T14:50:14 ⇒ 台账「E5/D-11 批属 10-29 会话」CONFIRMED。

### (2) hold13/14 闩行与退出证明 —— CONFIRMED（纪律红线未违反）

| 字段 | 台账 | 我从 `timeline.close_rows` 原始重算 | 判定 |
|---|---|---|---|
| hold13 闩行号 / 闩后 | row77 / +7.736 | `rows[77].exitstate==1`（`rows[76]==0`）；`rows[77].t − rows[0].t = 7.736` | CONFIRMED |
| hold14 闩行号 / 闩后 | row70 / +7.032 | `rows[70].exitstate==1`（`rows[69]==0`）；`7.032` | CONFIRMED |
| hold13/14 终态 | natural code0 | 末行 `wait=0`(=WAIT_OBJECT_0) `code=0` `code_read_ok=True`，`exit_kind=natural` | CONFIRMED |
| killed_on_cleanup 缺席 | — | 两趟 `_rec.json` **无此键**（ABSENT） | CONFIRMED |

退出证明走的是 `exited = rows[-1]["wait"] == V2.WAIT_OBJECT_0`（`lead/qc161_u0400_trip/_drive_c2_x_e12.py:495`），
`final_exitcode = rows[-1]["code"]`（同文件 `:508`），且 `code` 仅在 `res==WAIT_OBJECT_0` 时被写入（`:374`）。
**未见以 exitstate 代退出证明**；`WAIT_TIMEOUT=258 / WAIT_OBJECT_0=0` 定义于 `_drive_c2_x_probe_v2.py:73`。红线**未违反**。
闩判据为 `row["exitstate"] == LATCH_VALUE(=1)`（`:381`），地址 `G_EXITSTATE = 0x00A8EDD8`（`_drive_c2_x_probe_v2.py:68`）
⇒ 台账「闩的写者是 exitstate `[0xA8EDD8]`（≠焦点旗标 `[0xA8ED80]`）」CONFIRMED（`G_TICK = 0x00A8ED80`，`:72`）。
`wait` 值域（自算）：hold13 `{258:79, 0:1}`，hold14 `{258:72, 0:1}` ⇒ 仅末行转 0，与"自然退出"一致。
`close_delivery.t == rows[0].t` 三趟皆 True，`post_ok=True / post_err=0` ⇒ 关窗投递成功且首采样同刻（自算）。

### (3) hold15 值域与时序 —— CONFIRMED

- `close_rows_n`：文件 `rec` 与原始数组**双读一致 = 1195**。
- **exitstate 值域（全 1195 行，含 dict 态口径）= `{0: 1195}`** —— 严格 {0}，无 1、无 read_fail 混入。台账 CONFIRMED。
- `wait` 值域 = `{258: 1195}`（恒 258=TIMEOUT）CONFIRMED；`code` 值域 = `{None/ok=True: 1195}`。
- 采样节律：相邻 dt `min=0.1 max=0.104 median=0.1`，**无 >0.5s 空洞** ⇒ 120 s 观察窗是密采非盲区。
- `exit_kind=still_running_at_watch_end`、`stop_triggered=None`、`verdict=OK`、`except_changed=False`。
- **台账未给的量，我自算补充**：`hwnd`/`singleton` 首次归零在**同一行 idx=48**，绝对时刻 **+21.094 s**（=close+4.822 s）；
  末行仍 `hwnd=0 singleton=0 frame=0 tick=1`；观察窗绝对区间 = **[16.272 s, 136.213 s]**（跨度 119.941 s）。
- `killed_on_cleanup = [[19512,'rc4_loader.exe'],[61092,'gamemd.exe']]`：pid 与本趟 `loader_pid=19512 / gamemd_pid=61092` **逐一对应**（自算等值比较 True）⇒ 台账「单记（本批可归属进程）」CONFIRMED。
  时序自洽（读 `_drive_c2_x_probe_v2.py:462-498`）：`finalize` 先记 `killed_on_cleanup` 再 `TerminateProcess`，`a8_remaining` 是**强杀后重扫**结果（3 s 截止）⇒ `a8_remaining=[] / a8_verdict=PASS / carrier_deleted=True` 与 killed 单记**不矛盾**。

### (4) 主读数「同会话闩边界 close∈(14.997,16.272]」 —— 算术支持，但表述过强（黄项 Y-1）

我自算（`_xv_s01/s09`）：本会话内 `latch=True` 的 close 最大 = **14.997**，`latch=False` 的最小 = **16.272**；
hold13=14.131 / hold14=14.997 / hold15=16.272（`closed_at_s` 与原始 `rows[0].t − t0` 三趟逐位一致）。
⇒ 该区间作为**"两侧最近测点之间的开覆盖"**成立。过强之处：

1. **每点 n=1**，无同档重复 ⇒ 不能排除测点自身抖动（`closed_at_s` 含 0.997~1.272 s 的投递开销，见下）。
2. **未收窄到点**：14.997→16.272 之间 1.275 s 零采样（台账 GOAL2 §诚实边界第 2 条已自认，但 §474 主读数句用完成态「收窄到」，两处强度不一致）。
3. **上界其实未收紧**：E5 批已有不闩点 close=**16.091**（我自读 `20261030T072353/_rec.json`），比本批上界 16.272 **更小**。
   若跨会话合并同侧证据，边界应是 **(14.997, 16.091]**（宽 1.094 s），而非台账写的 (14.997,16.272]（宽 1.275 s）。
   台账加「同会话」限定词后算术上不错，但「较 E5 (11.19,16.09] 显著窄」的**增益全部来自下界**（11.19→14.997，抬 3.8 s），上界反而从 16.09 退到 16.272。
   ⇒ 建议改述：「同会话内 (14.997,16.272]；纳入 E5 可比点后 (14.997,16.091]；下界收紧 3.8 s，上界未收紧」。

另核：`closed_at_s − --hold`（我自算投递开销）= hold13 **1.131 s** / hold14 **0.997 s** / hold15 **1.272 s**；
E5h10 1.193 / E5h15 1.091 / E5h20 1.249 ⇒ 7 趟开销带宽 0.997~1.272 s。
即 `--hold 13/14/15` 三档的**实测 close 间距（0.866 / 1.275 s）与档位间距（1.0 s）不可交换**，边界只能用 `closed_at_s` 表达（台账用的正是 `closed_at_s`，**用场正确**，但引用 `--hold` 值作档位身份时不得当实测值用）。

### (5) 「绝对时钟模型被否证」 —— CONFIRMED（且可比台账更强的 n=3 形式）

我自算（`_xv_s01_trips2.py` 末段 + `_xv_s14_band.py`）：

| 量 | 自算值 |
|---|---|
| hold13 闩绝对时刻（相对驱动 t0）| **21.867 s**（台账/GOAL2 ≈21.87）|
| hold14 闩绝对时刻 | **22.029 s**（≈22.03）|
| hold15 观察窗绝对区间 | **[16.272, 136.213] s** ⇒ 完整覆盖 21~22 s |
| hold15 窗内 exitstate==1 行数 | **0**（1195 行全 0）|

⇒ 若真变量是「到 21~22 s 就闩」，hold15 应闩而未闩：**否证成立**。
**我的加强**：不闩侧不止 1 趟。E5h15（窗 [16.091, …]）与 E5h20（close=21.249，窗 [21.249, …]）同样覆盖 21~22 s 带且同样不闩
⇒ 否证证据是 **n=3 趟 / 跨 2 个会话**，不是台账写的单趟。
**反例搜索结论**：未找到「窗覆盖 21~22 s 却闩了」的反例；但需披露——**8 个有闩趟的闩绝对时刻全距 = 20.145~22.552 s**（`_xv_s14`），
比「21~22 s」带宽（P3e 205108=20.145、204921=20.61、挂死趟 204123=22.552）。故"21~22 s"是对 hold13/14 的具体刻画，不是对闩带的完整刻画；
以 20.145~22.552 作否证靶，hold15 窗 [16.272,136.213] **同样全覆盖** ⇒ 结论不变。
**基准披露**：我的"绝对时刻"基准 = 驱动 `t0`（`_drive_c2_x_e12.py:398`，取于 `popen` 之后一行），**非进程创建时刻** ⇒ 系统性偏小一个 popen→t0 间隔（未量化，三趟同基准不影响互比）。

### (6) 闩→退间隔 2.004 / 2.008 —— hold13 CONFIRMED；**hold14 REFUTED（红项 R-1）**

命令：`python lead/.../_xv_s07_intervals.py`、`_xv_s09_boundary_e2.py`（`_raw/s07`,`s09`）

| 趟 | 台账相减口径 | 我自算原始时间戳差 `rows[-1].t − rows[latch].t` | 判定 |
|---|---|---|---|
| hold13 | 2.004 (=`9.74−7.736`) | **2.004** | CONFIRMED |
| hold14 | **2.008** (=`9.04−7.032`) | **2.005** | **REFUTED（差 3 ms）** |
| E5h10 | 2.005 (=`12.35−10.345`) | **2.004** | 同类偏差 |
| P3e 205108 | 2.009 | **2.009** | CONFIRMED |
| P3e 204921 | 2.108 | **2.108** | CONFIRMED |

根因（读驱动）：`exit_after_close_s = round(rows[-1]["t"] − t_close, **2**)`（`_drive_c2_x_e12.py:507`）已被舍入到 0.01 s（9.037→9.04），
再减未舍入到同精度的 `latch_after_close_s`（round 3）⇒ **两个不同精度字段相减产生 3 ms 伪差**；
hold13 恰因 9.74 未变位而侥幸相等。⇒ 台账「2.004/2.008」中 **2.008 是舍入产物，非测量值**（真值 2.005）。
不影响「≈2.0 s 跨会话复现」主结论（5 趟实算 2.004/2.005/2.004/2.009/2.108，带宽 ≤0.104 s）。
纪律建议：闩→退一律由 `timeline.close_rows` 原始时间戳相减，勿用 `_rec` 舍入字段。

### (7) E2 标签与伪读数来源 —— 两态/absent=0 CONFIRMED；发现台账未披露的 CPU 侧同源污染（黄项 Y-2）

`_xv_s09` 逐行取证：

| 趟 | `hook6_state_counts` | 慢行来源行（自算） | 判定 |
|---|---|---|---|
| hold13 | `{present:1, absent:0, read_fail:1}` | slow[0]↔`close_row[78]`（wait=258，**退出前**）present；slow[1]↔`close_row[79]`（**wait=0，进程已退出**）read_fail | CONFIRMED 两态、absent=0 |
| hold14 | `{present:1, absent:0, read_fail:1}` | slow[0]↔`row[71]`(258) present；slow[1]↔`row[72]`(**wait=0**) read_fail | CONFIRMED |

- read_fail 明细 `{rpm_err:299, vquery_err:5, mbi_state:null}` = 进程已退 ⇒ 读不到被注入页。`absent=0` 严格成立。
- **ws 死进程伪读数**：`ws_kb` slow[1] = **20 KB**（死进程读数），`ws_delta_kb = −129080 / −118608` 正是 `20 − 129100 / 20 − 118628`（我实算逐位复现）
  ⇒ 台账唯一引用的两个 ws 数字**全部来自跨退出的死进程读数**；台账「ws 死进程伪读数不引用」**方向正确且必要**（CONFIRMED）。
- **台账未披露**：`cpu_delta_median_s = 0.7812 / 0.7188`（我实算 median 与文件逐位一致）的 2 个样本中，**各有 1 个的区间跨过进程退出**
  （hold13 slow[1] delta=0.734375、hold14 slow[1] delta=0.578125，其配对行 wait=0）。
  `e2_fork_label=spin_x_hook6_undetermined` 的 CPU 侧门槛 `med ≥ SPIN_MIN_DELTA=0.7`（`_drive_c2_x_e12.py:103`，我自读常量）
  是由**含污染样本的中位数**触发的。剔除跨退出样本后：hold13 唯一有效 delta=0.828125、hold14=0.859375，**仍 ≥0.7** ⇒ 标签不被推翻，但有效样本 **n=1**。
  ⇒ 黄项：应对 cpu 轴加注「中位数含 1/2 跨退出样本；净退前样本 n=1」，与已给的 ws 免责对称。
- hold15 `e2_fork_label=not_triggered_no_latch / hook6_state=not_triggered / slow_rows_n=0 / ws_delta=None`（自算）⇒ 台账「hold15 无闩⇒无慢采样」CONFIRMED。

### ② 批级主张

| 主张（§474/GOAL2） | 我的独立取证 | 判定 |
|---|---|---|
| 三趟 `a8=PASS`、载体删、`stop=None`、`except 恒` | 三趟 `a8_remaining=[] a8_enum_ok=True a8_verdict=PASS carrier_deleted=True except_changed=False stop_triggered=None`；`except_before == except_at.close_last == except_at.after_kill == 6694b75e46a6e773`（三趟同一哈希） | CONFIRMED |
| Guard=1+Bail=1 | 三趟 `ra2render_close_last.log`：`EnableRC4Guard=1 EnableRC4ExitBail=1 DryRun=0`、守卫 `已装 8/8`、bail `已装 1/1`（cave 0x18000000）| CONFIRMED |
| 冻结母本 v2 `6afe2711`/earlyclose `2e970eec` 零字节 | 我实算当前盘上 sha256 = `6afe2711136c3b52…3d13b9` / `2e970eec43fe37ff…09c2e1`，与三趟 `e2_params.frozen_masters_sha256_at_import` **逐位相同** | CONFIRMED |
| 驱动 = E5 候选 `90a1890a…38d03` | 见下（我找到正向指纹） | CONFIRMED（间接指纹） |
| 「发射前 --preflight 全过 + --selftest 110 红=0」 | 见下（Y-3）：110/0 数字对 **07:18 那次** CONFIRMED；本批时点有 **pyc 导入物证（21:12:39/21:14:03 < 首趟 21:17:57）** 支持"确实跑过"，但**结果值无 stdout 留档** ⇒ 时序 PARTIAL、结果对 07:18 档 CONFIRMED |
| 短 TEMP(4 字符) | 见下（Y-4） | **UNVERIFIED** |
| 「E5 红项 R3 把闩边界降为 (11.19,16.09]，缝内从未测点」 | 我扫 `c2ab_x` 全部 **20 趟**（有 `closed_at_s`）：开区间 (11.19,16.09) 内、本批之前的点只有 `20261030T072242` 的 **11.193**——即左端点档自身（与 11.19 差 0.003 s） | CONFIRMED（措辞见 Y-5） |

**驱动身份（台账声明 90a1890a，我曾找到的最强反否证路径）**
仓库有 **3 份同名** `_drive_c2_x_e12.py`：`lead/qc161_u0400_trip/` = `f9d3f36a…`(31492 B)；`codex_e12_e5_20261030/candidate/` = **`90a1890afe356191…38d03`**(36637 B)；`codex_e12_fix_20261029/candidate/` = `75daf4f7…`(33199 B)。
趟级 `_rec.json` **不记录驱动自身哈希**（我 grep：`90a1890a`/`f9d3f36a` 均不在 `_rec` 内）⇒ 单看台账声明不可证。
**但我用代码指纹把它钉死**（`_xv_s06_driver_identity.py`）：`rec["hold_override"]` 与 `e2_params.hold_after_window_s` **只有 candidate(90a1890a) 副本会写**
（特征串存在性：`hold_override`/`normalize_hold_s`/`module_const_s`/`effective_s` 在 A=False / B=True / C=False；写点 `candidate/_drive_c2_x_e12.py:345`）。
三趟 `_rec` 均含 `hold_override={'module_const_s':6.0,'effective_s':13/14/15}` ⇒ **产出这批记录的必为 90a1890a 副本**（A/C 副本无 `--hold` seam，`protocol` 串也无法产出 `window+13.0s` 形态）。
旁证：`candidate/__pycache__/_drive_c2_x_e12.cpython-312.pyc` 的 `pyc_file_mtime = 2026-10-30 21:14:03`（**落在本批发射前**，hold13 首个产物 21:17:57），
其内嵌 `source_size=36637 / source_mtime=1793315741(07:15:41)` **与 B 件当前 stat 逐位吻合**；root 件 pyc 的 size=31492（≠）。
⇒ **CONFIRMED（正向代码指纹 + 导入时刻旁证）**，非仅采信台账声明。
> **指纹的适用边界（我自查后收紧，避免把旁证说过头）**：
> 本批三趟的**双重**正向指纹 = ①`protocol` 串为 `window+13.0/14.0/15.0 s` —— A 件（`root/_drive_c2_x_e12.py:256`）与 C 件（`fix_20261029/candidate:290`）该串**恒拼模块常量 6.0**，只有 B 件（`candidate:673` 区段）拼 `normalize_hold_s(...)`；
> ②`hold_override` / `e2_params.hold_after_window_s` 两键存在且值 = 13/14/15（B 件 `:341-345` 仅在生效值 ≠ 6.0 时写）。
> ⇒ **对 13/14/15 这三趟，指纹是排他性的**（A/C 不可产）。
> 但我**不能**反过来用「某趟无 `hold_override`」判定它不是 B 件产的 —— B 件在 `--hold 6`/缺省时刻意**不加任何新键**（`candidate/_drive_c2_x_e12.py:343` 注释「生效值==常量时零新键：--hold 6 与缺省、与修复候选逐字节等价」）。
> 具体涉及 `20261029T222811` 与 `20261029T231621`（我实读两趟 `hold_override=KEY_ABSENT`、`protocol=window+6.0s`、`e2_params.hold_after_window_s=KEY_ABSENT`）⇒ **这两趟由哪份副本产出不可区分 = UNVERIFIED**。
> （此点不影响任何主读数：② 的边界/否证/间隔只用本批 3 趟 + E5 3 趟，E5h10 的 `hold_override.effective_s=10.0` 亦属排他指纹。）

**preflight / selftest（Y-3，本线未采信门禁）**
`evidence_selftest_run1.txt` 与 `run2_direct_entry.txt`：我实计数 **[OK] 行 = 110、[RED]/[FAIL] 行 = 0**，末行「110 项，红=0 ⇒ ALL-PASS」，两份输出**逐字节相同**（sha256[:16] 同 `e0788f43…`）；文件内声明 e12=90a1890a…/earlyclose=2e970eec…/v2=6afe2711… 与我实算一致 ⇒ **110/0 这一数字在"有档的那一次运行"成立（CONFIRMED）**。
`evidence_preflight.txt`：[OK] 10 行、末行「preflight: 全过」CONFIRMED。
**但**：这些档的 mtime 全在 **07:17~07:18**（E5 批时点）；我用 `_xv_s12` 扫 `lead/` 下 21:00~21:30 全部 mtime（21 个文件，均为趟产物/两篇 result 书），**无任何 preflight/selftest/evidence 留档**；`c2ab_x/_preflight/` 最新子目录仍是 `20261029T195838`。
⇒ 台账 §474/GOAL2 所称「**本批**三趟发射前 --preflight 全过 + --selftest 110 红=0」的**时序主张不可复核 = UNVERIFIED（缺盘上档）**。
（我未自跑 selftest：该套件会 `subprocess.run` 驱动并写 pyc，且含 `--live` 分支，属派单禁止的"可能启动游戏/写状态"操作 ⇒ **主动放弃该核验**，不做等价替代。）
静态计数亦不可用于证伪 110：套件内 `t()` 由循环生成（F 组变异项名等），我的标号正则只数到 78 个唯一标号 ⇒ 静态法失效，不据此判红。

**短 TEMP（Y-4，UNVERIFIED）**
两趟 `_rec.json` 内 **不含** `TEMP`/`tmp` 字段；`out_dir` 在 `lead/qc161_u0400_trip/c2ab_x/<stamp>` 下，载体 `ct/c…` 已随 `carrier_deleted=True` 删除 ⇒ **无路径长度留痕可核**。
对照：①（harness7）趟**有** `CARRIER.pathlen_near_limit = {max_chars:130, near_warn_chars:127}` 显式读数，②（E12 驱动）无对应字段
（驱动有 `CARRIER_PATH_MAX=130` 闸，但拒收时**不落值**）⇒ ② 的「短 TEMP(4 字符)」我**无法从原始记录验证**，只能验证"载体已删+无残留"。

---

## 2. ① 战斗 2 趟 —— 逐条亲算

### (8) gate —— CONFIRMED（含口径披露 Y-6）

直接回读 `measure_w0.json.gate`：q `pre_fps15=31.34 / units0=974 / ok=true`；r `pre_fps15=30.716 / units0=941 / ok=true`
⇒ 台账 31.34/30.72（r 系 round3→2 位）与 974/941 **CONFIRMED**。
`map_sha256=f3bb0a4efded…`、`gamemd_sha256=73201cc02149…`、`hz=500`、`verdict=ok`、`error=None`（两趟）CONFIRMED。
**口径披露**：件内 `gate.gate_fps15_min = **3.0**`（`qc151_trip.harness7.py:3847`「窗前在局闸：1.5 s 内推进 ≥3 fps」），
**「≥25」不是件内 gate**，而是 §474 台账 `:5823` 的 **V11-a 外部判档口径**（GOAL1_BATCH1 明确写「≥ V11-a 门 25」）。
⇒ 「≥25 ⇒ 31 档在场」按 V11-a 口径成立；但不得读成"件内 gate 通过即档位达标"。列黄项（口径易混，非台账之错）。

### (9) 战斗期内长停顿 = 0 —— CONFIRMED（我先用错口径，现披露两法）

`_xv_s03_battle.py`（错法留档）+ `_xv_s03b_recompute.py`（正确口径）。harness 明文规定 **D-1 帧沿差分**：
`frame_edges[k]=(f, t_first_observed)`，帧时=相邻沿时刻差；「禁用 bench『相邻轮询 dt/df』式——500 Hz 轮询下塌缩为轮询周期 2 ms」（`qc151_trip.harness7.py:4700-4712`）。
我第一次按"相邻样本差"算出 p50≈2.51 ms / fps≈477（**与文件 31.9 ms 差一个数量级**），即该被禁口径；改按帧沿重算后逐位复现：

| 量 | 台账 | 文件 `stats` | **我自算（帧沿口径，500 Hz 原始 t/f）** | 判定 |
|---|---|---|---|---|
| q `frame_ms p50/p90/p99/max` (ms) | 31.9/37.2/44.4/68.4 | 31.9048/37.1723/44.4283/68.3972 | **31.905 / 37.1722 / 44.4286 / 68.397** | CONFIRMED |
| r `frame_ms p50/p90/p99/max` (ms) | 32.1/36.0/41.4/45.7 | 32.1057/36.0349/41.3557/45.6832 | **32.106 / 36.034 / 41.3556 / 45.683** | CONFIRMED |
| q `fps_avg` | 31.1(2) | 31.12026 | **31.1203**（=logic_frames/span=778/24.9998） | CONFIRMED |
| r `fps_avg` | 31.3(2) | 31.32041 | **31.3204** | CONFIRMED |
| **W0 内 frame 连续不变 ≥0.5 s 区段数** | **0 / 0** | `max_stall_s` 0.068397 / 0.045683 | **0 / 0** | CONFIRMED |
| 阈值敏感性（我自加） | — | — | **0.2 s→0 / 0.3 s→0 / 0.5 s→0 / 1.0 s→0**（两趟）；帧沿间隔 ≥0.1 s 者亦 **0** | CONFIRMED（非阈值巧合） |
| `tick_miss`（>1.5×p50）| 未报 | 5 / 0 | **自算 5 / 0**（按 `MEASURE_TICK_MISS_FACTOR=1.5`，`:3850`） | CONFIRMED（与文件一致） |
| 采样完整性 | 未报 | `hz_effective` 500.1 | 跨度 24.9998/24.9997 s、样本 12502/12502；**最大采样空洞 5.3 ms / 8.3 ms**（无 >0.1 s 空洞）| CONFIRMED |
| 帧跨度 | 2955→3733 / 3100→3883 | — | **2955→3733 / 3100→3883** | CONFIRMED |
| `logic_frames`/`n_edges` | 未报 | 778/779 · 783/784 | 自算 run 数 **779 / 784**（=n_edges）| CONFIRMED |

⇒ **「战斗期内长停顿=0」成立**，且与文件 `max_stall_s`（≤0.068 s）互证；`n_multi_advance=0` ⇒ 无跳帧合并失真。

### (10) 活动战斗证据 —— units 轨迹 CONFIRMED；「真交火」的机制归属 UNVERIFIED（Y-7）

`counters[]` 原始 25 行逐秒回读：

| 趟 | 台账 | 我自算 | 判定 |
|---|---|---|---|
| q | 953→854（−99，逐秒降）| 953→854，净 **−99**；24/24 步**严格递减**，无持平无上升 | CONFIRMED |
| r | 923→842（−81，逐秒降）| 923→842，净 **−81**；**23/24 步降，idx=16 处持平（866→866）** | 净量 CONFIRMED；「逐秒降」**REFUTED（红项 R-2）** |
| 非静态在场 | 主张成立 | q 变化点 24/24；r 23/24；`infantry` q 231→203(17 点)/r 200→174(13 点)；`techno` q 1189→1062(**24/24**)/r 1128→1020(**24/24**)；`g` q 1236→1120(23 点)/r 1182→1059(23 点) | **CONFIRMED**（确为动态衰减，非静态在场）|
| 末点时刻 | — | `counters[-1].t_rel = 24.028 / 24.030 s`（span 25 s）⇒ 下降贯穿 W0 全程，窗内无转平段 | CONFIRMED |

**我挑出的证据基础弱点（台账未表述）**：对方侧 `b` 全程仅 **5 → 5(q) / 5 → 4(r)** 个单位，且 `aircraft` **恒 0**；
units 的 −99/−81 降幅几乎全部落在 `g`/`techno` 侧（q 降 116/127，r 降 123/108），**与 b 侧损失无对应量级**。
⇒ 「units 逐秒降 = 真交火」是**推断**（也可能是己方单位解散/被移除/脚本消耗）；`units/g/b/techno` 的语义在 §474 与 GOAL1 中**均未定义**（仅驱动注释 `:3949-3968` 给出地址，语义未注）。
⇒ 判定：**「活动战斗窗内 units 持续下降且非静态在场」CONFIRMED**；**「= 真交火」UNVERIFIED（无对手方对应损失、字段语义未定义）**。
（地址：`MEASURE_UNITS_VA=0x008B4118 / G=0x008A03A0 / B=0x00A8EB50 / TECHNO=0x00A8EC88`，`qc151_trip.harness7.py:3834-3841`，零写入 `ReadProcessMemory`。）

### (11) W1/W2 终局定性 —— CONFIRMED（冻结起点均晚于 units 停变点，无战斗期冻结误归）

`_xv_s04_windows.py` + `_xv_s05_freezealign.py`（原始 t/f 逐窗重算）：

| 窗 | 台账 | 我自算 |
|---|---|---|
| q·W0 | 停顿 0 | frame 2955→3733，≥0.5 s 冻结 **0**；units 降到窗末（末步 t_rel=24.028）|
| q·W1 | 未报（台账只提 W2）| frame **3733→4515**，≥0.5 s 冻结 **0**；units 852→811（24 步中 **21 降 / 3 持平**，持平 idx=6,10,23，**无上升**），最后变化 idx=24(t_rel=24.025)；`b` 5→**1**（未归零）|
| q·W2 | 冻于 4636、21.2 s、units 静态 811 | frame **4516→4636**，冻结区段 **1 条：frame=4636，起于 t_rel=3.844 s，持续 21.156 s**（台账 21.2 ✓）；units 全 25 行恒 **811**；`b` 于 idx=1(t_rel=1.001) **归零** |
| r·W0 | 停顿 0 | frame 3100→3883，冻结 **0**；units 降到窗末(24.030) |
| r·W1 | 冻于 4367、9.4 s | frame **3883→4367**，冻结 **1 条：4367 起于 t_rel=15.563 s，持续 9.436 s**（台账 9.4 ✓）；units 839→**828**，最后变化 idx=12(**t_rel=12.016**)，`b` 于 idx=10(**t_rel=10.011**) 归零 |
| r·W2 | 恒 4367、units 静态 828 | frame **4367→4367**（零推进），冻结 **1 条覆盖全窗 24.998 s**；units 恒 828；`b` 恒 0；`stats.fps_avg/frame_ms_max = null`（零推进按纪律写 null）|

**冻结起点 vs units 停变点（台账要求我核的关键）**：
- q·W2：冻结起于 3.844 s，**晚于** units 停变（W2 首步即持平，t_rel=1.001）**2.843 s**；亦晚于 `b` 归零(1.001)。
- r·W1：冻结起于 15.563 s，**晚于** units 最后变化(12.016) **3.547 s**，晚于 `b` 归零(10.011) **5.552 s**。
- r·W2：冻结自 t_rel=0 起，units 停变在 t_rel=1.0（差 −1.0 s）⇒ 二者同处终局静止段，**不存在战斗期被误归**。
⇒ **两趟 W0（活动窗）零冻结；所有 ≥0.5 s 冻结都发生在 units 停变/对方归零之后或同处终局静止段**
⇒ 台账「W1/W2 帧冻结伴 units 转平/一方归零 ⇒ 终局帧冻结，非战斗卡顿」**CONFIRMED，且未发现误归项**。
跨窗帧号衔接自洽：q 3733(W0末)=3733(W1首)→4515 | 4516→4636；r 3883→4367→4367 ⇒ 三窗连续，无跳窗。
`measure_forensics_w*` 显示 `focus_ok=true`、`fg_hwnd == game_hwnd`（q 5046414 / r 19991730）⇒ 前台=游戏窗，排除"失焦限流"解释。

### (12) 诚实边界的结构性解释 —— CONFIRMED，但对照非单一变量（黄项 Y-8）

| 对照量 | 10 档 `l3_20261021` | 本批 31 档 q / r | 台账 |
|---|---|---|---|
| `gate.units0` | **1342** | 974 / 941 | 1342 vs ~950 CONFIRMED |
| `gate.pre_fps15` | **10.023** | 31.34 / 30.716 | 档位差 CONFIRMED |
| W0 起始 frame | **387** | **2955 / 3100** | 「10 档≈387 / 31 档≈2955~3100」CONFIRMED |
| W0 frame 末 | 606 | 3733 / 3883 | — |
| W0 `fps_avg` / `p99`/`max` (ms) | 8.76 / 217.0 / 296.6 | 31.12 / 44.4 / 68.4 | 帧时量级 CONFIRMED |
| W0 counters 首末 units | 1330→1270（−60）| 953→854 / 923→842 | — |

⇒ 结构性解释（慢帧使测量落点更早→10 档能撞满员瞬间；快帧把窗推到交火后段→units0 已衰减）**方向被数据支持**：
起始 frame 387 vs 2955/3100 相差 ~2570 帧；按各自 fps 折算，10 档 ≈ 293 s 游戏进度、31 档 ≈ 83 s——
即"同一墙钟协议在两种帧率下落到完全不同的游戏进度"，与「窗起点绑墙钟而非帧计数」的归因一致。
`map_sha256` 三趟同为 `f3bb0a4efded…`、`gamemd` 同为 `73201cc0…`、`carrier-create-from` 同为 `_src_L3_sf10c_20261021`（88 个文件，与 `_src_L1_sf8_20261020` 同件数）⇒ 地图/母本同。
**但**：10 档趟的 harness = `…/qc151_harness_merge_20261021/qc151_trip.**harness3**.py`，本批 = `qc151_trip.**harness7**.py`(`sha16 d019e8be`)，
且 10 档 argv **无** `--h7-keep-rect-wait`（本批有）⇒ 跨档对照实际含 **3 个差异**（档位 / harness 大版本 / keep-rect 臂），非「仅档位变」。
⇒ 台账该条**结论方向成立**，但「唯一变量=档位」的对照严格性**未成立** ⇒ 黄项。

### ① 批级主张

| 主张 | 我的独立取证 | 判定 |
|---|---|---|
| 两趟 rc=0、用时 259.7/262.8 s、残留进程 0、载体残留 0 | `_launch_result.json`：`rc=0 duration_s=259.7/262.8 carriers_deleted=True leftover_procs=[] harness_sha16=d019e8beecfb5fd8 trip_id=…Q/…R` | CONFIRMED |
| harness7 `d019e8be` | 我实算 `sha256(qc151_trip.harness7.py)[:16] = d019e8beecfb5fd8`（口径=sha256 前 16 hex，与文件字段一致）| CONFIRMED |
| 原版直启**零注入**、不装 rc4 guard/bail、不 `--allow-loader` | argv 全量回读：仅 `--measure 1 --fullscreen --evid-diff --probe-frames 3900..6000 --h7-keep-rect-wait`，**无 `--allow-loader`**；`LAUNCH.via_loader=false`、`u8_allow_loader_authorized=false`、`debug_flags_used=false`；`s4_module_table.txt` 实测 10/11 个模块 = gamemd.exe + ntdll/KERNEL32/KERNELBASE/wow64×6（+apphelp），**无 ra2render.dll / 无 ra2rc4guard**；`S4.ra2render_hits=[] ra2loader_hits=[] hit_count=0 s4_gate=pass`；`CTRL1 sha256_pre==sha256_post==73201cc0…`、`CTRL2 bytes_pre==bytes_post=="4E 6F 20 4E 61 6D 65 00" @0x829284` | **CONFIRMED**（正向证据充分） |
| 两趟同会话（13:10:38，无中途重启） | ① 记录**无** `boot_wallclock` 字段 ⇒ 我改用 `measure_*.t_abs0` 与 `samples.t[0]`（`t_clock=time.perf_counter`）：q/W0 `t_abs0−boot=27527.313` vs `samples.t[0]=27527.346953`（差 0.0335 s）；q/W1/W2、r/W0/W1/W2 六窗差 **0.0335~0.0357 s**；折算 27527 s=7.646 h→20:50、28240 s=7.844 h→21:01，与目录 mtime（20:46–20:50 / 20:58–21:02）吻合 | **CONFIRMED**（我另辟的独立锚点法） |
| 载体短路径 129/130 | `CARRIER.pathlen_near_limit={max_chars:130, near_warn_chars:127, dirs:[…]}` | CONFIRMED（近限报警在册，非"短"） |
| 无新异常 | `EXCEPT.pre_line_count=post_line_count=1046`、`new_exception_count=0`；`WER.wer_report_count=0 wer_verdict=NO_NEW_REPORT` | CONFIRMED |
| 「31 档 × ≥900 交火」格此前不存在 | 我扫全树 **31 个**含 `measure_w0.json` 的趟目录：满足 `pre_fps15≥25 ∧ units0≥900` 的**恰为本批 2 趟**；31 档趟 units0 降序 = 974/941/**842**(t55k)/732/702/491/251/24x…；units0≥900 的趟只有 974/941/**1342(pre=10.023，10 档)** | **CONFIRMED** |
| 负载上界 842→974 | t55k_20261020 `units0=842 pre=31.401`、W0 冻结 **0**、units 841→809 —— 我实测复现 | CONFIRMED |

---

## 3. 红项（我的独立重算与台账读数不符）

- **R-1 ②hold14 闩→退间隔：台账 2.008 s，原始时间戳实算 2.005 s。**
  台账 `:19791`/GOAL2:31 报「2.004 / **2.008**」；`_rec` 的 `exit_after_close_s` 已被驱动 `round(…,2)` 舍入（9.037→9.04，`_drive_c2_x_e12.py:507`），再减 `latch_after_close_s`(round3)=7.032 得 2.008。
  由 `timeline.close_rows[70].t=1793366532.116 → close_rows[72].t=1793366534.121` 直接相减 = **2.005 s**。E5h10 同类（台账 2.005，实算 2.004）。hold13 恰无位变故 2.004 相等。
  ⇒ 影响面：仅 3 ms，不推翻「≈2.0 s 跨会话复现」；但**读数本身不可由原始数据复现**，属精度混用产生的伪值。
- **R-2 ①r 趟 units「逐秒下降」：实算 24 步中有 1 步持平（idx=16，866→866）。**
  台账 `:19782` 与 GOAL1:24 表格均写「923→842（−81，**逐秒降**）」。净 −81、23/24 步降成立；「逐秒（每步）降」不成立。
  ⇒ 影响面：措辞级；不影响"非静态在场/活动战斗窗"判定。q 趟为严格 24/24 递减（无此问题）。

> **R-3 撤回声明（对账员自身判据错误，留档不掩盖）**
> 我在 §7 一度据 `STALL_ANATOMY_raw.json` 的 `chpts`（units **整窗**变化点数）把台账前提件全称句「既有 31 档战斗趟长停顿**全是**终局帧冻结」判为红项 R-3。
> **该判据是错的**：整窗变化点多，不等于**冻结期内** units 仍在变。用正确判据重验后**撤回**。
> 命令：`python lead/codex_round_20261030/XVERIFY_TRIPS_20261030/_xv_s15_recheck_r3.py`（→ `_raw/s15_stdout.txt`）
> 判据：对每条 `stall ≥ 0.5 s` 条目回**原始** `measure_w*.json` 重算冻结起点 `t_rel`，再数「冻结起点**之后**的 units 变化步」。
> 结果：**24 条中 23 条 = 「冻结后 0 变化步」⇒ 终局成立**；两条我原先点名的"反例"实为终局：
>  - `archive_T47/w0`（pre=31.405/u0=251）：冻结起 t_rel=**18.380**，units 停变于 **13.018** ⇒ 冻结晚停变 **5.362 s**，属终局。
>  - `l1a_20261020/w2`（pre=31.397/u0=732）：冻结起 **23.218**，停变于 **21.030** ⇒ 晚 **2.188 s**，且对方 `b` 已归零 ⇒ 属终局。
> 唯一非零项 `l1_20261023e4/w2`：该窗 **frame 恒 0**（W1 已 3557→**0**，即游戏已退出 ⇒ 台账原文即称「W1W2 **空窗**」），
> 冻结自 t_rel=0 起、units 在 12.016 s 有 1 步变化 ⇒ 这是**终局之后空窗内的残值/清理变化**，不是「战斗期内长停顿被误归终局」；
> 台账该句已用「units 静态 **/W1W2 空窗**」并列涵盖之 ⇒ **不构成反例**。
> **最终判定：§474 前提件「既有 31 档战斗趟长停顿全是终局帧冻结」= CONFIRMED（23/23 可判条目 + 1 条空窗内不属战斗期）。**
> 连带纠正我先前的一句推论：`archive_T47/w0` 并非「31 档活动窗内见长停顿」的反例（其冻结在 units 停变之后）⇒ 该推论一并撤回。

## 4. 黄项（表述过强 / 口径需收紧）

- **Y-1 ②「同会话闩边界收窄到 close∈(14.997,16.272]」过强。** 每点 n=1；1.275 s 内零采样（未收窄到点）；且 E5 已有不闩点 16.091 ⇒ 本批**未收紧上界**（16.09→16.272 反而退 0.18 s），收窄全部来自下界。GOAL2 自认「未收窄到点」，但 §474 主读数句未带此限定。
- **Y-2 ②E2 的 cpu 轴免责缺失。** 台账只对 ws 声明「死进程伪读数不引用」，但 `cpu_delta_median_s`（0.7812/0.7188）的 2 个样本**各含 1 个跨进程退出的区间**（hold13 slow[1]=0.734375 / hold14 slow[1]=0.578125，配对行 `wait=0`）；`spin_x_hook6_undetermined` 的 CPU 门槛（≥0.7）由含污染样本的中位数触发。剔除后仍 ≥0.828/0.859 ⇒ 标签不被推翻，但有效样本 **n=1**，应显式加注。
- **Y-3 ②「本批三趟发射前 --preflight 全过 + --selftest 110 红=0」结果数值不可复核，但时序侧我找到物证（对我自己初判的下调）。**
  - 我能独立确认的：`evidence_selftest_run1.txt` 与 `run2_direct_entry.txt` 我实计数 **[OK]=110 行、[RED]/[FAIL]=0**，末行「110 项，红=0 ⇒ ALL-PASS」，两份输出**逐字节相同**；文件内声明 e12=90a1890a…/earlyclose=2e970eec…/v2=6afe2711… 与我实算一致 ⇒ **110/0 在"有档的那一次运行"成立（CONFIRMED）**。`evidence_preflight.txt` [OK]=10 行 + 「preflight: 全过」CONFIRMED。
  - **但这两份档的 mtime 全在 07:17~07:18（E5 批时点）**，非本批。
  - 我随后找到的**时序物证**（`_xv_s12` + 后续取证）：`codex_e12_e5_20261030/candidate/__pycache__/` 四个 pyc 的 **文件 mtime = 2026-10-30 21:12:39（v2/earlyclose）与 21:14:03（e12/selftest）**，
    **全部早于本批首趟产物 21:17:57**；pyc 内嵌 `source_size=36637 / source_mtime=1793315741(=07:15:41)` 与源件当前 stat 逐位吻合 ⇒ 21:14 那次导入加载的就是现在盘上这份 90a1890a 件。
    导入路径可溯源：`--selftest` 分支 `importlib.util.spec_from_file_location("e12_selftest", HERE/"_drive_c2_x_e12_selftest.py")`（`candidate/_drive_c2_x_e12.py:669-675`）会产 selftest.pyc；
    `--preflight` 分支（`:676-680`）走 `V2.preflight()+extra_preflight()`，其模块导入产 v2/earlyclose.pyc。
  - **仍不能判定的**：pyc **不落 stdout** ⇒ 无法证明 21 点那次运行的**结果是"全过/110 红=0"**，也无法排除该次导入另有用途（如零字节复验）。
    另需披露一处**反证**：selftest 内部只把 *基线件(fix 候选)* 与 *变异件* 复制到 temp 目录 `exec_module`（`_selftest.py:431,864`），**不会**在 candidate 目录产 e12.pyc ⇒ e12.pyc 本身来自"以模块方式导入 e12"的另一次动作，我不能把它直接归给 `--selftest`。
  - ⇒ 判定：**时序主张 = 有旁证支持但未坐实（PARTIAL）**；**结果数值 = 依赖 07:18 留档（对 07:18 那次为 CONFIRMED，对本批为 UNVERIFIED）**。
  - 附带收益：我实算 v2/earlyclose **当前盘上 sha256** = `6afe2711…3d13b9` / `2e970eec…09c2e1`，与 §474/GOAL2 声称的冻结母本哈希、及三趟 `e2_params.frozen_masters_sha256_at_import` **逐位相同**
    ⇒ ③「v2/earlyclose 零字节」= **CONFIRMED（直接哈希复算）**；e12 候选件当前 sha256 亦 = `90a1890a…38d03` ⇒ 该件从 07:15:41（其 mtime）至我读取时内容未变（mtime + 哈希 + pyc 内嵌 size 三证一致）。
- **Y-4 ②「短 TEMP(4 字符)」在 ② 记录内无留痕。** `_rec` 不含 TEMP/tmp 字段，载体已删；② 驱动有 `CARRIER_PATH_MAX=130` 拒收闸但不落实测值 ⇒ 只能验证"载体已删 + a8_remaining=[]"，长度本身 UNVERIFIED。（① 侧有 `CARRIER.pathlen_near_limit` 显式读数，可作补字段范式。）
- **Y-5 ②「缝内从未测点」的精度。** 我扫 20 趟：开区间 (11.19, 16.09) 内本批之前有 1 个值 —— E5 hold10 的 **11.193**（即左端点档自身，与 11.19 差 3 ms）。主张实质成立，但严格措辞应为「除左端点档自身外，缝内零测点」。
- **Y-6 ①「gate」与「V11-a 门 25」是两套口径。** 件内 `gate.gate_fps15_min=3.0`（仅判"在局"）；`pre_fps15≥25` 是 §474:5823 的 V11-a **外部**判档门。GOAL1 有标注「≥ V11-a 门 25」，但台账若把两者并读成"gate 通过 ⇒ 31 档达标"即口径混用。另：`gate_fps15_min` 为 3.0 意味着 **gate.ok=true 对档位毫无判别力**，档位判定完全依赖 V11-a 外部值。
- **Y-7 ①「真交火」证据基础偏弱（建议降级措辞）。** 对方 `b` 仅 5→5(q)/5→4(r)，`aircraft` 恒 0（0/24 步变化），而 `units` 的 −99/−81 与 `g`(−116/−123)、`techno`(−127/−108) 同向下降、`infantry`(−28/−26) 亦降 ⇒ **降幅方向全部落在己方侧计数上，b 侧几乎不动**，
  故「units 下降 = 交火歼灭」缺对手方对应证据；且 §474/GOAL1 **未定义** `units/g/b/techno` 各自计数对象（我只在 `qc151_trip.harness7.py:3834-3841` 读到 VA，语义无注）。
  注意我**不声称** units ⊂ g/techno（未证），只陈述二者同向、b 侧不动。可确证的是「活动窗内 units 持续单调下降、非静态在场」；「= 交火歼灭」目前是推断。
- **Y-8 ①跨档对照非单一变量。** 10 档趟用 `qc151_trip.harness3.py` 且**无** `--h7-keep-rect-wait`，本批用 `harness7(d019e8be)`+keep-rect ⇒ 「units0 随档位变」的解释还混有 harness 版本与测量臂差异（同源的 `frame_edges` schema 缓解但不消除）。
- **Y-9（附加）①W1/W2 终局读数在台账与原始记录间存在"归属"缝隙。** 台账 q 只报 W2（"q：W2 于 4636 冻 21.2s"）、r 只报 W1，而实算 q 的 **W1 无冻结且 units 单调下降（852→811，21 降/3 持平/0 升）**、r 的 W1 冻结前有 9 个 units 变化步（t_rel<15.563）⇒ 这些"冻结前仍在变化"的步都在对方归零之后（r：b 于 10.011 s 归零 vs 冻结 15.563 s），终局定性仍成立，但台账省略了「冻结前有变化步」这一事实，宜显式写出以免被读成"冻结即静止"。

## 5. 未验证 / 无结论（诚实账）

1. **② 本批是否真在发射前重跑过 preflight/selftest，及其结果值**：结果数值 **UNVERIFIED**（pyc 只证明"发生过一次导入"，不落 stdout；且 e12.pyc 不能直接归给 `--selftest`，见 Y-3）；发生时刻 **有物证（21:12:39/21:14:03 早于首趟 21:17:57）**。我**未自跑** selftest——它会 `subprocess.run` 驱动并含 `--live` 分支（`_drive_c2_x_e12_selftest.py:726-818`），属派单明令禁止的"可能启动游戏/写状态"风险面；我宁可留空也不做等价替代。
2. **②「短 TEMP(4 字符)」**：UNVERIFIED（Y-4）。
3. **①「units 下降 = 交火」**：UNVERIFIED（Y-7）；`g/b/techno/units` 计什么对象，台账与本线均无定义来源可查。
4. **①「31 档 × 1342 峰值交火」**：账上仍无读数，本线亦无法测（禁真机）⇒ 无结论（与台账诚实边界一致）。
5. **② 闩的"写者/进环"机制**：本线零运行期取证能力（不发射、不读内存），机制归属交回执行线裁定。我能给的只是**读数侧线索**（§6-1/6-2：Δ 二分 + 不闩趟 hwnd 归零聚集 ~21 s 带 ⇒ 支持"存在绝对引擎阶段边界、闩取决于关窗与该边界的先后"，与 §474 中介说同向，**非反证**）。台账自述「进环仍是机制相容(not contradicted)，非直证」——该自我限定我核对为**恰当**。
6. **`hz_effective` 文件 500.1 vs 我 500.04**：口径差（文件用 `len(samples)/span`=500.08→500.1，我用 `(len−1)/span`），非矛盾，**不作为红项**。
7. **`max_stall_s` 与 `frame_ms_max` 是否同一量**：我核对为 `round(frame_ms_max/1000, 6)`（q 0.068397 / r 0.045683 精确吻合）⇒ 本批 `n_multi_advance=0`、全为 df=1，两者退化为同值；不外推。
8. **绝对时刻基准**：我的"闩绝对时刻"以驱动 `t0` 为基准（`popen` 后一行），非进程创建时刻 ⇒ 系统性偏小一个未量化间隔；趟间互比有效，绝对值不宜对外引用为"进程已运行秒数"。
9. **本线身份局限**：我是 Qwen 家族异族核验者，只能做**原始记录回读 + 独立重算 + 代码溯源**；真机复现、Leader 终端态操作（闸值传入方式、"亲验"过程）、以及任何跨会话因果裁定，均超出本线可证范围。§474 的「③ 零历史改写 / 未派优化补丁」等流程性主张我只核了产物侧可查项（哈希/argv/残留/模块表），流程性部分 UNVERIFIED。

## 6. 本线增量线索（台账未表述；供执行线裁定，不作为对 §474 的裁定）

1. **「关窗→hwnd 归零延迟 Δ」在 11 趟上对闩/不闩完美二分**（`_xv_s11_delaydisc.py`，全部由原始 `close_rows` + `close_delivery.t − closed_at_s` 自算）：
   - 有闩趟（8 个）：hold13 **0.101** / hold14 **0.101** / E5h10 **0.101** / 1029T2228 0.122 / 1029T2316 0.101 / P3e204123 **0.102** / P3e204921 0.102 / P3e205108 0.100 ⇒ **max 0.122 s**。
   - 无闩趟（3 个）：hold15 **4.822** / E5h15 **5.023** / E5h20 **0.402** ⇒ **min 0.402 s**。
   - 二分判据 `Δ<0.15 ⇒ 闩 / Δ>0.35 ⇒ 不闩` 在 n=11 上零例外。
   - **会话可证性诚实披露（我重数后更正）**：8 个闩族趟中只有 **4 趟**的 `_rec.boot_wallclock_ms_at_start` 有值可证会话
     （hold13=1793337038119 / hold14=…113 / E5h10=1793256614230 / 1029T2316=1793256614228）⇒ **可证会话 = 2 个**（10-29 会话、10-30 会话）；
     另 **4 趟**（1029T2228、P3e204123、P3e204921、P3e205108）该字段为 `None`（旧 schema，未记 boot），
     其会话归属只能由 `close_delivery.t` 换算的墙钟日期（10-28 20:49/20:51、10-29 22:28）**推定**，非字段可证。
     ⇒ 按可证口径，本二分覆盖「**2 个已证会话 + 4 趟仅日期推定**」，不是我先前写的「跨 3 会话」。
   ⇒ 这把 §474 的「关窗时机经『关窗时引擎阶段』中介」**具体化**为可测判据：**hwnd 是否紧跟 WM_CLOSE 归零**（即引擎当时是否还在响应关窗的 destroy 路径）决定后续闩与否。
   注意 Δ 只判「是否闩」，**不判「是否正常退」**——挂死趟 P3e204123 Δ=0.102（属闩族）但 `exitstate==1` 连续 **1017 行**、窗末 `wait=258` 不退。
2. **不闩趟的 hwnd 归零绝对时刻聚集在 ~21 s 带**：hold15 **21.094** / E5h15 **21.114** / E5h20 **21.651**；而闩趟的 hwnd 归零在 close+0.1 s（绝对 7.2~15.1 s，早于该带）。
   ⇒ 存在一个 **绝对 ~21 s 的引擎事件**（与 `close` 无关），它对「闩」不是充分条件（3 个不闩趟的 hwnd 归零恰在该带内却不闩），但它是"关窗未即时生效"的标志。
   这条与 §474「否证纯绝对时钟」**不冲突**（否证的是"到点就闩"），反而说明**存在绝对时刻的引擎阶段边界、而闩取决于关窗与该边界的先后**。台账的中介说与此同向。
3. **闩态是持续态而非脉冲，⇒ 0.1 s 快采样不存在漏检风险**（加固 (5) 否证的有效性，台账未写）：
   `exitstate==1` 在 hold13/14/E5h10 各出现 **2 行连续**（闩→退出只有 2 次采样），在挂死趟 P3e204123 出现 **1017 行连续**，
   而三趟不闩记录 **0 行**（且采样节律 median 0.1 s、max 0.104 s 无空洞）⇒ 「不闩」不是采样盲区造成的假阴。
4. **本线新发现：同一「闩族」内部按「`exitstate==1` 连续段长度」可再分「即退 / 挂死」两支**（n=1 证据，不作结论，交执行线裁定）：
   即退趟连续段 = **2~21 行**（hold13=2、hold14=2、E5h10=2、1029T2228=3、P3e204921=21、P3e205108=20，全部 `exited=True / exit_kind=natural / code=0`）；
   挂死趟 P3e204123 连续段 = **1017 行**（=其全部 `exitstate==1` 行，自首 idx=153 直到窗末）、`exited=False / still_running_at_watch_end`、窗末 `wait=258`。
   （schema 披露：P3e 10-28 三趟的 `_rec` **无** `latch_detected/latch_row_index` 键，其闩首行 idx 系**我由 `close_rows` 自行推得**；1029T2228 有键且 `latch_row_index=132` 与我推得的 first idx 一致。）
   两支的 Δ 同属 <0.15 族 ⇒ **Δ 判"是否闩"，连续段长度才判"闩后能否收尾"**。
   这直接关系 ② 的硬门槛口径：§474 记「挂死单例 T204123 未在批内复现」，而我的跨趟读数显示——
   复现挂死所需的**不是**新的 close 档位，而是「闩发生但收尾未完成」这一第二重条件；本批 3 趟的 Δ/闩族归属与 T204123 并不相同（hold15 属不闩族）。
   ⇒ 只读盘上数据可给的**候选补点方向**（不派真机，仅供裁定）：与 T204123 **同属 Δ<0.15 闩族**的档位（本批 hold13/14 即在此族）才是"可能即退也可能挂死"的高信息区
   ——本批两趟即退的 n(1)=2，与 T204123 的 1017 差三个数量级，说明二者差异发生在**闩之后**，而非关窗时机上；
   而 hold15 落在 Δ=4.822 的不闩族，只能证"不闩"，**对挂死复现的信息量本就最低**。
   ⇒ 附注：§474「挂死单例 T204123 未在批内复现」为事实陈述（无误），但若据此认为本批 3 趟都同等针对挂死，则高估了 hold15 的作用——
   严格说本批只有 hold13/14 与 T204123 同族可比。

5. **hwnd 与 singleton 的归零步位可作「引擎阶段」的第二轴**：三趟不闩记录里 `hwnd==0` 与 `singleton==0` 出现在**同一行**（hold15 idx=48、E5h15、E5h20 同形）；
   而所有闩族趟二者也在同一行但极早（hold13/14 idx=1，即 close 后 **0.101 s**）。⇒ 两轴同步 ⇒ 二者反映同一次 destroy/teardown 节拍，
   可用来区分「关窗被即时处理」与「关窗排队到 ~21 s 边界才被处理」。

## 7. 台账 §474 / §475 其他读数

- §474「趟数 24→**29**（本批 5 有效：①2+②3）」：与 `ROUND_DELIVERY_20261030.md:30`「本批有效 5 趟（24→29）」一致；`①单趟≈260s、②单趟≈27s` 我核到 `duration_s=259.7/262.8` 与 ② 三趟产物 mtime 跨度（21:17:57→21:18:07 ≈ 10 s 落盘 + 发射≈27 s）量级相符 ⇒ 趟数账 **CONFIRMED**。
- **黄项 Y-10**：`GOAL1_BATCH1_RESULT:16` 写「趟数账 24 → **26**」、`GOAL2_BATCH_E5GAP:24` 写「趟数账 24 → **27**」，两篇都以 24 为基线各自加自己的趟数 ⇒ GOAL2 的 27 **不是终账**（终账 29），且两篇并读会让人以为 ② 只贡献 1 趟。建议 GOAL2 改写「26→29（② +3）」或标注"批内相对"。
- §474「三趟 a8=PASS」我核 ② 三趟皆 `a8_verdict=PASS`；① 两趟该组字段为 `A8.a8_verdict="N/A"`（harness7 侧不适用）⇒ 台账把 a8 只归给 ② 是对的（**未误用**，此点我特意核对）。
- §474「既有证据离线复算 …`STALL_ANATOMY_raw.json` 证：31 档战斗趟（t55k 842u/l1a 732u/e4 702u）长停顿**全是终局帧冻结**（units 静态/W1W2 空窗）」：
  我**第一次**筛 `stall≥0.5 s`（24 条）时用 `chpts`（整窗变化点数）作判据，误判出 2 条"反例"并一度立为红项；
  **改用正确判据（冻结起点之后的 units 变化步）回原始 `measure_w*.json` 重验 ⇒ 撤回**：23 条「冻结后 0 变化步」，
  其中我原点名的 `l1a_20261020/w2`（停变 21.030 < 冻结 23.218，且 b 已归零）与 `archive_T47/w0`（停变 13.018 < 冻结 18.380）**均属终局**；
  余 1 条 `l1_20261023e4/w2` 是 **frame 恒 0 的空窗**（W1 帧号 3557→**0**，游戏已退出），恰落在台账原文「W1W2 空窗」的并列表述内，不属"战斗期停顿误归"。
  ⇒ 该前提件 **CONFIRMED**（详见 §3 末「R-3 撤回声明」与 `_raw/s15_stdout.txt`）。
- §474/GOAL1「与 842/732 旧读数同量级、未随负载抬升」我逐点回原始件核：t55k W0 `p99/max`=41.7/48.2（units0=842）、l1a W0 37.7/42.1（732）vs 本批 q 44.4/68.4（974）、r 41.4/45.7（941）
  ⇒ 台账「与 842/732 旧读数同量级、未随负载抬升」在我核到的原始 stats 上**逐位成立**（q p99 44.43 vs t55k 41.70/l1a 37.73；q max 68.40 vs t55k 48.17/l1a 42.10；r 41.36/45.68）。
  **但我加一条台账未表述的限定**：`l1a_20261020` 的 W0 虽 `units0=732`，其 counters 实为 **730→727（dU=−3，24 步仅 3 步变化）**
  ⇒ 该趟 W0 近**静态在场**，不是活动交火窗；把它与 t55k（841→809，15/24 步变化）、e4（697→644，23/24 步）并列为「31 档战斗趟的帧时基准」时，
  其"战斗负载"含金量低于本批（q 24/24、r 23/24 步在变）⇒ 「同量级」在帧时维度成立，在**交火强度维度不完全同件**（并入 Y-7 口径问题）。
  **我不作引申**：另有一趟 `l1_20261023e4`（units0=702，W0 `p99/max`=**61.0/69.6**）其 p99 高于上述各点，但**台账未把 e4 纳入「同量级」句**（该句只举 842/732），
  且 e4 W0 的 units 变化步=23/24、停变在窗末 24.028 ⇒ 它同样是活动窗，帧时却偏高 ⇒ 我**不能**据本批数据断言"帧时分布与负载单调无关"，
  只能说「在本批 974/941 这个点上未见 ≥0.5 s 停顿」。此项列入未验证（见 §5）。
  另注：`archive_T47/w0` 是 **31 档 ∧ W0（活动）∧ 6.62 s 长停顿** 的现存条目（units0=251）⇒ 严格说"31 档活动窗内从未见长停顿"并不成立，只是其负载远低于 900+。本批结论（高负载下不复现）不受影响。

## 8. 我实际跑过的命令（全部为只读/离线）

```
python lead/codex_round_20261030/XVERIFY_TRIPS_20261030/_xv_s01_trips2.py        # ② 会话/哈希/闩/退出/值域/间隔
python lead/codex_round_20261030/XVERIFY_TRIPS_20261030/_xv_s02_deep.py          # ② 慢行来源行/节律/归零时点
python lead/codex_round_20261030/XVERIFY_TRIPS_20261030/_xv_s03_battle.py        # ① gate/停顿/counters/W1W2（含一处被我标[错法]的 frame_ms 尝试）
python lead/codex_round_20261030/XVERIFY_TRIPS_20261030/_xv_s03b_recompute.py    # ① frame_ms 正确口径（帧沿差分）独立重算
python lead/codex_round_20261030/XVERIFY_TRIPS_20261030/_xv_s04_windows.py        # ① 三窗全量 + qc151_fields + argv/残留
python lead/codex_round_20261030/XVERIFY_TRIPS_20261030/_xv_s05_freezealign.py    # ① 冻结起点 vs units 停变点对齐
python lead/codex_round_20261030/XVERIFY_TRIPS_20261030/_xv_s06_driver_identity.py# ② 驱动身份代码指纹
python lead/codex_round_20261030/XVERIFY_TRIPS_20261030/_xv_s07_intervals.py      # ② 闩→退跨会话复算 + selftest 静态计数
python lead/codex_round_20261030/XVERIFY_TRIPS_20261030/_xv_s08_stallanatomy.py   # ① 前提件 + ② 清扫时序一致性
python lead/codex_round_20261030/XVERIFY_TRIPS_20261030/_xv_s09_boundary_e2.py    # ② 边界合并收紧 + E2 轴取证
python lead/codex_round_20261030/XVERIFY_TRIPS_20261030/_xv_s10_premises.py       # ① 31档趟前提 + ② 缝内历史扫描(20 趟)
python lead/codex_round_20261030/XVERIFY_TRIPS_20261030/_xv_s11_delaydisc.py      # 跨 11 趟 Δ(hwnd归零−close) 判别
python lead/codex_round_20261030/XVERIFY_TRIPS_20261030/_xv_s12_batchartifacts.py # 本批时点留档 / TEMP / 第三方模块
python lead/codex_round_20261030/XVERIFY_TRIPS_20261030/_xv_s13_gridscan.py       # 全树 31 趟判别格扫描
python lead/codex_round_20261030/XVERIFY_TRIPS_20261030/_xv_s14_band.py           # STALL_ANATOMY 自校 + 闩绝对时刻带宽
sha256sum lead/qc161_u0400_trip/_drive_c2_x_probe_v2.py _drive_c2_x_earlyclose.py
sha256sum lead/goal1_harness7_20261023/qc151_trip.harness7.py
```
原始 stdout 全部留档于 `_raw/s01..s14_stdout.txt`。未跑项：`--selftest`/`--preflight`（会驱动游戏，禁止）、任何真机/发射类命令。
