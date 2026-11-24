# M80 MERGE_LOG — 3 行 name 更正（HYGIENE_R11 / YRpp 同址声明；非升降级）

## 一句话结论
并入 3 行的 **name 更正**：`004CC680` `MapClass::MapClass`→`TrajectoryHelper::IsCliffHit`、`0054E690` `Kamikaze::Kamikaze`→`KamikazeControl::~Kamikaze`、`004C6800` `NetworkEvents::FillEvent_Animation`→`NetworkEvent::FillEvent_Animation`（仅第 3 列改字 + 第 4 列末尾追加 M80 名更正句）。数据行数仍 18,498、8 列、TAB；全表 `[已证]` 1,654 / atlas 内 1,648 / atlas 外 6 均不变；3 行 grade 全仍 `[已证]`；named_L / named_S(R14) / named_strict 三列逐行与聚合均不变；**无达标翻转**。178 项自检全 PASS。

## 角色与边界
- 本轮唯一 COVERAGE 写者：agent-265。仅写 `COVERAGE\coverage.tsv`、`COVERAGE\PANEL.md` 与新建 `MERGE_M80\`。
- 未 git commit。
- 未碰：R14_COMMON / STATUS_BOARD / 台账 / BOARD_ARCHIVE / HYGIENE_R11 / PROBE_746 / 任何 R4_* / D47_SURFACE。
  - `HYGIENE_R11\rows.tsv` **只读**，未写。
  - atlas（`next_re_20261112_r10\W130_atlas\function_atlas.tsv`）与历史 MERGE 目录**只读**。

## 输入
| 文件 | 用途 | 状态 |
|---|---|---|
| `HYGIENE_R11\rows.tsv` | 11 行「全镜像 0 引用」行的同址声明证据（12 列） | 只读 |
| `COVERAGE\coverage.tsv` | 被更正目标（18,498 行 × 8 列） | 写（仅 3 行第 3 列、第 4 列追加） |
| `COVERAGE\PANEL.md` | 追加 M80 披露 | 写（插入 7 行） |
| `next_re_20261112_r10\W130_atlas\function_atlas.tsv` | atlas 归属判据（12,916 唯一 entry） | 只读 |

## 判据与口径（自己实测，不照抄派卡）
- 归一化 `ne()`：strip + upper + 去 `0X` + `%08X`（沿用 MERGE_M77/M79 verify.py）。
- `named_L` = name 非空且不以 `sub_` 开头。
- `named_S(R14)` = `named_L` 排除 `::sub_[0-9A-Fa-f]+$`（任意长度十六进制，M53 明确）。
- `named_strict` = `named_S(R14)` 排除 `::v?slot\d+$`（RULING_R15 / PANEL_CHK recalc.py 口径）。
- DoD 达标：每子系统 atlas_n 计 `named_S14 ≥ ceil(0.9·n)` 且（名义 proved / 严格 strict）`≥ ceil(0.5·n)`。
- strict 口径 = grade `[已证]` 且语义栏不含字面 `[未证]`（strict_panel.py:78）。

## 改前实测基线
| 项 | 值 |
|---:|---:|
| coverage 数据行 | 18,498（8 列，无 BOM、仅 LF、无末尾 LF） |
| 全表 `[已证]` | 1,654（atlas 内 1,648 / atlas 外 6） |
| 3 行改前 name | `MapClass::MapClass` / `Kamikaze::Kamikaze` / `NetworkEvents::FillEvent_Animation` |
| 3 行改前 grade | 全 `[已证]` |
| 3 行 HYGIENE_R11 判定 | 地址全部可信（`in_atlas=yes`、`looks_like_func=yes`、`prologue_within_16=none`、`real_func_start` 即 entry 本身），问题是名字与 YRpp 同址声明不符 |
| 其余 8 行 | 名字与 YRpp 同址声明一致（`NOVTABLE` 抽象类方法），未改 |

结论：3 行均为「地址可信、仅名不符」的名更正，非升降级。

## 执行
1. `capture_before.py` → 采集两文件 mtime/sha256/字节 → `_before_state.json`（coverage BEFORE sha256 `66830c3f…` 与 PANEL BEFORE sha256 `2317d26e…` 均与 MERGE_M79 记录的改后值一致，确认承接、无中间写者）。
2. `merge.py`：按 entry 定位 3 行，断言 subsystem/旧名/grade `[已证]` 全匹配后，仅置第 3 列为新名、第 4 列末尾追加 M80 句；断言第 1/2 列、第 4 列既有文字（纯追加）、第 5/6/7/8 列逐字不变；写回 coverage.tsv。PANEL.md 在 M79 披露块（L183–186）之后、M77 并表实算说明之前插入 M80 披露 7 行（新 L187–193）。
3. `write_before_after.py` → 采集 AFTER → `BEFORE_AFTER.txt` + `_after_state.json`。
4. `verify.py` → 全量复算 → `VERIFY.txt`。

## 改后核对（VERIFY.txt，178 PASS / 0 FAIL）
- **结构**：18,498 行 / 8 列 / TAB / 无 BOM / 仅 LF / 无末尾 LF（保持）。
- **3 行**：第 3 列 = 新名，第 4 列 = 原第 4 列 + M80 句（纯追加），grade 全仍 `[已证]`，第 1/2/5/6/7/8 列逐字未动；其余 18,495 行零变化。
- **强证据**：从 AFTER 去掉 3 行 M80 追加后缀并把第 3 列改回旧名，逐字节重建 BEFORE，sha256 = `66830c3f…` 精确等于改前记录 ⇒ 除 3 行第 3 列 + 第 4 列追加外无任何其他字节变化。
- **计数**：全表 `[已证]` 1,654、atlas 内 1,648、atlas 外 6（改前=改后）。
- **named 三列**：3 行旧名新名逐行判定均为 `(named_L, named_S14, named_strict) = (True, True, True)`，改前=改后；逐子系统 + TOTAL 聚合计数改前=改后（TOTAL named_L 7,210 / named_S14 7,203 / named_strict 1,372 全不变）。
- **特殊核**：`KamikazeControl::~Kamikaze`、`Kamikaze::Kamikaze`、`TrajectoryHelper::IsCliffHit` 三者均不匹配 `::sub_[0-9A-Fa-f]+$`、均不含 `::slotN`、均不匹配 `::v?slot\d+$`。
- **达标判定**：名义 S15/S16/S17、严格 S17，改前改后一致；**无翻转**。
- **PANEL**：M80 披露 7 行逐字一致，落点 L187–193（M79 披露 L183–186 之后、M77 实算说明 L194 之前）；行数 572 → 579；无 BOM / 仅 LF / 末尾换行保持。
- **BEFORE_AFTER**：两文件改前/改后 sha256 均已记录且可核。

## 差异说明
- 派卡给的三处新名与 `HYGIENE_R11\rows.tsv` 的 `yrpp@addr` 完全一致（MapClass.h:75 / Kamikaze.h:25 / NetworkEvents.h:60 的同址声明），**无差异**。
- 名更正不改变 named 判定：旧名（如 `Kamikaze::Kamikaze`）本就被 `named_S(R14)` 计为一个名字，新名亦然——这正暴露「错的 name 仍会被 `named_S(R14)` 计为一个名字」的数据质量风险（见 PANEL M80 披露）。

## 交付
`MERGE_M80\{MERGE_LOG.md, BEFORE_AFTER.txt, VERIFY.txt}`（另附 `capture_before.py` / `merge.py` / `write_before_after.py` / `verify.py` 与 `_before_state.json` / `_after_state.json` 供复核）。

## 最终一句话
3 行 name 已按 YRpp 同址声明更正；named 三列逐行与聚合均确实未变；无达标翻转。
