# R16-MERGE-D1-WIDE-B1 — D1 宽读 B1 批 18 行并表 + M99 披露

- 写者：agent-70（本轮 `coverage.tsv` / `PANEL.md` 唯一写者）
- 写域：`COVERAGE\coverage.tsv`（18 行第 4 列）、`COVERAGE\PANEL.md`（插入 1 条 M99）、本目录 `R16_MERGE_D1_WIDE_B1\`（产物）。未碰 R14_COMMON / STATUS_BOARD / 台账 / 看板 / `_drafts` / `_cards` / 任何卡目录；卡目录只读；未做逆向。

## 1. 本批来源与第 4 列取值
- **16 行**：第 4 列取 `R16_D1_WIDE_B1\delta.tsv`（异族审计 `R16_AUDIT_D1_WIDE_B1/VERDICT.md` 判 16/18 PASS，A/B/D/E/F 五项 0 不合格）。
- **2 行**（`004322A0` / `004324B0`）：第 4 列取 `R16_FIX_B1_2ROWS\delta.tsv`（修复版，替换 B1 旧 ④）。旧版把栈临时写 `mov [esp+0x20],0x7e1668`（装表点 `004014C4`，宿主 `004011C0`，与 scalar deleting destructor `004019A0` 逐指令同构）误当构造器装表；修复版改取真构造器 `0047AA3C`（宿主 `0047AA30`，指令 `mov [esi],0x7e1668`）。已实测确认最终盘上两行含 `0047AA3C`/`0047AA30` 且不含旧值。
- 18 行均取自 `R16_SIEVE_D1_WIDE` 按用户 D-52 宽读口径筛出的 81 行集合里 65 行待做部分的前 18 行（按 entry 升序）。

## 2. 写盘哈希
| 文件 | BEFORE sha256 | AFTER sha256 |
|---|---|---|
| coverage.tsv | `412ED7E36BC1AD4907763FEBB3A68D5FDABB3F0D2C999800444B57098B1AB2E1`（4,097,787 B） | `65E9CF2B3E778E98EF929D00F83BE61A4FF111D4E1C028DD26809B557F67D8A7`（4,108,800 B） |
| PANEL.md | `EC1715561FBB952B79FFD246EE1790FCE24E4F242498DCC4AFD3F488DB16FF8F`（190,122 B） | `E5E3E31A99A5C723F649839E9FD8D5D82E2733A90C2CBDDFB05DDDF628733625E`（193,197 B） |

## 3. 逐项验证（①–⑨，全部 PASS，详见 `VERIFY_RESULT.json`）
| 项 | 结果 | 要点 |
|---|---|---|
| ① 18 行第 4 列严格前缀 | PASS | 18/18 `新第4列 == 合并 delta 第4列` 且以盘上原第 4 列为严格前缀（纯追加 ④） |
| ② 逐字节还原性 | PASS | pin + before_col4：18 行第 4 列换回原值后 sha == 改前（`412ED7E3…`）；独立脚本 `REVERSIBILITY_PROOF.txt` 同证 |
| ③ 不变量 | PASS | 18,498 行 / `{8:18498}` / `[已证]` 1,654 / atlas 内 1,648 / 外 6 |
| ④ 仅 18 行第 4 列变 | PASS | 非目标行逐字节相同；18 行第 1/2/3/5/6/7/8 列逐字节同、grade 未改（全 `[已证]`） |
| ⑤ 口径 A/B 实测 | PASS | A：394→412（+18，23.82%→24.91%）；B：227→245（+18，13.72%→14.81%）；18 行改前含 `④` 计数全 0，实测非推算 |
| ⑥ §12.6 命中数 | PASS | 命中行 170→188（+18）、命中次数 202→220（+18） |
| ⑦ PANEL 还原性 | PASS | 插 8 行（M99，L297–L304，紧接 M98 块 L290–L296 之后、M77 说明之前）；移除后逐字节 == 改前；M98 块 7 行逐字不变、既有内容零删除零改字 |
| ⑧ 达标未翻转 | PASS | `strict_panel_local.py`（权威口径、输出本目录）：名义仍 S15/S16/S17、严格仍 S17；proved 1,648 / proved_strict 1,331 不变 |
| ⑨ 行尾不混用 | PASS | coverage LF=18,498（无末尾 LF）、PANEL LF=690（682+8）、两者 CRLF=0/lone CR=0/无 BOM |

## 4. M99 披露要点（PANEL L297–L304，8 行）
1. 本批 18 行取自 `R16_SIEVE_D1_WIDE` 按用户 D-52 宽读口径筛出的 81 行集合里 65 行待做部分的前 18 行。
2. 异族审计判 2 行（`004322A0`/`004324B0`）C 项 FAIL（栈临时写被当构造器装表），已由 `R16_FIX_B1_2ROWS` 改取真构造器 `0047AA3C` 后并入。
3. 根因如实写明：原 `generate.py` 的 `install_form`（`generate.py:82-88`）只看操作数形态、不校验宿主身份（装表点又继承最低地址命中）；已在后续批次用 G1–G5 宿主身份校验规则（`R16_FIX_B1_2ROWS/host_rule.py`）落实。
4. 数字用实测：A 394→412、B 227→245、§12.6 行 170→188 / 次 202→220、不变量同上。

## 5. 产物（本目录）
`_pin_coverage.tsv` / `_pin_PANEL.md` / `before_col4.json` / `baseline.json` / `precheck.py` / `merge.py` / `MERGE_LOG.json` / `strict_panel_local.py` / `before_strict_panel_strict_panel.json` / `after_strict_panel_strict_panel.json` / `verify.py` / `VERIFY_RESULT.json` / `_reversibility_proof.py` / `REVERSIBILITY_PROOF.txt` / `REPORT.md`（本文件）。
