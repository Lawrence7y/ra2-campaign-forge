#!/usr/bin/env python3
# R131 r131w: self-audit of every script in _r131 + the write-discipline invariants.
# This is the "N1" style pass: it re-runs each script and requires exit 0, and it greps
# for the two failure shapes this repo has been bitten by repeatedly:
#   (a) tautological assertions  (or True / if False: chk / == itself)
#   (b) assertions whose two sides come from the same expression (no independence)
import hashlib
import io
import json
import os
import re
import subprocess
import sys

D = '/home/t628/projects/ra2-campaign-forge/_r131'
R14 = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
ROOT = '/home/t628/projects/ra2-campaign-forge'
OUT = os.path.join(D, 'r131w_selfaudit.json')

SCRIPTS = ['r131p_c17vac.py', 'r131q_verify.py', 'r131r_semantics.py',
           'r131s_closings.py', 'r131t_loop_semantics.py', 'r131v_c18ctrl.py',
           'r131u_backup.py']

A = []
def chk(name, cond, detail=''):
    A.append({'assert': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + (' :: ' + str(detail) if detail else ''))

R = {}
print('=== N1 re-run every R131 script ===')
runs = {}
for s in SCRIPTS:
    p = os.path.join(D, s)
    r = subprocess.run([sys.executable, p], capture_output=True, text=True, timeout=1200)
    runs[s] = {'rc': r.returncode, 'out_tail': (r.stdout or '')[-300:]}
    print('   %-26s rc=%d' % (s, r.returncode))
R['runs'] = {k: v['rc'] for k, v in runs.items()}
chk('every R131 script exits 0 when re-run', all(v['rc'] == 0 for v in runs.values()),
    {k: v['rc'] for k, v in runs.items() if v['rc'] != 0})

print('\n=== N2 tautology / non-independence scan ===')
# SELF-ERROR S-210: the patterns below are spelled with concatenation on purpose. Written
# literally, this scanner matches ITSELF (it found 4 hits inside its own source) and the
# "only one known constant assertion" check then fails on its own bookkeeping. A detector
# must not be written in the same surface form as the thing it detects.
B = chr(92)   # backslash, kept out of the literals for the same reason
BAD_PATTERNS = [
    (r'\bor\s+True\b', 'or True makes the assertion constant'),
    (r'\b' + 'if' + chr(32) + 'False' + chr(32) + r'?:', 'if False: disables a branch'),
    (r'chk\([^,]+,\s*' + 'True' + r'\s*[,)]', 'chk(..., True, ...) is constant'),
    (r'assert' + chr(32) + 'True' + B + 'b', 'assert True'),
]
hits = []
for s in sorted(os.listdir(D)):
    if not s.endswith('.py') or s == 'r131w_selfaudit.py':
        continue          # a detector cannot audit its own detection patterns
    src = io.open(os.path.join(D, s), encoding='utf-8', errors='replace').read()
    for ln_no, ln in enumerate(src.splitlines(), 1):
        stripped = ln.strip()
        if stripped.startswith('#'):
            continue
        for pat, why in BAD_PATTERNS:
            if re.search(pat, ln):
                hits.append({'file': s, 'line': ln_no, 'why': why, 'text': stripped[:110]})
R['tautology_hits'] = hits
for h in hits:
    print('   %s:%d  %s  :: %s' % (h['file'], h['line'], h['why'], h['text']))
# P4 in r131v is a deliberate "chk(..., True, ...)" documenting a cross-reference, not a
# real assertion. Rather than delete it silently, require it to be the ONLY one and require
# it to be labelled as such.
known = [h for h in hits if h['file'] == 'r131v_c18ctrl.py' and 'P4' in h['text']]
other = [h for h in hits if h not in known]
chk('the only constant assertion is the labelled P4 cross-reference note in r131v',
    len(other) == 0 and len(known) == 1,
    {'known': len(known), 'other': [(h['file'], h['line']) for h in other]})

print('\n=== N3 every assertion count matches what the script printed ===')
counts = {}
for s in SCRIPTS:
    out = runs[s]['out_tail']
    m = re.search(r'ASSERTIONS:\s*(\d+)\s*total,\s*(\d+)\s*pass,\s*(\d+)\s*fail', out)
    if m:
        counts[s] = {'total': int(m.group(1)), 'pass': int(m.group(2)), 'fail': int(m.group(3))}
R['assertion_counts'] = counts
print('   ' + json.dumps(counts, indent=1))
chk('every assertion-bearing script reports fail=0', all(v['fail'] == 0 for v in counts.values()),
    {k: v for k, v in counts.items() if v['fail']})
chk('every assertion-bearing script reports pass == total',
    all(v['pass'] == v['total'] for v in counts.values()),
    {k: v for k, v in counts.items() if v['pass'] != v['total']})
R['total_assertions'] = sum(v['total'] for v in counts.values())
chk('total assertion count is at least 80', R['total_assertions'] >= 80, R['total_assertions'])

print('\n=== N4 write-discipline invariants ===')
FILES = {
    'R14_COMMON.md': (os.path.join(R14, 'R14_COMMON.md'), 1081),
    'LEAD_LOCK': (os.path.join(ROOT, 'lead', 'LEAD_LOCK'), 137),
    'GOAL_THREE_TARGETS_20261018.md':
        (os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'), 337),
    'STATUS_BOARD.md': (os.path.join(R14, 'STATUS_BOARD.md'), 0),
    'BOARD_ARCHIVE.md': (os.path.join(R14, 'BOARD_ARCHIVE.md'), 2952),
}
cr = {}
for name, (p, exp) in FILES.items():
    b = io.open(p, 'rb').read()
    cr[name] = {'cr': b.count(b'\r\n'), 'expected': exp, 'bytes': len(b),
                'lf': b.count(b'\n'), 'sha256': hashlib.sha256(b).hexdigest()}
    print('   %-32s CR=%-5d (want %-5d) bytes=%-8d' % (name, cr[name]['cr'], exp,
                                                       cr[name]['bytes']))
R['cr'] = cr
chk('all five CR invariants hold', all(v['cr'] == v['expected'] for v in cr.values()))

# backups exist and match the live files they claim to protect
bk = json.load(open(os.path.join(D, 'r131u_backup.json'), encoding='utf-8'))
chk('backup manifest says all 7 backups read back byte-identically', bk['all_ok'],
    [e['name'] for e in bk['files'] if not e.get('readback_ok')])
chk('7 backup files exist on disk',
    all(os.path.isfile(e.get('backup', '')) for e in bk['files']), len(bk['files']))
R['backup_files'] = [e.get('backup') for e in bk['files']]

# the gate itself is at the R131 version
gate = io.open(os.path.join(R14, 'check_disc.py'), encoding='utf-8').read()
R['gate_ver'] = re.search(r"GATE_VER\s*=\s*'([^']+)'", gate).group(1)
chk('GATE_VER has been raised to R131', R['gate_ver'] == 'R131', R['gate_ver'])
chk('the new C18 block is present in the gate', 'C18_VACUOUS' in gate)

print('\n=== N5 no orphan processes ===')
ps = subprocess.run(['ps', '-eo', 'pid,etime,cmd'], capture_output=True, text=True).stdout
orphan = [l for l in ps.splitlines()
          if ('_r131' in l or '_r130' in l) and 'r131w' not in l]
R['orphans'] = orphan
chk('no leftover R131/R130 python processes', not orphan, orphan[:4])

R['assertions'] = A
R['summary'] = {'total': len(A), 'pass': sum(1 for x in A if x['ok']),
                'fail': [x['assert'] for x in A if not x['ok']]}
print('\nASSERTIONS: %d total, %d pass, %d fail'
      % (R['summary']['total'], R['summary']['pass'], len(R['summary']['fail'])))
json.dump(R, open(OUT, 'w'), ensure_ascii=False, indent=1)
raise SystemExit(1 if R['summary']['fail'] else 0)
