"""S6: trace the A* round budget.

0x429D59 stores 0xFFF7 into [esp+0x70] but ONLY under `test eax,eax / jge`
(i.e. when [esp+0x70] is negative).  So 0xFFF7 is a *default*, and the real
loop bound is whatever [esp+0x70] holds when it is >= 0.
This script finds every write to [esp+0x70] inside 0x429A90 and follows the
provenance of the value that reaches it.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w171_lib as L
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

OUT = []


def p(*a):
    s = ' '.join(str(x) for x in a)
    OUT.append(s)
    print(s)


B = L.body(0x429A90)
addrs = B.addrs()

p('=== 1. prologue of 0x429A90 (first 30 insns) ===')
for a in addrs[:30]:
    p('  ' + L.fmt(B.insns[a]))

p()
p('=== 2. every reference to [esp+0x70] inside 0x429A90 ===')
for a in addrs:
    ins = B.insns[a]
    for k, op in enumerate(ins.operands):
        if op.type == X86_OP_MEM and op.mem.base and ins.reg_name(op.mem.base) == 'esp' \
                and op.mem.index == 0 and op.mem.disp == 0x70:
            w = (k == 0 and ins.mnemonic in
                 ('mov', 'movzx', 'movsx', 'lea', 'add', 'sub', 'or', 'and', 'inc', 'dec', 'xchg'))
            p('  %-6s %s' % ('WRITE' if w else 'read', L.fmt(ins)))

p()
p('=== 3. every reference to [esp+0x28] (the counter compared against it) ===')
for a in addrs:
    ins = B.insns[a]
    for k, op in enumerate(ins.operands):
        if op.type == X86_OP_MEM and op.mem.base and ins.reg_name(op.mem.base) == 'esp' \
                and op.mem.index == 0 and op.mem.disp == 0x28:
            w = (k == 0 and ins.mnemonic in ('mov', 'lea', 'add', 'sub', 'or', 'and', 'inc',
                                             'dec', 'xchg', 'movsx', 'movzx'))
            p('  %-6s %s' % ('WRITE' if w else 'read', L.fmt(ins)))

p()
p('=== 4. frame size and parameter area of 0x429A90 ===')
mx = 0
allesp = []
for a in addrs:
    ins = B.insns[a]
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base and ins.reg_name(op.mem.base) == 'esp' \
                and op.mem.index == 0:
            allesp.append((op.mem.disp, a, L.fmt(ins)))
            mx = max(mx, op.mem.disp)
p('  max [esp+N] = 0x%X' % mx)
p('  distinct [esp+N] values (sorted):')
seen = sorted(set(d for d, a, s in allesp))
p('    %s' % [hex(x) for x in seen])
p('  references with disp >= 0x1f00 (candidate parameter area):')
for d, a, s in allesp:
    if d >= 0x1f00:
        p('    %s' % s)

p()
p('=== 5. the call into 0x429A90 from FindPath (0x42CC02) and its arg push sequence ===')
for a in addrs:
    pass
Bf = L.body(0x42C900)
fa = Bf.addrs()
i = fa.index(0x42CC02)
for a in fa[max(0, i - 30):i + 4]:
    p('  ' + L.fmt(Bf.insns[a]))

p()
p('=== 6. FindPath 0x42C900 prologue + frame ===')
for a in fa[:26]:
    p('  ' + L.fmt(Bf.insns[a]))
mx2 = 0
for a in fa:
    ins = Bf.insns[a]
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base and ins.reg_name(op.mem.base) == 'esp' \
                and op.mem.index == 0:
            mx2 = max(mx2, op.mem.disp)
p('  max [esp+N] in FindPath = 0x%X' % mx2)

p()
p('=== 7. is 0x42CC02 inside a loop of FindPath? (back edges) ===')
for a in fa:
    ins = Bf.insns[a]
    if ins.mnemonic.startswith('j') and ins.operands and ins.operands[0].type == X86_OP_IMM:
        t = ins.operands[0].imm & 0xFFFFFFFF
        if t <= a:
            p('  latch %08X -> %08X (%s) spans 0x42CC02? %s'
              % (a, t, ins.mnemonic, t <= 0x42CC02 <= a))

p()
p('=== 8. follow 0x7D0 (=2000) as an immediate through the chain ===')
p('  CallFindPath 0x4CBBA0 pushes 0x7d0 at site 0x4D3E3B (from UpdatePathfinding).')
p('  disasm of UpdatePathfinding around 0x4D3E20..0x4D3E52:')
B2 = L.body(0x4D3920)
for a in B2.addrs():
    if 0x4D3E10 <= a <= 0x4D3E52:
        p('    ' + L.fmt(B2.insns[a]))

p()
p('=== 9. all immediates 0x7d0 / 0x7D0 in the path chain functions ===')
for fn, nm in ((0x429A90, 'A* container'), (0x42C900, 'FindPath'), (0x4CBBA0, 'CallFindPath'),
               (0x4D3920, 'UpdatePathfinding'), (0x4B2630, 'Drive Process')):
    Bx = L.body(fn, maxspan=0x9000)
    for a in Bx.addrs():
        ins = Bx.insns[a]
        for op in ins.operands:
            if op.type == X86_OP_IMM and (op.imm & 0xFFFFFFFF) in (0x7d0, 0xfffff):
                p('  %-16s %s' % (nm, L.fmt(ins)))

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'EVIDENCE',
                       'S6_budget.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(OUT) + '\n')
