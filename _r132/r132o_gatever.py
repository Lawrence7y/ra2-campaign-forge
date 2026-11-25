#!/usr/bin/env python3
# R132 r132o: update DISC_RECHECK row 20 to R132, then verify the gate is green.
# This exists because r132n bumped GATE_VER before updating the registration row,
# so its own assert fired mid-flight. The floor pin it made is correct and stays;
# what remains is the row-20 sync. Recorded as S-217.
import hashlib, io, json, os, re, subprocess, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
TSV = os.path.join(R14, 'DISC_RECHECK.tsv')
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
OUT = os.path.join(ROOT, '_r132', 'r132o_gatever.json')

def run_gate():
    p = subprocess.run(['python3', 'check_disc.py'], cwd=R14,
                       capture_output=True, text=True, timeout=600)
    return p.returncode, p.stdout + p.stderr

tb = io.open(TSV, 'rb').read()
tsha = hashlib.sha256(tb).hexdigest()
cr_before = tb.count(b'\r\n')
dst = os.path.join(BASE, 'R132.before_DISC_RECHECK.tsv_%s.bak' % time.strftime('%Y%m%d_%H%M%S'))
fd = os.open(dst, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
with os.fdopen(fd, 'wb') as f:
    f.write(tb)
assert hashlib.sha256(io.open(dst, 'rb').read()).hexdigest() == tsha
print('tsv backup:', os.path.basename(dst), 'CR=%d' % cr_before)

# byte-level replace of the single registration cell
old = b"grep=(?m)^GATE_VER = 'R131'"
new = b"grep=(?m)^GATE_VER = 'R132'"
assert tb.count(old) == 1, 'row-20 pattern count = %d' % tb.count(old)
nb = tb.replace(old, new, 1)
try:
    with io.open(TSV, 'wb') as f:
        f.write(nb)
    back = io.open(TSV, 'rb').read()
    assert back == nb, 'readback mismatch'
    assert back.count(b'\r\n') == cr_before, 'CR drifted %d -> %d' % (cr_before, back.count(b'\r\n'))
except Exception:
    with io.open(TSV, 'wb') as f:
        f.write(tb)
    raise
print('row 20 updated; CR kept at', back.count(b'\r\n'))

code, out = run_gate()
print(out.strip().splitlines()[-6] if out.strip() else '')
for ln in out.splitlines():
    if 'C16 per-section' in ln or 'C10 self-check' in ln or 'C7 live' in ln:
        print('  ', ln.strip())
rec = {'tsv_backup': dst, 'tsv_sha_before': tsha, 'gate_exit': code,
       'gate_tail': '\n'.join(out.strip().splitlines()[-10:])}
m16 = re.search(r'C16 per-section floors: (\d+) sections measured \(pinned (\d+)\), '
                r'hollow/deficient (\d+), missing (\d+), unpinned (\d+), min margin (\d+)', out)
if m16:
    rec['measured'], rec['pinned'], rec['hollow'], rec['missing'], rec['unpinned'], rec['margin'] = \
        [int(x) for x in m16.groups()]
m10 = re.search(r'C10 self-check: (ok\(R\d+\))', out)
rec['c10'] = m10.group(1) if m10 else None
m7 = re.search(r'C7 live-checks passed (\d+)', out)
rec['c7'] = int(m7.group(1)) if m7 else None
json.dump(rec, open(OUT, 'w'), ensure_ascii=False, indent=1)
print('c10=%s c7=%s exit=%d' % (rec['c10'], rec['c7'], code))
assert code == 0, 'gate still red'
assert rec['c10'] == 'ok(R132)', rec['c10']
assert rec.get('unpinned') == 0, rec.get('unpinned')
print('OK')
