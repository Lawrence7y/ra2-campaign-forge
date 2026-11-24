# Q1 判定表（同文副本；主文见 REPORT.md）

判定口径：原 24 条 `exists` 的产物里，是否存在「稳定、可机械提取、且能代表该纪律结论」的量。
正则不含字面空格（门禁按首空格切 `✓(...)` 注释），故用 `\s` 代替空格；命中数为实测 `re.findall` 计数。

| 纪律号 | 产物 | 可提取的量 | 提取式（确切正则） | 能升级? | 若否为什么 |
|---|---|---|---|---|---|
| 1 | `R14_COMMON.md` | — | — | 否 | 383 KB 规则正文，无可单独代表结论的稳定计数/断言行。**未取得** |
| 2 | `R14_COMMON.md` | 候选：`lea`+`中介` 应 0 命中 | 候选 `notgrep=lea.{0,20}中介` | 否 | 实测 4 命中（纪律自述含该二词），无判别力 → 回退 `exists`。**未取得** |
| 3 | `R17_R61_FACTINDEX_V58\anchor_check.txt` | 未核验单列为 0（L16） | `grep=池未加载\(未核验\)\s+0` | 是 | — |
| 4 | 同上 | 节号体例通过 15（L15） | `grep=节号体例通过\s+15` | 是 | — |
| 5 | `R17_R64_ADEQUACY2\lead_recheck2.tsv` | 「复合锚是并集」逐字原则（L5） | `grep=复合条目的锚是并集` | 是 | — |
| 6 | 同上 | F28「在锚里→不在锚里」误报（L4） | `grep=审计把「在锚里」说成「不在锚里」` | 是 | — |
| 7 | `R17_R62_ADEQUACY\lead_recheck.tsv` | F21 `REFUTED-OVERSTRICT`（L7） | `grep=REFUTED-OVERSTRICT` | 是 | — |
| 8 | `R17_R66_FACTINDEX_V511\CHANGES.md` | 列间未同步结论（L125） | `grep=列与列之间没有同步` | 是 | — |
| 9 | `R14_COMMON.md` | — | — | 否 | 规则正文；「分命名空间/0 误报」仅见纪律自述，无独立落盘结论量。**未取得** |
| 10 | 同上 CHANGES.md | 可作不变量白名单（L98） | `grep=当不变量用的只有` | 是 | — |
| 11 | `_r38\checkC3_report.md` | 控制组总判定 PASS（L19） | `grep=控制组总判定：\*\*PASS` | 是 | — |
| 12 | 同上 | 闭集合声明（L3） | `grep=闭集合声明（纪律\s*12①）` | 是 | — |
| 13 | `_r38\checkC3.py` | 四子检查控制组（L181） | `grep=控制组（四个子检查全都要）` | 是 | — |
| 14 | 同上 | FAIL 产物文件名（L264） | `grep=checkC3_report_FAIL\.md` | 是 | — |
| 15 | `_r38\settle_iat.py` | 三方分布各一次（L78–80） | `grepcount=所在节分布=3` | 是 | — |
| 16 | `R17_R72_T1_CLEANSCALE\REPORT.md` | 三文件「相同」（L281–283） | `grepcount=\*\*相同\*\*=3` | 是 | — |
| 17 | `R16_MEASURE_EVID675\mev675.py` | `out_excl`（L254、L261） | `grepcount=out_excl=2` | 是 | — |
| 18 | `R17_R70_T1_REPRO\REPORT.md` | 历史时刻无产物（L140） | `grep=12:07.*无产物` | 是 | — |
| 19 | `R17_R75_T2_DRIFT\REPORT.md` | 逐字节闭合 | `grep=逐字节闭合` | 是 | — |
| 20 | `check_disc.py` | 锚称禁不可见字符断言，产物仅有 CR 检查（L46） | — | 否 | 所述 U+200B 断言**未取得**，不能编造；保留 `exists` |
| 21 | `R17_R78_T4_AUDIT30\REPORT.md` | 2×2 溯源表（附录 A） | `grep=2×2\s*溯源表` | 是 | — |
| 23 | `R17_R78_T1_RECLASS\REPORT.md` | 「为什么该在一边」（Q1 判据表） | `grep=为什么该在一边` | 是 | — |
| 24 | `R17_R78_T4_AUDIT30\REPORT.md` | 附注性限定语（C3） | `grep=附注性限定语` | 是 | — |
| 25 | `R17_R78_T2_REGEXDIFF\REPORT.md` | 审计员丢 re.I（OVERALL） | `grep=丢\s*re\.I` | 是 | — |

能升级 20 / 不能 4（1,2,9,20）。纪律 22/26/27/28 原为 `rows=N`，不在 24 条 `exists` 内，不动。
