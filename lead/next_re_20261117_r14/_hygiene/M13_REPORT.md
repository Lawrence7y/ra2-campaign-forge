# M13_REPORT — C3-ADJ keep_A/keep_B name-only（2026-11-18）
写域：COVERAGE + _hygiene；快照 `_hygiene/M13_before/SHA256SUMS.tsv`（54 files，SHA-256 已记录）。
输入校验：DECISIONS.tsv 实载 58 数据行；keep_A=12 / keep_B=2 / needs_audit=44，与 PROGRESS.md 一致。

| entry | recommendation | 动作 | 来源卡裁决 | 结果 |
|---|---|---|---|---|
| 00489180 | keep_A | 无（现名已为推荐完整形） | PARTIAL | 一致；name 冲突消解 |
| 0048DCD0 | keep_A | 无（现名已为推荐完整形） | PARTIAL | 一致；name 冲突消解 |
| 004C6650 | keep_A | 无（现名已为推荐完整形） | PARTIAL | 一致；name 冲突消解 |
| 004C66C0 | keep_A | 无（现名已为推荐完整形） | PARTIAL | 一致；name 冲突消解 |
| 004C6720 | keep_A | 无（现名已为推荐完整形） | PARTIAL | 一致；name 冲突消解 |
| 004C6780 | keep_A | 无（现名已为推荐完整形） | PARTIAL | 一致；name 冲突消解 |
| 004C6800 | keep_A | 无（现名已为推荐完整形） | PARTIAL | 一致；name 冲突消解 |
| 004C6AE0 | keep_A | 无（现名已为推荐完整形） | PARTIAL | 一致；name 冲突消解 |
| 004C6B60 | keep_A | 无（现名已为推荐完整形） | PARTIAL | 一致；name 冲突消解 |
| 006805F0 | keep_A | 无（现名已为推荐完整形） | PARTIAL | 一致；name 冲突消解 |
| 00692300 | keep_A | 无（现名已为推荐完整形） | PARTIAL | 一致；name 冲突消解 |
| 00692610 | keep_A | 无（现名已为推荐完整形） | PARTIAL | 一致；name 冲突消解 |
| 006CF240 | keep_B | 改名 Here_I_Am → SwizzleManager::Here_I_Am | PARTIAL;PARTIAL | 改名；name 冲突消解(2 行) |
| 006DBE20 | keep_B | 改名 hover_cell_GetCellAt_caller → hover_GetCellAt_caller | PARTIAL | 改名；name 冲突消解(1 行) |

统计：实际改名 2；keep_A 现名已一致 12/12（无需动作）；来源卡未审计/FAIL 0；needs_audit 44 未触碰。
来源卡门：S13-F1 / S09-F1 / S18-F1 / S17-F1 / W177-H 的 VERDICT 均为 PARTIAL；006CF240 按 reason 取 SwizzleManager::Here_I_Am。
coverage.tsv：18,431→18,431；仅第 3 列 2 行变化，其余 7 列 0 差异。
grade before = after = [未证] 11,031 / [静态推断] 6,032 / [已证] 1,368（逐位相同）。
PANEL：atlas 内 L/S(R14)/strict/proved = 7,193 / 7,185 / 1,541 / 1,363，before=after；named_pct_S 双列、S13 240/148、S22 不排名、12,916/14,487/18,431 保留。
CONFLICTS.tsv：新增 status 列；14 个 entry 对应 15 条 name 行标记 RESOLVED_M13:改名后两侧已一致，6 条 subsystem 行仍 OPEN；记录未删，465 行不变。
PENDING_CORRECTIONS.tsv +2（两条实际改名）：239→241；无“名字来源卡未审计”条目。
未改动：12 条 keep_A（现名已优且已一致）、44 条 needs_audit（另派卡）、grade/one_line_semantics/evidence_path/subsystem/conflict 全字段。
SHA-256 after：coverage 3d4dbce78fc10c471141fd423edc876bb20d26408b99c384e8fa7708699682c8；PANEL c531618813854bad12d076bbe5176f9206cbd114dd57987a2ba67760f6e9feca；CONFLICTS 56d7731909b1f7421680fb7840ab06c91d4fd560f6bea0c463a392da134d8530；PENDING a38af16fc22f71dbab510ad7f5e0084c1538f3bc9b90254ccfd8a43971b9a732。
自检：58 行/10 列、裁决计数、VERDICT 门、18,431 行、grade Counter、逐格 diff、15 条消解标记全部通过。
