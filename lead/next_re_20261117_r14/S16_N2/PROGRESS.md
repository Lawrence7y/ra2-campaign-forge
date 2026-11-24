# S16-N2 · PROGRESS（最终）

卡号 S16-N2｜目标 ra2youli\gamemd.exe SHA-256 73201CC0…F67476（只读，自算一致）｜系统 Python 3.12 + capstone 5.0.7 + pefile（无 venv、无 pip）。

## 结论：**新增真名 0 条**（硬禁令 2 允许的合格交付）

## ① 盘上自算（⑨ 停机核验）
coverage.tsv 制表符分列：S16 全表 **92** 行；atlas∩coverage **90** 行（atlas 外 2 行 = 004F8440/004F9370）。
盘上（N1 已并入）：atlas∩coverage **named 81/90 = 90.00%**、**proved 46/90 = 51.11%**。
卡面「73 / 46」是 N1 并入前截面；现盘 81 已含 N1 8 名 ⇒ **不自造差异、按盘上记账**。
剩余 sub_ 恰好 **9** 条（与卡面清单逐字一致）：00430BA0 0053A6C0 0053D8E0 0053DDA0 0065E660 006CE240 006CE2D0 006CE320 0071AB60。
交付后 named/proved **不变**：**81/90 · 46/90**（零余量状态未改善，如实报告）。

## ② 逐条双通道核验（A=二进制，B=异源）——全部不达「真名」门槛
| entry | A（体内指令/字段，带偏移） | B（异源原文行） | 裁定 |
|---|---|---|---|
| 00430BA0 | alloc 0x114 +0x42；读 0x89C430/434/438 写 obj+0/+4/+8 +0x55；Beacon.CPP 串 +0xD11 | CONFLICT_CLASS2/CLASSIFIED.tsv:9 + S16-K3 VERDICT ★D：BeaconClass::sub_ = 占位；台账 32614/32654：无 RTTI、方法名未知 | 拒：占位名违禁令 1 |
| 0053A6C0 | 状态 0xA9FABC +0x0/0x58；计时 0x827FCC/C8 +0x11/0x67；遍历 Bolts/Clouds +0x8C..；call 0x53AF40/53B560/53A300 | 台账 32611：LightningStorm 状态机 tick，但方法名未知；CLASSIFIED.tsv:104 占位 | 拒：无真名 |
| 0053D8E0 | dec edx +0x0；按 8 递减计环 +0xE..+0x1B；写 [eax]=环/[eax+4]=偏移 +0x27/0x29 | 台账 32165 U4：螺旋坐标分解输入 edx 语义未追全，本卡未命名交付 | 拒：语义≠方法名 |
| 0053DDA0 | Count−1 +0xB；左移 +0x13..+0x24；ret 4 +0x29 | C08 known_hits.tsv:1928 仅 caller=IonBlastClass::Update；台账无真名 | 拒：调用者≠被调名；18 命中同码不特异 |
| 0065E660 | 数组 0xA8B21C +0x3/C；v[0x8C] +0x41；byte+0x3D4=1 +0x5E；call 0x4AA440 +0x96（7 参入栈 +0x7B..+0x95） | docs/re/superweapon_re.md:783-784 + re_sprint_S2:139-140 写 SpawnAircraftEdge (0x65E660 -> 0x4AA440)；但 radar_sweep:64 把该名给 0x4AA440，YRpp MapClass.h:287 亦把 0x4AA440 定为 PickCellOnEdge；0x65E660 YRpp 全库 0 绑定 | 拒：名归属冲突，按 ⑱ fail-closed |
| 006CE240 | 三分量逐项相加 +0xD..+0x27；ret 8 | C08 known_hits.tsv:329 仅 caller=SuperClass::Launch；YRpp 0 绑定 | 拒：无真名 |
| 006CE2D0 | v[0x10] 取键 +0xC；Count−1 +0x1B；左移 +0x23..+0x33；ret 4 | 台账 32617 按键向量删除，方法名未知；CLASSIFIED.tsv:202 占位 | 拒：占位名违禁令 1 |
| 006CE320 | 与 0053DDA0 逐字节同构；ret 4 | C08 known_hits.tsv:337 仅 caller=SuperClass::ClickFire；YRpp 0 绑定 | 拒：调用者≠被调名 |
| 0071AB60 | cmp [esi+0x24] +0xB；call 0x71ABC0 +0x1A；[esi+0x28]=0 +0x1F | YRpp TemporalClass.h:43 绑 0x71ABC0=LetGo（被调函数），但 0x71AB60 本身 0 绑定；台账/N1 U1 TemporalClass 未列名 | 拒：被调者名不能转嫁调用者 |

## ③ 误命中基线（**只准一个数**）
9 条候选中 YRpp 地址绑定 **0** 条；docs/re 带名字的记录 **1** 条（0065E660，且归属冲突）。
按「docs/re 名字记录」判据随机抽 3 条期望误命中 = 3×1/9 = **0.33**（唯一值，复算 work/baseline.py）。
该基线本身已说明：即使接受 0065E660 也无判别力。

## ④ 盘上现 grade → 本卡交付 grade（逐行，不虚报「未动」）
| entry | 盘上现 grade | 本卡交付 grade | 说明 |
|---|---|---|---|
| 00430BA0 | [静态推断] | [静态推断] | 核后未改 |
| 0053A6C0 | [静态推断] | [静态推断] | 核后未改 |
| 0053D8E0 | [未证] | [未证] | 核后未改 |
| 0053DDA0 | [未证] | [未证] | 核后未改 |
| 0065E660 | [未证] | [未证] | 核后未改 |
| 006CE240 | [未证] | [未证] | 核后未改 |
| 006CE2D0 | [未证] | [未证] | 核后未改 |
| 006CE320 | [未证] | [未证] | 核后未改 |
| 0071AB60 | [未证] | [未证] | 核后未改 |
全部 9 行均逐行读盘确认，**无一行 grade 变动**；proved 前后各算一次均 46/90，非「声称未动」。

## ⑤ 已试通道（全列）
YRpp 全 2188 文件按 6/8 位十六进制大小写全扫(0 命中)；docs/re 403 文件(仅 1 名字记录且冲突)；re_atlas/kb 8 文件(0)；台账+S16-K1/K2/K3/N1 全部 UNKNOWNS/VERDICT(只给语义不给名)；全镜像 dword 指针扫描(vtable 归属 0 命中)；capstone 全体反汇编至 ret(有序)；CONFLICT_CLASS2(仅占位)。
未创建 venv、未 pip install、未改 COVERAGE/台账/游戏文件、未 commit。
