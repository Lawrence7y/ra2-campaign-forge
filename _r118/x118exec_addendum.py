#!/usr/bin/env python3
# Addendum: strengthens K1 (discriminating power) and probes two scope caveats.
import struct, json, random
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from x118exec_independent import (pe, TEXT, RDATA, DATA, tstart, n, code, is_start,
                                  pushes, PS_ADDR, P_ADDR, G_PS, G_P)
OUT = '/home/t628/projects/ra2-campaign-forge/_r118/x118exec_independent.json'
md = Cs(CS_ARCH_X86, CS_MODE_32)

# ---- K1 strengthened: among 200 random real instruction starts, how many
# "5-byte windows" would yield a plausible-looking immediate (an address inside
# .rdata/.data) if they were accepted blindly as push imm32?
random.seed(20261117)
usable = [o for o in range(0, n - 5) if is_start(o)]
real = [random.choice(usable) for _ in range(200)]
target_vals = set(PS_ADDR) | set(P_ADDR)
push_starts = {a - tstart for a, v in pushes}

def in_img(v):
    return any(s['va'] <= v < s['va'] + s['vsz'] for s in pe.sections)

plaus = 0
starts_with_68 = 0
for o in real:
    if o in push_starts:
        starts_with_68 += 1
        continue
    imm = struct.unpack_from('<I', code, o + 1)[0]
    if in_img(imm):
        plaus += 1

# ---- caveat A: mov reg, imm32 (B8..BF) carrying a PS/P const but NOT a push site
mov_ps = []
for o in range(n - 5):
    if not is_start(o):
        continue
    if 0xb8 <= code[o] <= 0xbf:
        imm = struct.unpack_from('<I', code, o + 1)[0]
        if imm in target_vals:
            mov_ps.append({'va': tstart + o, 'reg': 'eax+%d' % (code[o] - 0xb8), 'imm': hex(imm)})

# ---- caveat B: are the 8 .data-copy sites genuinely distinct instructions
data_sites = sorted(a for a, v in pushes if v == 0x820270)
rdata_sites = sorted(a for a, v in pushes if v == 0x7f7c80)
overlap = set(data_sites) & set(rdata_sites)
# verify each site is an aligned instruction start and its bytes are exactly 68+imm
site_bytes_ok = all(pe.read_va(a, 5) == b'\x68' + struct.pack('<I', 0x820270) for a in data_sites)

# ---- caveat C: confirm the 43 OleSave sites are all real boundaries with FF 15 bytes
OLE = 0x7e15f4
ole_sites = [a for a, t in pushes and [(a, t) for a, t in []]] if False else None
ff15 = []
pos = 0
while pos < n:
    prog = False
    for (a, sz, mn, op) in md.disasm_lite(code[pos:], tstart + pos):
        prog = True
        o = a - tstart
        if code[o] == 0xff and code[o+1] == 0x15 and sz == 6:
            ff15.append((a, struct.unpack_from('<I', code, o + 2)[0]))
        pos = o + sz
    if not prog:
        pos += 1
ole_sites = sorted(a for a, t in ff15 if t == OLE)
ole_bytes_ok = all(pe.read_va(a, 6) == b'\xff\x15' + struct.pack('<I', OLE) for a in ole_sites)

d = json.load(open(OUT))
d['K1_random_real_instruction_windows'].update({
    'windows_starting_with_a_real_push_imm32_opcode': starts_with_68,
    'windows_whose_blind_5byte_imm_lands_in_a_section': plaus,
    'discriminating_power': ('of 200 random real instruction starts, %d yield a blind '
                             '"push imm32" immediate that lands inside the image, i.e. would '
                             'look like a plausible request constant to a value-only heuristic. '
                             'The aligned locator emitted 0 of them because the first byte is '
                             'not 0x68 at a boundary. This is why instruction alignment, not '
                             'plausibility of the immediate, is the admission criterion.'
                             % plaus),
})
d['scope_caveats'] = {
    'A_mov_reg_imm32_carrying_a_target_const': {
        'count': len(mov_ps),
        'sites': mov_ps[:40],
        'note': ('the 68/60/8/16 counts cover ONLY the push imm32 request form. mov reg,imm32 '
                 'constructions that load the same GUID address into a register are not push '
                 'sites and are excluded by definition; they are a separate potential request '
                 'population and are NOT included in the R118 numbers.'),
    },
    'B_data_copy_sites_are_distinct_and_byte_verified': {
        'data_0x820270_sites': [hex(a) for a in data_sites],
        'rdata_0x7f7c80_sites_share_any_address': [hex(a) for a in sorted(overlap)],
        'all_data_sites_bytes_are_68_plus_imm': site_bytes_ok,
        'count_data': len(data_sites), 'count_rdata': len(rdata_sites),
        'sum_equals_value_total': len(data_sites) + len(rdata_sites),
    },
    'C_ole_save_sites_byte_verified': {
        'count': len(ole_sites),
        'all_bytes_are_ff15_plus_abs32': ole_bytes_ok,
    },
}
json.dump(d, open(OUT, 'w'), indent=1)
print('K1 plaus=%d starts68=%d mov_ps=%d data_sites=%d rdata=%d overlap=%d sitebytes=%s'
      % (plaus, starts_with_68, len(mov_ps), len(data_sites), len(rdata_sites), len(overlap), site_bytes_ok))
print('ole=%d bytes_ok=%s' % (len(ole_sites), ole_bytes_ok))
print('mov imm32 site list (first 20):', [hex(x['va']) for x in mov_ps[:20]])
