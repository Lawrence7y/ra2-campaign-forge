# M59 MERGE LOG — 并表 S15S16_3B2 审计 PASS 7 行

## 范围与独占写权

- 本卡（M59-MERGE）为唯一 COVERAGE 写者；只写 `COVERAGE/coverage.tsv` 与 `COVERAGE/PANEL.md`，交付写在 `MERGE_M59/`。
- 未 git commit；未碰 `R14_COMMON.md`、`STATUS_BOARD.md`、`CONFLICTS.tsv`、`PENDING_CORRECTIONS.tsv`、任何 `SEMFIX_ENGFAM_B*` 目录。
- 未改 name/subsystem、第 1/2/3/7/8 列；未新增/删除数据行；未重排、未美行。

## 改动前核对（全部与卡片一致，无停下理由）

盘上改前实测：
- `coverage.tsv` 数据行 **18,498**，8 列 TAB 分隔、纯 LF、无末尾换行，表头逗号分隔 8 字段。
- 全表 `[已证]` **1,489**；atlas 内 `[已证]` **1,484**；atlas 外 `[已证]` **5**（与 PANEL M58 段一致）。
- S15 atlas 内 proved **101**、proved_strict **48**；S16 proved **46**、proved_strict **20**（与面板严格口径双列表一致）。
- 审计表 `S15S16_3B2/_audit/verdict.tsv`：11 行数据、7 列，裁 **PASS 7 / FAIL 4**；PASS 集合与卡片逐字一致。
- 两张 delta：`S15_delta.tsv` 10 行、`S16_delta.tsv` 1 行，合计 11 行；7 个 PASS entry 全部在两 delta 内，且盘上 grade 全为 `[静态推断]`。
- `006E6080` 不在 `function_atlas.tsv`（大小写归一比对）；其余 6 个 PASS entry 均在 atlas 内。

## 交叉核对 PASS 集合（= 7 行）

以 verdict.tsv（第 2 列 `verdict`）与两张 delta 交叉核出，恰 **7 行**：

| entry | subsystem | delta 中的 name | atlas 内? |
|---|---|---|---|
| 006E3DB0 | S15 | TActionClass::slot5 | 是 |
| 006E4660 | S15 | TActionClass::slot8 | 是 |
| 006E5730 | S15 | TagClass::slot5 | 是 |
| 006E6080 | S15 | TagTypeClass::slot25 | **否** |
| 006E6410 | S15 | TagTypeClass::slot5 | 是 |
| 00727240 | S15 | TriggerTypeClass::slot25 | 是 |
| 006CE800 | S16 | SuperWeaponTypeClass::slot5 | 是 |

FAIL 4 行（`006E3E30`/`006E56E0`/`006E57A0`/`007276A0`）整行拒绝，一个字未改，grade 仍 `[静态推断]`（见 VERIFY.txt L31–L35）。

## coverage.tsv 改动

仅对上表 7 行、仅改 3 列：
1. 第 4 列 `one_line_semantics` ← 对应 delta 第 4 列**原文照抄**（逐字，无截断/改写；7 行原文均无「未证」字样）。
2. 第 5 列 `grade`：`[静态推断]` → `[已证]`。
3. 第 6 列 `evidence_path` → `S15S16_3B2/_audit/VERDICT.md`。

第 1/2/3/7/8 列逐字节不变（脚本内以原行 split 后逐列断言）。改后：数据行仍 **18,498**、仍 8 列 TAB 分隔、表头与末尾形态不变。逐行 entry 与改前后只变 3 列的事实由 `merge_cov.py` 内断言 + `VERIFY.txt` 复核。

## PANEL.md 改动

按「S15 与 S16 的各类行同步」逐行定位（三类面板表各一处 S15/S16 行；TOTAL 一处）。参照 M58「三处 S09 C 行同步」先例，各处只改点名单元格：

**表 1 · 覆盖面板（A 分母，L69/L70/L77）**
- L69 S15：proved_n `101`→`106`、proved_pct `63.92`→`67.09`（实算 106/158=67.0886%→67.09）；备注列追加 M59 说明。
- L70 S16：proved_n `46`→`47`、proved_pct `51.11`→`52.22`（实算 47/90=52.2222%→52.22）；备注列追加 M59 说明。
- L77 TOTAL：atlas 内 proved `1,484`→`1,490`、proved_pct `11.49`→`11.54`（实算 1,490/12,916=11.5361%→11.54）；备注列前置 M59 +7 计数段（全表 1,489→1,496、atlas 内 1,484→1,490、atlas 外 5→6）并追加 M59 说明。
- 备注列追加的统一文字（卡片原文）：`M59 并表 S15S16_3B2 审计 PASS 7 行（S15 006E3DB0/006E4660/006E5730/006E6080/006E6410/00727240 + S16 006CE800，[静态推断]→[已证]，语义取 delta 原文、evidence_path 改指 S15S16_3B2/_audit/VERDICT.md；同卡 4 行 006E3E30/006E56E0/006E57A0/007276A0 审计 FAIL 整行拒绝；006E6080 不在 atlas 故 A 口径仅 +6）`

**表 2 · 严格口径双列表（L119/L120）**
- L119 S15：proved `101`→`106`、pct `63.92`→`67.09`、proved_strict `48`→`53`、strict_pct `30.38`→`33.54`（实算 53/158=33.5443%→33.54）；门槛 79 不变、名义「达标」不变、严格列「—」不变（53 < 79，差 26）。
- L120 S16：proved `46`→`47`、pct `51.11`→`52.22`、proved_strict `20`→`21`、strict_pct `22.22`→`23.33`（实算 21/90=23.3333%→23.33）；门槛 45 不变、名义「达标」不变、严格列「—」不变（21 < 45，差 24）。

**表 3 · M47 复算表（L183/L184，proved_n 列）**
- L183 S15：proved `101`→`106`；L184 S16：proved `46`→`47`。其余列（named/atlas_n/门槛/达标）不动。

**末尾新增小节 `## M59 并表说明`（L505 起）**，写明：
- 6 个 S15 PASS 行中 `006E6080` 在 atlas 外（只进全表、不进 A 分母，故 A 口径仅 +6）。
- 4 行 FAIL 的 entry 与一句话原因（逐字照抄 verdict.tsv 第 7 列 `reason`）。
- ③b② 通道基础率实测 28.05%（S15 45.45%、S16 7.89%；据 `S15S16_3B2/base_rate.tsv`），审计随后把 11 行的虚报率打到 4/11 = 36.4%，故该通道剩下的池很小。

> 说明：卡片「A 分母口径只 +6」按盘上口径执行 —— atlas_n（A=12,916）不动，atlas 内 `[已证]` 只 +6（S15 +5、S16 +1），`006E6080` 只让全表 `[已证]` +1、atlas 外已证 5→6。

## 并表后实测值（全部通过，见 VERIFY.txt）

- 数据行 **18,498**，8 列 TAB，表头/末尾形态不变。
- 全表 `[已证]` **1,496**（+7）；atlas 内 `[已证]` **1,490**（+6）；atlas 外 `[已证]` **6**（+1）。
- grade 直方图：`[未证]` 11,024 / `[静态推断]` 5,978 / `[已证]` 1,496（合计 18,498）。
- S15：atlas 内 proved **106**、proved_strict **53**。S16：atlas 内 proved **47**、proved_strict **21**。
- 7 行 PASS：grade 全 `[已证]`、evidence_path 全 `S15S16_3B2/_audit/VERDICT.md`、第 4 列全等于 delta 原文。
- 4 行 FAIL：grade 全仍 `[静态推断]`（未变）。

## 交付文件

- `MERGE_M59/MERGE_LOG.md`（本文件）
- `MERGE_M59/BEFORE_AFTER.txt`（两文件改前/改后 mtime、字节数、SHA-256 对照）
- `MERGE_M59/VERIFY.txt`（并表后重算：数据行数、全表/atlas 内/atlas 外 `[已证]`、S15/S16 `[已证]` 数、7 行新 grade、4 行 FAIL grade 未变 —— 全 PASS）
