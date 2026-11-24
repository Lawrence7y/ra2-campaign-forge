# §544「慢窗口径改判」判定书（XVERIFY_S544_c1606d35）

- 汇总员 · 2026-11-04 · 三路核验（V1/V2/V3）+ 三路独立复核 + 汇总员本轮独立复算
- 铁律：零真机（未启动 gamemd.exe / ra2loader.exe / YURI，未 taskkill，未读运行中进程内存）；母本与真机 json/png 全程只读；写入仅限本目录；未改台账、未改 swarm_20261104 根下已有文件、未 commit；python 一律 `python -I -X utf8`；绝对路径；未采信任何 lane 给出的数字，全部从原始件重算。
- §544 原文口径来源：`D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/xverify_s544.dwf.ts:69-88`；§544 之前的「38 慢窗」改判见 `D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md:4280-4290` 与 `D:/Project/ra2-campaign-forge/lead/PENDING_DECISIONS.md:35-39`。

## 0. 本轮汇总员实际执行的复算（可逐条复查）

| # | 命令 | 输出 |
|---|---|---|
| S1 | `find "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip" -type f -name "measure_w*.json" \| wc -l` | `104`（当前切面）；18:26:53 并发新建 `l3_1101v4h/measure_w0.json` 使 lane 的 103 切面 +1，见 `V1/RECHECK.md:7` |
| S2 | `python -I -X utf8 <本目录>/_verdict_recompute.py > <本目录>/_verdict_recompute_out.txt 2>&1` | `EXIT=0`，144 行，无 Traceback；全量逐窗复算 104/103 双切面 |
| S3 | `python -I -X utf8 <本目录>/_verdict_final.py > <本目录>/_verdict_final_out.txt 2>&1` | `EXIT=0`，57 行，无 Traceback；目标①样本分层、ρ/φ 敏感性、停摆缺口 |
| S4 | `python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/_leader_slow_decomp2.py" > <本目录>/_verdict_slow_decomp_replay.txt 2>&1` | `EXIT=0`；只读复现 leader 自己的 SLOW/FROZEN 分类脚本（输出 `:1-8`）。**注意**：该脚本跑在 104 切面，输出 `FROZEN 32 / SLOW 30 / HEALTHY 25 / TRUNC 8`，与台账的 29/38/25 口径不同，不作为本次判定数字来源 |
| S5 | `python -I -X utf8 -c <源码行 dump>` | `D:/Project/ra2-campaign-forge/lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py` 的 `:4730-4736, :4755-4762, :4782-4815, :3843-3850, :4000-4032, :5035-5060, :5183-5225, :5240-5265, :5305-5330, :7410-7427, :7600-7616, :7635-7641` |
| S6 | `python -I -X utf8 -c <argv/hashlib/PNG sha/导航链/异常普查>` 多次 | v4e/f/g argv 与 sha、`h8_wait_trace.json`、`counters.units`、`qc151_fields.json`、`frame_target_01.png`/`fs_boot_probe.png` sha、全库 except 普查 |

未采信 lane 的 `_v2_data.json` / `_v2_meta.json` / 各 `_out.txt` 中间产物；`V1/REPORT.md`、`V2/REPORT.md`、`V3/REPORT.md` 与三份 `RECHECK.md` 全文已读，用于对照与定位其自身错误。

---

## 1. 一句话结论

**§544 的改判只在「`fps_avg` 分母确为整窗实测墙钟跨度、停摆会稀释均值」这一句源码事实上 CONFIRMED；它的核心推论「慢窗池有大量假货、须改用活段/`fps_p50` 口径」被 REFUTED**——停摆本身就是用户可见卡顿，14 个低 `fps_avg` 高 `fps_p50` 窗中 11 个是 25 s 窗的 6.6–24.7 s 尾段停摆且 10/11 所在趟后续还有整窗零推进，属终局/冻结证据而非「假慢」；跨时段 3 倍差与 ρ=0.8925 两条支撑一条被工具链/地图/相位混淆推翻、一条是同义反复加伪重复。**「38 慢窗」这个数没错，但须分层：33 个 25 s 慢窗里 22 个是全程低速真慢窗（8 个独立趟）、11 个是停摆主导；另 5 个 4 s 门控失败废窗应剔除。**

---

## 2. §544 主张逐条处置表

| # | §544 主张（`xverify_s544.dwf.ts:76-80`） | 判定 | 依据（本轮复算 / 源码行 / 命令输出） |
|---|---|:---:|---|
| **P1** | `fps_avg` 分母是整窗 25 秒，一段停摆尾段会把正常 31 fps 稀释成「慢」 | **PARTIAL** | 分母事实 CONFIRMED 但措辞不准：源码 `:4757-4759` `span = t_b - t_a`（首末**实测**样本）、`:4791` `fps_avg = logic/span`；`:5322` JSON 的 `span_s` 才是常量 25.0。S2 输出 `:62` 58 个名义 25 s 可推进窗实测 span `(24.899944, 24.999961)` s、恰等于 25.0 的窗数 = 0；`l3_20261031hb/w0` 169/24.899944=6.787164（stored 6.787164），若硬编码 25.0 应为 6.760000。但「一段停摆尾段」并非普遍机制：S3 `:27-32` §544 点名 6 窗 `max_stall≤0.749879 s`、首末沿铺满 24.798–24.995 s、`\|fps_avg−live\|≤0.060994`，全是全程 4.7–9.2 fps 真推进，无尾段可稀释。 |
| **P2** | 因此目标①此前统计的慢窗池有大量假货，应改用「活段 fps」/ `fps_p50` 重判 | **REFUTED** | 源码 `:4733` 明写 `fps_avg` 为「主对照指标（总量式，稳健口径）」；`:4794-4802` 只把 `df==1` 相邻沿间隔入分位样本，停摆段没有新沿 ⇒ `fps_p50` 结构性抹掉停摆；`:4784-4787` 零推进写 `null`。`live_fps` 不是源码字段（S5 源码 grep `live_fps` 零命中；103 份 JSON 顶层键我另用 `python -I -X utf8 -c` 枚举亦无该键），是事后按首末沿切窗的派生量，S2 `:67/:96` 63 窗 `live_fps < fps_avg` 的窗 = 0，即它必然不稀释。反例 `archive_T34/measure_w0.json`：S2 `:140-142` `n_samples=12502`、`dt_sum=wall_span=24.999840000004042 s`、`dt_max=3.887 ms`、`dt>10ms` 缺口 **0 个 / 0 秒**、`f` 293→302 共 9 帧、末段 `f=302` 持续 **24.734760 s**；`fps_avg=0.360002`、`fps_p50=31.608660`、`live_fps=33.952014`（仅来自 0.265080 s 的 9 帧）。把它判成「不卡」等于改掉用户说的卡顿。S2 `:63-66` 全库 `fps_avg<28` 38 窗、`fps_avg<28 且 fps_p50≥28` 14 窗、`live<28` 26、`p50<28` 24。分型可以做，改主指标不行。 |
| **P3** | 同一负载跨会话时段 fps 差 3 倍以上（units≈1225 在 11-01 拿 31.2 fps，units≈881 在 10-21 只拿 9.2 fps） | **REFUTED** | 数字本身复算通过但「同负载/跨时段」不成立。S2 `:132-137` 六窗 live = 31.180659 / 31.286406 / 31.238013 / 9.221340 / 6.791083 / 4.758393（≈3.4 倍差存在）；但 units0 = 1225 / 1189 / 881 / 1347，881 ∉ `[1180,1360]`，快组均 1207.0 慢组均 1114.0（差 7.7051%）。S3 `:36-47` `map_sha256` 全库 10 种（`l1c` = `0add791d…`、v4d/v4e/hb = `f3bb0a4e…`），`gamemd_sha256` 全库 1 种；harness：`l1c` 用 `qc151_trip.harness3.py`，v4d/v4e 用 `harness8_v4.py`（`sha16=38244d2907e7f7fa`，我独立 hashlib 复算一致）。S3 `:43-45` 对标带 22 窗 2×2=(8,0,0,12) `φ=+1.000000`，但把 slow 切点改 `<28` 即 (8,0,1,13) `φ=+0.908514`，放宽 `units0≥800` 即 (8,8,0,21) `φ=+0.601722`（fast 非 v4 反例：`l3_20261023q/r` harness7、`t55k_20261020` 无版本记录）；同一 v4 的 `l3_1101v4c` 三窗 18.5396/28.4161/30.7053（S3 `:47`）。`h7_measure_start_frame` 分布 `{400:4, 800:5, 1200:1}`（我独立读 72 份 `qc151_fields.json`），快趟 f0=869/920/925、慢趟 f0=387/434/454/957/1095/1158，采样相位随版本变。**「时代效应不可与版本效应分立」成立；「只是版本效应」被自身反例推翻，「同负载跨时段差」不成立。** |
| **P4** | `ρ(pre_fps15, 活段fps) = +0.8925`，可作机制证据 | **REFUTED** | 数字**可精确复现**，不是伪造：S3 `:36-40` 全库 n=63 `ρ=+0.8717331488140595`；排除 `units0=0` 的 3 窗后 n=60 `ρ=+0.8925119893960896` = §544 的 +0.8925；`units0≥800` n=39 `ρ=+0.943163`；仅 25 s n=58 `ρ=+0.958348`；按趟去重 n=34 `ρ=+0.813921`。筛选条件（`units0>0`）未在 §544 文本声明，故该数对口径敏感。同义反复：源码 `:5186-5191` `pre_fps15` 取 settle 尾 1.5 s 帧差/时差，`:4004-4030` 与 `:4767-4770` 用同一个 `time.perf_counter()`(`:4022`) 与同一个 `_rpm_u32(CurrentFrame)`(`:4025`) 生成 samples/edges，`:5324` 一趟一个 `gate_block` 复制进 3 窗 ⇒ S2 `:127-129` 44 个 `trip_id`、30 个多窗 trip 的 `pre_fps15` 全窗相同、63 个相关性样本只有 34 个独立观测。`ρ(units0,live)` 全库 −0.350093、`units0>0` −0.585139，固定版本内符号还翻转（V2 `_v2_corr_out.txt:8-17`，我未逐组重算，见 §6）。高 ρ 只说明同一趟会话基线速度自相关，不证明负载因果或「时代」机制。 |
| **P5** | v4f/v4g 与 v4e「同机同命令」，两趟失败是随机导航失败 / 加载期崩溃 / 代码回归 | **REFUTED** | 「同机同命令」不成立：S6 读 `_launch_result.json` argv，v4e argc=24 含 `--h7-measure-start-frame 800` 与 `--h8-wait-trace`，v4f/g argc=21 两者皆 0；三趟 `harness_sha16` 同为 `38244d2907e7f7fa`（我独立 hashlib 得同值）、`gamemd.exe` 4825360 B / `73201cc0…`、`map_sha256` 同为 `f3bb0a4e…`、`qc151_run_log.json` 均 `final_exit:0` ⇒ 参数回归，非版本/母本回归。导航：S6 读三份 `qc151_fields.json`，三个 `verify_ok_nav_*` 全 True、`signature_got_nav_*` 与 `in_tactical_target='skirmish_setup'` 全等、`clicked_nav_*` 全等 ⇒ 不是随机导航失败；但 `seconds_to_window` 25.796/29.328/28.359 与 `window_stabilize_seconds` 12.843/11.875/11.89 DIFF，「逐字段一致」是 V3 的夸大（见 §3）。异常：三份 `except_post_*.txt` 均 26405 B / sha `6694b75e…` / `007CFC9F` 3 处，`except_set_diff.json` `no_new_exception=true`；我独立普查 trips 树 107 份 `except_post_*.txt` **只有 1 个 distinct sha**、`007CFC9F` 命中 107/107 ⇒ 载体预置基线，成功趟 v4e 同样有，不是崩溃。详见 §5。 |

**补充口径**：`live_fps` 这个「事后编造的口径」问题（`xverify_s544.dwf.ts:84`）——它不是源码统计量，本轮所有 103/104 份 JSON 顶层键里都没有该字段；用它替换主指标属于改定义。停摆应算卡顿，`fps_avg` 继续当目标①主指标，同时报 `max_stall_s`、零推进窗数与终局证据，`fps_p50`/`live_fps` 只作分型诊断。

---

## 3. 必须点名：本轮（核验/复核线）自己的错误

汇总判定不能只清算 §544，也要点名本轮六份件里被复核抓到、且我本轮独立复算确认的错误：

| 出处 | 错误 | 我复算的正确值 / 命令 |
|---|---|---|
| **`V1/REPORT.md:111, :120`**（核验件，最实质） | 称「`+0.8925` 未复现」「ρ 在 0.48–0.96 间变动」 | S3 `:37` 排除 `units0=0` 后 n=60 `ρ=+0.8925119893960896` **精确复现** §544；`0.48` 下界无依据，我实测 ρ(pre,live) 范围 **0.813921–0.958348**。`V2/_v2_corr_out.txt:9` 的 `+0.443479` 是固定 v3 组内的 `ρ(units0, live)`，被混成了另一个量。**判 V1-A4 = PARTIAL**（复核员 V1 已抓到，`V1/RECHECK.md:80-98`）。 |
| **`V1/REPORT.md:45`** | 40 个不可算窗拆成「37 零推进 + 2 不足样 + 1 回绕」 | S3 `:55` **35 零推进 + 4 样点不足 + 1 回绕**（4 个不足样窗：`l1_20261023c`、`l3_1101v3c`、`l3_1101v4b`、`l3_20261023/w0`）。总数 40 不变。 |
| **`V1/REPORT.md:101`** | 引 `archive_T34/qc151_fields.json:154-160` 为 `current_frame/empty_window` 记录 | 那些物理行是 hash expect/actual/match；且 `measure_w1/w2.json` 顶层**无** `current_frame`/`empty_window` 键，只有 `logic_frames=0`、`fps_avg=null`、`f` 恒 302。数组下标被误当行号（`V1/RECHECK.md:115`）。另 `V1/REPORT.md:101` 称两张 T34 PNG「同一张画面」：复核员纯 stdlib 解码得 800×600 中 **1687/480000 像素不同**、sha 不同、计时区 0/3675 全同、小地图 20.47% 不同 ⇒ 应表述为「同一结算屏布局」，非同一张图。 |
| **`V2/REPORT.md:87, :91-92, :145-146, :168-169, :242, :285`** | 计数/措辞六处 | 我独立复核：`_launch_result.json` 28 份中 **23 份带 sha16 / 5 份无**（非 24/4）；无 launch 的趟目录 **18 个**（非 15）；`h7_measure_start_frame` 分布 `{None:62, 400:4, 800:5, 1200:1}`，**`l3_1101v3c`=1200 被漏**；`MANIFEST.json` 的 `"sha256"` 字面 89 次但顶层仅 17 键；按 `trip_id` 分组 **30/30** 多窗 trip 的 pre 全相同（按目录分组才是 29/30，因根层 `measure_w0.json` 的 trip_id 是 T55j、w1/w2 是 T55h；`V2/RECHECK.md:167-169` 的 29/30 是口径差异，不算硬错）；`l1c_20261021/w0` `\|fps_avg−live\|` = **0.060994 > 0.06**，S3 `:30`，「差<0.06」被越界 0.000994。 |
| **`V2/REPORT.md:130-135, :236-239, :329`** | 「完全共线 φ=+1.0 / **只是版本效应**」措辞过强 | S3 `:43-47`：φ=1 只在丢弃 2 个 MID 窗且切点 (≥28/<15) 时成立，改 `<28` 得 0.908514、放宽带得 0.601722；同一 v4 的 `l3_1101v4c` 18.54→28.42→30.71 极差 12.166 是自身反例。「时代效应不可分立」成立，「完全/只是」不成立 ⇒ **V2-A2 判 PARTIAL**。另 `pre_fps15` 与 `live_fps` 不是「同一段数据的两次测量」，而是同一潜在量在 settle 1.5 s 与三段独立 25 s 采样下的两次估计。 |
| **`V3/REPORT.md:5, :238-239, :260, :293-298`** | 「**两个**绑帧等待 flag」「零反例」「真正的根因」「不可能靠随机运气成功」 | 源码 `:5044` 绑帧等待环唯一开关是 `H8_MEASURE_START_FRAME`（由 `--h7-measure-start-frame` 在 `:7612-7614` 装订）；`--h8-wait-trace` 只在 `:5056/:5065/:5127` 控制轨迹落盘、`:7425/:7637-7639` 装订，**不改控制流/gate/等待时长** ⇒ 真正影响结果的只有 1 个 flag。我独立普查 trips 树 28 份 launch：18 份不带该 flag 中 **7 份 verdict=ok**（`l1_20261023e4`、`l1c/l1d/l1e_20261021`、`l3_20261021`、`l3_20261023q/r`），其中 3 份同地图 `f3bb0a4e…`；「零反例」只在 v4a..h 同一 harness 的 8 趟内成立。另 `:138` 的 `37.073+4.0=41.073 ≠ 实测 41.188 s`（差 0.115 s，REPORT §6 已注明近似，keyFact 写成等式不严谨）。**V3-A1 判 PARTIAL**。 |
| **`V3/REPORT.md:47-53, :84-85`（V3-A2）** | headline「三趟导航链逐字段一致」 | 复核员按 `v3_probe.py` 的 64 个导航模式重算得 **38 DIFF**（17 `stage_begin` + 15 `stage_seconds` + 2 `wait_screen_nav_*` poll 内容 + 4 其它）；点名 9 字段 7 SAME / 2 DIFF；v4g `wait_screen_nav_menu_pre` 少 `red_centers=96`、v4f `setup_post` 2 拍（首拍 hit=False），报告漏报 menu_pre 差异。结论「非随机导航失败」CONFIRMED，「逐字段一致」REFUTED ⇒ **PARTIAL**。 |
| **`V3/REPORT.md` §2 / §4 / §5** | 「112/112 全部含异常」「5/5 同类」「三对逐像素差」易被读成独立样本 | `V3/RECHECK.md:251-261` 指出 112 份 `except_post` = **1 个 distinct sha × 112 份拷贝**（含 6 个镜像重复 basename），`frame_target_01.png ≡ navsig_burst_00_g.png`（同 sha `b633740a…`）。我本轮独立得 trips 树 107 份 / 1 个 distinct sha、全库 `find` 113 份（`S6`），方向一致；三趟 `frame_target_01.png` sha 全同 `b633740a547d8097`（S6）。这**不推翻**「预置基线」结论，但属任务书点名的重复计数口径风险。 |

**§544 自身需点名的数字问题**（`xverify_s544.dwf.ts:69-88`）：`ρ=+0.8925` 的数值**没错**，错在**未声明 `units0>0` 的筛选口径与 n=60**，且把它当机制证据；`units≈1225 vs units≈881` 被写成「同一负载」是错的（881 不在 `[1180,1360]` 带内，差 7.7%，且 map/harness/相位都不同）；「同机同命令」（`:153`）是错的（v4f/g 少 2 个 argv token）；「同负载跨会话时段差 3 倍」是错的（是版本/地图/相位混杂）。

---

## 4. 目标①「卡顿」主线：可用样本与下一步

**口径**：`D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md:4280-4290` 把目标①数据面从「29 冻结窗」改判为「38 个 `fps<28` 有推进慢窗」。本轮 S2/S3 在 103 切面上逐窗复算，38 这个数**正确**（`HEALTHY=25 / SLOW=38 / 可推进=63`，S3 `:2`），但 38 不是同质的，必须分层。

| 层 | 窗数 | 独立趟 | 与目标①关系 | 依据 |
|---|---:|---:|---|---|
| 全量 `measure_w*.json` | 103 | 44 `trip_id` | 语料 | S2 `:1-2, :128-129` |
| 可推进（正向 `fps_avg` 可算） | 63 | 34 | 63 窗但只 34 个独立 `pre` 观测 | S2 `:12, :118` |
| 健康对照 `fps_avg≥28` | 25 | — | 对照组 | S3 `:2` |
| **慢窗 `fps_avg<28`（台账口径）** | **38** | 24 | 名义数据面 | S3 `:2-5` |
| ├ 4 s settle / `verdict=no_advance` 门控失败废窗 | 5 | 5 | **应剔除**：`span_s=4.0`、非 25 s 采窗；`l1_20261023e1/hb/hc/k`、`l3_20261031ha`；V3 §7 亦要求 v4f/v4g 这类不得入池 | S3 `:24` |
| ├ **25 s 真·全程低速慢窗**（`p50<28` 且 `max_stall<1 s`） | **22** | **8** | **★ 目标①最硬的可用样本**：`l1c/l1d/l1e_20261021`、`l3_20261021`、`l3_1101v3a/v3b`、`l3_1101v4c`(w0)、`l3_20261031hb`；`fps_avg`、`live_fps`、`fps_p50` 三指标全部 <28，首末沿铺满整窗 | S3 `:9-10` |
| └ **25 s 停摆主导窗**（`p50≥28`，尾段停摆 6.618–24.735 s） | 11 | 11 | **单列，不得算「假货」也不得与全程慢混算**：10/11 所在趟后续还有整窗零推进（`logic_frames=0`），与 §539 的计分屏/终局态证据同向；`l3_20261023q/w2` 是唯一无后续零推进窗，须挂账 | S3 `:11-23` |
| 另有：整窗零推进 / 样点不足 / 计数回绕 | 35 + 4 + 1 = 40 | — | 冻结/终局/废趟证据，不是 fps 样本 | S3 `:55`；`V1/RECHECK.md:69` |

**结论**：若问「还剩多少个可用样本」，按最严口径是 **22 个 25 s 全程低速窗 / 8 个独立趟**（对照 25 个健康窗）；按「38 慢窗」台账口径须先扣掉 5 个 4 s 废窗得 **33 个 25 s 慢窗**，其中 11 个是停摆主导须单列。**没有任何一个慢窗应因改用 `fps_p50`/`live_fps` 而被删掉。**

**下一步往哪查（按优先级）**：
1. **先查「整趟锁定」而非窗内漂移**：S3 `:40` 按趟去重 ρ 仍 +0.8139；`V2/_v2_corr_out.txt:70-90` 趟内极差中位 0.5697 vs 两趟均值差中位 5.4368（≈9.5×）——我本轮未重算这两个中位数（见 §6），引用 lane 结果。优先做同一 harness 版本、同一 map、同一采样起点的 A/B，把「会话基线速度」当首要解释变量，别再往 units 数上找单调律（S3 `:41-42` `ρ(units0,live)` 全库 −0.350093 / `units0>0` −0.585139，符号随分层翻转）。
2. **攻坚同版本反例 `l3_1101v4c`**：三窗 18.5396 → 28.4161 → 30.7053（S3 `:47`），同 `harness8_v4` 同 `f3bb0a4e…` 却在趟内从慢爬到快。这是唯一能分离「版本效应」与「会话/进局相位效应」的天然对照，应查进局后帧 800→925 的 settle 相位、单位生成时序与寻路/脚本负载，而不是再比跨日期的 9.2 vs 31.2。
3. **把 11 个停摆主导窗与 35 个整窗零推进窗合并做终局/冻结归因**（查 `qc151_fields.json` 的 `current_frame`/`empty_window`、窗末截图，注意 V1 复核指出的行号错误与 T34 两 PNG 非同一张图），确认哪些是「对局打完 → 结算 → 帧号停推」，哪些是 §539 挂账未解释的 `T42`、`l1_20261023e4`。
4. **口径固化**：主指标 `fps_avg` + `max_stall_s` + 零推进窗数 + 终局证据；`fps_p50`/`live_fps` 仅分型。所有统计按 `trip_id` 去重（一趟 3 窗不是 3 个独立样本），并强制记录 `map_sha256`、`harness_sha16`、`h7_measure_start_frame`。

---

## 5. v4f / v4g 失败：定性与重跑建议

**定性**：`xverify_s544.dwf.ts:152-154` 的「同机同命令」前提被证伪；这是**发射参数回归导致的测量起点过早（加载期早采）**，不是随机导航失败、不是加载期崩溃、不是 harness/母本版本回归。

- 参数：S6 三份 `_launch_result.json` argv 逐项对比，v4e argc=24 含 `--h7-measure-start-frame 800` + `--h8-wait-trace`；v4f/g argc=21，两者 0 次。v4a..v4h 批次（我独立普查，含 lane 之后新建的 v4h）：6 趟带 flag → 3 `ok`(v4c/d/e) + 2 `frame_wait_timeout`(v4b/v4h) + 1 rc63 无 w0(v4a)；2 趟不带 → 2 `no_advance`(v4f/g)；v4h 带 flag 也超时，进一步说明 flag 不是成功充分条件。
- 机制：源码 `:5037-5044` `if H8_MEASURE_START_FRAME is not None:` 是绑帧等待环唯一开关，`:7612-7614` 由该 flag 装订；缺省 None ⇒ 整块零执行。`v4e/h8_wait_trace.json`（S6）`n=800 / wait_s=37.073 s / 14819 拍`，前 **3.191 s 帧号恒 0**（1275 拍）、首个非零 `[3.1936, 1]`、末拍 `[37.0729, 800]`。v4e `h7_nav_end_t=8733.593 → samples.t[0]=8774.780985`（41.188 s，含 37.073 等待 + 4 s settle + 0.115 s 偏差）；v4f/g 只差 0.128 / 0.141 s ⇒ 点 start 后立刻进 4 s settle，整段落在帧钟未启动的加载期。
- 现象：S6 `measure_w0.json`：v4f/g `span_s=4.0`、`verdict=no_advance`、`samples.f` 2001/2002 拍**全 0**、`error=None`、`hz_effective=500.5` ⇒ 采样器在跑、RPM 读到合法 u32=0，是「读了但不动」；`counters.units` f=`[0,0,1440,1451]`、g=`[0,0,0,1451]` ⇒ 地图在载入、单位在生成，不是崩溃。源码 `:5192-5199` `units0` 取首拍非 None 值（故为 0）且 gate 要求 `pre_fps15≥3.0 ∧ units0>0`，`:5241-5262` 不过即写 `no_advance` 的 w0 并 `return`，跳过三窗 ⇒ f/g 只有 w0、无 w1/w2。
- 排除：三份 `qc151_fields.json`（S6）三个 `verify_ok_nav_*` 全 True、`signature_got_nav_*`/`in_tactical_target='skirmish_setup'`/`clicked_nav_*` 全等；`frame_target_01.png` 三趟 sha 全同 `b633740a547d8097`（`fs_boot_probe.png` 三趟 sha 各不同，主菜单背景动画帧，不作分叉证据）；`except_post_*.txt` 三趟同为 26405 B / `6694b75e…` / `no_new_exception=true`，trips 树 107 份仅 1 个 distinct sha ⇒ `007CFC9F` 是载体预置基线，成功趟 v4e 同样有。
- **证据强度**：这是 8 趟同批次内的共变 + 源码机制 + 时序闭合，flag 与日期/宿主负载也完全共变（v4a..e 在 11-01/11-03，v4f/g 在 11-04；`seconds_to_window` 25.796 vs 29.328/28.359），**没有同日期 A/B 对照，铁律 1 禁止补跑** ⇒ 判「最可能的原因」，不判「已证实的唯一根因」（采纳 `V3/RECHECK.md:119-128` 的 PARTIAL）。我另独立普查 trips 树 28 份 `_launch_result.json`：18 份不带该绑帧 flag 中 **7 份 verdict=ok**（含 3 份同地图 `f3bb0a4e…`），故「无 flag 必失败」只在 v4 批次内成立，不可推广为全库定律。

**重跑建议**：
1. 恢复 v4e 的完整命令，**关键是加回 `--h7-measure-start-frame 800`**（`--h8-wait-trace` 只是留痕开关，可一并加回便于诊断，但它不影响成败）。按 v4c/v4d/v4e 同配置 3/3 `ok` 的历史，恢复到 `ok` 的把握较高；但 v4b/v4h 带 flag 仍 `frame_wait_timeout`，故不能承诺必成，应保留超时重试与 `h8_wait_trace.json` 留痕。
2. 重跑趟必须**排除在目标① fps 统计池之外**，直到产出 25 s 三窗 `verdict=ok`；`span_s=4.0` 的 `no_advance` 窗是门控废趟，不是「运行后停摆」。
3. 补一条工程护栏：发射器侧对 `harness8_v4` 强制校验 `h7_measure_start_frame` 存在且 ≥1（源码 `:7607-7611` 已有 N<1 拒发逻辑，但 N 缺省时无校验），并在 `nav_start` 后等首个 `CurrentFrame` 递增再进 settle；`:5192-5196` 的 `units0`「取首拍即 break」在加载相位会锁死 0，宜改为 settle 内取首个非 0 有效值或显式标注相位。
4. **本轮未真机重跑，以上全部为离线推断，未经实测闭环**。

---

## 6. 诚实账：本轮没查到 / 没做的事

1. **未启动任何真机进程**（gamemd.exe / ra2loader.exe / YURI），未 taskkill，未读运行中进程内存；未改母本、台账、`swarm_20261104` 根下已有文件，未 commit。v4f/v4g 的补参重跑建议**未验证**。
2. **未做 OCR**。屏显时间/画面判读沿用各 lane 的目视结论与 sha/逐像素差；`frame_target_01.png`/`fs_boot_probe.png` 我只独立算了文件 sha 与大小（S6），**未做逐像素差**，V3 的 0/480000、23.5758%、0.0958% 等像素数未由本轮汇总员重算。
3. **未重算的量（明确标注引用 lane，非本轮独立复算）**：`V2/_v2_corr_out.txt` 的固定 harness 版本内 `ρ(units0,live)` 各分组值与 pooled +0.591069/−0.069509、趟内极差中位 0.5697 / 两趟均值差中位 5.4368 / 比值 9.5×、Spearman 值、`V2/REPORT.md` 的 tz/rect/carrier/MANIFEST 逐项普查、`V3` 的 `_recheck_probe` 398 行逐字段表。这些都写成了「lane 结果」，未冒充本轮复算。
4. **11-04 命令为何丢 flag 未查明**：只读了三趟产物与 harness 源码，未找到 11-04 的 launcher 调用脚本/记录；「参数回归」是事实判定，无法归因人/某次编辑。
5. **宿主级第三变量不可判定**：未找到 CPU/内存/DPC/AV/进程争用的原始字段；11-01/03 vs 11-04 的宿主负载差异只能作为与 flag 共变的竞争解释列出，不能确认也不能排除。
6. **早期趟版本不可考**：我独立普查 103 切面 `_launch_result.json` 28 份（23 带 sha16 / 5 无）、`qc151_fields.json` 72 份，有 measure 窗但无 launch 的目录 18 个；这些趟当时所用 harness 的精确哈希无法从现有记录确定，现存 `harness3.py` 的 sha16 `5c56dac5…` 只是现存文件指纹，不证明当时跑的是它。
7. **数据切面并发写入**：lane 用 103 份 `measure_w*.json`，我本轮 `find|wc -l` = **104**（`l3_1101v4h/measure_w0.json`，mtime 2026-11-04 18:26:53，`verdict=frame_wait_timeout`、0 样本）。S2 在 104 与 103 双切面各跑一遍：63 可算窗、38/14/26/24、58 个 25 s 窗的 span 范围、ρ 各值、T34 全部数字**均不变**，只多一个不可算窗。全库 `find` 当前为 242 份 measure / 113 份 `except_post`（V3 报告 241/112），trips 树为 104/107；差异同样来自并发新建，不影响判定。
8. **未查 `.git` 历史版本**，只读工作树；未对 §544 之外的台账条目（`GOAL_THREE_TARGETS_20261018.md` §538/§539 等）重新裁决，本判定书只覆盖 `xverify_s544.dwf.ts:69-88` 所列主张及其连带样本口径。
9. **V3 复核件明示其任务书 JSON 在 V3-A3 后被截断**，只覆盖 V3-A1/A2/A3 三条；`V3/REPORT.md` 正文无 `V3-A*` ID，V3-A4/A5 类主张本轮无法逐条枚举复核，已按 V3 REPORT 全文与我的 S6 复算覆盖其结论方向，但不声称对不可见的自报条目逐条判定。

---

## 7. 产物（全部在本判定目录，未写入其它位置）

`VERDICT.md`（本件）、`_verdict_recompute.py` / `_verdict_recompute_out.txt`（144 行）、`_verdict_final.py` / `_verdict_final_out.txt`（57 行）、`_verdict_census.json`（逐窗复算中间表）、`_verdict_slow_decomp_replay.txt`（leader 脚本只读复现输出）。

*裁决签署：汇总员 2026-11-04*
