#!/usr/bin/env python3
# R132 r132n: pin the new 2.136 section into C16_FLOORS, then re-run controls.
# Discipline: back up the gate, edit in one atomic write with sha assertion,
# recompute C16_FLOORS_SHA256 from the MEASURED table (never hand-typed),
# and require the gate to go unpinned 1 -> 0. Must be idempotent-safe:
# if 136 is already present, refuse rather than append a duplicate (S-211).
import hashlib, io, json, os, re, subprocess, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
GATE = os.path.join(R14, 'check_disc.py')
COMMON = os.path.join(R14, 'R14_COMMON.md')
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
OUT = os.path.join(ROOT, '_r132', 'r132n_c16pin.json')

def run_gate():
    p = subprocess.run(['python3', 'check_disc.py'], cwd=R14,
                       capture_output=True, text=True, timeout=600)
    return p.returncode, p.stdout + p.stderr

# ---- measure the section body ----
rc = io.open(COMMON, encoding='utf-8').read()
i = rc.find('## 2.136')
assert i >= 0, '2.136 not found'
body = rc[i:]
nbytes = len(body.encode('utf-8'))
half = nbytes // 2
print('2.136 measured body = %d B ; half-rule floor = %d' % (nbytes, half))

gate_src = io.open(GATE, encoding='utf-8').read()
assert '136:' not in re.search(r'C16_FLOORS = \{(.*?)\n\}', gate_src, re.S).group(1), \
    '136 already pinned -- refusing to duplicate (S-211)'

# ---- back up the gate ----
gb = io.open(GATE, 'rb').read()
gsha = hashlib.sha256(gb).hexdigest()
dst = os.path.join(BASE, 'R132.before_check_disc.py_%s.bak' % time.strftime('%Y%m%d_%H%M%S'))
fd = os.open(dst, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
with os.fdopen(fd, 'wb') as f:
    f.write(gb)
assert hashlib.sha256(io.open(dst, 'rb').read()).hexdigest() == gsha
print('gate backup:', os.path.basename(dst), gsha[:12])

# ---- rebuild the table text with 136 appended, then recompute the sha from it ----
m = re.search(r'C16_FLOORS = \{.*?\n\}', gate_src, re.S)
tbl_src = m.group(0)
# evaluate the dict to get exact pairs
ns = {}
exec(tbl_src, ns)
floors = dict(ns['C16_FLOORS'])
assert 136 not in floors
floors[136] = half

# regenerate the literal block in the same 10-per-line style
items = sorted(floors.items())
lines = []
for r in range(0, len(items), 5):
    chunk = items[r:r + 5]
    lines.append('    ' + ', '.join('%d: %d' % (k, v) for k, v in chunk) + ',')
new_tbl = 'C16_FLOORS = {\n' + '\n'.join(lines) + '\n}'

norm = '\n'.join('%d:%d' % (k, floors[k]) for k in sorted(floors))
new_sha = hashlib.sha256(norm.encode('utf-8')).hexdigest()
print('new C16_FLOORS_SHA256 =', new_sha[:16], '(%d entries)' % len(floors))

new_gate = gate_src.replace(tbl_src, new_tbl, 1)
old_sha_const = re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'", gate_src).group(1)
new_gate = new_gate.replace(old_sha_const, new_sha, 1)
# bump GATE_VER and the DISC_RECHECK row 20 registration line
new_gate = new_gate.replace("GATE_VER = 'R131'", "GATE_VER = 'R132'", 1)
assert new_gate != gate_src

rec = {'section_bytes': nbytes, 'floor': half, 'entries_before': len(floors) - 1,
       'entries_after': len(floors), 'sha_before': old_sha_const, 'sha_after': new_sha,
       'gate_backup': dst}

# ---- atomic write with readback ----
try:
    with io.open(GATE, 'w', encoding='utf-8', newline='') as f:
        f.write(new_gate)
    back = io.open(GATE, encoding='utf-8').read()
    assert back == new_gate, 'readback mismatch'
except Exception:
    with io.open(GATE, 'wb') as f:
        f.write(gb)
    raise

# ---- gate must now be green with unpinned 0 ----
code, out = run_gate()
rec['gate_exit'] = code
rec['gate_out_tail'] = '\n'.join(out.strip().splitlines()[-8:])
print(out.strip().splitlines()[-3] if out.strip() else '')
m16 = re.search(r'C16 per-section floors: (\d+) sections measured \(pinned (\d+)\), '
                r'hollow/deficient (\d+), missing (\d+), unpinned (\d+), min margin (\d+)', out)
assert m16, 'C16 line not found'
rec['measured'], rec['pinned'], rec['hollow'], rec['missing'], rec['unpinned'], rec['margin'] = \
    [int(x) for x in m16.groups()]
print('measured=%d pinned=%d unpinned=%d exit=%d' %
      (rec['measured'], rec['pinned'], rec['unpinned'], code))

assert code == 0, 'gate not green'
assert rec['unpinned'] == 0, 'still unpinned %d' % rec['unpinned']
assert rec['pinned'] == rec['measured'], 'not every section pinned'
assert rec['sha_after'][:16] in out, 'new sha not echoed by gate'

json.dump(rec, open(OUT, 'w'), ensure_ascii=False, indent=1)
print('OK; wrote', OUT)
