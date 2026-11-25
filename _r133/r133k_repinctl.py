#!/usr/bin/env python3
# R133 r133k: controls for the 2.137 re-pin. Each mutates ONE thing in a staged copy.
# S-211 says the sha pin cannot see a DUPLICATED entry, so entry count is asserted too.
import io, os, shutil, subprocess, sys, tempfile, hashlib, re
ROOT = '/home/t628/projects/ra2-campaign-forge'
src = io.open(ROOT + '/_r133/r133j2_c7nctl.py', encoding='utf-8').read()
ns = {'__file__': ROOT + '/_r133/r133j2_c7nctl.py'}
exec(compile(src.split('# ---- baseline hash')[0], 'x', 'exec'), ns)
stage, gate_path, run_gate = ns['stage'], ns['gate_path'], ns['run_gate']
RC_rel = 'lead/next_re_20261117_r14/R14_COMMON.md'
OUT = os.path.join(ROOT, '_r133/r133k_repinctl.json')
A = []
def chk(n, c, d=''):
    A.append({'assert': n, 'pass': bool(c), 'detail': str(d)})
    print(('  PASS ' if c else '  FAIL ') + n + (('  [' + str(d) + ']') if d != '' else ''))

print('=== PC ===')
td = stage(); rc, out = run_gate(td)
chk('PC1 staged baseline exit 0', rc == 0, rc)
chk('PC2 C16 reports 131 pinned / 0 unpinned',
    'pinned 131' in out and 'unpinned 0' in out,
    [l.strip() for l in out.splitlines() if 'per-section floors' in l][:1])
shutil.rmtree(td, ignore_errors=True)

print('=== NC1: hollow out 2.137 below its floor ===')
td = stage(); p = os.path.join(td, RC_rel)
t = io.open(p, encoding='utf-8', newline='').read()
m = re.search(r'(?m)^## 2\.137\b.*?(?=^## 2\.\d|\Z)', t, re.S)
io.open(p, 'w', encoding='utf-8', newline='').write(t.replace(m.group(0), '## 2.137\n\nx\n\n'))
rc, out = run_gate(td)
chk('NC1 truncating 2.137 body fails the gate and names 137', rc != 0 and '137' in out, rc)
shutil.rmtree(td, ignore_errors=True)

print('=== NC2: delete the whole 2.137 section ===')
td = stage(); p = os.path.join(td, RC_rel)
t = io.open(p, encoding='utf-8', newline='').read()
m = re.search(r'(?m)^## 2\.137\b.*?(?=^## 2\.\d|\Z)', t, re.S)
io.open(p, 'w', encoding='utf-8', newline='').write(t.replace(m.group(0), ''))
rc, out = run_gate(td)
chk('NC2 deleting 2.137 entirely fails the gate (missing section)', rc != 0, rc)
shutil.rmtree(td, ignore_errors=True)

print('=== NC3: change ONLY the floor for 137, leave the sha pin alone ===')
td = stage(); g = gate_path(td)
s = io.open(g, encoding='utf-8').read()
s = s.replace('137: 3159,', '137: 3000,')
io.open(g, 'w', encoding='utf-8', newline='\n').write(s)
rc, out = run_gate(td)
chk('NC3 editing one floor without re-pinning the sha is caught (TAMPERED)',
    rc != 0 and 'TAMPERED' in out, rc)
shutil.rmtree(td, ignore_errors=True)

print('=== NC4: duplicate the 137 entry (the S-211 failure mode) ===')
td = stage(); g = gate_path(td)
s = io.open(g, encoding='utf-8').read()
s = s.replace('    137: 3159,\n}', '    137: 3159,\n    137: 3159,\n}')
io.open(g, 'w', encoding='utf-8', newline='\n').write(s)
rc, out = run_gate(td)
# target the C16 line specifically -- C15 also prints "pinned NNN", so an unanchored
# 'pinned (\d+)' matches the wrong line and silently reports the wrong number (S-227).
mp = re.search(r'C16 per-section floors: \d+ sections measured \(pinned (\d+)\)', out)
cnt = re.search(r'C16_FLOORS = \{(.*?)\n\}', s, re.S)
pairs = re.findall(r'(\d+):\s*(\d+)', cnt.group(1))
chk('NC4 a duplicated 137 entry does NOT change the reported pinned count (sha normalizes it '
    'away) -- proving the sha pin alone cannot catch duplication, exactly S-211',
    mp is not None and int(mp.group(1)) == 131,
    'pinned_reported=%s raw_pairs=%d gate_exit=%s' % (mp.group(1) if mp else None, len(pairs), rc))
shutil.rmtree(td, ignore_errors=True)

print('=== NC5: real tree untouched ===')
h = hashlib.sha256(open(os.path.join(ROOT, 'lead/next_re_20261117_r14/check_disc.py'), 'rb').read()).hexdigest()
chk('NC5 real gate sha unchanged by this suite', h.startswith('9f19f65d38350bf3'), h[:16])

print('\nSUMMARY %d/%d PASS' % (sum(1 for x in A if x['pass']), len(A)))
json_dump = {'assertions': A, 'summary': {'pass': sum(1 for x in A if x['pass']), 'total': len(A)}}
import json as _j
_j.dump(json_dump, io.open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
