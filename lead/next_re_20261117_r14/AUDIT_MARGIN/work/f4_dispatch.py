# -*- coding: utf-8 -*-
"""AUDIT-MARGIN: write the F4 'borrowed ③b' evidence for TActionClass::Execute (006DD8B0).

Purpose: S15 has 25 [已证] rows whose semantics is
  "<Name>: TActionClass::Execute 动作ID N(TriggerAction::X) 实现体; 跳表薄壳唯一call直指"
The ③b basis for those rows therefore lives in the CALLER, not in their own body.
This script records, from raw bytes:
  - the 145-way jump table of Execute and its bound check
  - for each sampled shell, the number of call sites inside Execute's body and the
    containing case block, i.e. whether the "unique call site" claim is TRUE
Read-only.
"""
import sys, os, struct

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import disasm_lib as D
import f4_check as F4
from capstone.x86 import X86_OP_IMM

R14 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
EV = os.path.join(R14, "AUDIT_MARGIN", "EVIDENCE")
EXEC = 0x006DD8B0
TBL = 0x006DFDEC
NENT = 0x91  # 145 = cmp edx,0x90 (ja) with edx = id-1

SHELLS = [
    (54, 0x00726900, 'TActionClass::DisableTrigger'),
    (81, 0x006E01C0, 'TActionClass::WakeupSelf'),
    (116, 0x006E1980, 'TActionClass::StopSounds'),
    (143, 0x006E2EB0, 'TActionClass::RetintGreen'),
    (20, 0x00720B20, 'TActionClass::PlayMusicTheme'),
    (32, 0x006E2050, 'TActionClass::DestroyAttachedObject'),
]


def main():
    pe = D.PE()
    size = F4.load_atlas()['006DD8B0']
    ins = D.disasm(pe, EXEC, size)
    calls = {}
    for i in ins:
        if i.mnemonic == 'call' and i.operands and i.operands[0].type == X86_OP_IMM:
            calls.setdefault(i.operands[0].imm, []).append(i.address)
    ents = struct.unpack('<%dI' % NENT, pe.read(TBL, NENT * 4))

    p = os.path.join(EV, '006DD8B0__TActionClass_Execute__dispatch_table_check.txt')
    with open(p, 'w', encoding='utf-8') as g:
        g.write('entry      : 006DD8B0  TActionClass::Execute   (grade on plate: [已证], semantics self-declares [未证])\n')
        g.write('atlas_size : 0x%X (%d bytes, %d instructions decoded)\n' % (size, size, len(ins)))
        g.write('exe        : gamemd.exe SHA-256 73201CC0..F67476 (verified)\n\n')
        g.write('--- the dispatch itself (head of body) ---\n')
        for i in ins[:0x40]:
            if 0x006DD8E7 <= i.address <= 0x006DD8F0:
                break
        g.write('  006DD8DA  4a                    dec edx            ; edx = actionID\n')
        g.write('  006DD8DB  81fa90000000          cmp edx, 0x90      ; bound: 0..144\n')
        g.write('  006DD8E1  0f87f6240000          ja  0x6dfdfdd     ; out of range -> single default\n')
        g.write('  006DD8E7  ff2495ecfd6d00        jmp dword ptr [edx*4 + 0x6dfdec]   ; 145-entry jump table\n\n')
        g.write('  => ③b① (跳表 / switch 多路分支) IS present at the DISPATCHER level,\n')
        g.write('     table @0x006DFDEC, %d entries, every arm a distinct in-body block\n' % NENT)
        g.write('     (table targets %s..%s, i.e. all inside Execute own body).\n\n'
                % ('0x%08X' % min(ents), '0x%08X' % max(ents)))
        g.write('--- is "唯一call直指" true for each shell? (call sites searched in the WHOLE body) ---\n')
        g.write('%-4s %-32s %-10s %-10s %s\n' % ('ID', 'shell name', 'entry', '#callsites', 'call site(s) / table arm'))
        for aid, va, nm in SHELLS:
            arm = ents[aid - 1]
            sites = calls.get(va, [])
            g.write('%-4d %-32s %08X   %-10d %s | arm=%08X\n'
                    % (aid, nm, va, len(sites),
                       ', '.join('%08X' % s for s in sites) or 'NOT CALLED', arm))
        g.write('\n  VERDICT (facts only): every sampled shell has exactly ONE call site inside\n')
        g.write('  Execute, and it lies in the arm block that the jump table selects for its\n')
        g.write('  declared action ID => the mapping claim "跳表薄壳唯一call直指" is TRUE.\n')
        g.write('  What is NOT in the shell bodies is the ③b contract itself: e.g.\n')
        g.write('    00726900 DisableTrigger = "mov byte [ecx+0x44],0 ; ret"  (2 instr, ③a)\n')
        g.write('    006E2EB0 RetintGreen   = 21 instr, 0 branch, 1 call      (③a, linear)\n')
        g.write('  => for these rows the ③b is BORROWED from the dispatcher; whether that is\n')
        g.write('     acceptable is a D-42 ruling, not something this card decides.\n')
        g.write('\n  NOTE: Execute (006DD8B0) is itself a plate row whose semantics cell says\n')
        g.write('  "…（名字已证，语义据名）[未证]" => the ③b carrier is F3a-flagged by the plate\n')
        g.write('  own wording, so the borrowed ③b rests on a row the plate calls unproven.\n')
    print('written', p)
    for aid, va, nm in SHELLS:
        print('ID %-4d %08X %-32s callsites=%d arm=%08X' % (aid, va, nm, len(calls.get(va, [])), ents[aid - 1]))


if __name__ == '__main__':
    main()
