# -*- coding: utf-8 -*-
# R59-T2-AUDITGATE2 counter-controls (backup -> mutate -> run -> restore -> verify)
import os, sys, io, re, hashlib, subprocess, shutil
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
except Exception:
    pass
R14 = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
REPORT = os.path.join(R14, 'R17_R95_T2_AUDITGATE2')
os.makedirs(REPORT, exist_ok=True)
TSV = os.path.join(R14, 'DISC_UNVERIFIABLE.tsv')
CHK = os.path.join(R14, 'check_disc.py')
RC  = os.path.join(R14, 'R14_COMMON.md')
DR  = os.path.join(R14, 'DISC_RECHECK.tsv')

def sha(p):
    with io.open(p, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def gate():
    r = subprocess.run([sys.executable, CHK], cwd=R14,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return r.returncode, r.stdout.decode('utf-8', 'replace')

def focus(out):
    return [l for l in out.splitlines()
            if ('C11' in l or '[exit' in l or 'C10 self' in l or 'C7 live' in l)]

bak = {}
for p in (TSV, CHK, RC):
    b = os.path.join(REPORT, 'bak_' + os.path.basename(p))
    shutil.copy2(p, b)
    bak[p] = (b, sha(p))
    print('BACKUP %-24s sha256=%s' % (os.path.basename(p), bak[p][1]))

def restore(p):
    b, h = bak[p]
    shutil.copy2(b, p)
    ok = (sha(p) == h)
    print('RESTORED %-22s sha256=%s %s' % (os.path.basename(p), sha(p)[:16],
                                          'OK' if ok else '!!!MISMATCH!!!'))
    return ok

rc, out = gate()
print('\n=== BASELINE exit=%d ===' % rc)
for l in focus(out): print('   ', l)

NEWROW = '99\tx2.99\tx\ty\tstructure\ttest\t2026-11-22T17:50:21+08:00\tno\n'

# ---------- Q2-1 ----------
print('\n=== Q2-1  add row to DISC_UNVERIFIABLE.tsv (expect FAIL) ===')
try:
    with io.open(TSV, 'a', encoding='utf-8', newline='') as f:
        f.write(NEWROW)
    print('   tsv sha now', sha(TSV)[:16])
    rc, out = gate()
    print('   exit=%d' % rc)
    for l in focus(out): print('   ', l)
finally:
    restore(TSV)
rc, out = gate()
print('   after-restore exit=%d' % rc)

# ---------- Q2-2 ----------
print('\n=== Q2-2  add row + sync FREEZE_SHA256 (what happens?) ===')
try:
    with io.open(TSV, 'a', encoding='utf-8', newline='') as f:
        f.write(NEWROW)
    newh = sha(TSV)
    with io.open(CHK, 'r', encoding='utf-8', newline='') as f:
        src = f.read()
    src2, n = re.subn(r"FREEZE_SHA256 = '[0-9a-f]{64}'",
                      "FREEZE_SHA256 = '%s'" % newh, src, count=1)
    assert n == 1, 'FREEZE_SHA256 replacement count=%d' % n
    with io.open(CHK, 'w', encoding='utf-8', newline='') as f:
        f.write(src2)
    print('   tsv sha=%s ; FREEZE_SHA256 -> %s' % (newh[:16], newh[:16]))
    rc, out = gate()
    print('   exit=%d' % rc)
    for l in focus(out): print('   ', l)
finally:
    restore(TSV); restore(CHK)
rc, out = gate()
print('   after-restore exit=%d' % rc)

# ---------- Q2-3 ----------
print('\n=== Q2-3  append COMPLIANT self-desc line to frozen discipline 1 product ===')
row3 = None
with io.open(DR, 'r', encoding='utf-8', newline='') as f:
    for ln in f:
        c = ln.rstrip('\n').split('\t')
        if c and c[0].strip() == '1':
            row3 = c[3]
            break
print('   discipline-1 row[3] anchor present =', bool(row3))
h = hashlib.sha256(row3.encode('utf-8')).hexdigest()
line = ('DISC_RECHECK discipline=1 round=R55 at=2026-11-22T17:39:19+08:00 '
        'anchors=sha256:%s conclusion=PASS\n' % h)
print('   appended prefix:', line.strip()[:60])
try:
    with io.open(RC, 'a', encoding='utf-8', newline='') as f:
        f.write(line)
    rc, out = gate()
    print('   exit=%d' % rc)
    for l in focus(out): print('   ', l)
    sys.path.insert(0, R14)
    import recheck_verify as vv
    row = None
    with io.open(DR, 'r', encoding='utf-8', newline='') as f:
        for ln in f:
            c = ln.rstrip('\n').split('\t')
            if c and c[0].strip() == '1':
                row = c; break
    ok, detail = vv.verify_recheck_line(R14, row)
    print('   verifier ok=%s detail=%s' % (ok, detail[:120]))
finally:
    restore(RC)
rc, out = gate()
print('   after-restore exit=%d' % rc)

print('\n=== FINAL INTEGRITY ===')
for p in (TSV, CHK, RC):
    print('   %-24s %s %s' % (os.path.basename(p), sha(p)[:16],
                             'UNCHANGED' if sha(p) == bak[p][1] else 'CHANGED!!!'))
