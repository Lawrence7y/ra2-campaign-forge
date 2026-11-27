#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r159c_sandbox.py — 在沙箱副本里**预演**整笔写入，再决定是否碰生产文件。

沙箱做法：/tmp/r159sb/{lead/next_re_20261117_r14,lead}，大文件用符号链接（只读），
只把本轮要改的三件（check_disc.py / DISC_RECHECK.tsv / DISC_UNVERIFIABLE.tsv）拷实体。
沙箱里把 ROOT 反推出来仍是 /tmp/r159sb，故 check_disc.py 会去读沙箱目录。
正控：未改动的沙箱副本跑门禁必须 exit 0（证明沙箱保真，否则后面所有结论都不可信）。
"""
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

R = '/home/t628/projects/ra2-campaign-forge'
D = R + '/lead/next_re_20261117_r14'
SB = '/tmp/r159sb'

fails = []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok:
        fails.append(n)
    return ok

if os.path.isdir(SB):
    shutil.rmtree(SB)
os.makedirs(SB + '/lead/next_re_20261117_r14')

# 大文件/目录走符号链接，三件实体拷贝
for name in os.listdir(D):
    src = os.path.join(D, name)
    dst = os.path.join(SB, 'lead/next_re_20261117_r14', name)
    if name in ('check_disc.py', 'DISC_RECHECK.tsv', 'DISC_UNVERIFIABLE.tsv'):
        shutil.copy2(src, dst)
    else:
        os.symlink(src, dst)
for name in ('GOAL_THREE_TARGETS_20261018.md',):
    src = os.path.join(R, 'lead', name)
    if os.path.exists(src):
        os.symlink(src, os.path.join(SB, 'lead', name))

# 沙箱根下若门禁还要别的顶层物，补齐符号链接
for name in os.listdir(R):
    if name in ('lead',):
        continue
    src = os.path.join(R, name)
    dst = os.path.join(SB, name)
    if not os.path.exists(dst):
        try:
            os.symlink(src, dst)
        except OSError:
            pass

def run_gate(root):
    p = subprocess.run([sys.executable, os.path.join(root, 'lead/next_re_20261117_r14/check_disc.py')],
                       capture_output=True, text=True, timeout=300,
                       cwd=os.path.join(root, 'lead/next_re_20261117_r14'))
    return p.returncode, p.stdout + p.stderr

print('== 0 · 沙箱保真正控 ==')
rc, out = run_gate(SB)
hard = [l for l in out.split('\n') if re.match(r'^\s*(\[FAIL\]|FAIL)\b', l)]
print('  沙箱未改动副本：exit=%d  FAIL行=%d' % (rc, len(hard)))
for l in hard[:5]:
    print('    ', l.strip()[:140])
ck('0.1 沙箱未改动副本 exit 0（沙箱保真）', rc == 0, rc)
ck('0.2 沙箱未改动副本无 FAIL 行', hard == [], len(hard))
ck('0.3 沙箱自报版本 == 生产门禁的当前版本（不写死 R158，S-432 同族）',
   any('ok(R%d)' % n in out for n in range(140, 200)),
   [l.strip() for l in out.split('\n') if l.startswith('C10')][:1])

# ---------- 1 · 在沙箱里执行 r159b 的事务 ----------
print('\n== 1 · 沙箱内预演 r159b（改 3 处 + 重钉 4 处常量）==')
sbG = os.path.join(SB, 'lead/next_re_20261117_r14/check_disc.py')
sbDR = os.path.join(SB, 'lead/next_re_20261117_r14/DISC_RECHECK.tsv')
sbUN = os.path.join(SB, 'lead/next_re_20261117_r14/DISC_UNVERIFIABLE.tsv')
sbBD = sbG + '_bakdir'
os.makedirs(sbBD, exist_ok=True)

script = io.open(R + '/_r159/r159b_fix_c14pin.py', encoding='utf-8').read()
# 把生产路径整体换到沙箱（同样三层深度，ROOT 反推仍正确）
script = script.replace("R = '/home/t628/projects/ra2-campaign-forge'", "R = '%s'" % SB)
script = script.replace("D = R + '/lead/next_re_20261117_r14'", "D = R + '/lead/next_re_20261117_r14'")
script = script.replace("G = D + '/check_disc.py'", "G = D + '/check_disc.py'")
script = script.replace("BD = D + '/R17_LEAD_BASELINE'", "BD = '%s'" % sbBD)
sbscript = '/tmp/r159sb_fix.py'
io.open(sbscript, 'w', encoding='utf-8').write(script)

p = subprocess.run([sys.executable, sbscript], capture_output=True, text=True, timeout=300, cwd=SB)
print(p.stdout[-4000:])
if p.stderr:
    print('--- stderr ---'); print(p.stderr[-2500:])
ck('1.1 沙箱预演脚本 exit 0', p.returncode == 0, p.returncode)
ck('1.2 沙箱预演自身 FAILS=0', 'FAILS=0' in p.stdout,
   [l for l in p.stdout.split('\n') if l.startswith('FAILS=')])

# ---------- 2 · 沙箱独立复跑门禁（第二遍，验证不是脚本自说自话）----------
print('\n== 2 · 沙箱里独立再跑一遍门禁 ==')
rc2, out2 = run_gate(SB)
hard2 = [l for l in out2.split('\n') if re.match(r'^\s*(\[FAIL\]|FAIL)\b', l)]
ck('2.1 沙箱改后门禁 exit 0', rc2 == 0, rc2)
ck('2.2 沙箱改后无 FAIL 行', hard2 == [], hard2[:3])
ck('2.3 沙箱改后自报 R159', 'ok(R159)' in out2, None)
ck('2.4 沙箱改后 C7d ok', 'C7d product/expression fingerprint ok' in out2, None)
ck('2.5 沙箱改后 C12b ok', 'C12b frozen registry mirrors the live table' in out2, None)
ck('2.6 沙箱改后 C14 ok', 'C14 free-text table fingerprint ok' in out2, None)

# ---------- 3 · 幂等：再跑一次事务 ----------
print('\n== 3 · 幂等复跑（第二次执行同一事务）==')
p3 = subprocess.run([sys.executable, sbscript], capture_output=True, text=True, timeout=300, cwd=SB)
ck('3.1 第二次执行 exit 0', p3.returncode == 0, p3.returncode)
ck('3.2 第二次执行 FAILS=0', 'FAILS=0' in p3.stdout,
   [l for l in p3.stdout.split('\n') if l.startswith('FAILS=')])
idem = [l.strip() for l in p3.stdout.split('\n') if 'idempotent' in l]
print('  幂等分支命中 %d 处' % len(idem))
ck('3.3 第二次执行确实走了幂等分支（不是又改了一遍）', len(idem) >= 3, len(idem))

rc3, out3 = run_gate(SB)
ck('3.4 幂等复跑后门禁仍 exit 0', rc3 == 0, rc3)

print('\nFAILS=%d' % len(fails))
sys.exit(0 if not fails else 1)
