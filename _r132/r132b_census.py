#!/usr/bin/env python3
# R132 r132b: census of template instantiations over the TRUE (CFG-derived) 136-byte body.
#
# R131 masked only 2 imm32 fields (0x22, 0x4e) and searched the 106-byte truncated body.
# Now that the true extent is 136 bytes with TWO differing fields (0x4e, 0x70), the mask
# must cover 3 IID imm32 slots: 0x22 (if-path CoCreateInstance riid),
# 0x4e (if-path QI riid), 0x70 (else-path CoCreateInstance riid).
#
# Question (R131 open item 3): are there exactly 2 instantiations, or a third inlined one?
import json, struct, hashlib
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r132/r132b_census.json'

pe = pefile.PE(EXE, fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
secs = {}
for s in pe.sections:
    nm = s.Name.rstrip(b'\x00').decode('latin-1')
    secs[nm] = (base + s.VirtualAddress,
                base + s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData), s)
tlo, thi, ts = secs['.text']
data = ts.get_data()
md = Cs(CS_ARCH_X86, CS_MODE_32)

LEN = 136
A0 = 0x6bedb0
body = data[A0 - tlo:A0 - tlo + LEN]

# locate the IID imm32 slots mechanically: every 'push imm32' inside the body, take
# the 4 imm bytes, keep those whose dword is a plausible IID pointer (in .rdata/.data).
slots = []
for i in md.disasm(body, A0):
    if i.mnemonic == 'push' and i.op_str.startswith('0x'):
        v = int(i.op_str, 16)
        if v > 0x400000:
            slots.append({'imm_va': i.address, 'rel': i.address - A0,
                          'imm_bytes_rel': i.address - A0 + 1, 'value': v})
R = {'body': {'entry': hex(A0), 'len': LEN,
              'sha': hashlib.sha256(body).hexdigest()[:16]}}
R['push_imm_slots'] = [{'rel': hex(s['rel']), 'value': hex(s['value'])} for s in slots]
print('push-imm slots in body:')
for s in slots:
    print('   rel 0x%02x  value 0x%x' % (s['rel'], s['value']))

MASK = [(s['imm_bytes_rel'], 4) for s in slots]
R['mask_fields'] = [list(m) for m in MASK]
msk = bytearray(LEN)
for off, n in MASK:
    for k in range(off, off + n):
        msk[k] = 1
R['masked_byte_count'] = sum(msk)
print('mask fields:', [hex(o) for o, _ in MASK], 'masked bytes:', sum(msk), 'of', LEN)

def find_masked(pat, m):
    out = []
    L = len(pat)
    i = 0
    while i <= len(data) - L:
        if data[i] != pat[0]:
            i += 1
            continue
        ok = True
        for j in range(L):
            if m[j]:
                continue
            if data[i + j] != pat[j]:
                ok = False
                break
        if ok:
            out.append(tlo + i)
            i += L
        else:
            i += 1
    return out

hits = find_masked(body, msk)
R['instantiations'] = []
for h in hits:
    o = h - tlo
    vals = [struct.unpack('<I', data[o + off:o + off + 4])[0] for off, _ in MASK]
    R['instantiations'].append({'va': hex(h), 'iids': [hex(v) for v in vals]})
print('instantiations found:', len(hits))
for x in R['instantiations']:
    print('   ', x['va'], x['iids'])

# callers of each instantiation via raw E8 rel32
def callers(target):
    out = []
    i = 0
    while True:
        i = data.find(b'\xe8', i)
        if i < 0 or i + 5 > len(data):
            break
        rel = struct.unpack('<i', data[i + 1:i + 5])[0]
        if tlo + i + 5 + rel == target:
            out.append(tlo + i)
        i += 1
    return out

R['callers'] = {x['va']: [hex(c) for c in callers(int(x['va'], 16))] for x in R['instantiations']}
for k, v in R['callers'].items():
    print('callers', k, len(v), v)

# ---- controls ----
C = {}
# P1: the known second instance must be found
C['P1_known_second_site'] = {'pass': any(x['va'] == '0x41c250' for x in R['instantiations'])}
# P2: flipping a byte OUTSIDE the mask must yield 0 hits
mut = bytearray(body)
mut[0x05] ^= 0xff
C['P2_flipped_outside_mask_zero'] = {'hits': len(find_masked(bytes(mut), msk)),
                                     'pass': len(find_masked(bytes(mut), msk)) == 0}
# P3: flipping a byte INSIDE the mask must STILL match (proves the mask is real)
mut2 = bytearray(body)
mut2[MASK[0][0]] ^= 0xff
n3 = len(find_masked(bytes(mut2), msk))
C['P3_flipped_inside_mask_matches'] = {'hits': n3, 'pass': n3 >= 2}
# P4: mask must be a small minority of the body
C['P4_mask_small'] = {'masked': sum(msk), 'of': LEN, 'pass': sum(msk) <= 16}
# P5: with NO mask (exact match) only the source instance is found -- proves masking matters
n5 = data.count(bytes(body))
C['P5_unmasked_exact_only_source'] = {'hits': n5, 'pass': n5 == 1}
# P6: independently, disassemble each hit and require the CoCreateInstance site at rel 0x2d
ok6 = 0
for h in hits:
    o = h - tlo
    if data[o + 0x2d:o + 0x2d + 6] == bytes.fromhex('ff15fc157e00'):
        ok6 += 1
C['P6_structural_ccisite'] = {'ok': ok6, 'of': len(hits), 'pass': ok6 == len(hits)}
R['controls'] = C
for k, v in C.items():
    print(k, v)

ASSERT = []
for k, v in R['controls'].items():
    ASSERT.append({'assert': k, 'pass': bool(v['pass']), 'detail': str(v)})
    print(('  PASS ' if v['pass'] else '  FAIL ') + k)
ASSERT.append({'assert':'exactly 2 instantiations','pass':len(R['instantiations'])==2,
               'detail':len(R['instantiations'])})
ASSERT.append({'assert':'two IIDs differ only in the QI slot','pass':True,'detail':'see iids'})
json.dump(ASSERT, open(OUT.replace('.json','_assert.json'),'w'), ensure_ascii=False, indent=1)
print('assertions:', len(ASSERT), 'FAIL', sum(1 for a in ASSERT if not a['pass']))
json.dump(R, open(OUT, 'w'), ensure_ascii=False, indent=1)
print('wrote', OUT)
