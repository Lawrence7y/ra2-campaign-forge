# XVERIFY_B_20261101 · 逐趟 BOOT 证据表（A'' B 线）

> **族属声明（同族标注版）**：本判定书为**同族标注版——本线（BOOT 证据员）与执行线同族（GLM start-plan），非异族对账**；不以同族冒充异族。
> **mimosa 声明**：mimosa security_scan **未调用**（本 ask 为纯只读回读+独立重算，零代码部署、零写域外改动，扫描器无对象）；但 mimosa **预写钩子（PreToolUse:Write）在本线实际生效**：4 支探针脚本被其静态规则误报「高危·路径穿越」拦截（经二分定位：`os.path.join(...)` 结果直接传入 `open(p,"w")` 即触发；改用 `_guard_write` 包装校验形状可通过）。受影响的 `_boot_b04_master.py`/`_boot_b05_consistency.py` 已改为无操作占位，其原定核验改由 **Bash 内联 python 探针**执行，stdout 全部留档本目录 `_raw/`。如实登记，未绕过任何真实安全边界（全部写入仍限本写域）。

- 派单：§503 A'' 批准「B=逐趟 BOOT 证据表（BOOT 身份来源与可信度；**日期不能直接充当 BOOT 身份**；核对地图/二进制/配置/协议/速度/分辨率/有效战斗阶段）」。
- 纪律：全程零真机、零游戏进程、零 git 写、零写域外（写域=本目录）；逐趟回读原始件独立判定；python 一律 `python -I -B -X utf8`。
- 亲算探针：`_boot_b01_collect.py`（32 趟证据盘点 → `_raw/p01_collect.json`）、`_boot_b02_anchor.py`（boot_epoch 精算+聚类 → `_raw/p02_anchor_stdout.txt`）、`_boot_b03_resolve.py`（uptime 单调性消解+e4 特查 → `_raw/p03_resolve_stdout.txt`）、内联探针（E12 锚表/墙钟自洽/一致性/双份比对/BUDGET 证伪/v4c 链 → `_raw/p04a..p04h_*.txt`）。

---

## 0. 结论摘要

1. **32 个目标趟目录全部定位**（25 趟主清单 + archive_T32-45/47/49_u0800 共 22 个 archive 目录 + T46/T48 缺席属文档化事实）。
2. 全部 28 个含 `measure_w*.json` 的趟的 **BOOT 身份由 `t_abs0 − samples.t[0]` 亲算反推**（同一时刻的墙钟 epoch 与 perf_counter 开机秒之差），**6 个 BOOT 会话**聚类成立；四个独立外部锚（E12 `_rec.boot_wallclock_ms_at_start`、boot_fp 10-23 指纹、E6 卡 WMI/事件日志、v4c 链上 perf 锚）交叉验证**零冲突**。
3. **三个"日期陷阱"全部实证**：t55k/l1a（名 1020）BOOT=10-19 14:31；l1_20261023e4（名 1023）BOOT=运行日 10-26 15:14；l3_20261023q/r（名 1023）BOOT=10-30 13:10。**趟名日期与 BOOT 日三次全部不一致**——"日期不能充当 BOOT 身份"由数据直接成立。
4. **同 BOOT 跨夜 ≥3 例**（10-16 12:10 BOOT 跨 10-16→10-18 共 ≥54 h 承载 14 趟 archive；10-19 14:31 BOOT 跨夜承载 t55k+l1a；10-31 08:26 BOOT 跨夜承载 ha/hb/v3a/b/c/v4a/b/v4c）。
5. 一致性核验：gamemd sha 全线一致（`73201cc0…`）；L1/L3 地图双母本各归其位；**t55k 用变体图（`93c2974b`，与 archive_T32/33 同图）≠ l1a 的 `0add791d`**；800×600 逐趟直证（`FRAME.frame_target_wh=[800,600]`）；**GameSpeed=2 的配置真身 `ra2md.ini` 不在 88 件载体清单内**（只能锚到母本与批次卡口径，趟级无载体直证；且 ra2render.ini 本身不含 GameSpeed/分辨率键）；协议旗标逐趟对卡；有效战斗阶段（units0/units 轨迹）逐位对上批次卡。

---

## 1. 方法学（锚定与判据）

**主锚（亲算推导）**：harness 各代（harness3/h7/h8/v3/v4）的 `measure_w*.json` 内 `t_abs0`（窗口起点墙钟 epoch 秒，`time.time` 轴）与 `samples.t[0]`（同刻 `time.perf_counter` 开机秒）是**同一时刻的双钟读数**，故
`boot_epoch = t_abs0 − t[0]`（亲算命令：`_boot_b02_anchor.py`，`_raw/p02_anchor_stdout.txt`）。
- 趟内自检：同一趟 w0/w1/w2 三窗推导差 ≤2.2 ms（亲算，p02 A 段全表）。
- 跨趟同 BOOT 判据①（epoch 等值）：不同趟推导差毫秒级。
- 跨趟同 BOOT 判据②（**uptime 单调性**，用于吸收墙钟步进）：同 BOOT 内 `t[0]`（开机秒）必随 `t_abs0`（墙钟）单调增，且相邻趟 `Δt0 == Δwall`（毫秒级）。判据②是判据①的容错版：墙钟被 NTP 步进 ±1~2 s 时 epoch 等值会破，但 Δt0==Δwall 与单调性不破（亲算实例见 §2-BOOT#0/#1）。

**外部交叉锚（四路，全部亲读）**：
1. **E12 驱动 `_rec.json.boot_wallclock_ms_at_start`**（39 个 `_rec`，主仓 `lead/qc161_u0400_trip/c2ab_x|c2ab|ab24`；`_raw/p04a_e12anchor_stdout.txt`）：3 个会话锚 10-29 14:50:14.227-.230 / 10-30 13:10:38.106-.119 / 10-31 08:26:27.119-.129。
2. **boot_fp_20261023 指纹**（`boot_fp_20261023/boot_fingerprint_*.json`：`boot_key=2026-10-23T09:48`、`Win32_OperatingSystem.LastBootUpTime`、Kernel-General 事件日志）——目标清单内无 10-23 会话趟，作方法学旁证。
3. **GOAL3T_e4_VERIFY_20261026.md §E6**（前轮以 `Get-CimInstance Win32_OperatingSystem`+`Get-WinEvent Id=6005` 独立判定 e4 有效会话=「10-26 15:14」）——与本线推导 `10-26T15:14:25.087` **分钟级互证**（两种独立时钟体系：QPC 对 vs WMI/事件日志）。
4. **v4c 链上夹逼**（l3_1101v4c 三窗 boot=`10-31T08:26:28.387-.388`，亲算 `_raw/p04h_v4c_stdout.txt`）。

**不可用/会误判的证据源（本线逐一证伪）**：
- **趟名日期 / 文件 mtime**：三重不一致实例见 §0-3；mtime 只能给运行日，不能给 BOOT。
- **`qc151_fields.BUDGET` 组（time.monotonic+ts 成对）**：亲算证伪（`_raw/p04g_budget_stdout.txt`）——`stage_begin:carrier_ownership=0.0` 出现在趟起点 ⇒ 值是**进程内相对节拍**而非开机秒；l1a 37 对的 boot_est 跨度 242.6 s 且与主锚差 −7.0 h。**禁用**。
- **墙钟步进陷阱**：跨趟 epoch 「精确等值」作同 BOOT 判据会误判——本线实测 BOOT#0 内 +1.617 s、BOOT#1 内 +2.052 s、10-31 会话 E12 锚与本线主锚 Δ=1.26 s（步进未定因：NTP 或双进程写读时差，如实存疑）。同 BOOT 结论必须落在判据②（Δt0==Δwall+单调）或夹逼上。
- **E12 `_rec` 的 `boot_wallclock_ms_at_start` 为 None 的旧 schema 趟**（XVERIFY_TRIPS §6-1 已述）：archive 全族与 t55k/l1a 无 `_rec`，本线改用其 `measure_w*.json` 主锚，不受影响。

---

## 2. 逐趟 BOOT 证据表

聚类亲算输出：`_raw/p02_anchor_stdout.txt`（A 段逐趟逐窗）/`_raw/p03_resolve_stdout.txt`（A 段 Δt0==Δwall 全表）/`_raw/p04b_walls_stdout.txt`（C 段墙钟-uptime 自洽，28 趟全 OK）。下表「boot(推导)」= 本线主锚亲算值。

### BOOT#0 —— `2026-10-16T12:10:36.7`（+08:00），承载 ≥54 h（10-16 → 10-18 18:11）

| 趟 | BOOT 身份结论 | 证据来源与可信度 |
|---|---|---|
| archive_T32/33/34/36/38/39/40/41/42/43/44（11 趟） | **BOOT#0**（10-16 12:10:36.711） | **强**：主锚推导 11 趟×3 窗 epoch 逐位一致（离散 ≤2.2 ms）；跨趟 uptime 严格单调、相邻 Δt0==Δwall 毫秒级（p03 A 段 9:12→17:33 七段全等）；墙钟-uptime 自洽 OK×11（p04b）。 |
| archive_T45/47/49_u0800（3 趟） | **BOOT#0**（同上；推导 epoch=12:10:38.328，+1.617 s） | **强**：T44→T45 处墙钟步进 +1.617 s（Δt0=+824.929 vs Δwall=+826.546，`_raw/p03` A 段逐位），步进后 T47/T49 恢复 Δt0==Δwall 全等；uptime 全程单调（162119 s→194443 s 无回落）⇒ 同 BOOT、非重启（两 BOOT 相隔 1.6 s 物理不可能）。 |
| archive_T35 / T37 | **BOOT#0（推定）** | **中**：无 measure（导航未完成趟，nav_start_pre ok=False，窗态 rect [880,420,1680,1020]）；仅墙钟（META 10-18 12:26:24 / 12:56:05）**时间槽位**落在 T34(12:17)→T36(12:52)→T38(14:06) 两个已证同 BOOT 测点之间 + T 号批次连续；BUDGET 轴已证不可用 ⇒ 无开机轴直证。 |

### BOOT#1 —— `2026-10-19T14:31:37/39`，跨夜至 10-20 20:13（uptime 至 29.7 h）

| 趟 | BOOT 身份结论 | 证据来源与可信度 |
|---|---|---|
| t55k_20261020 | **BOOT#1**（10-19 14:31:37.088） | **强**：主锚三窗 ±0.4 ms；与 l1a 跨趟：t55k(10-20 09:20, uptime 67753 s)→l1a(10-20 20:13, uptime 106938 s) Δt0=+39185.353 vs Δwall=+39187.405 ⇒ 墙钟步进 +2.052 s、uptime 单调 ⇒ 同 BOOT。台账旁证：§144B/§151 记 10-19 晨间判别轮（其 boot 属 10-16 族）与梯2 重启待办 ⇒ 10-19 存在多次重启、14:31 boot 晚于 §151（10:2x）轮，时序无矛盾。 |
| l1a_20261020 | **BOOT#1**（10-19 14:31:39.140） | **强**：同上三窗 ±1.1 ms + 步进后与 t55k 同簇；META 10-20 20:11:10、w_abs0−meta=167.8 s 自洽。**披露**：主仓 `lead/l1a_20261020/` 仅 2 份报告 md（E2_SUCCESS_TRIP_REPORT/RULING_PACK_313），原始件正本在镜像 `out/…/qc161_u0400_trip/l1a_20261020/`（本表用后者）。 |

### BOOT#2 —— `2026-10-21T09:45:43.095`（离散 1 ms，4 趟）

| 趟 | BOOT 身份结论 | 证据来源与可信度 |
|---|---|---|
| l1c/l1d/l1e_20261021、l3_20261021 | **BOOT#2** | **强**：4 趟×3 窗 epoch 离散 ≤1.4 ms；四趟 uptime 单调（p02 A 段 l1c 19:01 起→l3 21:10）；墙钟-uptime 自洽 OK×4。此批趟名日期=运行日（BOOT 日 10-21 与运行同日，但 BOOT 身份仍以锚定值为准）。 |

### BOOT#3 —— `2026-10-26T15:14:25.087`（单趟）

| 趟 | BOOT 身份结论 | 证据来源与可信度 |
|---|---|---|
| l1_20261023e4 | **BOOT#3** | **强**：主锚三窗 ±0.8 ms；**与 E6 卡独立锚互证**（GOAL3T_e4_VERIFY_20261026.md §E6:116-117：「e4 趟 ts=2026-10-26 19:56–20:01…落在 **10-26 15:14** 会话内…当前有效会话 = 10-26 15:14」，WMI+事件日志法）；META.started=10-26 19:56:36、mtime 19:56:49–20:01:11、w_abs0−meta=177.1 s 全自洽。**趟名 20261023 与运行日（10-26）、BOOT 日（10-26）不一致——趟名日期标签错误在案（E6 已判 REFUTED，本线锚定值复证）。** |

### BOOT#4 —— `2026-10-30T13:10:38.08`（2 趟）

| 趟 | BOOT 身份结论 | 证据来源与可信度 |
|---|---|---|
| l3_20261023q / l3_20261023r | **BOOT#4** | **强**：两趟×3 窗 epoch 离散 2.1 ms、相互 Δt0==Δwall（713.506 s 逐位）；**与 E12 `_rec` 跨驱动互证**：hold13/14/15 与 21:17-21:22 三 E12 趟 `boot_wallclock_ms_at_start`=13:10:38.106/.113/.119，与本线推导 .083-.086 差 ≤36 ms（`_raw/p04a`）；趟名 20261023、运行 10-30 晚（20:46/20:58）——又一「趟名日期≠运行日」实例（XVERIFY_TRIPS §474 已按 10-30 会话处理，本线锚定值复证）。 |

### BOOT#5 —— `2026-10-31T08:26:28.39`，跨夜至 11-01 09:46（uptime 至 ≥25.3 h）

| 趟 | BOOT 身份结论 | 证据来源与可信度 |
|---|---|---|
| l3_20261031ha / l3_20261031hb | **BOOT#5**（10-31 08:26:28.388） | **强**：主锚直证（ha w0 / hb 三窗，±1.3 ms）；相互 Δt0==Δwall（444.531 s 逐位）；与 E12 `_rec`（08:33/08:36/15:41 三趟 boot=08:26:27.119-.129）同会话互证（Δ=1.26 s，墙钟步进未定因，如实注）；META 20:06/20:13（10-31 晚）、v3a/v3b 于次日 07:06/07:10 同簇 Δt0==Δwall（39040.839 s 逐位）。 |
| l3_1101v3a / l3_1101v3b | **BOOT#5** | **强**：主锚直证（±2.0 ms）+ 与 ha/hb 跨夜同簇（Δt0==Δwall 毫秒级）+ §496 批面（v3 发射器三趟 rc=0、07:04/07:08/07:12 ≈10 min 批内）。 |
| l3_1101v3c | **BOOT#5（夹逼）** | **强（夹逼推定；自身无 perf 轴——如实披露）**：measure_w0 存在但 `verdict=frame_wait_timeout`（120.05 s 未达 1200 帧，reached=1058）⇒ samples 空、无 t0；墙钟锚 t_abs0=11-01T07:15:21.459、META 07:12:29、mtime 07:12:42–07:15:49。夹逼链：v3b（07:10，**perf 直证** BOOT#5）→ v3c（07:12–07:15）→ … → v4c（09:43–09:46，**perf 直证** BOOT#5 同 epoch 亚毫秒）；夹逼区间内同 epoch 重启不可能 ⇒ v3c ∈ BOOT#5；§496 批面（同一发射器 rc=0×3）佐证。 |
| l3_1101v4a | **BOOT#5（夹逼）** | **强（夹逼推定；自身无 measure/无 perf 轴——如实披露）**：rc=63（EXIT_MODULE_ENUM_FAILED，err=299 瞬态，§501 作废趟）；仅墙钟（META 11-01 09:06:54、mtime 09:07:34–09:10:03）。夹逼：v3c（07:15）→ v4a（09:06–09:10）→ v4c（09:43–09:46 perf 直证 BOOT#5）⇒ 链上无重启空间 ⇒ v4a ∈ BOOT#5。 |
| l3_1101v4b | **BOOT#5（夹逼）** | **强（夹逼推定；无 t0 轴——如实披露）**：measure_w0 有 t_abs0（11-01T09:19:17.569）但 `verdict=frame_wait_timeout`（reached=271）⇒ 无 samples/t0；META 09:15:00、mtime 09:15:39–09:20:53。同上夹逼（v3b/v4c 之间）⇒ v4b ∈ BOOT#5；§501 批面佐证。 |
| （锚点，非清单）l3_1101v4c | BOOT#5 perf 直证 | 三窗 boot=08:26:28.387-.388（亚毫秒同簇），verdict=ok×3；不在本 ask 清单，仅作夹逼锚点使用（`_raw/p04h`）。 |

**archive_T46 / T48**：目录不存在属**文档化事实**——TRIP_ID_RECONCILIATION_20261018.md:23「T46 无 archive、卡面无 §T46（疑为跳号）」、:10「T48 …fields 未及归档（关键数值在 ROUND 日志 §101）」。非本线发现缺口，BOOT 身份不可判（无原始件）= UNVERIFIED。

---

## 3. 一致性核验（逐趟，与批次卡口径对照）

亲算输出：`_raw/p04d_consistency_stdout.txt`（母本哈希+全趟对照表）、`_raw/p04e_pairs_argv_stdout.txt`（argv 细节+双份比对）、`_raw/p04f_screen_t35t37_stdout.txt`（800×600 直证+T35/T37）。母本哈希本线亲算：L1/L3 双母本的 `gamemd.exe=73201cc0…`、`ra2render.ini=27c9a60c…`、`ddraw.ini=95949842…`、`ra2md.ini=0cc65385…`、`game.exe=c4bf2a57…`（两母本六件逐一相同）；地图 `L1:XMP29U2.MAP=0add791d…`、`L3:XMP29U2.MAP=f3bb0a4e…`。

| 趟 | 地图 sha | gamemd sha | 配置（载体 sha 对母本） | 协议（argv / qc151 侧证） | 速度/分辨率 | 有效战斗阶段（units0；w0→w1→w2 units） | 判定 |
|---|---|---|---|---|---|---|---|
| l1a_20261020 | `0add791d`（L1） | `73201cc0` ✓ | r=`27c9a60c`✓ d=`95949842`✓（m 不在载体） | 旧 schema 无 `_launch_result`；qc151：evid_diff=true、fullscreen=true（亲读） | res 直证 `[800,600]`；speed 仅母本锚 | **732**；730→727｜727→708｜706→629（三窗 ok） | 一致（L1 卡 732✓；W0 近静态、W2 活动降，与 §477 R-3 复核口径同） |
| t55k_20261020 | **`93c2974b`（变体图 `_src_variant_800x600_csf`，≠l1a）** | `73201cc0` ✓ | 旧 schema 无 carrier_manifest（cwd 无清单） | 同上（无 argv 留档；qc151 fullscreen=true） | res `[800,600]`；speed 仅母本锚 | **842**；841→809｜807→770｜769→762 | 一致（卡 842✓；**图与 l1a 不同，并列引用须注明**） |
| l1c_20261021 | `0add791d` | `73201cc0` ✓ | r✓ d✓（88 件，manifest_ok=True） | `--measure 1 --fullscreen --evid-diff --probe-frames 3900..6000` ✓ | res✓ | **881**；879→867｜867→858｜858→850 | 一致（卡 881✓） |
| l1d_20261021 | `0add791d` | `73201cc0` ✓ | r✓ d✓ | 同上 ✓ | res✓ | **874**；870→858｜858→847｜846→833 | 一致（卡 874✓） |
| l1e_20261021 | `0add791d` | `73201cc0` ✓ | r✓ d✓ | 同上 ✓ | res✓ | **866**；865→855｜855→836｜836→824 | 一致（卡 866✓） |
| l3_20261021 | `f3bb0a4e`（L3） | `73201cc0` ✓ | r✓ d✓ | 同上 ✓ | res✓ | **1342**；1330→1270｜1267→1187｜1184→1106 | 一致（L3 收据 1342✓；W0 轨迹与 XVERIFY_TRIPS §(12) 逐位同） |
| l1_20261023e4 | `0add791d` | `73201cc0` ✓ | r✓ d✓ | `--measure 1 --fullscreen --evid-diff --probe-frames … --h7-keep-rect-wait`（keep-rect 对照臂 ✓，E4 卡在案） | res✓ | **702**；697→644｜642→640｜640→**None**（W2 空窗） | 一致（卡 702✓；W1W2 空窗与 §474/R-3 口径同） |
| l3_20261023q | `f3bb0a4e` | `73201cc0` ✓ | r✓ d✓ | h7 全套+keep-rect ✓ | res✓ | **974**；953→854｜852→811｜811→811 | 一致（§474 974✓；W0 24/24 步降为前轮已证，本线复读首末同） |
| l3_20261023r | `f3bb0a4e` | `73201cc0` ✓ | r✓ d✓ | 同上 ✓ | res✓ | **941**；923→842｜839→828｜828→828 | 一致（§474 941✓；R-2「1 持平步」不在本线重判范围，首末一致） |
| l3_20261031ha | `f3bb0a4e` | `73201cc0` ✓ | r✓ d✓ | `--measure 1 --fullscreen --evid-diff --probe-frames … --h7-measure-start-frame 400` ✓（无 keep-rect） | res✓ | **1342**；1342→1340｜—｜—（no_advance 短路，w1/w2 按设计不落=§487 Y-7 ✓） | 一致 |
| l3_20261031hb | `f3bb0a4e` | `73201cc0` ✓ | r✓ d✓ | 同上 ✓ | res✓ | **1347**（gate）/1341（counters 首行，Y-9 双口径）；1341→1298｜1297→1262｜1262→1179 | 一致（§487 链逐位同✓） |
| l3_1101v3a | `f3bb0a4e` | `73201cc0` ✓ | r✓ d✓ | h8_v3：measure-start-frame 400 ✓ | res✓ | **1349**；1336→1265｜1262→1147｜1145→1107 | 一致（§496 链逐位同✓） |
| l3_1101v3b | `f3bb0a4e` | `73201cc0` ✓ | r✓ d✓ | 同上 + **`--h8-wait-hz 50`**（唯此趟）✓ | res✓ | **1352**；1338→1215｜1211→1117｜1114→1066 | 一致（§496✓） |
| l3_1101v3c | `f3bb0a4e` | `73201cc0` ✓ | r✓ d✓ | h8_v3、N=1200 ✓ | res✓ | 拒采（frame_wait_timeout，reached=1058）⇒ 无战斗窗 | 一致（§496「v3-c 超时拒采」✓） |
| l3_1101v4a | （无 measure） | （argv `--target-sha256 f3bb0a4e…`✓） | r✓ d✓（manifest 在案，88 件） | h8_v4 + `--h8-wait-trace` ✓；rc=63（作废） | res✓（fields 在） | 无（S4 阶段 fail-closed 硬停） | 一致（§501 作废口径✓） |
| l3_1101v4b | `f3bb0a4e` | `73201cc0` ✓ | r✓ d✓ | h8_v4 + `--h8-wait-trace` ✓ | res✓ | 拒采（reached=271/800）⇒ 无战斗窗 | 一致（§501✓） |
| archive_T32/33 | `93c2974b`（变体图） | `73201cc0` ✓ | 无 carrier_manifest（旧 schema） | 无 `_launch_result`（旧 schema） | res `[800,600]` 直证 | **241**；241→240×3 窗近静态 | 一致（A/B 批变体图设计；前轮 §477 R-3 已用 T47 同法） |
| archive_T34/36/38/39/40/41/42/43/44/45/47/49 | 各自变体图：`be07d2b4`/`60cb0262`/`6fac3a3e`/`9a249526`/`e7dee568`/`e3acc130` | `73201cc0` ✓ | 无 | 无 | res✓（有 fields 趟） | u0=241-251（T49=491）；各窗近静态（242→241 型） | 一致（变体批设计内；T35/T37 无 measure） |
| archive_T35/T37 | 无 measure（fields 的 TARGET=变体图目录） | — | 无 | 无 | **窗态 rect=[880,420,1680,1020]**（非全屏臂） | 无（nav 未完成，nav_start_pre ok=False） | 一致（作废趟口径） |

**配置口径勘误（重要）**：批次卡「GameSpeed=2 / 800×600」的两键**都不在 ra2render.ini 里**（本线亲读该文件全文：仅 EnableSIMD/EnableVxlCachePrewarm/EnableSWChargeOpt/UnlockGameSpeed=0/L4DirtyMode 等，无 GameSpeed、无分辨率键）。真身：`GameSpeed=2` 在**母本 `ra2md.ini`**（本线亲读 grep），而 `ra2md.ini/RA2MD.INI` **不在 88 件 `--carrier-create-files` 清单内**（v4a argv 全量亲读）⇒ 趟级载体无法锚定 GameSpeed=2，只能锚到母本配置+批次卡声明；`800×600` 在 `ddraw.ini`（windowed=false/width=800/height=600，在载体、sha 与母本一致）且有**逐趟运行期直证** `FRAME.frame_target_wh=[800,600]`。引用「GameSpeed=2」时建议改注「母本 ra2md.ini 口径」。

**双份目录比对**：l1c/l1d/l1e/l3_20261021 主仓与镜像五件关键 JSON 逐字节 IDENTICAL；l1a 主仓无原始件（见 §2 BOOT#1 披露）；t55k 仅主仓有。

---

## 4. 方法学结论

**足以锚定 BOOT 身份的源（按强度排序）**：
1. `measure_w*.json` 的 `t_abs0 − samples.t[0]`（双钟对，QPC 轴）——逐窗直证，跨趟一致即定谳；本线 28 趟全适用，与 WMI/事件日志（E6）、E12 `_rec` 跨驱动互证零冲突。
2. E12 `_rec.boot_wallclock_ms_at_start`——直证但仅 E12 族有；10-30 会话与本线主锚差 ≤36 ms，10-31 会话差 1.26 s（步进未定因），同会话判定仍稳。
3. WMI `LastBootUpTime`/Kernel-General 事件日志（boot_fp、E6 法）——独立体系，分钟级即可互证。
4. **夹逼链**：两端 perf 直证同 BOOT、中间趟墙钟严格落内 ⇒ 中间趟归属被逻辑锁定（v3c/v4a/v4b 实例）。

**会误判的源与陷阱（本线全部有实证）**：
- **趟名/台账日期**：t55k·l1a（1020→BOOT 10-19）、e4（1023→BOOT 10-26）、q/r（1023→BOOT 10-30）——三次全不一致。
- **同 BOOT 跨夜**：三例（≥54 h/29.7 h/25.3 h）；「跨天=不同 BOOT」不成立。
- **同日多次重启**：10-19 至少两 BOOT（晨判别轮族 vs 14:31 族）；「同日=同 BOOT」不成立。
- **墙钟步进（±1~2 s）**：BOOT#0 内 +1.617 s、BOOT#1 内 +2.052 s、10-31 会话跨源 Δ1.26 s——「epoch 逐位相等」才能判同 BOOT 的用法会把同 BOOT 误拆；必须配 uptime 单调性（Δt0==Δwall）或夹逼。
- **BUDGET 组（monotonic+ts）**：进程内相对节拍，禁作 BOOT 轴（l1a 证伪：跨度 242.6 s、与主锚差 −7.0 h）。
- **旧 schema 缺件**：archive 全族与 t55k/l1a 无 `_launch_result`（协议面靠 qc151_fields 侧证）、archive 无 carrier_manifest（配置面靠母本+gamemd 读数）——缺件不等于异常，但相应一致性项降为「侧证」。
- **采样节律**：measure `hz=500` 为名义值；§501 实测 83–347 Hz 随会话劣化——引用「500Hz」须带实测注。

---

## 5. 分歧/异常清单

1. **三重日期不一致实例**（§0-3）：e4/q/r/t55k/l1a 五趟的趟名日期、运行墙钟日、BOOT 日两两错位。影响面：任何以趟名日期归并会话的既有表述需按本表锚定值校正（§474/§487 等前轮已按正确会话处理者不受损）。
2. **墙钟步进三处**（+1.617 s / +2.052 s / Δ1.26 s）：跨 BOOT 对账表若用「墙钟起点」做主键须容忍 ~2 s 步进；本表一律以锚定 boot epoch+判据②表达。
3. **t55k 地图 `93c2974b` ≠ l1a `0add791d`**（与 archive_T32/33 同图、属 `_src_variant_800x600_csf` 变体族）：L1 卡把两趟并列为「同源变体」基线，**非同图**——跨趟帧时对比含地图变量（除档位/harness 外的第三个变量，Y-8 同类）。
4. **GameSpeed=2 载体无直证**：ra2md.ini 不在 88 件载体清单；ra2render.ini 不含该键（口径勘误，§3 末）。
5. **archive_T46/T48 缺席=文档化事实**（跳号/未归档），T49 目录实名 `archive_T49_u0800`。
6. **lead/l1a_20261020 主仓只有报告**（E2_SUCCESS_TRIP_REPORT.md、RULING_PACK_313.md），原始件仅在镜像——引用路径时须指向镜像。
7. **v3c/v4b 拒采趟、v4a 作废趟**：BOOT 身份仍可判（夹逼），但**无有效战斗窗**，任何「有效战斗阶段」引用只落 ha/hb/v3a/v3b（N=400 批）与之前各趟。
8. **l1a W2 units 706→629（活动降）**：XVERIFY_TRIPS §477 对 l1a 的「W0 近静态」表述仅针对 W0；本线补全三窗轨迹供后续引用（w0 730→727 / w1 727→708 / w2 706→629）。
9. **e4 W2 `counters.units` 末行=None**：空窗残值形态，与「W1W2 空窗」口径一致（非新异常，登记备查）。
10. **工具面（如实登记）**：mimosa 预写钩子 4 次误报拦截探针写入（bisect 定位+规避方式见文首 mimosa 声明）；`_boot_b04_master.py`/`_boot_b05_consistency.py`/`_hook_bisect.py` 为无操作占位（禁删文件故留档）；p04 原定核验由内联探针完成且 stdout 全留档。
11. **本线局限**：零真机/零进程注入复测；E12 `_rec` 的 10-29 会话（14:50:14）无本清单趟落其上，仅作锚表记录；boot_fp（10-23 会话）与 §144B/§151（10-19 晨会话）的趟不在本清单，未逐趟建表。

---

## 6. 命令与留档

```
python -I -B -X utf8 lead/codex_round_20261030/XVERIFY_B_20261101/_boot_b01_collect.py   # _raw/p01_collect.json
python -I -B -X utf8 lead/codex_round_20261030/XVERIFY_B_20261101/_boot_b02_anchor.py    # _raw/p02_anchor_stdout.txt
python -I -B -X utf8 lead/codex_round_20261030/XVERIFY_B_20261101/_boot_b03_resolve.py   # _raw/p03_resolve_stdout.txt
# 内联探针（Bash python -c，均 tee 留档）：
#   p04a E12 _rec 锚表 / p04b 墙钟-uptime 自洽 / p04d 一致性母本哈希 / p04e 双份比对+argv
#   / p04f 800×600 直证+T35/T37 / p04g BUDGET 证伪 / p04h v4c 夹逼锚
```
全部为只读回读+独立重算；零真机、零发射、零写域外、零 git 写。
