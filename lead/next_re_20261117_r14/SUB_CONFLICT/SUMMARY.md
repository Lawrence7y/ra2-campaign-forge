# SUB_CONFLICT SUMMARY — subsystem=180

口径：对象=`COVERAGE/CONFLICTS.tsv` 中 `field=subsystem` 的全部数据行；只分类，不改表、不做归属裁决。
RTTI：只查 `S22_CENSUS/CENSUS.tsv`（A1/A2/A3 且有类名=Y；A4 无类名=N；无条目=unknown），未重扫 `gamemd.exe`。
PASS/PARTIAL 支持：以 `CARD_STATUS/STATUS.tsv` 为权威；源卡状态为 PASS/PARTIAL 且其冲突值等于 `coverage.tsv` 现值才计支持。
形态特例：4 条 `RulesClass` 非 Sxx 记 S4；`004E0E80` 的 `D-37:pending (...=>S22)` 按语义 pending-S22 且容器模板记 S3。

| 形态 | 含义 | 条数 |
|---|---|---:|
| S1 | 一侧 S22、一侧业务子系统 | 52 |
| S2 | 两侧业务子系统 | 123 |
| S3 | S22 + 容器模板实例 | 1 |
| S4 | 记录残缺（缺有效 subsystem/来源卡） | 4 |
| 合计 |  | 180 |

S1 class_known：Y=10 / N=29 / unknown=13；S2：Y=0 / N=0 / unknown=123。
class_known=Y 共 10 条（全在 S11↔S22 的 TClassFactory 行）= D-37 可机械落地规模。
coverage 现值获 PASS/PARTIAL 卡支持：10/180（按形态：S2=10；S1/S3/S4=0）。

## 有效子系统对 Top 10（S4 不计；pending=>S22 归一为 S22）
| # | 子系统对 | 条数 |
|---:|---|---:|
| 1 | S11↔S22 | 23 |
| 2 | S05↔S12 | 17 |
| 3 | S06↔S12 | 14 |
| 4 | S09↔S22 | 9 |
| 5 | S05↔S10 | 7 |
| 6 | S06↔S08 | 7 |
| 7 | S06↔S22 | 6 |
| 8 | S05↔S22 | 5 |
| 9 | S07↔S09 | 5 |
| 10 | S01↔S18 | 4 |
并列 4 条的还有：S03↔S04、S04↔S05、S05↔S14、S05↔S20、S07↔S08、S10↔S11（Top10 按字典序截到 S01↔S18）。

## 结论
真正需人裁决 165 条 = S1 非Y 42 + S2 123；S3 1 条按容器规则不需裁决，S4 4 条属记录补录、不计裁决。
