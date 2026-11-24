"""S10: (1) prove mechanically that no branch between 0x4D399F and the FindPath call can
skip it;  (2) resolve the two `call [reg+0x124]` (slot 73) sites in UpdatePathfinding to
UnitClass's slot-73 implementation and its chain primitives (virtual-call path, which the
plain call-graph closure cannot see).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w171_lib as L
from capstone.x86 import X86_OP_IMM

OUT = []


def p(*a):
    s = ' '.join(str(x) for x in a)
    OUT.append(s)
    print(s)


p('=== 1. every conditional branch in UpdatePathfinding 0x4D3920 (site -> target) ===')
B = L.body(0x4D3920)
addrs = B.addrs()
CALL = 0x4D3E4B
bad = []
for a in addrs:
    ins = B.insns[a]
    if ins.mnemonic.startswith('j') and ins.mnemonic != 'jmp' and ins.operands and \
            ins.operands[0].type == X86_OP_IMM:
        t = ins.operands[0].imm & 0xFFFFFFFF
        flag = ''
        if a < CALL < t:
            flag = '  <<< SKIPS FindPath call'
            bad.append((a, t))
        p('  %08X -> %08X  %-6s %s%s' % (a, t, ins.mnemonic, ins.op_str, flag))
p()
p('  branches with site < 0x%08X < target: %d  %s' % (CALL, len(bad), bad))

p()
p('=== 2. unconditional jmps in UpdatePathfinding ===')
for a in addrs:
    ins = B.insns[a]
    if ins.mnemonic == 'jmp' and ins.operands and ins.operands[0].type == X86_OP_IMM:
        t = ins.operands[0].imm & 0xFFFFFFFF
        p('  %08X -> %08X%s' % (a, t, '   (backward)' if t < a else ''))

p()
p('=== 3. the two slot-73 (+0x124) sites inside UpdatePathfinding, with context ===')
for site in (0x4D3E11, 0x4D3EAC):
    i = addrs.index(site)
    p('  --- site %08X' % site)
    for a in addrs[max(0, i - 8):i + 8]:
        p('      ' + L.fmt(B.insns[a]))

p()
p('=== 4. UnitClass main vtable slot 73 (+0x124) -> ? ===')
for vt, nm in ((0x7F5C70, 'UnitClass'), (0x7EB058, 'InfantryClass'), (0x7E22A4, 'AircraftClass')):
    v = L.u32(vt + 0x124)
    p('  %-14s vt=%08X [+0x124] = %08X' % (nm, vt, v))
B73 = L.body(0x4D3780, maxspan=0x200)
p('  0x4D3780 cfg_insns=%d calls=%s' % (len(B73.insns),
  [(hex(a), hex(v) if v else 'virt') for a, v in sorted(B73.calls.items())]))
p('  full body:')
for a in B73.addrs():
    p('    ' + L.fmt(B73.insns[a]))

p()
p('=== 5. the chain primitives: sizes + their calls ===')
for fn, nm in ((0x5683C0, 'wrapper INSERT'), (0x5687F0, 'wrapper REMOVE'),
               (0x47E8A0, 'chain insert body'), (0x47EA90, 'chain remove body')):
    Bx = L.body(fn, maxspan=0x1000)
    p('  %-20s %08X cfg_insns=%-5d calls=%s' % (nm, fn, len(Bx.insns),
      [(hex(a), hex(v) if v else 'virt') for a, v in sorted(Bx.calls.items())][:8]))
    p('    first 10:')
    for a in Bx.addrs()[:10]:
        p('      ' + L.fmt(Bx.insns[a]))

p()
p('=== 6. do 0x5683C0 / 0x5687F0 reach 0x47E8A0 / 0x47EA90 as DIRECT calls? ===')
for fn, tgt in ((0x5683C0, 0x47E8A0), (0x5687F0, 0x47EA90)):
    Bx = L.body(fn, maxspan=0x1000)
    sites = [a for a, v in Bx.calls.items() if v == tgt]
    p('  %08X -> %08X : %s' % (fn, tgt, [hex(x) for x in sites]))

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'EVIDENCE',
                       'S10_slot73_chain.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(OUT) + '\n')
