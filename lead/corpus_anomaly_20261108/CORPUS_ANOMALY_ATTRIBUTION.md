# CORPUS_ANOMALY_ATTRIBUTION · 语料异常 A/B 两项只读归因核查报告（终稿）

- 撰写：归因报告撰写员·GLM（动态工作流子件）；日期 2026-11-08。
- 铁律执行：零真机（未启动任何被测程序/未触碰活进程）、零采样代码（本报告新增脚本无 hook / 注入 / 动态解析代码）、语料只读、不改台账、唯一写域 = `lead/corpus_anomaly_20261108/`、不 commit / 不 push（HEAD=26574589aa8401e8f3f2934680a1ea7109bafa2d，本会话 `git log -1` 实查，与任务开始快照一致）。
- 上游材料：①编排方盘点（14 件指纹）；②分析员归因回件（inline 回件，复核员逐字落盘为 `_verify_hy4_object.json`）；③复核员回件（verdict=**confirmed**，实跑记录 `_verify_hy4_stdout.txt`）。
- 本报告自身实跑仅两项（输出见 §2/§4/§5）：`python -I -X utf8 lead/corpus_anomaly_20261108/_ca_report_fp_check.py`（指纹）与 `python -I -X utf8 lead/corpus_anomaly_20261108/_ca_report_ctx_check.py`（counters 上下文 + 语料 mtime）。其余数值结论系**引用**复核员实跑记录 `_verify_hy4_stdout.txt`（该记录在 §5 已绑定指纹）与分析员报告 `_ca_A_item…md`/`_ca_B_item…md`，均标注到行。

## 1 目的与边界

**目的**：对 `lead/slowframe_round2_20261107/SLOWFRAME_PROXY.md` 未验清单第 4、5 条做只读归因核查并落终稿——

- 第 4 条（SLOWFRAME_PROXY.md:221，本会话 Read 实读原文）：「`l1_20261023e4/measure_w2.json` 仅 12/25 个 units 有效读（`_proxy_scan_corpus_out.txt:62`），中断原因未查。」→ 本文 §3【A 项】。
- 第 5 条（SLOWFRAME_PROXY.md:222）：「`archive_T34/T36/T43` 的 fps_avg 异常低（0.36 / 7.12 / 7.28，:20、:23、:41）原因未查——本轮用 frame_ms_p50，不受影响。」→ 本文 §4【B 项】。

**边界**：

1. 只读归因：不改语料、不改台账、不恢复已撤回断言；`SLOWFRAME_PROXY.md`/`SLOW_WINDOW_LIMITS.md`/`qc161_trip.harness7.py`/语料趟件全部只读（§5 有 mtime 复查）。
2. 归因 ≠ 因果机制：本报告只确立「窗口内容 / 进程状态差异」层面的可归因事实，**不构成引擎快慢的因果机制结论**；两份分析员报告（`_ca_A_item…md` §3、`_ca_B_item…md` §3）均有同款纪律声明。
3. 「有效 / 无效」判据、fps 口径全部取自既有 harness 代码与既有普查脚本，非本次新造（§3、§4 引行号为证）。
4. 拿不到的证据写「未归因 / 未验」，不补造。

## 2 异常件清单与指纹

语料根 = `D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\`（`_ca_A_item…md:10` 记载；本会话 `ls` 确认 l1_20261023e4 / archive_T34 / archive_T36 / archive_T43 四目录均在）。

本会话实算 hashlib（`_ca_report_fp_check.py`，`python -I -X utf8` 运行，最终输出 `checked=17 match=15 mismatch/missing=0`）：12 件 measure_*.json + 2 件 md **共 14/14 与编排方盘点逐位一致**，另复核对象件 `_verify_hy4_object.json` 亦 MATCH（§5）。T43 两件首跑曾因本脚本预期字节数笔误（w0/w2 互换）报 DIFF，其 SHA256 本身即吻合；改正后重跑 15/15 MATCH，脚本与运行留痕均在本写域。

| 件（相对语料根 / lead） | SHA256 | 字节数 |
|---|---|---|
| l1_20261023e4/measure_w0.json | 8799e08dbc12e7f8674af9f7ade70d38fa4c46437861871b6d472c665616fdf9 | 271,414 |
| l1_20261023e4/measure_w1.json | 9439e8ef02725a76d3ce2dac2eba8b330a2e70b439dc4d3c79c0104590c7834e | 233,984 |
| **l1_20261023e4/measure_w2.json（A 项异常件）** | 8d85ac02ff78e228fc12f65da2c3f8850e6fda0c1f3f35d5ca7aec5dbe2b0540 | 106,895 |
| archive_T34/measure_w0.json（B 项异常件） | da30c275d8d985ddec019ce5a64f56c590b08a2f66499a7935d3b1b10df1cecd | 255,493 |
| archive_T34/measure_w1.json | 39f0aae1feff6c43894ce2011e2ea952d7ac7e5825271af888de3ae8eeb31d0c | 255,071 |
| archive_T34/measure_w2.json | 7cfe25d8447179772fdd827582c381e0e7d6685ed1f4eb98bf0230f4d140292b | 255,122 |
| archive_T36/measure_w0.json（B 项异常件） | 20ecf4cf5274760bdf8c6c5747eaddbabf33367584ca3e70f9c128d56d89572f | 259,112 |
| archive_T36/measure_w1.json | 434c6267c9fc465a500c48c2c44d06cd0a8ceba058a95171550a170e2c72e485 | 255,059 |
| archive_T36/measure_w2.json | b389f1a0a155cae913e38e7c97189d363f2af81b9125f1088d2257218c20b448 | 255,074 |
| archive_T43/measure_w0.json（B 项异常件） | 818f2c00be1499063871e70f03902c8eee8dff4deff6c30909b2663a0674103f | 259,244 |
| archive_T43/measure_w1.json | 813744fad706f3990564064b3110b754d1aee6184a3939f199c8069474523650 | 255,094 |
| archive_T43/measure_w2.json | 413223078e295f4ef9cc8b6a81a02cce9e642522f4083f5c9adbb5bdcf386358 | 255,062 |
| lead/slowframe_round2_20261107/SLOWFRAME_PROXY.md（A/B 断言源） | 5fe880595965de4e0b39639c0d4a80d626476a9715f1cae5efd7361a0c8985d3 | 26,916 |
| lead/slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md（同批参照件） | e7c29e06f48b2380d5bec3f99e08ac2a4ce90d94da27b48b98d5eb2113a75d60 | 23,707 |

分析员/复核员产出件指纹（本会话实算）：`_ca_A_item_l1_w2_units12of25.md` = 8588f6af60531dd3c8d26ee33e02fe7d5ceebf1d84675ff91c13d3e62eb9f870（7,184 B）；`_ca_B_item_T34_T36_T43_fps.md` = b8cce5be51a8e7c194e1b7332e4149b5dc8953358472d096c5581c87f82329bb（6,399 B）；复核对象件见 §5。

## 3 A 项：l1_20261023e4/measure_w2.json「units 仅 12/25 有效读」核查

### 3.1 「有效」判定标准（既有代码，非事后自造）

- 每秒 1 行 counters 副读：`lead/goal1_harness7_20261023/qc151_trip.harness7.py:4000-4004`（`row = _rpm_counters(handle)`，`next_ctr = t_now + 1.0`；本会话 Read 实读）。
- 每字段独立经 `ReadProcessMemory` 读 u32，**4 字节须全读否则视为失败**，失败返回 `None`：同文件 `:3897-3913`（`if not ok or got.value != ctypes.sizeof(buf): return None`）。
- 任一项读失败该字段写 `null` 不写 0（不可测写 null 是 Recorder 纪律）：`:3953` 区段（引自复核员摘录 `_ca_harness_sampler_3890_4110.txt` 与 `_verify_hy4_stdout.txt:188`）。
- 读失败不抛、退避 1 ms 继续守窗：`:3995-3997`（本会话实读）；错误串由 `:4012-4013` 生成（本会话实读）。
- 既有普查口径同源：`lead/slowframe_round2_20261107/_proxy_scan_corpus.py:58-59`（`isinstance(v,(int,float))`），其 mtime 2026-11-07 21:20 早于分析员报告 2026-11-08 19:18（`_verify_hy4_stdout.txt:40-43`）——**判据非事后调整**。

→ **units 字段非 null 即有效读**。12/25 的口径成立且唯一。

### 3.2 数值复核：12/25 属实

引用复核员独立重算（`_verify_hy4_stdout.txt:50-76`，本会话 Read 逐行核对）：25 行 counters，前 12 行（t_rel 0.000–11.012）units=640、ws_kb ∈ {138868, 138904, 139980}；第 13 行 row[12]（t_rel=12.015976）起 13 行 units/inf/g/b/techno 全 `null`、ws_kb=20、pf_kb=64。六种口径全部得 12/25（`:59-64`：not None / isinstance int,float / 非 0 / shape.g_valid True / ws_kb>1000 / 7 字段全非 null）。既有普查行 `_proxy_scan_corpus_out.txt:62` 第 9 列=12，与断言一致（`_verify_hy4_stdout.txt:39`）。JSON 尾 120 字节完整（`:74`），无截断。

### 3.3 中断原因：直接层面已归因——被测游戏进程在 w2 窗中段进入不可读终止态

被测对象：trip = QC161-U0800-L1-20261023E4，launch 记录 via_loader=false（直启）、pid 22628、主窗 hwnd 662272（`_ca_A_item…md:30`）；被测游戏主程序字节指纹 sha256 前缀 73201cc0…（同处，与 `carrier_post_state.json` 互证）。

证据链（除注明外均引自复核员实读记录 `_verify_hy4_stdout.txt`，本会话 Read 逐行核对）：

1. **样本断崖**：5949 个有效样本连续覆盖 span=11.894575 s，恰等于 `stats.max_stall_s`（`:68-70`），max gap 仅 0.006715 s——断崖后至 25 s 窗末再无有效样本；`error = "ReadProcessMemory 失败 6190 次（有效样本 5949）"`（`:67`）。失败期采样器按 `:3995-3997` 退避守窗——**是实况记录，不是采样器故障**。
2. **工作集塌缩**：counters ws_kb 从 139,980 KB 塌缩为 20 KB（`:66`）。ws_kb/pf_kb 经 GetProcessMemoryInfo 实测、失败写 null（harness `:3929-3945`，见摘录件）——20/64 KB 是进程终止态残影值。
3. **窗末取证**：rec 行 `measure_forensics_w2`（`:85`）：game_title=""、fg_title="BuddySwitch 整合预览版"、focus_ok=false、current_frame=null、**empty_window=true**；紧随 `verdict="degraded"`（`:86`），note「★ QC208 空窗降级：w2:empty」——harness 自己已把 w2 判为空窗。
4. **趟末旁证**：ISOLATION `CreateToolhelp32Snapshot(pid=22628) 失败: err=299`（ERROR_PARTIAL_COPY，`:87-88`）；TERM terminate_sent=true 且 `wait_returncode=0`（`:89-90`）；WER `wer_report_count=0` / `NO_NEW_REPORT`（`:91-92`）。
5. **except 件是历史遗留**：except_set_diff pre/post 各 1046 行、new=0、gone=0（`:93-96`）；except_post 文件名时间戳=采集时刻（harness `:5624-5662` 命名逻辑，见摘录件 `_ca_harness_except_5620_5670.txt`）——该转储是被动基线遗留件，**不能作为本趟中断的崩溃证据**。
6. **窗中断之前帧钟已停**：w1 取证 current_frame 已被重置为 0（`:84`，QC213P2 frozen_final 时刻），w2 samples f 全程恒定 [0]（`:71`）。
7. **时间对齐**（`_ca_A_item…md:40`）：t_abs0 → 本地 20:00:23.18；最后有效样本 ≈20:00:35.08；measure_w2.json mtime=20:00:48.20。

**归因结论（直接层面）**：w2 窗内 t_rel≈11.89 s（墙钟 20:00:35.1）起，被测游戏进程对所有被测地址停止可读、工作集塌缩至终止态残影值、主窗标题读空——被测进程在第三个采样窗中段自行退出/进入终止态，采样器按纪律守满 25 s 并如实记 6190 次失败。12/25 即由此而来。

**未归因（深层原因）**：游戏为何在 w1 末停帧换景（CurrentFrame 归 0）、又为何在 20:00:35 退出——语料内无任何记录：except 零新增行、WER 零报告、无 abort 件；`wait_returncode=0` 与 terminate_sent 并存使「自行干净退出 vs 终止竞态」**不可区分**；w2 末前台已被第三方应用（BuddySwitch 整合预览版）占据，但其与 20:00:35 事件的先后仅能夹逼在 (20:00:23, 20:00:48]，语料无法定序。**不补造。**

### 3.4 纪律声明

以上只确立「窗口内容/进程状态差异」：w2 是进程终止态空窗、w0 是战斗活跃窗。该趟 w0 活跃段 fps_avg=29.441、frame_ms_p50=32.62 ms（`_verify_hy4_stdout.txt:75`），与其他趟健康段同量级——**不构成任何引擎快慢的因果机制结论**。

## 4 B 项：archive_T34/T36/T43「fps_avg 异常低（0.36/7.12/7.28）」核查

### 4.1 数值复核：三值属实（口径=既有代码）

fps_avg 定义 = (末样本帧号 − 首样本帧号) / 样本时间跨度：harness `:4760` `st["fps_avg"] = logic / span`（本会话 Read 实读）；帧不推进时置 `note="frame not advancing"` 并返回（`:4755`）。

复核员对同批五趟 × 3 窗共 15 窗独立自算并与 stats.fps_avg 对照（`_verify_hy4_stdout.txt:101-115`，本会话 Read 逐行核对）：

| 窗 | stats.fps_avg | 自算 | \|diff\| | 帧号 | p50 |
|---|---|---|---|---|---|
| archive_T34 w0 | 0.3600022968 | 0.3600023040 | 7.2e-9 | 293→302 | 31.6087 |
| archive_T36 w0 | 7.1204500979 | 7.1204502973 | 2.0e-7 | 132→310 | 30.8874 |
| archive_T43 w0 | 7.2803948304 | 7.2803948886 | 5.8e-8 | 132→314 | 31.3484 |
| archive_T32 w0（健康对照） | 19.2802733943 | 19.2802737799 | 3.9e-7 | 296→778 | 30.9126 |
| archive_T40 w0（健康对照） | 31.0019330326 | 31.0019332806 | 2.5e-7 | 133→908 | 31.1346 |

与断言值 0.36/7.12/7.28 一致。精度注记：吻合为 ~8 位有效数字而非比特相同——counters 的 t 按 `round(…, 6)` 落盘（harness `:4002`，本会话实读），而 fps_avg 用全精度 logic/span（`:4760`），离线从存档 JSON 重算必有 ~1e-7 级差异（复核员减损点，§5）。另注意 `fps_avg` 精确值与普查行 `_proxy_scan_corpus_out.txt:20/:23/:41` 逐位一致（`_verify_hy4_stdout.txt:36-38`）。

### 4.2 异常原因：已归因——w0 窗内提前终局（败北记分板）冻结尾对 25 s 分母的稀释

1. **帧推进止点**（`_verify_hy4_stdout.txt:120-136`）：三趟 w0 帧边沿均为「~31 fps 匀速推进 → 某时刻起恒定」——T34 推进仅至 t_rel=0.26508 s（293→302，9 帧）、T36 至 5.665647 s（132→310，178 帧）、T43 至 5.810276 s（132→314，182 帧）；w1/w2 帧号恒定 302/310/314 且 `note="frame not advancing"`（`:123-138`）。
2. **终局签名（counters，1 Hz）**：本会话实读（`_ca_report_ctx_check.py` ①）T36/T43 w0 units 在 t_rel≈3.0 s 由 242→241（车辆死亡）后 8 行内恒为 241，infantry 恒 92；gate.units0=242（`:121/:128/:135`）。T34 自 row0 起即 units=241（败局在窗前 settle 期已定）。
3. **trip 判级**：三趟 trip-level MEASURE.verdict 均 `degraded`，note「★ QC208 空窗降级：w1:empty w2:empty」（`:125/:132/:139`）。
4. **终局截图同态**（复核员独立 stdlib zlib 像素直读，`:164-166`）：三趟 `measure_w1_end_x.png` avg=(85,66,51)、top 直方图逐 bin 相同、字节 269,645/269,628/269,625——同一确定性终局画面；与战斗帧（avg=(27,29,25)，`:167`）、与 l1 趟进程死亡后的空面（avg=(228,230,231)，`:168`）均不同。
5. **语料内既有定谳可衔接**：`out/re_work/work_chain/CONTINUE_20261003/lead/goal1_earlyend_analysis_20261018/EARLY_END_ANALYSIS.md:11/:67-79`（原文见 `_verify_hy4_stdout.txt:173-177`）已以反汇编+截图定谳同族 orig 图：人类 House 存活容器清零 → `HouseClass::AI` 逐帧歼灭检查（0x4F8F21–0x4F8F87）→ `DestroyAll()+AcceptDefeat()` → 记分板画面，帧钟停=记分板。三趟进局签名（units≈241-242/inf=92）与之一致。
6. **图归属**（`_maps_fixed` sha 实算，`:154-159`）：T34=spawnfix1（be07d2b4…）、T36/T43=spawnfix2（60cb0262…）、l1_20261023e4=spawnfix8（0add791d…）、T32=orig（93c2974b…）、T40=spawnfix4（9a249526…）——三趟均为该早停缺陷的修复迭代图。

**归因结论**：0.36/7.12/7.28 = 三趟战局在 w0 窗内（窗后 0.27 s / 5.7 s / 5.8 s 处）提前终局进入记分板态，fps_avg 按「全窗 25 s」分母稀释所致；非采样故障、非数值错误、非引擎变慢。

### 4.3 同批对比与「本轮用 frame_ms_p50 不受影响」

- 三趟活跃段 fps_p50 = 31.61/30.89/31.35、frame_ms_p50 = 31.64/32.38/31.90 ms（`:104/:107/:113` 与 `:145-149` 复核员自算），与健康趟 T32/T40（30.91–31.13 / 32.12–32.35 ms）完全同量级。
- frame_ms 只收相邻帧沿差 df==1 的入样（D-1 纪律，harness `:4761-4768`，本会话实读），冻结尾只贡献 1 个离群区间、不进中位——**断言方「本轮用 frame_ms_p50，不受影响」经复核成立**。
- 措辞减损（复核员减损点 1，本会话 `_ca_report_ctx_check.py` ①再证）：分析员报告「units 死亡后 counters 全行恒定」**偏宽**——实读 T36/T43 死亡行后 g 列仍有波动（T36 666→666→669→663；T43 673→667→665→665），ws_kb/pf_kb 数行亦波动；严格恒定的仅 units/infantry/b/techno。核心事实（units 恒定 + 帧停 + 空窗降级）不受影响。

### 4.4 未归因残留

1. spawnfix1/spawnfix2 各自「为何 ~10 局秒即终局」（早于 orig 图 ~24 局秒）：EARLY_END_ANALYSIS 的反汇编定谳针对 orig 图；三趟所用修复迭代图的逐图根因（出生点/容器清零时序差异）语料未载、趟载体已删，无法复核——**未归因，不补造**。
2. T34 gate.units0=242（12:17:42）与 w0 row0 units=241 之间的那次死亡发生在窗前 settle 期，语料仅此两采样点，无法更精确定位（如实记）。

### 4.5 纪律声明

本归因只确立「窗口内容差异」（战斗活跃段 vs 败北记分板段占比不同）——不构成「引擎慢/引擎快」的任何性能结论；慢窗判定引用这些窗必须先剔除终局尾（断言方本轮用 frame_ms_p50 正是如此，已核实不受影响）。

## 5 复核回件（含被核对象指纹绑定）与两项归因状态表

### 5.1 复核回件与对象绑定

- 复核对象 = 分析员 inline 归因回件，复核员逐字落盘为 `lead/corpus_anomaly_20261108/_verify_hy4_object.json`。
- **被核对象 SHA256 = c2b777e27358158b314e208c49e86179c2541b66e4633624995967c92471b385，字节数 = 4598**（字符数 2982；canonical json.dumps(ensure_ascii=False, separators=(',',':')) 逐字节复现；与 rollout 用户消息原文逐字提取件一致——`_verify_hy4_stdout.txt:4-8`）。本会话以 `_ca_report_fp_check.py` 重算，MATCH（§2）。
- 指纹可复现性脆弱点（复核员自记，如实转记）：换序列化（带尾换行 / pretty-print / ensure_ascii=True）即得不同 SHA；本报告按其 canonical 口径复现一致。

**复核 verdict = confirmed（五项复核全过）**，实跑 46 条命令，记录件 `_verify_hy4_stdout.txt`（连同脚本 `_verify_hy4_recompute.py`，`python -I -X utf8` 运行，EXIT=0）：

1. **独立重算**：counters 25 行、12/25 六口径（`:50-76`）；15 窗 fps 自算 |diff|≤3.9e-7（`:101-115`）。
2. **判据非事后调整**：普查脚本/输出 mtime 2026-11-07 早于 _ca_A 2026-11-08 19:18（`:40-43`）。
3. **归因充分且未越界**：§3/§4 证据链逐项实读；两份 _ca_ 均含纪律声明（_ca_A §3、_ca_B §3）。
4. **不可归因未被硬凑**：_ca_A §2「不可归因」、_ca_B §4 保留原状，回件 explainedCount=4 / unexplainedCount=2 与之相符。
5. **未改语料/台账**：复核员指纹 14/14（`:13-27`）、写域文件清单（`:205-206`）、语料目录 19:00 后无改动（`:207`）、产出脚本无禁用模式、HEAD 未变无 commit/push。本会话独立重放该 mtime 检查（`_ca_report_ctx_check.py` ②）：扫描四趟目录 220 件 + 2 个只读 md，**2026-11-08 19:00 后被修改者 = 0**。

复核员指出的三处减损（均不推翻核心归因，如实转记）：①「全行恒定」措辞偏宽（本会话已再证，§4.3）；②「fps_avg 逐位吻合」实为 ~8 位有效数字吻合（round(t,6) vs 全精度，§4.1）；③分析员自报 ranCommands=30 为其自身会话计数，复核与本报告均无法重放核验。另：分析员附注「Read 工具对 PNG 两次渲染返回无关环境截图（工具侧异常）」——复核员未复现该异常、改用独立解码器得到与分析员一致结果，该附注记**未验**（不影响任何取证结论）。写域现存 `_verify_` 件 4 件（复核回件点名 3 件，第 4 件 `_verify_hy4_out.txt` 系其重算脚本自身输出件，`_verify_hy4_stdout.txt:215`）。

### 5.2 两项归因状态表

| 项 | 被核断言（源） | 已归因内容 | 状态 | 未归因残留 |
|---|---|---|---|---|
| A | l1_20261023e4/measure_w2.json 仅 12/25 units 有效读，中断原因未查（SLOWFRAME_PROXY.md:221） | 12/25 属实（§3.2）；中断直接原因 = 被测游戏进程 w2 窗中段（t_rel≈11.89 s）进入不可读终止态（RPM 全失败 / ws_kb 塌缩 20 KB / 主窗标题读空 / QC208 空窗降级）（§3.3） | **已归因（直接层面）**；复核 verdict=confirmed | 深层原因：w1 末帧钟归零 + 20:00:35 退出的触发机制——语料无据（exit 0 与 terminate_sent 不可区分、WER NO_NEW_REPORT≠证明、第三方前台仅能夹逼） |
| B | archive_T34/T36/T43 fps_avg 异常低 0.36/7.12/7.28 原因未查——本轮用 frame_ms_p50（SLOWFRAME_PROXY.md:222） | 三值属实（15 窗自算吻合）；原因 = w0 窗内提前败北终局（记分板）冻结尾稀释 25 s 分母；活跃段 fps_p50 30.9–31.6 与健康趟 T32/T40 同量级；「frame_ms_p50 不受影响」成立（§4） | **已归因**；复核 verdict=confirmed | spawnfix1/spawnfix2 逐图 ~10 局秒终局根因（载体已删、语料未载）；T34 窗前 settle 期那次死亡（units0=242→row0=241）无法更精确定位 |

## 6 结论

1. **归因计数**：explainedCount = 4（A：12/25 属实；A：中断直接原因；B：三值属实；B：低 fps_avg 稀释机制）；unexplainedCount = 2（A：深层退出/停帧触发原因；B：spawnfix1/2 逐图秒终局根因 + T34 窗前死亡定位，按 §4.4 计 2 处）。severity = medium（分析员回件自评）。
2. **是否影响既有结论**：**不影响**。SLOWFRAME_PROXY 本轮判定用 frame_ms_p50，B 项三个低 fps_avg 不进入其判定链，且「不受影响」经复核与本报告双重核实；A 项原断言「12/25 有效读」数字成立，「中断原因未查」升级为「直接层面已归因、深层未归因」——SLOWFRAME_PROXY.md:221-222 的表述今后可据此收窄，但**本报告不改台账**（收窄属台账维护动作，须由台账责任方另行登记）。
3. **因果边界**：A/B 全部结论均为「窗口内容/进程状态差异」层面的归因，不构成引擎快慢的因果机制结论；引用低 fps_avg 窗作慢帧判定前必须剔除终局尾。
4. **未验项**：①Read 工具对 PNG 的两次异常渲染（复核员未复现，记未验，不影响取证）；②分析员 ranCommands=30 自报计数（不可重放核验）。
5. **不改语料声明**：本报告与全部上游核查产出（12 件 `_ca_` + 4 件 `_verify_` + 本报告 + 本报告 2 件检查脚本）仅落 `lead/corpus_anomaly_20261108/`；语料与台账**零改动**（本会话 220 件 mtime 扫描 0 命中 + `_verify_hy4_stdout.txt:207` 同结论）；未 commit / 未 push（HEAD=26574589aa8401e8f3f2934680a1ea7109bafa2d 未变）；零真机、零采样代码（本报告新增脚本仅 json/hashlib/os 标准库只读操作）。
