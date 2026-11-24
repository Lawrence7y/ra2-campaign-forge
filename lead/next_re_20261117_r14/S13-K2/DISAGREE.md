# DISAGREE.md — S13-K2 与派卡面 / 前序卡 / 台账的分歧

## D1 · 派卡假设「11×N byte 全局矩阵 @ .rdata / 0–255」—— 实测否定
- 派卡 T2 原文：「Verses 表：11 种护甲 × N 种弹头 的矩阵。表在哪（.rdata）？元素宽度（byte？）？缩放因子 0–100% → 0–255？」
- 实测：Verses 是**每个 WarheadTypeClass 实例中的 double[11] @ +0xA0..+0xF7**（实例字段，非 .rdata 全局矩阵），元素宽 8，缩放 0–100%→**0.0–1.0**（×0.01）。`.rdata 0x7E5210` 是 11 项装甲名字符串表，不是倍率矩阵。
- 依据：loader `mov ebp,0xB`/`fstp qword [ebx]`/`add ebx,8`@0x75DE0C–0x75DE58；默认串 0x847C40=11×`100%%`；9 处 `scale=8 disp=0xA0` FPU 读。证据 `EVIDENCE/VERSES_TABLE.txt`。
- 结论：派卡的这条是**猜测假设**（纪律 12），本卡按字节实测推翻，未凑数。

## D2 · 8 个 GetSize/WhatAmI 曾被 M1-FIX7 降级为 [未证] —— 本卡按恢复路径补证
- 盘面：`COVERAGE/UNSOURCED_PROVED.tsv` 第 2/3/6/7/36/37/40/41 行记录这 8 行原 `[已证]` 因「缺可核来源」在 M1-FIX7 降 `[未证]`，并写明「**如需恢复须由卡提供实存 evidence_path，sub=S13，sem=…**」；`coverage.tsv` 相应行 sem 带「；无来源支撑，待补证」。
- S13-K1 的 delta 虽断言过这 8 行 `[已证]`，但 evidence_path 指向的 `verify_slots.txt`/`rtti_extract.txt` 被审计判「无 delta 断言/无来源」而未采纳。
- 本卡不重蹈覆辙：提供**本卡实存** `EVIDENCE/GETSIZE_CLOSURE.txt`，含 ① vtable slot11/slot12 逐字节 `B8 imm32 C3` ② 工厂 `push size → new 0x7C8E17 → ctor` 双点闭合 ③ slot35/36 反例与 0x4C9150 桩排除 ④ 复跑脚本入口。满足「字节级证据，可独立复算」（STATUS_BOARD 升级硬规矩①）。
- 结论：8 行以 `[已证]` 交 delta，grade 恢复；这是**补证恢复**而非静默提级，审计可逐字节复核。

## D3 · Verses 消费者归属 S05/S06/S14，非 S13 —— 不把它们计入 S13 proved
- 9 处 Verses FPU 读的归属函数：0x48923D→S06/MapClass::GetTotalDamage；0x6F36FE/0x6F3731→S05/FootClass::slot185；0x6F7D3D→S05/TechnoClass::ctor；0x6FCB6A→S05/FootClass::slot240；0x708AF7→S14；0x70CEB2/0x70CEC7/0x70CF49→S05/sub_0070CD10。
- 因此「伤害结算读 Verses」这一事实虽在本卡完全证出，但**按 coverage 的 subsystem 归属，它给 S05/S06/S14 加分，不给 S13 加分**。本卡不跨系统挪用，不把 consumer 侧算作 S13 proved 增量。
- 依据：`work/t2_extra.py` 用 atlas 区间包含判定站点归属（纪律 17，非 entry_at_or_before）。

## D4 · S13-F1 审计对 #3/#5/#8 的降级 —— 本卡沿用，不翻案
- S13-F1 `_audit/VERDICT.md`：GetFireError 门控降 `[静态推断]`、Construct 字段名降 `[静态推断]`（偏移保留）、`+0x9C=Armor` 降 `[静态推断]`、跳转表六项→5 项。
- 本卡伤害链分析沿用这些分级：`+0x9C` 在 U2 保持 `[静态推断]`，不因 Verses 乘子坐实而顺带升级（坑 4）。跳转表/GetFireError 非本卡范围，不重开。

## D5 · proved 目标 120 与实际可达 55 —— 如实报告，不凑数
- 派卡要求 proved 47→120（+73）。本卡可靠字节级增量 = +8（D2），得 55。差距 65 属 U6 结构性缺口（27 个 sub_ 弱语义 + 消费者跨系统）。
- 按纪律 9（停机核验：自算与入账不符先报告，不凑数）与「只交真能定的行」，本卡交 8 行而非 73 行，未编造任何 `[已证]`。
