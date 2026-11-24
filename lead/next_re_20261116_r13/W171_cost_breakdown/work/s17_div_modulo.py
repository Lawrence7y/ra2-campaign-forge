"""S17: every integer division / modulo in the movement chain, to find any additional
frame-based throttle.  Also prints the context of each frame-counter read in
UpdatePathfinding and Drive::Process that feeds a division.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w171_lib as L
from capstone.x86 import X86_OP_IMM, X86_OP_MEM

OUT = []


def p(*a):
    s = ' '.join(str(x) for x in a)
    OUT.append(s)
    print(s)


FNS = [(0x4B0500, 'Drive wrapper'), (0x4B2630, 'Drive::Process'), (0x4B0F20, 'Drive helper'),
       (0x4D3920, 'UpdatePathfinding'), (0x4CBBA0, 'CallFindPath'), (0x42C900, 'FindPath'),
       (0x429A90, 'A* container')]
p('=== 1. every div/idiv in the movement chain ===')
for fn, nm in FNS:
    B = L.body(fn, maxspan=0x9000)
    for a in B.addrs():
        ins = B.insns[a]
        if ins.mnemonic in ('div', 'idiv'):
            addrs = B.addrs()
            i = addrs.index(a)
            p('  %s %08X : %s' % (nm, a, L.fmt(ins)))
            for c in addrs[max(0, i - 6):i + 6]:
                p('        ' + L.fmt(B.insns[c]))

p()
p('=== 2. context of the two frame reads in UpdatePathfinding ===')
B = L.body(0x4D3920)
addrs = B.addrs()
for site in (0x4D3EB2, 0x4D401C):
    i = addrs.index(site)
    p('  --- %08X' % site)
    for a in addrs[max(0, i - 10):i + 14]:
        p('      ' + L.fmt(B.insns[a]))

p()
p('=== 3. context of the frame reads in Drive::Process (all 9) ===')
B2 = L.body(0x4B2630, maxspan=0x9000)
a2 = B2.addrs()
for site in (0x4B281F, 0x4B3673, 0x4B3693, 0x4B372A, 0x4B3A5F, 0x4B3AEB, 0x4B3C10, 0x4B425B, 0x4B452E):
    i = a2.index(site)
    p('  --- %08X' % site)
    for a in a2[max(0, i - 5):i + 9]:
        p('      ' + L.fmt(B2.insns[a]))

p()
p('=== 4. A*: any use of the frame counter? (none expected) ===')
B3 = L.body(0x429A90)
c = 0
for a in B3.addrs():
    for op in B3.insns[a].operands:
        if op.type == X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0 and \
                (op.mem.disp & 0xFFFFFFFF) == 0xA8ED84:
            c += 1
            p('  ' + L.fmt(B3.insns[a]))
p('  count = %d' % c)

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'EVIDENCE',
                       'S17_div_modulo.txt'), 'w', encoding='utf-8') as fh:
    fh.write('\n'.join(OUT) + '\n')
