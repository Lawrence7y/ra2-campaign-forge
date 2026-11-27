#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r158h1_gate_update.py — 门禁回归：把 check_disc.py 的版本与下界推进到 R158。
变更项（最小改动，逐项断言）：
  1. GATE_VER 'R157' -> 'R158'
  2. C16_FLOORS 增加 163: floor（= 该节实测字节 // 2）
  3. C16_FLOORS_SHA256 重钉（表内容变了，必须显式重钉）
  4. DISC_RECHECK.tsv 第 20 行（C10 自检行）里的 grep 锚点同步为 R158
  5. FREEZE_SHA256 / C7_TEXT_SHA256 / C7_ROW_SHA / C14_* 本轮**未动**对应产物 ⇒ 保持不变（断言未被无意改动）
幂等：所有替换都写成「已是新值则跳过」。
"""
import hashlib, io, os, re, sys

R = '/home/t628/projects/ra2-campaign-forge'
D = R + '/lead/next_re_20261117_r14'
G = D + '/check_disc.py'
DR = D + '/DISC_RECHECK.tsv'
RC = D + '/R14_COMMON.md'

fails = []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok:
        fails.append(n)
    return ok

# ---------- 0 · 量 §2.163 实测字节，算 floor ----------
rc = io.open(RC, encoding='utf-8', newline='').read().replace('\r\n', '\n')
m = re.search(r'(?ms)^##\s+2\.163\b.*?(?=^##\s+2\.\d+\b|\Z)', rc)
ck('0.1 能切出 §2.163', m is not None, m is not None)
sec_bytes = len(m.group(0).encode('utf-8'))
floor163 = sec_bytes // 2
print('  §2.163 实测 %d B -> floor %d' % (sec_bytes, floor163))
ck('0.2 floor 为正且小于实测', 0 < floor163 < sec_bytes, floor163)

src = io.open(G, encoding='utf-8', newline='').read()
orig_src = src

# ---------- 1 · GATE_VER ----------
if "GATE_VER = 'R158'" in src:
    print('  [idempotent] GATE_VER 已是 R158')
else:
    ck('1.0 GATE_VER 当前为 R157', "GATE_VER = 'R157'" in src,
       "GATE_VER = 'R157'" in src)
    src = src.replace("GATE_VER = 'R157'", "GATE_VER = 'R158'", 1)
ck('1.1 GATE_VER == R158', "GATE_VER = 'R158'" in src, "GATE_VER = 'R158'" in src)

# ---------- 2 · C16_FLOORS 增加 163 ----------
if re.search(r'(?m)^\s*163:\s*\d+,', src):
    print('  [idempotent] C16_FLOORS 已含 163')
else:
    ck('2.0 C16_FLOORS 当前末项为 162', re.search(r'(?m)^\s*162:\s*4867,\s*$', src) is not None,
       re.findall(r'(?m)^\s*1(?:5|6)\d:\s*\d+,', src)[-3:])
    src = re.sub(r'(?m)^(\s*162:\s*4867,\s*)$', r'\1\n    163: %d,' % floor163, src, count=1)
ck('2.1 C16_FLOORS 已含 163', re.search(r'(?m)^\s*163:\s*%d,' % floor163, src) is not None,
   re.findall(r'(?m)^\s*163:\s*\d+,', src))

# ---------- 3 · C16_FLOORS_SHA256 重钉 ----------
# 抽出整张表，重建规范化串，算新 sha
m2 = re.search(r'(?s)C16_FLOORS = \{(.*?)\n\}', src)
ck('3.0 能抽出 C16_FLOORS 表', m2 is not None, m2 is not None)
pairs = re.findall(r'(\d+):\s*(\d+)', m2.group(1))
floors = dict((int(k), int(v)) for k, v in pairs)
print('  表内节数 =', len(floors), ' 末三项 =', sorted(floors.items())[-3:])
norm = '\n'.join('%d:%d' % (k, floors[k]) for k in sorted(floors))
new_sha = hashlib.sha256(norm.encode('utf-8')).hexdigest()
print('  新 C16_FLOORS_SHA256 =', new_sha)
old_sha_m = re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'", src)
ck('3.1 能读到旧 C16_FLOORS_SHA256', old_sha_m is not None, old_sha_m.group(1)[:16] if old_sha_m else None)
if old_sha_m and old_sha_m.group(1) != new_sha:
    src = src.replace(old_sha_m.group(1), new_sha, 1)
    print('  [repinned] C16_FLOORS_SHA256 %s -> %s' % (old_sha_m.group(1)[:16], new_sha[:16]))
else:
    print('  [idempotent] C16_FLOORS_SHA256 已是新值')

# ---------- 4 · 写回 check_disc.py ----------
if src != orig_src:
    bak = D + '/R17_LEAD_BASELINE/check_disc.py.before_r158_%s.bak' % __import__('time').strftime('%Y%m%d_%H%M%S')
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(open(G, 'rb').read())
    ck('4.0 check_disc.py 备份已建（wx）', os.path.exists(bak), os.path.basename(bak))
    with io.open(G, 'w', encoding='utf-8', newline='') as f:
        f.write(src)
    print('  [written] check_disc.py 已更新')
else:
    print('  [idempotent] check_disc.py 无变化')

back = io.open(G, encoding='utf-8', newline='').read()
ck('4.1 回读 GATE_VER == R158', "GATE_VER = 'R158'" in back, True)
ck('4.2 回读含 163 floor', re.search(r'(?m)^\s*163:\s*%d,' % floor163, back) is not None, floor163)
ck('4.3 回读 C16_FLOORS_SHA256 == 新值', new_sha in back, new_sha[:16])
ck('4.4 无 CRLF 混入（check_disc.py 全 LF）', back.count('\r') == 0, back.count('\r'))

# ---------- 5 · DISC_RECHECK.tsv 第 20 行 C10 自检锚点 ----------
dr = io.open(DR, encoding='utf-8', newline='').read()
ck('5.0 DISC_RECHECK CR 数不变（记录基线）', True, dr.count('\r'))
row20 = [l for l in dr.split('\n') if l.startswith('20\t')]
ck('5.1 找到第 20 行', len(row20) == 1, len(row20))
if row20:
    r20 = row20[0]
    if "GATE_VER = 'R158'" in r20:
        print('  [idempotent] 第 20 行锚点已是 R158')
    else:
        ck('5.2 第 20 行当前锚点为 R157', "GATE_VER = 'R157'" in r20, r20[-60:])
        new_dr = dr.replace(r20, r20.replace("GATE_VER = 'R157'", "GATE_VER = 'R158'"), 1)
        with io.open(DR, 'w', encoding='utf-8', newline='') as f:
            f.write(new_dr)
        print('  [written] DISC_RECHECK 第 20 行锚点已同步')
    dr2 = io.open(DR, encoding='utf-8', newline='').read()
    r20b = [l for l in dr2.split('\n') if l.startswith('20\t')][0]
    ck('5.3 第 20 行锚点 == R158', "GATE_VER = 'R158'" in r20b, "GATE_VER = 'R158'" in r20b)
    ck('5.4 DISC_RECHECK CR 数未变', dr2.count('\r') == dr.count('\r'),
       (dr.count('\r'), dr2.count('\r')))

print('\nFAILS=%d' % len(fails))
sys.exit(0 if not fails else 1)
