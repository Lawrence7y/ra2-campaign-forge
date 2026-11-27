#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r160n_bump_gate.py —— 把门禁版本 R159 → R160（三处联动，一次事务）。

R159（OP2/OP4）已记录过这个坑：改 GATE_VER 会同时牵动
  (1) check_disc.py 的 GATE_VER 常量
  (2) DISC_RECHECK.tsv 第 20 行的 col6（C10 自检正则）
  (3) DISC_UNVERIFIABLE.tsv 第 20 行的 col4（该行镜像）⇒ FREEZE_SHA256 变
另需把 C16_FLOORS 纳入新节 165 并重钉 C16_FLOORS_SHA256。

本脚本按依赖顺序一次做完，并在写盘前用**影子副本**跑一遍门禁做正反控。
"""
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

R = '/home/t628/projects/ra2-campaign-forge'
D = R + '/lead/next_re_20261117_r14'
G = D + '/check_disc.py'
DR = D + '/DISC_RECHECK.tsv'
UN = D + '/DISC_UNVERIFIABLE.tsv'
RC = D + '/R14_COMMON.md'
BD = D + '/R17_LEAD_BASELINE'
NEW_VER = 'R160'

fails = []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok: fails.append(n)
    return ok

def rd(p): return io.open(p, encoding='utf-8', newline='').read()
def rb(p):
    with open(p, 'rb') as f: return f.read()
def sha(b): return hashlib.sha256(b).hexdigest()
def bak(path):
    stamp = time.strftime('%Y%m%d_%H%M%S')
    out = os.path.join(BD, os.path.basename(path) + '.before_r160b_%s.bak' % stamp)
    fd = os.open(out, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f: f.write(rb(path))
    return out

print('== 0 · 旧态 ==')
g0, dr0, un0, rc0 = rd(G), rd(DR), rd(UN), rd(RC)
print('  check_disc.py        sha=%s' % sha(g0.encode())[:16])
print('  DISC_RECHECK.tsv     sha=%s' % sha(dr0.encode())[:16])
print('  DISC_UNVERIFIABLE    sha=%s' % sha(un0.encode())[:16])
cur = re.search(r"GATE_VER = '([^']+)'", g0).group(1)
ck('0.1 当前 GATE_VER 是 R159 或已是 R160（幂等）', cur in ('R159', NEW_VER), cur)
IDEMP = (cur == NEW_VER)

# ---- 计算新节 165 的实测字节 ----
t = rc0.replace('\r\n', '\n')
blocks = {}
order = []
cur_n = None
buf = []
for line in t.split('\n'):
    m = re.match(r'^##\s+2\.(\d+)\b', line)
    if m:
        if cur_n is not None:
            blocks[cur_n] = len('\n'.join(buf).encode('utf-8'))
        cur_n = int(m.group(1)); buf = [line]; order.append(cur_n)
    elif cur_n is not None:
        buf.append(line)
if cur_n is not None:
    blocks[cur_n] = len('\n'.join(buf).encode('utf-8'))
ck('0.2 实测到 2.165 的字节', 165 in blocks, blocks.get(165))
print('  §2.165 measured body = %d B' % blocks[165])
NEW_FLOOR = blocks[165] // 2          # 与既有纪律一致：下界 = 实测的一半
print('  NEW_FLOOR = %d // 2 = %d' % (blocks[165], NEW_FLOOR))

# ---- 构造新 check_disc.py ----
g1 = g0
if not IDEMP:
    g1 = g1.replace("GATE_VER = 'R159'", "GATE_VER = 'R160'", 1)
# C16_FLOORS 追加 165
m = re.search(r'(C16_FLOORS = \{\n)(.*?)(\n\})', g1, re.S)
ck('0.3 找到 C16_FLOORS 表', bool(m))
body = m.group(2)
if '\n    165:' not in body:
    g1 = g1[:m.start(2)] + body + '\n    165: %d,' % NEW_FLOOR + g1[m.end(2):]
m2 = re.search(r'C16_FLOORS = \{\n(.*?)\n\}', g1, re.S)
floors = dict((int(a), int(b)) for a, b in re.findall(r'(\d+):\s*(\d+),', m2.group(1)))
new_norm = '\n'.join('%d:%d' % (k, floors[k]) for k in sorted(floors))
new_fl_sha = hashlib.sha256(new_norm.encode()).hexdigest()
old_fl_sha = re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'", g1).group(1)
print('  C16 floors 条数 %d，旧 sha=%s 新 sha=%s'
      % (len(floors), old_fl_sha[:16], new_fl_sha[:16]))
if old_fl_sha != new_fl_sha:
    g1 = g1.replace("C16_FLOORS_SHA256 = '%s'" % old_fl_sha,
                    "C16_FLOORS_SHA256 = '%s'" % new_fl_sha, 1)

# ---- DISC_RECHECK 第 20 行 col6 ----
def rows_of(txt):
    nl = txt.replace('\r\n', '\n')
    return [l.split('\t') for l in nl.split('\n') if l.strip()]

dr_rows = rows_of(dr0)
r20 = [r for r in dr_rows if r[0] == '20'][0]
ck('0.4 DISC_RECHECK 第20行 col6 含 R159', "'R159'" in r20[5], r20[5])
dr1 = dr0
if not IDEMP:
    dr1 = dr1.replace("grep=(?m)^GATE_VER = 'R159'", "grep=(?m)^GATE_VER = 'R160'", 1)
ck('0.5 DISC_RECHECK 已改到 R160', "'R160'" in dr1)

# ---- DISC_UNVERIFIABLE 第 20 行 col4（镜像）----
un_rows = rows_of(un0)
u20 = [r for r in un_rows if r[0] == '20'][0]
ck('0.6 UNVERIFIABLE 第20行 col4 含 R159', "'R159'" in u20[3], u20[3])
un1 = un0
if not IDEMP:
    un1 = un1.replace("grep=(?m)^GATE_VER = 'R159'", "grep=(?m)^GATE_VER = 'R160'", 1)
new_freeze = sha(un1.encode())
old_freeze = re.search(r"FREEZE_SHA256 = '([0-9a-f]{64})'", g1).group(1)
if old_freeze != new_freeze:
    g1 = g1.replace("FREEZE_SHA256 = '%s'" % old_freeze,
                    "FREEZE_SHA256 = '%s'" % new_freeze, 1)
print('  FREEZE %s -> %s' % (old_freeze[:16], new_freeze[:16]))

if fails:
    print('\n[abort] 旧态断言失败'); sys.exit(1)

# ---- 影子副本正反控 ----
print('\n== 1 · 影子副本预演（先证明这套改动能让门禁 exit 0）==')
SB = tempfile.mkdtemp(prefix='/tmp/r160sb_gate_')
os.makedirs(SB + '/lead/next_re_20261117_r14', exist_ok=True)
for src, dst in ((G, SB + '/lead/next_re_20261117_r14/check_disc.py'),
                 (DR, SB + '/lead/next_re_20261117_r14/DISC_RECHECK.tsv'),
                 (UN, SB + '/lead/next_re_20261117_r14/DISC_UNVERIFIABLE.tsv'),
                 (RC, SB + '/lead/next_re_20261117_r14/R14_COMMON.md'),
                 (D + '/STATUS_BOARD.md', SB + '/lead/next_re_20261117_r14/STATUS_BOARD.md')):
    shutil.copy2(src, dst)
with open(SB + '/lead/next_re_20261117_r14/check_disc.py', 'wb') as f:
    f.write(g1.encode('utf-8'))
with open(SB + '/lead/next_re_20261117_r14/DISC_RECHECK.tsv', 'wb') as f:
    f.write(dr1.encode('utf-8'))
with open(SB + '/lead/next_re_20261117_r14/DISC_UNVERIFIABLE.tsv', 'wb') as f:
    f.write(un1.encode('utf-8'))
shutil.copy2(R + '/lead/GOAL_THREE_TARGETS_20261018.md',
             SB + '/lead/GOAL_THREE_TARGETS_20261018.md')
p = subprocess.run([sys.executable, 'lead/next_re_20261117_r14/check_disc.py'],
                   capture_output=True, text=True, cwd=SB, timeout=400)
ck('1.1 影子副本门禁 exit 0', p.returncode == 0, p.returncode)
for ln in (p.stdout + p.stderr).split('\n'):
    if 'FAIL' in ln or 'C16 per-section' in ln or 'C10 self' in ln or 'C15 content' in ln:
        print('     ' + ln.strip()[:180])

# 反控：影子副本若不改 GATE_VER（旧值），C10 必须 FAIL
with open(SB + '/lead/next_re_20261117_r14/check_disc.py', 'wb') as f:
    f.write(g0.encode('utf-8'))
p2 = subprocess.run([sys.executable, 'lead/next_re_20261117_r14/check_disc.py'],
                    capture_output=True, text=True, cwd=SB, timeout=400)
ck('1.2 反控：旧 check_disc.py 配新 DISC_RECHECK 必须 FAIL（联动是必需的）',
   p2.returncode != 0, p2.returncode)
shutil.rmtree(SB, ignore_errors=True)

# ---- 生产写入 ----
print('\n== 2 · 生产备份 + 一次性写入 + 回读 ==')
for path, old_b, new_t, label in ((UN, un0, un1, 'DISC_UNVERIFIABLE'),
                                  (DR, dr0, dr1, 'DISC_RECHECK'),
                                  (G, g0, g1, 'check_disc.py')):
    if IDEMP and old_b == new_t.encode('utf-8'):
        print('     %-18s 幂等，无需写' % label); continue
    b = bak(path)
    ck('2.%s 备份 %s' % (label, os.path.basename(b)), rb(b) == old_b)
    with open(path, 'wb') as f:
        f.write(new_t.encode('utf-8'))
    ck('2.%s 回读一致 %s' % (label, label), rb(path) == new_t.encode('utf-8'))
    print('     %-18s %d -> %d B' % (label, len(old_b), len(new_t.encode())))

print('\n== 3 · 生产门禁真实回归 ==')
p3 = subprocess.run([sys.executable, 'check_disc.py'], capture_output=True, text=True, cwd=D)
ck('3.1 生产门禁 exit 0', p3.returncode == 0, p3.returncode)
print('     FAIL 行数 = %d' % p3.stdout.count('  FAIL  '))
for ln in p3.stdout.split('\n'):
    if any(k in ln for k in ('C16 per-section', 'C10 self', 'C15 content', 'exit')):
        print('     ' + ln.strip()[:180])
ck('3.2 C10 自报 R160', 'ok(R160)' in p3.stdout, 'ok(R160)' in p3.stdout)
ck('3.3 C16 unpinned 已归 0', 'unpinned 0' in p3.stdout)

print('\nFAILS:', fails if fails else 'NONE')
sys.exit(1 if fails else 0)
