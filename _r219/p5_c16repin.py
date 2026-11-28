# -*- coding: utf-8 -*-
"""R219 p5：把 R14_COMMON 新增节 227（R219）钉进 check_disc.C16_FLOORS，并重钉 C16_FLOORS_SHA256。
理由：C16 实测 unpinned 0（R218 已钉到 226），本轮新增 227 ⇒ 必须同步钉入，否则 unpinned 1。
正控：重算旧表（不含 227）的 sha 必须等于现钉值 5fbfe782…
"""
import os, hashlib, re
ROOT = '/home/t628/projects/ra2-campaign-forge'
G = ROOT + '/lead/next_re_20261117_r14/check_disc.py'
RC = ROOT + '/lead/next_re_20261117_r14/R14_COMMON.md'

txt = open(RC, 'rb').read().decode('utf-8')
secs = []; cur = None; buf = []
for l in txt.split('\n'):
    m = re.match(r'^## (2\.(\d+))\b', l)
    if m:
        if cur is not None: secs.append((cur, len('\n'.join(buf).encode('utf-8'))))
        cur = int(m.group(2)); buf = [l]
    elif cur is not None: buf.append(l)
if cur is not None: secs.append((cur, len('\n'.join(buf).encode('utf-8'))))
d = dict(secs)
print('[实测] R14 节数=%d 末三节=%s' % (len(secs), secs[-3:]))
assert secs[-1][0] == 227, secs[-1]

b0 = open(G, 'rb').read(); s0 = b0.decode(); h0 = hashlib.sha256(b0).hexdigest()
m = re.search(r'C16_FLOORS = \{(.*?)\n\}', s0, re.S)
tbl = {}
for ln in m.group(1).split('\n'):
    ln = ln.strip()
    if not ln: continue
    k, v = ln.split(':'); tbl[int(k)] = int(v.strip().rstrip(','))
print('[前态] 已钉=%d 最大 id=%d 227in=%s' % (len(tbl), max(tbl), 227 in tbl))
assert 227 not in tbl
# 正控：重算旧表 sha 必须等于现钉值
oldsha = hashlib.sha256('\n'.join('%d:%d' % (k, tbl[k]) for k in sorted(tbl)).encode()).hexdigest()
pinned = re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'", s0).group(1)
print('[正控] 旧表重算 sha=%s  现钉=%s  一致=%s' % (oldsha[:16], pinned[:16], oldsha == pinned))
assert oldsha == pinned, (oldsha, pinned)

anchor = '    %d: %d,\n}' % (max(tbl), tbl[max(tbl)])
assert s0.count(anchor) == 1, s0.count(anchor)
s1 = s0.replace(anchor, '    %d: %d,\n    %d: %d,\n}' % (max(tbl), tbl[max(tbl)], 227, d[227]))
m2 = re.search(r'C16_FLOORS = \{(.*?)\n\}', s1, re.S)
t2 = {}
for ln in m2.group(1).split('\n'):
    ln = ln.strip()
    if not ln: continue
    k, v = ln.split(':'); t2[int(k)] = int(v.strip().rstrip(','))
assert len(t2) == len(tbl) + 1 and t2[227] == d[227]
sha = hashlib.sha256('\n'.join('%d:%d' % (k, t2[k]) for k in sorted(t2)).encode()).hexdigest()
assert s1.count(pinned) == 1
s2 = s1.replace(pinned, sha)
open(G, 'wb').write(s2.encode('utf-8'))
r = open(G, 'rb').read()
assert sha in r.decode()
print('[写入] C16_FLOORS %d -> %d 节；新增 227:%d' % (len(tbl), len(t2), d[227]))
print('        SHA256 %s -> %s' % (oldsha[:16], sha[:16]))
print('        check_disc bytes %d -> %d sha %s -> %s'
      % (len(b0), len(r), h0[:16], hashlib.sha256(r).hexdigest()[:16]))
