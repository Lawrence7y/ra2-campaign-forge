# M79 MERGE_LOG — 91 行 ④ 成文文档升级（非升格）

## 一句话结论
并入 `R4_FILL_91_R3\fill_delta.tsv` 的 **91 行**，仅改 `coverage.tsv` 第 4 列（语义栏原文 + 成文 ④ 句）与第 6 列（evidence_path 追加）；**grade 一字未动**（91 行本就 `[已证]`）。数据行数仍 18,498、8 列、TAB；全表 `[已证]` 1,654 / atlas 内 1,648 / atlas 外 6 均不变；「④ 已成文」实测 228 → 319（+91）；**无达标翻转**。502 项自检全 PASS。

## 角色与边界
- 本轮唯一 COVERAGE 写者：agent-261。仅写 `COVERAGE\coverage.tsv`、`COVERAGE\PANEL.md` 与新建 `MERGE_M79\`。
- 未 git commit。
- 未碰：R14_COMMON / STATUS_BOARD / 台账 / BOARD_ARCHIVE / 任何 R4_* / D47_SURFACE / NAMED_PUSH_* / AUDIT* / INVENTORY*。
  - `R4_FILL_91_R3\fill_delta.tsv` 与 `REPORT.md` **只读**，未写。
  - atlas（`next_re_20261112_r10\W130_atlas\function_atlas.tsv`）与历史 MERGE 目录**只读**。

## 输入
| 文件 | 用途 | 状态 |
|---|---|---|
| `R4_FILL_91_R3\fill_delta.tsv` | 91 行升级源（6 列：entry/subsystem/name/one_line_semantics/grade/evidence_path） | 只读 |
| `COVERAGE\coverage.tsv` | 被升级目标（18,498 行 × 8 列） | 写（仅 91 行第 4/6 列） |
| `COVERAGE\PANEL.md` | 追加 M79 披露 | 写（插入 4 行） |
| `next_re_20261112_r10\W130_atlas\function_atlas.tsv` | atlas 归属判据（12,916 唯一 entry） | 只读 |

## 判据与口径（自己实测，不照抄派卡）
- 归一化 `ne()`：strip + upper + 去 `0X` + `%08X`（沿用 MERGE_M77 verify.py）。
- ④ 已成文 = grade `[已证]` 且第 4 列含字符「④」（实测基线 **228**，与派卡一致；另试「④+空格」198、「④：」5、`④升级句` 0 等口径均不符 228，故取「含 ④」）。
- atlas 内/外 = entry 是否 ∈ function_atlas 唯一 entry 集。
- strict 口径 = `[已证]` 且语义栏不含字面 `[未证]`（`strict_panel.py:78`）。
- DoD 达标：每子系统 atlas_n 计 `named_S14 ≥ ceil(0.9·n)` 且（名义 proved / 严格 strict）`≥ ceil(0.5·n)`。

## 改前实测基线（analyze.py / 盘上 BEFORE）
| 项 | 值 |
|---|---:|
| coverage 数据行 | 18,498（8 列，无 BOM、仅 LF、无末尾 LF） |
| 全表 `[已证]` | 1,654 |
| atlas 内 / 外 `[已证]` | 1,648 / 6 |
| ④ 已成文 | 228（13.78%） |
| delta 数据行 | 91（6 列，grade 全 `[已证]`，entry 唯一） |
| 91 行命中 coverage | 91/91（唯一）；subsystem/name/grade 三项全一致 |
| delta 第 4 列起始 = coverage 第 4 列 | 91/91（纯追加） |
| coverage 第 4 列改前含 ④ | 0/91 |
| delta 第 6 列起始 = coverage 第 6 列 | 91/91（纯追加） |

结论：91 行均为「原文 + 追加」纯文档升级，无升格、无新行。

## 执行
1. `capture_before.py` → 采集两文件 mtime/sha256/字节 → `_before_state.json`（coverage BEFORE sha256 `299aa732…` 与 MERGE_M78 记录的 coverage 改后值一致，确认承接、无中间写者）。
2. `merge.py`：按 entry 定位 91 行，仅置第 4/6 列为 delta 值；断言第 1/2/3/5/7/8 列逐字不变；写回 coverage.tsv。PANEL.md 在 M78 披露块（原 L178–182）之后、M77 并表实算说明之前插入 M79 披露 4 行。
3. `write_before_after.py` → 采集 AFTER → `BEFORE_AFTER.txt` + `_after_state.json`。
4. `verify.py` → 全量复算 → `VERIFY.txt`。

## 改后核对（VERIFY.txt，502 PASS / 0 FAIL）
- **结构**：18,498 行 / 8 列 / TAB / 无 BOM / 仅 LF / 无末尾 LF（保持）。
- **91 行**：第 4 列 = delta 第 4 列、第 6 列 = delta 第 6 列；grade 全 `[已证]`；第 1/2/3/5/7/8 列逐字未动；④ 从无到有；其余 18,407 行零变化。
- **强证据**：从 AFTER 去掉 91 行追加后缀逐字节重建 BEFORE，sha256 = `299aa732…` 精确等于改前记录 ⇒ 除第 4/6 列外无任何其他字节变化。
- **计数**：全表 `[已证]` 1,654、atlas 内 1,648、atlas 外 6（改前=改后）；91 行 `[未证]` 字面 presence 改前=改后（strict 不受影响）。
- **④ 已成文**：228 → 319（13.78% → 19.29%），恰 +91。
- **达标判定**：名义 S15/S16/S17、严格 S17，改前改后一致；**无翻转**。
- **PANEL**：M79 披露 4 行逐字一致，落点 L183–186（M78 披露 L178–182 之后、M77 实算说明之前）；行数 568 → 572。
- **BEFORE_AFTER**：两文件改前/改后 sha256 均已记录且可核。

## 差异说明
- 派卡给基线 228 与实测一致，**无差异**。
- M78 披露中的 1,347 行（81.4%）是 D47_SURFACE 按证据来源 F4 分类的「④ 未成文」数，与本表「第 4 列含 ④」的字面判据不同量纲，不冲突：本轮按派卡指定判据实测 228，只升级其中机械可补的 91 行（848 行 `name_only_no_ring4` 的子集）。

## 交付
`MERGE_M79\{MERGE_LOG.md, BEFORE_AFTER.txt, VERIFY.txt}`（另附 `analyze.py`/`capture_before.py`/`merge.py`/`write_before_after.py`/`verify.py` 与 `_before_state.json`/`_after_state.json` 供复核）。

## 最终一句话
并行数 91；「④ 已成文」由基线 228 → 319；无达标翻转。
