# M22 · 合并员：清「已审计但未并入」的合并队列（COVERAGE\ 唯一写者）

## 身份与写域（绝对路径）
你是**合并员**。**你是 COVERAGE\ 的唯一写者**，本卡串行执行，不得与其它 M 卡并行。
写域仅：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\`
     + `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M22\`（你的报告与日志）
其他任何位置一律只读。**不得改台账、不得改 R14_COMMON、不得改任何卡目录、不得 git commit。**

## 输入白名单（**只读这些卡目录，别的一概不读**）
按优先级（`S17-K3` 先做，它只有 1 行但直接决定 S17 的数字）：

| 序 | 卡 | STATUS 裁决 | delta 行 | 备注 |
|---|---|---|---|---|
| 1 | `S17-K3` | **PASS** | 1 | `00431B80` |
| 2 | `S13-K2` | PARTIAL | 8 | 提级 8 行 |
| 3 | `S13_K5` | PARTIAL | 6 | |
| 4 | `S15-K3` | PARTIAL | 3 | |
| 5 | `S18-K2` | PARTIAL | 4 | |
| 6 | `S12-Q2` | PARTIAL | 11 | |
| 7 | `S01-K2` | PARTIAL | 9 | |
| 8 | `S02-K2` | PARTIAL | 5 | |
| 9 | `S06-K1` | PARTIAL | 20 | |
| 10 | `S03-K1` | PARTIAL | 16 | |
| 11 | `S10_K4` | PARTIAL | 19 | 注意：K4 的语义已由审计更正为 `MissionClass::UpdateTimer` 450 帧 |
| 12 | `S19-F1` | PARTIAL | 39 | 低优先（多为 atlas 外地址）|

**本次最多处理前 8 张**（1–8）；做到就写 `PARTIAL_DONE.md` 说明进度，**不要一次做完 12 张**。
**绝对不读**：`S11_K4`(FAIL 331 行)、`S13_K6`(FAIL 45 行)、`S03-K2`/`S03-K2R`(FAIL)、`S05-K2`/`S19-K2`(NO_VERDICT)
—— 这些并入＝污染盘面。若发现白名单外的卡，忽略并在报告里列名。

## 每张卡的处理规程（逐卡，不许批量糊过去）
1. 读该卡 `_audit\VERDICT.md` **全文**，把审计明确要求的「须改 / 须降级 / 不得并入」逐条抄进你的日志。
2. 读 `coverage_delta.tsv`，**按 VERDICT 修正**其 name/grade/semantics 后再考虑并入（例如 S10_K4 的语义行要按审计改成 `UpdateTimer`；S13_K2 若审计只认部分行，只并那部分）。
3. **逐行幂等检查**：拿 entry 去 `coverage.tsv` 比对现值——
   - 盘上 grade ≥ delta grade 且 name 已一致 ⇒ **跳过**（记 `already`）。
   - delta 更高 ⇒ 升级（记 `upgrade`）。
   - 同 grade、名字不同 ⇒ 写 `CONFLICTS.tsv`，`coverage.tsv` **保留旧值**并标 `conflict=1`，记 `conflict`。
   - entry 不在 `coverage.tsv` ⇒ 记 `not_in_coverage`，**不新增行**（新增入口属 P0 通道，本卡无此权限）。
4. 写前记录该行 before 值，写后 after 值，进 `M22\MERGE_LOG.tsv`
   （列：card, entry, action(already/upgrade/conflict/not_in_coverage/skipped_by_audit), grade_before, grade_after, name_before, name_after, verdict_quote）。
5. **每张卡做完就落盘一次** `coverage.tsv`，并在 `M22\PROGRESS.md` 追加一段（卡号 / 并入行数 / 跳过原因计数）。

## 不可违反
- **grade 只按第 5 列**统计与读取（语义栏里也含 grade 字样，全行正则会把它们算进去）。
- **atlas entry 是小写 hex、coverage.tsv 也是小写** —— 但比较前**一律 `tolower` + 去 `0x`**。
- **不得自行裁决**任何冲突、不得凭推断改 name、不得「顺手提升」VERDICT 没认的行。
- 结束后 `PANEL.md` 必须与 `coverage.tsv` 自洽：报每子系统 `n / named / named% / proved / proved%`，
  并**同时**报 `named_L`（不含 `sub_`）与 `named_S`（再排除 `Class::sub_` 与 `Class::slotN`）两列（D-38 未裁，两列都报）。

## 交付
`COVERAGE\coverage.tsv`（就地更新）、`COVERAGE\CONFLICTS.tsv`、`COVERAGE\PANEL.md`
`M22\PROGRESS.md`、`M22\MERGE_LOG.tsv`、`M22\PARTIAL_DONE.md`（若未做满白名单）、`M22\work\`（你的脚本，可复跑）

## 核心数字（给 Lead 复核）
① 每张卡的 upgraded / already / conflict / not_in_coverage / skipped_by_audit 计数 ② 全表 `[已证]` 变更前后值
③ 22 个子系统 named_L/named_S/proved 三列前后对照表。
