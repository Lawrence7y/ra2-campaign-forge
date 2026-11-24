"""S13: (a) absolute (global) memory operands inside the A* body - looking for a per-round
counter that a live probe could read;  (b) dual-channel cross-check of every instruction
count against function_atlas.tsv n_instr (atlas channel), plus a linear-sweep channel.
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


p('=== (a) global (absolute-address) operands inside A* 0x429A90 ===')
B = L.body(0x429A90)
for a in B.addrs():
    ins = B.insns[a]
    for k, op in enumerate(ins.operands):
        if op.type == X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0:
            is_write = (k == 0 and ins.mnemonic in ('mov', 'add', 'sub', 'or', 'and', 'inc', 'dec', 'xchg'))
            p('  %-6s %s' % ('WRITE' if is_write else 'read', L.fmt(ins)))
p('  (the round counter is the stack local [esp+0x28] - NOT a global, see S6/S7)')

p()
p('=== (a2) global operands inside the A* outer loop body only (0x429D6D..0x42A3D8) ===')
for a in B.addrs():
    if not (0x429D6D <= a < 0x42A3D8):
        continue
    ins = B.insns[a]
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0:
            p('  ' + L.fmt(ins))

p()
p('=== (b) dual-channel instruction counts ===')
atlas = {}
with open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv',
          encoding='utf-8', errors='replace') as f:
    hdr = f.readline().rstrip('\n').split('\t')
    for line in f:
        parts = line.rstrip('\n').split('\t')
        if len(parts) < 3:
            continue
        rec = dict(zip(hdr, parts))
        try:
            atlas[int(rec['entry'], 16)] = (int(rec['size']), int(rec['n_instr']),
                                            int(rec['n_callers']), int(rec['n_callees']))
        except Exception:
            pass
p('  atlas entries = %d' % len(atlas))
p('  %-10s %-26s %8s %8s %8s %6s %6s' % ('addr', 'label', 'cfg', 'atlasN', 'lin', 'caller', 'callee'))
rows = [(0x4B0500, 'Drive Process wrapper'), (0x4B2630, 'Drive::Process'),
        (0x4D3920, 'UpdatePathfinding'), (0x4CBBA0, 'CallFindPath'),
        (0x42C900, 'PathFinder::FindPath'), (0x429A90, 'A* container'),
        (0x4D3780, 'Unit slot73'), (0x5683C0, 'chain insert wrapper'),
        (0x5687F0, 'chain remove wrapper'), (0x47E8A0, 'chain insert body'),
        (0x47EA90, 'chain remove body'), (0x4B0F20, 'Drive helper 0x4B0F20'),
        (0x4DF0D0, 'clear +0x5A0/+0x5A4'), (0x4C9480, 'path test 0x4C9480'),
        (0x4D3810, 'slot +0x2CC'), (0x421EA0, 'called from Drive 0x4B0823'),
        (0x4DA530, 'FootClass::AI'), (0x46B640, 'frame stamp')]
for va, nm in rows:
    Bx = L.body(va, maxspan=0x9000)
    n_atlas = atlas.get(va, ('?', '?', '?', '?'))
    lin_n = len(L.lin(va, n_atlas[0])) if isinstance(n_atlas[0], int) else -1
    p('  %08X  %-26s %8d %8s %8d %6s %6s'
      % (va, nm, len(Bx.insns), n_atlas[1], lin_n, n_atlas[2], n_atlas[3]))

p()
p('=== (c) re-verify the numbers W164 quoted, using the atlas row directly ===')
for va, nm, w164 in ((0x42C900, 'FindPath', '1563 instr / 67 calls'),
                     (0x4B2630, 'Drive big Process', '2600'),
                     (0x4D3920, 'UpdatePathfinding', '669'),
                     (0x4CBBA0, 'CallFindPath', '58')):
    sz, ni, nc, nca = atlas[va]
    p('  %08X %-20s atlas n_instr=%-5d size=%-5d n_callees=%-3d | W164 said %s'
      % (va, nm, ni, sz, nc, w164))

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'EVIDENCE',
                       'S13_globals_dualchannel.txt'), 'w', encoding='utf-8') as fh:
    fh.write('\n'.join(OUT) + '\n')
