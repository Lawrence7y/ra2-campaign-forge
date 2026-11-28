#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R214-EX1 -- slot +0x48 (index 18) forwarding-surface forensics.

Single-shot, byte-level reconstruction of MSVC RTTI COL/predecessor/vftable
tables from gamemd.exe (reusing _r185/pe185.py), then E1..E5 measurements.

No whole-.text detail disassembly: only capstone small windows (count=1)
on rel32-prefiltered candidate direct call/jmp sites in E4.
"""
import sys, os, json, struct, hashlib, collections, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, ROOT + '/_r185')
import pe185 as P

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_INS_CALL, X86_INS_JMP

T0 = time.time()
RAW = P.RAW
CHECKS = []


def check(name, ok, detail=''):
    CHECKS.append({'name': name, 'pass': bool(ok), 'detail': detail})
    print('[%s] %s%s' % ('PASS' if ok else 'FAIL', name,
                         (' :: ' + detail) if detail else ''))


def h(v):
    return 'None' if v is None else ('0x%08x' % v)


sha = hashlib.sha256(RAW).hexdigest()
print('=== META ===')
print('RAW sha256 = %s' % sha)
print('RAW size   = %d' % len(RAW))
for s in P.SECS:
    print('  %-10s VA[0x%08x,0x%08x) rawptr=0x%x rawsize=0x%x'
          % (s['name'], s['lo'], s['hi_file'], s['rawptr'], s['rawsize']))

# ------------------------------------------------------------------
# Table reconstruction (exact R213 judging criteria, no changes)
# ------------------------------------------------------------------
def valid_name(b):
    return b is not None and b.startswith(b'.?A') and b.endswith(b'@@')


# COL: scan .rdata AND .data; w[k] in (0,1,2), w[k+2]==0,
# where(w[k+3])=='.data', where(w[k+4])=='.rdata', TD+8 name valid.
col_by_sec = collections.Counter()
cols = []
for secname in ('.rdata', '.data'):
    s = P.B[secname]
    for va in range(s['lo'], s['hi_file'] & ~3, 4):
        if P.dw(va) not in (0, 1, 2):
            continue
        if P.dw(va + 8) != 0:
            continue
        ptd, pchd = P.dw(va + 12), P.dw(va + 16)
        if P.where(ptd) != '.data' or P.where(pchd) != '.rdata':
            continue
        nb = P.cstr(ptd + 8)
        if not valid_name(nb):
            continue
        nm = nb[1:].decode('latin1')  # strip leading dot: .?AVXxx@@ -> ?AVXxx@@
        cols.append({'C': va, 'sig': P.dw(va), 'mdisp': P.dw(va + 4),
                     'pTD': ptd, 'pCHD': pchd, 'name': nm})
        col_by_sec[secname] += 1

colset = set(c['C'] for c in cols)
cols.sort(key=lambda c: c['C'])

# predecessor sites: w[k] in COL and where(w[k+1])=='.text'
pred = {}
pred_sites = 0
for secname in ('.rdata', '.data'):
    s = P.B[secname]
    for va in range(s['lo'], s['hi_file'] & ~3, 4):
        d = P.dw(va)
        if d in colset and P.where(P.dw(va + 4)) == '.text':
            pred[d] = va
            pred_sites += 1

# views: vftable starts at predecessor+4, slot i at base+4*i,
# length = consecutive dwords whose value lands in .text
views = []
for c in cols:
    V = pred.get(c['C'])
    base = V + 4 if V is not None else None
    slots = []
    if base is not None:
        va = base
        while len(slots) < 4096:
            d = P.dw(va)
            if d is None or P.where(d) != '.text':
                break
            slots.append(d)
            va += 4
    views.append({'C': c['C'], 'V': V, 'base': base, 'pCHD': c['pCHD'],
                  'mdisp': c['mdisp'], 'name': c['name'], 'n': len(slots),
                  'slots': slots})

by_chd = collections.defaultdict(list)
for v in views:
    by_chd[v['pCHD']].append(v)
primary, secondary = [], []
one_primary_per_chd = True
for chd, grp in by_chd.items():
    p = [v for v in grp if v['mdisp'] == 0]
    if len(p) != 1:
        one_primary_per_chd = False
    if p:
        primary.append(p[0])
    secondary.extend(v for v in grp if v['mdisp'] != 0)
primary.sort(key=lambda v: v['C'])
secondary.sort(key=lambda v: v['C'])

ncol = len(cols)
nchd = len(by_chd)
nslot = sum(v['n'] for v in views)

print('\n=== TABLE SIZES ===')
print('COL      = %d  (.rdata=%d, .data=%d)' % (ncol, col_by_sec['.rdata'], col_by_sec['.data']))
print('pred     = %d' % pred_sites)
print('CHD      = %d' % nchd)
print('primary  = %d' % len(primary))
print('secondary= %d' % len(secondary))
print('slot tot = %d' % nslot)
check('COL count == 1214 (R213 ref)', ncol == 1214, str(ncol))
check('predecessor bijection', pred_sites == ncol and len(pred) == ncol,
      'pred_sites=%d distinct=%d' % (pred_sites, len(pred)))
check('CHD count == 954 (R213 ref)', nchd == 954, str(nchd))
check('primary == 954 / secondary == 260', len(primary) == 954 and len(secondary) == 260,
      '%d/%d' % (len(primary), len(secondary)))
check('exactly one mdisp==0 COL per pCHD', one_primary_per_chd)
check('total slots == 14044 (R213 ref)', nslot == 14044, str(nslot))

# ------------------------------------------------------------------
# E1: view slot counts and slot18 coverage
# ------------------------------------------------------------------
IDX = 18
print('\n=== E1: view slot counts / slot18 coverage ===')


def dist_str(counter):
    return '{' + ', '.join('%d:%d' % (k, v) for k, v in sorted(counter.items())) + '}'


for label, group in (('primary', primary), ('secondary', secondary), ('all', views)):
    dc = collections.Counter(v['n'] for v in group)
    gt = sum(1 for v in group if v['n'] > IDX)
    le = len(group) - gt
    print('%-9s views=%d  ndist=%s  n>18=%d  n<=18=%d'
          % (label, len(group), dist_str(dc), gt, le))

gt_all = [v for v in views if v['n'] > IDX]
check('n>18 + n<=18 == total views',
      len(gt_all) + sum(1 for v in views if v['n'] <= IDX) == ncol)
check('slot18 view set size == count(n>18)', len(gt_all) == len(set(v['C'] for v in gt_all)))

E1 = {
    'primary_views': len(primary), 'secondary_views': len(secondary),
    'primary_slotlen_dist': {str(k): v for k, v in sorted(collections.Counter(v['n'] for v in primary).items())},
    'secondary_slotlen_dist': {str(k): v for k, v in sorted(collections.Counter(v['n'] for v in secondary).items())},
    'all_slotlen_dist': {str(k): v for k, v in sorted(collections.Counter(v['n'] for v in views).items())},
    'primary_n_gt18': sum(1 for v in primary if v['n'] > IDX),
    'primary_n_le18': sum(1 for v in primary if v['n'] <= IDX),
    'secondary_n_gt18': sum(1 for v in secondary if v['n'] > IDX),
    'secondary_n_le18': sum(1 for v in secondary if v['n'] <= IDX),
    'all_n_gt18': len(gt_all), 'all_n_le18': ncol - len(gt_all),
    'slot18_view_set_size': len(set(v['C'] for v in gt_all)),
}

# ------------------------------------------------------------------
# E2: slot18 landing-point distribution (positive + negative controls)
# ------------------------------------------------------------------
print('\n=== E2: slot18 landing points ===')


def slot_stats(idx):
    grp = [v for v in views if v['n'] > idx]
    vals = [v['slots'][idx] for v in grp]
    cnt = collections.Counter(vals)
    where_cnt = collections.Counter(P.where(x) for x in vals)
    return {
        'views': len(grp), 'total': len(vals), 'distinct': len(cnt),
        'top10': [{'addr': h(a), 'count': n, 'where': P.where(a)} for a, n in cnt.most_common(10)],
        'top3': [{'addr': h(a), 'count': n} for a, n in cnt.most_common(3)],
        'where': dict(where_cnt),
        'text_ratio': (where_cnt.get('.text', 0) / len(vals)) if vals else None,
        'bad_virt_only': where_cnt.get('virt-only', 0),
        'bad_other': where_cnt.get('other', 0) + where_cnt.get('None', 0),
    }


s18 = slot_stats(IDX)
print('views with slot18 = %d ; distinct landing points = %d'
      % (s18['views'], s18['distinct']))
print('top10 = %s' % json.dumps(s18['top10'], ensure_ascii=False))
print('where = %s ; text_ratio = %s'
      % (json.dumps(s18['where']), s18['text_ratio']))
check('slot18 distinct > 1 (non-trivial)', s18['distinct'] > 1, str(s18['distinct']))
check('slot18 landings all in .text (positive control)', s18['text_ratio'] == 1.0,
      'ratio=%s' % s18['text_ratio'])
check('slot18 virt-only count == 0 (negative control)', s18['bad_virt_only'] == 0)
check('slot18 other/None count == 0 (negative control)', s18['bad_other'] == 0)

# ------------------------------------------------------------------
# E3: MouseClass / TabClass / ScrollClass primary views
# ------------------------------------------------------------------
print('\n=== E3: MouseClass / TabClass / ScrollClass ===')
CLASSES = ['MouseClass', 'TabClass', 'ScrollClass', 'HouseClass']
E3 = {'note':
      'The card self-check slot0==0x6d1770 does NOT apply to primary (mdisp==0) '
      'views: at mdisp==0 the vftable base is this+0x00, so this+0x48 is slot18 '
      'and slot0 is 0x004f4240. 0x006d1770 is slot0 of the mdisp==21784 SECONDARY '
      'view, whose vftable base is this+0x40, so this+0x48 is slot1 there. '
      'Both views are reported below; slot0==0x6d1770 is checked on secondary.'}
for cls in CLASSES:
    want = '?AV%s@@' % cls
    hits = [v for v in views if v['name'] == want]
    prim = [v for v in hits if v['mdisp'] == 0]
    # secondary view with mdisp==21784 (S3 from R213): its vftable base is at
    # this+0x40; therefore this+0x48 is slot1 there.  Its slot0 is 0x6d1770.
    disp_s3 = [v for v in hits if v['mdisp'] == 21784]
    rec = {'name': want, 'all_cols': len(hits), 'primary_cols': len(prim),
           'disp21784_cols': len(disp_s3),
           'primary_bases': [h(v['base']) for v in prim],
           'slot_counts': [v['n'] for v in prim]}

    def slotval(v, i):
        return h(v['slots'][i]) if v['n'] > i else None

    if prim:
        v = prim[0]
        rec['primary'] = {'base': h(v['base']), 'mdisp': v['mdisp'], 'n': v['n'],
                          'slot0': slotval(v, 0), 'slot18': slotval(v, 18)}
        print('%-12s PRIMARY   base=%s mdisp=%d n=%s slot0=%s slot18=%s (cols=%d)'
              % (cls, rec['primary']['base'], v['mdisp'], v['n'],
                 rec['primary']['slot0'], rec['primary']['slot18'], len(hits)))
        check('%s has exactly one primary COL' % cls, len(prim) == 1)
    else:
        print('%-12s PRIMARY NOT FOUND (cols=%d)' % (cls, len(hits)))
        check('%s primary COL found' % cls, False)

    if disp_s3:
        v = disp_s3[0]
        rec['secondary_mdisp21784'] = {'base': h(v['base']), 'mdisp': v['mdisp'],
                                       'n': v['n'], 'slot0': slotval(v, 0),
                                       'slot1': slotval(v, 1)}
        print('%-12s M21784    base=%s mdisp=%d n=%s slot0=%s slot1(this+0x48)=%s'
              % (cls, rec['secondary_mdisp21784']['base'], v['mdisp'], v['n'],
                 rec['secondary_mdisp21784']['slot0'], rec['secondary_mdisp21784']['slot1']))
        check('%s mdisp21784 slot0 == 0x006d1770 (caliber self-check)' % cls,
              slotval(v, 0) == '0x006d1770', str(slotval(v, 0)))
    elif cls in CLASSES[:3]:
        print('%-12s M21784 NOT FOUND' % cls)
        check('%s secondary mdisp==21784 COL found' % cls, False)
    E3[cls] = rec

s18_three = [E3[c].get('primary', {}).get('slot18') for c in CLASSES[:3]]
same3 = len(set(s18_three)) == 1 and s18_three[0] is not None
E3['three_primary_slot18_same'] = same3
E3['three_primary_slot18_values'] = s18_three
print('three classes PRIMARY slot18 same address = %s (%s)' % (same3, s18_three))

# ------------------------------------------------------------------
# E4: direct call/jmp references to 0x723ea0 / 0x723eb0
# ------------------------------------------------------------------
print('\n=== E4: references to 0x723ea0 / 0x723eb0 ===')
TARGETS = {0x723ea0, 0x723eb0}
t = P.B['.text']
lo, ro, rs = t['lo'], t['rawptr'], t['rawsize']
blob = RAW[ro:ro + rs]

# rel32 prefilter over every byte offset (x86 instructions are unaligned)
cand = []
for op in (0xe8, 0xe9):
    ob = bytes([op])
    pos = 0
    while True:
        i = blob.find(ob, pos)
        if i < 0 or i + 5 > len(blob):
            break
        pos = i + 1
        rel = struct.unpack_from('<i', blob, i + 1)[0]
        addr = lo + i
        target = addr + 5 + rel
        if target in TARGETS:
            cand.append({'addr': addr, 'op': op, 'rel': rel, 'target': target})
print('e8/e9 rel32 prefilter hits = %d' % len(cand))

# capstone small-window operand verification on hits ONLY (count=1)
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
verified = []
decode_fail = []
for c in cand:
    o = P.r2o(c['addr'])
    code = RAW[o:o + 16]
    ins = next(md.disasm(code, c['addr'], count=1), None)
    ok = False
    if ins is not None:
        want_id = X86_INS_CALL if c['op'] == 0xe8 else X86_INS_JMP
        ok = (ins.id == want_id and ins.size == 5 and len(ins.operands) == 1
              and ins.operands[0].type == X86_OP_IMM
              and ins.operands[0].imm == c['target'])
    if ok:
        c['mnemonic'] = ins.mnemonic
        c['op_str'] = ins.op_str
        verified.append(c)
    else:
        decode_fail.append({'addr': h(c['addr']), 'op': h(c['op']),
                            'ins': (ins.mnemonic + ' ' + ins.op_str) if ins else None})
print('capstone-verified direct call/jmp sites = %d' % len(verified))
for v in sorted(verified, key=lambda x: x['addr']):
    print('  site=%s  %-4s %-12s -> %s (rel=%d)'
          % (h(v['addr']), v['mnemonic'], v['op_str'], h(v['target']), v['rel']))
check('all prefilter hits decoded by capstone', len(decode_fail) == 0,
      'decode_fail=%d' % len(decode_fail))
check('verified targets subset of {0x723ea0,0x723eb0}',
      all(v['target'] in TARGETS for v in verified))
print('ff /2 (call r/m32) and ff /4 (jmp r/m32) indirect forms: '
      'excluded by construction (no immediate target; not counted)')

# vftable slot value occurrence across ALL 14044 slots
allslot_vals = [d for v in views for d in v['slots']]
slot_hits = [{'view_C': h(v['C']), 'slot': i, 'value': h(d), 'class': v['name']}
             for v in views for i, d in enumerate(v['slots']) if d in TARGETS]
print('vftable slot occurrences of targets (over %d slots) = %d'
      % (len(allslot_vals), len(slot_hits)))
for x in slot_hits[:20]:
    print('  %s' % json.dumps(x, ensure_ascii=False))
check('no vftable slot holds 0x723ea0/0x723eb0', len(slot_hits) == 0,
      'hits=%d' % len(slot_hits))

# ------------------------------------------------------------------
# E5: negative control with slot index 17 and 19
# ------------------------------------------------------------------
print('\n=== E5: control slots 17 / 19 ===')
E5 = {}
for idx in (17, 19):
    s = slot_stats(idx)
    print('slot%-2d views=%d distinct=%d top3=%s where=%s'
          % (idx, s['views'], s['distinct'],
             json.dumps(s['top3'], ensure_ascii=False), json.dumps(s['where'])))
    E5['slot%d' % idx] = s
    check('slot%d landings all in .text' % idx, s['text_ratio'] == 1.0,
          'ratio=%s' % s['text_ratio'])

nontrivial = (E5['slot17']['distinct'] != s18['distinct']
              or E5['slot19']['distinct'] != s18['distinct'])
check('slot18 distinct differs from slot17/19 (non-trivial)', nontrivial,
      'd17=%d d18=%d d19=%d' % (E5['slot17']['distinct'], s18['distinct'],
                                 E5['slot19']['distinct']))

# ------------------------------------------------------------------
# JSON + summary
# ------------------------------------------------------------------
np = sum(1 for c in CHECKS if c['pass'])
nf = len(CHECKS) - np
print('\n=== SUMMARY ===')
print('PASS=%d FAIL=%d elapsed=%.2fs' % (np, nf, time.time() - T0))

res = {
    'meta': {
        'task': 'R214-EX1 slot +0x48 (index 18) forwarding surface',
        'raw_sha256': sha, 'raw_size': len(RAW), 'imagebase': h(P.IB),
        'sections': [s['name'] for s in P.SECS],
        'judging': 'same COL / predecessor / vftable criteria as R213 x1.py; '
                   'scan .rdata AND .data for COL and predecessor sites',
        'elapsed_sec': round(time.time() - T0, 3),
    },
    'tables': {
        'COL': ncol, 'COL_by_section': dict(col_by_sec), 'pred_sites': pred_sites,
        'CHD': nchd, 'primary': len(primary), 'secondary': len(secondary),
        'total_slots': nslot,
    },
    'E1': E1,
    'E2': s18,
    'E3': E3,
    'E4': {
        'targets': [h(x) for x in sorted(TARGETS)],
        'prefilter_hits': len(cand),
        'verified_sites': [{'site': h(v['addr']), 'mnemonic': v['mnemonic'],
                            'op_str': v['op_str'], 'target': h(v['target']),
                            'rel': v['rel']}
                           for v in sorted(verified, key=lambda x: x['addr'])],
        'decode_fail': decode_fail,
        'indirect_ff_2_4_excluded': True,
        'slots_scanned': len(allslot_vals),
        'vftable_slot_hits': slot_hits,
    },
    'E5': E5,
    'checks': {'pass': np, 'fail': nf, 'items': CHECKS},
}
with open(ROOT + '/_r214/ex1.json', 'w') as f:
    json.dump(res, f, indent=2, ensure_ascii=False)
print('JSON written to _r214/ex1.json')
