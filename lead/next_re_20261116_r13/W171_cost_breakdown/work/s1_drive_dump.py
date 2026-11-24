"""S1: verify the Drive Process entry chain, then dump 0x4B0500 fully (CFG channel).

Also verifies: which vtable slot actually holds 0x4B0500, and who calls it.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w171_lib as L

OUT = []


def p(*a):
    s = ' '.join(str(x) for x in a)
    OUT.append(s)
    print(s)


# ---- 1. Drive locomotion off4 subtable: confirm slot 16 (+0x40) = 0x4B0500
p('== Drive off4 vtable 0x7E7EB0 slot check ==')
for k in range(0, 24):
    v = L.u32(0x7E7EB0 + 4 * k)
    p('  slot %2d (+0x%02X) = %08X %s' % (k, 4 * k, v, 'IN_TEXT' if L.in_text(v) else ''))

# ---- 2. who can reach 0x4B0500 (byte channel: sweep .text for call/jmp/call[disp])
p()
p('== byte-channel refs to 0x4B0500 (.text linear sweep) ==')
m = L.md()
data = L.PE.__data__[L.TEXT['raw']:L.TEXT['raw'] + L.TEXT['rawsize']]
n = 0
hits = []
for ins in m.disasm(data, L.TEXT_LO):
    if ins.id == 0:
        continue
    n += 1
    if ins.mnemonic in ('call', 'jmp') and ins.op_str.startswith('0x'):
        if int(ins.op_str, 16) == 0x4B0500:
            hits.append((ins.address, L.fmt(ins)))
    for op in ins.operands:
        if op.type == L.X86_OP_IMM and (op.imm & 0xFFFFFFFF) == 0x4B0500:
            if not (ins.mnemonic in ('call', 'jmp')):
                hits.append((ins.address, L.fmt(ins) + '   <imm operand>'))
p('  linear .text insns = %d' % n)
for a, t in hits:
    p('  %s' % t)

# ---- 3. dword occurrences of 0x004B0500 anywhere (vtable channel)
p()
p('== dword 0x004B0500 occurrences in .rdata / .data (vtable entries) ==')
for sec in L.SECS:
    if sec['name'] not in ('.rdata', '.data'):
        continue
    buf = L.PE.__data__[sec['raw']:sec['raw'] + sec['rawsize']]
    start = 0
    while True:
        i = buf.find(b'\x00\x05\x4b\x00', start)
        if i < 0:
            break
        p('  %s VA %08X' % (sec['name'], sec['va'] + i))
        start = i + 1

# ---- 4. full dump of the CFG body
p()
p('== 0x4B0500 CFG body: reachable instruction set, address order ==')
B = L.body(0x4B0500)
p('  reachable insns = %d   calls = %d   indirect calls = %d   unresolved indirect jmps = %d'
  % (len(B.insns), len(B.calls), len(B.vcalls), len(B.unres)))
p('  jump tables resolved: %s' % [(hex(s), [hex(t) for t in t]) for s, t in B.table_jmps])
lo = min(B.insns)
hi = max(B.insns) + B.insns[max(B.insns)].size
p('  addr range %08X..%08X  (%d bytes span)' % (lo, hi, hi - lo))
p()
for a in B.addrs():
    ins = B.insns[a]
    tag = ''
    if a in B.calls:
        t = B.calls[a]
        tag = '   ; -> %08X' % t if t else '   ; VIRTUAL'
    elif a in B.jmps:
        tag = '   ; -> %08X' % B.jmps[a]
    p('  ' + L.fmt(ins) + tag)

p()
p('== call targets, first appearance order ==')
order = []
for a in B.addrs():
    if a in B.calls and B.calls[a] is not None:
        t = B.calls[a]
        if t not in [x[0] for x in order]:
            order.append((t, a))
for t, a in order:
    p('  %08X  first site %08X' % (t, a))

p()
p('== indirect (virtual) call sites ==')
for a in B.vcalls:
    p('  ' + L.fmt(B.insns[a]))

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'EVIDENCE',
                       'S1_drive_4B0500_full.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(OUT) + '\n')
