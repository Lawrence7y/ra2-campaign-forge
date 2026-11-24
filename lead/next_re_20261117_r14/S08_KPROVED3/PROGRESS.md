# S08-KPROVED3 PROGRESS（卡号 S08-KPROVED3）

目标：仅做 ≤4 行、目标 ≥2；S08 最小缺口（proved 9/22，门槛 11）。
目标二进制 ra2youli\gamemd.exe，SHA-256 73201CC0…F67476（现场复算一致，只读）。
写域：仅本目录与 _ghidra\S08_KPROVED3\；未动 coverage.tsv / 台账 / 其它卡目录。

## 核心数字（本次独立复算）
- coverage.tsv 中 S08 共 23 行；0065B800 不在 atlas ⇒ 排除；in-atlas 22 行。
- 现 proved = 9：004309D0 / 0045A680 / 0045A730 / 0047EFE0 / 0047F250 / 004D24A0 / 004D2510 / 004D27D0 / 004D2810。门槛 11。
- 静态推断池 n=19；已并入 6；剩余 13（含 0045A640）。
- 候选行数 = 1（0045A640）；四环齐全数 = 1；delta 行数 = 1。
- 并入后 S08 = 10/22 ⇒ 不达标（差 1 行）。

## ③b 基率（S08 池内随机取 N 行，seed 20261119，2000 次）
- strict（D-42 ③b 合同闭合：多路闸/可证伪错误码/≥10 字段形状/完整循环 I/O）= 9/19 = 47.37%。
- loose（体内有出向调用 call/indirect_call）= 10/19 = 52.63%。
- N=1：mean_strict 0.4750 / mean_loose 0.5135；P(all strict) 0.4750 / P(all loose) 0.5135。
- N=8（对照前卡）：mean 3.7920 / 4.1670；P(all strict)=0 / P(all loose)=0.0005。
- 不报「K=行数×均值」作校验（恒等式零鉴别力，判据 3）。

## 必做行 0045A640（operator==）四环
- ① 入口：+0x00 push ebx，+0x33 ret 4，函数体 0x45A640..0x45A67B（63 B）。
- ② 持有表（全部枚举）：vt 007E44F4 slot1 @007E44F8 → COL 007FC528/TD 00819230/`.?AV?$DynamicVectorClass@PAVFoggedObjectClass@@@@`；vt 007E4514 slot1 @007E4518 → COL 007FC558/TD 008191F8/`.?AV?$VectorClass@PAVFoggedObjectClass@@@@`。两表同址、槽号均为 1 ⇒ 按 ⑯/R4 归基类 VectorClass<FoggedObjectClass*>。
- ③b：+0x0A 容量闸（cmp esi,[edi+8]；+0x0D jne 假）、+0x1D~+0x2C 逐元读→cmp→inc/add→cmp→jl 完整循环 I/O、+0x30 mov al,1 / +0x38 xor al,al 可证伪 bool，ret 4。
- ④ livevt：direct E8/E9 = 0；vt 007E44F4 slot1 活表，装表点 00457BFD/00483A61/00486AF2（堆对象 ctor）+ 004D076D（全局 0x8B3D10 静态初值），均非 atexit；atexit dtor 0x4D079E 装的是基类表 007E4514，不作活表。site 未被其它 proved 行使用。

## 其余 13 行评估（不进 delta）
- 0040D250 裸 ret；0045A070/0045AC00 Clear（单次 free+字段写，无循环/错误码）；0045A0A0/0045AC70 GetItemIndex（无循环）；0045A0C0 GetItem（4 条线性）；0045AB00/0045AC90 dtor；004D27B0 B8 3D 桩；004D2910 getter —— 全 ③a。
- 0045AB50/0045AC30：③b 体成立但 ④ 失败（007E4514 非活表；007E44F4 slot10/12 不存在），前卡已列黑名单，不硬凑。

## 状态
完成：1 行交付（0045A640）。S08 并入后 10/22，未达标。详见 EVIDENCE/PROOFS.md、UNKNOWNS.md、DISAGREE.md。
