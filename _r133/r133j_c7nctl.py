#!/usr/bin/env python3
# R133 r133j: positive/negative controls for the new C7b census pin.
# A gate change that nobody can break is not a check. Each control copies the gate plus its
# data files into a temp dir, mutates exactly ONE thing, and asserts the exit code flips.
import json, os, shutil, subprocess, tempfile, io

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead/next_re_20261117_r14')
OUT = os.path.join(ROOT, '_r133/r133j_c7nctl.json')

R = {}; ASSERT = []
def chk(n, c, d=''):
    ASSERT.append({'assert': n, 'pass': bool(c), 'detail': str(d)})
    print(('  PASS ' if c else '  FAIL ') + n + (('  [' + str(d) + ']') if d else ''))
    return bool(c)

def run_gate(td):
    p = subprocess.run(['python3', os.path.join(td, 'check_disc.py')],
                       capture_output=True, text=True, timeout=280, cwd=td)
    return p.returncode, p.stdout + p.stderr

def stage():
    td = tempfile.mkdtemp(prefix='r133j_')
    dst = os.path.join(td, 'r14')
    shutil.copytree(R14, dst, ignore=shutil.ignore_patterns('__pycache__'))
    return td, dst

TABNAME = 'DISC_RECHECK.tsv'

td, dst = stage()
rc, out = run_gate(dst)
R['pc_exit'] = rc
chk('PC1 unmodified copy exits 0', rc == 0, rc)
chk('PC2 unmodified copy prints the C7b census with three zero-count shapes',
    'C7b shape census' in out and 'exists=0' in out and 'bytes==0' in out and 'none=0' in out,
    [l for l in out.splitlines() if 'C7b' in l][:1])
shutil.rmtree(td, ignore_errors=True)

# NC1: turn one grep row into the dead `exists` shape -> exists 0->1 -> census drift FAIL
td2, dst2 = stage()
tab = os.path.join(dst2, TABNAME)
lines = io.open(tab, encoding='utf-8').read().rstrip('\n').split('\n')
idx = next(i for i, l in enumerate(lines) if l.count('\t') == 6 and '\tgrep=' in l)
cols = lines[idx].split('\t'); cols[5] = 'exists (1 B)'; lines[idx] = '\t'.join(cols)
io.open(tab, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
rc2, out2 = run_gate(dst2)
R['nc1_exit'] = rc2
chk('NC1 turning a row into the dead `exists` shape makes the gate FAIL', rc2 != 0, rc2)
chk('NC2 the failure names the drifted shape (exists=1)',
    'C7b shape census drifted' in out2 and 'exists=1' in out2,
    [l for l in out2.splitlines() if 'drifted' in l][:1])
shutil.rmtree(td2, ignore_errors=True)

# NC3: break a live grep row -> must still FAIL on its own (census unchanged)
td3, dst3 = stage()
tab3 = os.path.join(dst3, TABNAME)
lines3 = io.open(tab3, encoding='utf-8').read().rstrip('\n').split('\n')
idx3 = next(i for i, l in enumerate(lines3) if l.count('\t') == 6 and '\tgrep=' in l)
c3 = lines3[idx3].split('\t'); c3[5] = 'grep=ZZZ_no_such_pattern'; lines3[idx3] = '\t'.join(c3)
io.open(tab3, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines3) + '\n')
rc3, out3 = run_gate(dst3)
R['nc3_exit'] = rc3
chk('NC3 breaking a live grep row still FAILs (C7b is additive, not a replacement)', rc3 != 0, rc3)
shutil.rmtree(td3, ignore_errors=True)

# NC4: remove the zero-seeding -> the three zero shapes report as vanished and FAIL
td4, dst4 = stage()
g4 = os.path.join(dst4, 'check_disc.py')
src = io.open(g4, encoding='utf-8').read()
seed = 'c7_shape = dict((_k, 0) for _k in C7_SHAPE_PIN)'
assert seed in src
io.open(g4, 'w', encoding='utf-8', newline='\n').write(src.replace(seed, 'c7_shape = {}'))
rc4, out4 = run_gate(dst4)
R['nc4_exit'] = rc4
chk('NC4 removing the zero-seeding makes zero-count shapes FAIL as vanished',
    rc4 != 0 and 'vanished from the table entirely' in out4, rc4)
shutil.rmtree(td4, ignore_errors=True)

# NC5: deliberate repin lets the mutated table through -> drift is catchable but not unpassable
td5, dst5 = stage()
tab5 = os.path.join(dst5, TABNAME)
g5 = os.path.join(dst5, 'check_disc.py')
lines5 = io.open(tab5, encoding='utf-8').read().rstrip('\n').split('\n')
idx5 = next(i for i, l in enumerate(lines5) if l.count('\t') == 6 and '\tgrep=' in l)
c5 = lines5[idx5].split('\t'); c5[5] = 'exists (1 B)'; lines5[idx5] = '\t'.join(c5)
io.open(tab5, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines5) + '\n')
src5 = io.open(g5, encoding='utf-8').read()
src5 = src5.replace("'exists': 0", "'exists': 1").replace("'grep=': 24", "'grep=': 23")
io.open(g5, 'w', encoding='utf-8', newline='\n').write(src5)
rc5, out5 = run_gate(dst5)
R['nc5_exit'] = rc5
chk('NC5 a DELIBERATE repin lets the mutated table through (drift is catchable, not unpassable)',
    rc5 == 0, rc5)
shutil.rmtree(td5, ignore_errors=True)

R['assertions'] = ASSERT
R['summary'] = {'pass': sum(1 for x in ASSERT if x['pass']), 'total': len(ASSERT)}
print('\nSUMMARY %d/%d PASS' % (R['summary']['pass'], R['summary']['total']))
json.dump(R, open(OUT, 'w'), indent=1)
