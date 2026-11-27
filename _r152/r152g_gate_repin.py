#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R152 门禁回归：C16_FLOORS 纳 157（floor = 实测含标题体的一半），重钉 C16_FLOORS_SHA256，
GATE_VER R151 -> R152，同步 DISC_RECHECK[DISC_UNVERIFIABLE] id20 锚点，重钉 FREEZE_SHA256，跑门禁。
"""
import hashlib, io, os, re, subprocess, sys

D = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
G = os.path.join(D, 'check_disc.py')
DR = os.path.join(D, 'DISC_RECHECK.tsv')
DU = os.path.join(D, 'DISC_UNVERIFIABLE.tsv')
fail = []


def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok:
        fail.append(n)
    return ok


raw = open(G, 'rb').read()
print('check_disc.py pre sha=%s bytes=%d' % (hashlib.sha256(raw).hexdigest()[:16], len(raw)))
s = raw.decode('utf-8')
ck('pre GATE_VER = R151', "GATE_VER = 'R151'" in s)
ck('pre C16_FLOORS 末项 156: 5873', re.search(r'156:\s*5873', s) is not None)
ck('pre C16_FLOORS_SHA256 = 5c67b295…',
   "C16_FLOORS_SHA256 = '5c67b2952a42cc805fcc10e62b4f002243aa691cfca92fc1bddecc92ce3601c5'" in s)

# ---------- 实测 §2.157 含标题体 ----------
rc = io.open(os.path.join(D, 'R14_COMMON.md'), encoding='utf-8', newline='').read()
cur, buf, out = None, [], {}
for l in rc.split('\n'):
    m = re.match(r'^##\s+2\.(\d+)\b', l)
    if m:
        if cur is not None:
            out[cur] = len('\n'.join(buf).encode('utf-8'))
        cur = int(m.group(1)); buf = [l]
    elif cur is not None:
        buf.append(l)
if cur is not None:
    out[cur] = len('\n'.join(buf).encode('utf-8'))
ck('实测节数 151 / 末节 157', len(out) == 151 and max(out) == 157, (len(out), max(out)))
b157 = out[157]
ck('§2.157 含标题体 > 4000', b157 > 4000, b157)
newfloor = b157 // 2
print('§2.157 含标题体=%d ⇒ 新 floor=%d（= 一半，与既有建表口径一致）' % (b157, newfloor))

old_row = '    152: 6702, 153: 9662, 154: 6373, 155: 10813,\n    156: 5873,\n}'
new_row = '    152: 6702, 153: 9662, 154: 6373, 155: 10813,\n    156: 5873,\n    157: %d,\n}' % newfloor
ck('表尾锚点唯一', s.count(old_row) == 1, s.count(old_row))
s = s.replace(old_row, new_row)

blk = re.search(r'C16_FLOORS = \{(.*?)\n\}', s, re.S).group(1)
T = {int(a): int(b) for a, b in re.findall(r'(\d+):\s*(\d+)', blk)}
ck('新表 151 条、末项 157', len(T) == 151 and max(T) == 157, (len(T), max(T)))
ck('新表 157 值 = %d' % newfloor, T[157] == newfloor, T[157])
norm = '\n'.join('%d:%d' % (k, T[k]) for k in sorted(T))
newsha = hashlib.sha256(norm.encode('utf-8')).hexdigest()
print('新 C16_FLOORS_SHA256 = %s' % newsha)
olds = "C16_FLOORS_SHA256 = '5c67b2952a42cc805fcc10e62b4f002243aa691cfca92fc1bddecc92ce3601c5'"
ck('旧 sha 常量唯一', s.count(olds) == 1, s.count(olds))
s = s.replace(olds, "C16_FLOORS_SHA256 = '%s'" % newsha)

# ---------- GATE_VER ----------
ck('GATE_VER 常量唯一', s.count("GATE_VER = 'R151'") == 1)
s = s.replace("GATE_VER = 'R151'", "GATE_VER = 'R152'")
s = s.replace("live 写 `grep=(?m)^GATE_VER = 'R151'`", "live 写 `grep=(?m)^GATE_VER = 'R152'`")
open(G, 'wb').write(s.encode('utf-8'))
ck('check_disc 回读一致', open(G, 'rb').read() == s.encode('utf-8'))

# ---------- DISC_RECHECK / DISC_UNVERIFIABLE 锚点 ----------
OLD = "grep=(?m)^GATE_VER = 'R151'"
NEW = "grep=(?m)^GATE_VER = 'R152'"
for p, name in ((DR, 'DISC_RECHECK'), (DU, 'DISC_UNVERIFIABLE')):
    t = open(p, 'rb').read().decode('utf-8')
    ck('%s 旧锚点恰 1 处' % name, t.count(OLD) == 1, t.count(OLD))
    t2 = t.replace(OLD, NEW)
    ck('%s 新锚点 1 处 / 旧 0' % name, t2.count(NEW) == 1 and t2.count(OLD) == 0)
    open(p, 'wb').write(t2.encode('utf-8'))
    ck('%s 回读一致且 CR 0' % name,
       open(p, 'rb').read() == t2.encode('utf-8') and open(p, 'rb').read().count(b'\r') == 0)

# ---------- FREEZE_SHA256 ----------
du_new = open(DU, 'rb').read()
new_freeze = hashlib.sha256(du_new).hexdigest()
print('DISC_UNVERIFIABLE 新 sha256 = %s' % new_freeze)
gs = open(G, encoding='utf-8').read()
m = re.search(r"FREEZE_SHA256 = '([0-9a-f]+)'", gs)
ck('找到 FREEZE_SHA256', m is not None)
ck('FREEZE 旧值 = 2b0bc498…', m.group(1).startswith('2b0bc498'), m.group(1)[:12])
gs2 = gs.replace("FREEZE_SHA256 = '%s'" % m.group(1), "FREEZE_SHA256 = '%s'" % new_freeze)
open(G, 'wb').write(gs2.encode('utf-8'))
ck('check_disc 回读一致', open(G, 'rb').read() == gs2.encode('utf-8'))

# ---------- 跑门禁 ----------
print('\n[跑门禁]')
r = subprocess.run([sys.executable, 'check_disc.py'], cwd=D, capture_output=True, text=True, timeout=600)
ck('门禁 exit 0', r.returncode == 0, r.returncode)
for ln in r.stdout.split('\n'):
    if re.search(r'C7 |C7b|C7d|C10 |C11 |C12 |C15 |C16 |C16d|PASS|FAIL|BOUNDARY|exit', ln):
        print('  ' + ln.strip())
if r.returncode != 0:
    print('--- STDERR ---'); print(r.stderr[-2000:])

print('\nFAIL %d：%s' % (len(fail), fail))
sys.exit(1 if fail else 0)
