# R16-MERGE-D1-FINAL · 合并报告

> 合并员：`agent-59` · 2026-11-21 · 唯一写者：`COVERAGE/coverage.tsv` + `COVERAGE/PANEL.md`。
> 写域：`lead/next_re_20261117_r14/COVERAGE/`（仅 2 文件）+ 本目录 `R16_MERGE_D1_FINAL/`。
> 输入：`R16_D1_FINAL/delta.tsv`（5 行）；裁决：`R16_AUDIT_D1_FINAL/VERDICT.md`（事实层 5/5 可用、批级 FAIL 仅涉筛选口径，与本 5 行事实层无关）。

## 1. 落盘内容

- **coverage.tsv**：仅 5 行第 4 列追加 `；④ 活表槽位见证：…`（严格前缀），其余 7 列逐字节相同、grade 未改 `[已证]`；无行增删。
  - entry / 行号：`0051B1F0`@4426、`0051DAF0`@4435、`00522340`@4483、`0070B570`@10147、`00748190`@10965。
- **PANEL.md**：紧接 M97 块（结束于原第 289 行）之后插入 1 条 M98 披露（原第 290 行 M77 说明之前），共 7 行；既有内容零删除零改字。
  - M98 如实写明三件事：① 5 行事实层经异族审计 5/5 可用；② 该批「按 ② 筛出 17 行」实为 ④ 形态轴（F1/F2）、代码无审计链判定（Lead 错误 R16-6），D-52 已重定义口径、另一张筛选卡 R16_SIEVE_D1_WIDE 已重做；③ 「做完这批即整线收口」不成立，真实可收集合以 R16_SIEVE_D1_WIDE 实测为准。

## 2. SHA-256（改前 → 改后）

| 文件 | 改前 | 改后 |
|---|---|---|
| coverage.tsv | `e4f111b6643661d01c66db1889172437a06a563233f0a252ad0db4a54fd51c8a` | `412ed7e36bc1ad4907763febb3a68d5fdabb3f0d2c999800444b57098b1ab2e1` |
| PANEL.md | `3cf798f0e076795e4aeed8ce98dbad7dc729b7c053748d7587e5ae5d107b536a` | `ec1715561fbb952b79ffd246ee1790fce24e4f242498dcc4afd3f488db16ff8f` |

## 3. 验证逐项（全部 PASS）

| # | 检查 | 结果 | 实测 |
|---|---|---|---|
| ① | 严格前缀 | **PASS** | 5/5：新第 4 列 = 原第 4 列严格前缀，且等于 delta 第 4 列 |
| ② | 逐字节还原性（coverage） | **PASS** | 5 行第 4 列换回 `before_col4` 后 sha == pin sha（`e4f111b6…`） |
| ③ | 不变量 | **PASS** | 18,498 数据行 / `{8:18498}` / `[已证]` 1,654 / atlas 内 1,648 / 外 6 |
| ④ | 只改 5 行第 4 列 | **PASS** | 其余列逐字节同、grade 未变、非目标行逐字节同、行数不变 |
| ⑤ | 口径 A/B 实测 | **PASS** | A 389→394（**+5**）；B 222→227（**+5**，5 行均含 `④ 活表槽位见证` 子串）；改前改后盘上实测，非推算（R16-5 教训） |
| ⑥ | PANEL 还原性 | **PASS** | 移除插入的 7 行后 sha == pin PANEL sha（`3cf798f0…`）；既有行逐字节同、锚点 M97→M98→M77 正确 |
| ⑦ | 达标未翻转 | **PASS** | `strict_panel` 权威口径本地复算（输出仅写本目录）：名义 S15/S16/S17、严格 S17 前后一致；total_proved 1,648、proved_strict 1,331 前后一致 |
| ⑧ | 行尾不混用 | **PASS** | coverage LF=18,498/CRLF=0；PANEL LF=682(675+7)/CRLF=0；均无 BOM、无 lone CR |

## 4. 产物（仅本目录）

`_pin_coverage.tsv`、`_pin_PANEL.md`（改前 pin）；`before_col4.json`、`baseline.json`、`merge.py`、`MERGE_LOG.json`、`strict_panel_local.py`、`before_strict_panel.json`、`after_strict_panel.json`、`verify.py`、`VERIFY_RESULT.json`、`REPORT.md`。

## 5. 边界声明

未改 `R14_COMMON` / 台账 / 看板 / `_drafts` / `_cards` / 任何卡目录；未做逆向；`strict_panel` 口径副本输出到本目录；卡目录只读。
