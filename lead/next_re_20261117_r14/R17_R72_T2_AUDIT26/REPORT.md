# R40-T2-AUDIT26 · 跨家族审计：`R14_COMMON.md` §2.26「度量器自污染与漂移」六条断言

> 审计员：`t2-audit26`（独立审计员，非 §2.26 执行方）
> 被审对象：`lead/next_re_20261117_r14/R14_COMMON.md:2482-2546`（`## 2.26`）
> 相关产物：`lead/next_re_20261117_r14/R17_R70_T1_REPRO/`（`REPORT.md` / `scale_summary_today.json` /
> `scale_vs_baseline.json` / `files_scale_today.tsv` / `contamination_check.log` / `_run_scale.log` …）
> 只读审计：**未修改任何被审文件**；本目录之外无写入。
> 纪律：结论只附我亲自读到的逐字引用；读不到写「未取得」。

---

## 0 · 交付（第四节格式，原文）

```
A1 | 成立 | 依据=mev675.py:259-261「for root, dirs, fnames in os.walk(args.lead):」「dirs[:] = [d for d in dirs if d.lower() != ".git"」「and os.path.normcase(os.path.abspath(os.path.join(root, d))) != out_excl]」——逐字核对：排除项恰为 (a) 目录名小写等于 ".git"、(b) 绝对路径（normcase）等于 --out 目录（:254 out_excl = os.path.normcase(os.path.abspath(args.out))）；文件级无任何排除，排除集严格只有这两个，且只作用于 dirs 不作用于 fnames。anchored「只排除 .git 与 --out 目录」成立。
A2 | 部分 | 依据=机制成立、因果数值不成立(部分)。①机制:mev675.py:266-272 只按扩展名白名单(PRIMARY_EXT 含 .tsv，EXPECT 于 :30 附近)与 getsize 计数，无「自身产物文件名」否决；:300 pat_path 与 :349 附近 _hits 输出都写在 args.out 之下，而 :260-261 只排 --out 整目录、不排单个文件名 ⇒ 若 --out ≠ --lead 下的目录，_hits_primary.tsv 必被下一趟 scan 计入。②但 T1 的实测里「+80,580,525 B」不是 _hits_primary.tsv:scale_summary_today.json 的 exclusions 明写 "R17_R70_T1_REPRO (this card's own out dir)" 被排除，我却在该 tsv 里读到第 16485 行「_hits_primary.tsv  .tsv  80580525」仍被计入(它不在 out 内)——**这一行是真的**；然而同文件第 16486-16500 行显示 R16_MEASURE_EVID675 下所有 .tsv/.json/.md 均被计入，且 24676 与 24693 差 17，恰好等于该目录当前 17 个被计数的文件 ⇒ 意味着「同一条命令」不是两个口径，而是两次不同快照。更关键的否定证据:contamination_check.log:2-5「_hits_primary.tsv 1 files 80,580,525 B / 其它R16 16 files 1,618,342 B / rest 24,676 files 1,504,414,642 B / TOTAL 24,693 files 1,586,613,509 B」，TOTAL 减去 _hits_primary.tsv 后 = 1,506,032,984 B，**但 rest+其它R16 = 1,504,414,642+1,618,342 = 1,506,032,984 B 也恰好相等**——即「干净值」不是「TOTAL − 一件产物」而是「另一个快照」，两次快照的差值 186,721 B 与 17 个文件的增量不同源。⇒ 因果链 A2 的「于是…被扫进去」这半句无可复现的产物支撑：_hits_primary.tsv 确实存在于 files_scale_today.tsv 第 16485 行（成立），但把它「从 TOTAL 中剔掉就得到 24,692 / 1,506,032,984」这一步不成立(见 A4)。
A3 | 不成立(数字有出处但同口径不成立) | 依据=三数出处+时刻如下：①24,650 / 1,503,651,599 —— R17_R70_T1_REPRO/_run_scale.log:5「[scale] 文件数 = 24,650   总体积 = 1,503,651,599 B = 1434.0 MB = 1.40 GB」，该 log mtime 2026-11-22 11:53:53（step1）；②24,691 / 1,507,135,243 —— **盘上任何产物文件里都没有**：全树 grep `24691` / `1507135243` 只命中 REPORT.md:142、:260 与 §2.26 自身及 _r38 草稿；REPORT.md:142「2026-11-22 12:19（同命令重跑两次）| 24,691 | 1,507,135,243 | 两次完全一致」**是唯一出处，且是文本转录、无 log、无 json**（T1 自己 §6 只能援引这行）；③24,693 / 1,586,613,509 —— scale_vs_baseline.json:4-5「"files_total": 24693, "bytes_total": 1586613509」，generated_utc 2026-11-22T04:23:27+00:00（=12:23:27 本地）与 contamination_check.log:5「TOTAL 24693 files 1,586,613,509 B」（log mtime 12:23:17）。**但同口径不成立**：scale_summary_today.json（generated_utc 2026-11-22T03:55:10Z = 11:55:10 本地）给的是 files=24676 / bytes=1586426788，与其 _run_scale_measure.log:1「[scale_measure] files=24,676 bytes=1,586,426,788」一致；24,676 与 24,693 差 **17**，正好是 files_scale_today.tsv 里 R16_MEASURE_EVID675 目录下的 17 个行（第 16484-16500 行）；而 11:53 那一趟（24,650）同一目录同样含 _hits_primary.tsv。三数分属三条不同命令路径（mev675.py --stage scale / 未落盘的「同命令重跑两次」/ scale_measure.py 或另一遍 scale），且 24,650 与 24,691 之间差 41 文件 / 3,483,644 B，在 11:53 之后按 mtime 只增长了 17 文件 / 1,644,874 B ⇒ 「4 分钟内漂移」的 41 里至少有 24 文件 / 1,838,770 B 无法归因，**且 24,650 那一趟之后 mev675.py 的 search 会在 --out 里再写 _pats_primary.tmp（.tmp 不在 6 扩展名里，不计）**——「同一条命令」这一措辞三数中只有一个数有 log 支撑，另两个（24,691）无产物。⇒ 判不成立(就「同一条命令」+「互相同口径」而言) ; 同口径: 否
A4 | 不成立 | 依据=两个减法本身都对得上，但**减法不成立为测量**。复算: 24693-1=24692 ✓ ; 1586613509-80580525=1506032984 ✓（我手算与 PowerShell 复核一致）。问题在等式右边：我用 files_scale_today.tsv **亲自求和**得 24676 行 / 1,586,426,788 B（与 scale_summary_today.json:18-19 一致，可复算）；在该 tsv 内剔除第 16485 行 _hits_primary.tsv(80,580,525 B) 后得 **24675 行 / 1,505,846,263 B**——不是 24,692 / 1,506,032,984。差 **-186,721 B**。逐扩展名分解复算(excl 行)：.tsv 1464 行 494,752,674 B / .json 6709 行 411,090,247 B / .txt 9281 行 349,927,862 B / .md 4974 行 216,302,667 B / .log 2223 行 25,645,415 B / .csv 24 行 8,127,398 B = 1,505,846,263 B，与 scale_vs_baseline.json:13-14「"files_clean": 24692, "bytes_clean": 1506032984」以及同文件 :17-24 by_ext(.md 4987 / .tsv 1466 / .txt 9284) 全部不符（差 13 .md + 2 .tsv + 3 .txt = 18 行? 与实际 17 行差 1，且该 json 的 by_ext 总数 24,693 = files_total）。且 **scale_vs_baseline.json 无生成脚本**：本目录 .py 只有 scale_measure.py / readback_check.py / regex_env_probe.py / _run_readback_inproc.py，无 scale_vs_baseline.py（Get-ChildItem *.py 已核）；该 json 的 note(:3) 写「口径同 mev675.py:stage_scale」，但其 files_total 24,693 与 scale_measure.py 在 11:55:10 测得的 24,676 相差 17，**两个数不可能是同一脚本同一口径在同一 5 分钟内的两次结果**（除非有 17 个文件在 11:55:10 之后 12:23:27 之前写入——mtime 复核证实确有 17 个：R16 的 buckets675/recheck116/_judge_primary 与 T3_AUDIT2 的 11 个 out.txt 等，见下）。⇒ 「干净值 = 24,692 文件 / 1,506,032,984 B」在盘上**无一份逐文件清单能复算出来**（files_scale_today.tsv 不是它的底稿），判不成立（减法对，但被减数与结果不同源）。
A5 | 不成立(只是叙事) | 依据=无分解产物。要找「树增长 vs 自污染」的分解，盘上存在的只有两类：(a) **快照**——_run_scale.log:5(24,650/1,503,651,599，11:53:53)、scale_summary_today.json:18-19(24,676/1,586,426,788，11:55:10)、scale_vs_baseline.json:4-5(24,693/1,586,613,509，12:23:27)、contamination_check.log:5(同 12:23)；这些是四个时刻的**总数**，彼此口径不一致（见 A3/A4），不是分解。(b) **单件属性**——files_scale_today.tsv:16485「_hits_primary.tsv .tsv 80580525」是本审计能找到的唯一「自身产物被计入」的**单件证据**，它只能证明「该文件在 24,676 那个快照里被数了」，**不能**把 24,650→24,691 的 41 文件差额拆成「多少是树长、多少是自污染」。我按 mtime_ns 复核 11:53:46 之后新增的 16 个文件（第 16485 行 + 16486-16500 的 15 个 R16/T3 文件 + detour_profile_out.txt 等），合计 17 文件 1,644,874 B——**41 文件 / 3,483,644 B 的漂移里，有 24 文件 / 1,838,770 B 找不到任何单件对应**。全树内**不存在**按「新增文件来源分类（树自然增长 / 度量器自身产物）」落盘的 TSV/JSON；_r38/s226.md:23「⇒ 这也解释了上一轮看到的『漂移』为何比我预估的更快——**不全是树在长，有相当一部分是它自己写出来的东西被自己数了**」是散文，无数字、无来源分解表。⇒ 按本项目「闭集合/未留痕的叙事不算证据」，A5 判不成立（纯叙事）。
A6 | 成立(但措辞过强) | 依据=找到了，不止 T1 一处。全 lead 树递归搜 `36[ /]639`（排除 _hits_primary.tsv），命中并逐一读原文：① R16_MEASURE_EVID675/REPORT.md:52-53「| **`CTX_STRONG`** | **36** | 5.3% |」「| **`CTX_MEDIUM`** | **639** | 94.7% |」（该文件 mtime 2026-11-21 12:07:43 / 24,046 B，与 §2.26:2506 声明一致）；② 同文件 :13「`CTX_STRONG` 36 行、`CTX_MEDIUM` 639 行」、:44「修后干净语料上 **36/639/0/0 与 104/12 完全不变**」、:57「wide 口径 `STRONG 39 / MEDIUM 636`」、:69「36 行的锚点文件」、:81「合计 639（仅 6 个文件）」、:83「639 行 MEDIUM 里有 91.5%」；③ R16_AUDIT_EVID675/VERDICT.md:63「复现值：639 行 CTX_MEDIUM 中，最强锚点文件 = next_re_20261112_r10/W130_atlas/function_atlas.tsv 的行数 = 585（与执行方 585 精确一致）」、:65「639 行」、:46「## §B · 36 行 CTX_STRONG 是否 dump-only」；④ _cards/R16-CLERK-1054.md:35「四桶：**`CTX_STRONG 36` / `CTX_MEDIUM 639` / `CTX_WEAK 0` / `CTX_NONE 0`**」；⑤ _drafts/§1054.md:1、:34、:124、:146（「四桶 36/639/0/0 与 wide 39/636/0/0」）；⑥ R16_BASE/BOARD_R16_SEG5.md:5「四桶 **`CTX_STRONG 36` / `MEDIUM 639` / `WEAK 0` / `NONE 0`**」；⑦ LEDGER 系列 R17_LEAD_BASELINE/ledger.before_1055.md:39781/39793、LEDGER.before_{1056,1059,...,1076_112932}.md 同段（「四桶 36/639/0/0」）；⑧ 旁证（未被覆写的独立产物）：R16_MEASURE_EVID675/buckets675_wide.tsv mtime 2026-11-21 12:06:45、其 bucket 列实测 **CTX_STRONG 39 / CTX_MEDIUM 636**，与 REPORT.md:57 所述 wide 口径逐字吻合 ⇒ 可反推 primary 36/639 与 wide 39/636 是同一套判据的两个口径，历史 primary 分布虽被覆写但**同族宽口径原件仍在**。⇒ 「只剩 T1 报告里的记述」不成立（§2.26:2507 该措辞需改）；「不可从盘上重建」在**同口径原件**意义上成立（primary 原件已覆写，无法重算 36/639）。
OVERALL | §2.26 需改四处措辞：(1) A4/A5 的「干净值 24,692 文件 / 1,506,032,984 B」——两个减法都对得上，但盘上没有逐文件清单能复算出这个数（files_scale_today.tsv 剔除后是 24,675 / 1,505,846,263，差 −186,721 B，且 scale_vs_baseline.json 无生成脚本），须改写为「执行员转录值，本审计复算不符，待重测」；(2) A3 的「同一条命令」——24,650 有 log（11:53:53）、24,693 有 json+log（12:23）、24,691 无任何产物只有 REPORT.md:142 转录，三数互不同口径，须拆成「三个不同时刻/不同脚本的三次测量」；(3) A5「有相当一部分是它自己写出来的东西被自己数了」——无分解产物，41 文件差额里只有 17 文件 1,644,874 B 有单件证据，其余 24 文件 / 1,838,770 B 无从归因，须降格为「待分解」；(4) A6「只剩 T1 报告里的记述」——至少 8 处独立记载（R16/AUDIT_EVID675 REPORT.md、VERDICT.md、R16-CLERK-1054.md、§1054.md、BOARD_R16_SEG5.md、7 份 LEDGER 备份），且 wide 39/636 原件 buckets675_wide.tsv 仍在盘上，须改为「primary 原件已覆写不可重算，但 36/639 有多处独立记载」。
```

---

## 1 · 逐条审计过程与证据原文

### A1 · `stage_scale()` 的排除面

被指文件确认：`lead/next_re_20261117_r14/R16_MEASURE_EVID675/mev675.py`（928 行）。
`stage_scale()` 定义在 `:251`，循环体 `:259-261` 逐字：

```python
259:    for root, dirs, fnames in os.walk(args.lead):
260:        dirs[:] = [d for d in dirs if d.lower() != ".git"
261:                   and os.path.normcase(os.path.abspath(os.path.join(root, d))) != out_excl]
```

`out_excl` 的定义在 `:254`：

```python
254:    out_excl = os.path.normcase(os.path.abspath(args.out))
```

文件级循环 `:262-277` 只有扩展名过滤（`:263-264 if ext not in exts: continue`）与 `getsize`，
**没有任何文件名/路径前缀否决**。`:274-277` 只维护 biggest 列表。
⇒ 排除集严格 = {目录名 `.git`} ∪ {绝对路径 == `--out` 的目录}；作用于 `dirs`，不作用于 `fnames`。
anchored「只排除 `.git` 与 `--out` 目录」**成立**。

补充事实：`--out` 默认值就是脚本所在目录（`:901 ap.add_argument("--out", default=here)`），
所以「默认不设 `--out`」= 「不排除 `R16_MEASURE_EVID675`」。这一句 §2.26 没有写，但它是自污染的成因前提。

---

### A2 · 「于是 `_hits_primary.tsv` 在下一趟 `scale` 里被当成语料扫进去」

**能证实的部分**

- 机制：`stage_scale` 无文件名否决（A1）。
- `_hits_primary.tsv` 确实存在于被扫的语料清单里：
  `files_scale_today.tsv:16485`
  ```
  next_re_20261117_r14/R16_MEASURE_EVID675/_hits_primary.tsv	.tsv	80580525	1795319626529884900
  ```
  该文件位于 `R16_MEASURE_EVID675/` 下，而 `scale_summary_today.json:16` 明写排除项只有
  `"D:\\...\\R17_R70_T1_REPRO (this card's own out dir)"` ⇒ 它**不在**排除面内，被计入。
  这条是「自身产物被自己数了」的**唯一单件硬证据**。

**不能证实的部分（数值因果）**

`contamination_check.log` 全文 8 行：

```
1: R17_R70_T1_REPRO                  0 files              0 B
2: _hits_primary.tsv         1 files     80,580,525 B
3: 其它R16                            16 files      1,618,342 B
4: rest                          24676 files  1,504,414,642 B
5: TOTAL                         24693 files  1,586,613,509 B
7: 若排除 R16 的 _hits_primary.tsv（80.6MB，本次 search 的产物）:
8:   -> 24692 files / 1,506,032,984 B
```

我复算：`rest + 其它R16 = 1,504,414,642 + 1,618,342 = 1,506,032,984 B`，与第 8 行的「干净值」**逐字节相等**。
且 `rest` 的 24,676 行 = `scale_summary_today.json:18 "files": 24676`。
⇒ 第 8 行那个「干净值」其实是「**另一个快照**（24,676 + 16 = 24,692）」，不是「TOTAL(24,693) − 1 件产物」。
两件事同时成立才叫因果，而这里只有「_hits_primary.tsv 被计入」成立，
「剔除它就得到 24,692」是**把两个不同快照拼在一起**。

另：`scale_vs_baseline.json` 无生成脚本（本目录 `*.py` 只有 4 个，无 `scale_vs_baseline.py`），
其 `note` 声称「口径同 mev675.py:stage_scale」，但同一脚本 `scale_measure.py` 在 11:55:10 测得 24,676，
5 分钟后该 json 报 24,693 —— 期间确有 17 个文件写入（见 A3 的 mtime 复核），所以两次是**不同时刻**。

---

### A3 · 三个数（24,650 / 24,691 / 24,693）的出处与时刻

| 数 | 唯一出处 | 时刻 | 有无机器产物 |
|---|---|---|---|
| 24,650 / 1,503,651,599 | `_run_scale.log:5`「`[scale] 文件数 = 24,650   总体积 = 1,503,651,599 B = 1434.0 MB = 1.40 GB`」 | log mtime **11:53:53** | 有（log） |
| 24,691 / 1,507,135,243 | `REPORT.md:142`「`2026-11-22 12:19（同命令重跑两次）| 24,691 | 1,507,135,243 | 两次完全一致`」；`REPORT.md:260` 复述 | **12:19**（仅 REPORT.md 自述） | **无**。全树 grep `24691` / `1507135243` 除 REPORT.md 与 §2.26 及 `_r38` 草稿外**零命中** |
| 24,693 / 1,586,613,509 | `scale_vs_baseline.json:4-5`（`generated_utc 2026-11-22T04:23:27+00:00`）+ `contamination_check.log:5`（mtime **12:23:17**） | **12:23:27** 本地 | 有（json + log） |

**同口径判定：否。** 依据三处：

1. `24,676`（11:55:10，`_run_scale_measure.log:1`「`[scale_measure] files=24,676 bytes=1,586,426,788`」）
   与 `24,693` 差 **17**，我逐行核对 `files_scale_today.tsv` 第 **16484-16500** 行恰为
   `R16_MEASURE_EVID675/` 下 17 个被计数的文件（`REPORT.md` 24,046 / `_hits_primary.tsv` 80,580,525 /
   `_judge_primary.json` 20,746 / `_judge_wide.json` 20,398 / `_proof675.json` 33,545 /
   `_proof_subject.json` 92 / `_recall.json` 1,541 / `_rings.json` 670,701 / `_rings2.json` 131,407 /
   `_sample_draft.tsv` 2,622 / `_shortform.json` 3,926 / `buckets675.tsv` 301,579 /
   `buckets675_wide.tsv` 292,745 / `recheck116.tsv` 53,790 / `recheck116_wide.tsv` 53,593 /
   `sample18.tsv` 5,480 / `sample18_draft.tsv` 2,131）。
   **11:53 那一趟（24,650）同样含 `_hits_primary.tsv`**，所以「24,650 → 24,691」这 41 里
   `_hits_primary.tsv` 的贡献是 **0**，不是 80.6 MB。
2. `24,650` 与 `24,691` 差 **41 文件 / 3,483,644 B**；我按 `mtime_ns` 复核 11:53:46（`_hits_primary.tsv` 写入时刻）
   之后新增的 16 个文件（`R17_R70_T3_AUDIT2/a2..a12_out.txt` 11 个 + `R16_MEASURE_EVID675/{buckets675,recheck116,_judge_primary}`
   + `R17_R70_T5_DETOUR/detour_profile_out.txt`）合计 **1,644,874 B**。
   ⇒ 3,483,644 − 1,644,874 = **1,838,770 B / 24 文件**在此路径外，**找不到任何单件对应**。
3. 「同一条命令」不成立：24,650 走的是 `python mev675.py --stage scale`（`_run_scale.log`）；
   24,693 至少多了 `R16_MEASURE_EVID675` 里 3 个 11:54:50 新写的文件与 T3/T5 的产物；
   24,691 的「两次完全一致」无任何 log 可查（`REPORT.md` §7 列的日志清单里没有 12:19 的 log）。

`mev675.py` 的 stage 调用点（`:913-914`）确认 `scale` 的返回值被丢弃：

```python
913:    if args.stage in ("all", "scale"):
914:        stage_scale(args)
```

⇒ 三个数里只有第一个是「同一脚本 stdout 被原样留下」，第三个是另一条写入路径，
第二个连产物都没有。

---

### A4 · 复算

我亲自做的复算（PowerShell `Import-Csv -Delimiter "\t"`，逐行累加 `[int64]$_.bytes`）：

```
files_scale_today.tsv           : rows = 24676 , sum = 1586426788   （= scale_summary_today.json:18-19）
剔除第 16485 行 _hits_primary.tsv: rows = 24675 , sum = 1505846263
scale_vs_baseline.json:13-14     : files_clean = 24692 , bytes_clean = 1506032984
差                                : −186,721 B
```

逐扩展名（剔除后，我实测）：

| ext | n | bytes | `scale_vs_baseline.json:17-24` | 差 |
|---|---:|---:|---|---|
| .tsv | 1464 | 494,752,674 | 1466 | −2 |
| .json | 6709 | 411,090,247 | 6709 | 0 |
| .txt | 9281 | 349,927,862 | 9284 | −3 |
| .md | 4974 | 216,302,667 | 4987 | −13 |
| .log | 2223 | 25,645,415 | 2223 | 0 |
| .csv | 24 | 8,127,398 | 24 | 0 |

卡面要求的两个减法：

- `24,693 − 1 = 24,692` ✓（算术对）
- `1,586,613,509 − 80,580,525 = 1,506,032,984` ✓（算术对，我用 PowerShell 整数减法复核一致）

**但这两条减法不能推成「干净值」**：被减数 `24,693 / 1,586,613,509` 的逐文件底稿不存在
（`files_scale_today.tsv` 是 24,676 那一趟的，`sum` 已复核为 1,586,426,788，与 1,586,613,509 差 **186,721 B**）。
用现有的唯一逐文件清单做同样操作，得 `24,675 / 1,505,846,263`，与声称的干净值差 **−186,721 B**。
⇒ 判**不成立**（减法对；被减数与被声称结果不同源，无法在盘上闭合）。

另附 §2.26:2545 自己已写「24,692 / 1,506,032,984 这组干净值是**执行员的测量**……未复核每一个字节」——
本审计的复核结论是：**逐字节都复算不出来**，不是「未复核」的问题。

---

### A5 · 「漂移不全是树在长」是否有分解产物

盘上能找到的相关产物，我全部列在这里（闭集合）：

| 文件:行 | 内容 | 是分解吗 |
|---|---|---|
| `_run_scale.log:5` | 24,650 / 1,503,651,599（11:53:53） | 快照 |
| `scale_summary_today.json:18-19` | 24,676 / 1,586,426,788（11:55:10） | 快照 |
| `scale_vs_baseline.json:4-5` | 24,693 / 1,586,613,509（12:23:27） | 快照 |
| `contamination_check.log:5,8` | 24,693 → 24,692 | 快照 + 一次减法 |
| `files_scale_today.tsv:16485` | `_hits_primary.tsv  .tsv  80580525` | **单件属性**（唯一） |
| `readback_check_today.json:104` | `"files_scanned": 24660` | 另一套扫描面，非规模口径 |

**没有任何产物把漂移拆成「树自然增长」与「度量器自身产物」两栏。**
`_r38/s226.md:23` 与 `STATUS_BOARD.md:244` 的那句话是散文：

```
⇒ 这也解释了上一轮看到的「漂移」为何比我预估的更快——不全是树在长，有相当一部分是它自己写出来的东西被自己数了。
```

无数字；「有相当一部分」既未给比例也未给绝对值。
按 A3 的 mtime 复核，41 文件 / 3,483,644 B 的差额里能被单件解释的只有
**17 文件 1,644,874 B**（其中 `_hits_primary.tsv` 占 1 文件 80,580,525 B 字节但**文件数为 1**），
剩下的 24 文件 **没有任何对应**。
⇒ 判**不成立（只是叙事）**。符合本项目「闭集合/未留痕的叙事不算证据」。

---

### A6 · 「STRONG 36 / MEDIUM 639」在盘上还有没有别的记载

**找到了，至少 8 处独立文件**（全部亲读）：

1. `R16_MEASURE_EVID675/REPORT.md`（mtime 2026-11-21 12:07:43，24,046 B —— 与 §2.26:2506 声明的原件一致）
   - `:52` `| **`CTX_STRONG`** | **36** | 5.3% | 以该 entry 为主体的锚点，且不在工具参数位 |`
   - `:53` `| **`CTX_MEDIUM`** | **639** | 94.7% | 结构化表的主体列出现（`entry` 列一行） |`
   - `:13` 「`CTX_STRONG` 36 行、`CTX_MEDIUM` 639 行」
   - `:44` 「修后干净语料上 **36/639/0/0 与 104/12 完全不变**」
   - `:57` 「wide 口径 `STRONG 39 / MEDIUM 636`」
   - `:69` 「36 行的锚点文件全部同时承载别的 791 entry」
   - `:81` 「合计 639（**仅 6 个文件**）」、`:83` 「639 行 MEDIUM 里有 **91.5%**」
2. `R16_AUDIT_EVID675/VERDICT.md:46`「## §B · 36 行 CTX_STRONG 是否 dump-only —— PASS（抽样 12 行，含四环 0/12）」
   `:63`「复现值：639 行 CTX_MEDIUM 中，最强锚点文件 = …function_atlas.tsv 的行数 = 585（与执行方 585 精确一致）」
   `:65`「639 行里有无以该 entry 为主体的四环文档：0」
   —— **这是异族审计（hy4）独立复算过的 639**，比「T1 报告里的记述」强得多。
3. `_cards/R16-CLERK-1054.md:35`「四桶：**`CTX_STRONG 36` / `CTX_MEDIUM 639` / `CTX_WEAK 0` / `CTX_NONE 0`**（wide 39/636/0/0）」
4. `_drafts/§1054.md` `:1` / `:34` / `:124`（「`CTX_STRONG 36 / MEDIUM 639 / WEAK 0 / NONE 0`」）/ `:146`（「四桶 36/639/0/0 与 wide 39/636/0/0」）
5. `R16_BASE/BOARD_R16_SEG5.md:5`「四桶 **`CTX_STRONG 36` / `MEDIUM 639` / `WEAK 0` / `NONE 0`**」
6. `R17_LEAD_BASELINE/ledger.before_1055.md:39781,39793`（「四桶 36/639/0/0」）
7. `R17_LEAD_BASELINE/LEDGER.before_{1056,1059,1060,…,1076_112932}.md` 同段（7 份备份均含）
8. **旁证（同族判据、未被覆写的独立产物）**：`R16_MEASURE_EVID675/buckets675_wide.tsv`
   mtime **2026-11-21 12:06:45**（覆写前），我实测其 `bucket` 列 = `CTX_STRONG 39 / CTX_MEDIUM 636`，
   与 `REPORT.md:57` 的 wide 口径**逐字吻合**。
   ⇒ 36/639 不是孤立数字，它与仍在盘上的 wide 39/636 是同一套判据的两个口径。

对照：`s_rerun_buckets675.tsv` 确实是**新**产物（301,579 B，与覆写后的 `buckets675.tsv` 同尺寸，
`bucket` 列实测 `CTX_STRONG 41 / CTX_MEDIUM 634`），按卡面提示不计入原始记载。

**结论**：§2.26:2507「历史桶分布 36/639 已不可从盘上重建，只剩 T1 报告里的记述」
—— 后半句（「只剩 T1 报告」）**不成立**（≥8 处独立记载，含异族审计的独立复算）；
前半句（「不可从盘上重建」）在 **primary 原件**意义上成立（原件已覆写，无法重算），
但在「同族口径是否自洽」意义上**部分可验证**（wide 原件仍在）。

---

## 2 · 附带发现（不属于 A1-A6，但审计应报）

1. **`contamination_check.log` 与 `scale_vs_baseline.json` 的差集不可闭合**：前者第 3 行
   「其它R16 16 files 1,618,342 B」+ 第 4 行「rest 24676」= 24,692，与后者 `files_clean 24692` 相等，
   但后者的 `by_ext` 总和是 24,693（= files_total），两条内部不自洽。
2. **`files_scale_today.tsv` 的 `.tsv` 计数包含 `_hits_primary.tsv`**（第 16485 行），
   而 `scale_summary_today.json` 的 `by_ext_counts[".tsv"] = 1465` 也含它 ⇒ 该文件**不是干净语料**，
   却被 `REPORT.md` §6 当成「今日值」的落盘基准。
3. 本审计目录 `R17_R72_T2_AUDIT26` 在 `files_scale_today.tsv`（11:55:10 快照）中**0 行**
   —— 该快照早于本目录创建（12:28 之后），不影响上述结论。

---

## 3 · 产物清单（仅本目录）

| 文件 | 内容 |
|---|---|
| `REPORT.md` | 本文件：A1..A6 + OVERALL，逐字引用 + 行号 + 复算 |
