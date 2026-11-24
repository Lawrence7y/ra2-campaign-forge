# R44-T4-AUDIT32 · 独立审计报告

被审对象：`R14_COMMON.md` §2.30/§2.31/§2.32 与 `R17_R80_FACTINDEX_V520\FACT_INDEX.tsv` 的 `F24`（statement/limitations）。
纪律：只读；三清单直接求和与集合运算，未重跑全树；结论附逐字引用 + 文件/行/键。

---

## 逐条结论（严格按卡第四节格式，中文，纯文本）

D1 | 成立 | 三数和=24,723/1,589,964,358（C′ 18,712/1,363,708,720 + 被排 4,769/179,570,859 + 无法判定 1,242/46,684,779；直接对三 TSV 逐行 sum：CP=1,363,708,720、EXCL=179,570,859、UNDEC=46,684,779、A=1,589,964,358，行数 18,712+4,769+1,242=24,723）; 集合不重不漏: 是（以 rel 列做 Ordinal 集合：三表各 0 重复；C′∩EXCL=0、C′∩UNDEC=0、EXCL∩UNDEC=0；并集 24,723 与档 A 双向差集均为 0）

D2 | 不成立（求和相等不能排除互换错，故「恒等式钉住分类正确性」的自我证明说法不成立） | 互换错构造=<有: 等字节互换——把 C′ 件 `next_re_20261112_r10/W110_crash/work/w94_design_hunt_near.json`（237,273 B，family=F99_other，why=P0_未被排除判据命中）与 EXCL 件 `next_re_20261112_r10/W110_crash/out/_archive_probe/trip_rof_probe_r1/installed_inputs/w94_design_rof_probe.json`（237,273 B，family=F08_probe_check，label=EXCL，why=E3_元记录目录）互换归属。因两者字节完全相同，互换后 C′ 仍 18,712/1,363,708,720、被排仍 4,769/179,570,859，三数和仍精确 = 24,723/1,589,964,358，恒等式照样闭合，但两件已被错分。此类等字节候选盘上有 4,124 对（跨 family 474 对），非孤例。一般不等字节互换亦成立：X=`re_chain_synthesis_20261111/baseline_backup/re_orphan_owners_20261110/_oo_disasm_out.txt`（73,899,177 B，在 C′）↔ Y=`a_dim_reduced_20261108/_ar_out.txt`（24,614 B，在 EXCL），互换后 C′ 字节变 1,289,834,157、被排变 253,445,422，但总和仍 1,589,964,358、件数不变。> ；理由：该恒等式只检验「三桶是否构成档 A 的一个划分（不重不漏）」，不检验「每件是否被分进正确的桶」——互换错既不产生漏项也不产生重项，恰能通过恒等式。§2.32:2873-2874 逐字「这条恒等式是 C′ 的自我证明：一个分类若有漏项或重项，三分类之和就不可能恰好等于档 A」「分类的正确性被一条加法约束住了」——把「划分的算术闭合」误当成「分类的语义正确」。

D3 | 不够 | 缺的限定=<④「C′ 判据含内容级判断（前 8 KiB 取行首 VA 比例、横幅特征等），换人重跑可能不一致；本轮只复算清单求和与分类恒等式，未复算其对每一件的分类理由」——此条 §2.32:2917-2918 未取得①写了，但 F24 limitations 未写；此缺项正中要害：F24 把 C′ 标为「我独立复算」，读者会误以为分类正确性已被核。> ; F24 limitations 里有「内容级判据」这条吗: 无（F24 COL5 limitations 逐字只列三条限定「被测对象优先口径 / 1,242 件 46,684,779 B 冲突件单列 / 对 EVIDENCE 敏感且非下界」，另有 selfkind/漂移/旧数等口径句，均无内容级判据或换人重跑不一致字样）

D4 | 成立（但须改写理由；不是「一边确定」而是「不确定桶被逐件定位」） | 理由=<区分区分本身成立：旧区间 [23,014,23,419] 文件 / [1,116,236,545,1,301,772,579] B（§2.30:2788-2789、§2.31:2842、2856）的两端各依赖一条未审计判据，宽度不可指名，确属「把不确定藏进方括号」；而 C′ 区间 18,712~19,954 / 1,363,708,720~1,410,393,499 的宽度恰是 1,242 件逐件列出、带 family/why/label 的 `files_excluded_prime.tsv` 桶（§2.32:2891-2892），不确定被定位、可逐件复核。但 §2.32:2908-2913 的理由表述有自伤：它称「下界 = C′（确定分类）」「一条确定判据」，而同节 2917-2918 又承认 C′ 含内容级判据、换人重跑可能不一致、本轮未复算逐件分类理由——两端其实仍依赖未经复核的判据。⇒ 转向可取，但正确理由是「那 1,242 件被显式单列并可逐件审计」，不是「一边确定、一边是桶」；应按此改写并补上 D3 的限定，否则「拒用旧区间」的理由并没有真正被推翻，只是被换了个说法绕过。>

D5 | 矛盾/过时 3 处: ①F24 statement 逐字「我独立复算：C′ + 被排 6,011 / 226,255,638 B = 24,723 / 1,589,964,358 B，与档 A 精确闭合」——把 1,242 件无法判定并进了「被排」（6,011=4,769+1,242；226,255,638=179,570,859+46,684,779），与同条 limitation②逐字「1,242 件...单列、既不计入 C′ 也不算已排除」及 §2.32:2870「被排（EXCL）4,769」自相矛盾：既然不算已排除，就不该计入「被排 6,011」；②F24 limitations 逐字「漂移分解只成立于 11:55→12:31 这一对快照、沿用未审计的 selfkind 口径」——「C′ 用的不是 selfkind」属实，故该句对「漂移分解」这一特定对象仍是准确的，并未因 C′ 引入而失效；但它仍是不准确/过时表述：漂移分解（R17_R75_T2_DRIFT/REPORT.md:39、78-84）确用 `files_tier_A_snap2.tsv` 的 selfkind 列，而 §2.31:2857 与 F24 statement 已判档 C 的 selfkind 语义不自洽（72 个 *_report.md 被排而 208 个裸 REPORT.md 被留、*_out.json 372 / stdout 789 未覆盖），仍写「未审计」沿用了 R75 时点口径；更实质的是 F24 现在同时主推 C′（内容判据）与这条 selfkind 口径分解，却未声明两者不是同一判据、不可互相换算；③「旧档 C 已被 C′ 取代、不得再引用」与「旧档 C 的 375 与 333 两数分别对应 re.I 与无 re.I」并存：两数并非严格矛盾（375/333 是脚注错标诊断，不是档 C 的引用值），但 limitations 未把「不得引用档 C 的值」与「375/333 只是说明脚注为何错、本身也不得当可引数」分开写，读者易把 375/333 当成仍可引用的数；§2.30:2761 与 §2.31:2811 本已把两者分清（值可复现/脚注改双 flags），v5.20 压缩成一句后丢了这层区分。

D6 | 不准 | 先例=<找到: R16_EVID9/REPORT.md:81、87（早于 R17）：执行员逐字「据『宁可少定、不可凑数』的纪律，我把这 6 行判为 UNDECIDED，并把上述观察完整记录在此，供 Lead/合并员决策，不擅自硬选」「6 行 UNDECIDED 不计入」——正是执行员主动把判不了做成单列桶、不硬塞两边；AUDIT_ATEXIT/PROGRESS.md:37-41「D 无法判定 332 22.9%」并拆 D-1=23 / D-2=309 子桶，CARD.md:25 定义「D 无法判定：给出原因（fail-closed，不许猜）」；CONFLICT_CLASS2/SUMMARY.md:12「C6 记录残缺(缺name行)无法判定 16 6.4%」；R17_R75_T2_DRIFT/REPORT.md Q2/Q3/Q4 三表均列「无法判定 0/0」行（0 值但桶已显式设立）；AUDIT_SEM_SELF/CARD.md:30「P3 无法判定：fail-closed，写清原因」。>；§2.32:2901 逐字「这是本项目第一次出现执行员主动把「判不了」做成一个单列桶」为错。

OVERALL | §2.32：把 2873-2874 的「自我证明/钉住分类正确性」降级为「只证明三桶构成档 A 的划分，不证明逐件归类正确」并补 D2 互换错构造，把 2901「第一次」改为有先例，把 2908-2913 转向理由从「一边确定」改写为「不确定桶逐件单列可审计」；F24 v5.20：把 ④内容级判据/换人重跑不一致补进 limitations（现三条不够），把 statement 的「被排 6,011」拆回 4,769 + 1,242 与 limitation②一致，并把「沿用未审计 selfkind 口径」加上「与 C′ 内容判据不同、不可换算」的限定。

---

## 证据底稿（逐字引用 + 文件/行/键）

### 来源文件与行
- `lead\next_re_20261117_r14\R14_COMMON.md`：§2.30 lines 2732-2791；§2.31 lines 2792-2859；§2.32 lines 2860-2920。
- `lead\next_re_20261117_r14\R17_R80_FACTINDEX_V520\FACT_INDEX.tsv`：F24 在 line 25（5 列：fact_id/statement/grade/evidence_paths/limitations）。
- 三清单：`R17_R78_T1_RECLASS\files_tier_Cprime.tsv`（18,712 行，列 rel/ext/bytes/mtime_ns/family/why）；`R17_R78_T1_RECLASS\files_excluded_prime.tsv`（6,011 行，列 rel/.../family/label/why/layer/in_tier_C_old，label∈{EXCL 4,769, UNDECIDED 1,242}）；`R17_R72_T1_CLEANSCALE\files_tier_A_snap2.tsv`（24,723 行，列 rel/ext/bytes/mtime_ns/selfkind）。

### D1 实测输出（直接求和 + Ordinal 集合）
```
CP rows=18712  EX rows=6011  A rows=24723
EX labels: EXCL=4769, UNDECIDED=1242
CP  bytes=1363708720 ; EXCL bytes=179570859 ; UNDEC bytes=46684779
A   bytes=1589964358 ; CP+EXCL+UNDEC count=24723 bytes=1589964358
dup rel within CP/EXCL/UNDEC/A = 0/0/0/0
|setCP|=18712 |setEX|=4769 |setUN|=1242 |setA|=24723
CP∩EXCL=0  CP∩UNDEC=0  EXCL∩UNDEC=0  |union|=24723
in union but not in A = 0 ; in A but not in union = 0
```

### D2 构造佐证
- 等字节对：`w94_design_hunt_near.json`（C′，237,273 B，why=P0_未被排除判据命中）↔ `w94_design_rof_probe.json`（EXCL，237,273 B，label=EXCL，why=E3_元记录目录）。盘上 C′↔EXCL 等字节候选 4,124 对，跨 family 474 对。
- 不等字节对：`_oo_disasm_out.txt`（C′，73,899,177 B，对应 §2.32:2880-2882 的「捞回真反汇编」）↔ `_ar_out.txt`（EXCL，24,614 B）；互换后 C′=1,289,834,157 B、EXCL=253,445,422 B，总和仍 1,589,964,358 B。

### D5 逐字引用
- F24 statement（COL1）：「我独立复算：C′ + 被排 6,011 / 226,255,638 B = 24,723 / 1,589,964,358 B，与档 A 精确闭合」；「引用 C′ 必须同引三条限定：① ... ② 口径外有 1,242 件 / 46,684,779 B 落在 EVIDENCE\ 内的冲突件 ... 单列、既不计入 C′ 也不算已排除 ... ③ 它对 EVIDENCE 族最敏感 ... 不可写成『不含任何自身产物的下界』」；「其 selfkind 判据的语义自洽性被判为不成立」；「旧档 C（23,347 / 1,300,742,927 B）已被 C′ 取代、不再引用」。
- F24 limitations（COL5）：「沿用未审计的 selfkind 口径，不可移用于历史漂移」；「旧档 C 已被 C′ 取代、不得再引用；旧档 C 的 375 与 333 两数分别对应 re.I 与无 re.I（差 42 行 / 111,897 B，全为 BEFORE_AFTER.txt）」；「引用 C′ 必须同引三条限定（被测对象优先口径 / 1,242 件 46,684,779 B 冲突件单列 / 对 EVIDENCE 敏感且非下界）」。
- R17_R75_T2_DRIFT/REPORT.md:39「按 files_tier_A_snap2.tsv 的 selfkind 列优先，空值再按文件名形态判」；:81「selfkind 未审计：§2.28『未取得③』明示档 C 的判据『尚未经第二人审计』」；:84「selfkind 口径不自洽：AUDIT_REPORT.md 命中 C5_report_md 算自身产物，裸 REPORT.md 却是空 selfkind」。
- R14_COMMON.md:2857「档 C 的 selfkind 判据语义自洽性仍未修好（208 vs 72、*_out.json 372 个...）——这是 R43-T1 的任务」；:2917-2918 未取得①（见 D3）。

### D6 先例逐字
- R16_EVID9/REPORT.md:81、87（见上）；R16_AUDIT_EVID9/VERDICT.md:98「这 6 行恰是卡面的 6 行 UNDECIDED」。
- AUDIT_ATEXIT/CARD.md:25、PROGRESS.md:37-41（见上）；BOARD_ARCHIVE.md:1701「| D 无法判定 | 332 | 22.9% | 见下 D 桶拆分 |」。
- CONFLICT_CLASS2/SUMMARY.md:12；AUDIT_SEM_SELF/CARD.md:30；AUDIT_PROVED_UNNAMED/CARD.md:24「P3：无法判定（fail-closed，写清原因）」。
- R17_R75_T2_DRIFT/REPORT.md Q2/Q3/Q4「无法判定 | 0 | 0」。

### 未取得
- F24 的 statement/limitations 全文已取得（TSV line 25 完整 5 列）。
- 三清单已取得并完成求和/集合运算。
- 未重跑全树、未改任何被审文件；仅写本目录。
