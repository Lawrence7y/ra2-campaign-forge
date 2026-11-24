"""S2: the pathfinding chain 0x4B0500 -> 0x4B2630 -> 0x4D3920 -> 0x4CBBA0 -> 0x42C900 -> A* core.

Counts (CFG channel = control-flow discovered, NOT atlas entry+size) + every gate that can
skip the FindPath call.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w171_lib as L

OUT = []


def p(*a):
    s = ' '.join(str(x) for x in a)
    OUT.append(s)
    print(s)


def report(fn, label, maxspan=0x8000):
    B = L.body(fn, maxspan=maxspan)
    lo, hi = min(B.insns), max(B.insns) + B.insns[max(B.insns)].size
    p('%s  %08X  cfg_insns=%d  calls=%d (imm %d / virt %d)  span=%08X..%08X (%d B)'
      % (label, fn, len(B.insns), len(B.calls),
         sum(1 for v in B.calls.values() if v is not None), len(B.vcalls), lo, hi, hi - lo))
    return B


from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

p('=== A. chain members ===')
B_drive = report(0x4B0500, 'Drive Process wrapper')
B_proc = report(0x4B2630, 'Drive big Process')
B_upd = report(0x4D3920, 'FootClass::UpdatePathfinding')
B_cfp = report(0x4CBBA0, 'CallFindPath')
B_fp = report(0x42C900, 'PathFinder::FindPath')
B_sc = report(0x429A90, 'fn 0x429A90 (A*-core container)')

p()
p('=== B. Drive wrapper: call sites of the big Process 0x4B2630 ===')
for a in sorted(B_drive.calls):
    if B_drive.calls[a] == 0x4B2630:
        p('  site %08X' % a)

p()
p('=== C. Drive big Process 0x4B2630: all direct calls (sorted by site) ===')
for a in sorted(B_drive.calls):
    t = B_drive.calls[a]
    if t is not None:
        p('  %08X -> %08X' % (a, t))
p('  virtual call sites: %d' % len(B_drive.vcalls))
for a in B_drive.vcalls:
    p('    ' + L.fmt(B_drive.insns[a]))

p()
p('=== D. UpdatePathfinding 0x4D3920: all direct calls (sorted by site) ===')
for a in sorted(B_upd.calls):
    t = B_upd.calls[a]
    if t is not None:
        p('  %08X -> %08X' % (a, t))
p('  virtual call sites: %d' % len(B_upd.vcalls))
for a in B_upd.vcalls:
    p('    ' + L.fmt(B_upd.insns[a]))

p()
p('=== E. UpdatePathfinding: gates that can skip the FindPath call ===')
CALLSITE = None
for a in sorted(B_upd.calls):
    if B_upd.calls[a] in (0x4CBBA0, 0x42C900, 0x4D3920):
        p('  candidate target %08X first reached from site %08X' % (B_upd.calls[a], a))
p('  calls to 0x4CBBA0 inside 0x4D3920: %s'
  % [hex(a) for a in B_upd.calls if B_upd.calls[a] == 0x4CBBA0])
tgt_sites = [a for a in B_upd.calls if B_upd.calls[a] == 0x4CBBA0]
if tgt_sites:
    CS = min(tgt_sites)
    p('  using call site %08X as the "recompute" point; enumerating jcc with target > it' % CS)
    addrs = B_upd.addrs()
    for a in addrs:
        ins = B_upd.insns[a]
        if ins.mnemonic.startswith('j') and ins.mnemonic != 'jmp' and ins.operands and \
                ins.operands[0].type == X86_OP_IMM:
            t = ins.operands[0].imm & 0xFFFFFFFF
            if t > CS:
                idx = addrs.index(a)
                ctx = addrs[max(0, idx - 8):idx]
                p('  --- skip gate @%08X -> %08X (%s)' % (a, t, L.fmt(ins)))
                for c in ctx:
                    p('        ' + L.fmt(B_upd.insns[c]))

p()
p('=== F. CallFindPath 0x4CBBA0: full body ===')
for a in B_cfp.addrs():
    p('  ' + L.fmt(B_cfp.insns[a]))

p()
p('=== G. FindPath 0x42C900: call sites into the A* core region 0x429A90..0x42A45D ===')
for a in sorted(B_fp.calls):
    t = B_fp.calls[a]
    if t is not None:
        p('  %08X -> %08X%s' % (a, t, '   <A* container>' if t == 0x429A90 else ''))

p()
p('=== H. A* container 0x429A90: instruction budget of the inner loop ===')
p('  total cfg_insns = %d' % len(B_sc.insns))
p('  reference (upstream): fn 0x429A90 = 2509 B ending 0x42A45D; core loop 0x429D6D..0x42A3D8')
core = [a for a in B_sc.addrs() if 0x429D6D <= a < 0x42A3D8]
p('  instructions with addr in [0x429D6D,0x42A3D8) = %d' % len(core))
# back edges: jcc/jmp whose target < own address (within function)
p('  backward jumps (loop back edges) in whole function:')
for a in B_sc.addrs():
    ins = B_sc.insns[a]
    if ins.mnemonic.startswith('j') and ins.operands and ins.operands[0].type == X86_OP_IMM:
        t = ins.operands[0].imm & 0xFFFFFFFF
        if t < a:
            p('    %08X -> %08X   (%s)  span=%d insns' % (a, t, L.fmt(ins), len([x for x in B_sc.addrs() if t <= x <= a])))
    if ins.mnemonic == 'jmp' and ins.operands and ins.operands[0].type == X86_OP_IMM:
        t = ins.operands[0].imm & 0xFFFFFFFF
        if t < a:
            p('    %08X -> %08X   (%s) [jmp] span=%d' % (a, t, L.fmt(ins), len([x for x in B_sc.addrs() if t <= x <= a])))

p()
p('=== I. rounds cap 0xFFF7 near 0x429D59 ===')
for a in B_sc.addrs():
    if 0x429D40 <= a <= 0x429D70:
        p('  ' + L.fmt(B_sc.insns[a]))
p('  raw bytes 0x429D59..0x429D60 = %s' % L.rd(0x429D59, 8).hex())

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'EVIDENCE',
                       'S2_pathchain.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(OUT) + '\n')
