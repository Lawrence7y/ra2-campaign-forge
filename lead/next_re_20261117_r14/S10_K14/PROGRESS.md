# S10-K14 PROGRESS（≤40 行）
卡号 S10-K14；只修 004D85D0；gamemd.exe SHA-256 73201CC0…F67476（现场复算一致）；Python 3.12.10 + capstone 5.0.7(skipdata=True) + pefile 2024.8.26；未用 Ghidra。
## 现场基线（2026-11-18T06:45:12.882805+08:00 读盘；统一大小写；grade 只读第 5 列）
COV sha=CA5CE493…E887979 mtime=06:29:37+08；ATL sha=4527079B…A73653DB69；S10 528 / ∩atlas 526 / 表外 2；[已证]113/[静态推断]400/[未证]13 ⇒ 113/526=21.4829%；named_L=513/526=97.5285%。证据 EVIDENCE/BASELINE.txt。
## 三处硬伤逐条复核（独立脚本，见 work/ 与 EVIDENCE/）
① 0x816CAC：004D85D0 全部 739 条指令中 operand-imm 0 次、原始字节 0 次；全 .text 有 12 处字面量，均在 0x5B374D..0x5B3955，按指令边界全为 dword[idx*4+0x816CAC]。目标实际 4 次调用 [vt+0x184]（4D891A/4D8929/4D8938/4D8947），比较 0x15/0x0B/0x01/0x0F；+0x184=005B3040，字节为 mov eax,[ecx+0xAC]; cmp -1; mov eax,[ecx+0xB4]; ret。覆盖表 005B3040 虽 [已证]，但名 AircraftClass::slot97 且语义栏自注“槽语义未证”。⇒ 原 0x816CAC Mission 表表述删除；环①无外部已证枚举锚点。
② 幽灵环④：004D85D0 共 40 个 direct call，目标表无 0065C7E0；operand 与 rel32 解码双查 0 次。所谓收尾是 4D8ED7/4D8F24 call 006F5090（覆盖表 [静态推断]，不能作环④）。真实可锚定的是 005657A0 MapClass::TryGetCellAt，8 次直接调用，盘面 [已证] S06、conflict=1（仅名字争议）。⇒ 幽灵依据删除，环④改用 005657A0。
③ 类归属：RTTI 链 COL+0xC→TD+8 实测 vt 0x7E8C94=.?AVFootClass@@、vt 0x7E22A4=.?AVAircraftClass@@，两者 slot0x18C 均为 004D85D0。InfantryClass 0x519630 在 0x51A9FC 以 ecx=esi 调它；UnitClass 0x739EC0 在 0x73A4FB(push 2, ecx=ebp) 与 0x73B0A0(ecx=ebp) 调它。vt+0x2C imm 实测 Unit=1/Aircraft=2/Building=6/Infantry=0xF。⇒ FootClass 级实现，0xF 分支活；前缀改 FootClass::。
## 剩余环数判定
环①缺：目标确有枚举式比较，但比较源是内部 getter [vt+0x184] 与 WhatAmI [vt+0x2C]；+0x184 的 mission 语义没有本类写点+读点双支撑，覆盖表也注明槽语义未证；0x816CAC 已证为 0 引用。补足需：对 +0xAC/+0xB4 做同类写点溯源并命名，或找到盘面 [已证] 的外部 mission 枚举函数覆盖 0x15/0x0B/0x01/0x0F。
环②在：mode==2 分支清 byte [this+0x6B0]/[this+0x6B2]；按 8 项 stride-4 (short,short) 表 0x89F688 重算 packed cell [this+0x55C]，经 5657A0 访问后 dec/inc cell byte +0x122；条件写 [this+0x5E0]=0xFFFFFFFF。
环③在：0x51A9FC / 0x73A4FB / 0x73B0A0 三处外部 caller 均 mov ecx,this 后 call 004D85D0；其中 Unit 一处 push 2 与入口 arg==2 自洽。
环④在：005657A0 [已证] S06、本批外；8 次直接调用均有 lea/push 坐标参数，形成真实外部地图查询锚点。
⇒ 去掉编造环①与幽灵环④依据后剩三环（②③④），不是四环；按派卡口径交 1 行 [静态推断]，绝不补造环①。
## 交付行（9 列；name_kind=behavioral）
004D85D0 / S10 / FootClass::Mode2CellAndMissionStateRefresh_behavior / [静态推断] / EVIDENCE/PROOF_004D85D0.txt#004D85D0 / n_sources=3 / conflict=0。
## 纪律
004D7330 保持 PASS 已并状态，未碰；未写台账、未改游戏文件、未 git commit。
