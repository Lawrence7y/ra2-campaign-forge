"""S5: locate the caller(s) of the A* container 0x429A90, dump FindPath 0x42C900's
structure, and measure the A* loop body / rounds cap from bytes.
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


p('=== 1. byte-channel: every `call rel32` to 0x429A90 in .text (linear sweep, skipdata) ===')
m = L.md()
data = L.PE.__data__[L.TEXT['raw']:L.TEXT['raw'] + L.TEXT['rawsize']]
tot = 0
hits = []
for ins in m.disasm(data, L.TEXT_LO):
    if ins.id == 0:
        continue
    tot += 1
    if ins.mnemonic == 'call' and ins.op_str.startswith('0x') and int(ins.op_str, 16) == 0x429A90:
        hits.append(ins)
p('  .text instructions decoded = %d' % tot)
p('  call sites to 0x429A90 = %d' % len(hits))
for h in hits:
    p('    ' + L.fmt(h))

p()
p('=== 2. dword 0x00429A90 occurrences (vtable / pointer table channel) ===')
for sec in L.SECS:
    buf = L.PE.__data__[sec['raw']:sec['raw'] + sec['rawsize']]
    start = 0
    while True:
        i = buf.find(b'\x90\x9a\x42\x00', start)
        if i < 0:
            break
        p('  %s VA %08X' % (sec['name'], sec['va'] + i))
        start = i + 1

p()
p('=== 3. neighbours 0x429780 / 0x42A5B0: are they part of the same A* family? ===')
for fn in (0x429780, 0x42A5B0, 0x42A460):
    B = L.body(fn, maxspan=0x800)
    p('  %08X cfg_insns=%d calls=%s' % (fn, len(B.insns),
      [hex(v) for v in B.calls.values() if v]))

p()
p('=== 4. FindPath 0x42C900: full call table + callers of 0x42C900 ===')
Bf = L.body(0x42C900)
for a in sorted(Bf.calls):
    if Bf.calls[a] is not None:
        p('  site %08X -> %08X' % (a, Bf.calls[a]))
p('  virtual sites: %s' % [hex(a) for a in Bf.vcalls])

p()
p('=== 5. A* container 0x429A90: loop skeleton ===')
B = L.body(0x429A90)
addrs = B.addrs()
backs = []
for a in addrs:
    ins = B.insns[a]
    if ins.mnemonic.startswith('j') and ins.operands and ins.operands[0].type == X86_OP_IMM:
        t = ins.operands[0].imm & 0xFFFFFFFF
        if t <= a:
            backs.append((a, t, ins.mnemonic))
p('  back edges (target <= site):')
for a, t, mn in backs:
    lo = len([x for x in addrs if t <= x <= a])
    p('    latch %08X -> header %08X  (%s)  region_insns=%d' % (a, t, mn, lo))

p()
p('=== 6. rounds cap: search the body for 0xFFF7 / 65527 immediates ===')
for a in addrs:
    ins = B.insns[a]
    for op in ins.operands:
        if op.type == X86_OP_IMM and (op.imm & 0xFFFFFFFF) == 0xFFF7:
            p('  ' + L.fmt(ins))
            p('     raw bytes: %s' % ins.bytes.hex())
        if op.type == X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0 and \
                (op.mem.disp & 0xFFFFFFFF) == 0xFFF7:
            p('  ' + L.fmt(ins))

p()
p('=== 7. the 0xFFF7 store site context (0x429D40..0x429DA0) ===')
for a in addrs:
    if 0x429D40 <= a < 0x429DA0:
        p('  ' + L.fmt(B.insns[a]))

p()
p('=== 8. full body of the A*-core region 0x429D6D..0x42A3D8 (instruction list to EVIDENCE) ===')
core = [a for a in addrs if 0x429D6D <= a < 0x42A3D8]
p('  count = %d' % len(core))
p('  first 40:')
for a in core[:40]:
    p('    ' + L.fmt(B.insns[a]))

p()
p('=== 9. how many instructions are in the loop whose header is 0x429D6D (if any) ===')
hdrs = set(t for a, t, mn in backs)
p('  loop headers discovered: %s' % [hex(x) for x in sorted(hdrs)])

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'EVIDENCE',
                       'S5_searchcore.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(OUT) + '\n')

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'EVIDENCE',
                       'S5_core_body.txt'), 'w', encoding='utf-8') as f:
    for a in core:
        f.write(L.fmt(B.insns[a]) + '\n')
