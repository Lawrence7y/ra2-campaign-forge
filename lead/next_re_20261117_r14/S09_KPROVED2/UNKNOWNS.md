# S09-KPROVED2 · UNKNOWNS.md

卡号 S09-KPROVED2。本文件记录 8 行候选中**任一环不成立**的行、以及复算中未能完全消化的疑点。未改 grade / 未改 coverage.tsv / 未写台账。

## U1 · 00654320 RadarClass::slot34 —— ③b 不成立（③a 机械可述），不进 delta
- ① 入口：16B 对齐、E8@6403A3 边界直调、体外非自环 —— 成立。
- ② 类属：全 1214 张 RTTI 表中恰 1 张命中 vt7F0344[34]=entry，COL8083C0→TD816BF8→TD+8 逐字 `.?AVRadarClass@@`（name 类 RadarClass 一致）—— 成立。
- ③b：**不成立**。逐条打完 [654320,65448C) 全部 88 条指令（EVIDENCE\dis_00654320.txt）：
  - 无 jmp 表 / switch 状多路分支；
  - 唯一 1 道 jcc @6543D7 `test eax / je 6543E1` 仅在两个调试串指针 0x8393C8 / 0x8393B4 间二选一（动作仅"换打印串"），不满足"≥3 道互斥闸且各动作不同"；
  - 无循环（0 个后向跳）；
  - 无可证伪错误码/返回约定；
  - 非构造器，无 ≥2 vt 写 / ≥10 字段布局断言的内存形状断言。
  - 整体形态 = 线性算绘制矩形（写 [0xB049xx]）+ 11 次外部调用 + 末尾 65447E 写 `[edi+0x14DA]=1` ⇒ ③a 机械可述。按 D-42（§8.6 条3）③a 留 `[静态推断]`，不升 `[已证]`。
- ④ 站：E8@6403A3（site+5+rel32==entry、体外、非自环）—— 成立，但 ④ 单独成立不足以升格（D-40 最小环集）。
- 处置：**不进 coverage_delta.tsv**；保留 coverage.tsv 原 grade（该行本为 A 集合候选，未并入）。

## U2 · 004E2690 / 0069DEB0 —— ③b 仅在 D-42 细则#1 口径下成立（细则#1 级边际）
- 两行 ①②④ 均成立（见 coverage_delta.tsv 与 EVIDENCE\）；③b 均为"线性化 switch / 互斥闸链"，无物理 jmp 表、无循环。
- 若严格只认 D-42 ③b 四充分条件中的"①跳表 / ④循环 / ②错误码"三档，则两行 ③b **不成立**；仅"①switch 状多路分支（细则#1：≥3 互斥闸各动作不同）"可作边际并入。
- 按 L4 已明说、标"细则#1 级边际"并给敏感性说明（见 coverage_delta.tsv one_line_semantics 与 DISAGREE.md D2/D3）。两行已并入但**边际**，若后续审计收紧细则#1 应首先回退此两行。

## U3 · A 集合复算的 direct/livevt 口径差（已消化，非缺口）
- 自写 exe 复算（EVIDENCE\A_recompute.tsv / A_recompute_log.txt）：②RTTI 槽命中 601 行、④direct 站点体外 128 行、②∩④direct = **102** 行；classification.tsv 的 A_strict = **103** 行。
- 差 1 行 = `004F4240`（MouseClass::slot0），其 `n_direct_out=0 / n_livevt=1` ⇒ 属 SURVEY_RING24 记的 S09 "④dir/lv = 102/1" 中那 1 条 livevt 行。我的 direct-only 复算不收 livevt 故少 1，与 SURVEY 口径一致，**非错误**。该行不在本卡 8 候选中。

## U4 · 指令总数与 SURVEY_RING24 的微小差（口径差，非错误）
- 本卡 capstone skipdata 全 `.text` 扫描得 **1,394,186 条指令 / 68,253 个 E8@边界**；SURVEY_RING24 记 1,392,592 / 68,253。
- E8@边界数逐字相同（68,253），且本卡 8 行全部 direct 站点都落在该边界集内；指令总数差 1,594（0.11%）来自 skipdata 对不可解码字节的切分粒度，不影响任何站点判定。所有交付站点均在扫描覆盖 100% `.text` 内（符合错源㉖）。

## U5 · 未使用 Ghidra
- 本卡全部结论由 capstone 5.0.7 + pefile 2024.8.26 从 exe 直接复算得出，未创建 `_ghidra\S09_KPROVED2\`（任务允许"仅确实需要 Ghidra 时"才建）。无待补 Ghidra 项。
