"""S4: inside Drive::Process 0x4B2630 - what gates the three UpdatePathfinding call sites,
and what the wrapper's gate actually changes.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w171_lib as L
from capstone.x86 import X86_OP_IMM

OUT = []


def p(*a):
    s = ' '.join(str(x) for x in a)
    OUT.append(s)
    print(s)


B = L.body(0x4B2630, maxspan=0x9000)

p('=== head of 0x4B2630: first 90 reachable instructions (address order) ===')
addr = B.addrs()
for a in addr[:90]:
    p('  ' + L.fmt(B.insns[a]))

p()
p('=== 0x4B28A3 call site context (0x4B2860..0x4B28C0) ===')
for a in addr:
    if 0x4B2860 <= a < 0x4B28C0:
        p('  ' + L.fmt(B.insns[a]))

p()
p('=== 0x4B3A0E call site context (0x4B39D0..0x4B3A30) ===')
for a in addr:
    if 0x4B39D0 <= a < 0x4B3A30:
        p('  ' + L.fmt(B.insns[a]))

p()
p('=== 0x4B3F37 call site context (0x4B3EF0..0x4B3F60) ===')
for a in addr:
    if 0x4B3EF0 <= a < 0x4B3F60:
        p('  ' + L.fmt(B.insns[a]))

p()
p('=== gate sources: the SKIPS branches and their tested fields ===')
for site in (0x4B2706, 0x4B2719, 0x4B274E, 0x4B2761, 0x4B329B, 0x4B33A5, 0x4B33FA,
             0x4B3439, 0x4B3650, 0x4B3E77, 0x4B3EE7):
    i = addr.index(site)
    p('  --- gate %08X : %s' % (site, L.fmt(B.insns[site])))
    for c in addr[max(0, i - 10):i]:
        p('        ' + L.fmt(B.insns[c]))

p()
p('=== does 0x4B2630 itself read the loco gate fields +0x54 / +0x5F ? ===')
for a in addr:
    ins = B.insns[a]
    for op in ins.operands:
        if op.type == L.X86_OP_MEM:
            base = ins.reg_name(op.mem.base) if op.mem.base else ''
            if op.mem.base and op.mem.index == 0 and op.mem.disp in (0x54, 0x5f) and base in ('esi', 'edi', 'ebp', 'ecx', 'eax', 'edx'):
                p('  ' + L.fmt(ins))

p()
p('=== 0x4B2630 arg region math: max [esp+N] over the body ===')
mx = 0
for a in addr:
    for op in B.insns[a].operands:
        if op.type == L.X86_OP_MEM and op.mem.base and B.insns[a].reg_name(op.mem.base) == 'esp' \
                and op.mem.index == 0:
            mx = max(mx, op.mem.disp)
p('  max [esp+N] = 0x%X' % mx)

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'EVIDENCE',
                       'S4_process_gates.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(OUT) + '\n')
