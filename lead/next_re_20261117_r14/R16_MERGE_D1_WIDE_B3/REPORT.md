# R16-MERGE-D1-WIDE-B3 · 并表报告

> 角色：合并员（agent-72）· 本轮唯一 `COVERAGE/coverage.tsv` 与 `COVERAGE/PANEL.md` 写者。
> 写域：仅 `COVERAGE\coverage.tsv`（17 行第 4 列）、`COVERAGE\PANEL.md`（插入 1 条 M101 披露），以及本目录 `R16_MERGE_D1_WIDE_B3\`。未改 R14_COMMON/台账/看板/_drafts/_cards，卡目录只读，未做逆向，`strict_panel.py` 副本输出本目录。
> 表头逗号分隔，数据行 TAB 分隔（8 列），已注意。

## 0. 结论

**18 行里实并 17 行，`005F4B10` 按 Lead 裁定 + 异族审计复核剔除且盘上原样未动；10 项验证全 PASS。**

| 项 | 结果 | 证据摘要 |
|---|---|---|
| ① 17 行第 4 列严格前缀 | PASS | 17/17，新第 4 列 == delta 第 4 列且以盘上原值严格为前缀 |
| ② 005F4B10 未被改动 | PASS | line 7046 整行与第 4 列逐字节同；`ObjectClass slot65 wrapper (consumes NeedsRedraw)` |
| ③ 逐字节还原性 | PASS | 17 行第 4 列换回 `before_col4` 后 sha == 改前 `89edbd91…`，逐字节相等 |
| ④ 不变量 | PASS | 18,498 / `{8:18498}` / `[已证]` 1,654 / atlas 内 1,648 / 外 6 |
| ⑤ 只有 17 行第 4 列变 | PASS | 其余列逐字节同、grade 未变；非目标行整行逐字节同（含 005F4B10 行） |
| ⑥ 口径 A/B 实测 | PASS | A 430→447（+17，26.00%→27.03%）；B 263→280（+17，15.90%→16.93%）；改前以 pin 实值为准 |
| ⑦ §12.6 命中数 | PASS | 命中行 206→223（+17），命中次数 238→255（+17） |
| ⑧ PANEL 还原性 | PASS | 移除 9 行 M101 后 sha == pin `f069339c…`，既有行零改字；M100 块逐字完好 |
| ⑨ 达标未翻转 | PASS | 名义 S15/S16/S17、严格 S17（改前改后同）；total proved/strict 1,648/1,331 不变 |
| ⑩ 行尾不混用 | PASS | coverage LF=18,498（无末尾 LF）、PANEL LF=708=699+9，二者 CRLF=0、孤立 CR=0、无 BOM |

## 1. 改前 / 改后截面（实测）

| 文件 | 改前 sha256 / bytes | 改后 sha256 / bytes |
|---|---|---|
| coverage.tsv | `89edbd91e5ec5d4d72954cbc2251df5292090d624137dfd3c193abe5e260d919` / 4,119,324 | `b84d53dd046c71c15a36d3425981974a227175cb09e0f8e1a8d7fcebc1d3527f` / 4,129,477 |
| PANEL.md | `f069339cd29c1e50cbc0b44795640752b21c63a1cf82092002599ba82e2677f9` / 196,867 | `5a5a6742d44ec974346bf08721b1936f97271b22ace722cfb3a18def281a55a6` / 201,071 |

- delta 来源：`R16_D1_WIDE_B3/delta.tsv`（18 行，sha `b1d04648940fed8e1a31b56f7520cb2b665b1eb8476f822d3c6fbd7c1c87d8a4`），排除 `005F4B10` 后取 17 行第 4 列照抄。
- `005F4B10`：line 7046，改前/改后第 4 列均为 `ObjectClass slot65 wrapper (consumes NeedsRedraw)`，整行逐字节同，未并入任何 ④。

## 2. 排除 `005F4B10` 的依据（Lead 裁定 + 异族审计复核）

- ② 审计原文 `C06_census/_audit/VERDICT.md:15` 只写 `005F4B10 <- BuildingLightClass vt 007E3AD0 slot 65`，全文不含 `ObjectClass`；`verdict_polarity=NEG`。
- 该 entry 在 slot65 被 16 张表共有，无任何 ② 产物支持归到 `ObjectClass`。
- 其 ④ 字节**为真**（`007EF060` slot65 确为该 entry，RTTI `.?AVObjectClass@@`），所以排除理由是「**这行不该在集合里**」，不是「④ 写错」。
- 异族审计 `R16_AUDIT_D1_WIDE_B3/AUDIT_REPORT.md` §5.2 独立复核成立，结论 17 PASS / 0 FAIL / 1 WITHDRAW。

## 3. M101 披露要点（已写入 PANEL，紧接 M100 块之后）

1. 取自 D-52 宽读 81 行集合里 65 行待做部分的第 37–54 行，1 行（`005F4B10`）剔除，实并 17 行。
2. 剔除理由（② 审计原文指向 BuildingLightClass、极性 NEG、该 entry 被 16 张表共有而无 ② 支持归 ObjectClass；其 ④ 字节为真，剔除的是「行不该在集合里」）。
3. 6 行 SITE_FIX（4 行 RawFileClass 与 2 行 CDFileClass 的决定性装表点实为析构器或栈临时写，已改真构造器）经审计 6/6 成立。
4. 2 行 CLASS_FIX 中 `00631CC0` 成立、`005F4B10` 撤回。
5. 审计另如实指出：④ 正文在「slot 也归一」后只有 12/18 互异（4 组同 class/同 vt/同装表点、仅差 slot 与 entry）——事实同源非抄袭，判通过；未声称「slot 归一后仍 18/18 不同」。
6. 数字全部实测（口径 A/B、§12.6 等）。

## 4. 产物清单（均在本目录 `R16_MERGE_D1_WIDE_B3\`）

`precheck.py` / `_pin_coverage.tsv` / `_pin_PANEL.md` / `before_col4.json` / `baseline.json` / `strict_panel_local.py` / `before_strict_panel.json` / `after_strict_panel.json` / `merge.py` / `_after_coverage.tsv` / `_after_PANEL.md` / `MERGE_LOG.json` / `verify.py` / `VERIFY_RESULT.json` / `_reversibility_proof.py` / `REVERSIBILITY_PROOF.txt` / `REPORT.md`（本文件）。
