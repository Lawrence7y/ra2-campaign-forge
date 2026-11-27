#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R153 L：门禁回归 —— C16_FLOORS 纳 158、GATE_VER R152->R153、同步锚点、重钉 FREEZE / C7d。

必须重钉的原因（逐条由脚本自己算，不写死）：
  1) R14_COMMON 新增 §2.158 ⇒ 节数 151->152、末节 157->158、C16 unpinned 1。
  2) GATE_VER 变化 ⇒ DISC_RECHECK / DISC_UNVERIFIABLE 的 C10 锚点行要同步 ⇒
     DISC_UNVERIFIABLE 的 sha 变 ⇒ FREEZE_SHA256 要重钉。
  3) DISC_RECHECK 的 C10 行 col5 变化 ⇒ C7_TEXT_SHA256 / C7_ROW_SHA[20] 要重钉。
口径正控：把 id20 的锚点还原成 R152 后，必须复现旧钉 58a17e1a…
"""
import hashlib
import io
import os
import re
import subprocess
import sys
import time

ROOT = '/home/t628/projects/ra2-campaign-forge'
D = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
G = os.path.join(D, 'check_disc.py')
DR = os.path.join(D, 'DISC_RECHECK.tsv')
DU = os.path.join(D, 'DISC_UNVERIFIABLE.tsv')
RC = os.path.join(D, 'R14_COMMON.md')
BAKDIR = os.path.join(D, 'R17_LEAD_BASELINE')
fail = []


def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok:
        fail.append(n)
    return ok


def backup(p):
    b = os.path.join(BAKDIR, os.path.basename(p) + '.before_r153_%s.bak'
                     % time.strftime('%Y%m%d_%H%M%S'))
    fd = os.open(b, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(open(p, 'rb').read())
    ck('备份 wx %s' % os.path.basename(b), os.path.exists(b))


s = open(G, encoding='utf-8').read()
ck('pre GATE_VER = R152', "GATE_VER = 'R152'" in s)
ck('pre C16_FLOORS 末项 157: 4596', re.search(r'157:\s*4596', s) is not None)
ck('pre C16_FLOORS_SHA256 = ba2ce8a0…',
   "C16_FLOORS_SHA256 = 'ba2ce8a0def4412f1c1d14349bf5d656dacfdebab7202f97e90633d9fc221833'" in s)

# ---------- 实测 §2.158 含标题体 ----------
rc = io.open(RC, encoding='utf-8', newline='').read()
cur, buf, out = None, [], {}
for l in rc.split('\n'):
    m = re.match(r'^##\s+2\.(\d+)\b', l)
    if m:
        if cur is not None:
            out[cur] = len('\n'.join(buf).encode('utf-8'))
        cur = int(m.group(1))
        buf = [l]
    elif cur is not None:
        buf.append(l)
if cur is not None:
    out[cur] = len('\n'.join(buf).encode('utf-8'))
ck('实测节数 152 / 末节 158', len(out) == 152 and max(out) == 158, (len(out), max(out)))
b158 = out[158]
ck('§2.158 含标题体 > 4000', b158 > 4000, b158)
newfloor = b158 // 2
print('§2.158 含标题体=%d ⇒ 新 floor=%d（= 一半，与既有建表口径一致）' % (b158, newfloor))

old_row = '    156: 5873,\n    157: 4596,\n}'
new_row = '    156: 5873,\n    157: 4596,\n    158: %d,\n}' % newfloor
ck('表尾锚点唯一', s.count(old_row) == 1, s.count(old_row))
s = s.replace(old_row, new_row)

blk = re.search(r'C16_FLOORS = \{(.*?)\n\}', s, re.S).group(1)
T = {int(a): int(b) for a, b in re.findall(r'(\d+):\s*(\d+)', blk)}
ck('新表 152 条、末项 158', len(T) == 152 and max(T) == 158, (len(T), max(T)))
ck('新表 158 值 = %d' % newfloor, T[158] == newfloor, T[158])
norm = '\n'.join('%d:%d' % (k, T[k]) for k in sorted(T))
newsha = hashlib.sha256(norm.encode('utf-8')).hexdigest()
print('新 C16_FLOORS_SHA256 = %s' % newsha)
olds = "C16_FLOORS_SHA256 = 'ba2ce8a0def4412f1c1d14349bf5d656dacfdebab7202f97e90633d9fc221833'"
ck('旧 sha 常量唯一', s.count(olds) == 1, s.count(olds))
s = s.replace(olds, "C16_FLOORS_SHA256 = '%s'" % newsha)

# ---------- GATE_VER ----------
ck('GATE_VER 常量唯一', s.count("GATE_VER = 'R152'") == 1)
s = s.replace("GATE_VER = 'R152'", "GATE_VER = 'R153'")
s = s.replace("live 写 `grep=(?m)^GATE_VER = 'R152'`", "live 写 `grep=(?m)^GATE_VER = 'R153'`")
backup(G)
open(G, 'wb').write(s.encode('utf-8'))
ck('check_disc 回读一致', open(G, 'rb').read() == s.encode('utf-8'))

# ---------- DISC_RECHECK / DISC_UNVERIFIABLE 锚点 ----------
OLD = "grep=(?m)^GATE_VER = 'R152'"
NEW = "grep=(?m)^GATE_VER = 'R153'"
for p, name in ((DR, 'DISC_RECHECK'), (DU, 'DISC_UNVERIFIABLE')):
    t = open(p, 'rb').read().decode('utf-8')
    ck('%s 旧锚点恰 1 处' % name, t.count(OLD) == 1, t.count(OLD))
    t2 = t.replace(OLD, NEW)
    ck('%s 新锚点 1 处 / 旧 0' % name, t2.count(NEW) == 1 and t2.count(OLD) == 0)
    backup(p)
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
ck('FREEZE 旧值 = 9d0d4678…', m.group(1).startswith('9d0d4678'), m.group(1)[:12])
gs2 = gs.replace("FREEZE_SHA256 = '%s'" % m.group(1), "FREEZE_SHA256 = '%s'" % new_freeze)
open(G, 'wb').write(gs2.encode('utf-8'))
ck('check_disc 回读一致（FREEZE）', open(G, 'rb').read() == gs2.encode('utf-8'))

# ---------- C7d 重钉 ----------
txt = open(DR, encoding='utf-8', newline='').read()
raw = [l for l in txt.split('\n') if l]
rows = [l.split('\t') for l in raw[1:]]
ck('门禁口径 rows = 31', len(rows) == 31, len(rows))


def digest(rs):
    blob = '\n'.join('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip()) for r in rs if len(r) == 7)
    return hashlib.sha256(blob.encode('utf-8')).hexdigest()


new_text = digest(rows)
rowsha = {r[0]: hashlib.sha256(('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip()))
                               .encode('utf-8')).hexdigest() for r in rows if len(r) == 7}
print('现算 C7_TEXT_SHA256 = %s' % new_text)
old_rows = []
for r in rows:
    r2 = list(r)
    if len(r2) == 7 and r2[0] == '20' and "GATE_VER = 'R153'" in r2[5]:
        r2[5] = r2[5].replace("GATE_VER = 'R153'", "GATE_VER = 'R152'")
    old_rows.append(r2)
ck('口径正控：还原 id20 后复现旧钉 58a17e1a…', digest(old_rows).startswith('58a17e1a'),
   digest(old_rows)[:12])

gs = open(G, encoding='utf-8').read()
m = re.search(r"C7_TEXT_SHA256 = '([0-9a-f]{64})'", gs)
ck('当前 C7_TEXT_SHA256 = 58a17e1a…', m.group(1).startswith('58a17e1a'), m.group(1)[:12])
gs = gs.replace("C7_TEXT_SHA256 = '%s'" % m.group(1), "C7_TEXT_SHA256 = '%s'" % new_text)
m2 = re.search(r"C7_ROW_SHA = \{.*?'20': '([0-9a-f]{64})'", gs, re.S)
ck('找到 C7_ROW_SHA[20]', m2 is not None)
gs = gs.replace("'20': '%s'" % m2.group(1), "'20': '%s'" % rowsha['20'])
open(G, 'wb').write(gs.encode('utf-8'))
ck('check_disc 回读一致（C7d）', open(G, 'rb').read() == gs.encode('utf-8'))
m3 = re.search(r"C7_ROW_SHA = \{(.*?)\}", open(G, encoding='utf-8').read(), re.S)
pairs = dict(re.findall(r"'(\d+)': '([0-9a-f]{64})'", m3.group(1)))
ck('C7_ROW_SHA 条目 31', len(pairs) == 31, len(pairs))
ck('C7_ROW_SHA 与现算逐键全等', [k for k in rowsha if pairs.get(k) != rowsha[k]] == [])

# ---------- 跑门禁 ----------
print('\n[跑门禁]')
r = subprocess.run([sys.executable, 'check_disc.py'], cwd=D, capture_output=True, text=True,
                   timeout=600)
ck('门禁 exit 0', r.returncode == 0, r.returncode)
for ln in r.stdout.split('\n'):
    if re.search(r'C7 |C7b|C7d|C10 |C11 frozen|C12|C15 |C16 |C16d|PASS|FAIL|BOUNDARY', ln):
        print('  ' + ln.strip())
if r.returncode != 0:
    print('--- STDERR ---')
    print(r.stderr[-1500:])

print('\nFAIL %d：%s' % (len(fail), fail))
sys.exit(1 if fail else 0)
