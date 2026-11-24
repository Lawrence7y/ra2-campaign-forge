"""S7: (a) A* argument / round-counter semantics, (b) depth<=3 closure of the Drive
wrapper with per-function instruction counts (CFG channel, no atlas bounds), (c) which
closure members touch the cell/occupancy structures.
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


B = L.body(0x429A90)
addrs = B.addrs()

p('=== (a) A* 0x429A90: uses of the argument slots [esp+0x60..0x78] ===')
for a in addrs:
    ins = B.insns[a]
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base and ins.reg_name(op.mem.base) == 'esp' \
                and op.mem.index == 0 and 0x58 <= op.mem.disp <= 0x78:
            p('  ' + L.fmt(ins))

p()
p('=== (a2) A* round counter [esp+0x28]: where it is incremented (0x42A3C0..0x42A3E0) ===')
for a in addrs:
    if 0x42A3B8 <= a <= 0x42A3E4:
        p('  ' + L.fmt(B.insns[a]))

p()
p('=== (a3) loop header 0x429D6D..0x429DC2 (bound test) ===')
for a in addrs:
    if 0x429D61 <= a <= 0x429DD0:
        p('  ' + L.fmt(B.insns[a]))

p()
p('=== (a4) the A* exit path 0x42A3DE..0x42A45D ===')
for a in addrs:
    if 0x42A3DE <= a < 0x42A460:
        p('  ' + L.fmt(B.insns[a]))

p()
p('=== (a5) does anything else compare/branch on [esp+0x14] (the "more work" flag)? ===')
for a in addrs:
    ins = B.insns[a]
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base and ins.reg_name(op.mem.base) == 'esp' \
                and op.mem.index == 0 and op.mem.disp == 0x14:
            p('  ' + L.fmt(ins))

# ---------------- (b) closure -----------------
p()
p('=== (b) depth<=3 closure from Drive wrapper 0x4B0500 (CFG channel) ===')
levels = L.closure(0x4B0500, 3, maxspan=0x9000)
for r in levels:
    p('  depth %d : fns=%d  insns=%d  call_sites=%d' % (r['depth'], r['fns'], r['insns'], r['calls']))
p('  cumulative fns = %d  cumulative insns = %d'
  % (sum(r['fns'] for r in levels), sum(r['insns'] for r in levels)))

p()
p('=== (b2) membership test: are the grid/chain primitives inside the depth<=3 closure? ===')
frontier = [0x4B0500]
seen = set()
fn_insns = {}
for d in range(4):
    nxt = []
    for f in frontier:
        if f in seen:
            continue
        seen.add(f)
        Bx = L.body(f, maxspan=0x9000)
        fn_insns[f] = len(Bx.insns)
        for site, t in Bx.calls.items():
            if t is not None and L.in_text(t) and t not in seen:
                nxt.append(t)
    frontier = nxt
for probe, name in ((0x47E8A0, 'grid chain INSERT (0x5683C0 wrapper)'),
                    (0x47EA90, 'grid chain REMOVE (0x5687F0 wrapper)'),
                    (0x5683C0, 'wrapper insert'),
                    (0x5687F0, 'wrapper remove'),
                    (0x47C620, 'per-cell can-place check'),
                    (0x4D3920, 'UpdatePathfinding'),
                    (0x4CBBA0, 'CallFindPath'),
                    (0x42C900, 'FindPath'),
                    (0x429A90, 'A* container'),
                    (0x421EA0, '0x421EA0 (called from Drive at 0x4B0823)')):
    p('  %-42s %08X in depth<=3 closure: %s' % (name, probe, probe in fn_insns))

p()
p('=== (b3) depth<=3 closure membership, all functions with instruction counts ===')
for f in sorted(fn_insns, key=lambda x: -fn_insns[x]):
    p('  %08X  insns=%-5d  %s' % (f, fn_insns[f], L.fmt(L.body(f, maxspan=0x9000).insns[f])))

p()
p('=== (b4) which closure members reference the cell table 0x87F924 / write [x+0xE4]/[x+0xE8]? ===')
for f in sorted(fn_insns):
    Bx = L.body(f, maxspan=0x9000)
    hits = []
    for a in Bx.addrs():
        ins = Bx.insns[a]
        for op in ins.operands:
            if op.type == X86_OP_MEM:
                if op.mem.base == 0 and op.mem.index == 0 and (op.mem.disp & 0xFFFFFFFF) == 0x87F924:
                    hits.append(('celltable', a, L.fmt(ins)))
                if op.mem.disp in (0xe4, 0xe8) and op.mem.base:
                    hits.append(('cell+e4/e8', a, L.fmt(ins)))
    if hits:
        p('  %08X:' % f)
        for k, a, s in hits[:12]:
            p('     [%s] %s' % (k, s))

p()
p('=== (b5) per-function: does it contain a write to [reg+0xE4] / [reg+0xE8]? ===')
for f in sorted(fn_insns):
    Bx = L.body(f, maxspan=0x9000)
    w = []
    for a in Bx.addrs():
        ins = Bx.insns[a]
        if ins.operands and ins.operands[0].type == X86_OP_MEM and \
                ins.operands[0].mem.disp in (0xe4, 0xe8) and ins.mnemonic in ('mov', 'lea', 'add', 'sub', 'and', 'or'):
            w.append(L.fmt(ins))
    if w:
        p('  %08X writes/lea [x+0xE4|0xE8]: %d site(s)' % (f, len(w)))
        for s in w[:6]:
            p('     ' + s)

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'EVIDENCE',
                       'S7_argcount_closure.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(OUT) + '\n')
