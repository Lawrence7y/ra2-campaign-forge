# M64 MERGE LOG — 并表 NAMED_PUSH_AUDIT2 审计 PASS 10 行

## 范围与授权

- 本轮唯一 COVERAGE 写者；只写 `COVERAGE/coverage.tsv` 与 `COVERAGE/PANEL.md`，以及本目录 `MERGE_M64/` 交付物。
- 未 git commit；未碰 `R14_COMMON.md`、`STATUS_BOARD.md`、台账、`NAMED_PUSH_*`、`NAMED_PUSH_AUDIT*`。

## 事实来源与交叉核验

- 审计表 `NAMED_PUSH_AUDIT2/verdict.tsv`：表头 8 列（entry/subsystem/verdict/ring2_at/ring3b_form/ring4_at/same_source/reason），数据 11 行；第 3 列 verdict。
- 按 verdict 核出 PASS **10 行**：S14 00691EE0/00691FA0/006A4930/006E87F0/006E9140 + S05 00410C30/00414290/0041CFE0/00524D70/005F9950，与卡片逐字一致。
- FAIL 1 行整行拒绝（一个字未改）：`006A48A0`（第 4 列把 `00410320` 流写出写成「流读入」，读写方向反）。
- 另 1 行不进本次并表：`00748190`（NAMED_PUSH_S05_B3 产出，未经异族审计，留池等下一张审计卡；不在 verdict.tsv 内）。
- 10 行 delta 语义来源：`NAMED_PUSH_S14_B2/delta.tsv`（S14 5 行）、`NAMED_PUSH_S05_B1/delta.tsv`（00410C30/00414290/0041CFE0）、`NAMED_PUSH_S05_B2/delta.tsv`（00524D70/005F9950），各取第 4 列 `one_line_semantics` 原文照抄。

## 改前前置核验（全部通过，详见 work/before.json）

- 审计表 11 行 8 列、PASS 10 / FAIL 1 与卡片一致；00748190 不在审计表。
- 10 行改前 grade 全 `[静态推断]`，在 coverage 各唯一；全部在 `function_atlas.tsv`（entry 大写归一）内。
- 006A48A0 与 00748190 改前均 `[静态推断]`。
- 改前盘上：数据行 18,498、全表 [已证] 1,502、atlas 内 1,496、atlas 外 6、S18 56、S14 111、S05 165（与卡片一致）。
- 10 行 delta 语义唯一、均不含「未证」token ⇒ proved_strict 同增。

## 落地改动

- `coverage.tsv` 10 行各只改 3 列：第 4 列 ← delta 第 4 列 `one_line_semantics` 原文；第 5 列 → `[已证]`；第 6 列 → `NAMED_PUSH_AUDIT2/VERDICT.md`。第 1/2/3/7/8 列逐字节未动；数据行仍 18,498、8 列、TAB 分隔。
- `PANEL.md` 同步 7 行（主面板 17/59/68/77 + 严格双列表 109/118/127）：S14 proved 111→116、S05 proved 165→170；全表 [已证] 1,502→1,512、atlas 内 1,496→1,506、atlas 外仍 6；严格列 S14 98→103、S05 133→138、TOTAL 1,169→1,179；百分比实算重算。备注列追加 M64 说明。表头行 1、D-44 达标声明、达标列（3/22、1/22）、M47 历史快照均未动。
- S14 行备注追加限定：`〔模板级低信息量 ③b②：析构体内容器 Find 返 -1 哨兵分支成立；与既有 6 行同型，未收紧口径〕`
- 10 行语义均不含「未证」⇒ strict 同增（S14 +5 / S05 +5 / TOTAL +10）。

## 改后结果

- 数据行 18,498；全表 [已证] 1,512；atlas 内 1,506；atlas 外 6；S14 proved 116；S05 proved 170；S18 proved 56（未变）。
- 10 行新 grade 全 `[已证]`、evidence_path 全 `NAMED_PUSH_AUDIT2/VERDICT.md`、语义与 delta 第 4 列逐字节一致、全 atlas 内。
- `006A48A0`（审计 FAIL）与 `00748190`（未审）grade 仍 `[静态推断]`、整行逐字节未变。
- 达标判定未翻转：名义 S15,S16,S17、严格仍仅 S17。
- 两文件改前/改后 mtime/字节/sha256 见 `BEFORE_AFTER.txt`；复算见 `VERIFY.txt`。
- 已知既存差异（非本卡引入，未改）：严格双列表 S22 strict 面板记 2，`strict_panel.py` 口径重算为 12（+10），属 M60 截面差异；本卡只按增量 +10 更新 TOTAL，不重算全表、不碰 S22。
