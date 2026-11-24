# S06-K5 DISAGREE

## D1 与 S06-K4 审计裁决的关系
- 审计 W179/K4 VERDICT 判 PARTIAL 并指出 00483780 被误述为「仅字段访问/锚点调用，缺完整闭环」是事实错误。本卡独立复算后确认：00483780 具备完整行为闭环，已升为 [已证]；00483710 的「return true」文案错误在本卡新行中已避免（写为「返回被调 al」）。

## D2 K4 候选普查漏采的可复现根因（锚点地址笔误）
- K4 work/k4_behavior_probe.py 的 anchors 字典为 0x80A80/0x87190/0x80510，而 coverage.tsv 实际为 00480A80(ReduceTiberium)/00487190(IncreaseTiberium)/00480510(ConnectsToOverlay)：三者均缺前缀 4。
- 后果：直接 call IncreaseTiberium(0x487190) 不会被 K4 扫描器计入锚点命中，00483780/00483710 的调用均漏匹配；疑为审计「42→1」vs「45→1」计数差异与漏采根因之一（未改 K4 文件，仅报告）。

## D3 与 K4 数字口径
- K4 delta(23 行) 未提交进 coverage.tsv；盘上现值 proved=103/848，若并入 K4 为 126，再并本卡为 127。本卡按纪律 9 分开报告，与卡面/审计数字一致，未调整口径、未停。

## D4 命名区分
- 00483710 = CellClass::GrowTiberiumIfAllowed（typeIndex,1，单格）；00483780 = CellClass::SpreadTiberiumToNeighbor（typeIndex,3，8 邻向）。二者同族不同门控分支，未复用名字。

## D5 方法学遵循
- 双通道：裸 E8 扫描通道不依赖 atlas entry+size；站点用 coverage 区间包含归属（0x482000..0x483400 atlas 空洞未被误判）。
- 「不存在」结论已查直接调用者一层与等价形（0x4838E0 canSpread、0x7C060 实为 0x47C060 已更正）；入口已证 != 语义已证，全部证明以字节链为准。
- 卫生：未改 exe/coverage/台账、未 git commit、未用 Ghidra。
