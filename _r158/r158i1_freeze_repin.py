#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r158i1_freeze_repin.py — R157 同款收尾：改 DISC_RECHECK 第 20 行后，
冻结档 DISC_UNVERIFIABLE.tsv（id 20）+ C7_TEXT_SHA256 + C7_ROW_SHA['20'] 必须同步重钉。

C12b 要求冻结档 col3/col4 == live col5/col6（镜像，不是第二数据源）；
C7d 钉住 (id, col5, col6) 的整表指纹。
三处必须一起改，否则门禁必 FAIL —— 这正是本轮先踩到的（C12 / C12b / C7d 三 FAIL）。
幂等。
"""
import hashlib, io, os, re, sys, time

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
    if not ok:
        fails.append(n)
    return ok

def rd(p):
    return io.open(p, encoding='utf-8', newline='').read()

dr = rd(DR)
live20 = [l for l in dr.replace('\r\n', '\n').split('\n') if l.startswith('20\t')]
ck('0.1 live 表第 20 行唯一', len(live20) == 1, len(live20))
f_live = live20[0].split('\t')
ck('0.2 live 第 20 行 7 列', len(f_live) == 7, len(f_live))
print('  live col5 =', f_live[4][:70])
print('  live col6 =', f_live[5][:70])
ck('0.3 live col6 已是 R158 锚点', "GATE_VER = 'R158'" in f_live[5], f_live[5][:60])

# ---------- 1 · DISC_UNVERIFIABLE.tsv id 20 ----------
un = rd(UN)
ck('1.0 冻结档 CR 数记录', True, un.count('\r'))
line20 = [l for l in un.replace('\r\n', '\n').split('\n') if l.startswith('20\t')]
ck('1.1 冻结档 id 20 唯一', len(line20) == 1, len(line20))
f_un = line20[0].split('\t')
ck('1.2 冻结档 id 20 至少 4 列', len(f_un) >= 4, len(f_un))
if f_un[2].strip() == f_live[4].strip() and f_un[3].strip() == f_live[5].strip() \
        and f_un[1].strip() == f_live[1].strip():
    print('  [idempotent] 冻结档 id 20 已与 live 镜像一致')
else:
    stamp = time.strftime('%Y%m%d_%H%M%S')
    bak = os.path.join(BD, 'DISC_UNVERIFIABLE.tsv.before_r158_%s.bak' % stamp)
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(open(UN, 'rb').read())
    ck('1.3 冻结档备份已建（wx）', os.path.exists(bak), os.path.basename(bak))
    nl = '\r\n' if '\r\n' in un else '\n'
    newf = list(f_un)
    newf[1] = f_live[1]     # sec
    newf[2] = f_live[4]     # product  <- live col5
    newf[3] = f_live[5]     # expr     <- live col6
    new_line = '\t'.join(newf)
    new_un = un.replace(line20[0], new_line, 1)
    with io.open(UN, 'w', encoding='utf-8', newline='') as f:
        f.write(new_un)
    print('  [written] 冻结档 id 20 已与 live 镜像同步')

un2 = rd(UN)
ck('1.4 冻结档 CR 数未变', un2.count('\r') == un.count('\r'), (un.count('\r'), un2.count('\r')))
f_un2 = [l for l in un2.replace('\r\n', '\n').split('\n') if l.startswith('20\t')][0].split('\t')
ck('1.5 冻结档 id 20 col2/col3/col4 == live col2/col5/col6',
   f_un2[1].strip() == f_live[1].strip() and f_un2[2].strip() == f_live[4].strip()
   and f_un2[3].strip() == f_live[5].strip(),
   (f_un2[1][:20], f_un2[2][:30], f_un2[3][:40]))

# ---------- 2 · FREEZE_SHA256 ----------
src = rd(G)
freeze_sha = hashlib.sha256(open(UN, 'rb').read()).hexdigest()
old_f = re.search(r"FREEZE_SHA256 = '([0-9a-f]{64})'", src)
ck('2.1 能读到 FREEZE_SHA256', old_f is not None, old_f.group(1)[:16] if old_f else None)
if old_f and old_f.group(1) != freeze_sha:
    src = src.replace(old_f.group(1), freeze_sha, 1)
    print('  [repinned] FREEZE_SHA256 %s -> %s' % (old_f.group(1)[:16], freeze_sha[:16]))
else:
    print('  [idempotent] FREEZE_SHA256 已是新值')

# ---------- 3 · C7_TEXT_SHA256 + C7_ROW_SHA ----------
rows = [l.split('\t') for l in dr.replace('\r\n', '\n').split('\n')]
blob = '\n'.join('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip()) for r in rows if len(r) == 7)
new_c7 = hashlib.sha256(blob.encode('utf-8')).hexdigest()
print('  新 C7_TEXT_SHA256 =', new_c7)
old_c7 = re.search(r"C7_TEXT_SHA256 = '([0-9a-f]{64})'", src)
ck('3.1 能读到 C7_TEXT_SHA256', old_c7 is not None, old_c7.group(1)[:16] if old_c7 else None)
if old_c7 and old_c7.group(1) != new_c7:
    src = src.replace(old_c7.group(1), new_c7, 1)
    print('  [repinned] C7_TEXT_SHA256 %s -> %s' % (old_c7.group(1)[:16], new_c7[:16]))
else:
    print('  [idempotent] C7_TEXT_SHA256 已是新值')

# 逐行 sha：只重钉 20（其余必须保持不变，作反控）
m = re.search(r'(?s)C7_ROW_SHA = \{(.*?)\}', src)
ck('3.2 能抽出 C7_ROW_SHA', m is not None, m is not None)
pairs = dict(re.findall(r"'(\d+)':\s*'([0-9a-f]{64})'", m.group(1)))
ck('3.3 C7_ROW_SHA 有 31 项', len(pairs) == 31, len(pairs))
live_row = {}
for r in rows:
    if len(r) == 7:
        live_row[r[0].strip()] = hashlib.sha256(
            ('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip())).encode('utf-8')).hexdigest()
drift = {k: v for k, v in pairs.items() if k in live_row and v != live_row[k]}
print('  漂移的 id =', sorted(drift))
ck('3.4 只有 id 20 漂移（其余 30 项不变，反控）', sorted(drift) == ['20'], sorted(drift))
new_body = m.group(1)
for k in drift:
    new_body = new_body.replace("'%s': '%s'" % (k, pairs[k]), "'%s': '%s'" % (k, live_row[k]), 1)
src = src.replace(m.group(1), new_body, 1)
ck('3.5 C7_ROW_SHA 已含新 id20', ("'20': '%s'" % live_row['20']) in src, live_row['20'][:16])

# ---------- 4 · 写回 check_disc.py ----------
bak = os.path.join(BD, 'check_disc.py.before_r158_repin_%s.bak' % time.strftime('%Y%m%d_%H%M%S'))
fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
with os.fdopen(fd, 'wb') as f:
    f.write(open(G, 'rb').read())
ck('4.0 check_disc.py 备份已建（wx）', os.path.exists(bak), os.path.basename(bak))
with io.open(G, 'w', encoding='utf-8', newline='') as f:
    f.write(src)

back = rd(G)
ck('4.1 FREEZE_SHA256 == 冻结档实 sha', freeze_sha in back, freeze_sha[:16])
ck('4.2 C7_TEXT_SHA256 == 实算', new_c7 in back, new_c7[:16])
ck('4.3 无 CRLF', back.count('\r') == 0, back.count('\r'))
print('\nFAILS=%d' % len(fails))
sys.exit(0 if not fails else 1)
