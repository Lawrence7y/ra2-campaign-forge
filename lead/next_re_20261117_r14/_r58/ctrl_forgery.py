import io, os, shutil, subprocess
R14 = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
T = os.path.join(R14, 'DISC_RECHECK.tsv')
F = os.path.join(R14, 'DISC_UNVERIFIABLE.tsv')
PY = r'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe'
G = os.path.join(R14, 'check_disc.py')
BASE = io.open(T, encoding='utf-8', newline='').read()
FBASE = io.open(F, encoding='utf-8', newline='').read()

def run():
    r = subprocess.run([PY, G], capture_output=True, text=True, encoding='utf-8', errors='replace')
    fl = [l.strip() for l in (r.stdout or '').split('\n') if 'FAIL' in l]
    return r.returncode, fl

print('=== baseline ===')
rc, fl = run()
print('  exit=%d FAIL=%d' % (rc, len(fl)))

# ---- 反造控 A：非冻结行（纪律 11，第7列原为「无」）改成「有」----
rows = [l for l in BASE.split('\n') if l]
hdr, body = rows[0], [r.split('\t') for r in rows[1:]]
for r in body:
    if r[0] == '11':
        print()
        print('ctrl A: discipline 11 later-column %r -> "有（后续轮回跑）"' % r[6][:22])
        r[6] = '有（后续轮回跑）'
io.open(T, 'w', encoding='utf-8', newline='').write('\n'.join([hdr] + ['\t'.join(r) for r in body]) + '\n')
rc, fl = run()
print('  exit=%d ; %s' % (rc, fl[0][:95] if fl else '(NO FAIL — forgery not caught!)'))
print('  -> %s' % ('OK caught' if rc == 1 else '!! FORGERY PASSED'))
io.open(T, 'w', encoding='utf-8', newline='').write(BASE)

# ---- 反造控 B：把纪律 11 加进冻结档（追溯伪造入类）----
print()
print('ctrl B: append discipline 11 to frozen registry (retroactive membership)')
extra = FBASE.rstrip('\n') + '\n11\t§2.24\t(none)\tnone\tstructurally_unverifiable\tFORGED retroactive entry\t2026-11-22T18:00:00+08:00\tYES\n'
io.open(F, 'w', encoding='utf-8', newline='').write(extra)
rows2 = [l for l in BASE.split('\n') if l]
hdr2, body2 = rows2[0], [r.split('\t') for r in rows2[1:]]
for r in body2:
    if r[0] == '11':
        r[6] = '有（后续轮回跑）'
io.open(T, 'w', encoding='utf-8', newline='').write('\n'.join([hdr2] + ['\t'.join(r) for r in body2]) + '\n')
rc, fl = run()
print('  exit=%d ; %s' % (rc, fl[0][:95] if fl else '(NO FAIL — registry tampering not caught!)'))
print('  -> %s' % ('caught' if rc == 1 else '!! REGISTRY TAMPERING PASSED (weakness)'))
io.open(F, 'w', encoding='utf-8', newline='').write(FBASE)
io.open(T, 'w', encoding='utf-8', newline='').write(BASE)

print()
print('=== restored ===')
rc, fl = run()
print('  exit=%d FAIL=%d' % (rc, len(fl)))
