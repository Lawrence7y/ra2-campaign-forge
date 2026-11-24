# -*- coding: utf-8 -*-
"""M83 phase 3 (VERIFY): all mandatory recomputations. Read-only for coverage/PANEL/card dirs.

Runs EVID_RESOLVE/resolve.py with --out pointed into MERGE_M83 (never writes EVID_RESOLVE).
"""
import os, re, json, hashlib, importlib.util, subprocess, sys

R14 = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
PAN = os.path.join(R14, 'COVERAGE', 'PANEL.md')
MERGE = os.path.join(R14, 'MERGE_M83')
RESOLVE_PY = os.path.join(R14, 'EVID_RESOLVE', 'resolve.py')
ATLAS = os.path.join(os.path.dirname(R14), 'next_re_20261112_r10', 'W130_atlas', 'function_atlas.tsv')
VOUT = os.path.join(MERGE, '_verify_resolve_out')


def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def state(path):
    st = os.stat(path)
    b = open(path, 'rb').read()
    return {'mtime': st.st_mtime, 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}


res = json.load(open(os.path.join(MERGE, '_apply_result.json'), 'r', encoding='utf-8'))
changes = res['changes']
assert len(changes) == 4 and res['fix_count'] == 4 and res['unresolved_count'] == 9 and res['ambiguous_count'] == 13

# 1. current disk state matches AFTER recorded by apply
assert sha(COV) == res['after']['coverage.tsv']['sha256']
assert sha(PAN) == res['after']['PANEL.md']['sha256']
print('sha256: coverage.tsv AFTER OK, PANEL.md AFTER OK')
print('BEFORE->AFTER cov: %s -> %s' % (res['before']['coverage.tsv']['sha256'][:8], res['after']['coverage.tsv']['sha256'][:8]))
print('BEFORE->AFTER pan: %s -> %s' % (res['before']['PANEL.md']['sha256'][:8], res['after']['PANEL.md']['sha256'][:8]))

# 2. read coverage.tsv
b = open(COV, 'rb').read()
assert b[:3] != b'\xef\xbb\xbf' and b'\r\n' not in b and not b.endswith(b'\n')
lines = b.decode('utf-8').split('\n')
assert lines[0].split(',') == ['entry', 'subsystem', 'name', 'one_line_semantics', 'grade',
                               'evidence_path', 'n_sources', 'conflict']
rows = [ln.split('\t') for ln in lines[1:]]
assert all(len(r) == 8 for r in rows)
print('data rows:', len(rows))
assert len(rows) == 18498, len(rows)

# 3. counts
n_proved = sum(1 for r in rows if r[4] == '[已证]')
print('全表 [已证]:', n_proved)
assert n_proved == 1654

def norm(e):
    return ('%08X' % int(e.strip(), 16)).upper()
atlas = set()
for i, raw in enumerate(open(ATLAS, 'r', encoding='utf-8').read().split('\n')):
    if i == 0 or not raw.strip():
        continue
    f = raw.replace('\r', '').split('\t')
    if f and re.match(r'^[0-9A-Fa-f]{8}$', f[0].strip()):
        atlas.add(norm(f[0]))
n_atlas_proved = sum(1 for r in rows if r[4] == '[已证]' and norm(r[0]) in atlas)
print('atlas 内 [已证]:', n_atlas_proved)
assert n_atlas_proved == 1648, n_atlas_proved

# 4. changed rows: grade unchanged, other columns unchanged, annotation parses back
by_entry = {r[0]: r for r in rows}
for c in changes:
    e = c['entry']
    r = by_entry[e]
    assert r[4] == c['grade'] == '[已证]', ('grade changed', e)
    assert r[5] == c['new_value'], ('col6 mismatch', e)
    assert r[1] == c['subsystem']
    assert 'M83 歧义消解：原记 ' + c['old_value'] + '，按 subsystem=' + c['subsystem'] + ' 锁定为 ' + c['new_main'] in r[5]
    assert r[5].startswith(c['new_main'])
    # new path exists
    rp = c['new_main'].split('#', 1)[0].strip()
    assert os.path.isfile(os.path.join(R14, rp.replace('/', os.sep))), (e, rp)
print('changed rows grade/annotation/path OK:', len(changes))

# 5. unresolved rows: col6 unchanged from original R_MISSING value, no M83 annotation
unresolved_entries = [d['entry'] for d in res['unresolved_detail']]
for e in unresolved_entries:
    r = by_entry[e]
    assert 'M83 歧义消解' not in r[5], ('unresolved row modified', e)
    assert r[4] == '[已证]'
print('unresolved rows untouched:', len(unresolved_entries))

# 6. re-run resolve.py into MERGE_M83 (never touching EVID_RESOLVE)
cmd = [sys.executable, RESOLVE_PY, '--repo', os.path.dirname(os.path.dirname(R14)),
       '--coverage', COV, '--out', VOUT]
print('running:', ' '.join(cmd))
proc = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
if proc.returncode != 0:
    sys.exit('resolve.py failed (returncode %d)' % proc.returncode)
# NOTE: resolve.py prints GBK-encoded console text; its stdout is not needed for
# verification — we read summary.tsv / resolve.tsv from disk directly below.

summary = {}
for raw in open(os.path.join(VOUT, 'summary.tsv'), 'r', encoding='utf-8').read().split('\n'):
    f = raw.split('\t')
    if len(f) == 3 and f[0] != 'class':
        summary[f[0]] = (int(f[1]), f[2])
print('new classification:', summary)
assert summary['R_OK'][0] == 843, summary
assert summary['R_MISSING'][0] == 9, summary
assert summary['R_TRACE_ONLY'][0] == 802, summary
assert summary['R_EMPTY'][0] == 0, summary
assert summary['R_OK'][0] == 839 + len(changes)
assert summary['R_MISSING'][0] == 13 - len(changes)

# 7. new resolve.tsv data rows = 9 + 802 = 811
vresolve = open(os.path.join(VOUT, 'resolve.tsv'), 'r', encoding='utf-8').read().split('\n')
vdata = [x for x in vresolve[1:] if x.strip()]
print('new resolve.tsv data rows:', len(vdata))
assert len(vdata) == 811, len(vdata)
# verify remaining R_MISSING entries are exactly the 9 unresolved
v_missing_entries = [x.split('\t')[0] for x in vdata if x.split('\t')[5] == 'R_MISSING']
assert set(v_missing_entries) == set(unresolved_entries), (sorted(v_missing_entries), sorted(unresolved_entries))
print('remaining R_MISSING entries == 9 unresolved: OK')

# 8. R_OK percent
pct_calc = '%.2f' % (100.0 * summary['R_OK'][0] / n_proved)
print('R_OK pct = %s%%' % pct_calc)
assert pct_calc == '50.97'

# 9. PANEL.md M83 note at expected lines
ptxt = open(PAN, 'r', encoding='utf-8').read()
plines = ptxt.split('\n')
s, e = res['m83_lines']
assert 'M83 补记' in plines[s - 1], (s, plines[s - 1])
assert 'R_OK' in plines[e - 1] and '判定与计数未变' in plines[e - 1]
assert '843 / 1,654' in plines[e - 1]
assert '修复 4 行、9 行仍未修' in plines[e - 1]
assert 'M82 补记' in plines[s - 4]  # M82 note first line (199) sits 3 lines above M83 first line (202)
print('PANEL M83 note L%d-L%d OK; M82 note intact' % (s, e))

# 10. 达标翻转 check: grade/semantics/counts unchanged => cannot flip
print('判定/计数: [已证] 1654 unchanged, atlas内 1648 unchanged, grades of 4 changed rows unchanged => 达标无翻转')

out = {
    'data_rows': len(rows), 'proved_total': n_proved, 'proved_atlas': n_atlas_proved,
    'fixed_rows': len(changes), 'unresolved_rows': len(unresolved_entries),
    'ambiguous_rows': res['ambiguous_count'],
    'R_OK': summary['R_OK'][0], 'R_OK_pct': summary['R_OK'][1],
    'R_MISSING': summary['R_MISSING'][0], 'R_TRACE_ONLY': summary['R_TRACE_ONLY'][0],
    'R_EMPTY': summary['R_EMPTY'][0], 'new_resolve_data_rows': len(vdata),
    'pct_calc': pct_calc, '达标翻转': 'no — grade/semantics/counts unchanged by pure pointer fix',
}
with open(os.path.join(MERGE, '_verify_result.json'), 'w', encoding='utf-8', newline='\n') as fh:
    json.dump(out, fh, ensure_ascii=False, indent=2)
    fh.write('\n')
print('\nALL VERIFICATION ASSERTIONS PASSED')
print(json.dumps(out, ensure_ascii=False, indent=2))
