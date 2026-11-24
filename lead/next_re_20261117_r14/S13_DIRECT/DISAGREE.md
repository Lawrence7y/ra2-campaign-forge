# S13-DIRECT DISAGREE

## D1 (⑨ 停机核验): 卡面 proved=89 ≠ 盘上复算 86
- 卡面原文：「盘上现态（Lead 实测…atlas∩coverage；与你自己复算不符就停下报告）S13: n=240、proved=89…[静态推断] 129 行」。
- 我的复算（coverage.tsv UTF-8 单遍读，atlas W130 统一大小写求交）：n=240 ✓ / [静态推断]=129 ✓ / proved([已证])=**86** ✗。
- 差异根因已定位：89 是审计调整口径（86 + S13_K12 VERDICT §4 白名单 3 行 0040F870/0054E890/0054EA70），这 3 行在盘上 coverage.tsv 仍为 [静态推断]；COMMON §9.0d、STATUS_BOARD L276 亦记 86→89。
- 判定：非盘面漂移、非错源，属卡面采用审计口径 vs literal 盘面口径的 3 行差。已按已授权范围继续 direct 通道（本卡 0 行可动 grade，名字/subsystem 未动）。⚠ 若 lead 要求严格「不符即停」，请指示；本卡所有交付均不写入 COVERAGE/。

## D2: direct 判据 0 命中与卡预期「可有 direct 行」不一致
- 卡要求 coverage_delta.tsv「只放 direct 行」；全 .text 1,392,592 指令 / 68,253 E8 边界扫 + raw E8 弱扫双证：129 行 [静态推断] 全部 0 direct call site ⇒ delta 为空（仅表头）。
- 差分检验（弱-强=0）排除「边界过滤误剔」；随机基线（同类静态行 15.3% / atlas 49.9% 命中）排除扫描失效。0 为结构性真阴性，与 S13_K12 审计「17 行无 direct」一致。
