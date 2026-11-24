#!/usr/bin/env python3
# R17-R7-REJECT-LAYER -- bounded, pure-static analysis of ra2youli/gamemd.exe
#
# Boundaries honoured:
#   * read-only open of gamemd.exe; no process, no debugger, no gamemd launch
#   * writes only inside this directory
#   * no whole-image sweep / no function index. The ONLY .text-wide pass is the
#     E8 call-site scan explicitly requested by card Q2.
#   * every disassembly run starts at an ANCHOR = first real instruction byte
#     after a C3 / C2 xx xx / 90|CC fill  (never at an arbitrary address)
import os, sys, struct, hashlib
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_REG_ESP

HERE = os.path.dirname(os.path.abspath(sys.argv[0]))
ROOTS = [os.path.abspath(os.path.join(HERE, *(['..'] * 4))),
         r'D:\Project\ra2-campaign-forge',
         '/mnt/d/Project/ra2-campaign-forge']
ROOT = next((r for r in ROOTS
             if os.path.isfile(os.path.join(r, 'ra2youli', 'gamemd.exe'))), None)
if ROOT is None:
    sys.exit('gamemd.exe not found, tried: %r' % (ROOTS,))
EXE = os.path.join(ROOT, 'ra2youli', 'gamemd.exe')
EXPECT_SHA = '73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476'
IB = 0x400000
TEXT_LO, TEXT_HI = 0x401000, 0x7E038D

d = open(EXE, 'rb').read()
sha = hashlib.sha256(d).hexdigest().upper()
assert sha == EXPECT_SHA, 'hash mismatch: %s' % sha

pe = struct.unpack_from('<I', d, 0x3c)[0]
nsec = struct.unpack_from('<H', d, pe + 6)[0]
opt = pe + 24
so = opt + struct.unpack_from('<H', d, pe + 20)[0]
SECS = []
for i in range(nsec):
    o = so + i * 40
    nm = d[o:o + 8].rstrip(b'\0').decode()
    vs, va, rs, ra = struct.unpack_from('<IIII', d, o + 8)
    SECS.append((nm, IB + va, vs, ra, rs))


def va2off(va):
    for nm, sva, vs, ra, rs in SECS:
        if sva <= va < sva + max(vs, rs):
            return ra + (va - sva)
    raise ValueError('unmapped %#x' % va)


def rb(va, n):
    o = va2off(va)
    return d[o:o + n]


def hx(va, n):
    return rb(va, n).hex(' ').upper()


md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True


def anchor_of(va, back=24):
    """First real instruction byte after C3 / C2 xx xx / 90 / CC fill."""
    for k in range(back):
        c = va - k
        if rb(c - 1, 1)[0] in (0xC3, 0x90, 0xCC):
            return c, 'after %02X at %#x' % (rb(c - 1, 1)[0], c - 1)
        if rb(c - 3, 1)[0] == 0xC2:
            return c, 'after C2 %s at %#x' % (hx(c - 2, 2), c - 3)
    raise RuntimeError('no anchor within %d bytes before %#x' % (back, va))


def walk(va, end, espd0):
    """Linear decode from an anchor; returns [(insn, espd_before, espd_after)].
    espd = esp relative to function entry. Post-call cleanup is modelled as
    'callee removes the args pushed since the previous call' (stdcall/thiscall),
    which is what makes [esp+d] comparable across the whole body."""
    out, espd, pend = [], espd0, 0
    for i in md.disasm(rb(va, end - va), va):
        m, ops, after = i.mnemonic, i.operands, espd
        if espd is None:                      # frame lost (mov/lea esp) -- stay unknown
            out.append((i, None, None))
            continue
        if m == 'call':
            after, pend = espd + pend, 0
        elif m == 'push':
            pend += 4
            after = espd - 4
        elif m in ('pushad', 'pusha'):
            pend += 32
            after = espd - 32
        elif m == 'pop':
            after = espd + 4
        elif m in ('sub', 'add') and len(ops) == 2 and ops[0].type == 1 \
                and ops[0].reg == X86_REG_ESP and ops[1].type == X86_OP_IMM:
            if m == 'sub':
                after = espd - ops[1].imm
                pend += ops[1].imm
            else:
                after = espd + ops[1].imm
                pend = max(0, pend - ops[1].imm)
        elif m in ('mov', 'lea') and len(ops) == 2 and ops[0].type == 1 \
                and ops[0].reg == X86_REG_ESP:
            after = None
        out.append((i, espd, after))
        espd = after
    return out


def call_sites(target):
    """Bounded .text-only scan for E8 rel32 -> target (card Q2)."""
    lo, hi = va2off(TEXT_LO), va2off(TEXT_HI)
    hits, i = [], lo
    while True:
        i = d.find(b'\xE8', i, hi - 4)
        if i < 0:
            break
        if TEXT_LO + (i - lo) + 5 + struct.unpack_from('<i', d, i + 1)[0] == target:
            hits.append(TEXT_LO + (i - lo))
        i += 1
    return hits


# ---------------------------------------------------------------- targets
F_43F180 = (0x43F180, 0x43F660)   # switch function; case body 0x43F1E9 = case 1/3
CASE     = (0x43F1E9, 0x43F5EF)   # case 1/3 body  (ends at shared epilogue/0x43F5EF)
F_47C620 = (0x47C620, 0x47CA70)   # per-cell placement attempt
F_47C3D0 = (0x47C3D0, 0x47C4CA)   # occupancy query at one cell
F_47C4D0 = (0x47C4D0, 0x47C51A)   # 'object of class X at cell' query
REJECT   = 0x43F5D8               # reject exit (returns al=0)

rows = []          # sites.tsv
dump = []          # disasm dump


def note(item, target, addr, nbytes, decoded, nt):
    rows.append((item, target, '%08X' % addr, hx(addr, nbytes), decoded, nt))


# ---------------------------------------------------------------- anchors
lines = ['# anchors (rule: first real instruction after C3 / C2 xx xx / 90|CC fill)']
for name, va in (('0x43F180', 0x43F180), ('0x43F1E9', 0x43F1E9),
                 ('0x43F5D8', 0x43F5D8), ('0x47C620', 0x47C620),
                 ('0x47C3D0', 0x47C3D0), ('0x47C4D0', 0x47C4D0)):
    a, why = anchor_of(va)
    lines.append('%-10s anchor=%#x  (%s)  %s' % (name, a, why, 'OK' if a == va else 'MISALIGNED'))
lines.append('')
print('\n'.join(lines))
open(os.path.join(HERE, 'anchors.txt'), 'w').write('\n'.join(lines) + '\n')

# ---------------------------------------------------------------- Q2: switch table
jt = [struct.unpack_from('<I', rb(0x43FB0C + 4 * i, 4), 0)[0] for i in range(4)]
note('switch_table', 'ebp=0..3', 0x43FB0C, 16,
     'jmp [ebp*4+0x43FB0C] -> ' + ', '.join('%#x' % t for t in jt),
     'F_43F180 is a 4-way switch; 0x43F1E9 is entries 1 and 3 (= this card CASE)')

# ---------------------------------------------------------------- Q1: [esp+0x23] writes
case = walk(*CASE, espd0=-0xC4)
WR, RD = [], []
for i, e0, _ in case:
    for op in i.operands:
        if op.type == X86_OP_MEM and op.mem.base == X86_REG_ESP and op.mem.disp == 0x23 \
                and i.mnemonic.startswith(('mov', 'and', 'or', 'xor', 'inc', 'dec')) \
                and op is i.operands[0]:
            WR.append((i, e0))
        elif op.type == X86_OP_MEM and op.mem.base == X86_REG_ESP and op.mem.disp == 0x23:
            RD.append((i, e0))
for i, e0 in WR:
    note('write_esp23', 'frame slot 0x%X' % (0x23 - e0), i.address, i.size,
         '%s %s' % (i.mnemonic, i.op_str),
         'writes 0 (BL, EBX=0 from 0x43F1EF xor ebx,ebx): init before loops'
         if i.op_str.endswith(', bl') else
         'writes 1: reached only if a cell completed the work path')
for i, e0 in RD:
    note('read_esp23', 'frame slot 0x%X' % (0x23 - e0), i.address, i.size,
         '%s %s' % (i.mnemonic, i.op_str), 'final success/fail gate after loops')

# ---------------------------------------------------------------- Q3: the reject chain
note('gate_reject', 'REJECT 0x43F5D8', 0x43F5B1, 2, 'je 0x43F5D8',
     'flag==0 -> reject; flag never set because no cell passed 0x47C620')
note('reject_exit', 'REJECT 0x43F5D8', 0x43F5E3, 2, 'xor al, al',
     'returns al=0 after call 0x6F4A70 -> this is the produced failure value')
note('decide_occupied', '0x47C853 fail exit', 0x47C73D, 8,
     'cmp eax,ebp / jne 0x47C853', 'eax = 0x47C3D0() = nearest blocking object at cell')
note('fail_exit', '0x47C853', 0x47C856, 2, 'xor al, al', 'per-cell placement fail')
note('percell_call', '0x47C620', 0x43F2AE, 5, 'call 0x47C620', 'called once per grid cell')
note('percell_gate', '0x43F504', 0x43F2B5, 6, 'je 0x43F504',
     'cell failed -> skip cell (loop increment); flag stays 0')
note('occupancy_query', '0x47C3D0', 0x47C738, 5, 'call 0x47C3D0',
     'close query: nearest object at cell, list [this+0xE4], bit0 filter at 0x47C427')
note('occupancy_filter', 'skip non-blocking', 0x47C427, 6,
     'mov al,[esi+0x14] / and al,1', 'objects with bit0==0 are not treated as occupants')
note('terrain_query', '0x47C4D0', 0x47C74A, 5, 'call 0x47C4D0',
     'WhatAmI==0x24 (Terrain) at cell -> also fail at 0x47C757')

# ---------------------------------------------------------------- Q2: call-site lists
cs = {}
for t in (0x43F180, 0x43F1E9, 0x47C620, 0x47C738, 0x47C3D0, 0x47C4D0, 0x449440):
    cs[t] = call_sites(t)
    rows.append(('call_sites', '%#x' % t, '-', '-',
                 '%d direct E8 site(s)' % len(cs[t]),
                 '; '.join('%#x' % x for x in cs[t]) if cs[t]
                 else 'none (vtable / indirect, or jump-table only)'))

# ---------------------------------------------------------------- dumps + tsv
for name, (a, b) in (('43F180', F_43F180), ('47C620', F_47C620),
                     ('47C3D0', F_47C3D0), ('47C4D0', F_47C4D0)):
    dump.append('=== %s  [%#x, %#x)' % (name, a, b))
    d0 = -0xC4 if a == 0x43F180 else 0
    for i, e0, _ in walk(a, b, d0):
        dump.append('%08x  %-24s %-40s espd=%s'
                    % (i.address, i.bytes.hex(' ').upper(), i.mnemonic + ' ' + i.op_str, e0))
    dump.append('')
open(os.path.join(HERE, 'disasm.txt'), 'w').write('\n'.join(dump) + '\n')

with open(os.path.join(HERE, 'sites.tsv'), 'w') as f:
    f.write('item\ttarget\taddress\tbytes\tdecoded\tnote\n')
    for r in rows:
        f.write('\t'.join(r) + '\n')

print('SHA256   :', sha, '(matches card)')
print('writes   :', len(WR), ' [esp+0x23] ->', ['%#x' % i.address for i, _ in WR])
print('reads    :', len(RD), ' [esp+0x23] ->', ['%#x' % i.address for i, _ in RD])
print('switch   :', ['%#x' % t for t in jt])
print('callsites:', {('%#x' % k): len(v) for k, v in cs.items()})
print('wrote sites.tsv (%d rows), disasm.txt, anchors.txt' % len(rows))
