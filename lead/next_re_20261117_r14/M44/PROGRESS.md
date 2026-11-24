# M44 PROGRESS — SEMFIX-SLOTS2 11 行补语义并入 + S05/S09 15 行语义判据拦下 + 3 行改名

卡号 M44｜合并员 agent-40｜2026-11-19。写域仅 COVERAGE\coverage.tsv、COVERAGE\PANEL.md、M44\、_hygiene\ M44 备份；其余只读，未 git commit / 未建 venv / 未 pip install。

## 并入结果
实际并入 N=11（组 1 全量）；组 2 计划 15 行全部被语义判据拦下，故 N < 预期 26。

## 26 行 entry 清单（组 1 并入 11 + 组 2 拦下 15）
1 0047AE10 S03 并入｜2 0065CDD0 S03 并入｜3 0065D0D0 S03 并入｜4 0065D190 S03 并入
5 004D82B0 S10 并入｜6 004D5690 S10 并入｜7 004DB260 S10 并入｜8 00702D40 S10 并入｜9 00706640 S10 并入｜10 00708C30 S10 并入｜11 004D94B0 S10 并入
12 006F3330 S05 拦下｜13 006F8DF0 S05 拦下｜14 006FC0B0 S05 拦下｜15 006FFEC0 S05 拦下｜16 0070BF50 S05 拦下｜17 00712170 S05 拦下｜18 00716150 S05 拦下
19 006D0270 S09 拦下｜20 006D04F0 S09 拦下｜21 00653850 S09 拦下｜22 004F4480 S09 拦下｜23 004A8960 S09 拦下｜24 006C6680 S09 拦下｜25 004F4320 S09 拦下｜26 006AC210 S09 拦下

## 被拦行说明（组 2 全 15 行）
白名单按审计：S05 = delta 8 行除 00704350（回退）之外 7 行；S09 = delta 全部 8 行。逐行核 coverage.tsv 第 4 列：15 行 one_line_semantics 全含「槽语义未证」占位模板，按组 1 同一判据（语义栏不得含未证字样，且只改第 5/6 列、semantics 不动）全部不并入，grade 保持 [静态推断]、evidence_path 不动。两审计 VERDICT 的「自陈未证 0 行」指 delta 第 4 列，不能替代 coverage 第 4 列核对。00704350 本就不在 S05 白名单（审计回退），不计入 26 行。

## 组 1 并入口径
三列同时改：第 4 列取 SEMFIX-SLOTS2 delta 的 ③b 整体合同（新语义全文无「未证」），第 5 列 [静态推断]→[已证]，第 6 列取 delta 原文 EVIDENCE/ANCHOR_<entry>.txt。改前 11 行 grade 全 [静态推断]（M43 未并入）、name 与 delta/改前逐字节相同。

## 组 3 改名（只改第 3 列）
按 S05_KPROVED3\_audit\VERDICT.md §2 line 26 的 ② 栏 ⑯ 基类级自证：006F3330 FootClass::slot185→TechnoClass::slot185；006FC0B0 FootClass::slot240→TechnoClass::slot240；00716150 AircraftTypeClass::slot42→TechnoTypeClass::slot42。VERDICT 已给齐地址到目标名的对应，故执行。grade/semantics/evidence_path 不动。

## 必做自检 (a)-(g)
(a) 行数改前 18,431 / 改后 18,431，entry 增删 0（逐行 entry 序列逐字节相同）。
(b) grade 直方图 改前 [已证] 1,424 / [静态推断] 5,983 / [未证] 11,024；改后 N=11：[已证] 1,435 / [静态推断] 5,972 / [未证] 11,024 不变；和 1,435+5,972+11,024=18,431。
(c) conflict==1 改前 254 / 改后 254。
(d) 并入 11 行逐行验证 grade=[已证]（11/11 通过）。
(e) 全表 [已证] 且语义栏含「槽语义未证」且 subsystem 非 S22：改前 0 / 改后 0。
(f) 组 1 11 行新语义全文无「未证」字样（11/11）、name 与改前逐字节相同（11/11）。
(g) coverage.tsv SHA-256 改前 6441686A8205B236315BAEDB4CD1477A5C7B2C87E49077DA532AC186DA2BA0E2 → 改后 3B955DA48727E7A850213D275B1B8A14832202A7E9C35922F87608350F182591；PANEL.md 改前 8CFD424B018D804E93E6E687DDB689785B3C2E1E2A7877C0FC3BD938B9B34C86 → 改后 0C27EA670607D0E1638BCDE9157016CC667885417124DA677A2A61AAB48F4BC7。

## 面板与备份
PANEL.md：标题流水追加 M44；两个量纲行与三分母段按 1,435/1,430 重算；S03 31→35/194=18.04%、S05 150/643=23.33%（0 并入）、S09 87/1051=8.28%（0 并入）、S10 123→130/526=24.71%、TOTAL 1419→1430/12916=11.07%；M43 段前新增 M44 并表说明；其余子系统行一字不动（脚本逐行校验）。
备份 _hygiene\coverage.M44.bak（SHA-256 同改前 coverage）、_hygiene\PANEL.M44.bak（SHA-256 同改前 PANEL）。未改 CONFLICTS.tsv、PENDING_CORRECTIONS.tsv、台账、R14_COMMON.md、STATUS_BOARD.md、ra2youli。
