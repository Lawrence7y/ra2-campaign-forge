#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R193 exec: complete function-boundary analysis of the 103 R192 inc pairs.

Read-only against ra2bench/gamemd.exe. Writes only _r193/exec/r193_fnbound.json.
All disassembly is per-target with a <=512-byte window and capstone detail=False.
"""
import sys, os, struct, json, hashlib, collections
ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, ROOT + '/_r185')
import pe185 as P
import capstone

EXE = ROOT + '/ra2bench/gamemd.exe'
OUT = ROOT + '/_r193/exec/r193_fnbound.json'
EXE_SHA = hashlib.sha256(open(EXE, 'rb').read()).hexdigest()

T = P.B['.text']
LO, HI = T['lo'], T['hi_file']
def in_text(x):
    return x is not None and LO <= x < HI

def wv(sn):
    s = P.B[sn]
    n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n

# ---- S1: R192-effective COL/VT/slot enumeration (mdisp = dword[1]) ----
COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1) or w[i + 2] != 0:
            continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata':
            continue
        nm = P.cstr(w[i + 3] + 8, 200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')):
            continue
        COL[base + 4 * i] = {'mdisp': w[i + 1], 'pTD': w[i + 3],
                             'pCHD': w[i + 4], 'name': nm.decode('latin1')}

VT = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(1, n):
        if in_text(w[i]) and w[i - 1] in COL:
            VT[base + 4 * i] = w[i - 1]

def nslot(vt):
    k = 0
    while in_text(P.dw(vt + 4 * k)):
        k += 1
    return k

NS = {vt: nslot(vt) for vt in VT}
group = collections.defaultdict(list)
for vt in sorted(VT):
    group[COL[VT[vt]]['name']].append(vt)

# R192's effective thunk removal: MSVC adjustor thunk shape only.  This is the
# predicate that reproduces the five check numbers; see thunk_difference below.
def is_adj(va):
    o = P.r2o(va)
    if o is None:
        return False
    z = P.RAW[o:o + 4]
    return (z[:3] in (b'\x83\x6c\x24', b'\x81\x6c\x24') and z[3] == 4)

direct = []
for vt in sorted(VT):
    if COL[VT[vt]]['mdisp'] == 0:
        continue
    for k in range(NS[vt]):
        v = P.dw(vt + 4 * k)
        if in_text(v) and not is_adj(v):
            direct.append((vt, k, v))

cat_counts = collections.Counter()
pairs = []
for vt, k, v in direct:
    sibs = [t for t in group[COL[VT[vt]]['name']]
            if t != vt and k < NS[t]]
    if not sibs:
        cat_counts['NOSIB'] += 1
        continue
    t = sibs[0]
    w = P.dw(t + 4 * k)
    if w == v:
        cat_counts['SAME'] += 1
        continue
    # R192 A3 pairs every sibling with a different slot value, including the
    # 10 adjustor siblings.  The class tag is recorded for reporting, but the
    # pair is retained so all five R192 baseline numbers reproduce exactly.
    if in_text(w) and is_adj(w):
        cat_counts['THUNK_OTHER'] += 1
    else:
        cat_counts['DIRECT_OTHER'] += 1
    pairs.append({'vt': hex(vt), 'col': hex(VT[vt]), 'k': k,
                  'left': hex(v), 'sib_vt': hex(t), 'right': hex(w),
                  'name': COL[VT[vt]]['name'],
                  'sibling_is_adjustor': is_adj(w)})

FIVE_EXPECT = [535, 1013, 478, 525, 10]
five = [len(pairs), len(direct), cat_counts['NOSIB'],
        cat_counts['DIRECT_OTHER'], cat_counts['THUNK_OTHER']]

# Diagnostic: the literal thunk wording on the card (E9/EB/FF25 head, or
# single-reference target whose first instruction is <=8 bytes) does NOT
# reproduce the R192 baseline.  Recorded here explicitly, not substituted.
md0 = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md0.detail = False
slot_refs = collections.Counter()
for vt in VT:
    for k in range(NS[vt]):
        slot_refs[P.dw(vt + 4 * k)] += 1

def card_text_thunk(va):
    o = P.r2o(va)
    if o is None:
        return False
    z = P.RAW[o:o + 8]
    if z[0] == 0xE9 or z[0] == 0xEB or z[:2] == b'\xff\x25':
        return True
    if slot_refs[va] <= 1:
        for ins in md0.disasm(P.RAW[o:o + 16], va):
            return ins.size <= 8
    return False

card_direct = [(vt, k, P.dw(vt + 4 * k)) for vt in sorted(VT)
               if COL[VT[vt]]['mdisp'] != 0 for k in range(NS[vt])
               if in_text(P.dw(vt + 4 * k))
               and not card_text_thunk(P.dw(vt + 4 * k))]
card_pairs = 0
card_cat = collections.Counter()
for vt, k, v in card_direct:
    sibs = [t for t in group[COL[VT[vt]]['name']]
            if t != vt and k < NS[t]]
    if not sibs:
        card_cat['NOSIB'] += 1
        continue
    w = P.dw(sibs[0] + 4 * k)
    if w == v:
        card_cat['SAME'] += 1
    elif card_text_thunk(w):
        card_cat['THUNK_OTHER'] += 1
    else:
        card_cat['DIRECT_OTHER'] += 1
        card_pairs += 1

THUNK_DIFF = {
    'used_for_baseline': ('R192 effective predicate: exclude only dword[0:3] in '
                          '{83 6c 24, 81 6c 24} with dword[3]==04 (adjustor thunk)'),
    'card_literal_probe': {
        'predicate': ('head E9/EB/FF25, or slot_refs<=1 and first-insn size<=8'),
        'five_numbers': [card_pairs, len(card_direct), card_cat['NOSIB'],
                         card_cat['DIRECT_OTHER'], card_cat['THUNK_OTHER']],
        'note': ('literal card wording does not reproduce 535/1013/478/525/10; '
                 'R192-effective predicate does, so it is used for S1 and reported.')
    }
}

if five != FIVE_EXPECT:
    out = {'meta': {'binary': EXE, 'sha256': EXE_SHA, 'card': 'R193'},
           's1': {'five_numbers': five, 'expected': FIVE_EXPECT,
                  'cat_counts': dict(cat_counts), 'thunk_difference': THUNK_DIFF},
           'aborted': 'S1 five-number self-test failed; no further measurement'}
    with open(OUT, 'w') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('S1 SELF-TEST FAIL five=', five, 'expected=', FIVE_EXPECT)
    print('SUMMARY pairs=%d inc=0 both_ret=0 both_not=0' % len(pairs))
    sys.exit(2)

# ---- R192 inc filter: 96-byte window, stop at jmp/int3/hlt (verbatim r192b) ----
def retn96(va, budget=96):
    o = P.r2o(va)
    if o is None:
        return 'unmapped'
    for ins in md0.disasm(P.RAW[o:o + budget], va):
        if ins.mnemonic == 'ret':
            return int(ins.op_str, 16) if ins.op_str else 0
        if ins.mnemonic in ('jmp', 'int3', 'hlt') and ins.address > va:
            return 'jmp/other'
    return 'noret96b'

inc_pairs = []
for p in pairs:
    r1 = retn96(int(p['left'], 16))
    r2 = retn96(int(p['right'], 16))
    if not (isinstance(r1, int) and isinstance(r2, int)):
        q = dict(p)
        q['r192_ret_left'] = r1
        q['r192_ret_right'] = r2
        inc_pairs.append(q)

if len(inc_pairs) != 103:
    out = {'meta': {'binary': EXE, 'sha256': EXE_SHA, 'card': 'R193'},
           's1': {'five_numbers': five, 'expected': FIVE_EXPECT,
                  'cat_counts': dict(cat_counts), 'thunk_difference': THUNK_DIFF},
           's2_precheck': {'inc_count': len(inc_pairs), 'expected': 103},
           'aborted': 'R192 96-byte inc filter did not reproduce 103'}
    with open(OUT, 'w') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('INC SELF-TEST FAIL inc=', len(inc_pairs), 'expected=103')
    print('SUMMARY pairs=%d inc=%d both_ret=0 both_not=0' % (len(pairs), len(inc_pairs)))
    sys.exit(3)

# ---- S2: full function-boundary analysis, <=512 bytes per target ----
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = False
WINDOW = 512

def full_boundary(va, window=WINDOW):
    o = P.r2o(va)
    if o is None:
        return {'category': 'WINDOW_OUT', 'boundary_va': None, 'offset': None,
                'boundary_bytes': None, 'insn_count': 0, 'reason': 'unmapped'}
    code = P.RAW[o:o + window]
    n = len(code)
    off = 0
    count = 0

    def pad_run(pos):
        if pos + 1 < n and code[pos] in (0x90, 0xCC) and code[pos] == code[pos + 1]:
            b = code[pos]
            j = pos
            while j < n and code[j] == b:
                j += 1
            return ('PAD_NOP' if b == 0x90 else 'PAD_CC', va + pos, j - pos)
        return None

    for ins in md.disasm(code, va):
        pos = ins.address - va
        if pos < 0 or pos >= n:
            break
        # Capstone may skip invalid bytes; never skip a possible padding run.
        for q in range(off, pos):
            pd = pad_run(q)
            if pd:
                return {'category': pd[0], 'boundary_va': hex(pd[1]),
                        'offset': pd[1] - va, 'boundary_bytes': None,
                        'insn_count': count, 'pad_len': pd[2]}
        pd = pad_run(pos)
        if pd:
            return {'category': pd[0], 'boundary_va': hex(pd[1]),
                    'offset': pd[1] - va, 'boundary_bytes': None,
                    'insn_count': count, 'pad_len': pd[2]}
        count += 1
        if ins.mnemonic in ('int3', 'hlt'):
            return {'category': 'PAD_CC', 'boundary_va': hex(ins.address),
                    'offset': ins.address - va, 'boundary_bytes': ins.bytes.hex(),
                    'insn_count': count, 'mnemonic': ins.mnemonic,
                    'text': (ins.mnemonic + ' ' + ins.op_str).strip()}
        if ins.mnemonic.startswith('ret'):
            return {'category': 'HAS_RET', 'boundary_va': hex(ins.address),
                    'offset': ins.address - va, 'boundary_bytes': ins.bytes.hex(),
                    'insn_count': count, 'mnemonic': ins.mnemonic,
                    'text': (ins.mnemonic + ' ' + ins.op_str).strip()}
        off = pos + ins.size
    for q in range(off, max(off, n - 1)):
        pd = pad_run(q)
        if pd:
            return {'category': pd[0], 'boundary_va': hex(pd[1]),
                    'offset': pd[1] - va, 'boundary_bytes': None,
                    'insn_count': count, 'pad_len': pd[2]}
    return {'category': 'WINDOW_OUT', 'boundary_va': None, 'offset': n,
            'boundary_bytes': None, 'insn_count': count,
            'reason': 'linear disassembly exhausted 512-byte window'}

def probes(va, n=16):
    o = P.r2o(va)
    return {'where': P.where(va), 'hex': None if o is None else P.RAW[o:o + n].hex()}

# ---- required controls ----
C1 = full_boundary(0x410450)
C2 = full_boundary(0x4C9150)
C3 = full_boundary(0x41045F)
controls = {
    'C1': {'input': hex(0x410450),
           'expected': {'category': 'HAS_RET', 'boundary_va': hex(0x41045E),
                        'offset': 14, 'body_hex': '8b4c240433c08a512084d20f94c0c20400'},
           'actual': C1, 'body_hex16': probes(0x410450, 16)['hex'],
           'pass': (C1['category'] == 'HAS_RET' and C1['boundary_va'] == hex(0x41045E)
                    and C1['boundary_bytes'] == 'c20400'
                    and probes(0x410450, 16)['hex'] ==
                    '8b4c240433c08a512084d20f94c0c204')},
    'C2': {'input': hex(0x4C9150),
           'expected': {'category': 'HAS_RET', 'boundary_va': hex(0x4C9152)},
           'actual': C2,
           'pass': (C2['category'] == 'HAS_RET'
                    and C2['boundary_va'] == hex(0x4C9152))},
    'C3': {'input': hex(0x41045F),
           'expected': {'category_in': ['PAD_NOP', 'PAD_CC'], 'non_HAS_RET': True},
           'actual': C3,
           'pass': (C3['category'] in ('PAD_NOP', 'PAD_CC'))},
    'C4': {'expected': [535, 1013], 'actual': five,
           'pass': five == FIVE_EXPECT},
}

# ---- S3/S4: run every inc pair, classify, sample both-non-HAS_RET ----
table = [[0, 0], [0, 0]]  # rows: left HAS_RET / not; cols: right HAS_RET / not
table_full = collections.Counter()
both_ret = 0
any_not = 0
both_not = 0
both_not_rows = []
detail_rows = []
for p in inc_pairs:
    L = full_boundary(int(p['left'], 16))
    R = full_boundary(int(p['right'], 16))
    lc, rc = L['category'], R['category']
    lh, rh = lc == 'HAS_RET', rc == 'HAS_RET'
    table[0 if lh else 1][0 if rh else 1] += 1
    table_full[(lc, rc)] += 1
    if lh and rh:
        both_ret += 1
    if not (lh and rh):
        any_not += 1
    if not lh and not rh:
        both_not += 1
        both_not_rows.append({
            'vt': p['vt'], 'sib_vt': p['sib_vt'], 'k': p['k'],
            'left': p['left'], 'right': p['right'],
            'left_category': lc, 'right_category': rc,
            'left_boundary': L, 'right_boundary': R,
            'left_probe': probes(int(p['left'], 16)),
            'right_probe': probes(int(p['right'], 16))})
    detail_rows.append({'vt': p['vt'], 'k': p['k'], 'left': p['left'],
                        'right': p['right'], 'left_category': lc,
                        'right_category': rc, 'left_boundary': L,
                        'right_boundary': R,
                        'r192_ret_left': p['r192_ret_left'],
                        'r192_ret_right': p['r192_ret_right']})

samples = both_not_rows if len(both_not_rows) <= 20 else []
out = {
    'meta': {
        'binary': 'ra2bench/gamemd.exe', 'sha256': EXE_SHA,
        'card': 'R193', 'capstone': capstone.__version__,
        'text_range': [hex(LO), hex(HI)],
        'full_window_bytes': WINDOW,
        'r192_inc_window_bytes': 96,
        'method': ('per-target linear capstone33 disasm, detail=False; boundary at '
                   'ret/retn, >=2 consecutive 90/CC, or 512-byte exhaustion'),
    },
    's1': {
        'COL': len(COL), 'VT': len(VT), 'slots': sum(NS.values()),
        'groups': len(group), 'nonprimary_slots': sum(NS[v] for v in VT if COL[VT[v]]['mdisp'] != 0),
        'direct': len(direct), 'cat_counts': dict(cat_counts),
        'pairs': len(pairs), 'five_numbers': five, 'expected': FIVE_EXPECT,
        'five_numbers_match': five == FIVE_EXPECT,
        'thunk_difference': THUNK_DIFF,
    },
    'pairs': len(pairs),
    'inc_pairs': len(inc_pairs),
    'both_has_ret': both_ret,
    'any_not_has_ret': any_not,
    'both_not_has_ret': both_not,
    'table_2x2': {
        'rows': 'left: [HAS_RET, not HAS_RET]',
        'cols': 'right: [HAS_RET, not HAS_RET]',
        'matrix': table,
        'both_has_ret': table[0][0], 'left_only': table[0][1],
        'right_only': table[1][0], 'both_not_has_ret': table[1][1],
    },
    'table_full': {lc + '|' + rc: c for (lc, rc), c in sorted(table_full.items())},
    'samples': samples,
    'samples_omitted_count': 0 if len(both_not_rows) <= 20 else len(both_not_rows),
    'controls': controls,
    'all_controls_pass': all(v['pass'] for v in controls.values()),
    'inc_pair_details': detail_rows,
    'measured_vs_unmeasured': {
        'measured': [
            'S1 535/1013/478/525/10 under R192-effective thunk predicate',
            'R192 96-byte inc filter result = 103 pairs',
            'S2 boundary category of every one of the 103 x 2 targets within a 512-byte window',
            'C1/C2/C3/C4 controls',
            'first-16-byte probes and P.where for every both-non-HAS_RET pair',
        ],
        'unmeasured': [
            'semantic identity / game meaning of any target function',
            'behavior beyond each 512-byte linear window',
            'whether any non-HAS_RET target is genuinely a function under a non-linear CFG model',
        ],
    },
}

with open(OUT, 'w') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print('=== S1 ===', json.dumps(out['s1'], ensure_ascii=False))
print('=== THUNK DIFF ===', json.dumps(THUNK_DIFF, ensure_ascii=False))
print('=== CONTROLS ===', json.dumps(controls, ensure_ascii=False))
print('=== STATS ===', json.dumps({
    'pairs': len(pairs), 'inc_pairs': len(inc_pairs),
    'both_has_ret': both_ret, 'any_not_has_ret': any_not,
    'both_not_has_ret': both_not, 'table_2x2': table,
    'table_full': out['table_full'], 'sample_count': len(samples)}, ensure_ascii=False))
if both_not_rows:
    print('=== SAMPLES ===', json.dumps(samples, ensure_ascii=False))
print('WROTE', OUT, 'bytes', os.path.getsize(OUT),
      'sha256', hashlib.sha256(open(OUT, 'rb').read()).hexdigest())
print('SUMMARY pairs=%d inc=%d both_ret=%d both_not=%d' %
      (len(pairs), len(inc_pairs), both_ret, both_not))
