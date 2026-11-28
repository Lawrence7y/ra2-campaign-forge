#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R199 EXEC B: 0x4C9150 纯桩跨 33 槽号的选择依据 —— 单脚本全量静态取证。"""
import sys, os, struct, json, re, collections
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone

STUB = 0x4C9150
TLO, THI = 0x401000, 0x7E1000
OUT = '/home/t628/projects/ra2-campaign-forge/_r199/exec_b'
os.makedirs(OUT, exist_ok=True)
PASS, FAIL = [], []
def chk(cond, msg):
    (PASS if cond else FAIL).append(msg)
    print(('PASS' if cond else 'FAIL') + ' ' + msg)
def text(va): return va is not None and TLO <= va < THI
def sec(va): return P.where(va)
def cstr(va, n=400):
    s = P.cstr(va, n)
    return s.decode('latin1', 'replace') if s else ''
def u32(va): return P.dw(va)
R = P.RAW
srd = P.B['.rdata']; ord_ = srd['rawptr']; erd = ord_ + srd['rawsize']
sda = P.B['.data'];  oda = sda['rawptr']; eda = oda + sda['rawsize']

# ================= P1 baseline =================
COL = set()
for base, o, e in ((srd['lo'], ord_, erd), (sda['lo'], oda, eda)):
    for off in range(o, e - 24 + 1, 4):
        v0, v4, v8, v12, v16 = struct.unpack_from('<5I', R, off)
        if v0 in (0, 1, 2) and v8 == 0 and sec(v12) == '.data' and sec(v16) == '.rdata':
            COL.add(base + (off - o))
print('[*] COL =', len(COL))
chk(len(COL) == 1214, 'P1 COL==1214 (measured %d)' % len(COL))

VT = set()
for base, o, e in ((srd['lo'], ord_, erd), (sda['lo'], oda, eda)):
    for off in range(o, e - 4 + 1, 4):
        va = base + (off - o)
        if u32(va - 4) in COL and text(struct.unpack_from('<I', R, off)[0]):
            VT.add(va)
print('[*] VT =', len(VT))
chk(len(VT) == 1214, 'P1 VT==1214 (measured %d)' % len(VT))

def nslot(vt):
    n = 0
    while text(u32(vt + 4 * n)):
        n += 1
        if n > 100000: break
    return n
NS = {vt: nslot(vt) for vt in VT}
slot_total = sum(NS.values())
print('[*] slot total =', slot_total)
chk(slot_total == 14044, 'P1 slot total==14044 (measured %d)' % slot_total)

# CHD / BCD: CHD = COL+16, CHD+8 = n, CHD+12 = BCD array pointer
# BCD: +0 pTD, +4 ncb, +8 mdisp (signed), +12 pdisp, +16 vdisp, +20 attributes
def bcd_of(b):
    ptd, ncb, md, pdisp, vdisp, attr = struct.unpack_from('<6I', R, P.r2o(b)) if P.r2o(b) else (None,)*6
    if md is not None and md >= 0x80000000: md -= 0x100000000
    return ptd, ncb, md, pdisp, vdisp, attr

chd_of, main_bcd_of = {}, {}
for col in COL:
    chd = u32(col + 16)
    n = u32(chd + 8) if chd else None
    arr = u32(chd + 12) if chd else None
    if n is None or arr is None or not (1 <= n <= 2000) or sec(arr) not in ('.data', '.rdata'):
        continue
    chd_of[col] = (chd, n, arr)
    b0 = u32(arr)
    if b0 is None: continue
    ptd, ncb, md, _, _, _ = bcd_of(b0)
    if ptd == u32(col + 12) and md == 0:
        main_bcd_of[col] = (b0, n, arr, ncb)

col_of = {vt: u32(vt - 4) for vt in VT}
col4_of = {vt: u32(col_of[vt] + 4) for vt in VT}
# P1 主表判据：COL+4 == 0；BCD mdisp==0 (main_bcd_of) 另用于继承比较
main_vt = {vt for vt in VT if col4_of.get(vt) == 0}
main_vt_cols = {col_of[v] for v in main_vt}
print('[*] main tables (mdisp==0) =', len(main_vt))
chk(len(main_vt) == 954, 'P1 main tables==954 (measured %d)' % len(main_vt))

# ================= P2 stub counts =================
stub_slots = []
for vt in VT:
    for k in range(NS[vt]):
        if u32(vt + 4 * k) == STUB:
            stub_slots.append((vt, k))
stub_tables = set(vt for vt, _ in stub_slots)
slot_nums = set(k for _, k in stub_slots)
print('[*] P2: kinds=%d tables=%d slots=%d' % (len(slot_nums), len(stub_tables), len(stub_slots)))
print('[*] P2 slot nums =', sorted(slot_nums))
chk(len(slot_nums) == 33, 'P2 kinds==33 (measured %d)' % len(slot_nums))
chk(len(stub_tables) == 39, 'P2 tables==39 (measured %d)' % len(stub_tables))
chk(len(stub_slots) == 205, 'P2 slots==205 (measured %d)' % len(stub_slots))
expect = set(range(25)) | {27, 28, 29, 32, 35, 40, 238, 292}
chk(slot_nums == expect, 'P2 slot set exact (measured %s)' % sorted(slot_nums))

# ================= Q2 stub body =================
o = P.r2o(STUB)
raw32 = R[o:o+32]
md2 = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md2.detail = True
insns = list(md2.disasm(raw32, STUB))
real = [i for i in insns if i.mnemonic != 'nop']
terminator = real[-1]
print('[*] Q2 bytes32 =', raw32.hex())
print('[*] Q2 insns =', [(hex(i.address), i.mnemonic, i.op_str, i.bytes.hex()) for i in real])
print('[*] Q2 detail insn count=%d bytes=%d terminator=%s %s' %
      (len(insns), sum(i.size for i in insns), terminator.mnemonic, terminator.op_str))
chk(insns[0].mnemonic == 'xor' and insns[1].mnemonic == 'ret', 'Q2 xor eax,eax; ret')

pat = b'\x33\xc0\xc3'
hits = []
CH = 65536
for cs in range(TLO, THI, CH):
    chunk = R[P.r2o(cs):P.r2o(cs)+min(CH, THI-cs)]
    pos = 0
    while True:
        idx = chunk.find(pat, pos)
        if idx < 0: break
        hits.append(cs + idx)
        pos = idx + 1
# explicit criterion: preceding byte is 0x90 (alignment NOP) or 0xC3/0xC2/0xCC (function boundary)
# — i.e. the 33 C0 C3 does not follow a call/jmp (E8/E9/EB) landing here.
def is_entry(va):
    prev = R[P.r2o(va) - 1] if P.r2o(va) > 0 else 0
    return prev in (0x90, 0xC3, 0xC2, 0xCC)
entries = [va for va in hits if is_entry(va)]
print('[*] Q2 33C0C3 hits=%d entries(prev=90/C3/C2/CC)=%d' % (len(hits), len(entries)))
# all vtable impl addrs whose body starts 33 C0 C3
all_impl = {u32(vt+4*k) for vt in VT for k in range(NS[vt])}
zero_impls = set()
for a in all_impl:
    if not text(a): continue
    ao = P.r2o(a)
    if ao is not None and R[ao:ao+3] == pat: zero_impls.add(a)
print('[*] Q2 vtable impl addrs with 33C0C3 body =', [hex(x) for x in sorted(zero_impls)])
chk(STUB in zero_impls, 'Q2 0x4C9150 reachable via vtable')

# ================= Q3 histogram =================
ai = collections.defaultdict(lambda: {'tables': set(), 'slots': 0, 'kinds': set()})
for vt in VT:
    for k in range(NS[vt]):
        a = u32(vt+4*k)
        ai[a]['tables'].add(vt); ai[a]['slots'] += 1; ai[a]['kinds'].add(k)
ranked = sorted(ai.items(), key=lambda kv: -len(kv[1]['kinds']))
multi = [(a, v) for a, v in ranked if len(v['kinds']) >= 2]
srank = next(i+1 for i, (a, _) in enumerate(ranked) if a == STUB)
print('[*] Q3 addresses with kind>=2 =', len(multi), 'stub rank =', srank)
for a, v in multi[:15]:
    print('   %08x tables=%d slots=%d kinds=%d slots=%s' %
          (a, len(v['tables']), v['slots'], len(v['kinds']), sorted(v['kinds'])[:40]))

# ================= Q4 per-table =================
def cname(vt):
    col = col_of.get(vt)
    return cstr(u32(col+12)+8) if col else ''
rows = []
for vt in sorted(stub_tables):
    ks = sorted(k for t, k in stub_slots if t == vt)
    n = NS[vt]
    rows.append({'vt': vt, 'name': cname(vt), 'mdisp': col4_of.get(vt), 'nslot': n,
                 'stub_slots': ks, 'contiguous': all(ks[i+1] == ks[i]+1 for i in range(len(ks)-1)),
                 'has_slot0': 0 in ks, 'pct': round(100.0*len(ks)/n, 2)})
for r in rows:
    print('   VT=%08x %-62s mdisp=%s nslot=%d stub=%s contig=%s s0=%s pct=%.2f' %
          (r['vt'], r['name'][:62], r['mdisp'], r['nslot'], r['stub_slots'], r['contiguous'], r['has_slot0'], r['pct']))
c0 = sum(1 for r in rows if 0 in r['stub_slots'])
c1 = sum(1 for r in rows if 1 in r['stub_slots'])
c2 = sum(1 for r in rows if 2 in r['stub_slots'])
print('[*] Q4 tables with slot0/1/2 =', c0, c1, c2)
chk(c0 <= 39 and c1 <= 39 and c2 <= 39, 'Q4 slot0/1/2 counts bounded')

# ================= P3 inheritance: direct children =================
ptd_cols = collections.defaultdict(set)
for vt in VT: ptd_cols[u32(col_of[vt]+12)].add(vt)
def direct_children(col):
    mb = main_bcd_of.get(col)
    if not mb: return []
    _, n, arr, ncb0 = mb
    out = []
    j = 1
    while j < n:
        b = u32(arr + 4*j)
        if b is None: break
        out.append(bcd_of(b))
        j += bcd_of(b)[1] + 1
    return out
def direct_base_vts(col, mdisp_filter):
    out = []
    for info in direct_children(col):
        ptd, ncb, md = info[0], info[1], info[2]
        if mdisp_filter is not None and md != mdisp_filter: continue
        for pcol in ptd_cols.get(ptd, ()):
            if pcol in main_vt_cols and pcol != col:
                out.append(pcol)
    return out

q5 = {'a': 0, 'b': 0, 'c': 0, 'ba': collections.Counter()}
q5r3 = {'a': 0, 'b': 0, 'c': 0, 'ba': collections.Counter()}
der = {'derived_tables': 0, 'same_stub': 0, 'other': 0, 'no_slot': 0}
for r in rows:
    vt = r['vt']; col = col_of[vt]
    for k in r['stub_slots']:
        b0 = direct_base_vts(col, 0)
        if not b0: q5['c'] += 1
        else:
            bcol = b0[0]; bvt = next((v for v in main_vt if col_of[v] == bcol), None)
            if bvt is None or k >= NS[bvt]: q5['c'] += 1
            else:
                ba = u32(bvt + 4*k)
                if ba == STUB: q5['a'] += 1
                else: q5['b'] += 1; q5['ba'][ba] += 1
        anyb = direct_base_vts(col, None)
        ok = False
        for bc in anyb:
            bvt = next((v for v in main_vt if col_of[v] == bc), None)
            if bvt and k < NS[bvt]:
                ba = u32(bvt + 4*k)
                if ba == STUB: q5r3['a'] += 1
                else: q5r3['b'] += 1; q5r3['ba'][ba] += 1
                ok = True; break
        if not ok: q5r3['c'] += 1
    for info in direct_children(col):
        if info[2] != 0: continue
        for dcols in ptd_cols.get(info[0], ()):
            if dcols in main_vt_cols and dcols != col:
                der['derived_tables'] += 1
                dvt = next((v for v in main_vt if col_of[v] == dcols), None)
                for k in r['stub_slots']:
                    if dvt is None or k >= NS[dvt]: der['no_slot'] += 1
                    elif u32(dvt + 4*k) == STUB: der['same_stub'] += 1
                    else: der['other'] += 1
print('[*] Q5 base(mdisp==0): a=%d b=%d c=%d sum=%d' % (q5['a'], q5['b'], q5['c'], q5['a']+q5['b']+q5['c']))
print('[*] Q5 top10 real base impl =', [(hex(a), c) for a, c in q5['ba'].most_common(10)])
print('[*] Q5 derived =', der)
print('[*] R3 base(any mdisp): a=%d b=%d c=%d' % (q5r3['a'], q5r3['b'], q5r3['c']))

# ================= Q6 =================
g = {'with': [0, 0], 'without': [0, 0]}
for r in rows:
    key = 'with' if direct_base_vts(col_of[r['vt']], 0) else 'without'
    g[key][0] += 1; g[key][1] += len(r['stub_slots'])
for v in g.values(): v.append(round(v[1]/v[0], 2) if v[0] else 0)
print('[*] Q6 groups =', g)

# ================= Q7 =================
def prefix_of(nm):
    if nm.startswith('.?AV'): nm = nm[4:]
    elif nm.startswith('AV'): nm = nm[2:]
    nm = nm.split('@@', 1)[0]
    m = re.match(r'([A-Za-z_][A-Za-z0-9_]*)', nm)
    return m.group(1) if m else nm[:12]
pref = collections.Counter(prefix_of(r['name']) for r in rows)
print('[*] Q7 prefix top15 =', pref.most_common(15))
print('[*] Q7 names =', [r['name'] for r in rows])

# ================= R1 thresholds =================
r1 = {t: sum(1 for _, v in ranked if len(v['kinds']) >= t) for t in (2, 3, 5)}
print('[*] R1 >=2/3/5 =', r1)

# ================= R2 body criterion =================
r2s, r2t = [], set()
for vt in VT:
    for k in range(NS[vt]):
        a = u32(vt+4*k); ao = P.r2o(a)
        if ao is not None and R[ao:ao+3] == pat:
            r2s.append((vt, k)); r2t.add(vt)
r2k = set(k for _, k in r2s)
print('[*] R2 body-based: kinds=%d tables=%d slots=%d' % (len(r2k), len(r2t), len(r2s)))

result = {
    'baseline': {'COL': len(COL), 'VT': len(VT), 'slots': slot_total, 'main': len(main_vt)},
    'P2': {'slot_kinds': len(slot_nums), 'tables': len(stub_tables), 'slots': len(stub_slots), 'slot_numbers': sorted(slot_nums)},
    'Q2': {'bytes32': raw32.hex(), 'detail_insn_count': len(insns), 'detail_bytes': sum(i.size for i in insns),
           'real_body': [i.mnemonic+' '+i.op_str for i in real], 'terminator': terminator.mnemonic+' '+terminator.op_str,
           'xor_ret_hits': len(hits), 'xor_ret_entries': len(entries), 'entry_criterion': 'preceding byte in {0x90,0xC3,0xC2,0xCC}',
           'vtable_zero_body_addrs': sorted(hex(x) for x in zero_impls), 'stub_unique_zero_ref': len(zero_impls) == 1},
    'Q3': {'ge2_count': len(multi), 'stub_rank': srank, 'top15': [
        {'addr': hex(a), 'tables': len(v['tables']), 'slots': v['slots'], 'kinds': len(v['kinds']), 'slotnums': sorted(v['kinds'])}
        for a, v in multi[:15]]},
    'Q4': {'rows': [{**r, 'vt': hex(r['vt']), 'mdisp': str(r['mdisp'])} for r in rows],
           'slot0': c0, 'slot1': c1, 'slot2': c2},
    'Q5': {'mdisp0': {'a': q5['a'], 'b': q5['b'], 'c': q5['c'], 'top10': [(hex(a), n) for a, n in q5['ba'].most_common(10)]},
           'derived': der, 'r3_any_mdisp': {'a': q5r3['a'], 'b': q5r3['b'], 'c': q5r3['c'],
           'top10': [(hex(a), n) for a, n in q5r3['ba'].most_common(10)]}},
    'Q6': g,
    'Q7': {'prefix_top15': pref.most_common(15), 'all_names': [r['name'] for r in rows]},
    'R1': r1,
    'R2': {'kinds': len(r2k), 'tables': len(r2t), 'slots': len(r2s)},
    'assertions': {'pass': PASS, 'fail': FAIL},
}
for fn in ('stub.json', 'stub.txt'):
    with open(os.path.join(OUT, fn), 'w') as f: json.dump(result, f, indent=2, ensure_ascii=False)
print('[*] DONE PASS=%d FAIL=%d' % (len(PASS), len(FAIL)))
if FAIL: sys.exit(1)
