#!/usr/bin/env python3
# R133 r133a2: CORRECTED IID conclusion.
#
# r133a shipped three FAILs whose PREMISES were wrong (self-error S-219), not whose readings
# were wrong. The premise I inherited from R131/R132 was "the two constants are the same
# shape, differing in one byte (c0 vs b0)". Measurement says otherwise:
#
#   0x817bc0 = 00 00 00 00 00 00 00 00 c0 00 00 00 00 00 00 46
#              {00000000-0000-0000-C000-000000000046}  = IID_IUnknown
#   0x817bb0 = 90 32 0f 07 41 98 d1 11 b7 09 00 a0 24 dd af d1
#              {070F3290-9841-11D1-B709-00A024DDAFD1}
#
# They are 16 bytes apart in .data (0x817bb0 + 0x10 = 0x817bc0) and differ in 15 of 16 bytes.
# The "single byte c0/b0" R131/R132 recorded is the LOW BYTE OF THE PUSHED IMM32 -- i.e. the
# address of the constant, not the constant. Both statements are arithmetically compatible,
# but "only one byte differs" is true of the PUSH ENCODING and false of the GUID VALUE.
# This script encodes that distinction as assertions so the two can never be conflated again.
import json, struct
import pefile

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r133/r133a2_iid_fix.json'

pe = pefile.PE(EXE, fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
img = pe.get_memory_mapped_image()

R = {}; ASSERT = []
def chk(n, c, d=''):
    ASSERT.append({'assert': n, 'pass': bool(c), 'detail': str(d)})
    print(('  PASS ' if c else '  FAIL ') + n + (('  [' + str(d) + ']') if d else ''))
    return bool(c)

def raw16(va):
    o = va - base
    return img[o:o + 16] if 0 <= o and o + 16 <= len(img) else None

def gs(b):
    d1, d2, d3 = struct.unpack_from('<IHH', b, 0)
    return '{%08X-%04X-%04X-%s-%s}' % (d1, d2, d3, b[8:10].hex().upper(), b[10:16].hex().upper())

C = {0x817bc0: raw16(0x817bc0), 0x817bb0: raw16(0x817bb0)}
R['constants'] = {hex(k): {'bytes': v.hex(), 'guid': gs(v)} for k, v in C.items()}
for k in sorted(C):
    print('%#x  %s  %s' % (k, C[k].hex(), gs(C[k])))

chk('0x817bc0 is IID_IUnknown',
    C[0x817bc0].hex() == '0000000000000000c000000000000046' and
    gs(C[0x817bc0]) == '{00000000-0000-0000-C000-000000000046}', gs(C[0x817bc0]))
chk('0x817bb0 is {070F3290-9841-11D1-B709-00A024DDAFD1}',
    gs(C[0x817bb0]) == '{070F3290-9841-11D1-B709-00A024DDAFD1}', gs(C[0x817bb0]))
diffs = [i for i in range(16) if C[0x817bb0][i] != C[0x817bc0][i]]
chk('the two GUID VALUES differ in 15 of 16 bytes (they are DIFFERENT interfaces)',
    len(diffs) == 15, {'n_diff': len(diffs), 'positions': [hex(i) for i in diffs]})
chk('the two constants are exactly 0x10 apart in .data',
    0x817bc0 - 0x817bb0 == 0x10, hex(0x817bc0 - 0x817bb0))
# The R131/R132 sentence, restated in its own domain: the pushed IMM32 differs in one byte.
imm_a, imm_b = 0x817bc0, 0x817bb0
ba, bb = struct.pack('<I', imm_a), struct.pack('<I', imm_b)
chk('the PUSHED IMM32 differs in exactly 1 byte (low byte c0 vs b0) -- this is what R131/R132 measured',
    sum(1 for x, y in zip(ba, bb) if x != y) == 1 and ba[0] == 0xc0 and bb[0] == 0xb0,
    (ba.hex(), bb.hex()))
chk('CONTRADICTION RESOLVED: 1-byte-different push encoding and 15-byte-different GUID value are both true',
    sum(1 for x, y in zip(ba, bb) if x != y) == 1 and len(diffs) == 15,
    {'imm32_byte_diffs': 1, 'guid_byte_diffs': len(diffs)})
# ANTI: an unrelated GUID elsewhere must not print as either of these
alt = raw16(0x817bd0)
R['anti_alt'] = {'va': '0x817bd0', 'bytes': alt.hex(), 'guid': gs(alt)}
chk('ANTI: the 16 bytes right after 0x817bc0 decode to a DIFFERENT string (reader has resolution)',
    gs(alt) != gs(C[0x817bc0]) and gs(alt) != gs(C[0x817bb0]), gs(alt))
# ANTI: the little-endian discipline actually matters. Print the same 16 bytes in big-endian
# field order and confirm the string changes -- proving the formatter is not byte-order blind.
def gs_be(b):
    d1 = struct.unpack_from('>I', b, 0)[0]; d2 = struct.unpack_from('>H', b, 4)[0]
    d3 = struct.unpack_from('>H', b, 6)[0]
    return '{%08X-%04X-%04X-%s-%s}' % (d1, d2, d3, b[8:10].hex().upper(), b[10:16].hex().upper())
chk('ANTI: big-endian field order yields a DIFFERENT string (formatter is order-sensitive)',
    gs_be(C[0x817bb0]) != gs(C[0x817bb0]),
    {'le': gs(C[0x817bb0]), 'be': gs_be(C[0x817bb0])})

R['assertions'] = ASSERT
R['summary'] = {'pass': sum(1 for x in ASSERT if x['pass']), 'total': len(ASSERT)}
print('\nSUMMARY %d/%d PASS' % (R['summary']['pass'], R['summary']['total']))
json.dump(R, open(OUT, 'w'), indent=1)
