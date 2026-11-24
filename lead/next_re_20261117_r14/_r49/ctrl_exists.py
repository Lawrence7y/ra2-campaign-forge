import io, os, subprocess, shutil
PY = r'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe'
G = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\check_disc.py'
tgt = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R72_T1_CLEANSCALE\REPORT.md'

bak = tgt + '.ctrl48'
shutil.copy2(tgt, bak)
orig = os.path.getsize(tgt)
try:
    io.open(tgt, 'w', encoding='utf-8').write('x')
    r = subprocess.run([PY, G], capture_output=True, text=True, encoding='utf-8', errors='replace')
    fails = [l for l in (r.stdout or '').split('\n') if 'FAIL' in l]
    print("ctrl B' : exists product %d B -> 1 B ; exit=%d" % (orig, r.returncode))
    for f in fails[:3]:
        print('   ', f.strip()[:110])
    print('   -> expected FAIL (exit 1)' if r.returncode == 1 else '   -> STILL SILENT PASS (bad)')
finally:
    shutil.move(bak, tgt)

r2 = subprocess.run([PY, G], capture_output=True, text=True, encoding='utf-8', errors='replace')
print('restored baseline exit=%d (expect 0)' % r2.returncode)
print('restored size=%d (expect %d) %s' % (os.path.getsize(tgt), orig,
                                           'OK' if os.path.getsize(tgt) == orig else 'MISMATCH'))
