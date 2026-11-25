#!/usr/bin/env python3
# Independent R133 cross-family audit probe (hy4). Streams disasm_lite; detail only on small windows.
from __future__ import annotations
import collections, json, os, re, struct, sys
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_EIP, X86_INS_JMP

ROOT = '/home/t628/projects/ra2-campaign-forge'
BIN = os.path.join(ROOT, 'ra2bench/gamemd.exe')
OUT = os.path.join(ROOT, '_r133/sub_hy4/r133hy_probe.json')
IB = 0x400000
A0, B0 = 0x6BEDB0, 0x41C250
IID0, IID1 = 0x817BC0, 0x817BB0
BODY_LEN = 0x88

blob = open(BIN, 'rb').read()
pe = pefile.PE(BIN)
SECS = []  # (VA, raw, virtual_size)
for s in pe.sections:
    SECS.append((s.VirtualAddress + IB, s.PointerToRawData, s.Misc_VirtualSize))

def rva(va: int) -> int | None:
    for va0, raw, vsize in SECS:
        if va0 <= va < va0 + vsize:
            return raw + va - va0
    return None

def at(va: int, n: int) -> bytes:
    r = rva(va)
    assert r is not None, hex(va)
    return blob[r:r+n]

def guid_le(b: bytes) -> str:
    d1, w2, w3 = struct.unpack_from('<IHH', b, 0)
    return '{%08X-%04X-%04X-%s-%s}' % (d1, w2, w3, b[8:10].hex().upper(), b[10:16].hex().upper())

def guid_be(b: bytes) -> str:
    d1, w2, w3 = struct.unpack_from('>IHH', b, 0)
    return '{%08X-%04X-%04X-%s-%s}' % (d1, w2, w3, b[8:10].hex().upper(), b[10:16].hex().upper())

md_lite = Cs(CS_ARCH_X86, CS_MODE_32)          # disasm_lite only, no detail
md_lite.skipdata = True   # keep a global linear sweep aligned past data blobs
md_det  = Cs(CS_ARCH_X86, CS_MODE_32); md_det.detail = True   # detail only <=0xc0 byte windows

def lite_window(va: int, n: int):
    return list(md_lite.disasm_lite(at(va, n), va))

def det_window(va: int, n: int):
    assert n <= 0xc0
    return list(md_det.disasm(at(va, n), va))

R: dict[str, object] = {}

# ---- C1: body diff ----
ba, bb = at(A0, BODY_LEN), at(B0, BODY_LEN)
doffs = [i for i in range(BODY_LEN) if ba[i] != bb[i]]
R['C1'] = {'diff_offsets': [hex(i) for i in doffs],
           'delta': [{'off': hex(i), 'A': hex(ba[i]), 'B': hex(bb[i])} for i in doffs]}

# ---- C5/C2/C4/C6/C7: detailed instance decode ----
instances = {}
for nm, entry in (('A', A0), ('B', B0)):
    body = at(entry, BODY_LEN)
    ins = det_window(entry, BODY_LEN)
    byoff = {i.address - entry: i for i in ins}
    test = [i for i in ins if i.mnemonic == 'test' and i.op_str == 'al, 0x14']
    assert len(test) == 1
    t = test[0]
    je_i = ins[ins.index(t) + 1]
    assert je_i.mnemonic == 'je' and je_i.operands[0].type == X86_OP_IMM
    else_va = je_i.operands[0].imm
    pushes = [(i.address - entry, i.operands[0].imm) for i in ins
              if i.mnemonic == 'push' and len(i.operands) == 1 and i.operands[0].type == X86_OP_IMM
              and IID0 - 0x100 <= i.operands[0].imm <= IID0 + 0x100]
    branches_to_else = [i for i in ins if len(i.operands) == 1 and i.operands[0].type == X86_OP_IMM
                        and i.operands[0].imm == else_va
                        and (i.mnemonic.startswith('j') or i.mnemonic == 'loop')]
    prev = max((i for i in ins if i.address < else_va), key=lambda x: x.address)
    # arms: if-arm [je.end, else_va), else-arm [else_va, entry+BODY_LEN)
    ifarm = [i for i in ins if je_i.address + je_i.size <= i.address < else_va]
    elsearm = [i for i in ins if i.address >= else_va]
    calls = []
    for arm_name, arm in (('if', ifarm), ('else', elsearm)):
        for i in arm:
            if i.mnemonic == 'call':
                calls.append({'arm': arm_name, 'off': hex(i.address - entry),
                              'va': hex(i.address), 'op': i.op_str,
                              'bytes': i.bytes.hex(),
                              'mem_disp': hex(i.operands[0].mem.disp) if i.operands and i.operands[0].type == X86_OP_MEM else None})
    iatrefs = sorted(set(i.address - entry for i in ifarm + elsearm
                         if any(hex(x) in i.op_str or str(x) in i.op_str
                                for x in (0x7e15fc, 0x7e1600))))
    instances[nm] = {
        'entry': hex(entry),
        'test_off': hex(t.address - entry), 'je_off': hex(je_i.address - entry),
        'je_target': hex(else_va),
        'iid_pushes': [(hex(o), hex(v)) for o, v in pushes],
        'branches_to_else': [(i.mnemonic, hex(i.address - entry)) for i in branches_to_else],
        'prev_before_else': {'mnemonic': prev.mnemonic, 'op': prev.op_str,
                             'off': hex(prev.address - entry), 'end_off': hex(prev.address + prev.size - entry)},
        'calls': calls, 'iat_operand_offsets': [hex(o) for o in iatrefs],
        'ins': [{'off': hex(i.address - entry), 'mn': i.mnemonic, 'op': i.op_str} for i in ins],
    }
R['instances'] = instances

# ---- C3 + C11a/b: GUID decode and controls ----
g0, g1, gx = at(IID0, 16), at(IID1, 16), at(IID0 + 16, 16)
R['C3'] = {'IID0_hex': g0.hex(), 'IID0_le': guid_le(g0),
           'IID1_hex': g1.hex(), 'IID1_le': guid_le(g1),
           'byte_diff_count': sum(x != y for x, y in zip(g0, g1))}
R['C11a'] = {'guid_817bd0': guid_le(gx), 'hex': gx.hex(),
             'differs_from_817bc0': guid_le(gx) != guid_le(g0)}
R['C11b'] = {'big_endian_same_bytes': guid_be(g0), 'little_endian': guid_le(g0),
             'differs': guid_be(g0) != guid_le(g0)}

# ---- C8: rel32 callers in whole binary (streamed) ----
targets = {A0: [], B0: []}
for va0, raw, vsize in SECS:
    if va0 != 0x401000:   # .text is the only executable section
        continue
    data = at(va0, vsize)
    off = 0
    while off < len(data):
      for addr, sz, mn, ops in md_lite.disasm_lite(data[off:off+0x10000], va0+off):
        if mn not in ('call', 'jmp') or sz != 5 or not ops.startswith('0x'):
            continue
        dst = int(ops, 16)
        if dst in targets:
            targets[dst].append({'from': hex(addr), 'mn': mn})
      off += 0x10000
R['C8'] = {hex(k): v for k, v in targets.items()}
for k, v in targets.items():
    for h in v:
        off = rva(int(h['from'], 16))
        h['bytes'] = blob[off:off+5].hex()

# ---- C11c: imm32 scan for A0 ----
imm_hits = []
needle = struct.pack('<I', A0)
pos = 0
while True:
    p = blob.find(needle, pos)
    if p < 0: break
    imm_hits.append(p); pos = p + 1
R['C11c'] = {'raw_imm32_hits': len(imm_hits), 'rel32_callers': len(targets[A0]),
             'raw_hit_offsets': [hex(x) for x in imm_hits[:20]]}

# ---- C9: contiguous-backward arg3, using global linear sweep ----
# Build addr -> (size, mnemonic, op_str) for .text via disasm_lite (one streaming sweep).
info = {}
for va0, raw, vsize in SECS:
    if va0 != 0x401000: continue
    data = at(va0, vsize)
    off = 0
    while off < len(data):
      for addr, sz, mn, ops in md_lite.disasm_lite(data[off:off+0x10000], va0+off):
        info[addr] = (sz, mn, ops)
      off += 0x10000

CTLS = {'call', 'jmp', 'ret', 'retf', 'jecxz', 'loop', 'loope', 'loopne', 'int', 'int3', 'hlt', 'sysenter'}
rev_end = {}
for addr, (sz, mn, ops) in info.items():
    rev_end[addr + sz] = (addr, sz, mn, ops)

def arg3_at(call_va: int):
    cur = call_va
    pushes = []
    control_stop = None
    steps = []
    while cur in rev_end:
        prev_addr, sz, mn, ops = rev_end[cur]
        steps.append((hex(prev_addr), mn, ops))
        if mn == 'push':
            v = ops.strip()
            try: val = int(v,16) if v.startswith('0x') else int(v,10)
            except ValueError: val = None
            pushes.append((prev_addr, val))
        if mn in CTLS or mn.startswith('j') or mn.startswith('loop') or mn.startswith('ret'):
            control_stop = {'addr': hex(prev_addr), 'mn': mn, 'op': ops}
            break
        cur = prev_addr
        if len(steps) > 40: break
    nearest3 = pushes[:3]
    arg3 = nearest3[-1] if len(nearest3) == 3 else None
    return {'arg3': arg3[1] if arg3 else None, 'arg3_addr': hex(arg3[0]) if arg3 else None,
            'nearest3': [(hex(a), o) for a, o in nearest3],
            'walk': steps, 'control_stop': control_stop, 'chain_contiguous': True}

arg3s = []
for dst in (A0, B0):
    for h in targets[dst]:
        r = arg3_at(int(h['from'], 16))
        h['arg3'] = r['arg3']; h['arg3_addr'] = r['arg3_addr']
        h['nearest3'] = r['nearest3']; h['control_stop'] = r['control_stop']
        h['walk'] = r['walk']
        arg3s.append(r['arg3'])
R['C9'] = {'arg3_values': arg3s, 'all_seven': all(x == 7 for x in arg3s),
           'sites': [h for dst in (A0, B0) for h in targets[dst]]}

# ---- C10 arithmetic ----
R['C10'] = {'arg3': 7, 'mask': 0x14, 'and_result': 7 & 0x14,
            'je_taken': (7 & 0x14) == 0,
            'scope': 'this build, observed arg3 only; arbitrary inputs not proven'}

with open(OUT, 'w') as f:
    json.dump(R, f, indent=2)
print('wrote', OUT)
for k in ('C1','C3','C8','C9','C10','C11a','C11b','C11c'):
    v=R[k]
    if k=='C9': print(k, 'all_seven=',v['all_seven'], 'values=',v['arg3_values'])
    elif k=='C8': print(k, {a:len(b) for a,b in v.items()})
    else: print(k, str(v)[:500])
