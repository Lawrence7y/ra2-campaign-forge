Q1 | band_c_wide.py:21 正则 = `RX_BACKUP = re.compile(r"(_before_|\.before|before_|_bak|backup/)", re.I)` flags=re.I(IGNORECASE) ; rollback_extra.py:19 = `RX_BACKUP = re.compile(r"(_before_|\.before|before_|_bak|\bbak\b|backup/|_backup)", re.I)` flags=re.I(IGNORECASE) ; 语义差异=两条 flags 相同、都以 re.search() 作用于清单 rel 列即全相对路径(非 basename)，差别只在第二条多出 `\bbak\b`(独立单词 bak)与 `_backup` 两个分支，在档 C 上仅多命中 2 行/10,061 B(两条 t3_V7_backup_orphan*.txt)，其余分支(含 backup/)逐字相同；两条之间不存在大小写差异，也不存在全路径/basename 差异
Q2 | 审计员正则(band_c_wide.py:21 原文、re.I、rel 全路径) -> 375 行 / 184,618,279 B ; rollback_extra 正则(:19 原文、re.I、rel 全路径) -> 377 行 / 184,628,340 B ; 我写的第三条 `re.compile(r"(_before_|\.before|before_|_bak|backup/)(?!AFTER)", re.I)`(在 band 原文后加负向前瞻，排除 BEFORE_AFTER 对照记录，仍施于 rel 全路径) -> 332 行 / 184,504,398 B；三数均由 files_tier_C.tsv 的 rel 列逐行 search + sum(bytes) 复算
Q3 | Lead 文中规则 `(_before_|\.before|before_|_bak|backup/)` 大小写不敏感、施于 files_tier_C.tsv 的 rel 全路径 -> 375 行 / 184,618,279 B ; 是否 = 375/184,618,279: 是（Lead 的规则与结果自洽、可复算；真正出错的是审计员——R17_R75_T1_AUDITSELF\_probe.ps1:26 用 `[regex]'...'` 构造对象，Options=None 即大小写敏感，丢了 re.I，才得 333；故「两份实现差」不是规则不同，而是一方把 flags 弄丢了）
Q4 | 对称差 = 42 行 / 111,897 B（375 集独有 42 行、333 集独有 0 行，即真子集关系；42 行全部是 `*/BEFORE_AFTER.txt`，均在 re.I 下由 `before_` 分支命中大写 `BEFORE_`，逐行明细见附录 A）; 是否 = 42/111,897: 是（375−333=42，184,618,279−184,506,382=111,897，与 42 行字节求和完全一致）
Q5 | 该写进文档的是: 375 / 184,618,279 B（在文中所写的 re.I 规则下这是正确值；333 是审计员丢 re.I 的实现错误） | 建议表述=<档 C 中命中回滚正则的行 = 375 行 / 184,618,279 B；口径 = 对 `files_tier_C.tsv` 的 `rel` 列（完整相对路径，非 basename）以 `re.compile(r"(_before_|\.before|before_|_bak|backup/)", re.I)` 做 `search()`（re.I = 大小写不敏感）；审计员的 333 行系同一正则去掉 re.I、按 PowerShell `[regex]` 默认大小写敏感所致，少计 42 个 `BEFORE_AFTER.txt` / 111,897 B。>
OVERALL | 42 行差异的根因不是正则文本而是 flags：审计员 `_probe.ps1:26` 用 PowerShell `[regex]'...'` 构造正则（Options=None，大小写敏感），丢了 band_c_wide.py:21 的 re.I，于是 42 个 BEFORE_AFTER.txt（靠 `before_` 分支仅在 re.I 下命中 `BEFORE_`）被漏计；两条正则文本本身对档 C 的实际差别只有 rollback_extra 多出的 `_backup` 分支（2 行 / 10,061 B），与大小写/backup 段写法/全路径-vs-basename 均无关——因此 375 对、333 错，文中那个 42 行 / 111,897 B 的差额本身是准的，只是当时没定位到根因。

---

## 附录 A · 对称差逐行清单（375 集独有 = 333 集独有 0 行）

全部 42 行命中片段均为 `before_` 分支（re.I 下匹配 `BEFORE_`），路径来自 `files_tier_C.tsv` 的 `rel` 列，字节来自 `bytes` 列。格式：`字节 | 命中片段 | rel`。

```
1276 | before_(BEFORE_) | next_re_20261117_r14/MERGE_M58/BEFORE_AFTER.txt
1708 | before_(BEFORE_) | next_re_20261117_r14/MERGE_M59/BEFORE_AFTER.txt
953 | before_(BEFORE_) | next_re_20261117_r14/MERGE_M60/BEFORE_AFTER.txt
904 | before_(BEFORE_) | next_re_20261117_r14/MERGE_M61/BEFORE_AFTER.txt
1064 | before_(BEFORE_) | next_re_20261117_r14/MERGE_M63/BEFORE_AFTER.txt
773 | before_(BEFORE_) | next_re_20261117_r14/MERGE_M64/BEFORE_AFTER.txt
1127 | before_(BEFORE_) | next_re_20261117_r14/MERGE_M65/BEFORE_AFTER.txt
1209 | before_(BEFORE_) | next_re_20261117_r14/MERGE_M66/BEFORE_AFTER.txt
1304 | before_(BEFORE_) | next_re_20261117_r14/MERGE_M67/BEFORE_AFTER.txt
1412 | before_(BEFORE_) | next_re_20261117_r14/MERGE_M68/BEFORE_AFTER.txt
895 | before_(BEFORE_) | next_re_20261117_r14/MERGE_M69/BEFORE_AFTER.txt
1759 | before_(BEFORE_) | next_re_20261117_r14/MERGE_M70/BEFORE_AFTER.txt
1775 | before_(BEFORE_) | next_re_20261117_r14/MERGE_M71/BEFORE_AFTER.txt
1794 | before_(BEFORE_) | next_re_20261117_r14/MERGE_M72/BEFORE_AFTER.txt
1941 | before_(BEFORE_) | next_re_20261117_r14/MERGE_M73/BEFORE_AFTER.txt
1473 | before_(BEFORE_) | next_re_20261117_r14/MERGE_M74/BEFORE_AFTER.txt
1492 | before_(BEFORE_) | next_re_20261117_r14/MERGE_M75/BEFORE_AFTER.txt
1491 | before_(BEFORE_) | next_re_20261117_r14/MERGE_M76/BEFORE_AFTER.txt
1660 | before_(BEFORE_) | next_re_20261117_r14/MERGE_M77/BEFORE_AFTER.txt
2446 | before_(BEFORE_) | next_re_20261117_r14/MERGE_M78/BEFORE_AFTER.txt
2359 | before_(BEFORE_) | next_re_20261117_r14/MERGE_M79/BEFORE_AFTER.txt
2507 | before_(BEFORE_) | next_re_20261117_r14/MERGE_M80/BEFORE_AFTER.txt
1405 | before_(BEFORE_) | next_re_20261117_r14/MERGE_M81/BEFORE_AFTER.txt
3013 | before_(BEFORE_) | next_re_20261117_r14/MERGE_M82/BEFORE_AFTER.txt
2901 | before_(BEFORE_) | next_re_20261117_r14/MERGE_M83/BEFORE_AFTER.txt
930 | before_(BEFORE_) | next_re_20261117_r14/PANEL_L1_DOC/BEFORE_AFTER.txt
5634 | before_(BEFORE_) | next_re_20261117_r14/R16_COMMON_D47/BEFORE_AFTER.txt
2213 | before_(BEFORE_) | next_re_20261117_r14/R16_COMMON_RENUM/BEFORE_AFTER.txt
4591 | before_(BEFORE_) | next_re_20261117_r14/R16_FIX_PANEL_M86/BEFORE_AFTER.txt
4870 | before_(BEFORE_) | next_re_20261117_r14/R16_MERGE_EVID9/BEFORE_AFTER.txt
11025 | before_(BEFORE_) | next_re_20261117_r14/R16_MERGE_F1_B1/BEFORE_AFTER.txt
2085 | before_(BEFORE_) | next_re_20261117_r14/R16_MERGE_F1_B2/BEFORE_AFTER.txt
1649 | before_(BEFORE_) | next_re_20261117_r14/R16_MERGE_F1_B3/BEFORE_AFTER.txt
2061 | before_(BEFORE_) | next_re_20261117_r14/R16_MERGE_F1_B4/BEFORE_AFTER.txt
4431 | before_(BEFORE_) | next_re_20261117_r14/R16_MERGE_F1_B5/BEFORE_AFTER.txt
2135 | before_(BEFORE_) | next_re_20261117_r14/R16_MERGE_SLOTN_B1/BEFORE_AFTER.txt
1846 | before_(BEFORE_) | next_re_20261117_r14/R16_MERGE_SLOTN_B2/BEFORE_AFTER.txt
25084 | before_(BEFORE_) | next_re_20261117_r14/R16_MERGE_SLOTN_B3/BEFORE_AFTER.txt
632 | before_(BEFORE_) | next_re_20261117_r14/_hygiene/H34/BEFORE_AFTER.txt
690 | before_(BEFORE_) | next_re_20261117_r14/_hygiene/H34/pass2/BEFORE_AFTER.txt
690 | before_(BEFORE_) | next_re_20261117_r14/_hygiene/H34/pass3/BEFORE_AFTER.txt
690 | before_(BEFORE_) | next_re_20261117_r14/_hygiene/H34/pass4/BEFORE_AFTER.txt
```
合计 42 行 / 111,897 B。

## 附录 B · 复算矩阵（全部来自同两份清单）

| 口径 | 文件 | 行数 | 字节 |
|---|---|---|---|
| band(`:21`, re.I) | files_tier_C.tsv | 375 | 184,618,279 |
| band(`:21`, re.I, 再排 `*_out.txt`) | files_tier_C.tsv | 375 | 184,618,279（档 C 内无 `*_out.txt`） |
| band(`:21`, **大小写敏感**) | files_tier_C.tsv | **333** | **184,506,382** |
| extra(`:19`, re.I) | files_tier_C.tsv | 377 | 184,628,340 |
| extra(`:19`, 大小写敏感) | files_tier_C.tsv | 335 | 184,516,443 |
| band(`:21`, re.I) | files_tier_A_snap2.tsv | 384 | 258,794,083（= F24 脚注的 384/258,794,083） |
| band(`:21`, 大小写敏感) | files_tier_A_snap2.tsv | **342** | **258,682,186** |
| extra(`:19`, re.I) | files_tier_A_snap2.tsv | 386 | 258,804,144（= rollback_extra.json 的 backup_like） |
| extra(`:19`, 大小写敏感) | files_tier_A_snap2.tsv | 344 | 258,692,247 |
| A−C 差集 | — | 1,376 | 289,221,428 |
| A 命中 band 但不在 C（全为 `*_out.txt`） | — | 9 | 74,175,804 |

闭合校验：
- re.I：384 − 9 = 375；258,794,083 − 74,175,804 = 184,618,279 ✓
- 大小写敏感：342 − 9 = 333；258,682,186 − 74,175,804 = 184,506,382 ✓
- 两套之差：384 − 342 = 42；258,794,083 − 258,682,186 = 111,897（与档 C 层差额完全相同）✓

## 附录 C · 附带发现：审计员把 342 的出处标错了

R17_R75_T1_AUDITSELF/REPORT.md:152、:315 把「342 行 / 258,682,186 B」标成 `rollback_extra.py:19` 的宽正则结果。实测该数 = **band_c_wide.py:21 正则在 files_tier_A_snap2.tsv 上大小写敏感**的结果；宽正则在档 A 上是 386 / 258,804,144 B（附录 B）。同样，F24 脚注的 384 / 258,794,083 B = band 正则在档 A 上 re.I 的结果。这一处误标不改变 Q4 的差额（42/111,897 在档 A 与档 C 两个层面都相同），但说明审计员当时的正则/flags 标注整体不可靠。

## 附录 D · 复现方式（只读）

脚本：`R17_R78_T2_REGEXDIFF/analyze.py`、`analyze2.py`、`analyze3.py`、`analyze4.py`。
输入：`R17_R72_T1_CLEANSCALE/files_tier_C.tsv`（列 rel/ext/bytes/mtime_ns/selfkind，23,347 行 / 1,300,742,927 B）与 `files_tier_A_snap2.tsv`（24,723 行 / 1,589,964,358 B）。
PowerShell 验证：`[regex]'(...)'.Options` = None（大小写敏感），而 `[regex]::new('...', 'IgnoreCase')` 命中 `BEFORE_AFTER.txt`；`-match` 运算符默认大小写不敏感（与 `.IsMatch()` 不同）——审计员用的是 `.IsMatch()`。
未运行 mev675.py；未写 lead\ 下任何既有目录。
