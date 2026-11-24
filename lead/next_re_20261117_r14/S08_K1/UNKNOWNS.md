# UNKNOWNS · S08-K1
- U1 `004309D0` 语义确为 BeaconArt/RadarBeaconArt 装载，但全库按 entry 查无独立真名；保留 `sub_004309D0`，只以 direct call 升 `[已证]`。
- U2 19 行 `slotN/vslotN` 语义行 strict direct=0；按卡面未用 exact/虚表通道，故未升格。
- U3 `0047EFE0` 命名分歧只报告不处理：前卡 `S08-K1/coverage_delta.tsv:13` 为 `MapClass::DrawShroudFogLayer`，`docs/re/ARCHITECTURE_ATLAS.md:4336` 为 `Draw_Shroud`。
- U4 `004309D0` 的直接调用者以 `ecx=0x89C3B0` 传入；该对象类归属未完成 RTTI/构造器闭环（`EVIDENCE/RTTI_004309D0.txt` 显示无虚表 dword 命中），因此不写任何 `Class::` 归属。
- U5 coverage 原始 S08 有 23 行；`0065B800` 不在 `function_atlas.tsv`，按卡面 `atlas∩coverage` 口径排除。
- U6 随机基线 22 样本中 10 行 strict direct 命中，说明随机基线不足以背书系统性错误；本卡以 weak-vs-strict 差分（差 0）+ 逐站点字节复核为准。
