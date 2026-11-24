# R51-T1-TIE152 · 清掉 EVIDENCE 最后 152 件平票

执行员：t1-tie152　日期：2026-11-22（本地）
写目标：`lead\next_re_20261117_r14\R17_R91_T1_TIE152\`（唯一写目标，新建）
只读 `lead\`；未运行 `mev675.py`；未写 `lead\` 下任何既有目录。

---

## 一 · 六行交付

```
Q1 | 152 件 = 152 / 2969249 B ; 算式 1242−976−114 件=152 字节=46684779−41719570−1995960=2969249 ; 清单=tie152.tsv
Q2 | 分类: ①空/仅表头 0件/0B ②纯JSON 38件/1260606B ③纯日志 10件/29405B ④含地址<60% 74件/320160B ⑤其他 30件/1359078B
Q3 | 可裁 4 类: ①空/仅表头=0件（该类为空，无需裁）=应排(理由:空文件不可能是对象抄本) ; ②纯JSON(无地址)=应排19件/356461B+应留19件/904145B, 理由=JSON 里只有统计/计数键者非对象记录、逐 entry 记 entry/vt/slot/lo/hi/insn 者是对象记录体 ; ③纯日志(无地址无对象帧)=应排6件/5473B, 理由=整篇自检断言([PASS]/pass=/expected=)或统计量, 记录的是判定过程 ; ④含地址<60%=应排10件/39717B+应留57件/212527B+混合1件/57586B, 理由=地址占比低是因为正文是 ROW 推送件的四环文字记录(slot/RTTI/合同)，属对象记录体；统计/抽样表则属过程 ; ⑤其他=应排15件/25524B+应留12件/1321186B, 理由=逐 entry 反汇编/虚表登记簿是对象记录体，裸地址池/普查计数器/基线率不是 ; 仍判不了 1 组=10件/41607B, 缺=「过程证据能否顶替对象证据」这一口径在 lead\ 内无正面定义(差分/哈希核对/INI 内容清单/字符串表/带运行现场头的清单如何归属)
Q4 | 应排 50 件/427175 B ; 应留 91 件/2442881 B ; 应排+应留=141 件/2870056 B(占 96.6%件/96.7%B) ; 混合 1 件/57586 B ; 仍判不了 10 件/41607 B（凭什么判不了逐件见 §四）
Q5 | 正控: 法1(Python q5_py.py)=152件/2969249B ; 法2(PowerShell q5_posctrl_ps.ps1)=152件/2969249B | 一致 ; 字节算式闭合=True(46684779−41719570−1995960=2969249，且 =落盘 sum(bytes)=2969249)
OVERALL | 152 件里 141 件（96.6%）可按内容直接归边（应排 50 / 应留 91），只剩 10 件/41607 B（1.4%）判不了：其中 9 件卡在 lead\ 里没有一条规定说"过程证据能不能顶替对象证据"（口径一落即可裁），第 10 件（verify_w151b.log，115 B）是原文件里反汇编体本就缺失、内容无法补。这 152 件已实质收口，未决桶不再是"信号弱"而是"等一条口径"。
```

---

## 二 · Q1 · 152 件是谁、在哪（数字逐项给源）

### 算法（三份源清单，两次减法）

| 步 | 动作 | 源清单 + 列 | 脚本 | 结果 |
|---|---|---|---|---|
| S0 | 取 EVIDENCE 冲突基线 | `R17_R78_T1_RECLASS\files_excluded_prime.tsv` · 列 `label`=UNDECIDED ∧ `rel` 含 EVIDENCE | `q1_extract.py` | **1242 件 / 46,684,779 B** |
| S1 | 减 R44 逐件裁决 976 | `R17_R81_T2_EVID\_verdicts.tsv` · 列 `verdict`∈{对象抄本,过程输出}；字节取盘上 `stat` | `q1_extract.py` | **976 件 / 41,719,570 B**（对象 732/10,251,220 + 过程 244/31,468,350） |
| 减法一 | 1242 − 976 | | | **266 件 / 4,965,209 B** |
| S2 | 减 R46 同目录多数派 114 | `R17_R84_T2_EVID2\q3_final.py` 规则复算：同父目录已裁件 ≥3 ∧ 同向 ≥75% | `q1_extract.py`（重实现，不硬编码 114） | **114 件 / 1,995,960 B** |
| 减法二 | 266 − 114 | | | **152 件 / 2,969,249 B** |

### 逐步算式（件数与字节都闭合）

```
件数 : 1242 − 976 − 114 = 152
字节 : 46684779 − 41719570 − 1995960 = 2969249
        其中 41719570 = 10251220(对象732) + 31468350(过程244)
校验 : 落盘 tie152.tsv 的 sum(bytes) = 2969249  ✔ 与算式一致
       落盘 152 行 = 152 件 ✔ ; 跨 49 个目录
```

S2 的 114 是**复算**出来的，不是抄 R46 的结论：`q1_extract.py` 用 `_verdicts.tsv` 的已裁件按父目录聚合，重跑同一规则得到 114 件 / 1,995,960 B，与 `R17_R84_T2_EVID2\q3_final.txt` 的 `COVER 114/266 件 bytes 1995960` 逐字相同。

### 落盘

- `tie152.tsv` — 列 `rel / bytes / parent_dir / cn_lines / va_lines / first_line`，152 行。
- `bytes` = 盘上实际大小（`os.path.getsize`），不是清单里的列；`cn_lines`/`va_lines` = 前 8 KiB 内含中文字符的行数 / 含 `0x[0-9A-F]{6,8}` 的行数；`first_line` = 前 8 KiB 首个非空行。
- 152 件全部存在于盘上（1242 件整体 0 缺失，已核）。

---

## 三 · Q2 · 为什么"两种信号都弱"（逐件读内容，不看文件名/扩展名）

分类口径（`q2_classify.py`，全文读，上限 512 KiB）：① 无实质行 ② 可 `json.loads`（含 JSONL）且地址行=0 ③ 地址行=0 且过程迹象行 >0 ④ 地址行>0 且 地址行/非空行 <60% ⑤ 其余。

| 类 | 件 | 字节 | 代表例（该类最大件） |
|---|---|---|---|
| ① 空文件/仅表头 | **0** | **0** | 无（152 件里没有一件是空/仅表头） |
| ② 纯 JSON（无地址） | **38** | **1,260,606** | `S09_KPROVED7\_audit\EVIDENCE\feat_pool642.json` 369,871 B / 24,760 行 / 地址行 0 / 首行 `[` |
| ③ 纯日志行（无地址无对象帧） | **10** | **29,405** | `W54_save_determinism\EVIDENCE\step3_streamdiff.stdout.txt` 18,909 B / 187 行 / 地址行 0 / 首行 `####…` |
| ④ 含地址但 <60% | **74** | **320,160** | `RECON_UNMERGED\EVIDENCE\merge_records.txt` 57,586 B / 415 行 / 地址行 12（2.9%）/ 首行 `# 9 张 A 类卡的逐行并表登记…` |
| ⑤ 其他（含地址 ≥60%，或 0 地址既非 JSON 又无过程迹象） | **30** | **1,359,078** | `S05_KPROVED3\_audit\EVIDENCE\q3_cfg.json` 846,854 B / 首行 `[{"entry": "006F3330", "aligned16": true, …` |

### 为什么会双双跌破阈值（可复算，`q3_signals.py`）

用 R44 同一套正则（`R17_R81_T2_EVID\judge_q4_v2.py` 的 `OBJ_PATTERNS` / `PROC_PATTERNS_LINE`）在这 152 件上重算：

- 152 件里 `O≥3 ∧ O>P`（R44 可直接判对象的门槛）只有 **3 件**，且这 3 件都是 O 仅比 P 多 1（44 vs 43、15 vs 14、10 vs 9）——按 `judge_q4_v2.py` 的判据只会被判成对象抄本，但三件内容分别是字节差分、运行参数回显、merge 操作日志帧，**判据本身在"地址与横幅同密度"的文件上失效**（这也解释了它们在 R44 为什么会落进 tie：`strong` 帧或 `O>P` 只差一点）。明细见 `q3_signals.tsv`。
- 各类中位数：② JSON med O=0 med P=0；③ 日志 med O=0 med P=0；④ 含地址 med O=2 med P=1；⑤ 其他 med O=0 med P=0。
- 原因分三类，都不是"信号随机抖动"：
  1. **信号载体不在正则覆盖的形态里**：`ROW_*.txt` 类推送件用中文散文写四环（`环① 入口与函数边界 / 环② 类身份`…），地址写成 `entry=00524D70`（大写无 `0x`）、槽写成 `slot#8`、RTTI 写成 `.?AVInfantryTypeClass@@`——正则的 `0x[0-9A-F]{6,8}` 一行也匹配不到，于是 O=1~2。
  2. **内容确实是过程**：自检断言、perf 采样、基线率、抽样核对，本来就没有对象记录。
  3. **大 JSON 是单行**：`q3_cfg.json` 846 KB 全在 1 行里，逐行口径下"行数=1"，任何按行占比的门槛都失效。

---

## 四 · Q3 / Q4 · 能不能裁、裁完剩多少

判据（`q3_verdicts.py`，逐件写进 `tie152_verdicts.tsv` 的 `reason`）：按 EVIDENCE 写域「对象抄本 = **被测对象本身**的记录载体」判，不看文件名；`SPECIAL` 表的键只是"读哪几行"的入口，每条 `reason` 都写明实读到的内容（首行原文 / 键名 / 结构计数）。另附每件的 `slots / rtti / dislines / selft / stat / ring / a8` 计数字段供复算。

### 汇总

| 裁决 | 件 | 字节 | 占件 | 占字节 |
|---|---|---|---|---|
| 应排 | **50** | **427,175** | 32.9% | 14.4% |
| 应留 | **91** | **2,442,881** | 59.9% | 82.3% |
| 混合（须逐行拆） | **1** | **57,586** | 0.7% | 1.9% |
| 仍判不了 | **10** | **41,607** | 6.6% | 1.4% |
| 合计 | 152 | 2,969,249 | | |

**已归边 = 应排 + 应留 = 141 件 / 2,870,056 B = 96.6% 件 / 96.7% 字节。**

### 类 × 裁决

| 类 | 应排 | 应留 | 混合 | 判不了 |
|---|---|---|---|---|
| ① 空/仅表头 | 0 | 0 | 0 | 0 |
| ② 纯 JSON（无地址） | 19 件/356,461 B | 19 件/904,145 B | 0 | 0 |
| ③ 纯日志 | 6 件/5,473 B | 3 件/5,023 B | 0 | 1 件/18,909 B |
| ④ 含地址<60% | 10 件/39,717 B | 57 件/212,527 B | 1 件/57,586 B | 6 件/10,330 B |
| ⑤ 其他 | 15 件/25,524 B | 12 件/1,321,186 B | 0 | 3 件/12,368 B |

### 四类的判定与理由（卡 §二 Q3 要求"至少 3 类"）

**① 空/仅表头 = 0 件 → 应排（该类本身为空，无件可裁）**
理由：空文件/仅分隔线不可能承载任何被测对象记录，语义上必然不是对象抄本 ⇒ 应排。**实测该类 0 件**，所以这条判定在这 152 件上没有扣减作用；它的价值是证明"最省事的一刀不存在"——1224 件全盛（非空）内容。

**② 纯 JSON（无地址）= 应排 19 件 / 356,461 B；应留 19 件 / 904,145 B**
- 应排判据：JSON 里只有统计/计数键（`"p"/"N"/"K"/"n_col"/"n_vtab"/"n_slots"/"pool"/"has2"/"has4"/"alias_hit"/"abnormal"`），对象键（`"entry"/"vt"/"slot"/"lo"/"hi"/"insn"`）为 0。内容是派生比率/池规模/计数器。
  例：`S10_KPROVED2\_audit\EVIDENCE\ring2_census.json`（84 B，`{"n_col":1216,"n_vtab":1218,"n_slots":14044,…}`）——只有三个计数器，无一条对象记录。
  例：`S10_KPROVED2\_audit\EVIDENCE\vt_liveness.json`（164 B，`{"watch":{"007E8C94":".?AVFootClass@@",…}}`）——这是**要检测的监视名单**，属测试计划，未含检测到的对象事实。
- 应留判据：JSON 是逐 entry 的记录骨架（`entry`+`vt/slot` 或 `lo/hi/extent/prologue/insn`）。
  例：`S09_KPROVED7\_audit\EVIDENCE\feat_pool642.json`（369,871 B，逐 entry `{entry,n_insns,jcc,jcc_tgts,jump_table,n_dcall,…}`）。

**③ 纯日志（无地址、无对象记录帧）= 应排 6 件 / 5,473 B（+应留 3 件 / 5,023 B）**
- 应排判据：整篇是自检断言或统计表——`[PASS]/[B-POS]/expected=/actual=/pass=True`，或 `cpu/frame、moving、极差、变异系数`。
  例：`W62_bline_new_criteria\EVIDENCE\b_selftest.stdout.txt`（536 B，`[B-POS] expected=SAME_DISTRIBUTION actual=SAME_DISTRIBUTION pass=True`）——记的是判定过程，没有对象。
  例：`W104_sentinel2\EVIDENCE\selftest.txt`（2,085 B）——被测对象是**合成内存**（`build: 4 independent object graphs`），不是目标 EXE。
- 应留的 3 件不是"日志"而是被分类口径误落进来的对象记录（`S19-F1\...\task2_explore_summary.txt` = play 函数入口字节 + 调用点普查 `TARGET 00750920 sites=116 caller_fns=66`）。

**④ 含地址 <60% = 应排 10 件 / 39,717 B；应留 57 件 / 212,527 B；混合 1 件 / 57,586 B**
- **这是 152 件里最大的一类，也是"为什么地址占比低"的答案所在**：57 件应留里绝大多数是 `ROW_*.txt` 推送件（`NAMED_PUSH_S05_B2` 19 件、`NAMED_PUSH_S13_B1` 9 件、`S13_PUSH` 12 件）——它们用中文散文写四环，地址是 `entry=00524D70`（无 `0x` 前缀）、槽是 `slot#8`、虚表是 `vt 007EB610 槽 007EB630`，正文占比高的其实是文字，所以 `0x` 地址行占比只有 1/24~2/27。但内容是**被测函数自身**的边界/类身份/整体合同/使用见证——正是对象记录体。判据行原文见 `tie152_verdicts.tsv` 的 reason。
  例：`NAMED_PUSH_S05_B2\EVIDENCE\ROW_00524D70.txt`（2,677 B）——`环① entry=00524D70 … atlas size=332 B，反汇编 n_instr=87` / `环② 槽驻留 007EB630 [.rdata]，vtable base=007EB610，slot offset=+32` / `RTTI … name=.?AVInfantryTypeClass@@`。
- 应排 10 件是**抽样/普查统计**：`P0_ADJ4\...\step1_numbers.txt`（ENUM 行数/verdict 分布）、`step3_sample15.txt`（15 行确定性抽样核对）、`S13_DIRECT\...\scan_stats.txt`（解出指令 1,392,592 / 覆盖率 100.0%）。
- 混合 1 件：`RECON_UNMERGED\EVIDENCE\merge_records.txt`（57,586 B）——同一文件里既有 `006A5840 / M40 / evidence_or_basis=… / old_value=[静态推断] / new_value=[已证]`（对象事实），又通篇是 `## 卡名 (delta N 行)` 的 merge 操作日志帧。整件不能单一归属，须按行拆。

**⑤ 其他 = 应排 15 件 / 25,524 B；应留 12 件 / 1,321,186 B**
- 应留判据：逐 entry 的反汇编/虚表登记/槽归属记录。
  例：`S13_K8\EVIDENCE\vt_rtti_registry.txt`（420,298 B，`VT 007E1668 COL 007FA4D8 NAME .?AVCDFileClass@@ NSLOTS 17` + `slot 0 -> 00401950` 逐槽）。
  例：`S05_KPROVED3\_audit\EVIDENCE\q3_cfg.json`（846,854 B，逐 entry `{"entry":"006F3330","lo":"006F3330","hi":"006F3816","extent":1254,"first6":[…],"insn":[…]}`）。
- 应排判据：裸地址名单/普查计数器/基线率。
  例：`P0_ADJ5\_audit\EVIDENCE\pool_1669.txt`（16,690 B）——1,669 行**只有** 8 位地址（`00402F80`/`00405AB0`/…），无槽/类/虚表/字节列。地址列本身不携带对象事实字段，是候选池名单。
  例：`S10_KPROVED2\_audit\EVIDENCE\a_set.json`（864 B，`{"pool":398,"has2":397,"has4":50,"A":49,"A_entries":[…]}`）。

### 仍判不了：10 件 / 41,607 B（凭什么判不了，逐件写明，不写"信号弱"）

| # | 件 | 字节 | 为什么判不了 | 缺什么才能裁 |
|---|---|---|---|---|
| 1 | `W54_save_determinism\EVIDENCE\step3_streamdiff.stdout.txt` | 18,909 | 内容是 OLE 复合文档 A1/A2/B1/B2 四份的**字节差分**（`dirEntry id=0 off=0x6c (mtime) A1=40 3e ab 8a A2=d0 0b 6d de`、stream 偏移区间、LCP/LCS）。差分结果本身是被测对象的文件字节事实，但同件含 `equal=False`/`idxDiff` 运行期比较结论与 4 个时间戳 | 一条口径：**差分产物算对象记录还是过程记录** |
| 2 | `W61_third_badge_route\EVIDENCE\dialog_bytes_diff.txt` | 11,595 | 内容是 RT_DIALOG 148 的逐字节 before/after 标记（`0x000 N 01`、`before=664 bytes after=696 bytes`）。既是被测资源字节事实，又只以"前后对照"形式存在 | 一条口径：**patch 前后 diff 是否计对象抄本** |
| 3 | `W61_third_badge_route\EVIDENCE\resource_integrity_stdout.txt` | 351 | 全资源完整性核对（每资源 `len/sha256/identical=True`），断言结论与对象哈希同件 | 口径：哈希核对表算不算对象记录 |
| 4 | `W64_bootcamp_inventory\EVIDENCE\S4_only_stdout.txt` | 2,516 | MAPSELMD.INI 提取核对（`ra2md.mix offset=0x71D050 length=5573 sha256=… identical=True` + 节清单），提取校验结论与对象哈希混编 | 同 #3 |
| 5 | `W64_bootcamp_inventory\EVIDENCE\S4_q4_stdout.txt` | 2,265 | MAPSELMD.INI 节/阶段名清单（`[GDI] stage entries (7): 1=ALL01…`）+ 提取校验头。是被测数据的内容记录，但以"核对报告"形式给出 | 口径：**被测数据内容清单是否计对象记录** |
| 6 | `W97_artmd\EVIDENCE\probe04_stdout.txt` | 1,510 | artmd.ini 逐条核对（`Foundation=` / `VERIFIED in file` / 计数断言），数据事实与核对结论逐行混编 | 口径：INI 字段核对表算对象还是过程 |
| 7 | `W97_artmd\EVIDENCE\probe17_stdout.txt` | 658 | artmd.ini 规则字段实读（`NAPOWR [NAPOWR] Foundation=3x2 line 3262 VERIFIED in file` + `ALL ASSERTIONS PASSED`），同上 | 同 #6 |
| 8 | `W154_live\EVIDENCE\verify_w151b.log` | 115 | 仅 2 行：`=== all control-flow transfers (incl. jcc) targeting 0x55B8F0 : 0 ===` + `=== disassembly 0x55B860 .. 0x55B905 ===`。**反汇编体不在文件里** | 不是口径问题：**内容本身缺失**，需回原扫描产物 |
| 9 | `S10_K11\EVIDENCE\disk_read_snapshot.tsv` | 1,595 | 某次读取的现场（`# read_at=2026-11-18T05:45:52+08:00` / `# sha256=…` 头 + 逐行 `entry / subsystem / name / 语义文本`）。现场头让它像过程记录，正文是对象清单 | 口径：带运行现场头的对象清单如何归属 |
| 10 | `S18-K2\EVIDENCE\event_names.txt` | 2,093 | 事件名字符串表（`name[ 1] @00820920 -> 00820BE0 : POWERON` …）。属 .rdata 数据对象的内容记录，但不含函数体/槽归属 | 口径：**数据字符串表算不算对象抄本**（对象抄本目前只覆盖 .text 函数/.rdata 虚表） |

**一句话**：这 10 件没有一件是"两种信号都低到看不清"。它们的内容都读得很清楚；卡住的是 lead\ 里**找不到一条规定**回答"过程证据能不能顶替对象证据"——R44 的 `judge_q4_v2.py` 只定义了 O/P 行计数与目录多数派，R46 只定义了同目录多数派，`R17_R78_T1_RECLASS\decide_cprime.py` 只按 `why` 前缀归类；没有任何一处正面定义"差分/哈希核对/内容清单/字符串表"该落哪边。这 10 件里除 #8 是内容缺失，其余 9 件**口径一落即可裁**。

---

## 五 · Q5 · 正控（双实现）

两实现互不复用代码：

| | 法1 Python（`q5_py.py`） | 法2 PowerShell（`q5_posctrl_ps.ps1`） |
|---|---|---|
| 读表 | `csv.DictReader` | `Import-Csv -Delimiter "`t"` |
| 字节 | `os.path.getsize` | `[System.IO.FileInfo].Length` |
| 集合差 | list comprehension | `Where-Object` |
| 分组 | `dict` 累加 | `Hashtable` 累加 |

结果（日志：`q5_posctrl_py.txt` / `q5_posctrl_ps.txt`）：

```
         法1 Python                法2 PowerShell
base1242   1242 件 / 46684779 B     1242 件 / 46684779 B
R44 已裁    976 件 / 41719570 B      976 件 / 41719570 B
1242-976    266 件 /  4965209 B      266 件 /  4965209 B
R46 再裁    114 件 /  1995960 B      114 件 /  1995960 B
1242-976-114 152 件 / 2969249 B      152 件 / 2969249 B
落盘 tie152  152 件 / 2969249 B      152 件 / 2969249 B
集合相同     -                        True
字节闭合     True                     True
```

**一致**。字节算式闭合：`46684779 − 41719570 − 1995960 = 2969249`，且等于 `tie152.tsv` 的 `sum(bytes)` = 2969249，且等于两实现各自 `stat` 的 152 件字节和。

---

## 六 · 纪律自查

1. **REPORT.md** 已交，六行在开头。✔
2. 每个数字给了「源清单 + 列 + 脚本名」（§二 的表格、§三/§四的表头）。✔
3. **不靠文件名**：Q2 分类读全文（`q2_classify.py`）；Q3 每条 reason 写实读到的首行/键名/结构计数，`tie152_verdicts.tsv` 另带 `slots/rtti/dislines/selft/stat/ring/a8` 计数供复算。`SPECIAL` 表键仅作"读哪几行"的入口，判据在 reason 里。✔
4. 判不了的 10 件**单列**并逐件写明缺什么（§四末表），未硬塞。✔
5. 未取得项：无（152 件全部读到；唯一"读不到"的 `verify_w151b.log` 反汇编体是原文件本就没有，已按内容缺失处理，不是取不到）。✔
6. 未运行 `mev675.py`；未写 `lead\` 下既有目录（`R17_R91_T1_TIE152\` 为新建）。✔

## 七 · 产物清单

| 文件 | 作用 |
|---|---|
| `REPORT.md` | 本报告 |
| `tie152.tsv` | **Q1 主产物**：152 件，列 `rel/bytes/parent_dir/cn_lines/va_lines/first_line` |
| `tie152_verdicts.tsv` | **Q3 主产物**：152 件，列 `rel/bytes/class/verdict/reason` + 证据计数字段 |
| `q2_classes.tsv` | Q2 分类明细（含 `why`：分类命中的内容依据） |
| `q3_signals.tsv` | 用 R44 同一套正则重算的 O/P/nlines/o_frac/p_frac |
| `q1_arith.txt` | Q1 逐步算式落盘 |
| `q4_summary.txt` | Q2/Q3/Q4 汇总 + 判不了分组 |
| `q1_extract.py` | S0/S1/S2 三次集合差 + 落 tie152.tsv |
| `q2_classify.py` | Q2 分类器 |
| `q3_signals.py` | O/P 重算 |
| `q3_verdicts.py` | Q3 逐件裁决 + 落 tie152_verdicts.tsv |
| `q4_summary.py` | 汇总 |
| `q5_py.py` | Q5 法1（Python） |
| `q5_posctrl_ps.ps1` | Q5 法2（PowerShell） |
| `q5_posctrl_py.txt` / `q5_posctrl_ps.txt` | Q5 双方日志 |
| `_fix.py` / `_fix2.py` / `_fix3.py` | 修 q3_verdicts.py 里中文引号破坏字面量的补丁（保留以备复现） |
