# PROGRESS — SUB_CONFLICT
- 写域：仅 `lead/next_re_20261117_r14/SUB_CONFLICT/`；只读 COVERAGE、CARD_STATUS、S22_CENSUS、卡目录/台账。
- 口径：`field=subsystem` 全量；`source_a/source_b(card:value)` 按首个冒号拆卡名与值；`pending=>S22` 仅用于 S3 形态识别，不改值。
- 解析：CONFLICTS.tsv 有 466 条数据行；其中 subsystem=180（与背景一致）、name=274、grade=11；本卡输出 CLASSIFIED.tsv 180 条数据行。
- 与 466 行关系：本卡仅处理其中 180 行 subsystem；name 的 274 行（C3-ADJ/C3-44/M13/M14 已闭环、deadlock=6 待裁）不在本卡范围，grade 的 11 行亦不在。
- RTTI 交叉：只查 S22_CENSUS/CENSUS.tsv，不重跑 RTTI、不读 gamemd.exe；S1/S2 之外 class_known 记 unknown。
- PASS/PARTIAL 支持：以 CARD_STATUS/STATUS.tsv 精确卡名判定；源卡不在权威表或值不等于 coverage 现值则不计。
- 复算：S1=52、S2=123、S3=1、S4=4，合计 180；class_known=Y=10；PASS/PARTIAL 支持=10。
- 异常：4 条 W175 的 `RulesClass` 非 Sxx，记 S4；`0055D360` 在 CONFLICTS 中同 entry 两条不同对（S01↔S18、S01↔S07），按行保留。
- 数字与盘上不符：无；466/180 均与盘上复算一致。未改任何共享表，未做裁决。
