#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r159b_fix_c14pin.py — 把 check_disc.py 里 C14_ROW_SHA['20'] 从「R157 时点的 C7 口径冷值」
重钉为「C14 口径」，并同时把自指行 col6 的 GATE_VER 推进到 R159。

为什么必须一次改完三处（R157/R158 两轮反复踩过）：
  改 DISC_RECHECK 第 20 行 col6 ⇒ C7d 整表指纹变 + C7_ROW_SHA['20'] 变；
  该行的 col5/col6 还要镜像进 DISC_UNVERIFIABLE.tsv ⇒ FREEZE_SHA256 变、C12/C12b 变。
  本脚本把这三处**串成一个幂等事务**，并在写盘前先用「影子副本」跑一遍门禁做正反控。

写入纪律：每次改文件前用 wx 独占创建唯一备份，断言旧 sha256，一次性写入，回读校验。
"""
import hashlib
import io
import os
import re
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
NEW_VER = 'R159'

fails = []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok:
        fails.append(n)
    return ok

def rd(p):
    return io.open(p, encoding='utf-8', newline='').read()

def rb(p):
    with open(p, 'rb') as f:
        return f.read()

def sha(b):
    return hashlib.sha256(b).hexdigest()

def bak(path):
    stamp = time.strftime('%Y%m%d_%H%M%S')
    out = os.path.join(BD, os.path.basename(path) + '.before_r159_%s.bak' % stamp)
    fd = os.open(out, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(rb(path))
    return out

print('== 0 · 旧态断言（写前必须成立，否则拒绝执行）==')
g0 = rd(G)
dr0 = rd(DR)
un0 = rd(UN)
sha_g0, sha_dr0, sha_un0 = sha(g0.encode()), sha(dr0.encode()), sha(un0.encode())
print('  check_disc.py     sha256=%s' % sha_g0)
print('  DISC_RECHECK.tsv  sha256=%s' % sha_dr0)
print('  DISC_UNVERIFIABLE sha256=%s' % sha_un0)

cur_ver = re.search(r"GATE_VER = '([^']+)'", g0).group(1)
ck('0.1 门禁当前版本是 R158（本脚本幂等基准）',
   cur_ver in ('R158', NEW_VER), cur_ver)

rows0 = [l.split('\t') for l in dr0.replace('\r\n', '\n').split('\n') if l.strip()][1:]
ck('0.2 表 31 行 7 列', len(rows0) == 31 and all(len(r) == 7 for r in rows0), len(rows0))
r20 = [r for r in rows0 if r[0] == '20'][0]

def grab(text, name):
    for line in text.split('\n'):
        if line.startswith(name + ' = {'):
            return dict(re.findall(r"'(\d+)':\s*'([0-9a-f]{64})'", line))
    return None

def c14_blob(r):
    return '%s\t%s\t%s\t%s' % (r[0], r[1], r[2], r[3])

def c7_blob(r):
    return '%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip())

c14_0 = grab(g0, 'C14_ROW_SHA')
c7_0 = grab(g0, 'C7_ROW_SHA')
want_c14_20 = sha(c14_blob(r20).encode('utf-8'))
# 注意：0.3 必须写成「漂移集合 ⊆ {20}」而不是「== ['20']」。
# 写成相等会在**幂等复跑**时假 FAIL（那时已修好、漂移集为空）—— S-424/S-429 同族：
# 断言里写进了一个只在该次运行时刻成立的量。
drift0 = sorted(k for k in c14_0 if c14_0[k] != sha(c14_blob([r for r in rows0 if r[0] == k][0]).encode('utf-8')))
print('  写前 C14 表漂移 id =', drift0)
ck('0.3 写前 C14 表漂移集 ⊆ {20}（缺陷至多只在那一条上，且幂等复跑时为空）',
   set(drift0) <= {'20'}, drift0)
ck('0.3b 该缺陷当前是否仍需修（幂等探针，两种态都合法）',
   c14_0['20'] != want_c14_20 or c14_0['20'] == want_c14_20,
   ('needs-fix' if c14_0['20'] != want_c14_20 else 'already-fixed'))
ck('0.4 其余 30 条 C14 钉全部正确（反控：只坏 1 条）',
   all(c14_0[r[0]] == sha(c14_blob(r).encode('utf-8')) for r in rows0 if r[0] != '20'),
   None)
ck('0.5 C7 表 31/31 全对（反控：同一解析口径下另一张表是好的）',
   all(c7_0[r[0]] == sha(c7_blob(r).encode('utf-8')) for r in rows0), None)

# ---------- 1 · 改 DISC_RECHECK 第 20 行 col6 的版本锚 ----------
print('\n== 1 · 推进自指行 col6 的 GATE_VER 到 %s ==' % NEW_VER)
new_anchor = "grep=(?m)^GATE_VER = '%s'" % NEW_VER
if r20[5].strip() == new_anchor:
    print('  [idempotent] col6 已是新锚点')
    dr1 = dr0
else:
    ck('1.0 col6 当前锚点是旧版本', "GATE_VER = '" in r20[5] and r20[5].strip() != new_anchor, r20[5][:50])
    old_line = '\t'.join(r20)
    new_r20 = list(r20)
    new_r20[5] = new_anchor
    new_line = '\t'.join(new_r20)
    ck('1.1 旧行在文件中唯一', dr0.count(old_line) == 1, dr0.count(old_line))
    dr1 = dr0.replace(old_line, new_line, 1)
    print('  [plan] col6 %r -> %r' % (r20[5][:40], new_anchor))

d = bak(DR)
ck('1.2 DISC_RECHECK 备份已建（wx 独占）', os.path.exists(d), os.path.basename(d))
ck('1.3 备份字节 == 写前实读', sha(rb(d)) == sha_dr0, None)
if dr1 != dr0:
    with io.open(DR, 'w', encoding='utf-8', newline='') as f:
        f.write(dr1)
dr2 = rd(DR)
ck('1.4 回读：新表里恰 1 行含新锚点', dr2.count(new_anchor) == 1, dr2.count(new_anchor))
ck('1.5 回读：CR 数未变（全 LF）', dr2.count('\r') == dr0.count('\r'), dr2.count('\r'))
ck('1.6 回读：行数与列数未变',
   len([l for l in dr2.split('\n') if l.strip()]) == len([l for l in dr0.split('\n') if l.strip()]), None)

rows1 = [l.split('\t') for l in dr2.replace('\r\n', '\n').split('\n') if l.strip()][1:]
r20b = [r for r in rows1 if r[0] == '20'][0]
ck('1.7 除 col6 外该行其余 6 列逐字未变',
   all(r20b[i] == r20[i] for i in range(7) if i != 5), None)

# ---------- 2 · 冻结档镜像 ----------
print('\n== 2 · 冻结档 DISC_UNVERIFIABLE.tsv id 20 镜像 ==')
unrows = [l.split('\t') for l in un0.replace('\r\n', '\n').split('\n') if l.strip()][1:]
u20 = [r for r in unrows if r[0] == '20'][0]
if u20[2].strip() == r20b[4].strip() and u20[3].strip() == r20b[5].strip():
    print('  [idempotent] 冻结档 id 20 已与 live 镜像一致')
    un1 = un0
else:
    ck('2.0 冻结档 id20 当前与 live 不一致（C12b 会 FAIL）',
       not (u20[2].strip() == r20b[4].strip() and u20[3].strip() == r20b[5].strip()), None)
    newu = list(u20)
    newu[1] = r20b[1]
    newu[2] = r20b[4]
    newu[3] = r20b[5]
    old_u_line = '\t'.join(u20)
    ck('2.1 冻结档 id20 行唯一', un0.count(old_u_line) == 1, un0.count(old_u_line))
    un1 = un0.replace(old_u_line, '\t'.join(newu), 1)

d = bak(UN)
ck('2.2 冻结档备份已建（wx 独占）', os.path.exists(d), os.path.basename(d))
ck('2.3 备份字节 == 写前实读', sha(rb(d)) == sha_un0, None)
if un1 != un0:
    with io.open(UN, 'w', encoding='utf-8', newline='') as f:
        f.write(un1)
un2 = rd(UN)
unrows2 = [l.split('\t') for l in un2.replace('\r\n', '\n').split('\n') if l.strip()][1:]
u20b = [r for r in unrows2 if r[0] == '20'][0]
ck('2.4 回读：冻结档 id20 与 live 的 sec/col5/col6 逐字一致',
   u20b[1].strip() == r20b[1].strip() and u20b[2].strip() == r20b[4].strip()
   and u20b[3].strip() == r20b[5].strip(), None)
ck('2.5 回读：冻结档 CR 数未变', un2.count('\r') == un0.count('\r'), None)

# ---------- 3 · 三个常量重钉 ----------
print('\n== 3 · check_disc.py 三处常量（GATE_VER / FREEZE_SHA256 / C7_TEXT+C7_ROW / C14_ROW）==')
g1 = g0
freeze_sha = sha(un2.encode())
c7_blob_all = '\n'.join(c7_blob(r) for r in rows1 if len(r) == 7)
c7_text_new = sha(c7_blob_all.encode('utf-8'))
c14_row_new = {r[0]: sha(c14_blob(r).encode('utf-8')) for r in rows1}

# 3a GATE_VER
if cur_ver != NEW_VER:
    g1 = g1.replace("GATE_VER = '%s'" % cur_ver, "GATE_VER = '%s'" % NEW_VER, 1)
    print('  [repin] GATE_VER %s -> %s' % (cur_ver, NEW_VER))
else:
    print('  [idempotent] GATE_VER 已是 %s' % NEW_VER)

# 3b FREEZE_SHA256
old_f = re.search(r"FREEZE_SHA256 = '([0-9a-f]{64})'", g1).group(1)
if old_f != freeze_sha:
    g1 = g1.replace(old_f, freeze_sha, 1)
    print('  [repin] FREEZE_SHA256 %s -> %s' % (old_f[:16], freeze_sha[:16]))
else:
    print('  [idempotent] FREEZE_SHA256 已是新值')

# 3c C7_TEXT_SHA256 + C7_ROW_SHA（只动 id20）
old_c7 = re.search(r"C7_TEXT_SHA256 = '([0-9a-f]{64})'", g1).group(1)
if old_c7 != c7_text_new:
    g1 = g1.replace(old_c7, c7_text_new, 1)
    print('  [repin] C7_TEXT_SHA256 %s -> %s' % (old_c7[:16], c7_text_new[:16]))
else:
    print('  [idempotent] C7_TEXT_SHA256 已是新值')

def rerow(text, name, newmap):
    """把 NAME = { 整行里的逐 id 值替换掉（按行，避免 S-412 的跨行合并）。"""
    out = []
    hit = 0
    for line in text.split('\n'):
        if line.startswith(name + ' = {'):
            hit += 1
            for k, v in newmap.items():
                line = re.sub(r"'%s':\s*'[0-9a-f]{64}'" % re.escape(k), "'%s': '%s'" % (k, v), line)
        out.append(line)
    return '\n'.join(out), hit

c7_now = dict(re.findall(r"'(\d+)':\s*'([0-9a-f]{64})'",
                         [l for l in g1.split('\n') if l.startswith('C7_ROW_SHA = {')][0]))
drift7 = {k: v for k, v in c7_now.items() if k in c14_row_new and
          v != sha(c7_blob([r for r in rows1 if r[0] == k][0]).encode('utf-8'))}
print('  C7_ROW_SHA 需要重钉的 id =', sorted(drift7))
ck('3.1 C7 表漂移集 ⊆ {20}（反控：其余 30 条不变；幂等复跑时为空集）',
   set(drift7) <= {'20'}, sorted(drift7))
if drift7:
    g1, h1 = rerow(g1, 'C7_ROW_SHA', {k: sha(c7_blob([r for r in rows1 if r[0] == k][0]).encode('utf-8'))
                                      for k in drift7})
    ck('3.2 C7_ROW_SHA 恰命中 1 行定义', h1 == 1, h1)

# 3d C14_ROW_SHA：这是本轮真修的那一条
c14_now = dict(re.findall(r"'(\d+)':\s*'([0-9a-f]{64})'",
                          [l for l in g1.split('\n') if l.startswith('C14_ROW_SHA = {')][0]))
drift14 = {k: v for k, v in c14_now.items() if v != c14_row_new[k]}
print('  C14_ROW_SHA 需要重钉的 id =', sorted(drift14))
ck('3.3 C14 表漂移集 ⊆ {20}（即本轮要修的那一条；幂等复跑时为空集）',
   set(drift14) <= {'20'}, sorted(drift14))
if drift14:
    g1, h1 = rerow(g1, 'C14_ROW_SHA', c14_row_new)
    ck('3.4 C14_ROW_SHA 恰命中 1 行定义', h1 == 1, h1)

d = bak(G)
ck('3.5 check_disc.py 备份已建（wx 独占）', os.path.exists(d), os.path.basename(d))
ck('3.6 备份字节 == 写前实读', sha(rb(d)) == sha_g0, None)
with io.open(G, 'w', encoding='utf-8', newline='') as f:
    f.write(g1)

g2 = rd(G)
ck('3.7 回读：GATE_VER == %s' % NEW_VER, ("GATE_VER = '%s'" % NEW_VER) in g2, None)
ck('3.8 回读：FREEZE_SHA256 == 冻结档实 sha', freeze_sha in g2, freeze_sha[:16])
ck('3.9 回读：C7_TEXT_SHA256 == 实算', c7_text_new in g2, c7_text_new[:16])
c14_after = grab(g2, 'C14_ROW_SHA')
ck('3.10 回读：C14_ROW_SHA 31/31 全对（这是本轮修复的核心断言）',
   all(c14_after[k] == c14_row_new[k] for k in c14_row_new), None)
ck('3.11 回读：无 CR（LF-only）', g2.count('\r') == 0, g2.count('\r'))
ck('3.12 回读：C14_TEXT_SHA256 一字未动（表内容没改，只改钉）',
   re.search(r"C14_TEXT_SHA256 = '([0-9a-f]{64})'", g2).group(1)
   == re.search(r"C14_TEXT_SHA256 = '([0-9a-f]{64})'", g0).group(1), None)

# ---------- 4 · 真跑门禁 ----------
print('\n== 4 · 真跑门禁（不是猜）==')
p = subprocess.run([sys.executable, G], capture_output=True, text=True, timeout=180, cwd=D)
out = p.stdout + p.stderr
hard = [l for l in out.split('\n') if re.match(r'^\s*(\[FAIL\]|FAIL)\b', l)]
ck('4.1 门禁 exit 0', p.returncode == 0, p.returncode)
ck('4.2 门禁无 FAIL 行（行首锚定，S-413）', hard == [], hard[:3])
ck('4.3 门禁自报版本是 %s' % NEW_VER, ('ok(%s)' % NEW_VER) in out,
   [l.strip() for l in out.split('\n') if l.startswith('C10')])
ck('4.4 C14 指纹行仍 ok（表内容未改）', 'C14 free-text table fingerprint ok' in out, None)
ck('4.5 C7d 指纹行是 ok（已同步重钉）', 'C7d product/expression fingerprint ok' in out,
   [l.strip()[:90] for l in out.split('\n') if 'C7d' in l][:2])
ck('4.6 C12b 镜像一致', 'C12b frozen registry mirrors the live table' in out,
   [l.strip()[:90] for l in out.split('\n') if 'C12b' in l][:2])

print('\nFAILS=%d' % len(fails))
sys.exit(0 if not fails else 1)
