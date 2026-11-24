# MERGE_M83 — 歧义证据指针消解（按 subsystem 锁定卡目录，纯指针修复）

- 写者：agent-272（本轮唯一 COVERAGE 写者）
- 结论：M82 后剩 13 行同名跨卡目录歧义；按「目录名含该行 subsystem 编号」消歧，修复 4 行、9 行仍未修。判定与计数均未变。
- 未 git commit；未碰 R14_COMMON / STATUS_BOARD / 台账 / BOARD_ARCHIVE / EVID_RESOLVE / 任何卡目录。

## 如何找到这 13 行（现盘口径）

`EVID_RESOLVE\resolve.tsv` 是 M82 之前的快照；现盘为准。用 `EVID_RESOLVE/resolve.py` 的 `resolve_row` 对当前 coverage.tsv 全部 1,654 行 `[已证]` 重分类：R_OK 839 / R_MISSING 13 / R_TRACE_ONLY 802 / R_EMPTY 0。对这 13 行 R_MISSING 逐行按后缀（case-insensitive / 组件边界 endswith，r14 下）找候选，全部为多候选歧义；恰好 13 行，与 M82 记录一致（未触发“不是 13 就停下”）。

找到的 13 个 entry：

> 0040F870, 004DF320, 004DF3A0, 004DFB70, 004DFCB0, 004DFE00, 004E0E80, 0054E890, 0054EA70, 006B6EA0, 006B6FA0, 006CDEF0, 006F4960

（口径说明：直接扫“无 M82 注记的 `[已证]` 行里后缀多候选”会把 `classification_trace.tsv` 的 R_TRACE_ONLY 行也算进来——它们不是 R_MISSING、不属于本卡尾巴。故以 resolve.py 现盘重分类的 R_MISSING 13 行为准。）

## 消歧方法（本卡核心）

对每个歧义行：先按后缀找出全部候选文件；再**只保留目录名含该行 subsystem 编号（S\<NN\>）的候选**；恰好剩 1 个 ⇒ 修；仍 >1 或 0 个 ⇒ 不修。

## 修复 4 行（仅改第 6 列）

第 6 列改成带卡目录的完整相对路径，末尾追加 `;M83 歧义消解：原记 <旧路径>，按 subsystem=<SXX> 锁定为 <新路径>`：

| entry | subsystem | 旧 | 新 | 消歧依据 |
|---|---|---|---|---|
| 0040F870 | S13 | `EVIDENCE/four_rings.md#0040F870` | `S13_K12/EVIDENCE/four_rings.md#0040F870` | 候选 S13_K12 / S16_PADD / S17_PADD，仅 S13_K12 含 S13 |
| 0054E890 | S13 | `EVIDENCE/four_rings.md#0054E890` | `S13_K12/EVIDENCE/four_rings.md#0054E890` | 同上 |
| 0054EA70 | S13 | `EVIDENCE/four_rings.md#0054EA70` | `S13_K12/EVIDENCE/four_rings.md#0054EA70` | 同上 |
| 006CDEF0 | S16 | `EVIDENCE/E01_rtti.txt` | `S16-K1/EVIDENCE/E01_rtti.txt` | 候选 S03-K1 / S16-K1，仅 S16-K1 含 S16 |

新路径均在盘上 `os.path.isfile` 为真。

## 未修 9 行（保持原样，原因逐条）

| entry | subsystem | evidence_path | 候选 | 原因 |
|---|---|---|---|---|
| 004DF320 | S10 | QUEUE_DISPATCH_AND_FALSE_KILLS.txt | S10_K8 / S10_K8F | 两者都含 S10，过滤后仍 2 个，不唯一 |
| 004DF3A0 | S10 | 同上 | 同上 | 同上 |
| 004DFB70 | S10 | 同上 | 同上 | 同上 |
| 004DFCB0 | S10 | 同上 | 同上 | 同上 |
| 004DFE00 | S10 | 同上 | 同上 | 同上 |
| 006F4960 | S10 | 同上 | 同上 | 同上 |
| 004E0E80 | S10 | OWNERSHIP_004E0E80.txt | S10_K8 / S10_K8F | 两者都含 S10，过滤后仍 2 个，不唯一 |
| 006B6EA0 | S22 | SPAWNMANAGER_CTORS.txt | S10_K8 / S10_K8F | 两者都不含 S22，过滤后 0 个，无法确定 |
| 006B6FA0 | S22 | SPAWNMANAGER_CTORS.txt | S10_K8 / S10_K8F | 同上 |

这 9 行第 6 列保持原值、无任何 M83 注记。

## 没做什么（不变量）

- 第 5 列 grade、第 4 列语义、第 1/2/3/7/8 列：逐行字节不变
- 数据行 18,498、全表 `[已证]` 1,654、atlas 内 `[已证]` 1,648：全部不变
- 达标判定（名义 S15/S16/S17 3/22；严格 S17 1/22）：无翻转
- PANEL.md：在 M82 补记（L199-201）后新插入 M83 补记 2 行（新 L202-203）

## 复算（见 VERIFY.txt）

| 项 | BEFORE | AFTER | 期望 |
|---|---:|---:|---:|
| R_OK | 839 | **843** | 839+4=843 ✅ |
| R_MISSING | 13 | **9** | 13−4=9 ✅ |
| R_TRACE_ONLY | 802 | **802** | 802 ✅ |
| R_EMPTY | 0 | **0** | 0 ✅ |

R_OK 由 839/1,654（50.73%）升至 **843/1,654（50.97%）** ≥ 839 要求。判定与计数均未变。

## 文件

- `MERGE_LOG.md`（本文件）
- `BEFORE_AFTER.txt`（两文件 before/after mtime/字节/sha256）
- `VERIFY.txt`（全部强制复算与断言）
- 附：`_before_state.json` / `_analysis.json` / `_apply_result.json` / `_verify_result.json` / `_*.py` / `_verify_resolve_out/` 为过程留痕，非交付项。
