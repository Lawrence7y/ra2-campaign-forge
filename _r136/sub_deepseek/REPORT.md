# R136-DS · F24 语料清单「现盘存活率」独立复算

角色 exec / 家族 deepseek / provider magpie-anthropic / model work/cn:deepseek-v4.1-flash
执行机：t628 (Linux x86_64)，全程只读。执行窗口 2026-11-25T09:17 ~ 09:20 +08:00。
脚本：`_r136/sub_deepseek/r136_f24surv.py`（自写，未复用任何既有报告代码）；原始机读结果：`_r136/sub_deepseek/r136_f24surv.json`。

## 归零核对（先确认口径，再算数）

被审对象 FACT_INDEX F24 行（取新版 V532，与 V531/V530 该行正文一致）主张的唯一可引用语料值：

> 对象证据集合（tier_final，本项唯一可引用的「语料」值）= **4,417 文件 / 737,517,286 B**（逐文件清单 `tier_final_4417.tsv`，回读 sum(bytes) 校验）

清单实际形态（自己读的表头，非照抄）：

```
$ awk -F'\t' 'NR==1{print "HEADER_FIELDS="NF; for(i=1;i<=NF;i++) print "  col"i"=" $i}' tier_final_4417.tsv
HEADER_FIELDS=4
  col1=rel
  col2=bytes
  col3=source
  col4=why_content
```

- rel 相对 **`lead/`** 根，不是工程根，也不是 `lead/next_re_20261117_r14/`（见 S6 反控实测）。
- 数据行字段数分布：`NF=4 : 4417`（无残缺行、无空行）。
- 快照 `files_tier_A_snap2.tsv` 的真实表头**与调度卡描述不同**，实际是 5 列：
  `rel / ext / bytes / mtime_ns / selfkind`，bytes 在**第 3 列**。调度卡写「列 rel / bytes / ...」，若按第 2 列取 bytes 会取到 `ext`。本卡按表头实际位置取第 3 列。

---

## S1 · 清单总行数与 sum(bytes)

**主张/预期值**：4,417 行 / 737,517,286 B（F24 正文明确给出）。

**实测值**：**4,417 行 / 737,517,286 B —— 与主张完全一致。**

**命令与输出原文**：

```
$ wc -l lead/next_re_20261117_r14/R17_R101_TIER_FINAL_4417/tier_final_4417.tsv
4418 lead/next_re_20261117_r14/R17_R101_TIER_FINAL_4417/tier_final_4417.tsv

$ awk -F'\t' 'NR>1{c[NF]++} END{for(k in c) print "NF="k, c[k]}' tier_final_4417.tsv
NF=4 4417

# 脚本内：S1_n = len(rows); S1_bytes = sum(int(r[1]))
"101": {"rows": 4417, "sum_bytes": 737517286}
```

`wc -l` 的 4418 减表头 1 行 = 4417 数据行；sum(bytes) 逐行整数求和精确等于 737,517,286，无浮点误差。

---

## S2 · 逐行 stat 现盘（三桶）

**主张/预期值**：本卡不预设（F24 正文只给清单当时值，没有存活率主张；这正是本卡要测的）。

**实测值**：

| 桶 | 件数 | 字节口径 |
|---|---:|---|
| 仍存在且字节数与清单**完全相同** | **64** | 清单值 26,846,620 B |
| 存在但字节数**不同** | **1** | 清单值 913,237 B / 现值 17,624,355 B / **差 +16,711,118 B** |
| 完全不存在（ENOENT） | **4,352** | 清单值 **709,757,429 B** |
| 其他（EACCES 等） | **0** | — |

**逐件明细 — 「存在但字节数不同」仅 1 件（全部列出）**：

| rel | 清单值 | 现值 | 差值 |
|---|---:|---:|---:|
| `next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json` | 913,237 | 17,624,355 | **+16,711,118** |

**命令与输出原文**：

```
$ python3 _r136/sub_deepseek/r136_f24surv.py
S2 same_n=64 same_listed=26846620 diff_n=1 enoent_n=4352 enoent_listed=709757429 other_n=0

$ python3 -c "...json.load...json.dumps(d['S2']['diff_detail'])"
[
 { "rel": "next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json",
   "listed": 913237, "current": 17624355, "delta": 16711118 }
]

$ stat -c '%n %s bytes mtime=%y' lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json
lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json 17624355 bytes mtime=2026-11-19 22:52:48.672449600 +0800
```

**注（口径交叉核对，非主张抄写）**：该件差值 16,711,118 B 与 F24 正文所述「剔 `a2_sites.json` 的 `bounds` 段 16,711,118 B」数值吻合，且 `17,624,355 − 16,711,118 = 913,237` 与清单值**精确相等**。实测该文件当前 top-level 键为 `calls`(dict, 6728) / `bounds`(list, 1,392,592)，即**盘上仍是未剔 bounds 的原件**，清单记的是**剔后**的逻辑体量。所以这唯一一件的「不一致」不是文件被改坏，而是**清单对单件做了裁剪、盘上未落地**，属口径差异而非数据损坏。但必须指出：**`stat` 口径的「清单体量与盘上体量」在此件上永久不可比**，任何用 stat 复核该件的人都会得到 17,624,355。

**ENOENT 的构成（已逐件核实，非路径拼错）**：

```
# 脚本内 os.stat 逐行，异常分支区分 FileNotFoundError / NotADirectoryError / PermissionError
ENOENT 4352 件，无任何「有文件当中间路径」的 NotADirectoryError，无 EACCES

# 3 件抽样人工 ls 复核（全量由 os.stat 覆盖，见 S3 自检）
$ ls -l "codex_round_20261030/XVERIFY_R064RECHK_GLM_20261101/_raw/xr2_out.txt"
ls: cannot access '...': No such file or directory      # 连父目录 codex_round_20261030/XVERIFY_R064RECHK_GLM_20261101 都不存在
$ ls -l "next_re_20261117_r14/S09_KPROVED7/_audit/EVIDENCE/mesh_imm32.json"
ls: cannot access '...': No such file or directory      # 父目录在，且只剩 e8_sites_audit.json 一件
$ ls -l "gate_validate_20261108/_gv_out/_gv_compare_out.txt"
ls: cannot access '...': No such file or directory      # 顶层树 gate_validate_20261108 整个不存在
```

**首次缺失路径分量分布**（证明不是拼错，而是目录被整体移除）：

```
first-missing-component index histogram (0-based, rel 以 lead/ 为根):
   depth 0  855     <- rel 的第一段（如 next_re_20261112_r10/）整个不存在
   depth 1 3382     <- 顶层在、第二段不在（如 next_re_20261117_r14/S09_KPROVED4/）
   depth 2   86
   depth 3    7
   depth 4   22
symlink components traversed: (无)   # 4,352 条路径上无任何一级是符号链接，不存在软链失效导致的假 ENOENT
```

**整体消失的顶层树（855 件）**：

```
  213  lead/next_re_20261112_r10
  209  lead/next_re_20261112_r02
  141  lead/next_re_20261116_r12
   54  lead/next_re_20261116_r11
   47  lead/next_re_20261116_r13
   41  lead/goal3t_nightwatch_20261102
   38  lead/re_line_20261105
   30  lead/next_re_20261112_r09
   27  lead/next_re_20261112_r06
   16  lead/next_re_20261112_r03
   13  lead/next_re_20261112_r04
    9  lead/next_re_20261112
   ... (共 21 个顶层树全灭)
```

**删而非移动**：20 件缺失文件的 basename 在全 `lead/` 树内做有界 walk 检索，**命中 0**：

```
xr2_out.txt -> 0 hits     step7.stdout.txt -> 0 hits    DIS_006F6CA0.txt -> 0 hits
ROW_006D0A20.txt -> 0 hits  entry_bytes.tsv -> 0 hits    ring2_holds.tsv -> 0 hits  ...(20/20 全 0)
```

---

## S3 · 三桶自检（不重不漏）

**主张/预期值**：本卡不预设（自检项，正确结果必须相等）。

**实测值**：**件数三桶和 4,417 = S1 的 4,417 —— 相等；字节三桶和 737,517,286 = S1 的 737,517,286 —— 精确相等。自检通过，无重无漏。**

**命令与输出原文**：

```
$ python3 _r136/sub_deepseek/r136_f24surv.py
"S3": {
  "bucket_n_sum": 4417, "S1_n": 4417, "n_equal": true,
  "bucket_listed_bytes_sum": 737517286, "S1_bytes": 737517286, "bytes_equal": true
}
```

---

## S4 · 按 source 列分桶（5 个整数）

**主张/预期值**：本卡不预设（F24 正文给的是构成 3,786 ∪ 627 ∪ 3 ∪ 1，但**没给各桶字节和、没给存活率**）。

**实测值**：

| source | 件数 | 字节和 | 仍存在件数 | 仍存在字节和 | 缺失件数 |
|---|---:|---:|---:|---:|---:|
| `P1a_前8KiB行首VA>=60%` | 3,786 | 714,228,639 | **61** | 22,484,224 | **3,725** |
| `rejudge_R53_对象抄本` | 627 | 13,233,082 | **1** | 913,237 | **626** |
| `R62R63_重判对象侧` | 3 | 8,690,200 | **2** | 2,997,031 | **1** |
| `R64_重判对象侧` | 1 | 1,365,365 | **1** | 1,365,365 | **0** |
| **合计** | **4,417** | **737,517,286** | **65** | **27,759,857** | **4,352** |

各桶件数与 F24 正文构成（3,786 / 627 / 3 / 1）逐项吻合；各桶字节和复算亦与 F24 的 714,228,639 / 29,944,200 中的 `627 件` 主体口径可对上（见「分歧」第 2 条关于 13,233,082 与 29,944,200 的差额）。

**命令与输出原文**：

```
$ python3 _r136/sub_deepseek/r136_f24surv.py
$ awk -F'\t' 'NR>1{c[$3]++} END{for(k in c) print c[k]"\t"k}' tier_final_4417.tsv | sort -rn
3786	P1a_前8KiB行首VA>=60%
627	rejudge_R53_对象抄本
3	R62R63_重判对象侧
1	R64_重判对象侧

# 脚本 S4 输出（exists 判定 = os.stat 成功）：
P1a_前8KiB行首VA>=60%   {'n': 3786, 'bytes': 714228639, 'exists_n': 61, 'exists_bytes': 22484224, 'missing_n': 3725}
rejudge_R53_对象抄本    {'n': 627,  'bytes': 13233082,  'exists_n': 1,  'exists_bytes': 913237,   'missing_n': 626}
R62R63_重判对象侧       {'n': 3,    'bytes': 8690200,   'exists_n': 2,  'exists_bytes': 2997031,  'missing_n': 1}
R64_重判对象侧          {'n': 1,    'bytes': 1365365,   'exists_n': 1,   'exists_bytes': 1365365, 'missing_n': 0}
```

**「exists_bytes 合计 27,759,857」与 S2「same 桶清单值 26,846,620」差 913,237 —— 恰好是 a2_sites.json，因为 S4 的 exists 按「存在」计，S2 的 same 按「存在且字节相同」计。此差已解释，非矛盾。**

**R62R63 桶内 1 件缺失即 `mesh_imm32.json`（5,693,169 B）**，是该桶唯一未存活件，也正是 F24 四步翻案中体量最大的一件：

```
$ ls "next_re_20261117_r14/S09_KPROVED7/_audit/EVIDENCE/"
e8_sites_audit.json                       # mesh_imm32.json 已不在
```

---

## S5 · 「不存在」4,352 件去快照里查（区分「曾存在后被移除」vs「从来不存在」）

**主张/预期值**：本卡不预设。

**实测值**：**能在快照里找到且 bytes 逐字节相同的 = 4,352（100%）；找到但 bytes 不同 = 0；快照里也找不到 = 0。**

即：**这 4,352 件在 2026-11-22T12:31:10 的机械枚举里全部存在、且字节数与清单完全一致**。结论是「**曾存在、后被移除**」，**不是「从来不存在」**，也不是清单写错了路径。

**命令与输出原文**：

```
# 主实现（python，脚本内 S5）：
"S5": {"in_snap_same_bytes": 4352, "in_snap_diff_bytes": 0, "not_in_snap": 0}

# 异实现复核（awk join，rel 为键、比较快照第 3 列）：
$ awk -F'\t' 'NR==FNR{k=$1;b[k]=$2;next} FNR>1{v=$1; if(v in b){ if(b[v]+0==$3+0) same++; else diff++ } } END{print "indep_snap_same="same+0" indep_snap_diff="diff+0}' \
    /tmp/r136_enoent.tsv .../files_tier_A_snap2.tsv
indep_snap_same=4352 indep_snap_diff=0

$ awk -F'\t' 'NR==FNR{k[$1]=1;next} FNR>1 && ($1 in k){c++} END{print "found_in_snap="c+0}' \
    /tmp/r136_enoent.tsv .../files_tier_A_snap2.tsv
found_in_snap=4352
```

两种独立实现同得 4,352 / 0 / 0。

**加测（超出本卡要求，用于加强归因）——全清单 4,417 件对快照的覆盖**：

```
manifest rows: 4417
rows present in snap2 at all: 4417 (100.00%)
rows in snap2 with identical bytes: 4416
total missing now: 4352
  of which in snap2 with identical bytes: 4352
  of which in snap2 with diff bytes    : 0
  of which not in snap2               : 0
```

**4,417 件在快照里 100% 命中**，唯一字节不一致的正是 `a2_sites.json`（清单 913,237 vs 快照 17,624,355）——与 S2 的唯一 diff 件**同源同因**（清单记剔 bounds 后的逻辑体量，快照与盘上都是未剔原件）。这条交叉验证把 S2 的「1 件 diff」和 S5 的「0 件 diff」缝合成一个自洽解释，而不是两个孤立异常。

---

## S6 · 反控（两组）

**主张/预期值**：5 个清单外现存文件必须全部命中「存在」；把根从 `lead/` 换成工程根，命中数应显著下降。

### S6a 正控：清单外 5 个现存文件

先证明它们在清单里**行数为 0**（否则不算「清单外」），再 stat：

```
$ awk -F'\t' -v t="$f" '$1==t{c++} END{print c+0}' tier_final_4417.tsv ; stat -c '%s' "lead/$f"

in_manifest=0  stat_bytes=1166348  rel=next_re_20261117_r14/R14_COMMON.md
in_manifest=0  stat_bytes=24836    rel=next_re_20261117_r14/COMPACT_STATE.md
in_manifest=0  stat_bytes=3661     rel=next_re_20261117_r14/DISC_ESTABLISH.tsv
in_manifest=0  stat_bytes=58491    rel=next_re_20261117_r14/R17_R102_FACTINDEX_V530/FACT_INDEX.tsv
in_manifest=0  stat_bytes=26602    rel=next_re_20261117_r14/R17_R72_T1_CLEANSCALE/REPORT.md
```

**5/5 全部命中「存在」**，同一套 `os.stat(os.path.join('lead', rel))` 代码。→ S2 的 ENOENT 不是路径拼错。

（附注：我第一版正控误选了 `R17_R17_SLOT73_MAP/reverse_map.tsv`，实测它在清单里 **1 行**，不满足「清单外」，已剔除并换成 5 个 `in_manifest=0` 的件。这条自曝说明「清单外」是逐条验过的，不是想当然。）

### S6b 负控：换根重跑 S2

```
$ python3 -c "...对全部 4417 条 rel 用不同 base 求 os.stat 命中数..."
(A) lead/                          hits=  65 / 4417  (1.4716%)
(B) project root                   hits=   0 / 4417  (0.0000%)
(C) lead/next_re_20261117_r14      hits=   0 / 4417  (0.0000%)
(D) lead/../lead                   hits=  65 / 4417  (1.4716%)
```

- 换成工程根：命中 **65 → 0**，显著下降，**符合预期，根没选错**。
- 换成 `lead/next_re_20261117_r14/`：同样 **0**，进一步排除「rel 其实相对 r14 目录」的可能。
- `lead/../lead` 命中 65 与 A 相同，说明路径语义稳定（无软链骗人）。

---

## 分歧

### 1【最重要】F24 主张「4,417 件 / 737,517,286 B」是**历史快照值，不是现盘值**——实测现盘存活仅 65/4,417 件（1.47%），实体字节 44,470,975 B（为清单的 6.03%）

- **差在哪**：清单 4,417 件中有 **4,352 件（98.53%）现已不存在**，另有 1 件字节数与清单不同。现盘实际能 stat 到的只有 65 件。
- **更相信哪一个**：**两个都成立，但适用范围不同，F24 的措辞会被误用。** 清单值 737,517,286 B 是 2026-11-22 机械枚举时刻的**真实体量**（S5 已用快照 100% 逐字节证实这 4,352 件当时确实存在），所以作为「当时测得的语料体量」它**没有错**；但 F24 正文把它写成「此值测的是**磁盘体量**」且未标注失效期，任何读者在 09:17 之后拿这句去引用「现在的语料有多大」都会错约 **16.6 倍**（737,517,286 / 44,470,975 ≈ 16.58）。
- **依据**：S2 逐行 stat（3 件人工 `ls` 复核 + 全量异常分支分类：无软链中间段、非 EACCES、非 NotADirectory）；S5 双实现证明这些件当时在；20 件 basename 全树检索 0 命中证明是删除而非移动；首次缺失分量分布显示 855 件是**顶层树整体消失**（如 `next_re_20261112_r10` 213 件、`next_re_20261112_r02` 209 件），3382 件是 r14 下的子目录整体消失——这是**系统性清理**的特征，不是零散损坏。

### 2【F24 内部构成可复算，但 627 件的字节口径对不上】

- F24 正文写：「构成 = P1a 3,786 件 / 714,228,639 B ∪ 逐件判为对象者 **627 件**（`tier_final_4413.tsv`，**29,944,200 B**）」。
- **实测**：`tier_final_4417.tsv` 里 `rejudge_R53_对象抄本` 桶 627 件，**字节和只有 13,233,082 B**，不是 29,944,200 B；差 **16,711,118 B**。
- **这个差额恰好等于 a2_sites.json 被剔掉的 bounds 段 16,711,118 B**（29,944,200 − 16,711,118 = 13,233,082，精确相等）。
- **更相信哪一个**：**清单文件（13,233,082）**。理由：清单是逐件可比对的落盘产物，13,233,082 是我逐行整数求和；而 29,944,200 是引用的中间态 `tier_final_4413.tsv` 的值。F24 正文叙述顺序为「627 件 29,944,200 B」→「再剔 bounds 16,711,118 B」，读起来像是「先有 627 件、后剔 bounds」，那么**F24 应当把剔后的 13,233,082 写出来**，而现在写的是剔前的 29,944,200。这是 F24 正文的**中间值残留**，不影响总数（总数 737,517,286 已由 S1/S3 证实自洽），但会让复核者以为清单漏了 16.7 MB。

### 3【F24 末尾的算术在现盘不可复核；且 a2_sites.json 的「剔 bounds」口径与 stat 永久不可比】

- F24 写「该件 17,624,355 → 913,237 B」。实测盘上该件**现在仍是 17,624,355 B**，top-level 键为 `calls`(6728) / `bounds`(1,392,592)。
- 更相信哪一个：**清单的 913,237 是逻辑口径，不是盘上文件**。这意味着清单里掺了一件**不是文件真实体量**的条目。任何「用 stat 复核清单」的人必然在这一件上失败。建议 F24 在该件上显式标注「逻辑裁剪值，盘上为 17,624,355」。

### 4【非分歧但需记录：调度卡对快照表头的描述有误】

- 调度卡 S5 写快照「同为 TSV，列 rel / bytes / ...」。实测表头为 `rel / ext / bytes / mtime_ns / selfkind`，bytes 在**第 3 列**，第 2 列是 `ext`。按第 2 列取会直接拿到扩展名字符串。本卡按表头位置取第 3 列。若其他卡照卡面描述实现，会静默得到 0 命中或异常。

### 5【未跑/未验证项（如实声明）】

- **删除动作的发生时刻与执行者：未验证。** `lead/` 不在 git 管理下（`git rev-parse` → `not a git repository`），无版本历史可回溯；也未发现 `_hygiene`/prune/trash 日志。本卡只证明了「2026-11-22T12:31:10 在、2026-11-25T09:18 不在」这一区间，**未定位到具体删除事件**。未跑原因：本卡只读且限 8 分钟预算，不做 inode/atime 取证与日志全树检索。
- **`mesh_imm32.json`（5,693,169 B）等大件的去向：未追查。** 仅知其现在不存在、快照里字节相同。
- **未对 4,352 件逐条人工 `ls`**：人工只做了 3 件 `ls` 抽查；程序化 `os.stat` 覆盖 100%（4,352 件全部经异常类型分类，且 S5 双实现交叉、首次缺失分量统计、20 件 basename 全树检索佐证）。

---

## 产物清单

- `_r136/sub_deepseek/r136_f24surv.py` —— 自写测量脚本（只读，无 live 树写入）
- `_r136/sub_deepseek/r136_f24surv.json` —— 全量机读结果（含 4,352 条 ENOENT 逐条明细）
- `_r136/sub_deepseek/REPORT.md` —— 本文件
- 临时文件 `/tmp/r136_enoent.tsv` 已按约定清理（见下）

```
$ rm -f /tmp/r136_enoent.tsv && echo cleaned
cleaned
```
