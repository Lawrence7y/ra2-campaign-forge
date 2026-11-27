#!/usr/bin/env python3
"""R144 exec: independent recomputation of multi-form vtable-install census.

Fully self-contained (no import of r144a/r144b conclusions). Address conversion
reimplemented locally from pefile+struct. .text streamed with disasm_lite 64KB
chunks; never opens detail=True over the whole section.
"""
import sys, re, json, struct, collections, random, hashlib, time, os
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

T0 = time.time()
BASE = '/home/t628/projects/ra2-campaign-forge'
EXE = os.path.join(BASE, 'ra2bench/gamemd.exe')
OUTDIR = os.path.join(BASE, '_r144/sub')
os.makedirs(OUTDIR, exist_ok=True)

# ---------------- binary / PE ----------------
data = open(EXE, 'rb').read(); N = len(data)
sha = hashlib.sha256(data).hexdigest()
pe = pefile.PE(EXE, fast_load=True); IB = pe.OPTIONAL_HEADER.ImageBase
secs = [(s.Name.decode().rstrip('\x00'), s.VirtualAddress, s.Misc_VirtualSize,
         s.PointerToRawData, s.SizeOfRawData) for s in pe.sections]
T = [s for s in secs if s[0] == '.text'][0]

def va2off(va):
    for nm, ava, vs, raw, rs in secs:
        lo = IB + ava
        if lo <= va < lo + max(vs, rs):
            d = va - lo
            return raw + d if d < rs else None
    return None

def rd(va, l):
    o = va2off(va)
    if o is None or o + l > N: return None
    return data[o:o+l]

def dw(va):
    b = rd(va, 4)
    return None if b is None else struct.unpack('<I', b)[0]

def sec_of(va):
    for nm, ava, vs, raw, rs in secs:
        lo = IB + ava
        if lo <= va < lo + max(vs, rs): return nm
    return None

# ---------------- VTS (R143 口径, independently implemented) ----------------
pat = re.compile(rb'\.\?A[VU][!-~]{1,200}?@@')
TDs = {}
for nm, ava, vs, raw, rs in secs:
    if nm in ('.data', '.rdata'):
        blob = data[raw:raw+rs]
        for m in pat.finditer(blob):
            s = IB + ava + m.start()
            if dw(s-8) is not None and dw(s-4) == 0 and sec_of(dw(s-8)) in ('.data', '.rdata'):
                TDs[s-8] = m.group()
tdset = set(TDs)
COL = set()
for nm, ava, vs, raw, rs in secs:
    if nm in ('.data', '.rdata'):
        blob = data[raw:raw+rs]
        for i in range(len(blob)//4):
            v = struct.unpack_from('<I', blob, i*4)[0]
            if v in tdset:
                c = IB + ava + i*4 - 12
                if dw(c) == 0 and dw(c+12) == v and dw(c+16) != 0:
                    COL.add(c)
VTS = set()
for nm, ava, vs, raw, rs in secs:
    if nm in ('.data', '.rdata'):
        blob = data[raw:raw+rs]
        for i in range(len(blob)//4):
            v = struct.unpack_from('<I', blob, i*4)[0]
            if v in COL:
                vt = IB + ava + i*4 + 4
                if dw(vt-4) == v:
                    VTS.add(vt)

COLof = {}
for vt in VTS:
    c = dw(vt-4)
    if c in COL: COLof[vt] = c
coloff = {c: dw(c+4) for c in COL}
coltd = {c: dw(c+12) for c in COL}
vt_off = {vt: coloff.get(COLof.get(vt)) for vt in VTS}
vt_td  = {vt: coltd.get(COLof.get(vt)) for vt in VTS}

# ---------------- streaming disassembly ----------------
GEN = ('eax', 'ebx', 'ecx', 'edx', 'esi', 'edi')
def norm(op):
    if not op: return ''
    op = re.sub(r'\s*([+,*])\s*', r'\1', op)
    op = re.sub(r'([+-])(\d+)(?![\dx])', lambda m: '%s0x%x' % (m.group(1), int(m.group(2))), op)
    return op
RE_STORE = re.compile(r'^dword ptr \[([a-z0-9]+)([+-]0x[0-9a-f]+)?\](?:,([^,]+))?$')
RE_IMM = re.compile(r'^(0x[0-9a-f]+|\d+)$')
def immv(t): return (int(t, 16) if t.startswith('0x') else int(t)) & 0xFFFFFFFF
def disp_of(s):
    if not s: return 0
    s = s.strip()
    if s.startswith('+0x'): return int(s[3:], 16)
    if s.startswith('-0x'): return -int(s[3:], 16)
    if s.startswith('+'): return int(s[1:])
    if s.startswith('-'): return -int(s[1:])
    return int(s, 0)

md = Cs(CS_ARCH_X86, CS_MODE_32)
f1 = []   # (va, base, vt)                   gen, disp==0
f3 = []   # (va, base, disp, vt)             gen, disp!=0
f4 = []   # (va, abs, disp, vt)              absolute base
o = T[3]; end = o + T[4]; chunk = 65536; nd = 0
while o < end:
    cb = data[o:min(o+chunk, end)]
    base_va = IB + (T[1] + (o - T[3]))
    consumed = 0
    for a, sz, mn, op in md.disasm_lite(cb, base_va):
        if a - base_va + sz > len(cb): break
        consumed = a - base_va + sz
        nd += 1
        m = RE_STORE.match(norm(op))
        if not m: continue
        b = m.group(1); disp = disp_of(m.group(2)); tgt = m.group(3)
        if tgt is None or not RE_IMM.match(tgt): continue
        iv = immv(tgt)
        if iv not in VTS: continue
        if b in GEN:
            if disp == 0: f1.append((a, b, iv))
            else: f3.append((a, b, disp, iv))
        elif b.startswith('0x'):
            f4.append((a, b, disp, iv))
    o += consumed if consumed else 1

# ---------------- numbers ----------------
covF1 = {s[2] for s in f1}
covF3 = {s[3] for s in f3}
covF4 = {s[3] for s in f4}
unc380 = sorted(VTS - covF1)
hist3 = collections.Counter(s[2] for s in f3)

# item 6: same-TypeDescriptor twin among F1-covered
by_td = collections.defaultdict(list)
for vt in VTS:
    by_td[vt_td.get(vt)].append(vt)
unc_td_twin = 0
for vt in unc380:
    tw = [x for x in by_td.get(vt_td.get(vt), []) if x != vt]
    if any(x in covF1 for x in tw): unc_td_twin += 1

# site pairs for items 7-9: all gen-register imm stores (F1 + F3)
sites = [(iv, 0) for (a, b, iv) in f1] + [(iv, d) for (a, b, d, iv) in f3]

def agree(pairs):
    ok = tot = 0
    for vt, d in pairs:
        off = vt_off.get(vt)
        if off is None: continue
        tot += 1; ok += (off == d)
    return ok, tot, (ok/tot if tot else None)

okr, totr, rater = agree(sites)

# global permutation of disp (seed=144)
random.seed(144)
vts_arr = [vt for vt, _ in sites]; disp_arr = [d for _, d in sites]
sh = disp_arr[:]; random.shuffle(sh)
okg, totg, rateg = agree(list(zip(vts_arr, sh)))

# within-disp-bucket permutation (seed=144) -- r144b-style control
random.seed(144)
buck = collections.defaultdict(list)
for vt, d in sites: buck[d].append(vt)
pairs_wb = []
for d, vl in buck.items():
    sl = vl[:]; random.shuffle(sl)
    pairs_wb += [(v, d) for v in sl]
okw, totw, ratew = agree(pairs_wb)

# independent-hypothesis baseline: sum_d P(off=d)*P(disp=d), both marginals measured
offs = [vt_off[vt] for vt, _ in sites if vt_off.get(vt) is not None]
dsp = [d for vt, d in sites if vt_off.get(vt) is not None]
n_b = len(offs)
c_off = collections.Counter(offs); c_dsp = collections.Counter(dsp)
baseline = sum((c_off[d]/n_b)*(c_dsp[d]/n_b) for d in set(c_off) | set(c_dsp))

# variant: include F4 abs sites too
sites_all = sites + [(iv, d) for (a, b, d, iv) in f4]
oka, tota, ratea = agree(sites_all)

targets = {
    'vts': 1218, 'F1_sites': 2741, 'F1_distinct': 838,
    'F3_sites': 1305, 'F3_distinct': 344,
    'F4_sites': 341, 'F4_distinct': 243,
    'unc380': 380, 'unc_td_twin': 229, 'rate': 0.9231, 'rate_perm': 0.9231,
}
def near(a, b, tol=0.005):
    return (abs(a-b) <= tol) if isinstance(b, float) else (a == b)

res = {
    'exe_sha256': sha, 'exe_bytes': N, 'image_base': hex(IB),
    'disasm_instructions': nd,
    'n_td': len(TDs), 'n_col': len(COL),
    'item1_vts_distinct': len(VTS),
    'item2_F1_sites': len(f1), 'item2_F1_distinct': len(covF1),
    'item3_F3_sites': len(f3), 'item3_F3_distinct': len(covF3),
    'item3_F3_disp_hist_top3': [[hex(d), c] for d, c in hist3.most_common(3)],
    'item3_F3_disp_hist_top12': [[hex(d), c] for d, c in hist3.most_common(12)],
    'item4_F4_sites': len(f4), 'item4_F4_distinct': len(covF4),
    'item5_F1_uncovered': len(unc380),
    'item6_unc_with_covered_td_twin': unc_td_twin,
    'item7_agree_real': [okr, totr], 'item7_rate': rater,
    'item7_variant_with_F4_rate': [oka, tota, ratea],
    'item8_global_perm_seed144': [okg, totg], 'item8_global_perm_rate': rateg,
    'item8b_within_bucket_perm_seed144': [okw, totw], 'item8b_within_bucket_rate': ratew,
    'item9_independent_baseline': baseline,
    'item9_marginals': {'n_b': n_b, 'off_top': [(hex(d), c) for d, c in c_off.most_common(8)],
                        'disp_top': [(hex(d), c) for d, c in c_dsp.most_common(8)]},
    'judgment': ('YES invariant: within a disp bucket every site has identical disp d, so a '
                 'match depends only on off(vt)==d; permuting vt inside the bucket preserves the '
                 'bucket vt multiset, hence the count of off(vt)==d is unchanged for any seed. '
                 'The stated reason "depends only on disp marginal, independent of vt" is NOT the '
                 'correct reason (rate depends jointly on vt via off); the control is degenerate '
                 'and must be scrapped. Global disp permutation is the meaningful control.'),
}
cmp = {
    'VTS==1218': near(len(VTS), 1218),
    'F1==2741/838': near(len(f1), 2741) and near(len(covF1), 838),
    'F3==1305/344': near(len(f3), 1305) and near(len(covF3), 344),
    'F3hist_top3': [[hex(d), c] for d, c in hist3.most_common(3)] == [['0xc', 345], ['0x4', 344], ['0x8', 338]],
    'F4==341/243': near(len(f4), 341) and near(len(covF4), 243),
    'unc380==380': near(len(unc380), 380),
    'td_twin==229': near(unc_td_twin, 229),
    'rate==0.9231': near(rater, 0.9231),
    'rate_perm==0.9231': near(ratew, 0.9231),
}
res['targets'] = targets
res['comparison'] = cmp
res['all_match'] = all(cmp.values())
res['elapsed_s'] = round(time.time() - T0, 1)

jpath = os.path.join(OUTDIR, 'r144_exec.json')
with open(jpath, 'w') as fh:
    json.dump(res, fh, indent=1, ensure_ascii=False)

summary = {
    'sha256': sha, 'VTS': len(VTS), 'F1': [len(f1), len(covF1)], 'F3': [len(f3), len(covF3)],
    'F3top3': res['item3_F3_disp_hist_top3'], 'F4': [len(f4), len(covF4)],
    'unc380': len(unc380), 'td_twin': unc_td_twin,
    'rate_real': [okr, totr, rater], 'rate_global_perm': [okg, totg, rateg],
    'rate_within_bucket_perm': [okw, totw, ratew], 'baseline': round(baseline, 6),
    'judgment_short': 'within-bucket perm is necessarily invariant -> degenerate control, scrap it',
    'all_match': res['all_match'],
}
print('SUMMARY ' + json.dumps(summary, ensure_ascii=False))
