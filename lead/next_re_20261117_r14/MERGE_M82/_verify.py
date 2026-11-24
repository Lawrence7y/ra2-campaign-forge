# -*- coding: utf-8 -*-
"""M82 phase 3 (VERIFY): all mandatory recomputations. Read-only."""
import os, re, json, hashlib, collections
import importlib.util

R14 = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
PAN = os.path.join(R14, 'COVERAGE', 'PANEL.md')
RESOLVE_PY = os.path.join(R14, 'EVID_RESOLVE', 'resolve.py')
MERGE = os.path.join(R14, 'MERGE_M82')
ATLAS = os.path.join(os.path.dirname(R14), 'next_re_20261112_r10', 'W130_atlas', 'function_atlas.tsv')
VOUT = os.path.join(MERGE, '_verify_resolve_out')

res = json.load(open(os.path.join(MERGE, '_apply_result.json'), 'r', encoding='utf-8'))
changes = res['changes']
ambiguous = res['ambiguous_entries']
assert len(changes) == 361 and len(ambiguous) == 13

def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()

# ---- 1. current disk state matches AFTER recorded by apply ----
assert sha(COV) == res['after']['coverage.tsv']['sha256']
assert sha(PAN) == res['after']['PANEL.md']['sha256']
print('sha256: coverage.tsv AFTER OK, PANEL.md AFTER OK')

# ---- 2. read coverage.tsv ----
b = open(COV, 'rb').read()
assert b[:3] != b'\xef\xbb\xbf' and b'\r\n' not in b and not b.endswith(b'\n')
lines = b.decode('utf-8').split('\n')
header = lines[0].split(',')
row_lines = lines[1:]
rows = [ln.split('\t') for ln in row_lines]
assert all(len(r) == 8 for r in rows)
print('data rows:', len(rows))
assert len(rows) == 18498, len(rows)

# ---- 3. counts ----
n_proved = sum(1 for r in rows if r[4] == '[已证]')
print('全表 [已证]:', n_proved)
assert n_proved == 1654

def norm(e):
    return ('%08X' % int(e.strip(), 16)).upper()
atlas = set()
for i, raw in enumerate(open(ATLAS, 'r', encoding='utf-8').read().split('\n')):
    if i == 0 or not raw.strip():
        continue
    f = raw.replace('\r','').split('\t')
    if f and re.match(r'^[0-9A-Fa-f]{8}$', f[0].strip()):
        atlas.add(norm(f[0]))
n_atlas_proved = sum(1 for r in rows if r[4] == '[已证]' and norm(r[0]) in atlas)
print('atlas 内 [已证]:', n_atlas_proved)
assert n_atlas_proved == 1648, n_atlas_proved

# ---- 4. changed rows: col5 grade unchanged, col1/2/3/4/7/8 unchanged, annotation present ----
by_entry = {r[0]: r for r in rows}
for c in changes:
    e = c['entry']
    r = by_entry[e]
    assert r[4] == c['grade'], ('grade changed', e)
    assert r[5] == c['new_value'], ('col6 mismatch', e)
    assert 'M82 指针修复：原记 ' in r[5]
    assert r[5].startswith(c['new_main'])
    # other columns compared against pre-change values are checked via byte-diff in apply;
    # here assert structural invariants
    assert r[6] == '1' or r[6].isdigit()
    assert r[7] in ('0','1')

# ---- 5. ambiguous rows: col6 unchanged (still original R_MISSING value, no annotation) ----
resolv_rows = []
with open(os.path.join(os.path.dirname(RESOLVE_PY), 'resolve.tsv'), 'r', encoding='utf-8') as fh:
    hdr = fh.readline().rstrip('\n').split('\t')
    for raw in fh.read().split('\n'):
        if not raw.strip():
            continue
        f = raw.split('\t')
        if len(f) == 8:
            resolv_rows.append(dict(zip(hdr, f)))
orig_ev = {r['entry']: r['evidence_path'] for r in resolv_rows if r['class'] == 'R_MISSING'}
for e in ambiguous:
    r = by_entry[e]
    assert r[5] == orig_ev[e], ('ambiguous row changed', e)
    assert 'M82 指针修复' not in r[5]
print('ambiguous rows unchanged:', len(ambiguous))

# ---- 6. new resolvability from re-run summary.tsv ----
summary = {}
for raw in open(os.path.join(VOUT, 'summary.tsv'), 'r', encoding='utf-8').read().split('\n'):
    f = raw.split('\t')
    if len(f) == 3 and f[0] != 'class':
        summary[f[0]] = (int(f[1]), f[2])
print('new classification:', summary)
assert summary['R_OK'][0] == 839
assert summary['R_MISSING'][0] == 13
assert summary['R_TRACE_ONLY'][0] == 802
assert summary['R_EMPTY'][0] == 0
assert summary['R_OK'][0] == 478 + len(changes)

# ---- 7. new resolve.tsv data rows = 13 + 802 = 815 ----
vresolve = open(os.path.join(VOUT, 'resolve.tsv'), 'r', encoding='utf-8').read().split('\n')
vdata = [x for x in vresolve[1:] if x.strip()]
assert len(vdata) == 815, len(vdata)
print('new resolve.tsv data rows:', len(vdata))

# ---- 8. all annotation notes parse back to original old value ----
MARK = ';M82 指针修复：原记 '
SEP = '（缺卡目录），实为 '
orig_ev_all = {r['entry']: r['evidence_path'] for r in resolv_rows if r['class'] == 'R_MISSING'}
for c in changes:
    v = by_entry[c['entry']][5]
    assert v.count(MARK) == 1
    pos = v.index(MARK)
    rest = v[pos+len(MARK):]
    old = rest[:rest.index(SEP)]
    assert old == c['old_value'] == orig_ev_all[c['entry']], ('old value mismatch', c['entry'])
print('annotation back-parse OK for all', len(changes), 'rows')

# ---- 9. grade/semantics unchanged for ALL rows (=> 达标 cannot flip) ----
# Compare against BEFORE by reconstructing BEFORE col4/col5 from _before_state? Not stored as bytes.
# Instead: apply-result recorded grade per changed row; for all others, file byte-diff already asserted in apply.
# Additional independent check: total [已证] and atlas [已证] unchanged (done), so proved counts unchanged.
print('判定/计数: [已证] 1654 unchanged, atlas内 1648 unchanged, grades of 361 changed rows unchanged => 达标无翻转')

# ---- 10. PANEL.md M82 note present at expected lines ----
ptxt = open(PAN, 'r', encoding='utf-8').read()
plines = ptxt.split('\n')
assert 'M82 补记' in plines[res['m82_lines'][0]-1]
assert 'R_OK' in plines[res['m82_lines'][1]-1]
assert '判定与计数均未变' in plines[res['m82_lines'][1]-1]
# M81 note still intact
assert 'M81 披露' in plines[193]
print('PANEL M82 note L%d-L%d OK; M81 note intact' % tuple(res['m82_lines']))

out = {
    'data_rows': len(rows),
    'proved_total': n_proved,
    'proved_atlas': n_atlas_proved,
    'fixed_rows': len(changes),
    'ambiguous_rows': len(ambiguous),
    'R_OK': summary['R_OK'][0], 'R_OK_pct': summary['R_OK'][1],
    'R_MISSING': summary['R_MISSING'][0],
    'R_TRACE_ONLY': summary['R_TRACE_ONLY'][0],
    'R_EMPTY': summary['R_EMPTY'][0],
    'new_resolve_data_rows': len(vdata),
    'pct_calc': '%.2f' % (100.0 * summary['R_OK'][0] / n_proved),
    'm81_upper_pct_note': 'M81 stated 50.72% (truncated); rounded recompute = 50.73%',
    '达标翻转': 'no — grade/semantics/counts unchanged by pure pointer fix',
}
with open(os.path.join(MERGE, '_verify_result.json'), 'w', encoding='utf-8', newline='\n') as fh:
    json.dump(out, fh, ensure_ascii=False, indent=2)
    fh.write('\n')
print('\nALL VERIFICATION ASSERTIONS PASSED')
print(json.dumps(out, ensure_ascii=False, indent=2))
