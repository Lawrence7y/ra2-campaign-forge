import io, os, subprocess
R14 = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
T = os.path.join(R14, 'DISC_RECHECK.tsv')
F = os.path.join(R14, 'DISC_UNVERIFIABLE.tsv')
PY = r'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe'
G = os.path.join(R14, 'check_disc.py')
FBASE = io.open(F, encoding='utf-8', newline='').read()
TBASE = io.open(T, encoding='utf-8', newline='').read()

def run():
    r = subprocess.run([PY, G], capture_output=True, text=True, encoding='utf-8', errors='replace')
    fl = [l.strip() for l in (r.stdout or '').split('\n') if 'FAIL' in l]
    return r.returncode, fl

print('=== ctrl B retest: retroactive registry append ===')
extra = FBASE.rstrip('\n') + '\n11\t§2.24\t(none)\tnone\tstructurally_unverifiable\tFORGED\t2026-11-22T18:00:00+08:00\tYES\n'
io.open(F, 'w', encoding='utf-8', newline='').write(extra)
rows = [l for l in TBASE.split('\n') if l]
hdr, body = rows[0], [r.split('\t') for r in rows[1:]]
for r in body:
    if r[0] == '11':
        r[6] = '有（后续轮回跑）'
io.open(T, 'w', encoding='utf-8', newline='').write('\n'.join([hdr] + ['\t'.join(r) for r in body]) + '\n')
rc, fl = run()
print('  exit=%d' % rc)
for l in fl[:3]:
    print('   ', l[:110])
print('  -> %s' % ('CAUGHT' if rc == 1 else '!! still passed'))

io.open(F, 'w', encoding='utf-8', newline='').write(FBASE)
io.open(T, 'w', encoding='utf-8', newline='').write(TBASE)

print()
print('=== ctrl A retest: 无->有 on non-frozen row (11) ===')
rows = [l for l in TBASE.split('\n') if l]
hdr, body = rows[0], [r.split('\t') for r in rows[1:]]
for r in body:
    if r[0] == '11':
        r[6] = '有（后续轮回跑）'
io.open(T, 'w', encoding='utf-8', newline='').write('\n'.join([hdr] + ['\t'.join(r) for r in body]) + '\n')
rc, fl = run()
print('  exit=%d ; %s' % (rc, fl[0][:95] if fl else 'NO FAIL'))
print('  -> %s' % ('CAUGHT' if rc == 1 else '!! passed'))
io.open(T, 'w', encoding='utf-8', newline='').write(TBASE)

print()
print('=== restored ===')
rc, fl = run()
print('  exit=%d FAIL=%d' % (rc, len(fl)))
