# V1 / §544 核验件 —— 复核员-V1 独立复核报告

- **复核对象**：`D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_c1606d35/V1/REPORT.md`（已读全文 1–131 行）。
- **复核日期**：2026-11-04。
- **铁律遵守**：零真机（未启动 gamemd.exe / ra2loader.exe / YURI，未 taskkill，未读运行中进程内存）；母本与真机 `measure_w*.json` / PNG 绝对只读；全部写入仅限本 V1 目录；未改台账、未改 swarm_20261104 根下已有文件、未 commit；所有 python 均为 `python -I -X utf8`，路径全部为绝对路径。
- **独立复算**：另写 `RECHECK_recompute.py`（本目录，从零实现，不 import、不执行核验员的 `recompute.py`，只读原始 `measure_w*.json` / `_launch_result.json` / `qc151_fields.json` / PNG / harness 源码）。输出 `RECHECK_recompute_out.txt`（229 行，103 文件快照，无 Traceback）。
- **会话内数据树发生并发写入（必须披露）**：核验员 REPORT 写于 18:05、`recompute_out.txt` 写于 17:48，我的主复算写于 18:18，当时 `find ... -name "measure_w*.json" | wc -l` = **103**。之后约 **18:26:53** 有并发进程新建 `l3_1101v4h/measure_w0.json`（0 样本、`verdict=frame_wait_timeout`），当前树已是 **104**。我用 `RECHECK_recompute_out_104.txt` 在 104 文件上重跑一遍：**38 / 14 / 26 / 24 / 12+2 / 58 个 25 s 窗 / ρ 三值 / T34 全部数字不变**，只多一个不可算窗、trip_id 44→45。故本报告以 **103 文件快照**（与核验件同一数据切面）为准，并明说这一差异，不把它算作核验员的错误。

---

## 0. 本次实际跑过的命令（逐条留痕）

| # | 命令 | 输出 |
|---|---|---|
| C1 | `find "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip" -type f -name "measure_w*.json" \| wc -l` | `103`（18:18 快照）；18:27 后复跑为 `104` |
| C2 | `find ... -type f -name "measure_w*.json" \| sort` | 首 30 行含 `archive_T32/w0..w2` …；`find ... -maxdepth 1 ... \| sort` = 根层 `measure_w0.json` / `measure_w1.json` / `measure_w2.json` |
| C3 | `python -I -X utf8 "<V1>/RECHECK_recompute.py" > "<V1>/RECHECK_recompute_out.txt" 2>&1` | 229 行，无 Traceback；`RECHECK_recompute_out.txt:2-4` = `TOTAL_FILES=103 / ROOT_LEVEL_FILES=3 / SUBDIR_FILES=100` |
| C4 | `python -I -X utf8 "<V1>/recompute.py" > "<V1>/RECHECK_orig_recompute_out.txt" 2>&1` | 208 行；`cmp -s RECHECK_orig_recompute_out.txt recompute_out.txt` → **IDENTICAL**（核验员自己的脚本可复现，但我下面的数字全部来自 C3 的独立实现） |
| C5 | `python -I -X utf8 "<V1>/RECHECK_recompute.py" > "<V1>/RECHECK_recompute_out_104.txt" 2>&1` | 104 文件快照复核，实质结论不变 |
| C6 | `python -I -X utf8 -c "..."` 多次 | 相关系数子集、T34 逐沿 `frame_ms`、`qc151_fields.json` 记录定位、PNG 纯 stdlib 解码逐像素差、JSON 全键枚举 |
| C7 | `Read` 源码 `qc151_trip.harness8_v4.py` 的 `:3838-3850`、`:4000-4034`、`:4700-4839`、`:5180-5224`、`:5305-5339`；`grep -n "live_fps\|fps_live\|active_span"` | 零命中（源码无 `live_fps`） |
| C8 | `Read` 两张 PNG `measure_w1_end_x.png` / `measure_w2_end_x.png` | 目视同一「遭遇战比分」画面，时间 `00:00:10` |

---

## 1. 抽出的 3 条最关键结论（逐条自己重算）

### ① V1-A1 —— `fps_avg` 分母是实测整窗跨度，不是活段、不是硬编码 25.0 → **CONFIRMED**

**读到的源码**（`D:/Project/ra2-campaign-forge/lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py`）：

- `:4757-4759`：`(t_a, f_a), (t_b, f_b) = samples[0], samples[-1]`；`span = t_b - t_a`；`logic = int(f_b) - int(f_a)`
- `:4784-4787`：`logic <= 0` ⇒ `note="frame not advancing"` 并提前 return（`fps_avg` 留 `None`）；`:4788-4790` `span <= 0` 同样不可测
- `:4791`：`st["fps_avg"] = logic / span`
- `:4765-4771`：`frame_edges` 只记 `f` 首次变化的那次读数；`:4794-4802` 相邻沿 `df==1` 才 `(tb-ta)*1000.0` 入 `frame_ms`，`df>1` 计 `n_multi_advance` 并整条丢弃；`:4805-4813` `p50 = _measure_pctl(frame_ms,0.50)`（`:4717-4727` 排序后线性插值），`fps_p50 = 1000.0/p50`
- `:4733` 原文：`fps_avg = (f_end − f_start)/实测跨度 —— 主对照指标（R8；总量式，稳健口径）`
- `:3843-3845` `MEASURE_HZ=500 / MEASURE_WINDOWS=3 / MEASURE_WINDOW_S=25.0`；`:4004-4030` `_measure_poll_span` 用 `time.perf_counter()` 定拍产出 `samples=[(t,f)]`；`:5322` **JSON 里 `span_s` 写的是常量 `MEASURE_WINDOW_S`**，但 `:5310` 的 `stats` 来自 `_measure_stats(w_samples)` 内的实测 `span`；`:5326-5330` 落盘 `samples.t` 被 `round(t,6)` 到 6 位小数。

**自己从 103 份原始 JSON 重算**（`RECHECK_recompute_out.txt`）：

- `:58` 58 个名义 25 s 的可推进窗，实测 `span` 范围 **`(24.899944, 24.999961)` s**；`:59` **恰好等于 25.000000 的窗数 = 0**。
- 判据性反例：`:60` `l3_20261031hb/measure_w0.json` 实测 `span=24.899944 s`、`logic=169` → 我算 `169/24.899944 = 6.787163859`，与原始 JSON 的 `stored_fps_avg=6.787163913198485` 一致（差 5.4e-8，来自 6 位小数舍入）；若分母真是硬编码 25.0，应为 **`169/25 = 6.760000000`**，差 0.0272。**分母不是 25.0，可证。**
- `:55` 63 个可推进窗的 `fps_avg` 逐窗与 JSON `stats.fps_avg` 全部吻合（容差 1e-5 内 **0 处不符**）；`:56` `fps_p50` 逐窗与 JSON 吻合（容差 0.01 内 **0 处不符**）。
- `:52` 名义 `span_s` 分布 `25.0:89 / 4.0:12 / 0.0:2`，与报告 §2 一致。
- `:88` **`live_fps < fps_avg` 的窗 = 0**（63/63 全为 `live_fps ≥ fps_avg`）：`live_fps` 把首末沿之外的墙钟从分母里剔掉，结构上必然不稀释——这从数据侧印证「`fps_avg` 分母含停摆、活段口径不含」。
- 源码 `:5186-5191` `pre_fps15` 用 settle 尾部 `gate_pts[-1]-[0]` 的 1.5 s 帧差，与窗内 `live_fps` 不是同一段数据；全库 JSON 键枚举（C6）中也**没有 `live_fps` 字段**，`:80` 报告「`live_fps` 是事后派生量」成立。

**结论**：A1 的源码定义、实测跨度、零推进写 null、`frame_ms_p50` 的 `df==1` 沿差分线性插值中位、`fps_p50=1000/p50` —— 全部逐行复算通过。判 **CONFIRMED**。

*（一处无害精度差：我按 JSON 里被 round 到 6 位的 `samples.t` 重算 T34 的 `frame_ms_p50=31.636999978` → `fps_p50=31.608559620`，而 JSON `stats.frame_ms_p50=31.636899977` → `fps_p50=31.608659531`，差 0.1 µs / 0.0001 fps，因 stats 由未舍入的内存浮点算出，源码 `:5326` 落盘时舍入。二者都在同一口径内自洽。）*

### ② V1-A2 —— 全量 103 窗：14 个低 `fps_avg` 高 `fps_p50` 窗，停摆应算卡顿，不能改主指标 → **CONFIRMED**（数字全部复现；报告自报的 PARTIAL 是它对 §544 原主张的判定，不是它自己算错了）

**自己重算**（`RECHECK_recompute_out.txt:2-4, 7, 62-68`）：`TOTAL_FILES=103`、`ROOT_LEVEL_FILES=3`、`SUBDIR_FILES=100`；`COMPUTABLE_LIVE_FPS=63 / NONCOMPUTABLE=40`；以 28 为阈值：

| 指标 | 我算的 | 报告 | 一致 |
|---|---:|---:|---|
| `fps_avg < 28` | **38** | 38（`REPORT.md:48`） | ✅ |
| `fps_avg < 28` 且 `fps_p50 >= 28` | **14** | 14（`:49`） | ✅ |
| `live_fps < 28` | **26** | 26（`:50`） | ✅ |
| `fps_p50 < 28` | **24** | 24（`:51`） | ✅ |
| 63 窗内 `fps_p50=None` | **0** | 0（`:51`） | ✅ |

14 个窗的逐窗三指标、停摆、沿跨度我自己算了全表（`RECHECK_recompute_out.txt:69-83`），与 `REPORT.md:57-70` 的 14 行逐位一致（例：`archive_T34/w0` avg=0.360002 / live=33.952014 / p50=31.608560 / max_stall=24.734760 / edge_dt=0.265080；`l1_20261023e1/w0` avg=2.000796 / live=2.009701 / p50=36.030842；`l1_20261023hb/w0` avg=10.002423 / live=10.066570 / p50=30.159999）。`:84-86` **12 个 `live_fps>=28`、2 个 `<28`**，`max_stall_s` 范围 **2.558256–24.734761 s**，14 窗 `n_multi_advance` 全为 0（`:69-83`），与 `mixed_classification_out.txt` 一致。

**立场复核**：源码 `:4733` 明确称 `fps_avg` 为「主对照指标（总量式，稳健口径）」；`:4794-4802` 的 `frame_ms` 只收 `df==1` 的相邻沿，停摆段没有新沿，**根本不进入分位样本**。把 `fps_p50`（或 `live_fps`）升为主指标，等于把「前 31 fps、后 20 s 不动」判成「不卡」——这确实改掉了「用户可见卡顿」的定义。报告 §3 的对抗自查站得住。判 **CONFIRMED**。

**附带勘误（不影响上述结论）**：
- `REPORT.md:45` 把 40 个不可算窗拆成「37 个零推进/空窗 + 2 个不足 2 样本 + 1 个 counter 回绕」。我从原始 JSON 按 `stats` 分（C6）得到 **35 个 `logic_frames=0` 零推进 + 4 个 `samples<2` 空窗 + 1 个 counter 回绕**（`l1_20261023e4/measure_w1.json` 的 `logic_frames=-3557`）；核验员自己的 `recompute_out.txt:46,49,50,53` 也列了 4 条 `samples=0`。分类措辞有误，总数 63/40 不变。
- `REPORT.md:57-70` 的 `fps_p50` 用的是**从 6 位小数 samples 重算值**（如 T32 `30.912857`），而 `mixed_classification_out.txt:2-15` 用的是**原始 JSON 的 stored 值**（T32 `30.912618`）。二者差 ≤0.0007 fps，来自 `:5326` 的 round，非计算错误；但同一份报告里两套数混排，引用时应注明口径。

### ③ V1-A4 —— 「跨时段 3 倍差与 ρ=0.8925 不成立」 → **PARTIAL**（混淆与伪重复部分 CONFIRMED；「未复现 0.8925」这一具体论断 **REFUTED**）

**A. 混淆与伪重复（CONFIRMED，我自己复算）**：

- `RECHECK_recompute_out.txt:148-158`：从原始 JSON 直接读 `l1c_20261021`（units0=881）三窗 `live_fps` = 9.221340 / 9.132282 / 10.035138（约 9.2），`l3_1101v4d`（units0=1225）三窗 = 31.180659 / 31.268243 / 31.267323（约 31.2），**3.4 倍差本身存在**；但二者 `map_sha256` 前缀分别 `0add791d11aea84d` / `f3bb0a4efdedd067`，全库 **10 种 map SHA**（`:155`），`gamemd_sha256` 全库唯一 `73201cc0...`（`:156`），`hz=500`、`schema=MEASURE_V1` 全库一致（`:157-158`）。
- `RECHECK_recompute_out.txt:161-167`：`l1c_20261021/_launch_result.json` 的 `argv[0]` = `qc151_trip.harness3.py`；`l3_1101v4d/_launch_result.json` 的 `argv[0]` / `harness` = `qc151_trip.harness8_v4.py`、`harness_sha16=38244d2907e7f7fa`。**不同 harness + 不同载体图**，所以「同一负载跨会话时段差 3 倍」不能归因为时段。我还 grep 了 9 份 harness 源码，`span = t_b - t_a` / `logic = int(f_b)-int(f_a)` 在 harness3/4/5/6/7/8/v3/v4 中一致 → 口径同、工具链/载体图不同，报告的定性成立。
- `RECHECK_recompute_out.txt:132-134, 146`：**44 个 trip_id**、**29 个 trip 有 3 窗**、63 个可算窗只来自 **34 个 trip**；C6 另算 **30/30 个多窗 trip 的窗内 `pre_fps15` 完全相同**（报告 §5 说「30 个 trip」，正确）。按窗把 3 窗当 3 个独立样本确属**伪重复**，报告主动揭露了这一点，值得记功。

**B. 但「ρ=+0.8925 未复现」被我自己的重算推翻（这是本次复核最重要的发现）**：

我自己实现 Pearson（不调库，`RECHECK_recompute.py:pearson`），从 63 个可算窗的原始 `gate.pre_fps15` 与首末沿 `live_fps` 重算（`RECHECK_recompute_out.txt:135-146`；C6 另跑一次逐子集对照）：

| 样本口径 | n | 我算的 ρ(pre_fps15, live_fps) |
|---|---:|---:|
| 全库 | 63 | **0.8717331488140595** |
| 仅 25 s 窗 | 58 | **0.9583480571138665** |
| 按 trip 均值去重 | 34 | **0.8139209103941468** |
| w0 窗 | 34 | 0.8258578364885807 |
| w1 窗 | 16 | 0.9459273085620142 |
| w2 窗 | 13 | 0.9048420755017146 |
| **排除 `units0=0` 的 3 窗** | **60** | **0.8925119893960896 → 四舍五入即 +0.8925** |

被排除的 3 窗是 `l1_20261023e1/w0`、`l1_20261023hb/w0`、`l1_20261023k/w0`（`RECHECK_recompute_out.txt:140-143`，`units0=0`、pre=5.342/26.691/12.086）。**§544 背景声称的 `+0.8925` 是可精确复现的**，只是筛选条件（排除 `units0=0`）未在 §544 文本里声明。核验件 `REPORT.md:111` 与 `:120` 说「都没有独立复现本件背景声称的 +0.8925」「未复现 0.8925」，是**它自己漏试了 `units0>0` 这一最自然的筛选**；同目录 `V2/REPORT.md:193-197` 和 `V2/_v2_corr_out.txt` 已复现该数（我另跑 C6 得同一值）。`REPORT.md:120` 另称「ρ 依过滤条件在 **0.48–0.96** 间变动」：我在这条线的产出里找不到 0.48 的 ρ(pre,live)；`V2/_v2_corr_out.txt:9` 的 `+0.443479` 是**固定 harness 版本内的 ρ(units0, live_fps)**，不同量。我的实测 ρ(pre,live) 范围是 **0.8139–0.9583**。下界 0.48 未被本会话复现，属未证实表述。

**C. 因果部分（CONFIRMED）**：报告 §5 明确写「高相关既有『进局时帧率状态延续』的解释，也有重复计数/同源代码结构，**不能当作负载因果的独立验证**」，并在 `:112` 指出 `pre_fps15` 与 `live_fps` 共用同一 `perf_counter` 时钟、同一 `CurrentFrame` 计数器、同一趟 3 窗共享 `pre`；源码 `:5205-5218` 还显示 H8 武装时 `pre_fps15`「降为数据不设门」。**它没有把相关当因果**——这一条防守成功。

**综合判定 A4 = PARTIAL**：混淆/伪重复/不作因果的防守 CONFIRMED 且证据扎实；但「0.8925 未复现」这一具体事实判断被证伪（我算出 0.8925119894），「0.48–0.96」下界无依据。核验件自报 verdict=PARTIAL，与我独立判定的 PARTIAL 同档，但**理由不同**：它是「因未复现而 PARTIAL」，我是「混淆成立 + 数字复现失败 → 部分成立」。

---

## 2. 对 4 类指定陷阱的专门检查

| 陷阱 | 判定 | 我读到 / 跑到的证据 |
|---|---|---|
| **① 把「像素判据」当「OCR」** | **未发现** | 命令 `grep -rn -i "ocr\|像素\|pixel\|判据" "<V1>/"` 在 `REPORT.md` 全文（1–131 行）**零命中**（C6 的 grep 与另一次 `grep -n -i "ocr\|像素\|像素判据"` REPORT.md 均无 OCR/像素判据主张）。本件所有量化结论来自 `samples.t/f`、`frame_edges`、`map_sha256` 等结构化 JSON 字段与源码；§4 对 PNG 只写「w1/w2 末屏 PNG 显示同一遭遇战比分画面（时间 00:00:10）」，是**目视描述**，未声称 OCR 输出、未用像素阈值冒充文字识别。**但**：我独立解码两张 PNG（纯 stdlib zlib+PNG 滤波，`RECHECK_recompute_out.txt:224-227`）发现它们 **SHA256 不同、并非同一张图**：`f8290e34…`(269645 B) vs `83b6798e…`(269509 B)，800×600，**1687/480000 像素不同（0.3515%）**，差异 bbox `(x 164..762, y 9..246)`；分区域（C6）：比分面板 26/65550 像素差、**计时区 0/3675 全同**、**小地图 1612/7875（20.47%）不同**。所以「同一画面」应精确表述为「同一结算屏布局、计时字段像素完全相同，但小地图动态区域有 0.35% 像素差，**非字节/逐像素同一张图**」。报告未把两张图当两个独立统计样本（见下），未触发该陷阱，但措辞偏松。 |
| **② 把「样本」当「总体」** | **未发现** | `REPORT.md:45-46` 明说 63 个可推进窗 / 40 个不可算窗，阈值计数一律以 `COMPUTABLE_DENOMINATOR=63` 为分母（`:127`/我 `RECHECK_recompute_out.txt:62`），并把 40 个零推进/空窗单列、不硬塞进 `fps_p50` 统计；`:51` 明说「63 个可推进窗内 `FPS_P50_NONE_COUNT=0`，全 103 窗另有 40 个 `fps_p50=null`」。没有把 63 窗样本冒充 103 窗总体。我自己复算全 103 `fps_p50=null` = **40**（`RECHECK_recompute_out.txt:68`），一致。 |
| **③ 把「同一张图重复计数」当多个样本** | **未发现（且主动防守）** | 报告 §5 `:111-112` 主动指出 103 窗分属 44 个 trip、29 个 trip 各有 3 窗、63 可算窗只来自 34 个 trip、30 个 trip 的窗内 `pre_fps15` 完全相同，**并按 trip 均值去重算了 ρ=0.8139209103941468 (n=34)**（`adversarial_out.txt:21`；我 `RECHECK_recompute_out.txt:145` 复算同值）。它没有把同一趟 3 窗或两张 PNG 当独立样本充数——恰恰是它揭发了 §544 的伪重复。 |
| **④ 把「相关」当「因果」** | **未发现（且主动防守）** | `REPORT.md:112` 明确「不能当作负载因果的独立验证」，`:120` 说「未作为稳健**因果**结论成立」，§5 列出工具链/地图混淆、同义反复、重复计数三条反因果理由。我复算 `ρ(units0, live_fps) = -0.3500926807979979`（`RECHECK_recompute_out.txt:137`，与报告一致），按 trip 去重后 -0.29451175808764596（`:145`）——符号/数值随过滤变化，进一步支持「非因果」。 |

---

## 3. 其他独立核到的细节 / 勘误

1. **`archive_T34/qc151_fields.json:154-160` 引用行号错误**（`REPORT.md:101` 与自报 A3 keyFacts）。我读该文件物理第 154–160 行是 `ra2opt_play.bat` / `except.txt` 的 hash `expect/actual/match` 记录（C6），**不是** `current_frame` / `empty_window`。真实记录在 **`:2459-2460`（w0 `current_frame=302, empty_window=false`）、`:2516-2517`（w1 `=302, true`）、`:2579-2580`（w2 `=302, true`）**；JSON 数组下标是 `idx 152/154/156/158/160`（0-based），核验员把**数组下标**误当成了**物理行号**。另外 `REPORT.md:101` 说「w1/w2 JSON 及 `qc151_fields.json` 记录 `current_frame=302`」——我查 `measure_w1.json` / `measure_w2.json` 的**顶层键里没有 `current_frame` / `empty_window`**（C6），它们的 `stats.logic_frames=0`、`fps_avg=null`、`samples.f` 恒为 302；`current_frame/empty_window` 只在 `qc151_fields.json` 里。**事实方向对，出处错**。
2. **T34「无采样缺口」我逐样本复核成立**（`RECHECK_recompute_out.txt:90-129`）：`n_samples=12502`、`dt_sum = measured_span = 24.999840000004042 s`、`dt_min=12.0 µs`、`dt_max=0.003887 s`、`gap_gt_10ms_count=0`、`gap_gt_5ms_count=0`、`n_multi_advance=0`；10 个恒定帧段，最后一段 `f=302 idx=133..12501 duration=24.734760 s`，`f` 仅 293→302（9 帧）；`fps_avg=9/24.999840=0.360002304`（JSON `0.360002297`）、`live_fps=9/0.265080=33.952014`、`fps_p50=31.608560`（仅 9 个 `df==1` 沿间隔入样）。**低 `fps_avg` 不是测量器丢拍，是帧钟停摆**——与报告 §4 一致。w1/w2 的 `logic_frames=0`、`fps_avg=null`、`note="frame not advancing"` 也从原始 JSON 核实。
3. **报告 §2 的 `:58-59`、`:127-129`、`:144`、`:171` 等行号引用**：我跑了核验员自己的脚本（C4），输出与 `recompute_out.txt` **字节相同**，行号引用无误。
4. **`REPORT.md:72` 的「12 + 2」分型**：我复算 `MIXED_WITH_LIVE_GE_28=12`、`MIXED_WITH_LIVE_LT_28=2`（`RECHECK_recompute_out.txt:84-85`），并确认那 2 个（`l1_20261023e1/w0`、`l1_20261023hb/w0`）是 4 s settle 窗、`max_stall_s` 分别为 3.780845 / 2.558256 s——报告没有把 14 窗一律解释成「尾段停摆」，这个细分是对的。
5. **不可复现的产物**：`REPORT.md:37` 与 `:109-112` 把 `metadata_out.txt` / `launch_versions_out.txt` / `adversarial_out.txt` / `mixed_classification_out.txt` 写成「对应命令」但未在正文给出那几条命令的全文（只给了 `recompute.py` 与 T34 的 `-c` 片段）；`V1/` 目录里也没有生成这些 out 的脚本。我**没有**把这些 out 当原始证据，而是从原始 JSON 自己重算了对应的 44 trip / 10 map SHA / harness 路径 / ρ / 14 窗分型，数值均一致。**这 4 个 out 的生成命令在本会话内不可复跑（脚本缺失），据实记为 not run**，但结论已由 C3/C6 从原始件独立闭合。
6. **数据树并发写入**：见 §0。`l3_1101v4h/measure_w0.json`（18:26:53 新建，0 样本）使当前 `find|wc -l` = 104；它不改变任何阈值计数或相关系数（`RECHECK_recompute_out_104.txt`）。报告在 18:05 写「103」在当时是正确的。

---

## 4. 汇总判定（按本 ask 的 3 条抽样）

| 主张 | 我的独立判定 | 我自己重算的关键数 |
|---|---|---|
| **V1-A1** `fps_avg` 分母是实测整窗采样跨度，非活段、非硬编码 25.0；零推进写 null；`fps_p50` 为 `df==1` 沿间隔线性插值中位数的倒数 | **CONFIRMED** | 58 个名义 25 s 窗实测 span `24.899944–24.999961 s`，无一等于 25.0；`l3_20261031hb/w0` `169/24.899944=6.787164`（JSON 6.787164）vs `169/25=6.760000`；63 窗 stored/recomputed 0 处不符；源码 `:4757-4759/:4784-4791/:4794-4813/:4733` 逐行核实 |
| **V1-A2** 全量 103 窗：14 个低 `fps_avg` 高 `fps_p50` 窗；停摆应算卡顿，不得改主指标 | **CONFIRMED**（38 / 14 / 26 / 24 / 12+2 全部复现；两处小勘误见 §1②） | 103 文件 = 根 3 + 子 100；63 可算 / 40 不可算；38 / **14** / 26 / 24；14 窗 `max_stall 2.558256–24.734761 s`、`n_multi=0`；`live_fps<fps_avg` 的窗 = 0；源码 `:4733` 主指标定性 + `:4794-4802` 停摆不入分位样本 |
| **V1-A4** 跨时段 3 倍差与 ρ=0.8925 不成立（混淆 / 伪重复 / 非因果） | **PARTIAL** —— 混淆与伪重复、非因果防守 CONFIRMED；**「0.8925 未复现」被我证伪**；「0.48–0.96」下界无依据 | 44 trips / 29 个 3 窗 / 63 窗仅 34 trips / 30 个多窗 trip 共享 `pre`；10 种 map SHA、harness3 vs harness8_v4；ρ 全库 **0.8717331488140595**、去重 0.8139209103941468、仅 25 s 0.9583480571138665、**排除 `units0=0` 后 `0.8925119893960896` = §544 的 +0.8925**；ρ(units0,live) = −0.3500926807979979 |

**总体**：核验件的源码口径、全量数据复算、T34 特别核、以及对 §544「改主指标」推论的驳回，**证据扎实、可复现**，主体应判 CONFIRMED。唯一实质性缺陷在 §5 的相关数小节：漏试 `units0>0` 筛选导致误称「+0.8925 未复现」，并写了一个未复现的 0.48 下界；另有 `qc151_fields.json` 行号、40 窗拆分措辞、两套 `fps_p50` 精度口径、PNG「同一张图」措辞等**非致命**勘误。四类指定陷阱（像素判据当 OCR / 样本当总体 / 同图重复计数 / 相关当因果）**均未发现**，其中③④还是核验件主动防守成功的部分。

**未做的事（据实声明）**：未启动任何真机进程、未读进程内存、未改母本/台账、未 commit、未做 OCR（本报告对 PNG 只做纯 stdlib 解码的逐像素差与目视，不产出任何文字识别结论）；`metadata_out.txt` 等 4 个 out 的生成脚本不在 V1 目录，其**生成命令未跑**，但对应数值已由我从原始 JSON 独立重算闭合。

---

## 5. 本次产物（全部在本 V1 目录）

- `RECHECK.md` —— 本报告
- `RECHECK_recompute.py` —— 独立复算脚本（从零实现；只读原始件）
- `RECHECK_recompute_out.txt` —— 103 文件快照全量输出（229 行，无 Traceback）
- `RECHECK_recompute_out_104.txt` —— 并发新文件出现后的 104 文件快照复核（230 行）
- `RECHECK_orig_recompute_out.txt` —— 按报告 §2 命令重跑核验员 `recompute.py` 的输出（与 `recompute_out.txt` 字节相同，仅作可复现性对照；**不作为我数字的依据**）
