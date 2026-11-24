import io, os, re, shutil, subprocess
ROOT = r'D:\Project\ra2-campaign-forge'
T = os.path.join(ROOT, r'lead\next_re_20261117_r14\DISC_RECHECK.tsv')
G = os.path.join(ROOT, r'lead\next_re_20261117_r14\check_disc.py')
PY = r'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe'

# t2-discup 交付的 20 条（纪律号 -> 校验式）。注释用 ✓(...) 追加，正则内无字面空格。
APPLY = {
 '3':  r'grep=池未加载\(未核验\)\s+0',
 '4':  r'grep=节号体例通过\s+15',
 '5':  r'grep=复合条目的锚是并集',
 '6':  r'grep=审计把「在锚里」说成「不在锚里」',
 '7':  r'grep=REFUTED-OVERSTRICT',
 '8':  r'grep=列与列之间没有同步',
 '10': r'grep=当不变量用的只有',
 '11': r'grep=控制组总判定：\*\*PASS',
 '12': r'grep=闭集合声明（纪律\s*12①）',
 '13': r'grep=控制组（四个子检查全都要）',
 '14': r'grep=checkC3_report_FAIL\.md',
 '15': r'grepcount=所在节分布=3',
 '16': r'grepcount=\*\*相同\*\*=3',
 '17': r'grepcount=out_excl=2',
 '18': r'grep=12:07.*无产物',
 '19': r'grep=逐字节闭合',
 '21': r'grep=2×2\s*溯源表',
 '23': r'grep=为什么该在一边',
 '24': r'grep=附注性限定语',
 '25': r'grep=丢\s*re\.I',
}

raw = [l for l in io.open(T, encoding='utf-8', newline='').read().split('\n') if l]
hdr, body = raw[0], [r.split('\t') for r in raw[1:]]
for r in body:
    assert len(r) == 7, r[0]
shutil.copy2(T, T + '.bak5')

applied, skipped = [], []
for r in body:
    n = r[0]
    if n in APPLY:
        old = r[5]
        r[5] = APPLY[n]
        applied.append((n, old[:34], r[5][:46]))
io.open(T, 'w', encoding='utf-8', newline='').write('\n'.join([hdr] + ['\t'.join(r) for r in body]) + '\n')

back = [l for l in io.open(T, encoding='utf-8', newline='').read().split('\n') if l]
assert len(back) - 1 == 28 and back[0].count('\t') + 1 == 7
print('applied %d rows ; readback 28 rows x 7 cols OK' % len(applied))
for a in applied:
    print('  id %-3s %-34s -> %s' % a)

def run():
    r = subprocess.run([PY, G], capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, (r.stdout or '')

rc, out = run()
fl = [l.strip() for l in out.split('\n') if 'FAIL' in l]
print()
print('gate exit=%d ; FAIL count=%d' % (rc, len(fl)))
for f in fl[:12]:
    print('   ', f[:110])
if rc == 0:
    print('   -> all applied expressions live-pass')
