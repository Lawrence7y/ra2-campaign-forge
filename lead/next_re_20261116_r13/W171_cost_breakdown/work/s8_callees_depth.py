"""S8: identity + size of every direct callee of the Drive wrapper, deeper closure probing
for the grid-chain primitives, and the per-sub-step instruction accounting inputs.
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


def head(fn, n=6, maxspan=0x9000):
    B = L.body(fn, maxspan=maxspan)
    out = []
    for a in B.addrs()[:n]:
        out.append(L.fmt(B.insns[a]))
    return len(B.insns), out


p('=== 1. every direct callee of Drive wrapper 0x4B0500: size + first insns ===')
B = L.body(0x4B0500)
done = set()
for a in sorted(B.calls):
    t = B.calls[a]
    if t is None or t in done:
        continue
    done.add(t)
    try:
        n, hd = head(t)
    except Exception as e:
        n, hd = -1, [str(e)]
    p('  site %08X -> %08X  insns=%d' % (a, t, n))
    for s in hd:
        p('        ' + s)

p()
p('=== 2. direct callees of Drive Process 0x4B2630 that are NOT in the wrapper list ===')
B2 = L.body(0x4B2630, maxspan=0x9000)
seen2 = {}
for a in sorted(B2.calls):
    t = B2.calls[a]
    if t is None:
        continue
    seen2.setdefault(t, a)
for t, a in sorted(seen2.items(), key=lambda kv: -len(L.body(kv[0], maxspan=0x9000).insns))[:22]:
    try:
        n, hd = head(t, 3)
    except Exception:
        n, hd = -1, []
    p('  %08X (first site %08X) insns=%d | %s' % (t, a, n, hd[0] if hd else ''))

p()
p('=== 3. depth probe: at what depth do the grid-chain primitives appear from 0x4B0500? ===')
targets = {0x47E8A0: 'chain insert', 0x47EA90: 'chain remove', 0x5683C0: 'wrapper insert',
           0x5687F0: 'wrapper remove', 0x47C620: 'per-cell check', 0x5657A0: 'MapClass::GetCell?',
           0x56DC20: 'map helper', 0x42C900: 'FindPath', 0x429A90: 'A* container'}
frontier = [0x4B0500]
seen = set()
depth_of = {}
for d in range(0, 9):
    nxt = []
    for f in frontier:
        if f in seen:
            continue
        seen.add(f)
        depth_of[f] = d
        Bx = L.body(f, maxspan=0x9000)
        for site, t in Bx.calls.items():
            if t is not None and L.in_text(t) and t not in seen:
                nxt.append(t)
    frontier = nxt
    p('  after depth %d: visited %d fns' % (d, len(seen)))
for t, nm in targets.items():
    p('  %-22s %08X depth = %s' % (nm, t, depth_of.get(t, 'NOT REACHED <=8')))

p()
p('=== 4. any function in the depth<=8 closure that writes [reg+0xE4] or [reg+0xE8]? ===')
for f in sorted(seen):
    Bx = L.body(f, maxspan=0x9000)
    w = []
    for a in Bx.addrs():
        ins = Bx.insns[a]
        if ins.operands and ins.operands[0].type == X86_OP_MEM and \
                ins.operands[0].mem.disp in (0xe4, 0xe8) and \
                ins.mnemonic in ('mov', 'lea', 'and', 'or', 'add', 'sub', 'xchg'):
            w.append((a, L.fmt(ins)))
    if w:
        p('  %08X  %d site(s)' % (f, len(w)))
        for a, s in w[:8]:
            p('      ' + s)

p()
p('=== 5. who references the cell-table global 0x87F924 inside the closure? ===')
cnt = 0
for f in sorted(seen):
    Bx = L.body(f, maxspan=0x9000)
    hits = []
    for a in Bx.addrs():
        ins = Bx.insns[a]
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0 and \
                    (op.mem.disp & 0xFFFFFFFF) == 0x87F924:
                hits.append(L.fmt(ins))
    if hits:
        cnt += 1
        p('  %08X (%d refs)' % (f, len(hits)))
        for s in hits[:4]:
            p('      ' + s)
p('  total functions referencing 0x87F924 in closure: %d' % cnt)

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'EVIDENCE',
                       'S8_callees_depth.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(OUT) + '\n')
