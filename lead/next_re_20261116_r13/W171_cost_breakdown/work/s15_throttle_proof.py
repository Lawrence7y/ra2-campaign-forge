"""S15: evidence-quality dump of the two facts that decide this card.

  (A) the throttled block 0x4DA554..0x4DA648 (what `frame % N` actually skips)
  (B) the unthrottled locomotion dispatch: `mov eax,[esi+0x674]` ... `call [ecx+0x40]`
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w171_lib as L

OUT = []


def p(*a):
    s = ' '.join(str(x) for x in a)
    OUT.append(s)
    print(s)


B = L.body(0x4DA530)
addrs = B.addrs()

p('=== (A) 0x4DA544..0x4DA648 : throttle site, gated block, join point ===')
for a in addrs:
    if 0x4DA544 <= a <= 0x4DA648:
        mark = ''
        if a == 0x4DA568:
            mark = '   <<<<< throttle gate: jne -> 0x4DA63B (skip block when frame%N != 0)'
        p('  ' + L.fmt(B.insns[a]) + mark)

p()
p('=== (B) 0x4DA850..0x4DA8A0 : unthrottled locomotion Process dispatch ===')
for a in addrs:
    if 0x4DA850 <= a <= 0x4DA8A0:
        mark = ''
        if a == 0x4DA877:
            mark = '   <<<<< call [ecx+0x40] = Locomotion off4-slot16 = Drive::Process 0x4B0500'
        p('  ' + L.fmt(B.insns[a]) + mark)

p()
p('=== (C) all reads/writes of [esi+0x674] with the raw bytes (loco pointer) ===')
for a in addrs:
    ins = B.insns[a]
    for op in ins.operands:
        if op.type == L.X86_OP_MEM and op.mem.disp == 0x674 and op.mem.base:
            p('  %08X  %s' % (a, L.fmt(ins)))

p()
p('=== (D) verify slot +0x40 of the Drive off4 table == Drive::Process 0x4B0500 ===')
p('  [0x7E7EB0 + 0x40] = %08X' % L.u32(0x7E7EB0 + 0x40))
p('  mean? UnitClass main vt 0x7F5C70 + 0x40 = %08X (unrelated table)' % L.u32(0x7F5C70 + 0x40))
p('  Drive off4 vt = 0x7E7EB0 (from R12_FACTS 16.1) ; [vt+0x40]=0x%08X' % L.u32(0x7E7EB0 + 0x40))

p()
p('=== (E) instruction accounting of the throttled block ===')
skip_set = [a for a in addrs if 0x4DA569 <= a < 0x4DA63B]
p('  instructions with address in [0x4DA569, 0x4DA63B) = %d' % len(skip_set))
p('  those instructions:')
for a in skip_set:
    p('    ' + L.fmt(B.insns[a]))

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'EVIDENCE',
                       'S15_throttle_proof.txt'), 'w', encoding='utf-8') as fh:
    fh.write('\n'.join(OUT) + '\n')
