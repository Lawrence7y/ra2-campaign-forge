"""S9: who writes the Locomotion gate fields (+0x54, +0x5E, +0x5F, +0x5A0, +0x5A4, +0x5E0)
and what their values mean.  Byte-level sweep of the whole .text for stores at those
displacements, with the base register recorded, restricted afterwards by "the base was
loaded from a Foot/loco-ish source" context printing.
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


FIELDS = (0x54, 0x5e, 0x5f, 0x5a0, 0x5a4, 0x5e0)
p('=== 1. whole-.text sweep: stores whose destination is [reg+field] ===')
m = L.md()
data = L.PE.__data__[L.TEXT['raw']:L.TEXT['raw'] + L.TEXT['rawsize']]
by_field = {f: [] for f in FIELDS}
n = 0
for ins in m.disasm(data, L.TEXT_LO):
    if ins.id == 0:
        continue
    n += 1
    if not ins.operands:
        continue
    dst = ins.operands[0]
    if dst.type != X86_OP_MEM or not dst.mem.base or dst.mem.index != 0:
        continue
    if dst.mem.disp in FIELDS and ins.mnemonic in ('mov', 'movzx', 'and', 'or', 'inc', 'dec',
                                                   'add', 'sub', 'xchg', 'not', 'neg'):
        by_field[dst.mem.disp].append((ins.address, ins.reg_name(dst.mem.base), L.fmt(ins)))
p('  .text instructions decoded = %d' % n)
for f in FIELDS:
    p('  [+0x%02X] stores = %d' % (f, len(by_field[f])))

p()
p('=== 2. [+0x54] stores (all) ===')
for a, b, s in by_field[0x54]:
    p('  ' + s)

p()
p('=== 3. [+0x5F] stores (all) ===')
for a, b, s in by_field[0x5f]:
    p('  ' + s)

p()
p('=== 4. [+0x5E] stores (all) ===')
for a, b, s in by_field[0x5e]:
    p('  ' + s)

p()
p('=== 5. [+0x5A0]/[+0x5A4]/[+0x5E0] stores (all) ===')
for f in (0x5a0, 0x5a4, 0x5e0):
    p('  --- +0x%X' % f)
    for a, b, s in by_field[f]:
        p('  ' + s)

p()
p('=== 6. context for the [+0x54] writers inside the locomotion code range ===')
for a, b, s in by_field[0x54]:
    p('  --- writer at %08X (base %s)' % (a, b))
    lo = a - 0x30
    B = L.body(a, maxspan=0x10)
    code = L.lin(lo, 0x50)
    for ins in code:
        mark = ' <== ' if ins.address == a else '      '
        p('    ' + L.fmt(ins) + mark)

p()
p('=== 7. 0x4C9480 (called at 0x4B077B) full body - it looks like a path/queue test ===')
B = L.body(0x4C9480, maxspan=0x200)
for a in B.addrs():
    p('  ' + L.fmt(B.insns[a]))

p()
p('=== 8. 0x4D3810 (slot +0x2CC, "can pathfind") full body ===')
B = L.body(0x4D3810, maxspan=0x400)
for a in B.addrs():
    p('  ' + L.fmt(B.insns[a]))

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'EVIDENCE',
                       'S9_field_writers.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(OUT) + '\n')
