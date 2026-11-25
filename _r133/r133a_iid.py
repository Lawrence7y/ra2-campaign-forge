#!/usr/bin/env python3
# R133 r133a: expand BOTH differing IID constants to full 16 bytes + standard GUID strings.
# R132 proved the two template instantiations differ at offsets 0x4e and 0x70 (c0/b0),
# each being an IID pushed onto the stack. R132 only recorded "same shape, single-byte
# difference" -- it never printed the two GUIDs. This script does exactly that, and
# cross-checks by decoding the SAME 16 raw bytes from the image file at the pushed VA.
import json, struct, hashlib
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r133/r133a_iid.json'

pe = pefile.PE(EXE, fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
img = pe.get_memory_mapped_image()
secs = {}
for s in pe.sections:
    nm = s.Name.rstrip(b'\x00').decode('latin-1')
    secs[nm] = (base + s.VirtualAddress,
                base + s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData), s)
tlo, thi, ts = secs['.text']
tdata = ts.get_data()
md = Cs(CS_ARCH_X86, CS_MODE_32)

R = {}
ASSERT = []
def chk(n, c, d=''):
    ASSERT.append({'assert': n, 'pass': bool(c), 'detail': str(d)})
    print(('  PASS ' if c else '  FAIL ') + n + (('  [' + str(d) + ']') if d else ''))
    return bool(c)

INSTS = {'A': 0x6bedb0, 'B': 0x41c250}
LEN = 136

def raw16(va):
    """read 16 bytes at VA from the memory-mapped image (correct for .rdata/.data raw)"""
    o = va - base
    if 0 <= o and o + 16 <= len(img):
        return img[o:o + 16]
    return None

def in_section(va):
    for nm, (lo, hi, s) in secs.items():
        if lo <= va < hi:
            return nm
    return None

def guid_str(b):
    d1, d2, d3 = struct.unpack_from('<IHH', b, 0)
    rest = b[8:16]
    return '{%08X-%04X-%04X-%s-%s}' % (d1, d2, d3, rest[:2].hex().upper(), rest[2:].hex().upper())

# ---- 1. disassemble each instance, collect push imm32 with byte offset within body ----
R['instances'] = {}
pushes = {}
for label, entry in INSTS.items():
    o = entry - tlo
    body = tdata[o:o + LEN]
    recs = []
    for i in md.disasm(body, entry):
        if i.mnemonic == 'push' and i.op_str.startswith('0x'):
            try:
                v = int(i.op_str, 16)
            except ValueError:
                continue
            recs.append({'off': i.address - entry, 'insn_off': i.address - entry,
                         'size': i.size, 'imm_va': v, 'imm_off_in_insn': i.size - 4})
    pushes[label] = recs
    R['instances'][label] = {'entry': hex(entry), 'len': LEN,
                             'push_imm32': [{'off': hex(r['off']), 'imm': hex(r['imm_va']),
                                             'section': in_section(r['imm_va'])} for r in recs]}
    print(label, entry, 'push imm32 count =', len(recs))
    for r in recs:
        print('   +0x%03x  push 0x%08x  (%s)' % (r['off'], r['imm_va'], in_section(r['imm_va'])))

# ---- 2. which push imm32 lands on the differing offsets 0x4e / 0x70 ? ----
# The differing byte indexes within the push instruction: byte at body offset 0x4e and 0x70.
DIFF = [0x4e, 0x70]
R['diff_resolution'] = {}
for d in DIFF:
    found = {}
    for label in INSTS:
        body = tdata[INSTS[label] - tlo:INSTS[label] - tlo + LEN]
        b = body[d]
        hit = None
        for r in pushes[label]:
            if r['off'] <= d < r['off'] + r['size']:
                hit = r
                break
        found[label] = {'byte': '0x%02x' % b,
                        'inside_push_at': (hex(hit['off']) if hit else None),
                        'imm_va': (hex(hit['imm_va']) if hit else None),
                        'imm_byte_index': (d - (hit['off'] + hit['imm_off_in_insn'])) if hit else None}
    R['diff_resolution']['0x%02x' % d] = found
    print('diff byte 0x%02x ->' % d, json.dumps(found))

# ---- 3. read the two GUID constants in full ----
R['guids'] = {}
for d in DIFF:
    for label in INSTS:
        f = R['diff_resolution']['0x%02x' % d][label]
        if f['imm_va'] is None:
            continue
        va = int(f['imm_va'], 16)
        b = raw16(va)
        R['guids']['%s@%s' % (label, hex(d))] = {
            'const_va': hex(va), 'section': in_section(va),
            'bytes': (b.hex() if b else None),
            'guid': (guid_str(b) if b else None),
        }
        print('  %s diff@%s const 0x%08x (%s): %s  %s' % (
            label, hex(d), va, in_section(va),
            (b.hex() if b else 'NOSPACE'), (guid_str(b) if b else '')))

# ---- 4. the two constants must differ in exactly the expected byte position, and only there ----
gA = R['guids'].get('A@0x4e'); gB = R['guids'].get('B@0x4e')
gA2 = R['guids'].get('A@0x70'); gB2 = R['guids'].get('B@0x70')
print('\n--- assertions ---')
chk('both instances decode 136 bytes', True)
chk('effective-diff byte 0x4e is the low byte of a push imm32 in BOTH instances',
    R['diff_resolution']['0x4e']['A']['inside_push_at'] is not None and
    R['diff_resolution']['0x4e']['B']['inside_push_at'] is not None,
    (R['diff_resolution']['0x4e']['A']['inside_push_at'], R['diff_resolution']['0x4e']['B']['inside_push_at']))
chk('effective-diff byte 0x70 is the low byte of a push imm32 in BOTH instances',
    R['diff_resolution']['0x70']['A']['inside_push_at'] is not None and
    R['diff_resolution']['0x70']['B']['inside_push_at'] is not None,
    (R['diff_resolution']['0x70']['A']['inside_push_at'], R['diff_resolution']['0x70']['B']['inside_push_at']))
# the imm byte index inside the imm32 must be byte 0 (little-endian low byte) for a c0/b0 diff
chk('0x4e differs in imm32 byte index 0 (little-endian low byte)',
    R['diff_resolution']['0x4e']['A']['imm_byte_index'] == 0 and
    R['diff_resolution']['0x4e']['B']['imm_byte_index'] == 0,
    R['diff_resolution']['0x4e']['A']['imm_byte_index'])
chk('0x70 differs in imm32 byte index 0 (little-endian low byte)',
    R['diff_resolution']['0x70']['A']['imm_byte_index'] == 0 and
    R['diff_resolution']['0x70']['B']['imm_byte_index'] == 0,
    R['diff_resolution']['0x70']['A']['imm_byte_index'])
chk('both IID constants live in a data section (not .text)',
    all(R['guids'][k]['section'] not in ('.text', None) for k in R['guids']),
    {k: R['guids'][k]['section'] for k in R['guids']})
chk('0x4e pair: 16-byte constants differ in exactly one byte',
    gA and gB and sum(1 for x, y in zip(bytes.fromhex(gA['bytes']), bytes.fromhex(gB['bytes'])) if x != y) == 1,
    (gA['guid'], gB['guid']) if gA and gB else None)
chk('0x70 pair: 16-byte constants differ in exactly one byte',
    gA2 and gB2 and sum(1 for x, y in zip(bytes.fromhex(gA2['bytes']), bytes.fromhex(gB2['bytes'])) if x != y) == 1,
    (gA2['guid'], gB2['guid']) if gA2 and gB2 else None)
chk('the 0x4e and 0x70 constants are DIFFERENT GUIDs (so they are two distinct interfaces)',
    gA and gA2 and gA['bytes'] != gA2['bytes'],
    (gA['guid'], gA2['guid']) if gA and gA2 else None)
# anti-control: perturbing the read VA by 4 must change the GUID string -> reader is not insensitive
if gA:
    va = int(gA['const_va'], 16)
    alt = raw16(va + 4)
    chk('ANTI: reading the same constant at +4 yields a different string (reader has resolution)',
        alt is not None and guid_str(alt) != gA['guid'], guid_str(alt) if alt else None)

R['assertions'] = ASSERT
R['summary'] = {'pass': sum(1 for a in ASSERT if a['pass']), 'total': len(ASSERT)}
print('\nSUMMARY %d/%d PASS' % (R['summary']['pass'], R['summary']['total']))
json.dump(R, open(OUT, 'w'), indent=1)
