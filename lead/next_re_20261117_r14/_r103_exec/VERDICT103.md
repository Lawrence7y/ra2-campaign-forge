# VERDICT103 · 门禁第 2/3/4 列是不是自由文本（独立复现）

执行者：R103-EXEC（hy4）。被测：`lead/next_re_20261117_r14/check_disc.py`（R102 版，`GATE_VER = 'R102'`，文件 md5 `9f64f5b35e148e791e8f6a5a72802077`）。
数据：`DISC_RECHECK.tsv`（31 行 + 表头，LF-only，7 列，md5 `114ee019d808a3809536976977cdc2a3`）、`DISC_UNVERIFIABLE.tsv`（冻结档 12 行，8 列，md5 `d1210ef02f03162d5c133725e92508f5`）。
复跑脚本：`r103_probe.py` → 结构化结果 `r103_results.json` → 原始 stdout `r103_probe_stdout.txt`。文本证据：`q5_col7_reads.txt`。

## 沙箱与复跑命令

沙箱 `/tmp/r103_exec/`：`lead/` 与顶层条目全部 symlink 指向真树；在 `lead/next_re_20261117_r14/` 内只把 `check_disc.py`、`DISC_RECHECK.tsv`、`DISC_UNVERIFIABLE.tsv`、`R14_COMMON.md` 复制成实体（`cp -p`，CRLF / LF 字节不变）；其余条目 symlink 指向真树。所有变异只写沙箱里的 `DISC_RECHECK.tsv`，每次跑完立即还原。真树文件只读，未修改。

```bash
harness-mem-budget
# MAX_SUBAGENTS=1（703.4 MB），本卡为主会话自做，未派子代理

cd /tmp/r103_exec/lead/next_re_20261117_r14
PYTHONDONTWRITEBYTECODE=1 python3 /home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/_r103_exec/r103_probe.py
# 输出 r103_results.json / r103_probe_stdout.txt
```

沙箱实体文件 md5（与真树逐字节一致）：

```text
9f64f5b35e148e791e8f6a5a72802077  check_disc.py
114ee019d808a3809536976977cdc2a3  DISC_RECHECK.tsv
d1210ef02f03162d5c133725e92508f5  DISC_UNVERIFIABLE.tsv
203b50e6069f7c3b68c7fa4405760029  R14_COMMON.md
```

基线（`r103_results.json` → `baseline`）：`exit=0`，FAIL 0 条。`r103_probe.py` 内 `assert io.open(TSV,'rb').read() == PRISTINE`，跑完 TSV 字节完全还原。

## Q1 · 第 3 列（可执行判据）

| 变异 | 退出码 | FAIL 数 | 首条 FAIL |
|---|---:|---:|---|
| 全 31 行第 3 列 → `x`（非负控） | 0 | 0 | — |
| 仅 id 3 第 3 列 → `x`（正控，id 3 今天会被 C11 读） | 0 | 0 | — |
| 反控：全 31 行第 3 列 → `TBD` | 1 | 31 | `C9 id 1 judge-column empty/placeholder (whole-cell tbd)` |
| 反控：仅 id 3 第 3 列 → `TBD` | 1 | 1 | `C9 id 3 judge-column empty/placeholder (whole-cell tbd)` |

**实测结论：第 3 列对门禁是自由文本。** 全表改成单字符 `x`、`id 3` 改成 `x`，退出码都为 0；只有 C9 的占位符判定（`check_disc.py:96-99`）会看它，`TBD` 反控被抓住。`check_disc.py` 全文对第 3 列只有一处读取：`96: _jp, _jr = _PLACE_IS(r[2].strip())`。判据内容本身从不参与任何检查（不查是否可执行、不查是否匹配 id/节/产物）。

C11 并不读第 3 列：C11 传给 `recheck_verify.verify_recheck_line(ROOT, r)` 的 `r` 是整行，但 verifier 只读 `row[3]`（第 4 列锚）做 R5 sha256 绑定（`recheck_verify.py:274,354-356`），不读 `row[2]`。所以“id 3 今天真的会被 C11 读”只适用于第 7 列，不适用于第 3 列；两种 `x` 变异退出码相同（都是 0）。

## Q2 · 第 4 列（必查的现有数据锚）

| 变异 | 退出码 | FAIL 数 | 首条 FAIL |
|---|---:|---:|---|
| 全 31 行第 4 列 → `ANCHOR-X`（非负控） | 1 | 5 | `C11 id 3 claims recheck but has no valid self-description line (R5 anchors mismatch: got sha256:22395a6103650a4840fe208f6a00fd2ae02f14)` |
| 仅 id 3 第 4 列 → `ANCHOR-X`（正控） | 1 | 1 | 同上（id 3） |
| 反控：全 31 行第 4 列 → `TBD` | 1 | 36 | `C9 id 1 anchor-column empty/placeholder (whole-cell tbd)` |
| 反控：仅 id 3 第 4 列 → `TBD` | 1 | 2 | `C9 id 3 anchor-column empty/placeholder (whole-cell tbd)` |

全表 `ANCHOR-X` 的 5 条 FAIL 分别命中 id 3/4/22/27/28 —— 恰好是这 31 行中**非冻结且第 7 列以「有」开头**的 5 行。冻结档 12 行（1/2/5/6/7/8/9/10/18/20/24/25）虽然第 7 列也是「有」，但 C11 把它们判成 `frozen-unverifiable`，不触发 R5 校验（C12 另行用冻结档自己的第 4 列跑锚，见下）。

R5 绑定层必须说清：`recheck_verify.py:274` 取 `anchor4 = row[3]`（**逐字，不 strip**），`:354-356` 用 `sha256(anchor4.encode('utf-8'))` 与产物中自描述行的 `anchors=sha256:<hex64>` 做整串比较。因此改第 4 列会使原本通过的 R5 立即失配 —— 这是自由文本的一个“内容校验”例外：对本行有自描述行的 5 个 id 而言它不是自由文本；对另外 26 行它仍是自由文本。C9 对该列同样只做占位词判定（`check_disc.py:97-101`）。C12 真跑的是 `DISC_UNVERIFIABLE.tsv` 自己的第 4 列（路径/表达式，`check_disc.py:346,353`），不是 `DISC_RECHECK.tsv` 的第 4 列；所以它抓不到这里对冻结档第 4 列的改写。

## Q3 · 第 2 列（节）

| 变异 | 退出码 | FAIL 数 | 首条 FAIL |
|---|---:|---:|---|
| 全 31 行第 2 列 → `§2.14`（真实存在） | 0 | 0 | — |
| 全 31 行第 2 列 → `§2.999`（不存在） | 1 | 31 | `C8 id 1 section '§2.999' not found in R14_COMMON` |
| 反控：仅 id 4 第 2 列 → `§2.999` | 1 | 1 | `C8 id 4 section '§2.999' not found in R14_COMMON` |

**实测：第 2 列只校验「存在」，不校验「对应」。** 全表改成同一个存在的节号 `§2.14`（原本分布在 §2.14..§2.98 共 19 个真实节）退出码仍为 0，31 条 C8 全过。证据代码：`check_disc.py:217` 从 `R14_COMMON.md` 抽出所有 `^## x.y` 节号集合 `secs`；`:221-223` 只判断 `r[1].lstrip('§').strip() in secs`，没有任何“该纪律号应属于哪个节”的映射检查。

## Q4 · 翻转矩阵（逐行单点变异，改完立即还原）

基线：id 1-10,18,20,22,24,25,27,28 第 7 列以「有」开头（17 行）；id 11-17,19,21,23,26,31-33 以「无」开头（14 行）。

### (a)(b)(c) 合并翻转矩阵（列内为「退出码 / 首个 FAIL」；每张表各自完整的行都已列出）

| id | (a) 有→无（探针） | (b) 无→有（探针） | (c) 无→无（探针措辞不同） |
|---:|---|---|---|
| 1 | 1 / C12 id 1 frozen but not claims-有 in DISC_RECHECK (freeze != escape hatch) | — | — |
| 2 | 1 / C12 id 2 frozen but not claims-有 in DISC_RECHECK (freeze != escape hatch) | — | — |
| 3 | 1 / C11b loadable gap drifted: [3, 11, 12, 13, 14, 15, 17, 26] != pinned [11, 12, 13, 14, 15, 17, 26] (fix the rows, then re-pin deliberately) | — | — |
| 4 | 1 / C11b loadable gap drifted: [4, 11, 12, 13, 14, 15, 17, 26] != pinned [11, 12, 13, 14, 15, 17, 26] (fix the rows, then re-pin deliberately) | — | — |
| 5 | 1 / C12 id 5 frozen but not claims-有 in DISC_RECHECK (freeze != escape hatch) | — | — |
| 6 | 1 / C12 id 6 frozen but not claims-有 in DISC_RECHECK (freeze != escape hatch) | — | — |
| 7 | 1 / C12 id 7 frozen but not claims-有 in DISC_RECHECK (freeze != escape hatch) | — | — |
| 8 | 1 / C12 id 8 frozen but not claims-有 in DISC_RECHECK (freeze != escape hatch) | — | — |
| 9 | 1 / C12 id 9 frozen but not claims-有 in DISC_RECHECK (freeze != escape hatch) | — | — |
| 10 | 1 / C12 id 10 frozen but not claims-有 in DISC_RECHECK (freeze != escape hatch) | — | — |
| 11 | — | 1 / C11b loadable gap drifted: [12, 13, 14, 15, 17, 26] != pinned [11, 12, 13, 14, 15, 17, 26] (fix the rows, then re-pin deliberately) | 0 / — |
| 12 | — | 1 / C11b loadable gap drifted: [11, 13, 14, 15, 17, 26] != pinned [11, 12, 13, 14, 15, 17, 26] (fix the rows, then re-pin deliberately) | 0 / — |
| 13 | — | 1 / C11b loadable gap drifted: [11, 12, 14, 15, 17, 26] != pinned [11, 12, 13, 14, 15, 17, 26] (fix the rows, then re-pin deliberately) | 0 / — |
| 14 | — | 1 / C11b loadable gap drifted: [11, 12, 13, 15, 17, 26] != pinned [11, 12, 13, 14, 15, 17, 26] (fix the rows, then re-pin deliberately) | 0 / — |
| 15 | — | 1 / C11b loadable gap drifted: [11, 12, 13, 14, 17, 26] != pinned [11, 12, 13, 14, 15, 17, 26] (fix the rows, then re-pin deliberately) | 0 / — |
| 16 | — | 1 / C11 id 16 claims recheck but has no valid self-description line (R1 line_count_for_discipline_16=0 (must be 1; product has 0 DISC_RECHECK lines total) | 0 / — |
| 17 | — | 1 / C11b loadable gap drifted: [11, 12, 13, 14, 15, 26] != pinned [11, 12, 13, 14, 15, 17, 26] (fix the rows, then re-pin deliberately) | 0 / — |
| 18 | 1 / C12 id 18 frozen but not claims-有 in DISC_RECHECK (freeze != escape hatch) | — | — |
| 19 | — | 1 / C11 id 19 claims recheck but has no valid self-description line (R1 line_count_for_discipline_19=0 (must be 1; product has 0 DISC_RECHECK lines total) | 0 / — |
| 20 | 1 / C12 id 20 frozen but not claims-有 in DISC_RECHECK (freeze != escape hatch) | — | — |
| 21 | — | 1 / C11 id 21 claims recheck but has no valid self-description line (R1 line_count_for_discipline_21=0 (must be 1; product has 0 DISC_RECHECK lines total) | 0 / — |
| 22 | 1 / C11b loadable gap drifted: [11, 12, 13, 14, 15, 17, 22, 26] != pinned [11, 12, 13, 14, 15, 17, 26] (fix the rows, then re-pin deliberately) | — | — |
| 23 | — | 1 / C11 id 23 claims recheck but has no valid self-description line (R1 line_count_for_discipline_23=0 (must be 1; product has 0 DISC_RECHECK lines total) | 0 / — |
| 24 | 1 / C12 id 24 frozen but not claims-有 in DISC_RECHECK (freeze != escape hatch) | — | — |
| 25 | 1 / C12 id 25 frozen but not claims-有 in DISC_RECHECK (freeze != escape hatch) | — | — |
| 26 | — | 1 / C11b loadable gap drifted: [11, 12, 13, 14, 15, 17] != pinned [11, 12, 13, 14, 15, 17, 26] (fix the rows, then re-pin deliberately) | 0 / — |
| 27 | 1 / C11b loadable gap drifted: [11, 12, 13, 14, 15, 17, 26, 27] != pinned [11, 12, 13, 14, 15, 17, 26] (fix the rows, then re-pin deliberately) | — | — |
| 28 | 1 / C11b loadable gap drifted: [11, 12, 13, 14, 15, 17, 26, 28] != pinned [11, 12, 13, 14, 15, 17, 26] (fix the rows, then re-pin deliberately) | — | — |
| 31 | — | 1 / C11 id 31 claims recheck but has no valid self-description line (R1 line_count_for_discipline_31=0 (must be 1; product has 0 DISC_RECHECK lines total) | 0 / — |
| 32 | — | 1 / C11 id 32 claims recheck but has no valid self-description line (R1 line_count_for_discipline_32=0 (must be 1; product has 0 DISC_RECHECK lines total) | 0 / — |
| 33 | — | 1 / C11 id 33 claims recheck but has no valid self-description line (R1 line_count_for_discipline_33=0 (must be 1; product has 0 DISC_RECHECK lines total) | 0 / — |

说明：「—」表示该 id 不属于该表的替换集合（(a) 只针对第 7 列以「有」开头的 17 行；(b)(c) 只针对以「无」开头的 14 行），并非缺失数据。

合计：(a) 17 行全部 exit=1 —— 12 个冻结 id 首报 C12，5 个非冻结可回跑 id（3/4/22/27/28）首报 C11b 缺口漂移，无一行首报 C11/C3；(b) 14 行全部 exit=1 —— 8 个 C11b 登记 id 首报缺口漂移，其余 6 个首报 C11 自描述行缺失；(c) 14 行全部 exit=0、零 FAIL。

## Q5 · 整串相等还是前缀？文本证据

**实测：门禁只读首字（`startswith('有'/'无')`），从不与任何规定字符串做整串相等比较。**

| 变异 | 退出码 | 首个 FAIL（代码来源） |
|---|---:|---|
| (a) id 1 有→无 | 1 | `C12 id 1 frozen but not claims-有 in DISC_RECHECK (freeze != escape hatch)` (C12) |
| (b) id 16 无→有 | 1 | `C11 id 16 claims recheck but has no valid self-description line (R1 line_count_for_discipline_16=0 (must be 1; product has 0 DISC_RECHECK lines total)` (C11) |
| (c) id 16 无→无（探针措辞不同） | 0 | — |

(a) 的 12 个冻结 id 由 C12 报「冻结但不再声明有」，5 个非冻结可回跑 id（3/4/22/27/28）由 C11b 钉死表报缺口漂移；(b) 的 8 个 C11b 登记 id（11-15/17/26）报缺口漂移，其余 6 个由 C11 自描述行检查报出。没有任何一行首条 FAIL 是 C3 或 C11 对「第 7 列声明被推翻」的直接报出。

`check_disc.py` 里读 `DISC_RECHECK.tsv` 第 7 列（`r[6]` / `_r[6]`）的每一处，逐行原文（1-based，来自 `q5_col7_reads.txt`）：

```text
81:     later = r[6].strip()
84:     elif not later.startswith(ALLOWED_LATER):
88:     if later.startswith('有'):
254:         if not _r[6].strip().startswith('有'):
293:     later = r[6].strip()
294:     if not later.startswith('有'):
336:         if len(_r) == 7 and _r[6].strip().startswith('有') and _r[0].strip().isdigit():
73: ALLOWED_LATER = ('有', '无')   # 以「有」或「无」开头
```

`:346` 的 `_c[6]` 读的是冻结档 `DISC_UNVERIFIABLE.tsv` 的第 7 列时间戳（同一份脚本里另一个文件），不列入本题。

**结论：所有读第 7 列的分支都是前缀判断。** `:81-89` 的 C3 只拒绝不以「有」或「无」开头的串；`:88,254,294,336` 全部是 `startswith`。因此 Q4(c) 那种“同为「无」开头、仅措辞不同”的变异**在原理上不可能被看见**：没有一个检查点区分「无（仅立条当轮自带）」与「无（探针措辞不同）」。C11b 只看「非『有』即缺口」，C11 只处理「有」，C3 只验证首字属于闭集合 —— 所有分支对「无*」整族等价。Q4(c) 的 14 行 exit 0 / 零 FAIL 正是该结论的动态验证。

## 总判定（逐列）

| 列 | 是否自由文本 | 依据 |
|---|---|---|
| 第 2 列「节」 | 是（仅受限为“真实存在”） | Q3：全表 §2.14 通过；只校验 `in secs`（`check_disc.py:221-223`） |
| 第 3 列「可执行判据」 | 是（仅受限为“非占位符”） | Q1：全表/单点 `x` 都通过；只有 C9 占位判定（`:96-99`） |
| 第 4 列「必查的现有数据锚」 | 部分自由：对 26/31 行是自由文本（仅非占位）；对 5 个有自描述行的非冻结「有」行被 R5 sha256 绑定 | Q2：`ANCHOR-X` 只打中 3/4/22/27/28；`recheck_verify.py:274,354-356` |

第 7 列同样是前缀语义的自由文本（只首字受控），但对「有」的翻转会被 C11/C11b/C12 间接抓住；对「无」的措辞变异完全不可见。

## 我无法判定的地方

1. **冻结档 12 行第 4 列被改写后，C12 为什么不 FAIL。** Q2 全表把 `DISC_RECHECK.tsv` 第 4 列改成 `ANCHOR-X` 后，冻结 id 仍无 FAIL；从代码看 C12 读的是 `DISC_UNVERIFIABLE.tsv` 自身的第 4 列（路径/表达式，`check_disc.py:346,353`），与本列无关。但我没有单独做“只改冻结档文件”的反控（该文件有 sha256 钉死，需同时改 `FREEZE_SHA256` 常量才可测），故只给出代码层解释，不选动态证据。
2. **Q4(a)/(b) 的首条 FAIL 是否被记录顺序偶然决定。** `fails` 列表按代码段追加（C6→C9→C7→C8→C10→C11b→C11→C12→C5）；“首条 FAIL”是脚本打印的第一条，不等于语义上最直接的失败。我没有进一步做“抑制 C11b/C12 后观察 C11 直接报错”的反控（那会修改被测脚本，超出本卡范围）。
3. **Q1 中 id 3 的“今天真的会被 C11 读”指的是第 7 列还是第 3 列。** 卡面措辞有歧义；我按列号字面理解做了第 3 列单点 `x`，同时确认 C11 经 verifier 只读第 4 列（`recheck_verify.py:274`），不读第 3 列。若 Lead 原意是“第 7 列”，应以 Q4/Q5 的结果为准。
