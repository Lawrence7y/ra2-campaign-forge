"""S3b: precise path A vs path B accounting for the Drive wrapper, plus the
UpdatePathfinding 0x4D3920 prelude dump.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w171_lib as L
from capstone.x86 import X86_OP_IMM


def cfg_edges(entry, maxspan=0x4000):
    B = L.body(entry, maxspan=maxspan)
    edges = {}
    for a, ins in B.insns.items():
        nxt = a + ins.size
        succ = []
        mn = ins.mnemonic
        if mn == 'call':
            succ.append(('call_ret', nxt))
        elif mn == 'jmp':
            op = ins.operands[0] if ins.operands else None
            if op is not None and op.type == X86_OP_IMM:
                succ.append(('jmp', op.imm & 0xFFFFFFFF))
            else:
                for t in L._resolve_jmptable(ins):
                    succ.append(('jmp_tbl', t))
        elif mn.startswith('j') and ins.operands and ins.operands[0].type == X86_OP_IMM:
            succ.append(('jcc_t', ins.operands[0].imm & 0xFFFFFFFF))
            succ.append(('jcc_f', nxt))
        elif mn in ('ret', 'retf', 'iret', 'iretd', 'hlt'):
            pass
        else:
            succ.append(('seq', nxt))
        edges[a] = succ
    return B, edges


def reach(entry, edges, banned):
    seen = {entry}
    work = [entry]
    while work:
        a = work.pop()
        for kind, t in edges.get(a, ()):
            if (a, kind) in banned:
                continue
            if t in edges and t not in seen:
                seen.add(t)
                work.append(t)
    return seen


S = None

OUT = []


def p(*a):
    s = ' '.join(str(x) for x in a)
    OUT.append(s)
    print(s)


B1, E1 = cfg_edges(0x4B0500)
A = reach(0x4B0500, E1, {(0x4B0564, 'jcc_f'), (0x4B056D, 'jcc_f')})
Bs = reach(0x4B0500, E1, {(0x4B0564, 'jcc_t'), (0x4B056D, 'jcc_t')})
p('path A (gates TAKEN: [+0x54]==-1 or [+0x5F]==0) reachable insns = %d' % len(A))
p('  reaches big-Process site 4B0647? %s   site 4B0A79? %s   0x4B0573 (post-gate)? %s'
  % (0x4B0647 in A, 0x4B0A79 in A, 0x4B0573 in A))
p('path B (gates NOT taken: has target and moving) reachable insns = %d' % len(Bs))
p('  reaches big-Process site 4B0647? %s   site 4B0A79? %s   0x4B066C? %s'
  % (0x4B0647 in Bs, 0x4B0A79 in Bs, 0x4B066C in Bs))
p('A-only insns = %d ; B-only insns = %d ; common = %d'
  % (len(set(A) - set(Bs)), len(set(Bs) - set(A)), len(set(A) & set(Bs))))

p()
p('=== path A block trace: every reachable instruction in A that is NOT in B ===')
for a in sorted(set(A) - set(Bs)):
    p('  ' + L.fmt(B1.insns[a]))

p()
p('=== 0x4D3920 prelude 0x4D3920..0x4D39F8 (full instruction list) ===')
B2 = L.body(0x4D3920)
for a in B2.addrs():
    if 0x4D3920 <= a < 0x4D39F8:
        p('  ' + L.fmt(B2.insns[a]))

p()
p('=== 0x4D3920 around the FindPath call 0x4D3DC0..0x4D3E70 ===')
for a in B2.addrs():
    if 0x4D3DC0 <= a < 0x4D3E70:
        p('  ' + L.fmt(B2.insns[a]))

p()
p('=== what is [vtable+0x2CC] for UnitClass main table 0x7F5C70 / InfantryClass 0x7EB058 / FootClass 0x7F5F48? ===')
for vt, name in ((0x7F5C70, 'UnitClass main'), (0x7EB058, 'InfantryClass main'),
                 (0x7E22A4, 'AircraftClass main')):
    try:
        v = L.u32(vt + 0x2CC)
        p('  %s vt=%08X  [+0x2CC] = %08X %s' % (name, vt, v, 'IN_TEXT' if L.in_text(v) else ''))
        if L.in_text(v):
            bb = L.body(v, maxspan=0x400)
            for a in bb.addrs()[:14]:
                p('      ' + L.fmt(bb.insns[a]))
    except Exception as e:
        p('  %s: %s' % (name, e))

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'EVIDENCE',
                       'S3b_pathAB_prelude.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(OUT) + '\n')
