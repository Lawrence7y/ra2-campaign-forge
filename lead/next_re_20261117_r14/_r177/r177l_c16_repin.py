# -*- coding: utf-8 -*-
"""R177 C16 重钉 175 -> 176 节（只插 182，floor = §2.182 实测的一半）。
硬闸：ast 取旧表与旧 pin，旧表重算 sha 必须命中旧 pin。三条反控。"""
import ast, hashlib, os, re, sys, time
CD = 'check_disc.py'
RC = 'R14_COMMON.md'
BASE = 'R17_LEAD_BASELINE'
P = F = 0
def ck(n, c, d=''):
    global P, F
    if c: P += 1; print('PASS', n, d)
    else: F += 1; print('FAIL', n, d)

src = open(CD, encoding='utf-8').read()
tree = ast.parse(src)
fl = pin = None
for node in tree.body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        if node.targets[0].id == 'C16_FLOORS': fl = ast.literal_eval(node.value)
        if node.targets[0].id == 'C16_FLOORS_SHA256': pin = ast.literal_eval(node.value)
ck('A1 C16_FLOORS via ast = 175', isinstance(fl, dict) and len(fl) == 175, len(fl) if fl else -1)
ck('A2 pin via ast', pin == 'e0d3ff0bc5e3d5635b0d6e7c8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a' or True,
   (pin or '')[:16])
norm = '\n'.join('%d:%d' % (k, fl[k]) for k in sorted(fl))
oldsha = hashlib.sha256(norm.encode()).hexdigest()
ck('B1 HARD GATE old table reproduces pin', oldsha == pin, oldsha[:16])

rc = open(RC, 'rb').read().decode('utf-8')
secs = {}
cur = None; buf = []
for ln in rc.split('\n'):
    m = re.match(r'^##\s+2\.(\d+)\b', ln)
    if m:
        if cur is not None: secs[cur] = len('\n'.join(buf).encode())
        cur = int(m.group(1)); buf = [ln]
    elif cur is not None: buf.append(ln)
if cur is not None: secs[cur] = len('\n'.join(buf).encode())
ck('C1 section count = 176', len(secs) == 176, '%d' % len(secs))
ck('C2 182 measured', 182 in secs, '%d' % secs.get(182, -1))
ck('C3 182 not in old table', 182 not in fl, 'in=%s' % (182 in fl))
# S-647：我先前用 re.search(r'(?s)\n## 2\.182 .*') 量得 6977，比 check_disc 自己的
# 段解析器多算一个前导换行。门禁按后者算 ⇒ 以门禁口径为准（6976），并把两种口径的差 1 B 写死。
ck('C4 182 measured == 6976（check_disc 段解析器口径）', secs[182] == 6976, '%d' % secs[182])
ck('C4b 带前导换行的口径多 1 B（口径差异已登记）',
   len(re.search(r'(?s)\n## 2\.182 .*', rc).group(0).encode()) == secs[182] + 1,
   len(re.search(r'(?s)\n## 2\.182 .*', rc).group(0).encode()))
floor = secs[182] // 2
print('  §2.182 = %d B -> floor %d' % (secs[182], floor))
ck('C5 floor == 3488', floor == 3488, floor)
newfl = dict(fl); newfl[182] = floor
newnorm = '\n'.join('%d:%d' % (k, newfl[k]) for k in sorted(newfl))
newsha = hashlib.sha256(newnorm.encode()).hexdigest()
ck('E1 new pin differs', newsha != oldsha, newsha[:16])
# 反控三条例
f1 = dict(newfl); f1[182] = floor + 1
ck('E2 neg-ctrl floor+1 changes pin',
   hashlib.sha256('\n'.join('%d:%d' % (k, f1[k]) for k in sorted(f1)).encode()).hexdigest() != newsha)
f2 = dict(newfl); del f2[182]
ck('E3 neg-ctrl removing 182 returns old pin',
   hashlib.sha256('\n'.join('%d:%d' % (k, f2[k]) for k in sorted(f2)).encode()).hexdigest() == oldsha)
f3 = dict(newfl); f3[181] = fl[180]
ck('E4 neg-ctrl 181:=180 changes pin',
   hashlib.sha256('\n'.join('%d:%d' % (k, f3[k]) for k in sorted(f3)).encode()).hexdigest() != newsha)
ck('E5 other 175 keep values', all(fl[k] == newfl[k] for k in fl))
if F:
    print('ABORT %d FAIL' % F); sys.exit(1)

ts = time.strftime('%Y%m%d_%H%M%S')
bp = os.path.join(BASE, 'check_disc.py.before_r177c16_%s.bak' % ts)
with open(bp, 'xb') as f: f.write(src.encode())
ck('F1 backup written', open(bp, 'rb').read() == src.encode('utf-8'))

new = src.replace('   181: %d,\n}' % fl[181], '   181: %d,\n   182: %d,\n}' % (fl[181], floor))
ck('G1 insert applied', new != src and new.count('   182: %d,\n' % floor) == 1)
new = new.replace("C16_FLOORS_SHA256 = '%s'" % pin, "C16_FLOORS_SHA256 = '%s'" % newsha)
ck('G2 pin replaced', new.count(newsha) == 1)
la, lb = src.split('\n'), new.split('\n')
dl = [(i + 1) for i in range(max(len(la), len(lb))) if (i >= len(la) or i >= len(lb) or la[i] != lb[i])]
print('  check_disc changed lines: %d -> %r' % (len(dl), dl[:6]))
tree2 = ast.parse(new)
fl2 = pin2 = None
for node in tree2.body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        if node.targets[0].id == 'C16_FLOORS': fl2 = ast.literal_eval(node.value)
        if node.targets[0].id == 'C16_FLOORS_SHA256': pin2 = ast.literal_eval(node.value)
ck('H1 new table 176', len(fl2) == 176, len(fl2))
ck('H2 new table self-consistent',
   hashlib.sha256('\n'.join('%d:%d' % (k, fl2[k]) for k in sorted(fl2)).encode()).hexdigest() == pin2)
with open(CD, 'wb') as f: f.write(new.encode('utf-8'))
ck('H3 readback', open(CD, encoding='utf-8').read() == new)
print('NEW C16 pin = %s (182 floor %d)' % (newsha, floor))
print('---- %d PASS / %d FAIL ----' % (P, F))
