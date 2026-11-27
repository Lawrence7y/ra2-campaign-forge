# -*- coding: utf-8 -*-
"""R184 E：把事实层门禁从 V564 重钉到 V565（facts_floors 4 处 + gate_runner 1 处 + 指针）。
fail-closed：全部断言在写盘之前；用旧常量复算旧 MASTER 命中旧 pin 作硬闸。
"""
import ast
import hashlib
import io
import os
import re
import sys
import time

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
BASE = os.path.join(TIER, 'R17_LEAD_BASELINE')
FF = os.path.join(ROOT, '_r160/facts_floors.py')
GR = os.path.join(ROOT, '_r161/gate_runner.py')
PTR = os.path.join(TIER, 'FACT_INDEX_CURRENT.md')
OLD_DIR = 'R17_R131_FACTINDEX_V564'
NEW_DIR = 'R17_R131_FACTINDEX_V565'
DST = os.path.join(TIER, NEW_DIR, 'FACT_INDEX.tsv')
stamp = time.strftime('%Y%m%d_%H%M%S')

fails, n = [], 0


def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        fails.append(name)


led = open(DST, 'rb').read()
SHA = hashlib.sha256(led).hexdigest()
print('== G1 · V565 实测 ==')
ck('G1a 字节 == 135931', len(led) == 135931, len(led))
ck('G1b sha == f64d36aaacbc4fbc…', SHA.startswith('f64d36aaacbc4fbc'), SHA[:16])
ck('G1c CR == 0', led.count(b'\r') == 0, led.count(b'\r'))
_lt = led.decode('utf-8').split('\n')
if _lt and _lt[-1] == '':
    _lt = _lt[:-1]
ck('G1d 55 行 × 5 列', len(_lt) == 55 and all(len(x.split('\t')) == 5 for x in _lt), len(_lt))

src = io.open(FF, encoding='utf-8').read()
need = ('CUR_SHA256', 'TOTAL_BYTES', 'MASTER_SHA256', 'GRADES', 'FLOORS', 'EVID', 'EVIDB',
        'LOST', 'ITEMS', 'UNIQ', 'LOST_ITEMS', 'LOST_UNIQ')
C = {}
for node in ast.parse(src).body:
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
        nm = node.targets[0].id
        if nm in need:
            C[nm] = ast.literal_eval(node.value)
print('== G2 · 旧态硬闸 ==')
ck('G2a ast 取到 12 个字面量常量', all(k in C for k in need), [k for k in need if k not in C])
ck('G2b EXPECT_CUR 行指向旧版本目录恰 1 次',
   len(re.findall(r'^EXPECT_CUR = .*%s.*$' % OLD_DIR, src, re.M)) == 1)


def canon_g(d):
    return '\n'.join("    '%s': '%s'," % (k, d[k]) for k in sorted(d))


def canon_f(d):
    return '\n'.join("    '%s': (%d, %d)," % (k, d[k][0], d[k][1]) for k in sorted(d))


def canon_e(d):
    return '\n'.join("    '%s': [%s]," % (k, ', '.join("'%s'" % x for x in d[k])) for k in sorted(d))


def canon_eb(d):
    return '\n'.join("    '%s': %d," % (k, d[k]) for k in sorted(d))


def master(sha, tot, floors):
    return hashlib.sha256(('\n'.join([sha, str(tot), canon_g(C['GRADES']), canon_f(floors),
                                      canon_e(C['EVID']), canon_eb(C['EVIDB']), canon_eb(C['LOST']),
                                      str(C['ITEMS']), str(C['UNIQ']), str(C['LOST_ITEMS']),
                                      str(C['LOST_UNIQ'])])).encode()).hexdigest()


old_m = master(C['CUR_SHA256'], C['TOTAL_BYTES'], C['FLOORS'])
ck('G2c 旧常量复算旧 MASTER 命中旧 pin（硬闸）', old_m == C['MASTER_SHA256'],
   (old_m[:16], C['MASTER_SHA256'][:16]))
ck('G2d 旧 TOTAL_BYTES == 134245', C['TOTAL_BYTES'] == 134245, C['TOTAL_BYTES'])
ck('G2e 旧 FLOORS[F24] == (11349, 36140)', C['FLOORS']['F24'] == (11349, 36140), C['FLOORS']['F24'])

import csv
_r = list(csv.reader(io.StringIO(led.decode('utf-8')), delimiter='\t'))
_d = {x[0]: x for x in _r[1:]}
f24s, f24l = len(_d['F24'][1].encode()), len(_d['F24'][4].encode())
ck('G2f F24 stmt 字节 11419 > 旧 floor 11349', f24s == 11419 and f24s > 11349, f24s)
ck('G2g F24 lim 字节 37746 > 旧 floor 36140', f24l == 37746 and f24l > 36140, f24l)
NEW_FLOORS = dict(C['FLOORS'])
NEW_FLOORS['F24'] = (f24s, f24l)
new_m = master(SHA, len(led), NEW_FLOORS)
ck('G2h 新 MASTER != 旧 MASTER', new_m != old_m, (new_m[:16], old_m[:16]))
ck('G2i 反控 A：把 F24 floor 调大 1 ⇒ MASTER 变',
   master(SHA, len(led), {**NEW_FLOORS, 'F24': (f24s, f24l + 1)}) != new_m)
ck('G2j 反控 B：把新 sha 换回旧的 ⇒ MASTER 变', master(C['CUR_SHA256'], len(led), NEW_FLOORS) != new_m)
ck('G2k 其余 53 条 floor 逐条未变',
   all(NEW_FLOORS[k] == C['FLOORS'][k] for k in C['FLOORS'] if k != 'F24'))

print('== G3 · 构造新源码 ==')
ns = src
ns = ns.replace("'%s'" % OLD_DIR, "'%s'" % NEW_DIR, 1)
ck('G3a 目录号替换：旧 0 次 / 新 1 次', OLD_DIR not in ns and ns.count(NEW_DIR) == 1,
   (ns.count(OLD_DIR), ns.count(NEW_DIR)))
ns = ns.replace("CUR_SHA256 = '%s'" % C['CUR_SHA256'], "CUR_SHA256 = '%s'" % SHA, 1)
ck('G3b CUR_SHA256 已换', ("CUR_SHA256 = '%s'" % SHA) in ns, SHA[:16])
ns = ns.replace("TOTAL_BYTES = %d" % C['TOTAL_BYTES'], "TOTAL_BYTES = %d" % len(led), 1)
ck('G3c TOTAL_BYTES 已换', ("TOTAL_BYTES = %d" % len(led)) in ns, len(led))
ns = ns.replace("    'F24': (11349, 36140),", "    'F24': (%d, %d)," % (f24s, f24l), 1)
ck('G3d F24 floor 行已换', ("    'F24': (%d, %d)," % (f24s, f24l)) in ns, (f24s, f24l))
ns = ns.replace("MASTER_SHA256 = '%s'" % C['MASTER_SHA256'], "MASTER_SHA256 = '%s'" % new_m, 1)
ck('G3e MASTER_SHA256 已换', ("MASTER_SHA256 = '%s'" % new_m) in ns, new_m[:16])
C2 = {}
for node in ast.parse(ns).body:
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
        nm = node.targets[0].id
        if nm in need:
            C2[nm] = ast.literal_eval(node.value)
ck('G3f 新源码 12 常量可 ast 取出', all(k in C2 for k in need))
ck('G3g 新源码 FLOORS 只有 F24 变',
   all(C2['FLOORS'][k] == C['FLOORS'][k] for k in C['FLOORS'] if k != 'F24')
   and C2['FLOORS']['F24'] == (f24s, f24l))
ck('G3h 新源码其余 8 组常量逐字段相同',
   all(C2[k] == C[k] for k in ('GRADES', 'EVID', 'EVIDB', 'LOST', 'ITEMS', 'UNIQ', 'LOST_ITEMS', 'LOST_UNIQ')))
ck('G3i 新源码用新常量复算 MASTER 命中新 pin',
   master(C2['CUR_SHA256'], C2['TOTAL_BYTES'], C2['FLOORS']) == C2['MASTER_SHA256'])
print('     facts_floors 差异行数 = %d' % sum(1 for a, b in zip(src.split('\n'), ns.split('\n')) if a != b))

gr = io.open(GR, encoding='utf-8').read()
ck('G4a gate_runner 含旧目录 1 次', gr.count(OLD_DIR) == 1, gr.count(OLD_DIR))
ck('G4b gate_runner 不持有旧 sha', gr.count(C['CUR_SHA256']) == 0, gr.count(C['CUR_SHA256']))
ck('G4c gate_runner 不持有旧 MASTER', gr.count(C['MASTER_SHA256']) == 0, gr.count(C['MASTER_SHA256']))
ngr = gr.replace("'%s'" % OLD_DIR, "'%s'" % NEW_DIR, 1)
ck('G4d 只改 1 行', sum(1 for a, b in zip(gr.split('\n'), ngr.split('\n')) if a != b) == 1)

ptr = io.open(PTR, encoding='utf-8', newline='').read()
ck('G5a 指针含旧目录恰 2 次（版本目录行 + 相对路径行）', ptr.count(OLD_DIR) == 2, ptr.count(OLD_DIR))
ck('G5b 指针含旧 sha 1 次', ptr.count(C['CUR_SHA256']) == 1, ptr.count(C['CUR_SHA256']))
ck('G5c 指针含旧字节 134245 1 次', ptr.count('| 134245 |') == 1, ptr.count('| 134245 |'))
ck('G5d 指针含旧声明轮次 R183 1 次', ptr.count('| 声明轮次 | R183 |') == 1, ptr.count('| 声明轮次 | R183 |'))
nptr = (ptr.replace(OLD_DIR, NEW_DIR)
        .replace(C['CUR_SHA256'], SHA)
        .replace('| 134245 |', '| %d |' % len(led))
        .replace('| 声明轮次 | R183 |', '| 声明轮次 | R184 |'))
ck('G5e 指针旧目录 0 次 / 新目录 2 次', OLD_DIR not in nptr and nptr.count(NEW_DIR) == 2,
   (nptr.count(OLD_DIR), nptr.count(NEW_DIR)))
# S-184e1：指针「声明依据」里的版本范围自述是过期字段，本轮一并改准（R183 未改它 -> 它写着 530..564）
ck('G5f 指针旧版本范围自述「530..564」在场', '530..564' in nptr, '530..564' in nptr)
nptr = nptr.replace('530..564', '530..565').replace('35 份', '36 份')
ck('G5g 指针版本范围改为 530..565 / 36 份', '530..565' in nptr and '36 份' in nptr)
ck('G5h 指针 CR == 0', nptr.count('\r') == 0, nptr.count('\r'))

if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails))
    sys.exit(1)

print('== G6 · 写盘（备份 + wx 独占 + 回读）==')
for path, newtxt in ((FF, ns), (GR, ngr), (PTR, nptr)):
    oldraw = open(path, 'rb').read()
    o = hashlib.sha256(oldraw).hexdigest()
    bak = os.path.join(BASE, '%s.before_r184_%s.bak' % (os.path.basename(path), stamp))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(oldraw)
    ck('G6a %s 备份独占且 sha 相同' % os.path.basename(path),
       hashlib.sha256(open(bak, 'rb').read()).hexdigest() == o)
    assert open(path, 'rb').read() == oldraw, '母本被外部改动: %s' % path
    io.open(path, 'w', encoding='utf-8', newline='').write(newtxt)
    back = open(path, 'rb').read()
    ck('G6b %s 回读一致' % os.path.basename(path),
       hashlib.sha256(back).hexdigest() == hashlib.sha256(newtxt.encode('utf-8')).hexdigest())
    print('   %-26s %d -> %d B' % (os.path.basename(path), len(oldraw), len(back)))

print()
print('断言 %d 条，FAIL %d 条' % (n, len(fails)))
print('MASTER: %s… -> %s…' % (old_m[:16], new_m[:16]))
sys.exit(1 if fails else 0)
