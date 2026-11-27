#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r163g_bump_gate.py —— 门禁版本 R162 → R163，并把新节 2.168 纳入 C16 逐节下界。

R160/R161 都踩过的联动坑（本次由 gate_runner 的 G3 断言逐条守住）：
  改 GATE_VER 会同时牵动
    (1) check_disc.py 的 GATE_VER 常量
    (2) DISC_RECHECK.tsv「纪律号 20」那一行的 col6（C10 自检正则）
    (3) DISC_UNVERIFIABLE.tsv「纪律号 20」那一行的 col4（镜像）⇒ FREEZE_SHA256 变
  改 DISC_RECHECK 第 20 行 ⇒ C7_TEXT_SHA256 与 C7_ROW_SHA['20'] 变
  新增 C16_FLOORS 条目 ⇒ C16_FLOORS_SHA256 变
先沙箱预演（整树三层镜像），再由 gate_runner 在生产上实名复验 G1/G2/G3。
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
T = R + '/lead/next_re_20261117_r14'
G = T + '/check_disc.py'
DR = T + '/DISC_RECHECK.tsv'
UN = T + '/DISC_UNVERIFIABLE.tsv'
RC = T + '/R14_COMMON.md'
BD = T + '/R17_LEAD_BASELINE'
NEW_VER = 'R163'

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
def bak(path, tag):
    stamp = time.strftime('%Y%m%d_%H%M%S')
    out = os.path.join(BD, os.path.basename(path) + '.before_r163g_%s_%s.bak' % (tag, stamp))
    fd = os.open(out, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f: f.write(rb(path))
    return out

print('== 0 · 旧态 ==')
g0, dr0, un0, rc0 = rd(G), rd(DR), rd(UN), rd(RC)
print('  check_disc   sha=%s' % sha(g0.encode())[:16])
print('  DR           sha=%s' % sha(dr0.encode())[:16])
print('  UN           sha=%s' % sha(un0.encode())[:16])
cur = re.search(r"GATE_VER = '([^']+)'", g0).group(1)
ck('0.1 当前 GATE_VER 是 R162 或已是 R163（幂等）', cur in ('R162', NEW_VER), cur)
IDEMP = (cur == NEW_VER)

# 2.168 实测字节
t = rc0.replace('\r\n', '\n')
m = re.search(r'(?ms)^##\s+2\.168\b.*?(?=^##\s+2\.\d|\Z)', t)
ck('0.2 能定位 2.168 节', m is not None)
sec_168 = len(m.group(0).encode('utf-8'))
NEW_FLOOR = sec_168 // 2
print('  §2.168 = %d B ; 下界 = %d' % (sec_168, NEW_FLOOR))

# --- 构造新 check_disc.py ---
g1 = g0
if not IDEMP:
    g1 = g1.replace("GATE_VER = 'R162'", "GATE_VER = '%s'" % NEW_VER, 1)
ck('0.3 GATE_VER 已改', "GATE_VER = '%s'" % NEW_VER in g1)

mf = re.search(r'(?m)^    167: (\d+),$', g1)
ck('0.4 能定位 C16 里 167 那一行', mf is not None, mf.group(0).strip() if mf else None)
# S-466（第十一条，同一族，R163 起同一坑第五次）：下界 = **首次实测的一半**，而 2.168 在追加「门禁升级」那节后
# 已从 6,152 B 长到 7,439 B。若拿「本次重算的 NEW_FLOOR」去比表里的值，幂等重跑必然假 FAIL。
# 判据改为「167 已在表里」，并单独断言表里的值不大于本次实测（下界语义：只许小于等于实测）。
m168 = re.search(r'(?m)^    168: (\d+),$', g1)
if not m168:
    ins = mf.end()
    g1 = g1[:ins] + '\n    168: %d,' % NEW_FLOOR + g1[ins:]
    m168 = re.search(r'(?m)^    168: (\d+),$', g1)
ck('0.5 C16 已纳入 168', m168 is not None, m168.group(0).strip() if m168 else None)
ck('0.5b 表里 167 的下界 <= 本次实测（下界语义，允许正文增长后不重钉）',
   m168 is not None and int(m168.group(1)) <= sec_168, (m168.group(1) if m168 else None, sec_168))

m2 = re.search(r'C16_FLOORS = \{\n(.*?)\n\}', g1, re.S)
floors = dict((int(a), int(b)) for a, b in re.findall(r'(\d+):\s*(\d+),', m2.group(1)))
norm = '\n'.join('%d:%d' % (k, floors[k]) for k in sorted(floors))
new_fl = hashlib.sha256(norm.encode()).hexdigest()
old_fl = re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'", g1).group(1)
if old_fl != new_fl:
    g1 = g1.replace("C16_FLOORS_SHA256 = '%s'" % old_fl, "C16_FLOORS_SHA256 = '%s'" % new_fl, 1)
print('  C16 %d 节 ; sha %s -> %s' % (len(floors), old_fl[:16], new_fl[:16]))

# --- DR / UN 第 20 行 ---
def rows_of(x):
    return [l.split('\t') for l in x.replace('\r\n', '\n').split('\n') if l.strip()]
dr_rows = rows_of(dr0)
r20 = next(r for r in dr_rows if r[0] == '20')
ck('0.6 DR 纪律号20 col6 现为 R162', "'R162'" in r20[5] or "'%s'" % NEW_VER in r20[5], r20[5][:60])
dr1 = dr0
if not IDEMP:
    dr1 = dr1.replace("grep=(?m)^GATE_VER = 'R162'", "grep=(?m)^GATE_VER = '%s'" % NEW_VER, 1)
ck('0.7 DR 已改到 R163', "'%s'" % NEW_VER in dr1)

un_rows = rows_of(un0)
u20 = next(r for r in un_rows if r[0] == '20')
un1 = un0
if not IDEMP:
    un1 = un1.replace("grep=(?m)^GATE_VER = 'R162'", "grep=(?m)^GATE_VER = '%s'" % NEW_VER, 1)
new_freeze = sha(un1.encode())
old_freeze = re.search(r"FREEZE_SHA256 = '([0-9a-f]{64})'", g1).group(1)
if old_freeze != new_freeze:
    g1 = g1.replace("FREEZE_SHA256 = '%s'" % old_freeze,
                    "FREEZE_SHA256 = '%s'" % new_freeze, 1)
print('  FREEZE %s -> %s' % (old_freeze[:16], new_freeze[:16]))

# --- C7d 重钉（DR 内容变了）---
rows1 = rows_of(dr1)
blob = '\n'.join('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip()) for r in rows1[1:])
new_c7txt = hashlib.sha256(blob.encode()).hexdigest()
r20b = next(r for r in rows1 if r[0] == '20')
new_c7row = hashlib.sha256(('%s\t%s\t%s' % (r20b[0], r20b[4].strip(), r20b[5].strip())).encode()).hexdigest()
cur_c7txt = re.search(r"C7_TEXT_SHA256 = '([0-9a-f]{64})'", g1).group(1)
cur_rows = dict(re.findall(r"'(\d+)':\s*'([0-9a-f]{64})'",
                           re.search(r'C7_ROW_SHA = \{(.*?)\}', g1, re.S).group(1)))
if cur_c7txt != new_c7txt:
    g1 = g1.replace("C7_TEXT_SHA256 = '%s'" % cur_c7txt,
                    "C7_TEXT_SHA256 = '%s'" % new_c7txt, 1)
if cur_rows.get('20') != new_c7row:
    g1 = g1.replace("'20': '%s'" % cur_rows['20'], "'20': '%s'" % new_c7row, 1)
print('  C7 text %s -> %s ; row20 %s -> %s'
      % (cur_c7txt[:16], new_c7txt[:16], cur_rows['20'][:16], new_c7row[:16]))
c14_before = re.search(r"C14_TEXT_SHA256 = '([0-9a-f]{64})'", g0).group(1)
c14_after = re.search(r"C14_TEXT_SHA256 = '([0-9a-f]{64})'", g1).group(1)
ck('0.8 反控：C14_TEXT_SHA256 一字未动', c14_before == c14_after, (c14_before[:12], c14_after[:12]))

if fails:
    print('\n[abort] 前置断言失败'); sys.exit(1)

print('\n== 1 · 沙箱预演（三层镜像 + gate_runner 全跑）==')
SB = tempfile.mkdtemp(prefix='/tmp/r163sb_bump_')
for name in os.listdir(R):
    if name in ('lead',) or name.startswith('r163sb_'):
        continue
    os.symlink(os.path.join(R, name), SB + '/' + name)
os.makedirs(SB + '/lead')
for name in os.listdir(os.path.join(R, 'lead')):
    if name == 'next_re_20261117_r14':
        continue
    os.symlink(os.path.join(R, 'lead', name), SB + '/lead/' + name)
os.makedirs(SB + '/lead/next_re_20261117_r14')
OV = {'check_disc.py', 'DISC_RECHECK.tsv', 'DISC_UNVERIFIABLE.tsv'}
for name in os.listdir(T):
    if name in OV:
        continue
    os.symlink(os.path.join(T, name), SB + '/lead/next_re_20261117_r14/' + name)
for name, txt in (('check_disc.py', g1), ('DISC_RECHECK.tsv', dr1), ('DISC_UNVERIFIABLE.tsv', un1)):
    with open(SB + '/lead/next_re_20261117_r14/' + name, 'wb') as f:
        f.write(txt.encode('utf-8'))
env = dict(os.environ); env['PYTHONDONTWRITEBYTECODE'] = '1'
p = subprocess.run([sys.executable, 'lead/next_re_20261117_r14/check_disc.py'],
                   capture_output=True, text=True, cwd=SB, timeout=600, env=env)
out = p.stdout + p.stderr
ck('1.1 沙箱门禁 exit 0', p.returncode == 0, p.returncode)
fsb = [l.strip() for l in out.split('\n') if l.strip().startswith('FAIL')]
for x in fsb[:6]:
    print('       ' + x[:150])
ck('1.2 沙箱 FAIL 行 0', len(fsb) == 0, len(fsb))
ck('1.3 沙箱 C10 自报 R163', 'ok(%s)' % NEW_VER in out, 'ok(R163)' in out)
ck('1.4 沙箱 C16 unpinned 0（2.168 已入表）', 'unpinned 0' in out)
ck('1.5 沙箱 C16d floor pin OK', 'C16d floor-table pin: %s (OK)' % new_fl[:16] in out, new_fl[:16])

# 反控：镜像不同步 ⇒ 必须 FAIL（证明联动是必需的）。
# S-464：首版把「负控 DR」写成**旧态 dr0**，幂等重跑时 dr0 已是 R162 ⇒ 负控失效、假 FAIL。
# 改为**显式构造成**「DR 登记 R999」的失配副本，与当前版本号无关。
sb2 = SB + '_neg'
shutil.copytree(SB, sb2, symlinks=True)
neg_dr = dr1.replace("GATE_VER = '%s'" % NEW_VER, "GATE_VER = 'R999'", 1)
ck('1.5b 负控副本确实与正本不同（否则负控无意义）', neg_dr != dr1)
with open(sb2 + '/lead/next_re_20261117_r14/DISC_RECHECK.tsv', 'wb') as f:
    f.write(neg_dr.encode('utf-8'))
p2 = subprocess.run([sys.executable, 'lead/next_re_20261117_r14/check_disc.py'],
                    capture_output=True, text=True, cwd=sb2, timeout=600, env=env)
o2 = p2.stdout + p2.stderr
ck('1.6 反控：DR 登记 R999（镜像不同步）⇒ 必须 FAIL 且报 C10',
   p2.returncode != 0 and 'C10 self GATE_VER registered' in o2,
   (p2.returncode, [l.strip()[:80] for l in o2.split('\n') if 'C10' in l][:2]))
shutil.rmtree(sb2, ignore_errors=True)
shutil.rmtree(SB, ignore_errors=True)

print('\n== 2 · 生产备份 + 一次性写入 + 回读 ==')
for path, old, newt, label in ((UN, un0, un1, 'UN'), (DR, dr0, dr1, 'DR'), (G, g0, g1, 'GATE')):
    if IDEMP and old == newt:
        print('     %-4s 幂等，跳过' % label); continue
    ck('2.%s 写前生产 sha 仍等于旧态' % label, sha(rb(path)) == sha(old.encode()))
    b = bak(path, label)
    ck('2.%s 备份与旧态逐字节相同' % label, rb(b) == old.encode())
    with open(path, 'wb') as f:
        f.write(newt.encode('utf-8'))
    ck('2.%s 回读一致' % label, rb(path) == newt.encode('utf-8'))
    print('     %-4s %d -> %d B' % (label, len(old.encode()), len(newt.encode())))

print('\n== 3 · 生产 gate_runner 实名复验（G1/G2/G3 全跑）==')
p3 = subprocess.run([sys.executable, R + '/_r161/gate_runner.py'],
                    capture_output=True, text=True, cwd=R, timeout=900, env=env)
o3 = p3.stdout + p3.stderr
print('\n'.join('     ' + l for l in o3.split('\n') if ('PASS' in l or 'FAIL' in l or 'GATE_VER=' in l)))
ck('3.1 gate_runner exit 0', p3.returncode == 0, p3.returncode)
ck('3.2 gate_runner 自报 GATE_VER=R163', 'GATE_VER=R163' in o3)
ck('3.3 G1/G2/G3 全 ok', 'G1=ok' in o3 and 'G2=ok' in o3 and 'G3=ok' in o3)
# S-463：gate_runner 只回显门禁的 FAIL 行与自家 PASS 行，**不回显门的 NOTE 行**，
# 所以原来直接在 o3 里找 'unpinned 0' 是找错了对象（假 FAIL）。改为直跑主门禁取它的 NOTE 行。
p4 = subprocess.run([sys.executable, G], capture_output=True, text=True, cwd=T, timeout=600, env=env)
o4 = p4.stdout + p4.stderr
n16 = [l.strip() for l in o4.split('\n') if 'C16 per-section floors' in l]
ck('3.4 C16 unpinned 0（直取主门禁 NOTE 行）',
   p4.returncode == 0 and any('unpinned 0' in l for l in n16), n16[:1])

print('\nFAILS:', fails if fails else 'NONE')
sys.exit(1 if fails else 0)
