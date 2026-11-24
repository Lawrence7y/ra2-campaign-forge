#!/usr/bin/env python3
"""R108-EXEC supplement 2:
 - span-matched negative control (the 6 real spans vs random A-pair spans)
 - dword-pointer references to each post-ret address across .rdata/.data/.text
 - linear-sweep resync report for the 6 regions
"""
import json, random, struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = 'ra2bench/gamemd.exe'
OUT = '_r108/_exec/'
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
sections = [(s.Name.rstrip(b'\x00').decode(), s.VirtualAddress + IB,
             max(s.Misc_VirtualSize, s.SizeOfRawData), s.PointerToRawData) for s in pe.sections]
raw = open(EXE, 'rb').read()
tsec = [x for x in sections if x[0] == '.text'][0]
TEXT_VA, TEXT_END = tsec[1], tsec[1] + tsec[2]

ac = json.load(open(OUT + 'ac_sets.json'))
bs = json.load(open(OUT + 'bset.json'))
A = {int(k, 16) for k in ac['A']}
C = {int(k, 16): [[int(a), m] for a, m in v] for k, v in ac['C'].items()}
B = {int(k, 16) for k in bs['B']}
Cset = set(C)
rf = json.load(open(OUT + 'rets_forensic.json'))

TABLES = [(0x46f5a0,0x46de20,0x46e4be),(0x5001e4,0x4ffd90,0x4ffde9),
          (0x58bda4,0x58bc20,0x58bd85),(0x71f2c0,0x71e940,0x71eea2),
          (0x71f328,0x71e940,0x71f092),(0x79f028,0x79da90,0x79ed73)]

# ---- span-matched negative control ----
rng = random.Random(20261117)
pool = sorted(A)
sample = rng.sample(pool, 600)
real_spans = [H - S for _, S, H in TABLES]
spans = []
for Sp in sample:
    nxt = next((x for x in pool if x > Sp), None)
    if nxt and 0 < nxt - Sp <= 0x40000:
        spans.append(nxt - Sp)
spans.sort()
lo_b, hi_b = min(real_spans), max(real_spans)
banded = [s for s in spans if lo_b <= s <= hi_b]
print('real spans', [hex(x) for x in real_spans])
print('random A-pair spans: n=%d median=%s p25=%s p75=%s' % (
    len(spans), hex(spans[len(spans)//2]), hex(spans[len(spans)//4]),
    hex(spans[3*len(spans)//4])))
print('random pairs inside real span band [%s,%s]: %d' % (hex(lo_b), hex(hi_b), len(banded)))

def counts(Sp, nxt):
    lo, hi = Sp + 1, nxt - 1
    a = [x for x in A if lo <= x <= hi]
    b = [x for x in B if lo <= x <= hi]
    c = [t for t in Cset if lo <= t <= hi and any(not (Sp <= s < nxt) for s, m in C[t])]
    return a, b, c

fired = 0
tot = 0
for Sp in sample:
    nxt = next((x for x in pool if x > Sp), None)
    if not nxt or not (lo_b <= nxt - Sp <= hi_b):
        continue
    tot += 1
    a, b, c = counts(Sp, nxt)
    if a or b or c:
        fired += 1
print('span-matched negative control: fired %d/%d = %.4f' % (fired, tot, fired/tot if tot else 0))

# ---- dword refs to post-ret addresses ----
refs = {}
for t in rf['tables']:
    for r in t['rets']:
        refs[r['after']] = []
for name, sva, sz, praw in sections:
    if name not in ('.text', '.rdata', '.data'):
        continue
    blob = raw[praw:praw + sz]
    for i in range(0, len(blob) - 3, 4):
        v = struct.unpack('<I', blob[i:i+4])[0]
        k = hex(v)
        if k in refs:
            refs[k].append({'section': name, 'at': hex(sva + i)})

n_ref = sum(1 for k, v in refs.items() if v)
print('post-ret addrs total %d | with any dword pointer ref %d' % (len(refs), n_ref))
ext_ref = {k: [r for r in v if r['section'] != '.text'] for k, v in refs.items()}
print('post-ret addrs with .rdata/.data dword ref %d' % sum(1 for v in ext_ref.values() if v))

# ---- resync + reachability summary ----
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False
def sweep(start, end):
    insns, resync = [], []
    mv = memoryview(raw[tsec[3] + (start - TEXT_VA):tsec[3] + (end - TEXT_VA)])
    off = 0
    while off < end - start:
        c = 0
        for (addr, size, mn, ops) in md.disasm_lite(mv[off:], start + off):
            insns.append((addr, size, mn, ops)); c += size
        if c == 0:
            resync.append(start + off); off += 1
        else:
            off += c
    return insns, resync

res = []
for tbl, S, H in TABLES:
    insns, resync = sweep(S, H)
    # fallthrough-reachability from S
    by = {i[0]: i for i in insns}
    seen, stack = set(), [S]
    while stack:
        cur = stack.pop()
        if cur in seen or cur not in by:
            continue
        seen.add(cur)
        a0, sz, mn, ops = by[cur]
        tgt = int(ops, 16) if ops.startswith('0x') and (mn == 'jmp' or mn in
              {'jo','jno','jb','jae','je','jne','jbe','ja','js','jns','jp','jnp','jl','jge','jle','jg'}) else None
        if mn in ('ret', 'retn', 'retf'):
            continue  # ret terminates the path: fallthrough is not executable
        if tgt is not None and S <= tgt < H:
            stack.append(tgt)
        if mn != 'jmp' and a0 + sz < H:
            stack.append(a0 + sz)
    res.append({'table': hex(tbl), 'S': hex(S), 'H': hex(H), 'span': H - S,
                'insns': len(insns), 'resync_bytes': len(resync),
                'resync_addrs': [hex(x) for x in resync],
                'reachable': len(seen),
                'unreachable_pct': round(100.0 * (len(insns) - len(seen)) / len(insns), 1)})
for r in res:
    print(r['table'], 'span', hex(r['span']), 'insns', r['insns'], 'resync', r['resync_bytes'],
          'reachable', r['reachable'], 'unreachable%%', r['unreachable_pct'])

json.dump({'span_matched': {'window': [hex(lo_b), hex(hi_b)], 'evaluated': tot,
                            'fired': fired, 'ratio': fired / tot if tot else 0.0},
           'random_pair_span_stats': {'n': len(spans), 'median': hex(spans[len(spans)//2])},
           'post_ret_refs': refs, 'sweep': res},
          open(OUT + 'supp2.json', 'w'), indent=1)
