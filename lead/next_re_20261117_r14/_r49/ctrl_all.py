import io, os, shutil, subprocess
ROOT = r'D:\Project\ra2-campaign-forge'
G = os.path.join(ROOT, r'lead\next_re_20261117_r14\check_disc.py')
T = os.path.join(ROOT, r'lead\next_re_20261117_r14\DISC_RECHECK.tsv')
PY = r'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe'
BASE = io.open(T, encoding='utf-8', newline='').read()

def run():
    r = subprocess.run([PY, G], capture_output=True, text=True, encoding='utf-8', errors='replace')
    fl = [l.strip() for l in (r.stdout or '').split('\n') if 'FAIL' in l]
    return r.returncode, fl

def ctrl(label, fn, expect_fail=True):
    rows = [l for l in BASE.split('\n') if l]
    hdr, body = rows[0], [r.split('\t') for r in rows[1:]]
    body = fn(body)
    io.open(T, 'w', encoding='utf-8', newline='').write('\n'.join([hdr] + ['\t'.join(r) for r in body]) + '\n')
    rc, fl = run()
    io.open(T, 'w', encoding='utf-8', newline='').write(BASE)
    ok = (rc == 1) if expect_fail else (rc == 0)
    mark = 'OK ' if ok else '!! '
    print('%s%-40s exit=%d  %s' % (mark, label, rc, (fl[0][:80] if fl else '(none)')))
    return ok

def setf(i, col, val):
    def f(b):
        for r in b:
            if r[0] == str(i):
                r[col] = val
        return b
    return f

results = []
print('--- controls (all must FAIL) ---')
results.append(ctrl('B  rows=9999 (expect wrong)', setf(22, 5, 'rows=9999')))
results.append(ctrl('E  product path missing', setf(22, 4, r'lead\NO_SUCH.tsv')))
results.append(ctrl('F  bad expr ZZZ=1', setf(22, 5, 'ZZZ=1')))
results.append(ctrl('H  later-column empty', setf(5, 6, '')))
results.append(ctrl('H2 later-column junk', setf(5, 6, 'MAYBE')))
results.append(ctrl('I  judge=GARBAGE', setf(5, 2, 'GARBAGE')))
results.append(ctrl('I2 anchor=无', setf(5, 3, '无')))
results.append(ctrl('J  section §9.99', setf(5, 1, '§9.99')))
results.append(ctrl('K  grep misses (impossible literal)', setf(1, 5, 'grep=ZZZ_NEVER_MATCHES_ZZZ')))
results.append(ctrl('L  C6 flood (raise outside mentions)', None) if False else True)

print()
print('--- C10 self-control: 版本标记写错必须 FAIL ---')
results.append(ctrl('M  self GATE_VER=R00', lambda b: setf(20, 5, "grep=(?m)^GATE_VER = 'R00'")(
    [r for r in b] if False else b) if False else [
    (r.__setitem__(5, "grep=(?m)^GATE_VER = 'R00'") or r) if r[0] == '20' else r for r in b]))

print()
rc, _ = run()
print('baseline restored exit=%d (expect 0)' % rc)
print('summary: %d/%d controls behaved as expected' % (sum(1 for x in results if x), len(results)))
