# R16-MERGE-D1-WIDE-B4 合并报告（收官批）

> 角色：合并员（agent-74）· 任务：把 D1 宽读集合 B4 批（11 行）并入 COVERAGE/coverage.tsv；PANEL 插入 1 条 M102 披露。
> 写域：`COVERAGE\coverage.tsv`（仅 11 行第 4 列）、`COVERAGE\PANEL.md`（仅插入 1 条 M102）、本目录 `R16_MERGE_D1_WIDE_B4\`。未写 R14_COMMON/台账/看板/_drafts/_cards/卡目录；未做逆向。

## 0. 一句话结论
9 项验证全 PASS（①–⑨）；coverage.tsv 与 PANEL.md 均通过 pin + before_col4/插入位置的逐字节还原性自证；达标判定未翻转。

## 1. 数据来源与写域
- 输入：`R16_D1_WIDE_B4/delta.tsv`（11 行，第 4 列照抄）；异族审计 `R16_AUDIT_D1_WIDE_B4` 判 11 PASS / 0 FAIL / 0 必改。
- coverage.tsv：表头逗号分隔、数据行 TAB 分隔；只改 11 行第 4 列，其余 7 列逐字节不动、grade 未改 `[已证]`。
- PANEL.md：紧接 M101 块（L314–L322）之后插入 1 条 M102 披露（L323–L331，共 9 行），既有内容零删除零改字。

## 2. 逐项验证（PASS/FAIL，实测非推算）
| 项 | 内容 | 结果 | 实测要点 |
|---|---|---|---|
| ① | 11 行第 4 列以盘上原第 4 列为严格前缀 | **PASS** | 11/11 严格前缀；新第 4 列 == delta 第 4 列 |
| ② | 逐字节还原性（11 行第 4 列换回改前原值后 sha == 改前） | **PASS** | pin sha `b84d53dd…` == rev sha；逐字节相等；独立脚本 `REVERSIBILITY_PROOF.txt` 同证 |
| ③ | 不变量 18,498 / {8:18498} / [已证] 1,654 / atlas 内 1,648 / 外 6 | **PASS** | 四项全部实测命中，改前改后相同 |
| ④ | 只有 11 行第 4 列变、其余列逐字节同、grade 未变 | **PASS** | 非目标行全等；11 行其余 7 列逐字节同、grade 未改 |
| ⑤ | 口径 A/B 实测改前改后 | **PASS** | A 447→458（+11）、B 280→291（+11），均为盘上实读；11 行改前 A/B 计数全 0 |
| ⑥ | §12.6 命中数变化 | **PASS** | 命中行数 223→234（+11）、命中次数 255→266（+11） |
| ⑦ | PANEL 还原性 | **PASS** | 移除 9 行插入后 rev sha == pin sha；M101 块逐字节未动；锚点 M101/M102/M77 就位 |
| ⑧ | 达标未翻转 | **PASS** | strict_panel 权威口径：名义仍 S15/S16/S17、严格仍 S17；proved 1648 / strict 1331 改前改后相同 |
| ⑨ | 行尾不混用 | **PASS** | coverage LF=18498（无末尾 LF）、PANEL LF=717（=708+9）、均 0 CRLF/0 lone CR/无 BOM |

## 3. 口径 A/B 与 §12.6（实测值）
- 口径 A（[已证] 且第 4 列含 `④`）：447/1654（27.03%）→ 458/1654（27.69%），净 +11。
- 口径 B（[已证] 且第 4 列含 `④ 活表槽位见证`）：280/1654（16.93%）→ 291/1654（17.59%），净 +11。
- §12.6（第 4 列字面 `§12.6`）：命中行 223→234（+11）、命中次数 255→266（+11）。

## 4. sha / bytes
| 文件 | 改前 sha256 | 改后 sha256 | 改前 bytes | 改后 bytes |
|---|---|---|---:|---:|
| coverage.tsv | `b84d53dd046c71c15a36d3425981974a227175cb09e0f8e1a8d7fcebc1d3527f` | `a07a74c173286b4d2163831022f1498f9ee903f44690702c90d05edea6d1c40c` | 4,129,477 | 4,136,525 |
| PANEL.md | `5a5a6742d44ec974346bf08721b1936f97271b22ace722cfb3a18def281a55a6` | `9a0be87e9bdde277e08b7145989bca132c6b253cd193034c205ea79dd848c1c9` | 201,071 | 205,207 |

## 5. M102 披露五件事（已写入 PANEL L323–L331）
1. 收官批：D-52 宽读集合 81 行 → 16 跳过 → 65 待做；B1 18 + B2 18 + B3 17 + B4 11 = 64 行已并，另 1 行 `005F4B10` 经裁定剔除，64+1=65 闭合。
2. 异族审计 11 PASS / 0 FAIL / 0 必改。
3. 两条事实订正留痕：M2「非最低地址命中 006F450D」与字节相反（实际 006F3130 最低且真构造器、006F450D 最高且析构器；结论对措辞错）；M1「11 行 = 65−18−18−18−1」为虚设步骤（005F4B10 已在 B3 18 行内，65−54=11 已成立，再减 1 得 10）。
4. 方法论保留：宿主身份校验实为手填 forced_host + 形态匹配、缺 `host ≤ site < fn_end(host)` 位置断言；审计独立求宿主后事后追认一致，方法不是真校验 —— 对整个 D1-WIDE 系列入账。
5. 数字用实测：A 447→458、B 280→291、§12.6 223→234 / 255→266。

## 6. 产物
`precheck.py` / `_pin_coverage.tsv` / `_pin_PANEL.md` / `before_col4.json` / `baseline.json` / `strict_panel_local.py` / `before_strict_panel.json` / `after_strict_panel.json` / `merge.py` / `_after_coverage.tsv` / `_after_PANEL.md` / `MERGE_LOG.json` / `verify.py` / `VERIFY_RESULT.json` / `_reversibility_proof.py` / `REVERSIBILITY_PROOF.txt` / `REPORT.md`（本文件）。
