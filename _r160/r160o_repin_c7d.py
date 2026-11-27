#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r160o_repin_c7d.py —— C7d 重钉（id 20 的 col5/col6 显式改为 R160），并顺带修 r160n 的备份断言 bug。

R159 已记过这个坑（OP2/OP4）：改 DISC_RECHECK 第 20 行的 col6 ⇒
  C7d 整表指纹变 + C7_ROW_SHA['20'] 变。
r160n 只改了 GATE_VER 常量与两处镜像，**漏了 C7d 这一格**，所以生产门禁剩 1 FAIL。
本脚本把 C7d 补上，并在写盘前用影子副本证明「改完恰好 exit 0」。
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
BD = D + '/R17_LEAD_BASELINE'

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

print('== 0 · 当前态 ==')
g0, dr0 = rd(G), rd(DR)
print('  check_disc.py    sha=%s' % sha(g0.encode())[:16])
print('  DISC_RECHECK.tsv sha=%s' % sha(dr0.encode())[:16])

rows = [l.split('\t') for l in dr0.replace('\r\n', '\n').split('\n') if l.strip()]
ck('0.1 表 31 行 7 列', len(rows) - 1 == 31 and all(len(r) == 7 for r in rows[1:]))
r20 = [r for r in rows if r[0] == '20'][0]
ck('0.2 第20行 col6 已是 R160', "'R160'" in r20[5], r20[5])

blob = '\n'.join('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip()) for r in rows[1:])
now_sha = hashlib.sha256(blob.encode()).hexdigest()
row20 = hashlib.sha256(('%s\t%s\t%s' % (r20[0], r20[4].strip(), r20[5].strip())).encode()).hexdigest()
cur_txt = re.search(r"C7_TEXT_SHA256 = '([0-9a-f]{64})'", g0).group(1)
cur_row = dict(re.findall(r"'(\d+)':\s*'([0-9a-f]{64})'",
                          re.search(r'C7_ROW_SHA = \{(.*?)\}', g0, re.S).group(1)))
print('  C7 实测整表 sha=%s  已钉=%s  一致=%s' % (now_sha[:16], cur_txt[:16], now_sha == cur_txt))
print('  id20 实测 sha=%s  已钉=%s  一致=%s'
      % (row20[:16], cur_row['20'][:16], row20 == cur_row['20']))
ck('0.3 只有 id20 漂移', now_sha != cur_txt, True)
drifted = [k for k in cur_row
           if hashlib.sha256(('%s\t%s\t%s' % (
               [r for r in rows[1:] if r[0] == k][0][0],
               [r for r in rows[1:] if r[0] == k][0][4].strip(),
               [r for r in rows[1:] if r[0] == k][0][5].strip())).encode()).hexdigest() != cur_row[k]]
print('  逐行实测漂移 ids = %r' % drifted)
ck('0.4 漂移集恰为 [20]', drifted == ['20'], drifted)

# 构造新门禁脚本
g1 = g0.replace("C7_TEXT_SHA256 = '%s'" % cur_txt,
                "C7_TEXT_SHA256 = '%s'" % now_sha, 1)
g1 = g1.replace("'20': '%s'" % cur_row['20'], "'20': '%s'" % row20, 1)
ck('0.5 两处已替换', now_sha[:16] in g1 and row20[:16] in g1)
# 反控：C14 一字未动
c14 = re.search(r"C14_TEXT_SHA256 = '([0-9a-f]{64})'", g1).group(1)
c14_old = re.search(r"C14_TEXT_SHA256 = '([0-9a-f]{64})'", g0).group(1)
ck('0.6 反控：C14_TEXT_SHA256 一字未动', c14 == c14_old)

print('\n== 1 · 影子副本预演 ==')
SB = tempfile.mkdtemp(prefix='/tmp/r160sb_c7d_')
os.makedirs(SB + '/lead/next_re_20261117_r14', exist_ok=True)
for src in (DR, UN, D + '/R14_COMMON.md', D + '/STATUS_BOARD.md'):
    shutil.copy2(src, SB + '/lead/next_re_20261117_r14/' + os.path.basename(src))
shutil.copy2(R + '/lead/GOAL_THREE_TARGETS_20261018.md', SB + '/lead/')
with open(SB + '/lead/next_re_20261117_r14/check_disc.py', 'wb') as f:
    f.write(g1.encode('utf-8'))
p = subprocess.run([sys.executable, 'lead/next_re_20261117_r14/check_disc.py'],
                   capture_output=True, text=True, cwd=SB, timeout=400)
ck('1.1 影子副本 exit 0', p.returncode == 0, p.returncode)
for ln in p.stdout.split('\n'):
    if 'C7d' in ln or 'FAIL' in ln or 'exit' in ln:
        print('     ' + ln.strip()[:170])
# 反控：不替换 C7 时应 FAIL
with open(SB + '/lead/next_re_20261117_r14/check_disc.py', 'wb') as f:
    f.write(g0.encode('utf-8'))
p2 = subprocess.run([sys.executable, 'lead/next_re_20261117_r14/check_disc.py'],
                    capture_output=True, text=True, cwd=SB, timeout=400)
ck('1.2 反控：不重钉 C7d 时必须 FAIL', p2.returncode != 0, p2.returncode)
shutil.rmtree(SB, ignore_errors=True)

print('\n== 2 · 生产写入（wx 备份 + 断言旧 sha + 回读）==')
ck('2.0 写前生产 sha 仍等于 g0', sha(rb(G)) == sha(g0.encode()))
stamp = time.strftime('%Y%m%d_%H%M%S')
bpath = os.path.join(BD, 'check_disc.py.before_r160c_%s.bak' % stamp)
fd = os.open(bpath, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
with os.fdopen(fd, 'wb') as f:
    f.write(rb(G))
ck('2.1 备份与旧态逐字节相同（修 r160n 的比较 bug：这里两边都是 bytes）',
   rb(bpath) == g0.encode('utf-8'), (len(rb(bpath)), len(g0.encode())))
with open(G, 'wb') as f:
    f.write(g1.encode('utf-8'))
ck('2.2 回读一致', rb(G) == g1.encode('utf-8'))
print('     check_disc.py %d -> %d B' % (len(g0.encode()), len(g1.encode())))

print('\n== 3 · 生产门禁真实回归 ==')
p3 = subprocess.run([sys.executable, 'check_disc.py'], capture_output=True, text=True, cwd=D)
ck('3.1 exit 0', p3.returncode == 0, p3.returncode)
ck('3.2 FAIL 行数 0', p3.stdout.count('  FAIL  ') == 0, p3.stdout.count('  FAIL  '))
for ln in p3.stdout.split('\n'):
    if any(k in ln for k in ('C7d', 'C10 self', 'C16 per-section', 'C14 free-text', 'exit')):
        print('     ' + ln.strip()[:170])
ck('3.3 C10 自报 R160', 'ok(R160)' in p3.stdout)
ck('3.4 C7d ok', 'C7d product/expression fingerprint ok' in p3.stdout)
ck('3.5 C16 unpinned 0', 'unpinned 0' in p3.stdout)
ck('3.6 C14 仍 ok', 'C14 free-text table fingerprint ok' in p3.stdout)

print('\nFAILS:', fails if fails else 'NONE')
sys.exit(1 if fails else 0)
