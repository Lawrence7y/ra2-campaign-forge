import io, os, re, shutil, subprocess
ROOT = r'D:\Project\ra2-campaign-forge'
T = os.path.join(ROOT, r'lead\next_re_20261117_r14\DISC_RECHECK.tsv')
G = os.path.join(ROOT, r'lead\next_re_20261117_r14\check_disc.py')
PY = r'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe'
BASE = io.open(T, encoding='utf-8', newline='').read()

def run():
    r = subprocess.run([PY, G], capture_output=True, text=True, encoding='utf-8', errors='replace')
    fl = [l.strip() for l in (r.stdout or '').split('\n') if 'FAIL' in l]
    return r.returncode, fl

rows = [l for l in BASE.split('\n') if l]
hdr, body = rows[0], [r.split('\t') for r in rows[1:]]
grep_ids = [r[0] for r in body if r[5].startswith(('grep=', 'grepcount='))]
print('rows using grep/grepcount: %d -> %s' % (len(grep_ids), grep_ids))
print()
print('negative control per row: replace its expr with grep=ZZZ_NOT_EXIST_ZZZ, expect exit 1')
print()

ok = bad = 0
for n in grep_ids:
    rs = [l for l in BASE.split('\n') if l]
    h2, b2 = rs[0], [r.split('\t') for r in rs[1:]]
    for r in b2:
        if r[0] == n:
            r[5] = 'grep=ZZZ_NOT_EXIST_ZZZ'
    io.open(T, 'w', encoding='utf-8', newline='').write('\n'.join([h2] + ['\t'.join(r) for r in b2]) + '\n')
    rc, fl = run()
    io.open(T, 'w', encoding='utf-8', newline='').write(BASE)
    good = (rc == 1 and any(('id %s ' % n) in f for f in fl))
    if good:
        ok += 1
    else:
        bad += 1
        print('  !! id %-3s did NOT fail -> rc=%d fails=%s' % (n, rc, fl[:2]))
print('controls with discriminating power: %d/%d (bad=%d)' % (ok, len(grep_ids), bad))
rc, _ = run()
print('baseline restored exit=%d (expect 0)' % rc)
