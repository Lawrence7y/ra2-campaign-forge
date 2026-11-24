# S13-DIRECT UNKNOWNS

## U1. ⑨ 卡面 proved=89 vs 盘上 literal 86（差 3）
- 盘上 coverage.tsv (SHA 502A56FE…, mtime 2026-11-18 14:42 +08:00) S13 grade: [已证] 86 / [静态推断] 129 / [未证] 25 = n 240。
- 卡面/COMMON §9.0d/STATUS_BOARD L276 用 89 = 86 + S13_K12 审计白名单 3 行 (0040F870/0054E890/0054EA70, VERDICT §4 裁「可并入」但未落盘 coverage)。
- 本卡不擅自改盘上 coverage（写域仅本目录）；交付按 literal 86 为基线，同时列 89 审计口径。direct 通道 0 增量，两口径并入后不变。
- 需 lead 裁决：是否将 K12 三行正式并入 coverage.tsv 以消除卡面/盘面差。

## U2. 129 行 virtual-only 的「活 vptr」判别未做
- 129 行均有 .rdata dword 引用（虚表槽值），但本卡不碰虚派发、不升格，未逐行区分构造器活 vptr vs atexit 析构器死表（错源㉓ / D-39）。
- 按卡纪律：虚表可达行只列 VIRTUAL_SKIPPED.tsv，不升格；活/死判别留后续虚派发卡。

## U3. 本卡 direct 通道 0 命中 ⇒ S13 差 31 无法经本通道缩小
- 门槛 120 - 盘上 86 = 34（literal）/ 120 - 89 = 31（审计口径）；direct 通道可升行数 0。
- S13 达标只能靠虚派发通道（本卡禁止）或 D-39 裁决解禁 C2 类；本卡不越界。
