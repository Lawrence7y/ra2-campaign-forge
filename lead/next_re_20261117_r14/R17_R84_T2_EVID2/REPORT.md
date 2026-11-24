# R45-T2-EVID2 · 收敛 EVIDENCE 那 266 件平票 + 定 _audit 归属

执行员：t2-evid2　日期：2026-11-22（本地）
写目标：lead\next_re_20261117_r14\R17_R84_T2_EVID2\（唯一写目标）
只读 lead\；未运行 mev675.py；未写 lead\ 下任何既有目录。

---

## 一 · 六行交付（严格照卡 §四格式）

```
Q1 | 266 件冲突类型分布: 名过内象=6件/4084B ; 名象内过=6件/58168B ; 两者都弱=254件/4902957B（合计266件/4965209B ; 源=R17_R78_T1_RECLASS\files_excluded_prime.tsv 列 rel/label/bytes 取1242 − R17_R81_T2_EVID\_verdicts.tsv 列 verdict 已裁976 ; 脚本=analyze.py/explore_q1.py） | 主因=绝大多数(254/266=95.5%)并非真正的名-内容对立，而是内容信号本身弱：262/266 件前8KiB行首VA=0、无强过程帧、O/P 双低而平票；名字与内容真正反向的仅12件（6+6）。
Q2 | 40 件抽样（分层 名过内象10/名象内过6/两者都弱24 ; 前8KiB ; 未看任何 label/why/verdict）: 对象=29 / 过程=10 / 判不了=1 ; 摘要=行首VA几乎全为0%(262/266整体如此)，对象件多靠「地址与字节/虚表/反汇编/字节diff」语义判定而非VA行 ; 明细40行见下方附录与 q2_sample40_features.txt（VA%/包装/中文/首行80字）+ q2_sample40_verdicts.txt（逐件理由）。
Q3 | 同目录多数派可用: 是（有条件） | 规则=同一 EVIDENCE 父目录内「已裁件」(对象抄本+过程输出)≥3 且同向占比≥75% ⇒ 该目录内的平票件随多数派裁定 ; 留一法校验=663/688=96.4%（只统计触发规则的目录）; 266 件覆盖率=114件/1995960B（余152件/2969249B继续单列 ; 更严的100%一致口径=80件）; 源=R17_R81_T2_EVID\_verdicts.tsv 列 rel/verdict + _undead_evid.tsv 列 bytes ; 脚本=q3_final.py。
Q4 | _audit 写域约定 3 处: a-S15S16-3B2.md:42:「- `S15S16_3B2\_audit\VERDICT.md`：逐行一节，含上述四件事的地址与字节 + 最终判定」 ; a-SEMFIX-BATCH.md:48:「- `<批次目录>\_audit\VERDICT.md`：逐行一节，含上述五件事的地址与字节 + 判定」 ; a-S09-KPROVED8.md:51:「- 每行一节：entry、你的 PASS / FAIL 判定、上述 5 个核查点的地址与字节、一句结论。」 ; C′ 中 _audit=540件/67129511B（按目录段「_audit」计 ; 若按路径含子串「audit」则868件/74089751B，多出的是 c07_gate_audit 等卡名非 _audit 目录）, P1a 占=527件/66864593B=97.59%(件)/99.61%(字节) | 结论=必须逐件判。
Q5 | 正控: 法1(Python posctrl_py.py)=Q1 1242−976=266(direct/ reason_tie 亦=266) ; Q4 _audit 540件/67129511B(P1a 527件/66864593B) ; 法2(PowerShell posctrl_ps.ps1)=Q1 266 ; Q4 540件/67129511B(P1a 527件) | 一致。
OVERALL | 两块都能再收一档、但都不能整体归边：EVIDENCE 的266件里真冲突仅12件、254件是内容信号弱，用「同目录多数派」可再裁114件（留一法96.4%），未决可从266降到152；_audit 是「地址与字节+判定」的混合审计写域，C′ 内97.6%件P1a对象抄本（应留）、但同目录段排除集另有1111件过程/元记录（应排），故按内容逐件判、不整体划到过程侧。
```

---

## 二 · 源与口径（纪律 1/3/4）

- **266 件的来源**：R17_R78_T1_RECLASS\files_excluded_prime.tsv（6011 行，列 rel/ext/bytes/label/why/family）。取 label=UNDECIDED 且 rel 含 EVIDENCE（大小写不敏感）=1242 件（含 1 件小写 evidence 路径 `next_re_20261112_r03/W86_render_channel/evidence/recon_stdout.txt`）。上一轮已裁 976 件见 R17_R81_T2_EVID\_verdicts.tsv 列 verdict∈{对象抄本(732), 过程输出(244)}；1242−976=266，与该文件 verdict=无法判定/reason=tie 的 266 行集合逐一相同。266 件合计 4,965,209 B。
- **Q1 冲突类型判据**（名字信号只看 basename 词、内容倾向只看 O/P 行计数，均不使用 label/why）：
  - 名字说过程 = basename 含 stdout/stderr/_out/report/log/selftest/check/probe/status/summary/verdict/exit/cmd/gen_/build/validat/reject/perf 等 ; 名字说对象 = 含 row_/disasm/bytes/addr/site/table/vtable/struct/insn/dump/map/ref/fact/index/rtti 等 ; 两类皆含或皆不含 = 弱。
  - 内容倾向 = O>P 记对象、P>O 记过程、O==P 记平（O/P 为 R17_R81_T2_EVID\judge_q4_v2.py 在前8KiB 统计的"对象信号行/过程信号行"计数）。
  - 名过内象 = 名字过程 ∧ 内容对象 ; 名象内过 = 名字对象 ∧ 内容过程 ; 其余 = 两者都弱。
  - 交叉表（件/字节）：名过×内象 6/4084 ; 名过×内过程 14/199336 ; 名过×平 28/35795 ; 名对象×内对象 74/304475 ; 名对象×内过程 6/58168 ; 名对象×平 60/2115301 ; 名弱×内对象 19/971769 ; 名弱×内过程 10/120896 ; 名弱×平 49/1155385。
- **Q2 抽样**：40 件，按 Q1 三类配额 10/6/24，每类内按 rel 字典序等距取；对歧义件实读前 1500 B 佐证。全程未读任何既有 label/why/verdict 作判据。判定按卡 §一写域约定：记被测对象（地址/字节/虚表/反汇编/字节diff/hash 等）=对象抄本；记测量过程（RUN_ID/横幅/时间戳/selftest 断言/perf/实验清单/构建日志/统计命中率）=过程输出；两者相当=判不了。
- **Q3 同目录多数派**：目录=rel 的父目录（多为 .../EVIDENCE）。分母只用已裁件（对象+过程），与卡例"8 件里 6 件对象抄本 ⇒ 其余 2 件也算对象"同口径。留一法（隐藏一件已裁件的 verdict、用同目录其余已裁件多数派回测）在触发规则的目录上 663/688=96.4%；全量已裁件口径 784/919=85.3%。
- **Q4 _audit 统计**：R17_R78_T1_RECLASS\files_tier_Cprime.tsv（C′，18712 行/1,363,708,720 B）。按 rel 路径**目录段**严格等于 `_audit` 计 540 件/67,129,511 B；P1a = why 前缀 `P1a_对象抄本`（内容有地址，见上一轮 R17_R78_T1_RECLASS\REPORT.md 判据表）=527 件/66,864,593 B。按子串 "audit" 宽松计 868 件/74,089,751 B，多出的 328 件是 c07_gate_audit、_lead_audit、dlc_capability_audit 等**卡名/目录名**含 audit 但非 `_audit` 目录（见 find 脚本）。
- **Q4 结论依据**：三处写域约定均指向 `_audit\VERDICT.md` = "逐行一节，含…地址与字节 + 判定"，即审计员自留的"对象事实 + 过程判定"混合域（与 EVIDENCE 同类）。事实佐证：C′ 内 540 件 97.6%(件)/99.6%(字节) 是 P1a 带地址对象抄本（应留），但同口径排除集 files_excluded_prime.tsv 里另有 1111 件 `_audit` 被判过程/元记录（EXCL 840：E3_元记录目录 567、E1_工具流出物 189、E2_包壳脚本流出物 84 等 ; UNDECIDED 271）。故不是整体过程区也不是整体对象区，须逐件判。
- **Q5 正控**：两实现互不复用代码——法1 Python csv.DictReader，法2 PowerShell 逐行 Split；对 Q1 的 266 与 Q4 的 540 件/67,129,511 B 各项完全一致。

---

## 三 · Q2 40 件抽样明细（对应六行第 2 行）

| # | 路径 | VA | 包装 | 中文 | 首行原文(截断) | 我判 |
|---|---|---|---|---|---|---|
| 01 | next_re_20261112_r02/W58_menu_review/EVIDENCE/16_export_integrity.stdout.txt | VA=0%(0/5) | 无 | 无 | exported .bin size = 664 | 对象 |
| 02 | next_re_20261112_r07/W97_artmd/EVIDENCE/w97_mixget_stdout.txt | VA=0%(0/2) | 无 | 无 | ra2.mix          ra2.mix/0xA8548FD9/0xF91B2C8B   245,825 B Found | 对象 |
| 03 | next_re_20261116_r12/W155_dispatch/EVIDENCE/scan_dispatch_stdout.log | VA=0%(0/3) | 无 | 无 | funcs=12916 insn_map=1030298 text_bytes=4060045 imagebase=0x4000 | 对象 |
| 04 | next_re_20261117_r14/PROBE_UNNAMED_R2/EVIDENCE/poolstats_out.txt | VA=0%(0/17) | 无 | 有(12行) | IMAGE  = D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe | 过程 |
| 05 | next_re_20261117_r14/W173_layer_add/EVIDENCE/w173_chain_check.txt | VA=0%(0/29) | 有(=====) | 有(18行) | ================================================================ | 对象 |
| 06 | next_re_20261117_r14/W173_layer_add/EVIDENCE/w173_selfaudit.txt | VA=0%(0/13) | 有(=====) | 有(11行) | ================================================================ | 判不了 |
| 07 | next_re_20261117_r14/S08_KPROVED3/_audit/EVIDENCE/s2_rtti_vtables.txt | VA=0%(0/39) | 无 | 无 | distinct COL-anchored vtable bases: 955 | 对象 |
| 08 | next_re_20261117_r14/S10-K2/EVIDENCE/t2_mission_slots.txt | VA=0%(0/119) | 有(=====) | 无 | ===== PRIMARY VTABLES (off=0), recounted ===== | 对象 |
| 09 | next_re_20261117_r14/S11-K2/EVIDENCE/t2_factory_alloc.txt | VA=0%(0/216) | 无 | 无 | === factory ctors found in registration fn: 67 === | 对象 |
| 10 | next_re_20261117_r14/S18-K2/EVIDENCE/event_names.txt | VA=0%(0/48) | 无 | 无 | === event name strings at 0x82091C === | 对象 |
| 11 | next_re_20261117_r14/W175_global8871/EVIDENCE/t1_esi0_rtti_link.txt | VA=0%(0/19) | 无 | 有(10行) | === all writes to [esi+0] in ctor 0x665650..0x667a26 === | 对象 |
| 12 | next_re_20261117_r14/W177-B/EVIDENCE/S0_baseline.txt | VA=0%(0/12) | 无 | 有(8行) | # W177-B · S0 卫生与就绪基线 | 过程 |
| 13 | next_re_20261112_r02/W43_b_line_s3/EVIDENCE/gen_s3_artifacts.stdout.txt | VA=0%(0/21) | 无 | 无 | [assert] W38 guard_decision_table has exactly 21 cells ... PASS | 过程 |
| 14 | next_re_20261112_r02/W68_criterion_discrete_fix/EVIDENCE/concurrent_GLM/gen_counterexamples.stdout.txt | VA=0%(0/27) | 无 | 无 | { | 过程 |
| 15 | next_re_20261112_r10/W109_attach/EVIDENCE/perf.txt | VA=0%(0/35) | 无 | 有(10行) | === cell_sentinel --perf (synthetic 512x512 table, half empty) = | 过程 |
| 16 | next_re_20261116_r12/W165_live/EVIDENCE/per_moving_cost.txt | VA=0%(0/19) | 无 | 有(4行) | #      cpu/frame   moving   cpu/moving  cpu/objects | 过程 |
| 17 | next_re_20261117_r14/NAMED_PUSH_S05_B1/EVIDENCE/ROW_00417CC0.txt | VA=0%(0/26) | 无 | 有(20行) | # ROW 00417CC0  S05  AircraftClass::vslot29 | 对象 |
| 18 | next_re_20261117_r14/NAMED_PUSH_S05_B2/EVIDENCE/ROW_00524D70.txt | VA=0%(0/24) | 无 | 有(19行) | # ROW 00524D70  S05  InfantryTypeClass::slot8 | 对象 |
| 19 | next_re_20261117_r14/NAMED_PUSH_S05_B2/EVIDENCE/ROW_007480B0.txt | VA=0%(0/24) | 无 | 有(19行) | # ROW 007480B0  S05  UnitTypeClass::slot6 | 对象 |
| 20 | next_re_20261117_r14/NAMED_PUSH_S10_B1/EVIDENCE/ROW_004D8560.txt | VA=0%(0/40) | 无 | 有(26行) | # ROW 004D8560  AircraftClass::slot267 | 对象 |
| 21 | next_re_20261117_r14/NAMED_PUSH_S10_B1/EVIDENCE/ROW_00519630.txt | VA=0%(0/82) | 无 | 有(23行) | # ROW 00519630  InfantryClass::slot99 | 对象 |
| 22 | next_re_20261117_r14/NAMED_PUSH_S13_B1/EVIDENCE/ROW_0075E2C0.txt | VA=0%(0/16) | 无 | 有(14行) | # ROW 0075E2C0  S13  WarheadTypeClass::slot6 | 对象 |
| 23 | next_re_20261117_r14/P0_ADJ5/_audit/EVIDENCE/baseline_mine.txt | VA=0%(0/9) | 无 | 无 | card 100 rows: FUNC 83/100 = 83.0% | 过程 |
| 24 | next_re_20261117_r14/S03_C5/_audit/EVIDENCE/dis/00431F10.txt | VA=0%(0/9) | 无 | 无 | # 00431F10  extent=[431F10,431F26)  span=0x16  n_reachable=8  n_ | 对象 |
| 25 | next_re_20261117_r14/S03_C7/EVIDENCE/dis_0047AAB0.txt | VA=0%(0/5) | 无 | 无 | # DISASM entry=0047AAB0 range=[0047AAB0,0047AABD) size=13 n_insn | 对象 |
| 26 | next_re_20261117_r14/S05_KPROVED2/_audit/EVIDENCE/holders_mine.json | VA=0%(0/314) | 无 | 无 | { | 对象 |
| 27 | next_re_20261117_r14/S05_KPROVED3/_audit/EVIDENCE/q9_baseline_mine.json | VA=0%(0/56) | 无 | 无 | { | 对象 |
| 28 | next_re_20261117_r14/S09_KPROVED/_audit/EVIDENCE/ring8_basic.txt | VA=0%(0/82) | 有(=====) | 无 | ===== 004AAE90 ===== | 过程 |
| 29 | next_re_20261117_r14/S09_KPROVED5/_audit/EVIDENCE/ring2_recompute.json | VA=0%(0/463) | 无 | 无 | { | 对象 |
| 30 | next_re_20261117_r14/S09_KPROVED6/_audit/EVIDENCE/S7b_baseline.json | VA=0%(0/45) | 无 | 无 | { | 对象 |
| 31 | next_re_20261117_r14/S09_KPROVED8/EVIDENCE/DETAIL_005566A0.txt | VA=0%(0/42) | 无 | 无 | === 005566A0  name=ControlClass::slot3 ext=[005566A0,005566CA) s | 对象 |
| 32 | next_re_20261117_r14/S10_K5/_audit/EVIDENCE/a9_false_kill_sweep.txt | VA=0%(0/42) | 无 | 有(36行) | S10 rows=528 nonproved=435 | 对象 |
| 33 | next_re_20261117_r14/S10_KPROVED3/EVIDENCE/per_row/004D82B0.txt | VA=0%(0/9) | 无 | 有(1行) | === 004D82B0 FootClass::slot289 | 对象 |
| 34 | next_re_20261117_r14/S13_K8/_audit/EVIDENCE/ring3_audit.json | VA=0%(0/232) | 无 | 无 | { | 对象 |
| 35 | next_re_20261117_r14/S13_PUSH/EVIDENCE/ROW_0075E0C0.txt | VA=0%(0/27) | 无 | 有(22行) | # ROW 0075E0C0  S13  WarheadTypeClass::slot5 | 对象 |
| 36 | next_re_20261117_r14/S21_DIRECT/_audit/EVIDENCE/recs_enriched.json | VA=0%(0/1) | 无 | 有(1行) | [{"entry": "00410A60", "grade": "[已证]", "name": "CampaignClass:: | 对象 |
| 37 | next_re_20261112_r02/W47_baseline_adjudication/EVIDENCE/build_candidates.stdout.txt | VA=0%(0/7) | 无 | 无 | W47 builder: wrote D:\Project\ra2-campaign-forge\lead\next_re_20 | 过程 |
| 38 | next_re_20261112_r02/W54_save_determinism/EVIDENCE/step3_streamdiff.stdout.txt | VA=0%(0/69) | 有(############) | 无 | ################################################################ | 对象 |
| 39 | next_re_20261112_r02/W58_menu_review/EVIDENCE/13_final_check.stdout.txt | VA=0%(0/38) | 无 | 无 | === W58 FINAL FALSIFICATION + BROADER FORM CENSUS === | 过程 |
| 40 | next_re_20261112_r02/W61_third_badge_route/EVIDENCE/dialog_bytes_diff.txt | VA=0%(0/535) | 无 | 无 | # W61 dialog byte diff: RT_DIALOG 148 before/after | 对象 |

逐件判定理由见 q2_sample40_verdicts.txt；原始特征（VA 占比/包装/中文/首行80字）见 q2_sample40_features.txt。

---

## 四 · 产物清单

- 主分析与中间结果：analyze.py、explore_q1.py、find_discrep.py、dump_tie.py、peek_ambig.py、q1_tie_detail.tsv、q1_summary.txt、q3_summary.txt、q3_summary2.txt、q3_final.py、q3_final.txt、q2_verdicts_and_q3b.py、q2_sample40_features.txt、q2_sample40_verdicts.txt、posctrl_py.py、posctrl_ps.ps1、assemble.py、REPORT.md。
- 判不了/未取得：Q2 中 1 件（w173_selfaudit.txt，过程自检与对象地址混合）判不了，已单列计数，未硬塞；本次所有需要的数均取得，无"未取得"项。
