#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R151 门禁锚点同步：DISC_RECHECK.tsv 与 DISC_UNVERIFIABLE.tsv 的 id 20 锚点
从 grep=(?m)^GATE_VER = 'R150' 同步到 'R151'，并重钉 FREEZE_SHA256 与 C7 相关钉。
写入前断言旧 sha，写入后跑门禁。
"""
import hashlib, io, os, re, subprocess, sys

D = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
DR = os.path.join(D, 'DISC_RECHECK.tsv')
DU = os.path.join(D, 'DISC_UNVERIFIABLE.tsv')
G = os.path.join(D, 'check_disc.py')

fail = []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok: fail.append(n)
    return ok

OLD = "grep=(?m)^GATE_VER = 'R150'"
NEW = "grep=(?m)^GATE_VER = 'R151'"

# ---------- 0. check_disc 里不该再有 R150 锚点 ----------
gs = open(G, encoding='utf-8').read()
ck('check_disc.py 已无 GATE_VER = R150 字面', "GATE_VER = 'R150'" not in gs)
ck('check_disc.py GATE_VER = R151', "GATE_VER = 'R151'" in gs)

# ---------- 1. DISC_RECHECK id 20 ----------
dr_raw = open(DR, 'rb').read()
dr_sha0 = hashlib.sha256(dr_raw).hexdigest()
ck('DISC_RECHECK pre CR == 0', dr_raw.count(b'\r') == 0, dr_raw.count(b'\r'))
ck('DISC_RECHECK 旧锚点恰 1 处', dr_raw.decode('utf-8').count(OLD) == 1,
   dr_raw.decode('utf-8').count(OLD))
dr = dr_raw.decode('utf-8').replace(OLD, NEW)
ck('DISC_RECHECK 新锚点恰 1 处、旧锚点 0', dr.count(NEW) == 1 and dr.count(OLD) == 0)
open(DR, 'wb').write(dr.encode('utf-8'))
ck('DISC_RECHECK 回读一致', open(DR, 'rb').read() == dr.encode('utf-8'))
ck('DISC_RECHECK CR 仍 0', open(DR, 'rb').read().count(b'\r') == 0)

# ---------- 2. DISC_UNVERIFIABLE id 20 ----------
du_raw = open(DU, 'rb').read()
du_sha0 = hashlib.sha256(du_raw).hexdigest()
ck('DISC_UNVERIFIABLE pre CR == 0', du_raw.count(b'\r') == 0, du_raw.count(b'\r'))
ck('DISC_UNVERIFIABLE 旧锚点恰 1 处', du_raw.decode('utf-8').count(OLD) == 1,
   du_raw.decode('utf-8').count(OLD))
du = du_raw.decode('utf-8').replace(OLD, NEW)
ck('DISC_UNVERIFIABLE 新锚点恰 1 处、旧锚点 0', du.count(NEW) == 1 and du.count(OLD) == 0)
open(DU, 'wb').write(du.encode('utf-8'))
ck('DISC_UNVERIFIABLE 回读一致', open(DU, 'rb').read() == du.encode('utf-8'))
ck('DISC_UNVERIFIABLE CR 仍 0', open(DU, 'rb').read().count(b'\r') == 0)

# ---------- 3. 重钉 FREEZE_SHA256 ----------
du_new = open(DU, 'rb').read()
new_freeze = hashlib.sha256(du_new).hexdigest()
print('DISC_UNVERIFIABLE 新 sha256 = %s' % new_freeze)
gs = open(G, encoding='utf-8').read()
m = re.search(r"FREEZE_SHA256 = '([0-9a-f]+)'", gs)
ck('找到 FREEZE_SHA256 常量', m is not None)
ck('FREEZE_SHA256 旧值 = 9a661131…', m.group(1).startswith('9a661131'), m.group(1)[:12])
gs2 = gs.replace("FREEZE_SHA256 = '%s'" % m.group(1),
                 "FREEZE_SHA256 = '%s'" % new_freeze)
ck('FREEZE 常量替换生效', new_freeze in gs2)
open(G, 'wb').write(gs2.encode('utf-8'))
ck('check_disc 回读一致', open(G, 'rb').read() == gs2.encode('utf-8'))

# ---------- 4. 跑门禁 ----------
print('\n[跑门禁]')
r = subprocess.run([sys.executable, 'check_disc.py'], cwd=D, capture_output=True, text=True, timeout=300)
ck('门禁 exit 0', r.returncode == 0, r.returncode)
for ln in r.stdout.split('\n'):
    if re.search(r'C7 |C7b|C7d|C10 |C11 |C12 |C16 |C16d|C15 |PASS|FAIL|BOUNDARY|exit', ln):
        print('  ' + ln.strip())

print('\nFAIL %d：%s' % (len(fail), fail))
sys.exit(1 if fail else 0)
