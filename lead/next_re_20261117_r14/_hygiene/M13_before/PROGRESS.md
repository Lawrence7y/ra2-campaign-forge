# PROGRESS — C3-ADJ

- 口径：只裁决 CONFLICT_CLASS2/CLASSIFIED.tsv 的 C3（58）；不动 C1/C2/C4，不改共享表。
- A/B：以 COVERAGE/CONFLICTS.tsv 的 source_a/source_b 为唯一口径；cov/other 由 coverage 当前行与 side 映射校验。
- 解析：CLASSIFIED.tsv 数据行 250，C3=58；CONFLICTS.tsv 中这 58 个 entry 命中 125 条 name/subsystem 行，coverage.tsv 命中 58/58 行。
- 交付：DECISIONS.tsv 58 行（不含表头）；字段 10；form=P1..P4；recommendation 仅 keep_A/keep_B/needs_audit/no_evidence。
- 计数：P1=14, P2=15, P3=22, P4=7；keep_A=12, keep_B=2, needs_audit=44, no_evidence=0。
- 证据：每行均列出 COVERAGE/coverage.tsv、COVERAGE/CONFLICTS.tsv 与卡目录已存在的 VERDICT/EVIDENCE 路径；无路径不推断。
- 纪律：P3 不裁决；P4 只给倾向并标 needs_audit；P2 标分类错误；未改 COVERAGE/、CONFLICT_CLASS2/ 或任何台账/卡目录。
- 复核：DECISIONS entry 集合与 CLASSIFIED C3 清单完全一致（58/58，无缺漏、无越界）。
