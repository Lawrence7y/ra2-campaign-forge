# PROGRESS.md — N-FIX noinit_t 误剔专项（≤60 行）

目标 `ra2youli\gamemd.exe` SHA-256 `73201CC0…F67476`｜ImageBase 0x400000｜只读。写域仅 `N_FIX\`。
日期 2026-11-17｜状态：**交付完成**，未改任何卡 tsv / COVERAGE / 台账 / gamemd.exe，未 commit。

## 判据（§952 基线已先做）
- 全镜像 816 个 `JMP_THIS(0x…)` 行按前一行分桶：普通签名 **686 (84.1%)**、noinit_t 委托 **99 (12.1%)**、其他 30、普通初始化列表 1 ⇒ 「下一行有 JMP_THIS」**不特异**，是 YRpp 统一样式。
- 收窄为双条件：上一行确为 `: Xxx(noinit_t())` **且**紧邻下一行有 `JMP_THIS(0x…)`。命中 99 实例 / 95 唯一地址。
- C08 已知 9、C09 已知 15 全部在命中集（双向核对），判据与已证缺陷同源。`BASELINE.md` 有完整比例。

## 核心数字（复算：见 work\）
| 项 | 数 | 复算方法 |
|---|---:|---|
| noinit_t 总行数 | 300 | 238 文件逐行 `in 'noinit_t'` |
| 真误剔（有 JMP_THIS 跟随） | 99 实例 / 95 唯一地址 | 双条件正则 |
| 纯空桩（无地址，不提升） | 106 | `explicit __forceinline Xxx(noinit_t)` 后 3 行无 JMP |
| 本轮新增 high 增量 | +34 | C04+7 C05+6 C06+8 C07+13 |
| 十片 high 修正合计 | 4,789 | lead 入账和 4,755 + 34 |

## 逐片结论
| 卡 | 入账 high | 误剔地址 | 本轮增量 | 修正后 |
|---|---:|---:|---:|---:|
| C01 | 96 | 0 | 0 | 96（已具名 high） |
| C02 | 840 | 9 | 0 | 840（`::noinit_t` 已 high，仅错名） |
| C03 | 428 | 6 | 0 | 428（同 C02） |
| C04 | 776 | 7 | **+7** | 783 |
| C05 | 565 | 6 | **+6** | 571 |
| C06 | 382·274 | 8 | **+8** | 390·282 |
| C07 | 559·359 | 13 | **+13** | 572·372 |
| C08 | 417·416 | 9 | 0 | 417（§960 已 +9） |
| C09 | 438 | 15 | 0 | 438（§942 已 +15） |
| C10 | 254 | 0 | 0 | 254 |

## 停机核验（§954）
- lead 入账和 = 4,755；P0-CLOSE = 4,752；差 +3 = C01(96 vs 102 = −6) + C08(417 vs 408 = +9)。非凑数，两处均既有口径差。
- 修正后 4,789 对 P0-CLOSE 4,752 净差 +37 = +9 −6 +34。
- 若以 P0-CLOSE 口径重算 = 4,795（C01=102、C08 未修 +9、本轮 +34），仅对照不入账。

## 反向核查（防过度纠正）
- 106 个纯空桩单列于 `SUMMARY.md`，零提升；不满足「委托行 + JMP_THIS」双条件。
- 4 地址同码折叠重复（0x40E320/0x52ACE0/0x5447C0/0x71E6A0）：TSV 逐实例列，high 按唯一地址计。
- 6 地址不在任何卡（0x5C5CE0/0x5C6150/0x5C93E0/0x5CA630/0x5CB3A0/0x6CF180）：仅登记，不入十片增量。
- C06 `0x5D8170` conf=high 但名 vtable 槽，按 §954 不归误剔。

## 分级
- [已证]：300/99/95/106 计数、C08=9/C09=15 回收核对、基线分桶（脚本逐行枚举）。
- [静态推断]：判据特异性结论、同码折叠判定、错名 vs 降级区分。
- 无 [未证] 进入核心结论。

## 证据路径（均不截断）
- `NOINIT_CENSUS.tsv`（99 行）、`BASELINE.md`、`IMPACT_BY_CARD.md`、`SUMMARY.md`。
- `EVIDENCE\census_detailed.json`（208 KB）、`scan_noinit_raw.txt`（300 行上下文）、`percard_correlation.json`、`card_detail_block.txt`。
- `work\`：scan_noinit_raw.py / analyze_yrpp.py / inspect_census.py / correlate_cards.py / show_census_rows.py / count_grades.py / verify_trace_conf.py / gen_census_tsv.py / gen_impact_md.py / gen_summary_md.py / card_summary.py（全部可复跑）。

## 纪律
- capstone `skipdata=True` 为任务族基线；本卡判据为 YRpp 文本扫描未自反汇编；站点归属用各卡 atlas 区间（函数区间包含），未用 entry_at_or_before。
- 未写台账、未改任何卡 tsv、未改 COVERAGE\、未改 ra2youli\、未 commit。
