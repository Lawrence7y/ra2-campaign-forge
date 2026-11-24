# R16-MERGE-D1-WIDE-B2 — D1 宽读 B2 批 18 行并表 + M100 披露

- 写者：agent-71（本轮 `coverage.tsv` / `PANEL.md` 唯一写者）
- 写域：`COVERAGE\coverage.tsv`（18 行第 4 列）、`COVERAGE\PANEL.md`（插入 1 条 M100）、本目录 `R16_MERGE_D1_WIDE_B2\`（产物）。未碰 R14_COMMON / 台账 / 看板 / `_drafts` / `_cards` / 任何卡目录；卡目录只读；未做逆向；`strict_panel_local.py` 输出只写本目录。

## 1. 本批来源与第 4 列取值
- **17 行**：第 4 列取 `R16_D1_WIDE_B2/delta.tsv`（异族审计 `R16_AUDIT_D1_WIDE_B2/AUDIT_REPORT.md` 判 17/18 PASS、1/18 FAIL，A 原文保全/B 字节事实/E 反抄袭/F 清单一致性四项 0 不合格；5 行 CLASS_FIX 全部成立）。
- **1 行**（`00473B10`，CCFileClass::slot9）：第 4 列取 `R16_FIX_B2_1ROW/delta.tsv`（修复版，替换 B2 旧 ④）。旧版把栈临时写 `mov dword ptr [esp+0x20],0x7e16b0`（装表点 `004014AC`，宿主 `004011C0`，1729 条指令无关函数）当成构造器装表；修复版改取真构造器 `00473A80` 里的 `00473A9B`（指令 `mov dword ptr [esi],0x7e16b0`）。已实测确认盘上该行含 `00473A9B`/`00473A80`/`mov dword ptr [esi], 0x7e16b0`，且不含旧值 `004014AC`/`004011C0`/`[esp + 0x20]`。
- 18 行均取自 `R16_SIEVE_D1_WIDE` 按用户 D-52 宽读口径筛出的 81 行集合里 65 行待做部分的第 19–36 行（`no_rows[18:36]`，与 B1 前 18 行交集为 0）。

## 2. 写盘哈希
| 文件 | BEFORE sha256 | AFTER sha256 |
|---|---|---|
| coverage.tsv | `65E9CF2B3E778E98EF929D00F83BE61A4FF111D4E1C028DD26809B557F67D8A7`（4,108,800 B） | `89EDBD91E5EC5D4D72954CBC2251DF5292090D624137DFD3C193ABE5E260D919`（4,119,324 B） |
| PANEL.md | `E5E3E31A99A5C723F649839E9FD8D5D82E2733A90C2CBDDFB05DDDF628733625E`（193,197 B） | `F069339CD29C1E50CBC0B44795640752B21C63A1CF82092002599BA82E2677F9`（196,867 B） |

> 注：B2 delta / 审计报告的「coverage 未改 sha `412ED7E3…`」是其开工时截面（B1 并表前）。本并表员开工实测盘上为 `65E9CF2B…`（= B1 并表 AFTER），以此为 pin 与改前基准；所有数字以此实值为准，未推算。

## 3. 逐项验证（①–⑨，全部 PASS，详见 `VERIFY_RESULT.json`）
| 项 | 结果 | 要点 |
|---|---|---|
| ① 18 行第 4 列严格前缀 | PASS | 18/18 `新第4列 == 合并 delta 第4列` 且以盘上原第 4 列为严格前缀（纯追加 ④）；盘上原 18 行 `④` 计数全 0 |
| ② 逐字节还原性 | PASS | pin + before_col4：18 行第 4 列换回原值后 sha == 改前（`65E9CF2B…`）；独立脚本 `REVERSIBILITY_PROOF.txt` 同证 |
| ③ 不变量 | PASS | 18,498 行 / `{8:18498}` / `[已证]` 1,654 / atlas 内 1,648 / 外 6（改前改后同） |
| ④ 仅 18 行第 4 列变 | PASS | 非目标行逐字节相同；18 行第 1/2/3/5/6/7/8 列逐字节同、grade 未改（全 `[已证]`） |
| ⑤ 口径 A/B 实测 | PASS | A：412→430（+18，24.91%→26.00%）；B：245→263（+18，14.81%→15.90%）；18 行改前含 `④` 计数全 0，实测非推算 |
| ⑥ §12.6 命中数 | PASS | 命中行 188→206（+18）、命中次数 220→238（+18） |
| ⑦ PANEL 还原性 | PASS | 插 9 行（M100，L305–L313，紧接 M99 块 L297–L304 之后、M77 并表实算说明之前）；移除后逐字节 == 改前；M99 块 8 行逐字不变、既有内容零删除零改字 |
| ⑧ 达标未翻转 | PASS | `strict_panel_local.py`（权威口径、输出本目录）：名义仍 S15/S16/S17、严格仍 S17；proved 1,648 / proved_strict 1,331 不变 |
| ⑨ 行尾不混用 | PASS | coverage LF=18,498（无末尾 LF）、PANEL LF=699（690+9）、两者 CRLF=0/lone CR=0/无 BOM |

## 4. M100 披露要点（PANEL L305–L313，9 行）
1. 本批 18 行取自 `R16_SIEVE_D1_WIDE` 按用户 D-52 宽读口径筛出的 81 行集合里 65 行待做部分的第 19–36 行。
2. 异族审计判 1 行（`00473B10`）FAIL（唯一失败形态＝栈临时写被当构造器装表，C/D 两项不过），已由 `R16_FIX_B2_1ROW` 改取真构造器 `00473A80` 的 `00473A9B` 后并入；A/B/E/F 四项 0 不合格。
3. 根因入账：vt `007E16B0` 共 185 个装表点、仅 5 个真 `this` 目标，`derive_raw.py:160` 的 `site=es[0]` 最低地址命中丢弃了 5 个真 this 目标，是该启发式的典型风险；G1–G5 宿主身份校验规则已落实。
4. 审计另确认本批 5 行 CLASS_FIX 全部成立（5/5）。
5. 数字用实测：A 412→430、B 245→263、§12.6 行 188→206 / 次 220→238、不变量同上。

## 5. 产物（本目录）
`_pin_coverage.tsv` / `_pin_PANEL.md` / `before_col4.json` / `baseline.json` / `precheck.py` / `merge.py` / `MERGE_LOG.json` / `strict_panel_local.py` / `before_strict_panel_strict_panel.json` / `after_strict_panel_strict_panel.json` / `verify.py` / `VERIFY_RESULT.json` / `_reversibility_proof.py` / `REVERSIBILITY_PROOF.txt` / `_after_coverage.tsv` / `_after_PANEL.md` / `REPORT.md`（本文件）。
