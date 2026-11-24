import io, os, re, shutil, subprocess
ROOT = r'D:\Project\ra2-campaign-forge'
G = os.path.join(ROOT, r'lead\next_re_20261117_r14\check_disc.py')
T = os.path.join(ROOT, r'lead\next_re_20261117_r14\DISC_RECHECK.tsv')
PY = r'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe'
VER = 'R49'

# 1) 确保 GATE_VER 定义存在
src = io.open(G, encoding='utf-8').read()
if '\nGATE_VER = ' not in src:
    anchor = 'SELF = os.path.abspath(__file__)'
    assert anchor in src
    src = src.replace(anchor, anchor + "\nGATE_VER = '%s'" % VER, 1)
    io.open(G, 'w', encoding='utf-8').write(src)
    print('added GATE_VER =', VER)
else:
    print('GATE_VER already present')

# 2) 纪律 20 行 -> grep 版本标记
raw = [l for l in io.open(T, encoding='utf-8', newline='').read().split('\n') if l]
hdr, body = raw[0], [r.split('\t') for r in raw[1:]]
shutil.copy2(T, T + '.bak4')
expr = "grep=(?m)^GATE_VER = '%s'" % VER
for r in body:
    if r[0] == '20':
        print('id20 old:', r[5][:50])
        r[5] = expr
        print('id20 new:', r[5])
io.open(T, 'w', encoding='utf-8', newline='').write('\n'.join([hdr] + ['\t'.join(r) for r in body]) + '\n')
back = [l for l in io.open(T, encoding='utf-8', newline='').read().split('\n') if l]
print('readback rows=%d cols=%d' % (len(back) - 1, back[0].count('\t') + 1))

r = subprocess.run([PY, G], capture_output=True, text=True, encoding='utf-8', errors='replace')
print()
print(r.stdout or '')
print('exit=%d' % r.returncode)
