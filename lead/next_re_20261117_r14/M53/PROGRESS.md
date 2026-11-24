# M53 PROGRESS — COVERAGE 单写者接管 / D-42 子项 / named 规则 / PANEL 生效声明

## 基线（写入前记录；两文件 untracked，靠 mtime+sha 识别第三方写）
- coverage.tsv: bytes=3,730,020 / 行数=18,498(LF；末行无换行，Get-Content=18,499) / sha256=b4c998c06f91e9b23c0a34ea459a308eee8212671d761b0189b7135dfbcbe94c / mtime=2026-11-19 22:04:36.637
- PANEL.md: bytes=102,125 / 行数=482(LF) / sha256=869e7daf4ea33936f3a8fc73566f069ee28c9370718408bbf831e796169f17a2 / mtime=2026-11-19 22:19:02.075
- 备份：_hygiene/coverage.M53.bak、_hygiene/PANEL.M53.bak（sha 与改前逐一相等）。
- 注：任务卡称 PANEL 477 行/101,651 B；实测基线 482 行/102,125 B（第二会话在其后追加），按实测基线记。

## (a) coverage.tsv 改前 / 改后
- 改前：3,730,020 B / 18,498 行 / b4c998c06f91e9b23c0a34ea459a308eee8212671d761b0189b7135dfbcbe94c
- 改后：3,730,077 B / 18,498 行 / 6734029ed9e68355d3f2a896fe6533547d2abf84eafc0cfcb04953b9c0df0920
- 行数仍 18,498 ✓；仅第 4 列语义改动，entry(第1列)/grade(第5列) 逐行断言未动。

## (b) 三行语义栏逐字对比（→ 后为改后）
- 006C9890 FileStraw::slot1：`...（③b①细则#1 对称解除…绑定到新 pipe：5 道互斥闸…）` → `...（③b 细则#1 级 对称解除…绑定到新 pipe：5 道互斥闸…）`；仅等级段变，锚 +0xB/+0x1C/+0x2D/+0x3B 全保留。
- 00631CC0 FilePipe::slot3：`...（③b①细则#1 对称解除…重新绑定到新 pipe：解绑走 vt+0xC…）` → `...（③b 细则#1 级 对称解除…重新绑定到新 pipe：解绑走 vt+0xC…）`；仅等级段变，锚 +0xB/+0x1C/+0x39/+0x43 全保留。
- 004AB9B0 DisplayClass::LMBUp：`byte-checked: …'no source support' note` → 同原文 + `（③b 细则#1 级：多路守卫链，非跳表）`；原文逐字保留。
- 全表 `③b①细则#1` 4→2（004AAD30/004E2690 属他项未动）；`③b 细则#1 级` 0→3。

## (c) named_S 两算法差异（短形态 `::sub_[0-9A-Fa-f]+$` 减 字面8位 `{8}`）
- 逐行 diff：S01 0; S02 0; S03 0; S04 0; S05 -1; S06 0; S07 0; S08 0; S09 0; S10 0; S11 0; S12 0; S13 0; S14 0; S15 0; S16 0; S17 0; S18 0; S19 -6; S20 0; S21 0; S22 0; TOTAL -7。
- 短形态值 vs 字面8位值：S19 40 vs 46；S05 520 vs 521；TOTAL 7203 vs 7210。
- 7 行短形态：S19 004060F0/00406130/00406170/004061D0/00406270/00406310（AudioController::sub_*）+ S05 0070DE00（TechnoClass::sub_70DE00）。面板现值已用短形态规则（正确）；按字面 8 位重写会 +7 虚高。

## (d) PANEL.md 改前 / 改后
- 改前：102,125 B / 482 行 / 869e7daf4ea33936f3a8fc73566f069ee28c9370718408bbf831e796169f17a2
- 改后：105,815 B / 499 行 / 93107ea25dbc8381402fb7f4d7fc8e07714f4aaa537be7338fdc667053538267（+3,690 B / +17 行）
- 仅 4 处文本改动：标题 M53 段、主口径 named 规则补语、严格双列表节 named 规则行、新增「RULING-R15 生效声明」节。

## (e) 21 子系统行 + TOTAL 核对
- 重算 named_S 与面板现值逐行比对：22/22 全等，改动 0 行（MERGE_LOG 记 SYNC_NO_CHANGE）。

## (f) 达标名单（自算，门槛 ceil(0.9n)/ceil(0.5n)）
- 名义(named R14 + proved)：S15,S16,S17 = 3/22；严格(named R14 + proved_strict)：S17 = 1/22。与面板一致。

## (g) mtime 与第三方写入声明
- coverage.tsv：22:04:36.637 → 22:23:09.329；PANEL.md：22:19:02.075 → 22:23:50.677。
- 每次写入前 guard 均比对 baseline sha+mtime 全等（通过）；备份 sha = 改前 sha；接管期间**无第三方写入**。
- 注：RULING_R15 §1 D-42 原文称 004AB9B0 属 D-44 类「不得靠标细则#1级过关」；本卡按任务卡显式改写规则补标，登记供 Lead 复核。

## 交付
- PROGRESS.md / MERGE_LOG.tsv / SINGLE_WRITER_TAKEOVER.md；未改 CONFLICTS/PENDING_CORRECTIONS/台账/R14_COMMON/STATUS_BOARD/ra2youli；未 git commit；未建 venv、未 pip install。
