#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R190 E：把事实层门禁从 V574 重钉到 V575。

结构不变（57 行 / F01..F56）。要动的常量：
  EXPECT_CUR 目录号、CUR_SHA256、TOTAL_BYTES、MASTER_SHA256
  FLOORS['F55']、EVID['F55']、EVIDB['F55']
  gate_runner.py 的 LEDGER 路径、FACT_INDEX_CURRENT.md 四个字段
其余 55 行四张常量表逐字节不变。fail-closed；用旧常量复算旧 MASTER 命中旧 pin 作硬闸。
"""
import ast, hashlib, io, os, re, sys, time
from collections import Counter
ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
FF = os.path.join(ROOT, '_r160/facts_floors.py')
GR = os.path.join(ROOT, '_r161/gate_runner.py')
PTR = os.path.join(TIER, 'FACT_INDEX_CURRENT.md')
OLD_DIR = 'R17_R131_FACTINDEX_V574'; NEW_DIR = 'R17_R131_FACTINDEX_V575'
DST = os.path.join(TIER, NEW_DIR, 'FACT_INDEX.tsv')
fails = []; n = 0
def ck(nm, c, d=''):
    global n; n += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

led = open(DST, 'rb').read(); SHA = hashlib.sha256(led).hexdigest()
ck('G1 V575 字节 167276 / sha ec21be7a… / CR 0',
   len(led) == 167276 and SHA.startswith('ec21be7a') and led.count(b'\r') == 0,
   (len(led), SHA[:16]))
_L = led.decode('utf-8').split('\n')
ck('G1b 58 段 / 57 行 5 列', len(_L) == 58 and all(len(x.split('\t')) == 5 for x in _L[:57]))
R = [x.split('\t') for x in _L[:57]]
ck('G1c fact_id F01..F56 连续', [r[0] for r in R[1:]] == ['F%02d' % i for i in range(1, 57)])
f55 = [r for r in R if r[0] == 'F55'][0]
ck('G1d F55 stmt 7937 / lim 5791 / evid 247',
   (len(f55[1].encode()), len(f55[4].encode()), len(f55[3].encode())) == (7937, 5791, 247),
   (len(f55[1].encode()), len(f55[4].encode()), len(f55[3].encode())))
src = io.open(FF, encoding='utf-8', newline='').read()
need = ('CUR_SHA256', 'TOTAL_BYTES', 'MASTER_SHA256', 'GRADES', 'FLOORS', 'EVID',
        'EVIDB', 'LOST', 'ITEMS', 'UNIQ', 'LOST_ITEMS', 'LOST_UNIQ')
C = {}
for node in ast.parse(src).body:
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
        nm = node.targets[0].id
        if nm in need: C[nm] = ast.literal_eval(node.value)
ck('G2 ast 取到 12 常量', all(k in C for k in need), [k for k in need if k not in C])
def canon_g(d): return '\n'.join("    '%s': '%s'," % (k, d[k]) for k in sorted(d))
def canon_f(d): return '\n'.join("    '%s': (%d, %d)," % (k, d[k][0], d[k][1]) for k in sorted(d))
def canon_e(d): return '\n'.join("    '%s': [%s]," % (k, ', '.join("'%s'" % x for x in d[k])) for k in sorted(d))
def canon_eb(d): return '\n'.join("    '%s': %d," % (k, d[k]) for k in sorted(d))
def master(sha, tot, floors, grades, evid, evidb, lost, items, uniq, li, lu):
    return hashlib.sha256(('\n'.join([sha, str(tot), canon_g(grades), canon_f(floors), canon_e(evid),
        canon_eb(evidb), canon_eb(lost), str(items), str(uniq), str(li), str(lu)])).encode()).hexdigest()
old_m = master(C['CUR_SHA256'], C['TOTAL_BYTES'], C['FLOORS'], C['GRADES'], C['EVID'], C['EVIDB'],
               C['LOST'], C['ITEMS'], C['UNIQ'], C['LOST_ITEMS'], C['LOST_UNIQ'])
ck('G2b 旧常量复算旧 MASTER 命中旧 pin（硬闸）', old_m == C['MASTER_SHA256'], (old_m[:16], C['MASTER_SHA256'][:16]))
ck('G2c 上一版 TOTAL_BYTES 162625 / ITEMS 191 / UNIQ 83 / LOST 43/16',
   (C['TOTAL_BYTES'], C['ITEMS'], C['UNIQ'], C['LOST_ITEMS'], C['LOST_UNIQ']) == (162625, 191, 83, 43, 16),
   (C['TOTAL_BYTES'], C['ITEMS'], C['UNIQ'], C['LOST_ITEMS'], C['LOST_UNIQ']))
def strip_note(s):
    s = s.strip()
    if s.endswith(')'):
        d = 0
        for i in range(len(s) - 1, -1, -1):
            if s[i] == ')': d += 1
            elif s[i] == '(':
                d -= 1
                if d == 0: return s[:i].strip()
    return s
def norm(p): return p.replace('\\', '/').strip()
def resolvable(p):
    for c in (p, 'lead/' + p, TIER + '/' + p):
        if os.path.exists(os.path.join(ROOT, c)): return True
    return False
items = []
for r in R[1:]:
    for x in r[3].split(';'):
        if x.strip(): items.append((r[0], norm(strip_note(x))))
uniq = set(p for _, p in items)
lost = [p for _, p in items if not resolvable(p)]
lostc = Counter(lost)
print('   ITEMS %d -> %d / UNIQ %d -> %d / LOST %d -> %d / LOST_UNIQ %d -> %d'
      % (C['ITEMS'], len(items), C['UNIQ'], len(uniq), C['LOST_ITEMS'], len(lost), C['LOST_UNIQ'], len(lostc)))
ck('G2d ITEMS/UNIQ 各 +3、LOST 两项未增',
   (len(items) - C['ITEMS'], len(uniq) - C['UNIQ'], len(lost) - C['LOST_ITEMS'],
    len(lostc) - C['LOST_UNIQ']) == (3, 3, 0, 0),
   (len(items) - C['ITEMS'], len(uniq) - C['UNIQ'], len(lost) - C['LOST_ITEMS'], len(lostc) - C['LOST_UNIQ']))
ck('G2e 三条新路径都可解析', all(resolvable(x) for x in
   ('_r190/r190a_groups.py', '_r190/r190b_thunks.py', '_r190/r190c_rtti.py')))
ck('G2f LOST 多重集逐键未变', dict(lostc) == C['LOST'])
GRADES2 = dict(C['GRADES']); FLOORS2 = dict(C['FLOORS'])
FLOORS2['F55'] = (len(f55[1].encode()), len(f55[4].encode()))
EVID2 = dict(C['EVID']); EVIDB2 = dict(C['EVIDB'])
EVID2['F55'] = [norm(strip_note(x)) for x in f55[3].split(';') if x.strip()]
EVIDB2['F55'] = len(f55[3].encode())
ck('G2g FLOORS["F55"] (5406,3735) -> (%d,%d)' % (FLOORS2['F55'][0], FLOORS2['F55'][1]),
   C['FLOORS']['F55'] == (5406, 3735) and FLOORS2['F55'] == (7937, 5791), FLOORS2['F55'])
ck('G2h EVIDB["F55"] 183 -> 247', C['EVIDB']['F55'] == 183 and EVIDB2['F55'] == 247,
   (C['EVIDB']['F55'], EVIDB2['F55']))
ck('G2i EVID["F55"] 由 8 条变 11 条、前 8 条逐项未动',
   len(EVID2['F55']) == 11 and EVID2['F55'][:8] == C['EVID']['F55'], len(EVID2['F55']))
_low = []
for fid in C['FLOORS']:
    if fid == 'F55': continue
    r = [x for x in R if x[0] == fid][0]
    cur = (len(r[1].encode()), len(r[4].encode())); fl = C['FLOORS'][fid]
    if not (cur[0] >= fl[0] and cur[1] >= fl[1]): _low.append((fid, fl, cur))
ck('G2j 既有 55 条 FLOORS 仍全部 <= 现盘（未触发 D6 缩水）', not _low, _low[:3])
ck('G2k 既有 55 条 grade 逐条未变',
   all(C['GRADES'][k] == [x for x in R if x[0] == k][0][2] for k in C['GRADES'] if k != 'F55'))
new_m = master(SHA, len(led), FLOORS2, GRADES2, EVID2, EVIDB2, dict(lostc),
               len(items), len(uniq), len(lost), len(lostc))
ck('G2l 新 MASTER != 旧 MASTER', new_m != old_m, (new_m[:16], old_m[:16]))
ck('G2m 反控 A：F55 lim floor +1 ⇒ MASTER 变',
   master(SHA, len(led), {**FLOORS2, 'F55': (7937, 5792)}, GRADES2, EVID2, EVIDB2, dict(lostc),
          len(items), len(uniq), len(lost), len(lostc)) != new_m)
ck('G2n 反控 B：EVIDB["F55"] +1 ⇒ MASTER 变',
   master(SHA, len(led), FLOORS2, GRADES2, EVID2, {**EVIDB2, 'F55': 248}, dict(lostc),
          len(items), len(uniq), len(lost), len(lostc)) != new_m)
ck('G2o 反控 C：ITEMS +1 ⇒ MASTER 变',
   master(SHA, len(led), FLOORS2, GRADES2, EVID2, EVIDB2, dict(lostc), len(items) + 1,
          len(uniq), len(lost), len(lostc)) != new_m)
ns = src
ns = ns.replace("'%s'" % OLD_DIR, "'%s'" % NEW_DIR, 1)
ck('G3a EXPECT_CUR 目录号已换且只 1 处', OLD_DIR not in ns and ns.count(NEW_DIR) == 1,
   (ns.count(OLD_DIR), ns.count(NEW_DIR)))
ns = ns.replace("CUR_SHA256 = '%s'" % C['CUR_SHA256'], "CUR_SHA256 = '%s'" % SHA, 1)
ck('G3b CUR_SHA256 已换', ("CUR_SHA256 = '%s'" % SHA) in ns)
ns = ns.replace("TOTAL_BYTES = %d" % C['TOTAL_BYTES'], "TOTAL_BYTES = %d" % len(led), 1)
ck('G3c TOTAL_BYTES 已换', ("TOTAL_BYTES = %d" % len(led)) in ns)
def block(olddict, newdict, name):
    global ns
    pat = re.compile(r'^%s = \{\n(.*?)\n\}$' % name, re.M | re.S)
    m = pat.search(ns); assert m, name
    body_old = m.group(1)
    body_new = '\n'.join("    '%s': %s," % (k, ("'%s'" % newdict[k]) if isinstance(newdict[k], str)
                          else ('(%d, %d)' % newdict[k] if isinstance(newdict[k], tuple)
                                else ('%d' % newdict[k] if isinstance(newdict[k], int)
                                      else '[%s]' % ', '.join("'%s'" % x for x in newdict[k]))))
                          for k in sorted(newdict))
    ns = ns[:m.start(1)] + body_new + ns[m.end(1):]
    return body_old != body_new
ch_g = block(C['GRADES'], GRADES2, 'GRADES')
ch_f = block(C['FLOORS'], FLOORS2, 'FLOORS')
ch_e = block(C['EVID'], EVID2, 'EVID')
ch_b = block(C['EVIDB'], EVIDB2, 'EVIDB')
ck('G3d 只有 FLOORS / EVID / EVIDB 三表变化（grade 表逐字节不变）',
   ch_f and ch_e and ch_b and not ch_g, (ch_g, ch_f, ch_e, ch_b))
for name, val in (('ITEMS', len(items)), ('UNIQ', len(uniq)),
                  ('LOST_ITEMS', len(lost)), ('LOST_UNIQ', len(lostc))):
    ns = re.sub(r'^%s = \d+$' % name, '%s = %d' % (name, val), ns, count=1, flags=re.M)
pat = re.compile(r'^LOST = \{\n(.*?)\n\}$', re.M | re.S)
m = pat.search(ns); ck('G3e LOST 表可定位', m is not None)
ns = ns[:m.start(1)] + '\n'.join("    '%s': %d," % (k, lostc[k]) for k in sorted(lostc)) + ns[m.end(1):]
ns = ns.replace("MASTER_SHA256 = '%s'" % C['MASTER_SHA256'], "MASTER_SHA256 = '%s'" % new_m, 1)
ck('G3f MASTER_SHA256 已换', ("MASTER_SHA256 = '%s'" % new_m) in ns)
ck('G3g D3/D4 结构未动（仍 56 行 / F01..F56）', '!= 56' in ns and 'range(1, 57)' in ns and 'F01..F56' in ns)
C2 = {}
for node in ast.parse(ns).body:
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
        nm = node.targets[0].id
        if nm in need: C2[nm] = ast.literal_eval(node.value)
ck('G3h 新源码 12 常量可 ast 取出', all(k in C2 for k in need))
ck('G3i 新源码用新常量复算 MASTER 命中新 pin',
   master(C2['CUR_SHA256'], C2['TOTAL_BYTES'], C2['FLOORS'], C2['GRADES'], C2['EVID'], C2['EVIDB'],
          C2['LOST'], C2['ITEMS'], C2['UNIQ'], C2['LOST_ITEMS'], C2['LOST_UNIQ']) == C2['MASTER_SHA256'])
ck('G3j 新源码 F55 floor == (7937, 5791) 且 EVIDB 247',
   C2['FLOORS']['F55'] == (7937, 5791) and C2['EVIDB']['F55'] == 247,
   (C2['FLOORS']['F55'], C2['EVIDB']['F55']))
ck('G3k 既有 55 条 grade 逐条未变', all(C2['GRADES'][k] == C['GRADES'][k] for k in C['GRADES']))
gr = io.open(GR, encoding='utf-8', newline='').read()
ck('G4a gate_runner 含旧目录 1 次', gr.count(OLD_DIR) == 1, gr.count(OLD_DIR))
gr2 = gr.replace(OLD_DIR, NEW_DIR, 1)
ck('G4b gate_runner 换后含新目录 1 次 / 旧目录 0 次',
   gr2.count(NEW_DIR) == 1 and gr2.count(OLD_DIR) == 0)
ptr = io.open(PTR, encoding='utf-8', newline='').read()
ck('G5a0 旧版本目录串在指针里出现 2 次（版本目录行 + 相对路径行）', ptr.count(OLD_DIR) == 2, ptr.count(OLD_DIR))
for old, new, tag in ((C['CUR_SHA256'], SHA, 'P2 sha256'),
                      (str(C['TOTAL_BYTES']), str(len(led)), 'P3 字节数'),
                      ('530..574 连续 45 份', '530..575 连续 46 份', 'P4 自述份数'),
                      ('| 声明轮次 | R189 |', '| 声明轮次 | R190 |', 'P5 声明轮次')):
    ck('G5a %s 在指针里恰 1 次' % tag, ptr.count(old) == 1, ptr.count(old))
ptr2 = ptr.replace(OLD_DIR, NEW_DIR).replace(C['CUR_SHA256'], SHA, 1) \
    .replace(str(C['TOTAL_BYTES']), str(len(led)), 1) \
    .replace('530..574 连续 45 份', '530..575 连续 46 份', 1) \
    .replace('| 声明轮次 | R189 |', '| 声明轮次 | R190 |', 1)
ck('G5b 指针新体含 V575 与 R190', NEW_DIR in ptr2 and '| 声明轮次 | R190 |' in ptr2)
if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails)); sys.exit(1)
print('== 写盘 ==')
BL = os.path.join(TIER, 'R17_LEAD_BASELINE'); stamp = time.strftime('%Y%m%d_%H%M%S')
for path, oldraw, newtxt, tag in ((FF, src.encode(), ns, 'facts_floors'),
                                  (GR, gr.encode(), gr2, 'gate_runner'),
                                  (PTR, ptr.encode(), ptr2, 'ptr')):
    bak = os.path.join(BL, '%s.before_r190_repin_%s.bak' % (tag, stamp))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f: f.write(oldraw)
    ck('W1 %s 备份 sha 一致' % tag,
       hashlib.sha256(open(bak, 'rb').read()).hexdigest() == hashlib.sha256(oldraw).hexdigest())
    assert open(path, 'rb').read() == oldraw, '%s 被外部改动' % tag
    io.open(path, 'w', encoding='utf-8', newline='').write(newtxt)
    ck('W2 %s 回读一致' % tag,
       hashlib.sha256(open(path, 'rb').read()).hexdigest() == hashlib.sha256(newtxt.encode()).hexdigest())
print('\nMASTER %s… -> %s…' % (C['MASTER_SHA256'][:16], new_m[:16]))
print('断言 %d 条，FAIL %d 条' % (n, len(fails)))
sys.exit(1 if fails else 0)
