# M55 PROGRESS — COVERAGE 唯一写者（承接 M53/M54）

任务：并入 S13_K8RECHK 11 行 + D41_SUBST 8 行（00405BE0 剔除）共 19 行 [静态推断]→[已证]；原地升格、不新增行。两审计 VERDICT 均逐行点名并入清单：S13 VERDICT:37（11 行）；D41 VERDICT:38（原文即并 4 行）/ :39（改文后并 4 行，理由逐行给出，非自猜）。name/subsystem/entry/n_sources/conflict 一字未动。

## (a) 改前/改后 bytes、行数、sha256、mtime
- cov BEFORE: bytes=3,729,995 dataRows=18,498 readLines=18,499 LF=18,498 sha8=C2FB3E52 sha256=C2FB3E525F513B69951FA51DF159DE586E760F4E5733B87767223C516AFAEE65 mtime=2026-11-19T22:29:15.8454658+08:00
- cov AFTER : bytes=3,733,969 dataRows=18,498 readLines=18,499 LF=18,498 sha8=1E3B3455 sha256=1E3B3455DFFF21892781CB0A7FF200B54BC290161B5E642615F122A11AE598E5 mtime=2026-11-19T23:20:54.1582814+08:00
- pan BEFORE: bytes=105,969 readLines=500 LF=500 sha8=2F70AC6C sha256=2F70AC6CF5F8FD9A737B4EFB125D86A8E240DDA54E91CB6ADF1D8C5353E56966 mtime=2026-11-19T22:29:54.1724403+08:00
- pan AFTER : bytes=108,360 readLines=501 LF=501 sha8=0EC9AEFE sha256=0EC9AEFED6DC64A5790D87A4AB8C4028636C6E505C4CD687A15664DC48F7CA87 mtime=2026-11-19T23:21:32.9109283+08:00
- 口径：18,498 = 数据行（M54 的 `wc -l` 口径），readLines 18,499 = 表头+数据。19 行均为纯升格（S13 VERDICT:14「11 行均已是 [静态推断] 同名单 ⇒ 纯升格、无重复行」；本卡实测 D41 8 行亦全为 [静态推断]），原地改写后行数 18,498 不变，与任务卡 (a)(c) 括注「18,498 加并入行数」不合。按硬约束规则1「静态推断→已证」、(b) 重复组=0、(f) 00405BE0 仍静态推断执行，未新增行，特此声明。
- PANEL 基线：任务卡所记 PANEL sha8=93107EA2/499 行是 M54 改前值（`_hygiene/PANEL.M54.bak`）；M54 PROGRESS (f) 记其改后为 2F70AC6C/500，与本卡实测一致，按「以实测为准」采用。

## (b) 改后 entry 重复组数
0（改前亦 0；19 行全部原地改，未新增/删除 entry）。

## (c) grade 直方图（本卡实扫）
- BEFORE: [已证] 1,460 / [静态推断] 6,014 / [未证] 11,024（和 18,498）
- AFTER : [已证] 1,479 / [静态推断] 5,995 / [未证] 11,024（和 18,498）
- 已证 +19、静态推断 -19、未证 11,024 不变、和 = 18,498（行数不变，口径见 (a)）。

## (d) conflict==1
改前 254 → 改后 254（第 8 列未改）。

## (e) 19 行逐行核
19/19：grade=[已证]、evidence_path 指向对应 VERDICT.md#行号；S13 11 行语义含「无直接调用者，仅虚派发见证」、D41 8 行含「② 走身份替代」；全部 19 行无「未证/未定/弱信号/线索」；entry/subsystem/name 与备份逐字相同。0 fail，明细见 MERGE_LOG.tsv。delta 原文均自带规定标注，无「补标注」项。

## (f) 00405BE0
改后仍 [静态推断]（L102，S19，evidence 原值），不在已证行。审计判 ③a 环不成立（§8.6 条1 清零+置默认仅算 P、无 vt 写/对象尺寸，VERDICT:25/39），整行剔除。

## (g) 「已证 且 语义栏含 槽语义未证 且 subsystem 非 S22」
改前 0 → 改后 0（全表实扫）。

## (h) mtime 与第三方写入
cov 22:29:15.8454658 → 23:20:54.1582814；pan 22:29:54.1724403 → 23:21:32.9109283（均 2026-11-19 +08:00）。写前 dry-run 复核 cov=C2FB3E52 / pan=2F70AC6C 与本卡实测基线一致；期间无第三方写入，所有变化均由本卡产生。备份 `_hygiene/coverage.M55.bak`、`_hygiene/PANEL.M55.bak`（sha8 与改前一致）。

## D41 4 行改文（VERDICT:39 逐行点名，理由见 §4 / a7_offsets.tsv / a9_discipline.md）
- 00428B80：偏移 +0x33→+0x28 / +0x43→+0x39 / +0x47→+0x40 / +0x35→+0x56。
- 00405190：+0x36→+0x48 / +0x2B→+0x93 / +0x3E→+0x63 / +0x41→+0x76；「ecx=this」→实测派生指针 [[0xB1D37C]+idx*4]。
- 004052F0：+0x43→+0x93 / +0x4F→+0xA5 / +0x60→+0xC1；「ecx=this」→ call 0x406130 返回值派生指针。
- 00401F90：删假地址 0x8B4154 → ecx=[esi+0x28] 解引；③b② 可证伪约定→状态不变量；+0x02→+0x03。

## 范围
PANEL 仅改第1行流水、三分母段全表已证值、面板 S02/S13/S19/TOTAL 行、RULING-R15 补 1 行 D-39 落地；其余子系统行未动。未改 CONFLICTS.tsv、PENDING_CORRECTIONS.tsv、台账、R14_COMMON.md、STATUS_BOARD.md、ra2youli\；未 git commit；未建 venv、未 pip install。自检 (a)-(h) 全部通过。
