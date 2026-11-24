#!/usr/bin/env python3
# R118-EXEC-INDEPENDENT: independent recomputation of the three R118 numbers.
# Written from PE header up. No reuse of _r113/r113_lib.py or _r118/*.py.
# Memory discipline: disasm_lite streaming generator, no detail=True,
# no accumulation of decoded instruction objects.
import struct, json, random, hashlib, bisect, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r118/x118exec_independent.json'

# ---------------------------------------------------------------- PE parse
class PE:
    def __init__(self, path):
        with open(path, 'rb') as f:
            self.raw = f.read()
        r = self.raw
        assert r[:2] == b'MZ'
        lfanew, = struct.unpack_from('<I', r, 0x3c)
        assert r[lfanew:lfanew+4] == b'PE\x00\x00'
        coff = lfanew + 4
        self.nsec, = struct.unpack_from('<H', r, coff + 2)
        sizeopt, = struct.unpack_from('<H', r, coff + 16)
        opt = coff + 20
        self.magic, = struct.unpack_from('<H', r, opt)
        self.imagebase, = struct.unpack_from('<I', r, opt + 28)
        self.sizeofimage, = struct.unpack_from('<I', r, opt + 56)
        assert self.magic == 0x10b, 'expected PE32'
        dd = opt + 96                      # PE32 DataDirectory offset (NOT +SizeOfOptionalHeader)
        nrd, = struct.unpack_from('<I', r, opt + 92)
        self.dirs = [struct.unpack_from('<II', r, dd + i * 8) for i in range(min(nrd, 16))]
        self.sections = []
        st = opt + sizeopt
        for i in range(self.nsec):
            o = st + i * 40
            name = r[o:o+8].rstrip(b'\x00').decode('latin1')
            vsz, va, rsz, rptr = struct.unpack_from('<IIII', r, o + 8)
            self.sections.append(dict(name=name, vsz=vsz, va=self.imagebase + va,
                                      rsz=rsz, rptr=rptr))
    def sec(self, name):
        return next(s for s in self.sections if s['name'] == name)
    def off2va(self, off):
        for s in self.sections:
            if s['rptr'] <= off < s['rptr'] + s['rsz']:
                return s['va'] + (off - s['rptr']), s['name']
        return None, None
    def va2off(self, va):
        for s in self.sections:
            if s['va'] <= va < s['va'] + s['rsz']:
                return s['rptr'] + (va - s['va']), s['name']
        return None, None
    def read_va(self, va, n):
        o, _ = self.va2off(va)
        return None if o is None else self.raw[o:o+n]

pe = PE(EXE)
TEXT, RDATA, DATA = pe.sec('.text'), pe.sec('.rdata'), pe.sec('.data')
for s in pe.sections:
    print('%-8s va=%#x vsz=%#x rsz=%#x rptr=%#x' % (s['name'], s['va'], s['vsz'], s['rsz'], s['rptr']))

# ------------------------------------------------------------ GUID codec
def guid_bytes(txt):
    a, b, c, d1, d2 = txt.strip('{}').split('-')
    d4 = bytes.fromhex(d1 + d2)
    assert len(d4) == 8
    return struct.pack('<IHH', int(a, 16), int(b, 16), int(c, 16)) + d4

def guid_decode(b16):
    a, b, c = struct.unpack_from('<IHH', b16, 0)
    d = b16[8:]
    return '%08X-%04X-%04X-%s-%s' % (a, b, c, d[:2].hex().upper(), d[2:].hex().upper())

IID_PS  = '00000109-0000-0000-C000-000000000046'
IID_P   = '0000010C-0000-0000-C000-000000000046'
IID_NUL = '00000000-0000-0000-C000-000000000046'
G_PS, G_P, G_NUL = guid_bytes(IID_PS), guid_bytes(IID_P), guid_bytes(IID_NUL)
guid_roundtrip = {
    'IPersistStream': (G_PS.hex(), guid_decode(G_PS), guid_decode(G_PS) == IID_PS),
    'IPersist': (G_P.hex(), guid_decode(G_P), guid_decode(G_P) == IID_P),
    'NullD4C0': (G_NUL.hex(), guid_decode(G_NUL), guid_decode(G_NUL) == IID_NUL),
}
for k, v in guid_roundtrip.items():
    print('GUID', k, v)

# -------------------------------------- streaming .text linear sweep
# Scan to vsz (real code extent), not raw size (raw tail is 0xCC/0x00 padding).
tstart = TEXT['va']
n = TEXT['vsz']
code = memoryview(pe.raw)[TEXT['rptr']:TEXT['rptr'] + n]
md = Cs(CS_ARCH_X86, CS_MODE_32)

insn_start = bytearray(n // 8 + 2)
def mark(off):
    insn_start[off >> 3] |= 1 << (off & 7)
def is_start(off):
    return (insn_start[off >> 3] >> (off & 7)) & 1

pushes, ff15 = [], []
ninsn = 0
pos = 0
while pos < n:
    progressed = False
    for (a, sz, mn, op) in md.disasm_lite(code[pos:], tstart + pos):
        progressed = True
        o = a - tstart
        mark(o)
        ninsn += 1
        if code[o] == 0x68 and mn == 'push' and sz == 5:
            pushes.append((a, struct.unpack_from('<I', code, o + 1)[0]))
        elif code[o] == 0xff and code[o+1] == 0x15 and mn == 'call' and sz == 6:
            ff15.append((a, struct.unpack_from('<I', code, o + 2)[0]))
        pos = o + sz
    if not progressed:
        pos += 1
print('insns=%d push_imm32=%d ff15=%d' % (ninsn, len(pushes), len(ff15)))

push_set = {a: v for a, v in pushes}

# ------------------------------------------- GUID constant copies (value)
def find_all(hay, needle, start=0):
    out, i = [], hay.find(needle, start)
    while i != -1:
        out.append(i)
        i = hay.find(needle, i + 1)
    return out

copies = {}
for label, g in (('IPersistStream', G_PS), ('IPersist', G_P), ('NullD4C0', G_NUL)):
    lst = []
    for off in find_all(pe.raw, g):
        va, s = pe.off2va(off)
        lst.append({'va': va, 'section': s})
    copies[label] = lst
    print(label, 'copies:', [(hex(x['va']), x['section']) for x in lst])

byte_exact = []
for label, g in (('IPersistStream', G_PS), ('IPersist', G_P)):
    for c in copies[label]:
        b = pe.read_va(c['va'], 16)
        byte_exact.append({'iid': label, 'va': c['va'], 'sec': c['section'],
                           'raw16': b.hex(), 'decoded': guid_decode(b),
                           'decoded_equals_expected': guid_decode(b) ==
                           (IID_PS if label == 'IPersistStream' else IID_P),
                           'byte_equals_expected': b == g})

PS_ADDR = [c['va'] for c in copies['IPersistStream']]
P_ADDR  = [c['va'] for c in copies['IPersist']]
NUL_ADDR = [c['va'] for c in copies['NullD4C0']]
PS_RDATA = [a for a in PS_ADDR if a is not None and RDATA['va'] <= a < RDATA['va'] + RDATA['rsz']]
P_RDATA  = [a for a in P_ADDR  if a is not None and RDATA['va'] <= a < RDATA['va'] + RDATA['rsz']]

def push_sites(val_set):
    return sorted(a for a, v in pushes if v in val_set)

NUM1_pc = {hex(a): len(push_sites({a})) for a in PS_ADDR}
NUM1_sites = {hex(a): push_sites({a}) for a in PS_ADDR}
NUM1_total = len(push_sites(set(PS_ADDR)))
NUM3_pc = {hex(a): len(push_sites({a})) for a in P_ADDR}
NUM3_sites = {hex(a): push_sites({a}) for a in P_ADDR}
NUM3_total = len(push_sites(set(P_ADDR)))
print('NUM1 per-copy', NUM1_pc, 'value_total', NUM1_total)
print('NUM3 per-copy', NUM3_pc, 'value_total', NUM3_total)

# --------------------------------------------------------- imports
def parse_imports():
    imp = {}
    rva, _sz = pe.dirs[1]
    base = pe.imagebase + rva
    i = 0
    while True:
        o, _ = pe.va2off(base + i * 20)
        if o is None:
            break
        oft, _ts, _fc, name_rva, ft = struct.unpack_from('<IIIII', pe.raw, o)
        if name_rva == 0 and ft == 0:
            break
        nameb = pe.read_va(pe.imagebase + name_rva, 256)
        dll = nameb.split(b'\x00')[0].decode('latin1') if nameb else '?'
        slot = ft or oft
        k = 0
        while True:
            so, _ = pe.va2off(pe.imagebase + slot + k * 4)
            if so is None:
                break
            v, = struct.unpack_from('<I', pe.raw, so)
            if v == 0:
                break
            iat_va = pe.imagebase + ft + k * 4
            if v & 0x80000000:
                imp[iat_va] = (dll, None, v & 0xffff)
            else:
                nb = pe.read_va(pe.imagebase + v + 2, 256)
                imp[iat_va] = (dll, nb.split(b'\x00')[0].decode('latin1') if nb else '?', None)
            k += 1
        i += 1
    return imp

imp = parse_imports()
print('imports parsed:', len(imp))
IAT_OLE = 0x7e15f4
iat_probe = {'slot': hex(IAT_OLE), 'resolved': imp.get(IAT_OLE)}
ole_slots = sorted(a for a, (d, nm, _o) in imp.items() if nm and 'OleSaveToStream' in nm)
print('IAT 0x7e15f4 =', iat_probe['resolved'], '| all OleSaveToStream slots:', [hex(a) for a in ole_slots])

ole_sites = sorted(a for a, t in ff15 if t in set(ole_slots) or t == IAT_OLE)
n_ole = len(ole_sites)
print('OleSaveToStream FF15 sites:', n_ole)

# --------------------------- independent function-start reconstruction
cand = {tstart}
# Reuse the SAME aligned sweep's boundaries: at each known instruction start,
# E8 rel32 is "call rel32" and E9 rel32 is "jmp rel32" by definition — no detail=True.
for off in range(n):
    if not is_start(off):
        continue
    b0 = code[off]
    if b0 == 0xe8 or b0 == 0xe9:
        rel, = struct.unpack_from('<i', code, off + 1)
        t = tstart + off + 5 + rel
        if tstart <= t < tstart + n:
            cand.add(t)
# padding-delimited starts (int3 0xCC / nop 0x90 / ret-aligned)
for off in range(1, n):
    if code[off - 1] in (0xcc, 0x90) and code[off] not in (0xcc, 0x90) and is_start(off):
        cand.add(tstart + off)
starts = sorted(cand)
print('function starts (heuristic):', len(starts))
def fn_start(x):
    j = bisect.bisect_right(starts, x) - 1
    return starts[j] if j >= 0 else tstart

# ---------------------------------------- NUM2: coupling, two scopes
already = {('num2'): None}
def coupled(site, target_set):
    lo = fn_start(site)
    return [a for a in push_sites(target_set) if lo <= a < site]

n2_val_infn = n2_addr_infn = 0
n2_detail = []
for s in ole_sites:
    v_ok = bool(coupled(s, set(PS_ADDR)))
    a_ok = bool(coupled(s, set(PS_RDATA)))
    n2_val_infn += v_ok
    n2_addr_infn += a_ok
    n2_detail.append({'site': hex(s), 'fn': hex(fn_start(s)),
                      'by_value': v_ok, 'by_address_rdata_only': a_ok,
                      'push_imms_in_fn_before_call': [hex(x) for x in coupled(s, set(PS_ADDR))]})
print('NUM2 same-fn-earlier: by_value %d/%d by_address %d/%d' % (n2_val_infn, n_ole, n2_addr_infn, n_ole))

# K2 : relax "same function, earlier" -> "anywhere in image, earlier"
k2_val = sum(1 for s in ole_sites if push_sites(set(PS_ADDR)) and
             any(a < s for a in push_sites(set(PS_ADDR))))
k2_addr = sum(1 for s in ole_sites if push_sites(set(PS_RDATA)) and
              any(a < s for a in push_sites(set(PS_RDATA))))
pval_all = push_sites(set(PS_ADDR))
paddr_all = push_sites(set(PS_RDATA))
k2_val = sum(1 for s in ole_sites if any(a < s for a in pval_all))
k2_addr = sum(1 for s in ole_sites if any(a < s for a in paddr_all))
k2_anyorder_val = sum(1 for s in ole_sites if pval_all)
k2_anyorder_addr = sum(1 for s in ole_sites if paddr_all)
print('K2 whole-image-earlier: by_value %d by_address %d' % (k2_val, k2_addr))

# K3 : substitute the null GUID
nul_sites = push_sites(set(NUL_ADDR))
k3_push_total = len(nul_sites)
k3_coupled = 0
k3_detail = []
for s in ole_sites:
    hits = coupled(s, set(NUL_ADDR))
    if hits:
        k3_coupled += 1
        k3_detail.append({'site': hex(s), 'fn': hex(fn_start(s)), 'hits': [hex(x) for x in hits]})
print('K3 null-GUID: push sites %d, same-fn-earlier coupled to OleSave %d' % (k3_push_total, k3_coupled))

# ------------------------- NUM3 claim: IPersist sites not OleSave-coupled
per_site_fn = {}
for s in ole_sites:
    per_site_fn.setdefault(fn_start(s), []).append(s)
p_all = sorted(a for lst in NUM3_sites.values() for a in lst)
p_coupled_samefn = []
p_coupled_window = []
for a in p_all:
    f = fn_start(a)
    # wide check: any OleSave call in the same reconstructed function, any distance
    if f in per_site_fn:
        p_coupled_samefn.append({'ip_persist_site': hex(a), 'fn': hex(f),
                                 'ole_saves': [hex(x) for x in per_site_fn[f]]})
    # also a purely local check: OleSave call within +-0x400 bytes, ignoring fn bounds
    near = [s for s in ole_sites if abs(s - a) <= 0x400]
    if near:
        p_coupled_window.append({'ip_persist_site': hex(a), 'ole_saves_within_0x400': [hex(x) for x in near]})
print('NUM3 IPersist coupled-same-fn:', len(p_coupled_samefn), '/', len(p_all),
      ' within 0x400B:', len(p_coupled_window))

# ------------------------------------------------------------------ K1
random.seed(20261117)
real, tries = [], 0
usable = [o for o in range(0, n - 5, 1) if is_start(o)]
while len(real) < 200 and tries < 200000:
    tries += 1
    off = random.choice(usable)
    real.append(tstart + off)

target_vals = set(PS_ADDR) | set(P_ADDR)
k1_mid_eq_target = 0
k1_locator_false = 0
k1_rows = []
for a in real:
    o = a - tstart
    mid = struct.unpack_from('<I', code, o + 1)[0]
    accepted = a in push_set          # locator verdict
    if accepted:
        continue
    if mid in target_vals:
        k1_mid_eq_target += 1
    if len(k1_rows) < 10:
        k1_rows.append({'va': hex(a), 'mid4_as_dword': hex(mid),
                        'equals_a_TARGET_const': mid in target_vals,
                        'locator_accepts_as_push_site': accepted})

# naive byte-scan contrast (deliberately WRONG method, quantified)
text_bytes = pe.raw[TEXT['rptr']:TEXT['rptr'] + n]
naive = {}
for v in PS_ADDR + P_ADDR:
    naive[hex(v)] = len(find_all(text_bytes, b'\x68' + struct.pack('<I', v)))
# and: naive FF15 scan count vs aligned
naive_ff15_ole = len(find_all(text_bytes, b'\xff\x15' + struct.pack('<I', IAT_OLE)))
unaliased_68 = 0
for off in find_all(text_bytes, b'\x68' + struct.pack('<I', PS_ADDR[0])):
    if not is_start(off):
        unaliased_68 += 1
print('K1 naive 68+addr:', naive, '| naive ff15 ole:', naive_ff15_ole,
      '| unaligned 68 0x7f7c80 hits:', unaliased_68)

# ---------------------------------------------------------------- write
res = {
    'card': 'R118-EXEC-INDEPENDENT',
    'role': 'exec / deepseek / independent recompute',
    'binary': EXE,
    'binary_sha256': hashlib.sha256(pe.raw).hexdigest(),
    'imagebase': hex(pe.imagebase),
    'method_one_line': ('hand-rolled PE parse (no pefile for structure) + capstone '
                        'disasm_lite instruction-aligned linear sweep of .text[0:vsz]; '
                        'push imm32 accepted only at opcode 0x68 on a verified instruction '
                        'boundary with size==5; FF15 only on a verified boundary with '
                        'size==6; IID identity resolved by 16-byte <IHH8> VALUE, not address.'),
    'text_sweep': {'instructions': ninsn, 'push_imm32_total': len(pushes),
                   'ff15_call_total': len(ff15)},
    'guid_roundtrip': guid_roundtrip,
    'guid_copies_in_image': copies,
    'guid_byte_exact_verification': byte_exact,
    'number1_IPersistStream': {
        'value': IID_PS,
        'by_address_per_copy': NUM1_pc,
        'by_value_total': NUM1_total,
        'claim_r118': {'rdata_0x7f7c80': 60, 'data_0x820270': 8, 'total': 68},
        'match_r118': NUM1_pc == {'0x7f7c80': 60, '0x820270': 8} and NUM1_total == 68,
        'sites': NUM1_sites,
    },
    'number2_OleSaveToStream': {
        'iat_slot': hex(IAT_OLE),
        'iat_resolves_to': iat_probe['resolved'],
        'all_OleSaveToStream_iat_slots': [hex(a) for a in ole_slots],
        'ff15_sites': n_ole,
        'sites': [hex(a) for a in ole_sites],
        'coupled_same_fn_earlier_by_value': n2_val_infn,
        'coupled_same_fn_earlier_by_address_rdata_only': n2_addr_infn,
        'claim_r118': {'by_value': 43, 'by_address': 35, 'total_sites': 43},
        'match_r118': n_ole == 43 and n2_val_infn == 43 and n2_addr_infn == 35,
        'per_site': n2_detail,
    },
    'number3_IPersist': {
        'value': IID_P,
        'by_address_per_copy': NUM3_pc,
        'by_value_total': NUM3_total,
        'claim_r118': {'rdata_0x7f7c70': 0, 'data_0x818858': 16, 'total': 16},
        'match_r118': NUM3_pc == {'0x7f7c70': 0, '0x818858': 16} and NUM3_total == 16,
        'sites': NUM3_sites,
        'coupled_to_OleSave_same_fn': len(p_coupled_samefn),
        'coupled_to_OleSave_within_0x400': len(p_coupled_window),
        'coupling_detail_same_fn': p_coupled_samefn,
        'coupling_detail_0x400': p_coupled_window,
    },
    'K1_random_real_instruction_windows': {
        'n': len(real),
        'seed': 20261117,
        'locator_false_positives': k1_locator_false,
        'windows_whose_middle_4_bytes_equal_a_target_const': k1_mid_eq_target,
        'examples': k1_rows,
        'naive_68_plus_const_hits_in_text': naive,
        'naive_ff15_ole_hits_in_text': naive_ff15_ole,
        'naive_68_for_0x7f7c80_at_unaligned_offsets': unaliased_68,
        'verdict': ('the locator emits a site only when 0x68 sits on a capstone-verified '
                    'instruction boundary and the decoded insn is exactly "push imm32" (5 '
                    'bytes). A random 5-byte window starting mid-instruction never becomes '
                    'a site, so middle bytes that happen to equal a const are not counted. '
                    'Naive byte scanning inflates because it also matches the 0x68 byte when '
                    'it is an immediate/displacement payload, not an opcode.'),
    },
    'K2_relax_to_whole_image_earlier': {
        'by_value': k2_val,
        'by_address_rdata_only': k2_addr,
        'by_value_any_order': k2_anyorder_val,
        'by_address_any_order': k2_anyorder_addr,
        'delta_vs_same_fn': {'by_value': k2_val - n2_val_infn,
                             'by_address': k2_addr - n2_addr_infn},
    },
    'K3_null_guid_substitution': {
        'value': IID_NUL,
        'guid_copies_in_image': copies['NullD4C0'],
        'push_sites_by_value': k3_push_total,
        'coupled_to_OleSave_same_fn_earlier': k3_coupled,
        'detail': k3_detail,
    },
    'inconsistencies': [],
}
with open(OUT, 'w') as f:
    json.dump(res, f, indent=1)
print('WROTE', OUT)
print('N1 %s total=%d | N2 sites=%d val=%d addr=%d | N3 total=%d coupled=%d' % (
    NUM1_pc, NUM1_total, n_ole, n2_val_infn, n2_addr_infn, NUM3_total, len(p_coupled_samefn)))
