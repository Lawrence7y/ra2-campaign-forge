# S20-DIRECT DISAGREE

## D1 · 无与卡面盘面数字的分歧
⑨ 复算 S20 n=410 / proved=68 / static=331，与卡面逐字一致（会话起点 coverage SHA `502A56FE…`）。未触发停机条件。

## D2 · 与 COMMON-R9 §9.0d 全库 proved 1,449 的表面差
本卡中途读到 1,452（SHA `DC471354…`），收尾读到另值（SHA `2C599504…`）——**并发写入移动靶**，非本卡所致，也非错误。
S20 子集三次读取恒为 68 proved，本卡申报的 S20 并入后 79 稳定。

## D3 · 无审计历史虚派发争点
本卡一律不碰虚派发/exact；COMMON-R9 ㉓–㉕ 的 3 次 FAIL（构造器 vs atexit 虚表混淆）不适用于 direct E8 通道：
11 行的 caller 均为真指令边界上的 E8 rel32，弱扫(raw E8)/强扫(边界E8) **差集=0**（`EVIDENCE/final_verification.json`），无同源系统性错误，随机基线有鉴别力。

## D4 · VIRTUAL_SKIPPED 行数 329
全 .rdata 对齐 dword 扫描：329 行 S20 非 proved 行仅虚表可达（无 direct caller）；2 行（005F3D90/007610A0）两者皆无，未列入。
11 行 direct 升级行与虚表集 **交集=0**（纯 direct，非“虚表+direct 取强”），无双重计证。
