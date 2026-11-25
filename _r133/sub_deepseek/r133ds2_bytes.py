#!/usr/bin/env python3
"""R133 deepseek audit: C1 (byte diff), C2 (push imm32 index), C3 (GUID decode), C4 (3 push constants)."""
import json, struct, sys
import pefile

BIN = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
A_VA = 0x6bedb0
B_VA = 0x41c250
LEN = 136

pe = pefile.PE(BIN, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
IMG = pe.get_memory_mapped_image()


def rd(va, n):
    off = va - IB
    return bytes(IMG[off:off + n])


A = rd(A_VA, LEN)
B = rd(B_VA, LEN)
out = {'A_va': hex(A_VA), 'B_va': hex(B_VA), 'len': LEN}

# ---------- C1 ----------
diffs = [i for i in range(LEN) if A[i] != B[i]]
out['C1'] = {
    'identical': A == B[:0] or False,
    'differing_offsets': [hex(i) for i in diffs],
    'differing_offsets_dec': diffs,
    'count': len(diffs),
    'pairs': {hex(i): (hex(A[i]), hex(B[i])) for i in diffs},
}

# ---------- C2 ----------
# For each differing offset, is it byte index 1 of a 0x68 push imm32 starting at off-1?
c2 = []
for i in diffs:
    start = i - 1
    ent = {'diff_off': hex(i), 'cand_push_off': hex(start),
           'opcode_at_start': hex(A[start]), 'opcode_B': hex(B[start]),
           'is_push_imm32': A[start] == 0x68 and B[start] == 0x68}
    if A[start] == 0x68:
        ent['A_imm32'] = hex(struct.unpack_from('<I', A, start + 1)[0])
        ent['B_imm32'] = hex(struct.unpack_from('<I', B, start + 1)[0])
        ent['A_imm_le_bytes'] = [hex(x) for x in A[start + 1:start + 5]]
        ent['B_imm_le_bytes'] = [hex(x) for x in B[start + 1:start + 5]]
        # which byte index within the imm32 (imm starts at start+1)
        ent['byte_index_within_imm32'] = i - (start + 1)
    c2.append(ent)
out['C2'] = c2

# GUID diff between the two pointed-at constants (computed in C4 too, cross-check here)
ptrs_a = [struct.unpack_from('<I', A, o + 1)[0] for o in (0x21, 0x4d, 0x6f) if A[o] == 0x68]
ptrs_b = [struct.unpack_from('<I', B, o + 1)[0] for o in (0x21, 0x4d, 0x6f) if B[o] == 0x68]
out['ptrs_A'] = [hex(p) for p in ptrs_a]
out['ptrs_B'] = [hex(p) for p in ptrs_b]
if 0x817bc0 and 0x817bb0:
    g1 = rd(0x817bc0, 16)
    g2 = rd(0x817bb0, 16)
    out['guid_byte_diff_count_B_vs_A'] = sum(1 for x, y in zip(g1, g2) if x != y)

# ---------- C3 ----------
def guid_le(b):
    d1 = struct.unpack_from('<I', b, 0)[0]
    d2 = struct.unpack_from('<H', b, 4)[0]
    d3 = struct.unpack_from('<H', b, 6)[0]
    rest = b[8:16]
    return '{%08X-%04X-%04X-%s-%s}' % (d1, d2, d3, rest[:2].hex().upper(), rest[2:].hex().upper())


def guid_be(b):
    d1 = struct.unpack_from('>I', b, 0)[0]
    d2 = struct.unpack_from('>H', b, 4)[0]
    d3 = struct.unpack_from('>H', b, 6)[0]
    rest = b[8:16]
    return '{%08X-%04X-%04X-%s-%s}' % (d1, d2, d3, rest[:2].hex().upper(), rest[2:].hex().upper())


b_c0 = rd(0x817bc0, 16)
b_b0 = rd(0x817bb0, 16)
out['C3'] = {
    '0x817bc0_hex': b_c0.hex(),
    '0x817bc0_le': guid_le(b_c0),
    '0x817bc0_be': guid_be(b_c0),
    '0x817bb0_hex': b_b0.hex(),
    '0x817bb0_le': guid_le(b_b0),
    '0x817bb0_be': guid_be(b_b0),
    'guid_diff_bytes_between': sum(1 for x, y in zip(b_c0, b_b0) if x != y),
}

# C11(a) negative control: the next 16 bytes
b_d0 = rd(0x817bd0, 16)
out['C11a'] = {'0x817bd0_hex': b_d0.hex(), '0x817bd0_le': guid_le(b_d0),
               'differs_from_0x817bc0': b_d0 != b_c0}
# C11(b) order sensitivity
out['C11b'] = {'le_eq_be_0x817bc0': guid_le(b_c0) == guid_be(b_c0)}

# ---------- C4 ----------
c4 = {}
for name, buf in (('A', A), ('B', B)):
    rows = []
    # find every 0x68 in the body and decode its imm32 as a VA candidate
    for off in range(LEN - 4):
        if buf[off] == 0x68:
            imm = struct.unpack_from('<I', buf, off + 1)[0]
            rows.append({'off': hex(off), 'imm': hex(imm)})
    c4[name] = rows
out['C4_all_68_in_body'] = c4
out['C4_three'] = {'A': [hex(p) for p in ptrs_a], 'B': [hex(p) for p in ptrs_b]}

print(json.dumps(out, indent=2))
with open('/home/t628/projects/ra2-campaign-forge/_r133/sub_deepseek/r133ds2_bytes.json', 'w') as f:
    json.dump(out, f, indent=2)
