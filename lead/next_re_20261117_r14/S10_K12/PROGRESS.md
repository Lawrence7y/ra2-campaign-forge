# S10-K12 PROGRESS（返工卡：修 S10-K9 的 5 行；≤50 行）
卡号 S10-K12；gamemd.exe SHA 73201CC0…F67476（只读，现场复算一致）；Python3.12.10 + capstone5.0.7(skipdata)+pefile，无 Ghidra。成稿 2026-11-18T06:03+08。
## 现场基线（只读第 5 列、大小写归一；时点 06:01:07+08）
coverage.tsv size=3657872 mtime=05:58:20.882+08 sha=314E19BC…A349FA0（K9 读时 05:01/9EF239C2…EC94 已变）；atlas sha=4527079B…DB69。
S10 528 行、∩atlas 526、表外 2；第 5 列 [已证]109/[静态推断]404/[未证]13；proved 109/526=20.7224%，门槛 263，差 154。5 个目标行当前均 [静态推断]/slot 名。
K9 的 107→本卡 109 为外部并发并表，本卡未写台账。证据 EVIDENCE/BASELINE_RING1_CALLEES.txt。
## 四项返工修正
1. RTTI 读法：vt=0x7EB058；COL 在 vt-4=0x7EB054=0x8033B8；vt-8=0x7EB050=0x410230 是函数指针、非 COL；COL+0xC→TD 0x825508，TD+8 内联 `.?AVInfantryClass@@`。K9「vt-8→COL」撤回，本卡全程用 vt[-1]=COL。
2. 0051BAB0 退 [静态推断]：004DAEE1 mov esi,[esi+0x694]、004DAEEB mov ecx,[esi+0x69c]、004DAEF3 call [edx+0x5c]，接收者是二跳子对象且类未钉死；slot0x5C 129 处调用无外部 Infantry 点（唯一同类 0051BB7A 在函数自身）；名仅覆盖尾部<2%。不入 delta。
3. 005B3A00 语义更正：实测 `mov eax,[ecx+0xAC]; shl eax,5; add eax,0xA8E3A8; ret`，是 mission 索引的 32B 表项取址器；台账 S12/[未证]/sub_（去盘上查，不信卡面）。行5 语义串已改，非删除析构；环④改用 ControlledByHuman+RandomRanged [已证] 独立闭合，未因更正失效。
4. 「环④互不共用同一证据」**撤回**：审计实测 slot342=0051D6F0 是本批行1，行2/3/4/5 原环④皆落本批；行3 环③=行4、行4 环④=行3 双向互引。本卡每行环③/④改用外部证据，同一份证据只计一环。
## 逐行修后结论（delta 4 行，behavioral/conflict=0/n_sources=4）
0051D6F0 [已证]（本批依赖根）：环① 0x816CAC[27..31]；环②自写 +0x6C4/+100/+104/+108/+10C/+F8/+6DB；环③外部 00521760(slot58) push 0x21/1/0、ecx=this；环④ RandomRanged 0065C7E0 [已证](S05)，另有 GetMapCoords/TryGetCellAt/GetAnimSpeed/PlayAt [已证]。
0051DAF0 [已证]：环②+0x6DC；环③外部 005180FE@00517FA0、0051A6CA@00519630、0051ABD1@0051AA40（ecx=this、无栈参）；环④ StopMoving 004D55C0 [已证](S10,conf=1,盘查)+FrameCRC+GetCellLevel [已证]。丢弃 [v+0x558]→0051D6F0 同批环④。
0051B1F0 [已证]：环② +0x68D/+0x2A8 对/+0x5E0=-1/+0x68E=0；环③外部 0051F39D@0051F330、0051F7AF@0051F6E0（单 target 参、ecx=this）；环④ 006FCDB0 AssignOrClearTargetAndNotifySpawnManager [已证](S10,conf=0,src=4)+00523340 WhatAmI [已证]。丢弃 0051BBEF@0051BAB0 与 [v+0x558] 同批互引。
00522340 [已证]（语义已更正）：环②+0x6E4=1；环③外部 004D473A@FootClass::slot151（ecx=this、arg0）；环④ ControlledByHuman 0050B730 [已证](S14)+RandomRanged 0065C7E0 [已证]+RaiseError/IsDirty [已证]；005B3A00 仅作取址器表述、不入环④。丢弃 [v+0x558] 同批互引。
0051BAB0 [静态推断]（退级）：环③失败＋命名以偏概全，见修正 2。
## 结算
模拟 proved 109→113/526=21.4829%，门槛仍差 150；named_L/S 513→517，strict 73→77（现场复算）。delta 4 行/9 列、entry/name 唯一、0 placeholder、锚点全命中：EVIDENCE/DELTA_VALIDATE.txt。
证据：BASELINE_RING1_CALLEES.txt、RECHECK_RTTI_5B3A00.txt、DISASM_ALL.txt、ROW_PROOFS.txt；脚本 work/。未写台账、未改游戏文件、未 git commit。