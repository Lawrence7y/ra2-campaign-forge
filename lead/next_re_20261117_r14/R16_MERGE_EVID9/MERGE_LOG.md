# R16-MERGE-EVID9 MERGE_LOG

> 合并员：`work/cn:hy4flash-free`（agent-7）　日期：2026-11-20　卡：`R16-MERGE-EVID9`

> 写域：`COVERAGE/coverage.tsv`（9 行第 6 列）+ `COVERAGE/PANEL.md`（插入 4 行）+ 本目录；两输入目录只读。

## 1. 改动摘要

- 3 行 delta（`004E0E80`/`006B6EA0`/`006B6FA0`）：第 6 列照 `R16_EVID9/coverage_delta.tsv` 原样取（审计 PASS、0 必改；`BOTH_IDENTICAL`，取 `S10_K8`）。
- 6 行（`004DF320`/`004DF3A0`/`004DFB70`/`004DFCB0`/`004DFE00`/`006F4960`）：第 6 列新路径统一并 `S10_K8F\EVIDENCE\QUEUE_DISPATCH_AND_FALSE_KILLS.txt#<entry>`；注记逐行带各自 entry 锚点说明，主体一致但 6 行不雷同。
- **不并 `S10_K8`**：审计已推翻「取字典序较小者」——`S10_K8F` 对 `S10_K8` 支配（K8 独有 4 行全为叙述行、载荷独有数 0）、K8 头部跳表行自相矛盾、盘上 6 行语义已为 K8F 措辞。

## 2. 9 行第 6 列 before / after

| entry | 行 | before 第 6 列 | after 第 6 列 |
|---|---|---|---|
| `004E0E80` | L3308 | `EVIDENCE/OWNERSHIP_004E0E80.txt#004E0E80` | `S10_K8\EVIDENCE\OWNERSHIP_004E0E80.txt#004E0E80;M84 指针修复：OWNERSHIP_004E0E80.txt 两候选字节全同，按字典序取 S10_K8。` |
| `006B6EA0` | L8949 | `EVIDENCE/SPAWNMANAGER_CTORS.txt#006B6EA0` | `S10_K8\EVIDENCE\SPAWNMANAGER_CTORS.txt#006B6EA0;M84 指针修复：SPAWNMANAGER_CTORS.txt 两候选字节全同，按字典序取 S10_K8，006B6EA0 为 S22 基线无参 ctor。` |
| `006B6FA0` | L14148 | `EVIDENCE/SPAWNMANAGER_CTORS.txt#006B6FA0` | `S10_K8\EVIDENCE\SPAWNMANAGER_CTORS.txt#006B6FA0;M84 指针修复：SPAWNMANAGER_CTORS.txt 两候选字节全同，按字典序取 S10_K8，006B6FA0 为 1arg ctor 行。` |
| `004DF320` | L3252 | `EVIDENCE/QUEUE_DISPATCH_AND_FALSE_KILLS.txt#004DF320` | `S10_K8F\EVIDENCE\QUEUE_DISPATCH_AND_FALSE_KILLS.txt#004DF320;M85 指针修复：原记缺卡目录层；两候选该 entry 锚点段落逐字节相同，但 S10_K8F 对 S10_K8 构成支配（K8 独有 4 行全为叙述行、证据载荷独有数 0）且 K8 头部跳表行自相矛盾，故取 S10_K8F。本行锚点 004DF320（QueueMissionId2ElseId1：清 +0x5D1 后按 0x5C8 / 0x5CC 分派 id=2 或 id=1），吞写块首行正落在 K8 头部 inner index 0 指向 41BADE 说反处。` |
| `004DF3A0` | L3253 | `EVIDENCE/QUEUE_DISPATCH_AND_FALSE_KILLS.txt#004DF3A0` | `S10_K8F\EVIDENCE\QUEUE_DISPATCH_AND_FALSE_KILLS.txt#004DF3A0;M85 指针修复：原记缺卡目录层；两候选该 entry 锚点段落逐字节相同，但 S10_K8F 对 S10_K8 构成支配（K8 独有 4 行全为叙述行、证据载荷独有数 0）且 K8 头部跳表行自相矛盾，故取 S10_K8F。本行锚点 004DF3A0（QueueMissionId1：cell-target 校验后入队 id=1、target=1），吞写 cur==1 且 queued 为 1 或 -1，对应 K8 头部 queued==-1 说反处。` |
| `004DFB70` | L3259 | `EVIDENCE/QUEUE_DISPATCH_AND_FALSE_KILLS.txt#004DFB70` | `S10_K8F\EVIDENCE\QUEUE_DISPATCH_AND_FALSE_KILLS.txt#004DFB70;M85 指针修复：原记缺卡目录层；两候选该 entry 锚点段落逐字节相同，但 S10_K8F 对 S10_K8 构成支配（K8 独有 4 行全为叙述行、证据载荷独有数 0）且 K8 头部跳表行自相矛盾，故取 S10_K8F。本行锚点 004DFB70（QueueMissionId7：nearby-filter 后入队 id=7、target=0），吞写 cur==7 且 queued 为 7 或 -1；K8 头部同段早退规则亦说反。` |
| `004DFCB0` | L3260 | `EVIDENCE/QUEUE_DISPATCH_AND_FALSE_KILLS.txt#004DFCB0` | `S10_K8F\EVIDENCE\QUEUE_DISPATCH_AND_FALSE_KILLS.txt#004DFCB0;M85 指针修复：原记缺卡目录层；两候选该 entry 锚点段落逐字节相同，但 S10_K8F 对 S10_K8 构成支配（K8 独有 4 行全为叙述行、证据载荷独有数 0）且 K8 头部跳表行自相矛盾，故取 S10_K8F。本行锚点 004DFCB0（QueueMissionId8：House-filter 后入队 id=8、target=1），吞写 cur==8 且 queued 为 8 或 -1，且 cur=30 跳过 +0x6D2 清位。` |
| `004DFE00` | L3261 | `EVIDENCE/QUEUE_DISPATCH_AND_FALSE_KILLS.txt#004DFE00` | `S10_K8F\EVIDENCE\QUEUE_DISPATCH_AND_FALSE_KILLS.txt#004DFE00;M85 指针修复：原记缺卡目录层；两候选该 entry 锚点段落逐字节相同，但 S10_K8F 对 S10_K8 构成支配（K8 独有 4 行全为叙述行、证据载荷独有数 0）且 K8 头部跳表行自相矛盾，故取 S10_K8F。本行锚点 004DFE00（QueueMissionId8：global-filter 后入队 id=8、target=1），全局表 0xA8EB44 / 0xA8EB50，与 004DFCB0 同 id 但过滤源不同。` |
| `006F4960` | L10005 | `EVIDENCE/QUEUE_DISPATCH_AND_FALSE_KILLS.txt#006F4960` | `S10_K8F\EVIDENCE\QUEUE_DISPATCH_AND_FALSE_KILLS.txt#006F4960;M85 指针修复：原记缺卡目录层；两候选该 entry 锚点段落逐字节相同，但 S10_K8F 对 S10_K8 构成支配（K8 独有 4 行全为叙述行、证据载荷独有数 0）且 K8 头部跳表行自相矛盾，故取 S10_K8F。本行锚点 006F4960（QueueMissionId15：mission14 分支入队 id=15、target=0），吞写 cur==15 且 queued 为 15 或 -1，target=0 不触发晋级。` |

## 3. 6 项验证（卡 §4）

| # | 检查 | 结果 | 实测 |
|---|---|---|---|
| 1_coverage_byte_restore | PASS | rebuilt_sha=325158B5 before_sha=325158B5 equal=True |
| 2_invariants | PASS | data_rows=18498 col_dist={8: 18498} proved=1654 atlas_in=1648 atlas_out=6 nine_grades_all_proved=True |
| 3_only_9_col6_changed | PASS | line_count_equal=True n_diff_lines=9 all_entry_in_NINE_and_only_col6=True details=[(3252, '004DF320', [5]), (3253, '004DF3A0', [5]), (3259, '004DFB70', [5]), (3260, '004DFCB0', [5]), (3261, '004DFE00', [5]), (3308, '004E0E80', [5]), (8949, '006B6EA0', [5]), (10005, '006F4960', [5]), (14148, '006B6FA0', [5])] |
| 4_resolve_reclassify | PASS | R_OK=852 R_MISSING=0 R_TRACE_ONLY=802 R_EMPTY=0 (resolve rc=0) |
| 5_panel_restore | PASS | inserted_at_line=210 n_insert_lines=4 rebuilt_sha=ADDA58E2 before_sha=ADDA58E2 equal=True marker_at=210 |
| 6_dod_not_flipped | PASS | nominal={S15,S16,S17} strict={S17} (rc=0) |

- 重跑四分类：`R_OK=852` / `R_MISSING=0` / `R_TRACE_ONLY=802` / `R_EMPTY=0`（预期 852/0/802/0，实测一致）。
- 名义达标：`S15,S16,S17`；严格达标：`S17`（预期 `S15,S16,S17` / `S17`，实测一致）。

## 4. `/`→`\` 额外字节变化

- 9 行原第 6 列各含 1 个 `/`（`EVIDENCE/` 分隔符）；新值中该分隔符统一写为 `\`，并新增卡目录前缀分隔符 `\`。
- 故 9 行各有 **1 处 `/`→`\` 字节替换**（共 9 处），均落在第 6 列内，属卡面允许的指针写法保留（3 行照 delta 交付、与 M82 风格一致；6 行按卡 §3.1 指定格式）。
- `resolve.py` 解析时 `/` 与 `\` 均归一化为 `os.sep`，不影响可解析性；实测 `R_OK=852` 已含此写法。
- 除第 6 列外无任何字节变化（验证 1 与 3 已逐字节证明）。

## 5. 产物

| 文件 | 内容 |
|---|---|
| `MERGE_LOG.md` | 本文件 |
| `verify.py` | 自包含复跑 6 项验证（只读两目标文件；resolve.py/strict_panel.py 输出落本目录 `EVID_RESOLVE` 副本与 `_strict_out`）|
| `BEFORE_AFTER.txt` | 关键行对照 + 两文件改前/改后 mtime/字节/sha256 |
| `before_state.json` / `after_state.json` | 改前/改后状态与验证结果 |
| `coverage_before.tsv` / `PANEL_before.md` | 改前原件逐字节副本（供还原验证）|
| `apply_changes.py` / `pre_record.py` / `precheck.py` | 写入与前置记录脚本 |
| `coverage_after_copy.tsv` / `_resolve_out/` / `strict_panel_copy.py` / `_strict_out/` | 验证用副本与输出（均在本目录）|
