# S10-K7 PROGRESS（≤40 行）
时点 2026-11-18T04:20+08。gamemd.exe SHA-256 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476，size 4825360；只读。Python 3.12.10 + capstone 5.0.7(skipdata=True) + pefile 2024.8.26；无 Ghidra；写域仅本卡。
现场读盘 coverage.tsv：size 3652533、mtime 2026-11-18T04:05:20+08、SHA C4805489...CAF43。统一大小写后 S10 行 528、∩atlas 526、第5列 [已证] 92=17.490494%，与 S10_K5/_audit/VERDICT.md 卡面一致，无纪律9停机。若按全部 528 行算是 93，差额是表外 005B3740 已 [已证]，非口径漂移。
目标行现场第5列均为非 [已证]：006B7010 与 004E0E80 均 sub_ 占位；本卡只闭合这两行。

## 结论表（2 行）
| entry | 新名 | grade | 证据 |
|---|---|---|---|
| 006B7010 | SpawnManagerClass::~SpawnManagerClass | [已证] | EVIDENCE/CLOSEOUT_006B7010.txt#006B7010；EVIDENCE/CLOSEOUT_CHECKS.txt |
| 004E0E80 | VectorClass<AbstractClass*>::VectorClass | [已证] | EVIDENCE/CLOSEOUT_004E0E80.txt#004E0E80；EVIDENCE/CLOSEOUT_CHECKS.txt |

## 006B7010：普通析构（非标量删除析构）
判据：本体内无 test byte [esp+8],1；006B70F3..F6=5f 5e 59 c3（pop/pop/pop/ret），不是 ret 4。标量删除包装 006B8140（虚表 007F3650 slot8 @007F3670）为 call 006B7010 → test [esp+8],1 → call 007C8B3D → ret 4，证明 006B7010 是被其调用的 dtor body。
四张虚表写入（同序）：[0]=007F3650、[4]=007F3634、[8]=007F362C、[0xC]=007F3624，位于 006B7015/701B/7022/7029。ctor 006B6C90@6B6CEF..6D03 与 006B6EA0@6B6EE6..6EFA 写同一组值、同一顺序；两者分别由 006F3F9D/006C0A3C 的 push 0x74; call 007C8E17; ecx=new; call 证明为构造器。
RTTI：四表 COL 分别 00809AE8/00809A80/00809A68/00809A50，均 COL+0xC→TD 00840120；TD+8 内联名串 2e3f4156537061776e4d616e61676572436c6173734040 = .?AVSpawnManagerClass@@。
释放：006B704F 与 006B70D2 两处 call 007C8B3D；007C8B3D=ff742404 e8a2080000 59 c3 → call 007C93E8（CRT free）。第一处释放 [edi+0x3c] 数组元素（计数 [edi+0x48]），第二处释放 owned buffer [esi+4]（flag [esi+0xd]）。
命名双源：类名由 RTTI，析构角色由调用者/vptr 回写/释放与 ret 形态；非 RTTI 单源。

## 004E0E80：同类可证（构造器）
RTTI：VT 007E920C → COL 008009E0 → TD 008225B8 → TD+8 内联名串 .?AV?$VectorClass@PAVAbstractClass@@@@。004E0E80 无精确 u32 vtable slot 命中，构造器本就非虚函数；本卡不把 slot 归属当升级证据。
字节：写 [esi]=007E920C、[+4]/[+8]/byte[+0xC]/byte[+0xD]；arg2 非空则用外部 buffer，arg2=0 则 shl eax,2; call 007C8E17 分配 capacity*4 并置拥有标记；尾 mov eax,esi; pop esi; ret 8。函数内唯一 call 是 007C8E17（new wrapper），无 007C8B3D/007C93E8，故不是析构。
调用者：capstone 校验 8 个直接 E8 调用点（004D32A5/32D6、004DB419/4C7、0050CC16、006F43E7/4402、007095E2）；例 004D3285..32AA 为 lea edi,[esi+588]; push 0; push 0; mov ecx,edi; call 004E0E80，随后 caller 写派生 vptr 007E91EC。命名双源：类名 RTTI + 构造角色（ecx=this、两栈参、ret 8、caller 形态）互相独立。

## 核心数字（供审计复算）
2 行 delta；006B7010 四虚表地址 007F3650/007F3634/007F362C/007F3624；RTTI TD 00840120，TD+8 名串如上；delete wrapper 007C8B3D→free 007C93E8（两处调用 006B704F/006B70D2）；004E0E80 RTTI TD 008225B8、new wrapper 007C8E17、直接调用者 8。复算脚本 work/baseline_recompute.py、work/verify_closeout.py；原始输出 EVIDENCE/targeted_proof.txt、EVIDENCE/caller_and_ctor_context.txt、EVIDENCE/CLOSEOUT_CHECKS.txt。
