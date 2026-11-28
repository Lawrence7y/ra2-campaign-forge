#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R213 EX1 -- independent MSVC RTTI closure recomputation from raw bytes.

All numbers are measured directly from ra2bench/gamemd.exe bytes via pe185's
PE mapping.  No disassembly is performed.  One run emits every A1..A11 item
and writes _r213/x1.json.
"""
import sys, struct, json, collections, hashlib, bisect
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P

ROOT = '/home/t628/projects/ra2-campaign-forge'
RAW  = P.RAW
SECS = P.SECS
B    = P.B
dw   = P.dw
cstr = P.cstr

def sec_of(va):
    for n, s in B.items():
        if s['lo'] <= va < s['hi_file']:
            return n
    return None
def in_sec(va, name):  return sec_of(va) == name
def is_data(va):       return in_sec(va, '.data')
def is_rdata(va):      return in_sec(va, '.rdata')
def is_text(va):       return in_sec(va, '.text')
def valid_name(b):     return b is not None and b.startswith(b'.?A') and b.endswith(b'@@')
def name_at(va):       return cstr(va, 512)

print("RAW sha256 =", hashlib.sha256(RAW).hexdigest())
print("RAW size   =", len(RAW))
print("=== SECTIONS ===")
for s in SECS:
    print("  %-10s VA[0x%08x,0x%08x) file[0x%x,0x%x) vsize=0x%x"
          % (s['name'], s['lo'], s['hi_file'], s['rawptr'], s['rawptr']+s['rawsize'], s['vsize']))

# ---------- A1: COL candidates ----------
rd = B['.rdata']; lo, hi = rd['lo'], rd['hi_file']
loose = []
for va in range(lo, hi & ~3, 4):
    sig = dw(va)
    if sig not in (0, 1, 2): continue
    if dw(va+8) != 0: continue
    ptd, pchd = dw(va+12), dw(va+16)
    if not is_data(ptd): continue
    if not is_rdata(pchd): continue
    if not valid_name(name_at(ptd+8)): continue
    loose.append({'C': va, 'sig': sig, 'mdisp': dw(va+4),
                  'pTD': ptd, 'pCHD': pchd, 'name': name_at(ptd+8)})
COLS = loose
colset = set(c['C'] for c in COLS)
A1 = len(COLS)
print("\n[A1] COL total = %d  %s (ref 1214)" % (A1, "PASS" if A1 == 1214 else "FAIL"))

# ---------- A2: predecessor sites ----------
pred = []
for secname in ('.rdata', '.data'):
    s = B[secname]
    for va in range(s['lo'], s['hi_file'] & ~3, 4):
        d = dw(va)
        if d in colset:
            nxt = dw(va+4)
            if nxt is not None and is_text(nxt):
                pred.append((va, d))
cnt = collections.Counter(c for v, c in pred)
A2_total = len(pred)
A2_each_one = sum(1 for C in colset if cnt[C] == 1)
A2_bijection = (A2_total == A1 and A2_each_one == A1 and len(cnt) == A1)
Vof = {c: v for v, c in pred}
print("[A2] pred sites = %d ; cols with exactly one pred = %d/%d ; bijection = %s  %s"
      % (A2_total, A2_each_one, A1, A2_bijection, "PASS" if A2_bijection else "FAIL"))

# ---------- A3: CHD / own ----------
chds = set(c['pCHD'] for c in COLS)
A3_chd = len(chds)
col_ranges = sorted((C, C+20) for C in colset)
def inside_col(va):
    i = bisect.bisect_right(col_ranges, (va, 1 << 30)) - 1
    return i >= 0 and col_ranges[i][0] <= va < col_ranges[i][1]
A3_own = sum(1 for c in COLS if inside_col(c['pCHD'] + 16))
A3_own_distinct = sum(1 for p in chds if inside_col(p + 16))
print("[A3] distinct pCHD = %d ; own (per-COL, pCHD+16 inside a COL) = %d ; "
      "distinct pCHD with own = %d  %s (ref pCHD 954)"
      % (A3_chd, A3_own, A3_own_distinct, "PASS" if A3_chd == 954 else "FAIL"))

# ---------- A4: pTD multiplicity ----------
ptdcnt = collections.Counter(c['pTD'] for c in COLS)
A4_distinct = len(ptdcnt)
multi = sorted([(p, n) for p, n in ptdcnt.items() if n >= 2], key=lambda x: (-x[1], x[0]))
A4_multi = len(multi)
A4_samples = [{'pTD': hex(p), 'count': n, 'name': cstr(p+8, 80).decode('latin1')}
              for p, n in multi[:8]]
print("[A4] distinct pTD = %d ; referenced >=2 = %d ; first8 = %s" % (A4_distinct, A4_multi, A4_samples))
print("     NOTE: the card's '260' matches the mdisp!=0 COL count, NOT distinct pTD (954).")

# ---------- A5: name equality ----------
name_at_ptd8_valid = sum(1 for c in COLS if valid_name(name_at(c['pTD']+8)))
name_at_ptd0_valid = sum(1 for c in COLS if valid_name(name_at(c['pTD'])))
both_valid = [(c['name'], name_at(c['pTD'])) for c in COLS
              if valid_name(name_at(c['pTD']+8)) and valid_name(name_at(c['pTD']))]
A5_equal = sum(1 for a, b in both_valid if a == b)
# additional name-location probes to make the ambiguous 'COL name' explicit
pvf_base = collections.Counter(dw(c['pTD']) for c in COLS)
A5_pVF_base_distinct = len(pvf_base)
A5_pVF_name_valid = 0; A5_pVF_name_equal = 0
for c in COLS:
    V = Vof.get(c['C'])
    if V is None: continue
    pvf = dw(V)
    b = name_at(pvf+8)
    if valid_name(b):
        A5_pVF_name_valid += 1
        if b == c['name']: A5_pVF_name_equal += 1
print("[A5] TD+8 names valid = %d/%d ; TD+0 names valid = %d/%d ; both-valid comparable = %d ; equal = %d"
      % (name_at_ptd8_valid, A1, name_at_ptd0_valid, A1, len(both_valid), A5_equal))
print("     pVFTable base at TD+0: distinct = %d (base %s) ; name at pVF+8 valid = %d ; equal to TD+8 = %d"
      % (A5_pVF_base_distinct, hex(pvf_base.most_common(1)[0][0]), A5_pVF_name_valid, A5_pVF_name_equal))

# ---------- A6 / A7: mdisp and TD+0 == COL+4 ----------
md0  = [c for c in COLS if c['mdisp'] == 0]
mdnz = [c for c in COLS if c['mdisp'] != 0]
A6_n = len(md0)
A6_match_C4 = sum(1 for c in md0 if dw(c['pTD']) == c['C'] + 4)
A6_match_V4 = sum(1 for c in md0
                  if Vof.get(c['C']) is not None and dw(c['pTD']) == Vof[c['C']] + 4)
A7_n = len(mdnz)
A7_dist = collections.Counter(c['mdisp'] for c in mdnz)
A7_match_C4 = sum(1 for c in mdnz if dw(c['pTD']) == c['C'] + 4)
A7_match_V4 = sum(1 for c in mdnz
                  if Vof.get(c['C']) is not None and dw(c['pTD']) == Vof[c['C']] + 4)
print("[A6] mdisp==0: %d ; TD+0==COLstruct+4: %d/%d ; TD+0==predecessor+4: %d/%d"
      % (A6_n, A6_match_C4, A6_n, A6_match_V4, A6_n))
print("[A7] mdisp!=0: %d ; TD+0==COLstruct+4: %d/%d ; TD+0==predecessor+4: %d/%d ; dist=%s"
      % (A7_n, A7_match_C4, A7_n, A7_match_V4, A7_n, dict(sorted(A7_dist.items()))))

# ---------- A8: vftable length ----------
def vftlen(base, cap=4096):
    n = 0; va = base
    while n < cap:
        d = dw(va)
        if d is None or not is_text(d): break
        n += 1; va += 4
    return n
lens_V4 = [vftlen(Vof[c['C']]+4) if c['C'] in Vof else None for c in COLS]
lens_C4 = [vftlen(c['C']+4) for c in COLS]
A8_dist_V4 = collections.Counter(lens_V4)
A8_total_V4 = sum(lens_V4)
A8_dist_C4 = collections.Counter(lens_C4)
A8_total_C4 = sum(lens_C4)
A8_firstsec = collections.Counter(sec_of(dw(Vof[c['C']]+4))
                                  for c in COLS if c['C'] in Vof)
print("[A8] from predecessor+4: dist=%s total=%d first-slot sections=%s"
      % (dict(sorted(A8_dist_V4.items())), A8_total_V4, dict(A8_firstsec)))
print("     from COLstruct+4: dist=%s total=%d" % (dict(sorted(A8_dist_C4.items())), A8_total_C4))

# ---------- A9 / A10 / A11: controls ----------
a9 = 0
for va in range(lo, hi & ~3, 4):
    if dw(va) not in (0, 1, 2): continue
    ptd, pchd = dw(va+12), dw(va+16)
    if not is_data(ptd): continue
    if not is_rdata(pchd): continue
    if valid_name(name_at(ptd+8)): a9 += 1
print("[A9] without +8==0 constraint = %d" % a9)

def prefix_count(pref):
    return sum(1 for c in loose
               if (lambda b: b is not None and b.startswith(pref) and b.endswith(b'@@'))(name_at(c['pTD']+8)))
A10_AV = prefix_count(b'.?AV')
A10_A  = prefix_count(b'.?A')
A10_AU = prefix_count(b'.?AU')
print("[A10] prefix .?AV=%d .?A=%d .?AU=%d (relaxed .?A=%d)" % (A10_AV, A10_A, A10_AU, A10_A))

a11 = 0
for va in range(lo, hi & ~3, 4):
    if dw(va) not in (0, 1, 2): continue
    if dw(va+8) != 0: continue
    ptd, pchd = dw(va+12), dw(va+16)
    if not is_rdata(pchd): continue
    if valid_name(name_at(ptd+8)): a11 += 1
print("[A11] without '+12 in .data' constraint = %d" % a11)

res = {
 'meta': {'raw_sha256': hashlib.sha256(RAW).hexdigest(), 'raw_size': len(RAW),
          'imagebase': hex(P.IB), 'sections': [s['name'] for s in SECS],
          'name_rule': 'COL+12=pTD; TD name at pTD+8 (.?A...@@); '
                       'predecessor V holds pointer to COL, vftable starts at V+4'},
 'A1': {'value': A1, 'ref': 1214, 'pass': A1 == 1214},
 'A2': {'pred_sites': A2_total, 'cols_with_exactly_one': A2_each_one, 'total_cols': A1,
        'bijection': A2_bijection, 'pass': A2_bijection},
 'A3': {'distinct_pCHD': A3_chd, 'own_per_COL': A3_own,
        'distinct_pCHD_with_own': A3_own_distinct, 'ref_pCHD': 954, 'pass': A3_chd == 954},
 'A4': {'distinct_pTD': A4_distinct, 'multi_ge2': A4_multi, 'samples': A4_samples,
        'card_ref': 260, 'note': '260 equals the mdisp!=0 COL count, not distinct pTD'},
 'A5': {'TD8_names_valid': name_at_ptd8_valid, 'total': A1,
        'TD0_names_valid': name_at_ptd0_valid, 'both_valid': len(both_valid), 'equal': A5_equal,
        'pVFTable_base_distinct': A5_pVF_base_distinct,
        'pVFTable_base': hex(pvf_base.most_common(1)[0][0]),
        'pVF8_names_valid': A5_pVF_name_valid, 'pVF8_equal_TD8': A5_pVF_name_equal,
        'note': 'No separate COL name field exists; both candidate name sites (TD+0, pVF+8) '
                'never hold a .?A name, so no equality pair is comparable'},
 'A6': {'mdisp0': A6_n, 'TD0_eq_COLstruct4': A6_match_C4,
        'TD0_eq_predecessor4': A6_match_V4},
 'A7': {'mdisp_nonzero': A7_n,
        'TD0_eq_COLstruct4': A7_match_C4, 'TD0_eq_predecessor4': A7_match_V4,
        'distribution': {str(k): v for k, v in sorted(A7_dist.items())}},
 'A8': {'vft_len_dist_from_pred4': {str(k): v for k, v in sorted(A8_dist_V4.items())},
        'total_slots_from_pred4': A8_total_V4, 'first_slot_sections': dict(A8_firstsec),
        'vft_len_dist_from_COLstruct4': {str(k): v for k, v in sorted(A8_dist_C4.items())},
        'total_slots_from_COLstruct4': A8_total_C4},
 'A9': {'value': a9},
 'A10': {'.?AV': A10_AV, '.?A': A10_A, '.?AU': A10_AU, 'relaxed': A10_A},
 'A11': {'value': a11},
}
with open(ROOT+'/_r213/x1.json', 'w') as f:
    json.dump(res, f, indent=2, ensure_ascii=False)
print("\nJSON written to _r213/x1.json")
