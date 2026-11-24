# S09-KPROVED3 · UNKNOWNS.md

卡号 S09-KPROVED3。本文件记录 8 候选中任一环不成立的行、以及未完全消化的口径疑点。未改 coverage.tsv / 台账 / 游戏文件。

## U1 · 0048E5A0 ControlClass::slot31 —— ③b 不成立（③a）
- ①入口、②RTTI（vt=007E528C slot31，COL=007FD308→TD=0081D0F0→TD+8 逐字 `.?AVControlClass@@`，单持有表）、④direct（14 处 E8@边界、体外、非自环）均成立。
- ③b 不成立：全 38 条 `+0x0000..+0x0052` 已逐条打完（EVIDENCE\DISASM_0048E5A0.txt）。`+0x000F/+0x0016/+0x0020/+0x002A/+0x003A` 是顺序独立条件，可共真，不是 D-42 细则#1 要求的 ≥3 道互斥闸；动作只写 `[edi]` 的 0/0x80/0x40 变体并汇聚到 `+0x004A` 单次直调。无后向跳、无 jmp 表、无可证伪错误码、无 ≥10 字段或 ≥2 vt 的形状断言。按 D-42 留 ③a，**不进 delta**。

## U2 · 0048E620 ControlClass::slot27 —— ③b 不成立（③a）
- ①②④ 成立：vt=007E528C slot27；COL=007FD308→TD=0081D0F0→TD+8 `.?AVControlClass@@`；3 张持有表（ControlClass/ToggleClass/SelectClass，同 slot27，按 L1/⑯归 ControlClass）；7 处 direct 站点全生效。
- ③b 不成立：全 14 条 `+0x0000..+0x001E`，唯一闸 `+0x0008`，真支 `+0x000E call [eax+0x6c]`，随后 `+0x0018 call 0x4E1550`。无第二/第三互斥闸、无循环、无错误码、无形状断言。**不进 delta**。

## U3 · 004A8960 DisplayClass::slot42 —— ③b 不成立（③a）
- ①②④ 成立：7 张持有表同 slot42，归 DisplayClass；direct 站点 2 处。
- ③b 不成立：全 176 条 `+0x0000..+0x0281` 无后向跳、无 jmp 表。`+0x0052/+0x0073/+0x008A/+0x00AE/+0x0110/+0x014B` 均为全局指针 NULL 检查；动作是同一「free 旧对象→new 0x30→复制 4 坐标」模式对两个全局槽重复，不是 ≥3 道互斥且各动作不同的模式闸；`+0x00E8` 单字段写不构成内存形状断言。分配 NULL 检查按 D-42 不算可证伪域错误码。**不进 delta**。

## U4 · 004AAD20 DisplayClass::slot44 —— ③b 不成立（③a 空桩）
- ①入口、②（5 张持有表同 slot44，归 DisplayClass）、④（2 处 direct）成立。
- ③b 不成立：全函数唯一指令 `+0x0000 ret 4`（EVIDENCE\DISASM_004AAD20.txt），无状态转移/判断/调用/循环。**不进 delta**。

## U5 · 004AAD30 —— ③b 仅在细则#1 级成立（边际）
- ③b① 依赖 D-42 细则#1（≥3 互斥闸且各闸动作不同）。已逐条证明 7 个真支直接 ret、helper 调用各异（0x4A8BF0/0x4AC8C0/0x4AC660/0x4AC820/0x4AC700/0x4AC960 与一个字段写），不是「仅参数不同汇入同一 call」；L4 标签已写进 delta。
- 敏感性：若只认物理跳表/完整循环/错误码/内存形状四档中的硬条件，本行 ③b 不成立，应首批回退。

## U6 · A 集合计数中的 livevt 行
- 本卡自算 ②RTTI=601、④direct 体外=128、②∩④direct=102；A_strict=103 = 102 + 1 行无歧义 livevt `004F4240`。该 livevt 标志来自 `SURVEY_RING24\EVIDENCE\classification.tsv` 的 `livevt_valid`，本卡未把它选入 8 候选，delta 也不含 livevt 行；所有交付 ④ 均为 direct。若后续收紧 livevt 口径，A 计数可能回到 102，但不影响本卡 delta。

## U7 · ③b 基率检测器的保守代理
- `BASELINE_3B_FEATURES.tsv` 是自动代理；“硬档/细则#1级”的最终逐行判定由 `CONTRACT_3B.tsv` 的全量反汇编人工复核覆盖。代理对 004A9840/004A9DD0/004AA050 标 strict、对 004AAD30 标 loose，与人工结论一致；004A8960 曾因分配 NULL 检查被早期过宽规则误标，已在 `s3_baseline.py` 收紧后归零。
- 基线报的是 **③b 基率**（strict 39/629、loose 40/629），不是 ②∧④ 入选率 103/629（那是挑选谓词本身）。

## U8 · 未使用 Ghidra
- 全部结论来自 capstone 5.0.7 + pefile 2024.8.26 对只读 exe 的复算；未创建/写入 `_ghidra\S09_KPROVED3\`，无待补 Ghidra 项。
