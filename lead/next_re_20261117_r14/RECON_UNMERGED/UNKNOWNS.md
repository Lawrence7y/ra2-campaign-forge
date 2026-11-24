# RECON-UNMERGED · UNKNOWNS

## U1（口径分歧，未决，交 Lead 裁）S10_K11 的 A/C 归属取决于铁规的读法

- 事实：`004DFCB0` / `004DFE00` 两行的语义栏由 **M11** 并入（首现于 `_hygiene\coverage.M12.before`，即 M11 合并前备份），grade 两行在 M11 之前**已是** `[已证]`，本卡未授予任何 grade。
- 事实：`S10_K11` 自身**没有** `_audit\VERDICT.md`；全树 130 份 VERDICT 中无一以 S10_K11 为审计对象。
- 事实：两行**有**审计结论——`S10_K8\_audit\VERDICT.md` L13-14 逐行判 `004DFCB0 ✔` / `004DFE00 ✔`；`S10_K8F\_audit\VERDICT.md` L20-21 残留 R1/R2 明令「004DFE00 的 `or` 应改 `and`」「004DFCB0 漏写跳过条件」，裁决 PASS 且写「R1/R2 进 PENDING_CORRECTIONS 改字即可，无需回退或降级任何行」。时序：该 VERDICT mtime 05:41:09 < K11 delta 05:45:52 < M11.bak 05:57:15。
- 两种读法：
  - 读法甲（本卡采用，**行级**）：并表行的结论有异族审计支撑 ⇒ A。
  - 读法乙（**卡级**）：R14_CARDS.md L184「输入：所有状态为 PASS/PARTIAL 的卡目录下 coverage_delta.tsv」要求卡自身有裁决 ⇒ S10_K11 无 PASS/PARTIAL 状态，其 2 行应算 C（1 卡 / 2 行）。
- 支持乙的旁证：台账 §999 自己写「`S10_K11`(2 行) **无审计** ⇒ 只写『措辞修正』」，即项目当时也是按「无审计」对待，只是没有降级/回退。
- 未裁原因：本卡只读，不改台账、不替 Lead 决定登记例外是否等同于合规。

## U2（事实缺口）`_hygiene\M38.bak` 与 `M47.bak` 缺失

- 现状：`_hygiene\` 有 `coverage.M23..M48.bak`，但**无 M38.bak、无 M47.bak**（M38 目录本身存在且 MERGE_LOG 为 4 列表头 `行标识/变更类型/改前值/改后值`、12 行，行标识非 entry，无法按 entry 反查）。
- 影响：`0045A680` 等 6 行的 grade 变迁只能定位到「M37.bak 为旧值、M39.bak 为新值」的区间，无法单凭快照区分是 M37 还是 M38 所为；本卡改用 `M37\MERGE_LOG.tsv` 的 `action=applied / reason=granted_by_audit_a-S08-KPROVED2` 定为 M37。若 M38 另有动作，本卡结论不变（该行仍有审计出处）。

## U3（口径边界）AUDIT_SEM_SELF 是否满足「异族审计 PASS 或 PARTIAL」的字面要求

- 事实：`AUDIT_SEM_SELF\CARD.md` 首行自述「⚠️ **只读测量卡，不改任何 grade、不交 delta**」；交付为 `ROW_VERDICTS.tsv`（95 行）+ 95 份独立反汇编，逐行给 P1/P2/P3 与 `criterion`（③b①/②/④）。
- 缺口：无卡级 `PASS`/`PARTIAL` 字样，也无 `_audit\VERDICT.md`。其 `PROGRESS.md` 给的是 `P1=73 P2=22 P3=0`。
- 本卡处理：把「逐行 P1（③b 成立，语义栏需按本条重写）」当作该行的审计结论，故 SEMFIX_6 / SEMFIX_REST / SEMFIX_S10 的 72 行判 A。**若 Lead 要求卡级 PASS/PARTIAL，则这 3 张卡共 72 行需重新定性**（这 3 张卡只改语义、未改 grade，且改动方向是由弱语义改为可证伪语义，不涉及提级）。

## U4（未核）合并时点之后是否有对已并入行的再次改动

- 本卡只核到「该行当前状态是否匹配 delta」与「首现于哪个快照」。`M48.bak` 与当前 `coverage.tsv` **字节相同**（SHA 均为 `e397af86…`），故 M48 之后无并表；但 M48 之前每行的**多次**改写未逐次穷举（如 `0045A680` 在 M37 提级、M42 改语义，两次已分别记；更早的 M25/M26/M32 记录只作旁证未深挖）。

## U5（未核）「异族」的模型身份

- 「异族」按 `R14_CARDS.md` 指审计模型与执行员不同族。本卡无从核验子代理实际模型（台账记 `work/cn:deepseek-v4.1-flash` high 等），只能核验**审计产物存在且给出裁决**。若需模型级异族证明，须查 `lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md`（本卡未展开，超出完整性核查范围）。
