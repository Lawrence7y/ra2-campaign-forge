"""S11: multiplicity and gating structure.
  (1) confirm no branch in 0x4D3920 can bypass the FindPath call,
  (2) how many UpdatePathfinding calls can one Drive::Process invocation make,
  (3) how many Drive::Process calls can one wrapper invocation make,
  (4) identity of the globals compared against the loco position (0x8A0790/94/98).
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


def edges_of(entry, maxspan=0x4000):
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


def reach(entry, E, banned=(), extra=()):
    seen = {entry}
    work = [entry] + list(extra)
    for x in extra:
        seen.add(x)
    while work:
        a = work.pop()
        for k, t in E.get(a, ()):
            if (a, k) in banned:
                continue
            if t in E and t not in seen:
                seen.add(t)
                work.append(t)
    return seen


# (1)
B, E = edges_of(0x4D3920)
CALL = 0x4D3E4B
bad = [(a, B.insns[a].op_str) for a in B.insns
       if B.insns[a].mnemonic.startswith('j') and B.insns[a].mnemonic != 'jmp'
       and B.insns[a].operands and B.insns[a].operands[0].type == X86_OP_IMM
       and a < CALL < (B.insns[a].operands[0].imm & 0xFFFFFFFF)]
p('(1) branches with site < %08X < target (i.e. able to bypass the FindPath call): %d  %s'
  % (CALL, len(bad), bad))
p('    jcc total in 0x4D3920: %d ; jumps to the 0x4D3E0A join point: %s'
  % (len([a for a in B.insns if B.insns[a].mnemonic.startswith('j')
          and B.insns[a].mnemonic != 'jmp']),
     [hex(a) for a in B.insns if B.insns[a].mnemonic.startswith('j')
      and B.insns[a].mnemonic != 'jmp' and B.insns[a].operands
      and B.insns[a].operands[0].type == X86_OP_IMM
      and (B.insns[a].operands[0].imm & 0xFFFFFFFF) == 0x4D3E0A]))

# (2)
p()
p('(2) UpdatePathfinding call sites inside Drive::Process 0x4B2630')
B2, E2 = edges_of(0x4B2630, maxspan=0x9000)
sites = sorted(a for a, v in B2.calls.items() if v == 0x4D3920)
p('    sites: %s' % [hex(x) for x in sites])
for i, s in enumerate(sites):
    conts = [t for k, t in E2[s] if k == 'cont']
    cont = conts[0]
    R = reach(cont, E2)
    others = [hex(x) for x in sites if x != s and x in R]
    p('    after site %08X returns -> reachable later call sites: %s' % (s, others))
# can one invocation reach site1 then site2 then site3?
p('    cycles that contain 2+ UpdatePathfinding sites: searching...')
cnt = 0
for a in sorted(B2.insns):
    for k, t in E2[a]:
        if t <= a:
            R = reach(t, E2)
            got = [x for x in sites if t <= x <= a]
            if len(got) >= 2:
                p('      back edge %08X -> %08X encloses sites %s' % (a, t, [hex(x) for x in got]))
                cnt += 1
p('    loops enclosing 2+ sites: %d' % cnt)

# (3)
p()
p('(3) Drive::Process call sites inside the wrapper 0x4B0500, and the retry loop')
B1, E1 = edges_of(0x4B0500)
wsites = sorted(a for a, v in B1.calls.items() if v == 0x4B2630)
p('    sites: %s' % [hex(x) for x in wsites])
for a in sorted(B1.insns):
    for k, t in E1[a]:
        if t <= a:
            got = [x for x in wsites if t <= x <= a]
            p('    back edge %08X -> %08X  encloses wrapper Process sites %s' % (a, t, [hex(x) for x in got]))

# (4)
p()
p('(4) the three globals compared against [loco+0x30..0x3c] / [obj+0x9c..] : 0x8A0790/94/98')
for g in (0x8A0790, 0x8A0794, 0x8A0798):
    p('    static dword at %08X = %08X' % (g, L.u32(g)))
p('    all .text instructions with an absolute operand == one of those addresses:')
m = L.md()
data = L.PE.__data__[L.TEXT['raw']:L.TEXT['raw'] + L.TEXT['rawsize']]
hits = 0
fns = {}
for ins in m.disasm(data, L.TEXT_LO):
    if ins.id == 0:
        continue
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0 and \
                (op.mem.disp & 0xFFFFFFFF) in (0x8A0790, 0x8A0794, 0x8A0798):
            hits += 1
            if hits <= 24:
                p('      ' + L.fmt(ins))
p('    total refs = %d' % hits)

p()
p('(5) writes to those globals (who maintains the "current cell" triple?)')
for g, nm in ((0x8A0790, '0x8A0790'), (0x8A0794, '0x8A0794'), (0x8A0798, '0x8A0798')):
    f = 0
    for ins in m.disasm(data, L.TEXT_LO):
        if ins.id == 0:
            continue
        if ins.operands and ins.operands[0].type == X86_OP_MEM and \
                ins.operands[0].mem.base == 0 and ins.operands[0].mem.index == 0 and \
                (ins.operands[0].mem.disp & 0xFFFFFFFF) == g and ins.mnemonic.startswith('mov'):
            f += 1
            if f <= 6:
                p('    %s <- %s' % (nm, L.fmt(ins)))
    p('    %s writes = %d' % (nm, f))

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'EVIDENCE',
                       'S11_multiplicity.txt'), 'w', encoding='utf-8') as fh:
    fh.write('\n'.join(OUT) + '\n')
