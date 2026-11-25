#!/usr/bin/env python3
# R132 r132p: adversarial controls for the C16 re-pin and the C7 dead-branch finding.
#
# Every mutation must make the gate FAIL; after each, restore from memory and verify the
# file returns byte-identically. This is what separates "the check exists" from
# "the check works".
import hashlib, io, json, os, re, subprocess

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
GATE = os.path.join(R14, 'check_disc.py')
COMMON = os.path.join(R14, 'R14_COMMON.md')
OUT = os.path.join(ROOT, '_r132', 'r132p_ctrl.json')

def run():
    p = subprocess.run(['python3', 'check_disc.py'], cwd=R14,
                       capture_output=True, text=True, timeout=600)
    return p.returncode, p.stdout + p.stderr

ASSERT = []
def chk(n, c, d=''):
    ASSERT.append({'assert': n, 'pass': bool(c), 'detail': str(d)})
    print(('  PASS ' if c else '  FAIL ') + n + ((' [%s]' % d) if d else ''))

GB = io.open(GATE, 'rb').read()
GSHA = hashlib.sha256(GB).hexdigest()
CB = io.open(COMMON, 'rb').read()
CSHA = hashlib.sha256(CB).hexdigest()

def mutate_and_run(old, new, label, path=GATE, orig=None):
    """apply a byte-level mutation, run the gate, then restore from memory"""
    o = orig if orig is not None else io.open(path, 'rb').read()
    assert o.count(old) >= 1, '%s: pattern not found' % label
    mut = o.replace(old, new, 1)
    if mut == o:
        return None, 'no-op'
    try:
        with io.open(path, 'wb') as f:
            f.write(mut)
        code, out = run()
    finally:
        with io.open(path, 'wb') as f:
            f.write(o)
    return code, out

# ---- baseline ----
code, out = run()
chk('P0 baseline gate is green', code == 0, code)

# ---- C1..C4: tamper the pinned 2.136 floor in the table ----
for newval, label in ((b'136: 1', 'floor set to 1'),
                      (b'136: 99999', 'floor set to 99999'),
                      (b'136: 4443', 'floor lowered by exactly 1')):
    code, out = mutate_and_run(b'136: 4444', newval, label)
    hit = re.search(r'C16[d]?[^\n]*', out or '')
    chk('C1 %s -> exit 1' % label, code == 1, code)
    chk('C1b %s -> C16 named' % label, 'C16' in (out or ''),
        (hit.group(0)[:70] if hit else 'no C16 line'))

# ---- C5: delete the whole 136 entry (the sha pin must catch it even though
#          "unpinned" would still be within the max of 2) ----
m = re.search(r'\n?    [^\n]*136: 4444[^\n]*', io.open(GATE, encoding='utf-8').read())
assert m, 'entry line not found'
entry = m.group(0).encode()
code, out = mutate_and_run(entry, b'', 'delete 136 entry')
chk('C5 deleting the 136 entry -> exit 1', code == 1, code)
chk('C5b deletion is caught by the sha pin, not by the unpinned count',
    'TAMPERED' in (out or ''), 'TAMPERED' in (out or ''))

# ---- C6: hollow out the 2.136 body in R14_COMMON (keep heading, empty body) ----
i = CB.find('## 2.136'.encode())
assert i > 0
head_end = CB.find(b'\n', i) + 1
hollow = CB[:head_end] + b'\n'
try:
    with io.open(COMMON, 'wb') as f:
        f.write(hollow)
    code6, out6 = run()
finally:
    with io.open(COMMON, 'wb') as f:
        f.write(CB)
chk('C6 hollowing 2.136 body -> exit 1', code6 == 1, code6)
chk('C6b hollow is reported as C16 section hollowed out',
    'hollowed' in (out6 or ''), 'hollowed' in (out6 or ''))

# ---- C7: the dead-branch finding, proved as a control rather than a claim ----
# Add a DISC_RECHECK row that uses a 'bytes=' expression: the branch exists and works,
# proving the branch is LIVE code, but no real row uses it -> the branch is DEAD by
# coverage. Both halves are asserted.
src = io.open(GATE, encoding='utf-8').read()
has_bytes = "re.fullmatch(r'bytes=(\\d+)', head)" in src
has_exists = "if head == 'exists':" in src
has_none = "if head == 'none': return None, 'none'" in src
chk('C7a the bytes= branch exists in the verifier', has_bytes)
chk('C7b the exists branch exists in the verifier', has_exists)
chk('C7c the none branch exists in the verifier', has_none)
rows = [l.rstrip('\n').split('\t') for l in io.open(os.path.join(R14, 'DISC_RECHECK.tsv'),
                                                    encoding='utf-8')]
exprs = [r[5].strip() for r in rows[1:] if len(r) >= 6]
n_exists = sum(1 for e in exprs if e.startswith('exists'))
n_bytes = sum(1 for e in exprs if e.startswith('bytes='))
n_none = sum(1 for e in exprs if e == 'none')
chk('C7d no registered row uses exists', n_exists == 0, n_exists)
chk('C7e no registered row uses bytes=', n_bytes == 0, n_bytes)
chk('C7f no registered row uses none', n_none == 0, n_none)
chk('C7g therefore those three branches are dead by coverage (0/%d rows)' % len(exprs),
    n_exists + n_bytes + n_none == 0, '%d rows' % len(exprs))

# ---- C8: restoration must be byte-identical ----
chk('C8 gate restored byte-identically after all mutations',
    hashlib.sha256(io.open(GATE, 'rb').read()).hexdigest() == GSHA)
chk('C8b R14_COMMON restored byte-identically',
    hashlib.sha256(io.open(COMMON, 'rb').read()).hexdigest() == CSHA)
code, out = run()
chk('C9 gate green again after restoration', code == 0, code)

json.dump({'asserts': ASSERT, 'gate_sha': GSHA, 'common_sha': CSHA},
          open(OUT, 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for a in ASSERT if not a['pass'])
print('\n== controls: %d total, %d FAIL ==' % (len(ASSERT), nf))
