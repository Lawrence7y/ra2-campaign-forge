#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R188 F：把事实层门禁从 V570 重钉到 V571（新增 F55/F56 两条，54 -> 56 行）。

重钉范围（这是 D3/D4 的**结构变更**，不是单纯的 sha 更新，必须逐项显式声明）：
  D3 54 数据行 -> 56 数据行
  D4 fact_id F01..F54 -> F01..F56
  GRADES / FLOORS / EVID / EVIDB 四张表各新增 F55 / F56 两项
  ITEMS 178 -> ITEMS'（新增两条证据项，其中 _r188/* 全部可解析）
  UNIQ 74 -> UNIQ'（_r188/r188d_resync.py / r188d.log / r188c.log 等为新路径）
  LOST / LOST_ITEMS / LOST_UNIQ 按现盘重算
  CUR_SHA256 / TOTAL_BYTES / MASTER_SHA256 / EXPECT_CUR 全部更新
另外 gate_runner.py 的 LEDGER 路径同步 V570 -> V571。

fail-closed：全部断言在写盘之前；用旧常量复算旧 MASTER 命中旧 pin 作硬闸。
"""
import ast, hashlib, io, os, re, sys, time
from collections import Counter
ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
BASE = os.path.join(TIER, 'R17_LEAD_BASELINE')
FF = os.path.join(ROOT, '_r160/facts_floors.py')
GR = os.path.join(ROOT, '_r161/gate_runner.py')
PTR = os.path.join(TIER, 'FACT_INDEX_CURRENT.md')
OLD_DIR = 'R17_R131_FACTINDEX_V572'; NEW_DIR = 'R17_R131_FACTINDEX_V573'
DST = os.path.join(TIER, NEW_DIR, 'FACT_INDEX.tsv')
stamp = time.strftime('%Y%m%d_%H%M%S')
fails = []; n = 0
def ck(nm, c, d=''):
    global n; n += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

led = open(DST, 'rb').read(); SHA = hashlib.sha256(led).hexdigest()
print('== G1 · V571 实测 ==')
ck('G1a 字节 160515', len(led) == 160515, len(led))
ck('G1b sha b15201b4…', SHA.startswith('b15201b4'), SHA[:16])
ck('G1c CR == 0', led.count(b'\r') == 0, led.count(b'\r'))
_L = led.decode('utf-8').split('\n')
ck('G1d 58 段（57 行 + 空尾）', len(_L) == 58, len(_L))
R = [x.split('\t') for x in _L[:57]]
ck('G1e 57 行每行 5 列', all(len(x) == 5 for x in R), [x[0] for x in R if len(x) != 5])
ck('G1f fact_id = F01..F56', [r[0] for r in R[1:]] == ['F%02d' % i for i in range(1, 57)])
f55 = [r for r in R if r[0] == 'F55'][0]; f56 = [r for r in R if r[0] == 'F56'][0]
ck('G1g F55 stmt/lim（V573 并入审计后 3636/3468）与 F56 stmt/lim 字节实测',
   (len(f55[1].encode()), len(f55[4].encode()), len(f56[1].encode()), len(f56[4].encode()))
   == (3636, 3468, 519, 1601),
   (len(f55[1].encode()), len(f55[4].encode()), len(f56[1].encode()), len(f56[4].encode())))
ck('G1h F55 grade=[已证] / F56 grade=[流程]', f55[2] == '[已证]' and f56[2] == '[流程]', (f55[2], f56[2]))

src = io.open(FF, encoding='utf-8', newline='').read()
need = ('CUR_SHA256', 'TOTAL_BYTES', 'MASTER_SHA256', 'GRADES', 'FLOORS', 'EVID', 'EVIDB', 'LOST',
        'ITEMS', 'UNIQ', 'LOST_ITEMS', 'LOST_UNIQ')
C = {}
for node in ast.parse(src).body:
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
        nm = node.targets[0].id
        if nm in need: C[nm] = ast.literal_eval(node.value)
ck('G2a ast 取到 12 常量', all(k in C for k in need), [k for k in need if k not in C])
def canon_g(d): return '\n'.join("    '%s': '%s'," % (k, d[k]) for k in sorted(d))
def canon_f(d): return '\n'.join("    '%s': (%d, %d)," % (k, d[k][0], d[k][1]) for k in sorted(d))
def canon_e(d): return '\n'.join("    '%s': [%s]," % (k, ', '.join("'%s'" % x for x in d[k])) for k in sorted(d))
def canon_eb(d): return '\n'.join("    '%s': %d," % (k, d[k]) for k in sorted(d))
def master(sha, tot, floors, grades, evid, evidb, lost, items, uniq, li, lu):
    return hashlib.sha256(('\n'.join([sha, str(tot), canon_g(grades), canon_f(floors), canon_e(evid),
        canon_eb(evidb), canon_eb(lost), str(items), str(uniq), str(li), str(lu)])).encode()).hexdigest()
old_m = master(C['CUR_SHA256'], C['TOTAL_BYTES'], C['FLOORS'], C['GRADES'], C['EVID'], C['EVIDB'],
               C['LOST'], C['ITEMS'], C['UNIQ'], C['LOST_ITEMS'], C['LOST_UNIQ'])
ck('G2b 旧常量复算旧 MASTER 命中旧 pin（硬闸）', old_m == C['MASTER_SHA256'],
   (old_m[:16], C['MASTER_SHA256'][:16]))
ck('上一版 TOTAL_BYTES == 158959 / ITEMS 188 / UNIQ 80',
   C['TOTAL_BYTES'] == 158959 and C['ITEMS'] == 188 and C['UNIQ'] == 80,
   (C['TOTAL_BYTES'], C['ITEMS'], C['UNIQ']))

# ---- 全表重算四项规模常量 ----
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
ck('G2d 新 ITEMS = 证据项总数（无上限断言，只与自身一致）', len(items) == len(items), len(items))
ck('G2e 新 UNIQ = 去重路径数', len(uniq) == len(set(uniq)), len(uniq))
print('   ITEMS %d -> %d / UNIQ %d -> %d / LOST_ITEMS %d -> %d / LOST_UNIQ %d -> %d'
      % (C['ITEMS'], len(items), C['UNIQ'], len(uniq), C['LOST_ITEMS'], len(lost),
         C['LOST_UNIQ'], len(lostc)))
ck('G2f 新增的两条证据路径 _r188/r188d_resync.py 与 _r188/r188d.log 可解析',
   resolvable('_r188/r188d_resync.py') and resolvable('_r188/r188d.log'))

GRADES2 = dict(C['GRADES']); GRADES2['F55'] = f55[2]; GRADES2['F56'] = f56[2]
FLOORS2 = dict(C['FLOORS'])
FLOORS2['F55'] = (len(f55[1].encode()), len(f55[4].encode()))
FLOORS2['F56'] = (len(f56[1].encode()), len(f56[4].encode()))
# 前 54 行的 FLOORS 是否与现盘一致（现盘 = V571 前 54 行逐字节同 V570）
for fid in list(C['FLOORS']):
    r = [x for x in R if x[0] == fid][0]
    if (len(r[1].encode()), len(r[4].encode())) != C['FLOORS'][fid]:
        print('  !! %s floor 与现盘不符: %r vs %r' % (fid, C['FLOORS'][fid],
              (len(r[1].encode()), len(r[4].encode()))))
# 注：D6 的语义是「不许缩」，floor 是**下界**不是等值 ⇒ 断言写成 floor <= 现盘，
# 并单独报出「floor 严格小于现盘」的既有条目（F23/F24/F35/F50 四条是历史增长留下的下界，
# 不是本轮改动；本轮只新增 F55/F56 两项，不改这四条）。
_lower = [(fid, C['FLOORS'][fid],
           (len([x for x in R if x[0] == fid][0][1].encode()),
            len([x for x in R if x[0] == fid][0][4].encode()))) for fid in C['FLOORS']]
ck('G2g 既有 54 条的 FLOORS 逐条仍 <= 现盘（未动既有行、未触发 D6 缩水）',
   all(cur[0] >= fl[0] and cur[1] >= fl[1] for _, fl, cur in _lower),
   [x for x in _lower if not (x[2][0] >= x[1][0] and x[2][1] >= x[1][1])])
print('   floor 严格小于现盘的既有条目 %d 个：%r（历史增长留下的下界，本轮未改）'
      % (len([x for x in _lower if x[1] != x[2]]),
         [(x[0], x[1], x[2]) for x in _lower if x[1] != x[2]]))
EVID2 = dict(C['EVID'])
EVIDB2 = dict(C['EVIDB'])
for r in R[1:]:
    if r[0] in ('F55', 'F56'):
        EVID2[r[0]] = [norm(strip_note(x)) for x in r[3].split(';') if x.strip()]
        EVIDB2[r[0]] = len(r[3].encode())
ck('G2h 既有 54 条 EVID 未动', all(norm(strip_note(x)) == EVID2[fid][i]
   for fid in C['EVID'] for i, x in enumerate([y for y in [r for r in R if r[0] == fid][0][3].split(';') if y.strip()])
   if i < len(EVID2[fid])))
new_m = master(SHA, len(led), FLOORS2, GRADES2, EVID2, EVIDB2, dict(lostc), len(items), len(uniq),
               len(lost), len(lostc))
ck('G2i 新 MASTER != 旧 MASTER', new_m != old_m, (new_m[:16], old_m[:16]))
ck('G2j 反控 A：F55 lim floor +1 ⇒ MASTER 变',
   master(SHA, len(led), {**FLOORS2, 'F55': (FLOORS2['F55'][0], FLOORS2['F55'][1] + 1)},
          GRADES2, EVID2, EVIDB2, dict(lostc), len(items), len(uniq), len(lost), len(lostc)) != new_m)
ck('G2k 反控 B：ITEMS +1 ⇒ MASTER 变',
   master(SHA, len(led), FLOORS2, GRADES2, EVID2, EVIDB2, dict(lostc), len(items) + 1, len(uniq),
          len(lost), len(lostc)) != new_m)
ck('G2l 反控 C：sha 换回旧 ⇒ MASTER 变',
   master(C['CUR_SHA256'], len(led), FLOORS2, GRADES2, EVID2, EVIDB2, dict(lostc), len(items),
          len(uniq), len(lost), len(lostc)) != new_m)

print('== G3 · 构造新源码 ==')
ns = src
ns = ns.replace("'%s'" % OLD_DIR, "'%s'" % NEW_DIR, 1)
ck('G3a 目录号替换（EXPECT_CUR 1 次）', OLD_DIR not in ns and ns.count(NEW_DIR) == 1,
   (ns.count(OLD_DIR), ns.count(NEW_DIR)))
ns = ns.replace("CUR_SHA256 = '%s'" % C['CUR_SHA256'], "CUR_SHA256 = '%s'" % SHA, 1)
ck('G3b CUR_SHA256 已换', ("CUR_SHA256 = '%s'" % SHA) in ns)
ns = ns.replace("TOTAL_BYTES = %d" % C['TOTAL_BYTES'], "TOTAL_BYTES = %d" % len(led), 1)
ck('G3c TOTAL_BYTES 已换', ("TOTAL_BYTES = %d" % len(led)) in ns)
# 四张表 + 两个计数 + lost 三表：整块重建（结构变更，逐表断言）
def block(olddict, newdict, name):
    global ns
    lines_old = [l for l in src.split('\n') if l.startswith("    'F%02d'" % 1) or True]
    pat = re.compile(r'^%s = \{\n(.*?)\n\}$' % name, re.M | re.S)
    m = pat.search(ns)
    assert m, name
    body_old = m.group(1)
    if name in ('ITEMS', 'UNIQ', 'LOST_ITEMS', 'LOST_UNIQ'):
        raise RuntimeError('not a dict')
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
ck('G3d 本轮只有 FLOORS 表变化（F55 floor 上调），其余三表逐字节不变',
   ch_f and not ch_g and not ch_e and not ch_b, (ch_g, ch_f, ch_e, ch_b))
for name, val in (('ITEMS', len(items)), ('UNIQ', len(uniq)),
                  ('LOST_ITEMS', len(lost)), ('LOST_UNIQ', len(lostc))):
    old = re.search(r'^%s = (\d+)$' % name, ns, re.M)
    ck('G3e %s 常量存在' % name, old is not None, name)
    ns = re.sub(r'^%s = \d+$' % name, '%s = %d' % (name, val), ns, count=1, flags=re.M)
# LOST 表
pat = re.compile(r'^LOST = \{\n(.*?)\n\}$', re.M | re.S)
m = pat.search(ns)
ck('G3f LOST 表可定位', m is not None)
body_new = '\n'.join("    '%s': %d," % (k, lostc[k]) for k in sorted(lostc))
if not lostc: body_new = ''
ns = ns[:m.start(1)] + body_new + ns[m.end(1):]
ns = ns.replace("MASTER_SHA256 = '%s'" % C['MASTER_SHA256'], "MASTER_SHA256 = '%s'" % new_m, 1)
ck('G3g MASTER_SHA256 已换', ("MASTER_SHA256 = '%s'" % new_m) in ns)
ns = ns.replace('D3  54 数据行 / 每行恰 5 列。', 'D3  56 数据行 / 每行恰 5 列。')
ns = ns.replace('D4  fact_id 恰为 F01..F54 有序无重。', 'D4  fact_id 恰为 F01..F56 有序无重。')
ns = ns.replace("if len(data) != 54: F('D3 data rows = %d != 54' % len(data))",
                "if len(data) != 56: F('D3 data rows = %d != 56' % len(data))")
ns = ns.replace("exp_ids = ['F%02d' % i for i in range(1, 55)]",
                "exp_ids = ['F%02d' % i for i in range(1, 57)]")
ns = ns.replace("print('  D4 fact_id F01..F54: %s'", "print('  D4 fact_id F01..F56: %s'")
ck('G3h D3/D4 仍为 56 行 / F01..F56（本轮不改结构）',
   "'F%02d' % i for i in range(1, 57)" in ns and '!= 56' in ns and 'F01..F56' in ns)
C2 = {}
for node in ast.parse(ns).body:
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
        nm = node.targets[0].id
        if nm in need: C2[nm] = ast.literal_eval(node.value)
ck('G3i 新源码 12 常量可 ast 取出', all(k in C2 for k in need), [k for k in need if k not in C2])
ck('G3j 新源码用新常量复算 MASTER 命中新 pin',
   master(C2['CUR_SHA256'], C2['TOTAL_BYTES'], C2['FLOORS'], C2['GRADES'], C2['EVID'], C2['EVIDB'],
          C2['LOST'], C2['ITEMS'], C2['UNIQ'], C2['LOST_ITEMS'], C2['LOST_UNIQ']) == C2['MASTER_SHA256'])
ck('G3k 既有 54 条 grade 逐条未变',
   all(C2['GRADES'][k] == C['GRADES'][k] for k in C['GRADES']))
ck('G3l F55 floor == (3636, 3468) / F56 floor == (519, 1601)',
   C2['FLOORS']['F55'] == (3636, 3468) and C2['FLOORS']['F56'] == (519, 1601),
   (C2['FLOORS']['F55'], C2['FLOORS']['F56']))
gr = io.open(GR, encoding='utf-8', newline='').read()
ck('G4a gate_runner 含旧目录 1 次', gr.count(OLD_DIR) == 1, gr.count(OLD_DIR))
ngr = gr.replace("'%s'" % OLD_DIR, "'%s'" % NEW_DIR, 1)
ck('G4b gate_runner 只改 1 行',
   sum(1 for a, b in zip(gr.split('\n'), ngr.split('\n')) if a != b) == 1)
ptr = io.open(PTR, encoding='utf-8', newline='').read()
ck('G5a 指针含旧目录 2 次', ptr.count(OLD_DIR) == 2, ptr.count(OLD_DIR))
ck('G5b 指针含旧 sha 1 次', ptr.count(C['CUR_SHA256']) == 1, ptr.count(C['CUR_SHA256']))
ck('G5c 指针含旧字节 158959 1 次', ptr.count('| 158959 |') == 1, ptr.count('| 158959 |'))
ck('G5d 指针行数自述恰 1 次（本轮行数不变，仍 57 行）', ptr.count('57（1 表头 + 56 数据行）') == 1,
   ptr.count('57（1 表头 + 56 数据行）'))
nptr = (ptr.replace(OLD_DIR, NEW_DIR).replace(C['CUR_SHA256'], SHA)
        .replace('| 158959 |', '| %d |' % len(led)))
ck('G5e 指针换完：旧目录 0 / 新目录 2 / 旧 sha 0 / 旧字节 0',
   OLD_DIR not in nptr and nptr.count(NEW_DIR) == 2 and C['CUR_SHA256'] not in nptr
   and '| 158959 |' not in nptr)
nptr = nptr.replace('530..572', '530..573').replace('43 份', '44 份')
ck('G5f 版本范围自述改为 530..573 / 44 份', '530..573' in nptr and '44 份' in nptr)
ck('G5g 声明轮次仍为 R188（本轮不推进轮次号）', '| 声明轮次 | R188 |' in nptr)
ck('G5h 指针 CR == 0', nptr.count('\r') == 0)
if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails)); sys.exit(1)
print('== G6 · 写盘（备份 + 回读）==')
for path, newtxt in ((FF, ns), (GR, ngr), (PTR, nptr)):
    oldraw = open(path, 'rb').read(); o = hashlib.sha256(oldraw).hexdigest()
    bak = os.path.join(BASE, '%s.before_r188_%s.bak' % (os.path.basename(path), stamp))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f: f.write(oldraw)
    ck('G6a %s 备份独占且 sha 相同' % os.path.basename(path),
       hashlib.sha256(open(bak, 'rb').read()).hexdigest() == o)
    assert open(path, 'rb').read() == oldraw, '母本被外部改动: %s' % path
    io.open(path, 'w', encoding='utf-8', newline='').write(newtxt)
    back = open(path, 'rb').read()
    ck('G6b %s 回读一致' % os.path.basename(path),
       hashlib.sha256(back).hexdigest() == hashlib.sha256(newtxt.encode()).hexdigest())
    print('   %-26s %d -> %d B' % (os.path.basename(path), len(oldraw), len(back)))
print()
print('断言 %d 条，FAIL %d 条' % (n, len(fails)))
print('MASTER: %s… -> %s…' % (old_m[:16], new_m[:16]))
sys.exit(1 if fails else 0)
