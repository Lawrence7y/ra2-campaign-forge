"""S18: which branches gate the locomotion dispatch 0x4DA877 (call [ecx+0x40]) inside
FootClass::AI, and does any of them implement a frame-modulo test?

Uses the same edge-removal criterion as S3.
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


B, E = edges_of(0x4DA530)
T = 0x4DA877
addrs = B.addrs()
base = reach(0x4DA530, E)
p('target %08X reachable by default: %s' % (T, T in base))
p()
p('=== branches that gate the locomotion dispatch ===')
rows = []
for a in addrs:
    ins = B.insns[a]
    if not (ins.mnemonic.startswith('j') and ins.mnemonic != 'jmp'):
        continue
    if not (ins.operands and ins.operands[0].type == X86_OP_IMM):
        continue
    no_t = reach(0x4DA530, E, {(a, 't')})
    no_f = reach(0x4DA530, E, {(a, 'f')})
    skips = T not in no_t
    required = T not in no_f
    if skips or required:
        rows.append((a, skips, required))
for a, skips, required in rows:
    i = addrs.index(a)
    tag = ('SKIPS ' if skips else '') + ('REQUIRED' if required else '')
    p('  %08X  %-28s %s' % (a, L.fmt(B.insns[a]), tag))
    for c in addrs[max(0, i - 9):i]:
        p('        ' + L.fmt(B.insns[c]))
    p()

p('=== any of the gating branches preceded by a frame-counter division? ===')
p('  frame reads in FootClass::AI at: %s'
  % [hex(a) for a in addrs if any(
      op.type == X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0
      and (op.mem.disp & 0xFFFFFFFF) == 0xA8ED84
      for op in B.insns[a].operands)])
p('  div/idiv in FootClass::AI at: %s'
  % [hex(a) for a in addrs if B.insns[a].mnemonic in ('div', 'idiv')])
for a in addrs:
    if B.insns[a].mnemonic not in ('div', 'idiv'):
        continue
    i = addrs.index(a)
    p('  --- div at %08X' % a)
    for c in addrs[max(0, i - 8):i + 8]:
        p('      ' + L.fmt(B.insns[c]))

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'EVIDENCE',
                       'S18_loco_dispatch_gates.txt'), 'w', encoding='utf-8') as fh:
    fh.write('\n'.join(OUT) + '\n')
