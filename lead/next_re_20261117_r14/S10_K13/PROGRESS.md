# S10-K13 PROGRESS（≤60 行）
卡号 S10-K13；gamemd.exe SHA-256 73201CC0…F67476（现场只读复算一致）；Python 3.12.10 + capstone 5.0.7(skipdata=True) + pefile 2024.8.26；未用 Ghidra。
## 现场基线（2026-11-18T06:32:17+08:00 读盘；统一大小写，grade 只读第 5 列）
COVERAGE size=3,659,848 sha=CA5CE493…E887979 mtime=06:29:37+08；atlas sha=4527079B…A73653DB69。S10 528 行、∩atlas 526、表外 2；[已证]113/[静态推断]400/[未证]13 ⇒ 113/526=21.4829%，门槛 263，差 150；named_L/S 513/526=97.5285%。证据 EVIDENCE/BASELINE.txt。卡面基线 113 与盘面一致。
## 本轮视角与得行
1. 族级非 mission 状态机（Reload）：**0 行**。006FB010 字节上确认“[this+0x2FC] 计数到期 → push 2 调 [v+0x124] → StartReloading 006FB080”，但环①的 push 2 无本批外已证枚举语义，StartReloading 只能计环④ ⇒ fail-closed，不入 delta；证据 PROOF_6FB010.txt。
2. 目标选择/威胁评估与伤害结果通知：**2 行**。004D7330 以 DamageState(0..5)+外部 ExitUnit 闭合；004D85D0 以 Mission 名表 0x816CAC[1/11/15/21]+WhatAmI 0xF 与外部 TryGetCellAt/RandomRanged 闭合。
3. 武器/弹药状态（SetAmmo/GetAmmo/HasAmmo）：**0 行**。全表已证关键词扫描无任何已证 SetAmmo/GetAmmo/HasAmmo；S10 非已证行中只有 006FB010 的 StartReloading 调用，已按视角 1 排除；不把“reload”词形当语义。
4. 升级/veterancy：**0 行**。全表已证关键词扫描 veteran/experience/promote/rank/upgrade 为 0；S10 非已证候选关键词仅命中 Mission_Unload/Repair/Attack 三个 B8 imm32 C3 桩（K3 已穷尽），未重复。
## 交付 2 行（9 列；n_sources=4，conflict=0，name_kind=behavioral）
- 004D7330 [已证] FootClass::ApplyDamageAndCacheSubobjectNotification_behavior；环① DamageState 5/0/4（00701900 盘面 [已证] 语义，仅计此环）；环②自写 [this+0x694]->+0x69C+0x2C 描述符；环③外部 callers 004165EC/00518042/00737D52 的 ecx=this 与七栈参；环④ 0062A4A0 ParasiteClass::ExitUnit（S13、[已证]、本批外）。证据 PROOF_4D7330.txt。
- 004D85D0 [已证] AircraftClass::ApplyMode2CellRefreshWithSubcellCounters_behavior；环① 0x816CAC mission 表与 WhatAmI=0xF；环②自写 +0x6B0/+0x6B2/+0x55C/+0x5E0；环③外部 callers 0051A9FC/0073A4FB/0073B0A0；环④ 005657A0 TryGetCellAt(S06)+0065C7E0 RandomRanged(S05)，均盘面 [已证] 且本批外。证据 PROOF_4D85D0.txt。
## 核心数字复算
A=执行 work/baseline.py：atlas entry 小写归一后与 coverage entry 小写相交，子系统取 S10，grade 只读 split('\t')[4]。B=执行 work/validate_delta.py：delta 行数/列数/entry 唯一/name 唯一/placeholder/evidence 路径。C=两行环④盘面级：执行 work/callee_validate.py（0062A4A0、005657A0、0065C7E0 均 [已证]）。
结算：模拟 proved 113→115/526=21.6730%，门槛仍差 148；named_L/S 513→515。未写台账、未改游戏文件、未 git commit。
