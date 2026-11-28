#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205-EXEC-X1: independent recomputation of RTTI class block layout.
All numbers are derived from gamemd.exe; no expected values are copied.
"""
import os, sys, json, struct, random, collections

ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, ROOT + '/_r185')
import pe185 as P  # P.B, P.RAW, P.dw, P.cstr, P.where

OUT = ROOT + '/_r205/exec_x1'
os.makedirs(OUT, exist_ok=True)


def sname(pTD, maxn=400):
    """Read the mangled class name from a TypeDescriptor pointer (name at +8)."""
    if pTD is None:
        return None
    b = P.cstr(pTD + 8, maxn)
    return None if b is None else b.decode('latin1', 'replace')


def dwords_in(secname):
    """Yield raw-backed, 4-byte-aligned virtual addresses of a section."""
    s = P.B[secname]
    lo = (s['lo'] + 3) // 4 * 4
    hi = s['lo'] + s['rawsize'] - 4
    for a in range(lo, hi + 1, 4):
        yield a


def signed32(v):
    if v is None:
        return None
    return v - 0x100000000 if v >= 0x80000000 else v


# ---------- Step 1: COL collection ----------
COL = {}
for sec in ('.rdata', '.data'):
    for a in dwords_in(sec):
        sig = P.dw(a)
        if sig not in (0, 1, 2):
            continue
        if P.dw(a + 8) != 0:                       # w[i+2] == 0
            continue
        pTD, pCHD = P.dw(a + 12), P.dw(a + 16)     # w[i+3], w[i+4]
        if P.where(pTD) != '.data' or P.where(pCHD) != '.rdata':
            continue
        raw = P.cstr(pTD + 8, 400)
        if raw is None or not raw.startswith(b'.?A') or not raw.endswith(b'@@'):
            continue
        COL[a] = {'sig': sig, 'mdisp': P.dw(a + 4), 'pMC': P.dw(a + 8),
                  'pTD': pTD, 'pCHD': pCHD, 'name': raw.decode('latin1', 'replace')}

# ---------- Step 2: vftable starts ----------
VFT = set()
for secname in P.B:
    for a in dwords_in(secname):
        v = P.dw(a)
        if v is None or P.where(v) != '.text':
            continue
        if P.dw(a - 4) in COL:
            VFT.add(v)

# ---------- Step 3: CHD set (group COL by pCHD = +16) ----------
GROUPS = collections.defaultdict(list)
for a, c in COL.items():
    GROUPS[c['pCHD']].append(a)
CHD = set(GROUPS)


# ---------- X4 criterion ----------
def x4(a):
    return (P.dw(a + 16) == 0 and P.dw(a + 20) == 0 and P.dw(a + 24) == 0
            and P.where(P.dw(a + 28)) == '.data' and P.dw(a + 32) == a)


def x4_shifted(a):
    return (P.dw(a + 20) == 0 and P.dw(a + 24) == 0 and P.dw(a + 28) == 0
            and P.where(P.dw(a + 32)) == '.data' and P.dw(a + 36) == a)


X4_hits = [a for a in sorted(CHD) if x4(a)]
X5_hits = [a for a in sorted(CHD) if (a + 16) in COL]
X6_hits = [a for a in X5_hits if P.dw(a + 32) == a]

# ---------- X7: mdisp==0 distribution per CHD group ----------
dist = collections.Counter()
for a, cols in GROUPS.items():
    z = sum(1 for c in cols if COL[c]['mdisp'] == 0)
    dist[z] += 1

# ---------- X8: deduplicated BCD records ----------
# Class-owned pTD set: the pTD pointer embedded in each CHD's COL (+16 COL -> +28).
# Compare by pTD name as well, since the same class can have distinct descriptor
# instances (different addresses, identical mangled name).
OWN_PTD_PTR = {P.dw(a + 28) for a in CHD}
OWN_PTD_NAME = {sname(P.dw(a + 28)) for a in CHD}

BCD = {}  # bcd address -> first pTD pointer seen (for stable reporting)
for a in CHD:
    n = P.dw(a + 8)
    pbca = P.dw(a + 12)
    if n is None or pbca is None:
        continue
    for j in range(min(n, 100000)):
        b = P.dw(pbca + 4 * j)
        if b is not None and b not in BCD:
            BCD[b] = P.dw(b + 0)

ZERO_BCD = [b for b in BCD if signed32(P.dw(b + 8)) == 0]
IN_OWN = [b for b in ZERO_BCD if BCD[b] in OWN_PTD_PTR]
NOT_OWN = [b for b in ZERO_BCD if sname(BCD[b]) not in OWN_PTD_NAME]

# ---------- Counter-control C1: random .rdata addresses ----------
# CHD blocks are 40-byte aligned; sample aligned 40-byte slots so the control
# matches the population being tested rather than arbitrary unaligned dwords.
rnd = random.Random(205)
rs = P.B['.rdata']
rlo = (rs['lo'] + 39) // 40 * 40
rhi = rs['lo'] + rs['rawsize'] - 4 - 36
NSLOT = (rhi - rlo) // 40 + 1
C1_hits = 0
C1_examples = []
for _ in range(5000):
    addr = rlo + 40 * rnd.randint(0, NSLOT - 1)
    if x4(addr):
        C1_hits += 1
        if len(C1_examples) < 5:
            C1_examples.append(addr)

# ---------- Counter-control C2: shifted criterion on the same CHD set ----------
C2_hits = sum(1 for a in sorted(CHD) if x4_shifted(a))

# ---------- Counter-control C3: names of the "not own" pTDs ----------
CLASS_NAMES = OWN_PTD_NAME
C3_rows = []
for b in sorted(NOT_OWN):
    ptd = BCD[b]
    nm = sname(ptd)
    C3_rows.append({'bcd': hex(b), 'pTD': hex(ptd), 'name': nm,
                    'name_in_class_set': nm in CLASS_NAMES})

RESULT = {
    'X1': len(COL),
    'X2': len(VFT),
    'X3': len(CHD),
    'X4': len(X4_hits),
    'X5': len(X5_hits),
    'X6': len(X6_hits),
    'X7': {str(k): dist[k] for k in sorted(dist)},
    'X8': {'mdisp_zero_total': len(ZERO_BCD),
           'ptd_in_own': len(IN_OWN),
           'ptd_not_in_own': len(NOT_OWN)},
}
with open(OUT + '/result.json', 'w', encoding='utf-8') as f:
    json.dump(RESULT, f, ensure_ascii=False, indent=2)
    f.write('\n')

# ---------- Evidence dump (single command output) ----------
def hx(v):
    return 'None' if v is None else hex(v)

print('=== SECTION TABLE ===')
for k, s in P.B.items():
    print('  %-8s lo=%08x rawsize=%08x vsize=%08x rawptr=%08x' %
          (k, s['lo'], s['rawsize'], s['vsize'], s['rawptr']))
print('file_size=%d' % len(P.RAW))

print('\n=== X1 COL sample (first 8) ===')
for a in sorted(COL)[:8]:
    c = COL[a]
    print('  %08x sig=%d mdisp=%d pMC=%s pTD=%s pCHD=%s %s' %
          (a, c['sig'], c['mdisp'], hx(c['pMC']), hx(c['pTD']), hx(c['pCHD']), c['name']))

print('\n=== X2 VFT sample (first 8) ===')
for v in sorted(VFT)[:8]:
    print('  %08x' % v)

print('\n=== X3 CHD sample (first 8) ===')
for a in sorted(CHD)[:8]:
    print('  %08x nBase=%s pBCA=%s pTD=%s(name=%s) ownCOL=%d' %
          (a, hx(P.dw(a + 8)), hx(P.dw(a + 12)), hx(P.dw(a + 28)),
           sname(P.dw(a + 28)), len(GROUPS[a])))

print('\n=== X4 failure breakdown (first 10) ===')
shown = 0
for a in sorted(CHD):
    if not x4(a):
        print('  %08x a16=%s a20=%s a24=%s a28=%s(%s) a32=%s' %
              (a, hx(P.dw(a + 16)), hx(P.dw(a + 20)), hx(P.dw(a + 24)),
               hx(P.dw(a + 28)), P.where(P.dw(a + 28)), hx(P.dw(a + 32))))
        shown += 1
        if shown >= 10:
            break
print('  total_fail=%d' % (len(CHD) - len(X4_hits)))

print('\n=== X5/X6 sample ===')
for a in X5_hits[:6]:
    print('  host=%08x embedCOL=%08x sig=%s mdisp=%s pMC=%s pTD=%s pCHD=%s(name=%s) host_match=%s' %
          (a, a + 16, hx(P.dw(a + 16)), hx(P.dw(a + 20)), hx(P.dw(a + 24)),
           hx(P.dw(a + 28)), hx(P.dw(a + 32)), sname(P.dw(a + 28)), P.dw(a + 32) == a))

print('\n=== X7 full distribution ===')
for k in sorted(dist):
    print('  zero_mdisp_count_per_group=%s -> groups=%d' % (k, dist[k]))
print('  groups_total=%d sum_cols=%d' % (len(GROUPS), sum(len(v) for v in GROUPS.values())))

print('\n=== X8 BCD stats ===')
print('  unique_BCD=%d zero_mdisp=%d in_own_ptr=%d not_own_name=%d ownPTD_ptr_unique=%d ownPTD_name_unique=%d' %
      (len(BCD), len(ZERO_BCD), len(IN_OWN), len(NOT_OWN), len(OWN_PTD_PTR), len(OWN_PTD_NAME)))
print('  not_own samples (first 12):')
for b in NOT_OWN[:12]:
    print('    bcd=%s pTD=%s name=%s in_class_set=%s' %
          (hx(b), hx(BCD[b]), sname(BCD[b]), sname(BCD[b]) in CLASS_NAMES))

print('\n=== C1 random .rdata control ===')
print('  range=[%08x,%08x] stride=40 slots=%d seed=205 trials=5000 hits=%d' %
      (rlo, rhi, NSLOT, C1_hits))
print('  hit examples: %s' % ', '.join(hx(x) for x in C1_examples))
print('\n=== C2 shifted control ===')
print('  hits=%d / %d CHD addresses' % (C2_hits, len(CHD)))
print('\n=== C3 not-own names (all %d) ===' % len(C3_rows))
for r in C3_rows:
    print('  bcd=%s pTD=%s name=%s in_954_class_set=%s' %
          (r['bcd'], r['pTD'], r['name'], r['name_in_class_set']))

print('\n=== RESULT.JSON ===')
print(json.dumps(RESULT, ensure_ascii=False, indent=2))
