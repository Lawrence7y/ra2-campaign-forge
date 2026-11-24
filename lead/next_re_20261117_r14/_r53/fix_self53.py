import io, os, shutil, subprocess
R14 = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
T = os.path.join(R14, 'DISC_RECHECK.tsv')
PY = r'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe'
G = os.path.join(R14, 'check_disc.py')

raw = [l for l in io.open(T, encoding='utf-8', newline='').read().split('\n') if l]
hdr, body = raw[0], [r.split('\t') for r in raw[1:]]
shutil.copy2(T, T + '.bakR53')
new_expr = "grep=(?m)^GATE_VER = 'R53'"
for r in body:
    if r[0] == '20':
        print('id20: %r -> %r' % (r[5], new_expr))
        r[5] = new_expr
io.open(T, 'w', encoding='utf-8', newline='').write('\n'.join([hdr] + ['\t'.join(r) for r in body]) + '\n')
print('readback rows:', len([l for l in io.open(T, encoding='utf-8', newline='').read().split('\n') if l]) - 1)

r = subprocess.run([PY, G], capture_output=True, text=True, encoding='utf-8', errors='replace')
out = r.stdout or ''
n_fail = sum(1 for l in out.split('\n') if 'FAIL' in l)
print()
print('exit=%d ; FAIL total=%d' % (r.returncode, n_fail))
for l in out.split('\n'):
    if 'C11' in l or 'C7 live' in l or 'C10' in l or 'PASS' in l:
        print('   ', l.strip()[:130])
