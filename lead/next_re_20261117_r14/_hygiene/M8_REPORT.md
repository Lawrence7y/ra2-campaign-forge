# M8 对账报告（2026-11-18）

## 0. 快照
开工前四文件已快照至 `_hygiene/M8_before/`（SHA256 见该目录 SHA256SUMS.txt）：coverage.tsv `ff43bb04…c75c7`、PANEL.md `1cda5f60…58de8`、CONFLICTS.tsv `fa8b8b87…f05dd`、PENDING_CORRECTIONS.tsv `a4b5a2ea…a33ecf`。

## 1. 逐行分类（697 数据行 = STATUS 723 物理行 − 26 表头）
| 类别 | 行数 | 占 697 | 占 507(现存条目) | 处置 |
|---|---:|---:|---:|---|
| 已并入一致（name+grade 一致） | 304 | 43.62% | 59.96% | 不动 |
| (a) 后审计更正/降级 | 5 | 0.72% | 0.99% | 不动（含 004F8440 PENDING 降级 2 行；coverage 更高 3 行） |
| (b) name/subsystem 不一致（含 grade 差异伴随） | 197 | 28.26% | 38.86% | 保留 coverage 现值；同 grade 175 行中 85 字段新增 CONFLICTS |
| (c) 真漏并 | 1 | 0.14% | 0.20% | 并入 1 行 |
| atlas 外新入口（不在 coverage/atlas） | 190 | 27.26% | — | 单独统计，**未加入** coverage |

(a)/(b)/(c) 三类占 507 条现存取样：0.99% / 38.86% / 0.20%；其余 59.96% 已一致。

## 2. truly_missing 清单与依据
| 卡 | entry | 变更 | 依据 |
|---|---|---|---|
| S06-K3 | 00721A50 | [静态推断]→[已证]，semantics/evidence 按 delta | S06-K3/_audit/VERDICT.md ★D：「0x721A50 够 [已证]（字节级可独立复算）」；★D proved 103→104 仅此行；无 PENDING/UNSOURCED/CONFLICTS 降级登记，evidence 三路径实存 |
合入 **1** 行（merged_now=1），未新增/删除 entry。

## 3. 其余为何不改
- **已并入一致 304**：name+grade 与 coverage 完全相同，STATUS 的「部分并入」由 semantics 措辞或 STATUS 计法差异造成，非漏并。
- **(a) 5**：004F8440（S08-K1/S16-K1）在 PENDING 有 `grade=[静态推断]` 降级、conflict=1；S17-K2 00431B80 已由 M7 S17-K3 升 [已证]；W174 2 行 coverage 已 [已证]。按规则不回改、不凭 delta grade 提级。
- **(b) 197**：delta name 多为 `fn_`/`sub_`/旧槽名，coverage 已是更权威命名（如 `CellClass::GetContainedTiberiumValue`）；同 grade 的 175 行按规则只登记冲突、保留现值；伴随 coverage 更高 grade 的 22 行属已更正。
- **atlas 外 190**：全部不在 function_atlas.tsv（S09-F1 30、S10-K1 36、S12-K2 10、S13-K1 19、S16-K1 2、S18-F1 64、W173 2、W175 19、W176 8），按规则不偷偷加；其中 22 行已在 probe_and_data_entries.tsv。

## 4. 落盘变化
- coverage.tsv：18,431→18,431 行；grade(第 5 列) [已证] 1,344→1,345、[静态推断] 6,053→6,052、[未证] 11,034 不变；conflict=1 205→250。
- CONFLICTS.tsv：378→**463**（+85：name 46 / subsystem 39；46 个 entry，45 个 conflict 标志新置 1）。PENDING_CORRECTIONS.tsv：174→174（+0）。
- PANEL.md：标题/量纲/三分母说明/全表与 atlas 内 proved/S06/TOTAL/M8 说明/已知不完整处已刷新；named_pct_S 双列、S13 240/148 双分母、S22 不参与排名、三分母 A/B/C 均保留。
- `_hygiene/M8_RECON.tsv`：26 卡逐行对账表（本卡最有价值产出）。

## 5. 合规
写域仅 `COVERAGE/` + `_hygiene/`；未新增/删除 entry；未凭 delta grade 单独提级；同 grade 冲突只登记不裁决；未 git commit。
