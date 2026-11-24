# MERGE_M82 — `evidence_path` 卡目录前缀修复（纯指针修复）

- 写者：agent-271（本轮唯一 COVERAGE 写者）
- 结论：修复 361 行；13 行因多候选歧义未修；0 行彻底丢失。判定与计数均未变。
- 未 git commit；未碰 R14_COMMON / STATUS_BOARD / 台账 / BOARD_ARCHIVE / EVID_RESOLVE / 任何卡目录。

## 做了什么

依据 `EVID_RESOLVE\REPORT.md` 的结论：`R_MISSING` 374 行的根因是 `evidence_path` 丢了卡目录层（记成 `EVIDENCE/x.txt`，实为 `S10-K2/EVIDENCE/x.txt`）。
对 `EVID_RESOLVE\resolve.tsv` 的 374 行 `R_MISSING`，按 REPORT 的后缀唯一匹配法（在 r14 下 case-insensitive、组件边界 endswith）找唯一同名文件：

- 路径级：87 唯一 / 5 歧义 / 0 丢失（精确复现 REPORT）
- 行级：**361 唯一可修 / 13 歧义不修 / 0 丢失**

对 361 个唯一行，仅改 `COVERAGE\coverage.tsv` 第 6 列：把每个路径段补上卡目录前缀（保留 `#anchor` 与 `:0x…` 行号锚点、保留多段 `;` 结构），并在末尾追加：
`;M82 指针修复：原记 <旧路径>（缺卡目录），实为 <新路径>`

示例：
  - `004011C0`: `EVIDENCE/evidence_raw.json#004011C0` → `C01_census/EVIDENCE/evidence_raw.json#004011C0`
  - `00401580`: `EVIDENCE/evidence_raw.json#00401580` → `C01_census/EVIDENCE/evidence_raw.json#00401580`
  - `004015C0`: `EVIDENCE/evidence_raw.json#004015C0` → `C01_census/EVIDENCE/evidence_raw.json#004015C0`
  - 行号锚点行 `006DBE20`: `work/t1a_xref2.py:0x6DBEB2-0x6DBECB` → `W177-G/work/t1a_xref2.py:0x6DBEB2-0x6DBECB`

`PANEL.md`：在 M81 披露之后追加 3 行 M82 补记（新 L199-201）。

## 没做什么（不变量）

- 第 5 列 grade、第 4 列语义、第 1/2/3/7/8 列：逐行字节不变
- 歧义 13 行：第 6 列保持原样，无注记
- 数据行 18,498、全表 [已证] 1,654、atlas 内 [已证] 1,648：全部不变
- 达标判定（名义 S15/S16/S17 3/22；严格 S17 1/22）：无翻转

## 复算（见 VERIFY.txt）

用 `EVID_RESOLVE/resolve.py` 原脚本对改后 coverage.tsv 重跑（输出重定向到 MERGE_M82，未写 EVID_RESOLVE）：

| 项 | BEFORE | AFTER | 期望 |
|---|---:|---:|---:|
| R_OK | 478 | **839** | 478+361=839 ✅ |
| R_MISSING | 374 | **13** | 374−361=13 ✅ |
| R_TRACE_ONLY | 802 | **802** | 802 ✅ |
| R_EMPTY | 0 | **0** | 0 ✅ |

R_OK 由 478/1,654（28.90%）升至 **839/1,654（50.73%）**。
（M81 披露把上界写作 50.72%，系截断；四舍五入实算为 50.73%。判定与计数均未变，本次只让证据指针重新可用。）

## 未修清单（歧义 13 行，保持原样）

0040F870, 004DF320, 004DF3A0, 004DFB70, 004DFCB0, 004DFE00, 004E0E80, 0054E890, 0054EA70, 006B6EA0, 006B6FA0, 006CDEF0, 006F4960

## 文件

- `MERGE_LOG.md`（本文件）
- `BEFORE_AFTER.txt`（两文件 before/after mtime/bytes/sha256，含一次可逆写入重试的透明记录）
- `VERIFY.txt`（全部强制复算与断言）
- 附：`_before_state.json` / `_apply_result.json` / `_verify_result.json` / `_analyze*.json` / `_*.py` 为过程留痕，非交付项。
