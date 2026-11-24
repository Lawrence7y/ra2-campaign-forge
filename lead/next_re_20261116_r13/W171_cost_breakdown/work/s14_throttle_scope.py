"""S14: resolve the contradiction between W164 ("the throttle does NOT gate the locomotion
process; pathfinding is deeper in the subclass AI") and R12_FACTS 18 ("the throttle gates
the movement/pathfinding block").

Method: reachability with the 0x4DA568 `jne` edge forced on/off, then locate every
`call [reg+0x40]` / `call [reg+0x84]` (locomotion process slot) relative to that gate.
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


p('=== 1. FootClass::AI 0x4DA530 prologue and the throttle ===')
B, E = edges_of(0x4DA530)
addrs = B.addrs()
for a in addrs[:26]:
    p('  ' + L.fmt(B.insns[a]))
GATE = 0x4DA568
p('  gate instruction: %s' % L.fmt(B.insns[GATE]))
p('  taken target    : %08X' % (B.insns[GATE].operands[0].imm & 0xFFFFFFFF))

p()
p('=== 2. instruction split around the throttle ===')
pre = [a for a in addrs if a < GATE]
post = [a for a in addrs if a >= GATE]
p('  insns at addr < gate  : %d' % len(pre))
p('  insns at addr >= gate : %d' % len(post))
skip = B.insns[GATE].operands[0].imm & 0xFFFFFFFF
Ran = reach(0x4DA530, E, {(GATE, 'f')})          # throttle fires: jump taken
Rnot = reach(0x4DA530, E, {(GATE, 't')})         # not divisible: fallthrough
p('  reachable when throttle FIRES (frame%%N!=0): %d insns' % len(Ran))
p('  reachable when throttle PASSES (frame%%N==0): %d insns' % len(Rnot))
p('  instructions reachable only in the PASS case: %d' % len(Rnot - Ran))

p()
p('=== 3. every indirect call in FootClass::AI with its displacement, and whether it is '
  'gated ===')
for a in addrs:
    ins = B.insns[a]
    if ins.mnemonic != 'call':
        continue
    op = ins.operands[0] if ins.operands else None
    if op is not None and op.type == X86_OP_MEM:
        disp = op.mem.disp
        p('  site %08X  disp=0x%-5X  in PASS-only set: %-5s  in FIRES set: %-5s  %s'
          % (a, disp, a in (Rnot - Ran), a in Ran, ins.op_str))
    elif op is not None and op.type == X86_OP_IMM:
        p('  site %08X  direct -> %08X  PASS-only:%-5s FIRES:%s'
          % (a, op.imm & 0xFFFFFFFF, a in (Rnot - Ran), a in Ran))

p()
p('=== 4. does FootClass::AI call the locomotion process slot (+0x40 / +0x84) at all? ===')
p('  (scan of its indirect call displacements above; +0x84 and +0x40 are the candidates)')

p()
p('=== 5. UnitClass::AI 0x7360C0 / InfantryClass::AI 0x51BAB0 / AircraftClass::AI 0x414BB0: '
  'where do they call FootClass::AI and the locomotion process? ===')
for fn, nm in ((0x7360C0, 'UnitClass::AI'), (0x51BAB0, 'InfantryClass::AI'),
               (0x414BB0, 'AircraftClass::AI')):
    Bx, Ex = edges_of(fn, maxspan=0x4000)
    p('  --- %s %08X  insns=%d' % (nm, fn, len(Bx.insns)))
    for a in sorted(Bx.calls):
        v = Bx.calls[a]
        ins = Bx.insns[a]
        if v is not None:
            if v in (0x4DA530,):
                p('      %08X -> %08X  (FootClass::AI)' % (a, v))
        else:
            op = ins.operands[0]
            if op.type == X86_OP_MEM:
                p('      %08X  virt disp=0x%X  %s' % (a, op.mem.disp, ins.op_str))

p()
p('=== 6. the 0x4DA694 / 0x4DA69C locomotion-pointer call mentioned by W164, in context ===')
for a in addrs:
    if 0x4DAED0 <= a <= 0x4DAF10:
        p('  ' + L.fmt(B.insns[a]))

p()
p('=== 7. where is the +/-0x674 loco pointer read inside FootClass::AI? ===')
for a in addrs:
    ins = B.insns[a]
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.disp in (0x674, 0x694, 0x69c, 0x278):
            p('  %-6s %s' % ('PASS-only' if a in (Rnot - Ran) else
                             ('FIRES' if a in Ran else 'common'), L.fmt(ins)))

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'EVIDENCE',
                       'S14_throttle_scope.txt'), 'w', encoding='utf-8') as fh:
    fh.write('\n'.join(OUT) + '\n')
