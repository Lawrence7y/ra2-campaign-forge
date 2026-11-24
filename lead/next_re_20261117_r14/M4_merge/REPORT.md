# M4 合并报告 — 修 M3 审计 PARTIAL 的 5 处缺陷

被审 `M3_merge/_audit/VERDICT.md` 裁决 PARTIAL；本卡逐项修 5 缺陷。所有 `COVERAGE/` 文件已改盘，未 git commit。备份在 `M4_merge/_backup/`，复核脚本 `analyze.py` / `verify_panel.py`，落盘脚本 `apply_all.py`。

## 总览（前→后）
- `coverage.tsv` 数据行 **18,436 → 18,431**（-5）；grade **已证 1,281→1,278**、**静态推断 6,093→6,091**、未证 11,062 不变。
- `probe_and_data_entries.tsv` **130 → 132**；`probe ∩ coverage` **3 → 0**。
- `PENDING_CORRECTIONS.tsv` **86 → 105**（+19 = 5 改判 + 14 归一）。
- `UNSOURCED_PROVED.tsv` 理由句 **0→41 行**改写（见 §3）。
- `PANEL.md` 逐 S atlas_n **13 处**改正（见 §4），三列百分比全表复算。

## 1. 删/修正 5 条「非函数入口」行（移入 probe，非删除）
独立测距复核：`entry − 宿主函数入口 < size`，5 条全部落在已知函数体内，**无反驳**。注意派卡表把 `0043F2AE`/`0043F218` 的偏移写反，实算 F218=+152、F2AE=+302（两者均体内，结论不变）。

| entry | 宿主函数(size) | 实算偏移 | 原 grade | PENDING 登记 |
|---|---|---:|---|---|
| `0043F218` | 0x43F180(2443) | +152 | 已证 | ✓ |
| `0043F2AE` | 0x43F180(2443) | +302 | 已证 | ✓ |
| `0043F678` | 0x43F180(2443) | +1272 | 已证 | ✓ |
| `0047C878` | 0x47C620(1116) | +600 | 静态推断 | ✓ |
| `005684B1` | 0x5683C0(1068) | +241 | 静态推断 | ✓ |

处理：5 行从 `coverage.tsv` 移出；3 行（F218/F2AE/F678）原已在 probe（W176_place81，kind=internal_label），补 note 注明宿主+偏移；2 行（C878/684B1）新增 probe 行，`kind=internal_label`，并修正 `005684B1` 原 `S12-K2 FEED_W177D.md` 空格笔误为 `S12-K2/FEED_W177D.md`。改判为 `entry_kind=函数体内标签` 登记 PENDING 5 条（88–92 行）。

## 2. 修 probe ∩ coverage = 3 的重叠
自算 `probe.entry ∩ coverage.entry` = 3：**`0043F218`/`0043F2AE`/`0043F678`**。判定依据：三者 probe 端 `kind=internal_label`、来源 W176_place81，coverage 端名称（`BuildingClass::CanPlace_slot1`/`CellClass::CanPlacePerCell_call_site`/`BuildingClass::CanPlace_slot2`）均为 0x43F180 函数体内部标签 —— **属非函数条目**，故「留 probe、删 coverage」，与 §1 一致。处理后 `probe ∩ coverage = 0`。

## 3. 改 `UNSOURCED_PROVED.tsv` 41 行理由句
41/41 行 `why_unsourced` 含矛盾句「任何 delta 均未断言 `[已证]`」全部改写，grade/entry 未动，CRLF 行尾保留（42 个 CRLF 不变）。
- 改前：`审计 audit7.json promotion_41：任何 delta 均未断言 [已证]，sub=S13，sem=returns 0x160 (352)；`
- 改后：`审计 audit7.json promotion_41：该行原 [已证] 缺可核来源，已降 [未证]；如需恢复须由卡提供实存 evidence_path，sub=S13，sem=returns 0x160 (352)；`
- 校验：旧句残留 0，新句 41 行。

## 4. 补 `PANEL.md` 13 处旧 atlas_n（含三列百分比复算）
从 `coverage.tsv ∩ function_atlas.tsv` 按 coverage 子系统重算 atlas_n（合计 12,916），与 PANEL 比对得 **13 处**不一致，全改：

| S | 前→后 | S | 前→后 | S | 前→后 |
|---|---|---|---|---|---|
| S05 | 638→643 | S06 | 850→848 | S07 | 807→804 |
| S08 | 23→22 | S09 | 1049→1051 | S10 | 513→526 |
| S12 | 284→279 | S14 | 491→489 | S18 | 660→659 |
| S19 | 362→357 | S20 | 407→410 | S21 | 127→129 |
| S22 | 4857→4851 | | | | |

三列百分比以新 atlas_n 为分母全表重算：`named_pct_L=named_n/atlas_n`、`proved_pct=proved_n/atlas_n`、`named_pct_S=(named_n−Class::sub_)/atlas_n`（Class::sub_ 8 条：S05 1/S06 1/S19 6）。`verify_panel.py` 独立验 **22/22 行三列全部可复算**，TOTAL 12,916/7,150/1,274 → 55.36/55.30/9.86 自洽。另同步更正表头 18,436→18,431、`[已证]`1,281→1,278、atlas 外 7→4 条、PENDING 86→105、probe 130→132。

## 5. 登记 W177-C 14 行非标 token（未静默改）
14 行 token 全在 W177-C，**evidence_path 全部实存**，按语义归一并逐行登记 PENDING（93–106 行）：

| 原 token | 行数 | 映射 grade | 依据 |
|---|---:|---|---|
| `[已证·复用]` | 8 | `[已证]` | evidence 实存，复用已证结论 |
| `[已证读数]` | 2 | `[已证]` | evidence 实存 |
| `[已证·观测]` | 1 | `[已证]` | evidence 实存 |
| `[未证·未调用]` | 2 | `[未证]` | 未调用=未证 |
| `[推断·可观测]` | 1 | `[静态推断]` | 未取 EIP |

覆盖内 0 个非标 token，无静默升级；映射仅登记，未改 delta 原文。
## 确认
5 项全部落盘；`REPORT.md` 已写；`coverage.tsv` mtime 已变（2026-11-17 23:11:29，size 3,635,243）。逐 S 百分比 22/22 可从表内复算。
