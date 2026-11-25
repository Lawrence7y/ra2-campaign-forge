#!/usr/bin/env python3
# R133 r133b: map each of the 3 IID push sites in both instantiations to its consumer call,
# and correct the R132/self-error about "the two constants differ by one byte".
#
# MEASURED (r133a): instance A pushes 0x817bc0 three times; instance B pushes 0x817bc0 once
# (+0x21) and 0x817bb0 twice (+0x4d, +0x6f). 0x817bc0 = IID_IUnknown
# {00000000-0000-0000-C000-000000000046}; 0x817bb0 = {070F3290-9841-11D1-B709-00A024DDAFD1}.
# so the "c0/b0 single byte" R132 saw is the LOW BYTE OF THE CONSTANT ADDRESS, and the two
# GUIDs are entirely different constants 16 bytes apart in .data.
#
# This script answers: at each push, WHICH call consumes it -- CoCreateInstance(riid) or
# IUnknown::QueryInterface(riid) or something else? Determined by the argument order the
# body uses and by which IAT slot / vtable slot the following call hits.
import json, struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r133/r133b_arms.json'

pe = pefile.PE(EXE, fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
img = pe.get_memory_mapped_image()
secs = {}
for s in pe.sections:
    nm = s.Name.rstrip(b'\x00').decode('latin-1')
    secs[nm] = (base + s.VirtualAddress,
                base + s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData), s)
tlo, thi, ts = secs['.text']
data = ts.get_data()
md = Cs(CS_ARCH_X86, CS_MODE_32)

# import slot resolution
IAT = {}
for entry in getattr(pe, 'DIRECTORY_ENTRY_IMPORT', []):
    dll = entry.dll.decode('latin-1', 'replace')
    for imp in entry.imports:
        if imp.name:
            IAT[base + imp.address] = dll + '!' + imp.name.decode('latin-1', 'replace')

R = {}; ASSERT = []
def chk(n, c, d=''):
    ASSERT.append({'assert': n, 'pass': bool(c), 'detail': str(d)})
    print(('  PASS ' if c else '  FAIL ') + n + (('  [' + str(d) + ']') if d else ''))
    return bool(c)

INSTS = {'A': 0x6bedb0, 'B': 0x41c250}
LEN = 136
NAMES = {0x817bc0: 'IID_IUnknown{00000000-0000-0000-C000-000000000046}',
         0x817bb0: 'IID_{070F3290-9841-11D1-B709-00A024DDAFD1}'}

R['bodies'] = {}
for label, entry in INSTS.items():
    body = data[entry - tlo: entry - tlo + LEN]
    rows = []
    for i in md.disasm(body, entry):
        rows.append({'va': hex(i.address), 'off': hex(i.address - entry), 'mn': i.mnemonic,
                     'ops': i.op_str, 'bytes': i.bytes.hex()})
    R['bodies'][label] = rows
    print('=== instance %s @ %#x ===' % (label, entry))
    for r in rows:
        print('  +%s  %-8s %s' % (r['off'], r['mn'], r['ops']))

# ---- for each IID push: the next call that consumes it ----
R['push_to_consumer'] = {}
for label, entry in INSTS.items():
    body = data[entry - tlo: entry - tlo + LEN]
    ins = list(md.disasm(body, entry))
    for idx, i in enumerate(ins):
        if i.mnemonic != 'push' or not i.op_str.startswith('0x'):
            continue
        v = int(i.op_str, 16)
        if v not in NAMES:
            continue
        # walk forward to the first call/branch; record how many pushes since, and target
        nxt = None
        npush = 0
        for j in range(idx + 1, min(idx + 20, len(ins))):
            m = ins[j].mnemonic
            if m == 'push':
                npush += 1
            if m.startswith('call'):
                nxt = ins[j]; break
            if m in ('ret',) or m.startswith('j'):
                nxt = ins[j]; break
        tgt = None; kind = None
        if nxt is not None:
            op = nxt.op_str
            if op.startswith('dword ptr [0x'):
                va = int(op[len('dword ptr [0x'):-1], 16)
                tgt = ('IAT', hex(va), IAT.get(va))
                kind = 'call_iat'
            elif op.startswith('0x'):
                tgt = ('direct', op, None); kind = 'call_direct'
            else:
                tgt = ('reg_or_mem', op, None); kind = nxt.mnemonic
            key = '%s+%#x' % (label, i.address - entry)
            before = [x.mnemonic + ' ' + x.op_str for x in ins[max(0, idx - 6):idx + 1]]
            R['push_to_consumer'][key] = {'iid': NAMES[v], 'const_va': hex(v),
                                          'consumer': kind, 'target': tgt,
                                          'pushes_between': npush,
                                          'tail_instrs': [x.mnemonic + ' ' + x.op_str for x in ins[idx + 1:ins.index(nxt) + 1]] if nxt is not None else [],
                                          'before': before}
            print('  %s push %s -> %s %s (intervening pushes %d)' % (key, NAMES[v], kind, tgt, npush))

# ---- assertions ----
print('\n--- assertions ---')
A = R['push_to_consumer']
chk('exactly 3 IID pushes recognised per instance (6 total)',
    len(A) == 6, len(A))
# The +0x21 push is identical in both instances (same IID) -> not part of the difference
chk('push at +0x21 is IID_IUnknown in BOTH instances',
    A['A+0x21']['const_va'] == A['B+0x21']['const_va'] == hex(0x817bc0),
    (A['A+0x21']['const_va'], A['B+0x21']['const_va']))
chk('pushes at +0x4d and +0x6f use different constants between A and B (A=IUnknown, B=other)',
    (A['A+0x4d']['const_va'], A['A+0x6f']['const_va']) == (hex(0x817bc0), hex(0x817bc0)) and
    (A['B+0x4d']['const_va'], A['B+0x6f']['const_va']) == (hex(0x817bb0), hex(0x817bb0)),
    (A['A+0x4d']['const_va'], A['B+0x4d']['const_va']))
# each IID push must be followed (within the same basic block) by a call on a fixed target
chk('every IID push has a resolved consumer call',
    all(v['target'][0] in ('IAT', 'direct') for v in A.values()),
    {k: v['target'][0] for k, v in A.items()})
# the two +0x4d/+0x6f consumers must be the SAME kind of call in A and B (structure identical)
for off in ('+0x4d', '+0x6f'):
    ka = A['A%s' % off]['target']
    kb = A['B%s' % off]['target']
    chk('consumer at %s is the same call target in A and B' % off, ka == kb, (ka, kb))
chk('consumer at +0x21 is the same call target in A and B',
    A['A+0x21']['target'] == A['B+0x21']['target'], (A['A+0x21']['target'], A['B+0x21']['target']))
# anti-control: the 16-byte block at 0x817bb0 and 0x817bc0 must be adjacent (0x10 apart)
o = 0x817bb0 - base
blk = img[o:o + 0x20]
chk('ANTI: 0x817bb0 and 0x817bc0 are adjacent 16-byte constants in one block',
    len(blk) == 0x20 and blk[0x10:0x20].hex() == '0000000000000000c000000000000046',
    blk.hex())
chk('ANTI: the block is not all zero (reader is not returning a fixed value)',
    blk[:0x10].hex() != '00' * 16, blk[:0x10].hex())

R['assertions'] = ASSERT
R['summary'] = {'pass': sum(1 for a in ASSERT if a['pass']), 'total': len(ASSERT)}
print('\nSUMMARY %d/%d PASS' % (R['summary']['pass'], R['summary']['total']))
json.dump(R, open(OUT, 'w'), indent=1)
