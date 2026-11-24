import io, os, re, shutil, subprocess
R14 = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
T = os.path.join(R14, 'DISC_RECHECK.tsv')
PY = r'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe'
G = os.path.join(R14, 'check_disc.py')
V = os.path.join(R14, 'recheck_verify.py')

# 1) 同步自注册 GATE_VER -> R55
raw = [l for l in io.open(T, encoding='utf-8', newline='').read().split('\n') if l]
hdr, body = raw[0], [r.split('\t') for r in raw[1:]]
shutil.copy2(T, T + '.bakR55')
for r in body:
    if r[0] == '20':
        r[5] = "grep=(?m)^GATE_VER = 'R55'"
io.open(T, 'w', encoding='utf-8', newline='').write('\n'.join([hdr] + ['\t'.join(r) for r in body]) + '\n')
print('row20 -> GATE_VER R55')

# 2) 检查窗口表现状
v = io.open(V, encoding='utf-8').read()
wins = re.findall(r"\((\d+), '(\d{6})', '(\d{6})'", v)
print('窗口表覆盖轮次:', [w[0] for w in wins])

r = subprocess.run([PY, G], capture_output=True, text=True, encoding='utf-8', errors='replace')
out = r.stdout or ''
nf = sum(1 for l in out.split('\n') if 'FAIL' in l)
print()
print('gate exit=%d ; FAIL=%d' % (r.returncode, nf))
for l in out.split('\n'):
    if 'C11 col7' in l or 'C10' in l or 'C7 live' in l:
        print('  ', l.strip()[:130])
# 分类当前 FAIL 原因
cats = {'line_count=2': 0, 'no round window': 0, 'line_count=0': 0, 'GATE_VER': 0, 'other': 0}
for l in out.split('\n'):
    if 'FAIL' not in l: continue
    if 'line_count=2' in l: cats['line_count=2'] += 1
    elif 'no round window' in l: cats['no round window'] += 1
    elif 'line_count=0' in l: cats['line_count=0'] += 1
    elif 'GATE_VER' in l: cats['GATE_VER'] += 1
    else: cats['other'] += 1
print()
print('FAIL 分类:', cats)
