"""S16: all frame-counter (0xA8ED84) uses inside the movement chain, and the scope of the
`frame % 10` gate found at 0x4B07A8 in the Drive wrapper.
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
       (0x429A90, 'A* container'), (0x4DA530, 'FootClass::AI')]
p('=== 1. references to the frame counter 0xA8ED84 inside the movement chain ===')
for fn, nm in FNS:
    B = L.body(fn, maxspan=0x9000)
    hits = []
    for a in B.addrs():
        ins = B.insns[a]
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0 and \
                    (op.mem.disp & 0xFFFFFFFF) == 0xA8ED84:
                hits.append((a, L.fmt(ins)))
    if hits:
        p('  %s %08X: %d ref(s)' % (nm, fn, len(hits)))
        for a, s in hits:
            p('      ' + s)

p()
p('=== 2. the frame%10 gate in the Drive wrapper: bytes + which instructions it skips ===')
B = L.body(0x4B0500)
for a in B.addrs():
    if 0x4B0795 <= a <= 0x4B0830:
        p('  ' + L.fmt(B.insns[a]))

def edges_of(entry, maxspan=0x9000):
    B = L.body(entry, maxspan=maxspan)
    E = {}
    for a, ins in B.insns.items():
        nxt = a + ins.size
        s = []
        mn = ins.mnemonic
        if mn == 'call':
            s.append(('cont', nxt))
        elif mn == 'jmp':
            op = ins.operands[0] if ins.operands else None
            if op is not None and op.type == X86_OP_IMM:
                s.append(('j', op.imm & 0xFFFFFFFF))
            else:
                for t in L._resolve_jmptable(ins):
                    s.append(('jt', t))
        elif mn.startswith('j') and ins.operands and ins.operands[0].type == X86_OP_IMM:
            s.append(('t', ins.operands[0].imm & 0xFFFFFFFF))
            s.append(('f', nxt))
        elif mn in ('ret', 'retf', 'iret', 'iretd', 'hlt'):
            pass
        else:
            s.append(('seq', nxt))
        E[a] = s
    return B, E


def reach(entry, E, banned=()):
    seen = {entry}
    work = [entry]
    while work:
        a = work.pop()
        for k, t in E.get(a, ()):
            if (a, k) in banned:
                continue
            if t in E and t not in seen:
                seen.add(t)
                work.append(t)
    return seen


Bw, Ew = edges_of(0x4B0500)
G = 0x4B07AC          # jne 0x4B0828  (frame % 10 != 0 -> skip)
p()
p('  gate instruction: %s' % L.fmt(Bw.insns[G]))
no_f = reach(0x4B0500, Ew, {(G, 'f')})   # forced to take the jump == frame%10 != 0
no_t = reach(0x4B0500, Ew, {(G, 't')})   # frame%10 == 0 -> block runs
p('  reachable when frame%%10 != 0 : %d' % len(no_f))
p('  reachable when frame%%10 == 0 : %d' % len(no_t))
p('  block only reachable when frame%%10==0 : %d insns, addresses 0x%X..0x%X'
  % (len(no_t - no_f), min(no_t - no_f), max(no_t - no_f)))
for a in sorted(no_t - no_f):
    p('     ' + L.fmt(Bw.insns[a]))

p()
p('=== 3. identity probe of 0x421EA0 (called from the frame%10 block) ===')
B4 = L.body(0x421EA0, maxspan=0x1000)
p('  insns=%d calls=%s' % (len(B4.insns), [(hex(a), hex(v) if v else 'virt') for a, v in sorted(B4.calls.items())][:14]))
for a in B4.addrs()[:28]:
    p('  ' + L.fmt(B4.insns[a]))

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'EVIDENCE',
                       'S16_frame_gates.txt'), 'w', encoding='utf-8') as fh:
    fh.write('\n'.join(OUT) + '\n')
