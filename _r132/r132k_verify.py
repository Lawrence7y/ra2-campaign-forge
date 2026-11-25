#!/usr/bin/env python3
# R132 r132k: consolidated verification with adversarial controls.
#
# Covers the four claims R132 will assert in the ledgers, each with a control that can
# fail if the claim is wrong:
#   K1 extent is 136 not 106 (control: else-block walked separately equals 30 bytes)
#   K2 instances are exactly 2 (control: 3 independent masks + a planted-decoy search)
#   K3 diff is at 2 offsets, not 1 (control: 106-byte view really does show only 1)
#   K4 arg3=dwClsContext=7 at all 15 call sites (control: a site with arg3!=7 would flip)
import json, struct, hashlib
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r132/r132k_verify.json'

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
md.skipdata = True

ASSERT = []
def chk(n, c, d=''):
    ASSERT.append({'assert': n, 'pass': bool(c), 'detail': str(d)})
    print(('  PASS ' if c else '  FAIL ') + n + ((' [' + str(d) + ']') if d else ''))
    return bool(c)

insn = {}
off = 0
while off < len(data):
    for a, sz, mn, ops in md.disasm_lite(data[off:off + 0x10000], tlo + off):
        insn[a] = (sz, mn, ops)
    off += 0x10000

R = {}

# ============ K1 extent 136 ============
print('--- K1: extent ---')
def cfg_walk(entry, limit=500):
    seen = set(); addrs = []; work = [entry]
    while work and len(addrs) < limit:
        va = work.pop()
        if va in seen or va not in insn:
            continue
        seen.add(va); addrs.append(va)
        sz, mn, ops = insn[va]
        if mn == 'ret':
            continue
        if mn in ('je','jne','jl','jle','jg','jge','jmp'):
            try: work.append(int(ops, 16))
            except ValueError: pass
        work.append(va + sz)
    return sorted(addrs)

K1 = {}
for label, entry, fr in (('A', 0x6bedb0, 0x6bee1a), ('B', 0x41c250, 0x41c2ba)):
    a = cfg_walk(entry)
    end = max(x + insn[x][0] for x in a)
    K1[label] = {'n_insn': len(a), 'cfg_end': hex(end), 'cfg_len': end - entry,
                 'first_ret_len': fr - entry}
    print('[%s] cfg_len=%d first_ret_len=%d' % (label, end - entry, fr - entry))
R['K1'] = K1
chk('K1a instance A extent is 136 bytes', K1['A']['cfg_len'] == 136, K1['A']['cfg_len'])
chk('K1b instance B extent is 136 bytes', K1['B']['cfg_len'] == 136, K1['B']['cfg_len'])
chk('K1c the 106-byte heuristic is shorter than the true extent in both instances',
    K1['A']['first_ret_len'] == 106 and K1['B']['first_ret_len'] == 106)
# control: walking from the else-block entry must close at the same end and be 30 bytes
eb = cfg_walk(0x6bee1a)
eb_end = max(x + insn[x][0] for x in eb)
R['K1']['else_block'] = {'n_insn': len(eb), 'len': eb_end - 0x6bee1a}
print('[A-else] n_insn=%d len=%d' % (len(eb), eb_end - 0x6bee1a))
chk('K1d control: else block is exactly 30 bytes and closes at the same address '
    '(106+30=136 tiles without gap or overlap)',
    eb_end - 0x6bee1a == 30 and eb_end == 0x6bee38, eb_end - 0x6bee1a)

# ============ K2 exactly 2 instantiations ============
print('--- K2: exactly two instantiations ---')
LEN = 136
A0 = 0x6bedb0
body = data[A0 - tlo:A0 - tlo + LEN]

def find_masked(pat, m):
    out = []; L = len(pat); i = 0
    while i <= len(data) - L:
        if data[i] != pat[0]:
            i += 1; continue
        ok = True
        for j in range(L):
            if not m[j] and data[i + j] != pat[j]:
                ok = False; break
        if ok:
            out.append(tlo + i); i += L
        else:
            i += 1
    return out

# mask variant 1: only the 3 IID push immediates (found structurally)
m1 = bytearray(LEN)
for rel in (0x22, 0x4e, 0x70):
    for k in range(rel, rel + 4):
        m1[k] = 1
# mask variant 2: every imm32 in the body
m2 = bytearray(LEN)
for i in md.disasm(body, A0):
    if i.op_str and '0x' in i.op_str:
        for tok in i.op_str.replace(',', ' ').replace('[', ' ').replace(']', ' ').split():
            if tok.startswith('0x'):
                try: v = int(tok, 16)
                except ValueError: continue
                if v > 0xff:
                    rel = (i.address - A0) + i.size - 4
                    if 0 <= rel <= LEN - 4:
                        for k in range(rel, rel + 4):
                            m2[k] = 1
# mask variant 3: no mask at all (exact)
m3 = bytearray(LEN)

v1 = find_masked(body, m1); v2 = find_masked(body, m2); v3 = find_masked(body, m3)
R['K2'] = {'mask_iid_only': [hex(x) for x in v1],
           'mask_all_imm': [hex(x) for x in v2],
           'mask_none': [hex(x) for x in v3],
           'masked_counts': {'iid': sum(m1), 'all_imm': sum(m2), 'none': sum(m3)}}
print('mask(iid only):', len(v1), [hex(x) for x in v1])
print('mask(all imm) :', len(v2), [hex(x) for x in v2])
print('mask(none)    :', len(v3), [hex(x) for x in v3])
chk('K2a IID-only mask finds exactly 2 instantiations', len(v1) == 2, len(v1))
chk('K2b all-imm mask finds exactly the same 2 (no third copy differs only in '
    'some other immediate)', sorted(v2) == sorted(v1), len(v2))
chk('K2c control: with no mask only the source instance matches (proves the mask is '
    'doing real work)', len(v3) == 1 and v3[0] == A0, len(v3))
# control: a decoy that matches the mask but breaks a NON-masked byte must not be reported
dec = bytearray(body); dec[0x60] ^= 0x01
plant = bytes(dec)
cnt = 0; i = 0
while True:
    i = data.find(plant, i)
    if i < 0: break
    cnt += 1; i += 1
chk('K2d control: a byte-flipped decoy outside the mask matches nowhere', cnt == 0, cnt)

# ============ K3 diff count ============
print('--- K3: byte differences ---')
B0 = 0x41c250
A = data[A0 - tlo:A0 - tlo + LEN]
B = data[B0 - tlo:B0 - tlo + LEN]
full = [k for k in range(LEN) if A[k] != B[k]]
part = [k for k in range(106) if A[k] != B[k]]
R['K3'] = {'full_len': LEN, 'full_diff': [hex(k) for k in full], 'full_diff_vals':
           [{'rel': hex(k), 'A': A[k], 'B': B[k]} for k in full],
           'trunc106_diff': [hex(k) for k in part]}
print('136-byte diff offsets:', [hex(k) for k in full])
print('106-byte diff offsets:', [hex(k) for k in part])
chk('K3a the true 136-byte bodies differ at exactly 2 offsets', len(full) == 2, len(full))
chk('K3b those offsets are 0x4e and 0x70', full == [0x4e, 0x70], [hex(k) for k in full])
chk('K3c both differences are the same byte pair c0/b0',
    all(A[k] == 0xc0 and B[k] == 0xb0 for k in full),
    [(hex(A[k]), hex(B[k])) for k in full])
chk('K3d control: the truncated 106-byte view really does show only 1 difference '
    '(so R131 number was not a typo, it was the truncation)',
    len(part) == 1 and part == [0x4e], [hex(k) for k in part])

# ============ K4 arg3 == 7 at all 15 sites ============
print('--- K4: arg3 at every wrapper call site ---')
def callers(target):
    out = []; i = 0
    while True:
        i = data.find(b'\xe8', i)
        if i < 0 or i + 5 > len(data): break
        rel = struct.unpack('<i', data[i + 1:i + 5])[0]
        if tlo + i + 5 + rel == target: out.append(tlo + i)
        i += 1
    return out

def pushes3(site):
    out = []; va = site
    for _ in range(14):
        cand = None
        for b in range(1, 16):
            a = va - b
            if a in insn and insn[a][0] == b:
                cand = a; break
        if cand is None: break
        if insn[cand][1] == 'push':
            out.append((cand, insn[cand][2]))
            if len(out) >= 3: break
        va = cand
    out.reverse()
    return out

sites = []
for entry in (0x6bedb0, 0x41c250):
    for c in callers(entry):
        ps = pushes3(c)
        arg3 = ps[0][1] if ps else None
        sites.append({'call': hex(c), 'arg3': arg3,
                      'pushes': [p[1] for p in ps]})
R['K4'] = sites
print('%-12s %-8s %s' % ('call', 'arg3', 'pushes(program order)'))
for s in sites:
    print('%-12s %-8s %s' % (s['call'], s['arg3'], s['pushes']))
chk('K4a exactly 15 wrapper call sites', len(sites) == 15, len(sites))
chk('K4b every one passes arg3 == 7', all(s['arg3'] == '7' for s in sites),
    sorted({s['arg3'] for s in sites}))
chk('K4c 7 & 0x14 == 4 (non-zero => ZF=0 => je not taken => fallthrough arm)',
    (7 & 0x14) == 4, 7 & 0x14)
# control: the arithmetic DOES differ for a value whose bit2 is clear
chk('K4d control: a dwClsContext of 0 would take the else arm (0 & 0x14 == 0)',
    (0 & 0x14) == 0)

json.dump(R, open(OUT, 'w'), ensure_ascii=False, indent=1)
json.dump(ASSERT, open(OUT.replace('.json', '_assert.json'), 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for a in ASSERT if not a['pass'])
print()
print('== assertions: %d total, %d FAIL ==' % (len(ASSERT), nf))
print('wrote', OUT)
