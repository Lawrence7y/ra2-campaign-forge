# M63 MERGE LOG — 并表 NAMED_PUSH 审计 PASS 6 行

## 范围与授权

- 本轮唯一 COVERAGE 写者；只写 `COVERAGE/coverage.tsv` 与 `COVERAGE/PANEL.md`，以及本目录 `MERGE_M63/` 交付物。
- 未 git commit；未碰 `R14_COMMON.md`、`STATUS_BOARD.md`、台账、`NAMED_PUSH_*`、`NAMED_PUSH_AUDIT`。

## 事实来源与交叉核验

- 审计表 `NAMED_PUSH_AUDIT/verdict.tsv`：表头 8 列（entry/subsystem/verdict/ring2_at/ring3b_form/ring4_at/same_source/reason），数据 8 行。
- 按第 3 列 verdict 核出 PASS 6 行：005414C0 / 0071F8C0 / 0041F580 / 00503040 / 00512290 / 00512480。
- FAIL 2 行：`005C46E0`（④ 锚点 `005C164A` 属析构器 `005C1640`，违 ㉓）、`0065AC40`（第 4 列把 `00410320` 的写出语义写成「流读入」，读写方向反）——整行拒绝，一个字未改。
- 6 行 delta 语义来源：`NAMED_PUSH_S18_B1/delta.tsv`（005414C0）、`NAMED_PUSH_S18_B2/delta.tsv`（0071F8C0）、`NAMED_PUSH_S14_B1/delta.tsv`（0041F580/00503040/00512290/00512480），各取第 4 列原文照抄。

## 改前前置核验（全部通过）

- 6 行改前 grade：`0071F8C0`=[未证]，其余 5 行=[静态推断]；6 行均在 coverage 且各唯一。
- 6 行全部在 `function_atlas.tsv`（entry 大写归一）内。
- 改前盘上：数据行 18,498、全表 [已证] 1,496、atlas 内 1,490、atlas 外 6、S18 54、S14 107。

## 落地改动

- `coverage.tsv` 6 行各只改 3 列：第 4 列 ← delta 第 4 列原文；第 5 列 → `[已证]`；第 6 列 → `NAMED_PUSH_AUDIT/VERDICT.md`。第 1/2/3/7/8 列逐字节未动；数据行仍 18,498、8 列、TAB 分隔。
- `PANEL.md` 同步 7 行（主面板 17/68/72/77 + 严格双列表 118/122/127）：S18 proved 54→56、S14 proved 107→111；全表 [已证] 1,496→1,502、atlas 内 1,490→1,496、atlas 外仍 6；严格列 S18 44→46、S14 94→98、TOTAL 1,163→1,169；百分比按实算重算。备注列追加 M63 说明。M47 历史快照行未动。
- 6 行语义均不含「未证」⇒ strict 同增（S18 +2 / S14 +4 / TOTAL +6）。

## 改后结果

- 数据行 18498；全表 [已证] 1502；atlas 内 1496；atlas 外 6；S18 proved 56；S14 proved 111。
- 6 行新 grade 全 `[已证]`、evidence_path 全 `NAMED_PUSH_AUDIT/VERDICT.md`、语义与 delta 逐字节一致。
- 2 行 FAIL grade 仍 `[静态推断]`、整行逐字节未变。
- 达标判定未翻转：名义 S15,S16,S17、严格 S17（严格仍仅 S17）。
- 两文件改前/改后 mtime/字节/sha256 见 `BEFORE_AFTER.txt`；复算见 `VERIFY.txt`。
- 已知既存差异（非本卡引入，未改）：严格双列表 S22 strict 面板记 2，`strict_panel.py` 口径重算为 12（+10），属 M60 截面差异；本卡只按增量 +6 更新 TOTAL，不重算全表、不碰 S22。
