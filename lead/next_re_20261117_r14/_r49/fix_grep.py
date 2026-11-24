import io, os, re, shutil, subprocess
ROOT = r'D:\Project\ra2-campaign-forge'
T = os.path.join(ROOT, r'lead\next_re_20261117_r14\DISC_RECHECK.tsv')
PY = r'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe'
G = os.path.join(ROOT, r'lead\next_re_20261117_r14\check_disc.py')

# 把「对增长型文档用固定字节数」的 3 行改成 grep=（稳定标记，内容级且不受增长影响）
# 纪律 1/2/9 都指向 R14_COMMON.md
NEW = {
 '1': r'grep=(?m)^\*\*\u7eaa\u5f8b 1 \u00b7',
 '2': r'grep=(?m)^\*\*\u7eaa\u5f8b 2 \u00b7',
 '9': r'grep=(?m)^\u21d2 \*\*\u7eaa\u5f8b 9 \u00b7',
}
raw = [l for l in io.open(T, encoding='utf-8', newline='').read().split('\n') if l]
hdr, body = raw[0], [r.split('\t') for r in raw[1:]]
shutil.copy2(T, T + '.bak2')
chg = []
for r in body:
    if r[0] in NEW:
        chg.append((r[0], r[5][:40], NEW[r[0]][:46]))
        r[5] = NEW[r[0]]
io.open(T, 'w', encoding='utf-8', newline='').write('\n'.join([hdr] + ['\t'.join(r) for r in body]) + '\n')
for c in chg:
    print('  id %-3s  %-40s -> %s' % c)
back = [l for l in io.open(T, encoding='utf-8', newline='').read().split('\n') if l]
print('readback: %d rows, %d cols' % (len(back) - 1, back[0].count('\t') + 1))

r = subprocess.run([PY, G], capture_output=True, text=True, encoding='utf-8', errors='replace')
print()
print((r.stdout or '')[:1600])
print('exit=%d' % r.returncode)
