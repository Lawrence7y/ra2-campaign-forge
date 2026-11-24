import io, os, shutil, subprocess
ROOT = r'D:\Project\ra2-campaign-forge'
G = os.path.join(ROOT, r'lead\next_re_20261117_r14\check_disc.py')
M = os.path.join(ROOT, r'lead\next_re_20261117_r14\DISC_NS_MAP.tsv')
PY = r'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe'

def run():
    r = subprocess.run([PY, G], capture_output=True, text=True, encoding='utf-8', errors='replace')
    fl = [l.strip() for l in (r.stdout or '').split('\n') if 'FAIL' in l]
    nt = [l.strip() for l in (r.stdout or '').split('\n') if 'C6' in l]
    return r.returncode, fl, nt

base = io.open(M, encoding='utf-8', newline='').read()
rows = [l for l in base.split('\n') if l]

print('baseline:')
rc, fl, nt = run()
for n in nt: print('   ', n)
print('    exit=%d' % rc)

# 反控 1：删一行映射（覆盖不全）
shutil.copy2(M, M + '.bak')
io.open(M, 'w', encoding='utf-8', newline='').write('\n'.join(rows[:-1]) + '\n')
rc, fl, nt = run()
print()
print('ctrl1: map rows %d -> %d (coverage gap)' % (len(rows) - 1, len(rows) - 2))
print('    exit=%d ; %s' % (rc, fl[0][:100] if fl else '(no FAIL)'))

# 反控 2：映射表整个删掉
os.remove(M)
rc, fl, nt = run()
print()
print('ctrl2: DISC_NS_MAP.tsv removed')
print('    exit=%d ; %s' % (rc, fl[0][:100] if fl else '(no FAIL)'))

shutil.move(M + '.bak', M)
rc, fl, nt = run()
print()
print('restored: exit=%d (expect 0)' % rc)
