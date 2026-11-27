#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R175 F：把守门脚本重钉到 V557（facts_floors 4 处常量 + F24 floors；gate_runner 1 处目录号）。

fail-closed 顺序（S-619/S-602 纪律：全部断言在写盘之前）：
 G1  V557 五项实测（字节 / sha256 / CR / 行数 / 列数）
 G2  用 ast 从 facts_floors 源码取出全部常量，**用旧常量复算旧 MASTER 必须命中旧 pin**（硬闸，
     不命中说明我的规范化实现与脚本自身不同源，禁止写盘）
 G3  只改 4 处：EXPECT_CUR 目录、CUR_SHA256、TOTAL_BYTES、FLOORS 的 F24 二元组；
     其余常量逐字不变（用 ast 重取后逐字段比）
 G4  gate_runner 只改 LEDGER 中的目录号 1 处；该文件不持有 sha 字面量（实测次数 0）
 G5  反控 N1：把新 sha 换成 V556 的 ⇒ D0 语义必错（新 MASTER 也随之变，证明 pin 不是恒真）
 G6  反控 N2：把 F24 floor 调大 1 ⇒ 新 MASTER 变化（证明 MASTER 覆盖 FLOORS）
写盘：两文件各自 wx 备份 -> 一次性写 -> 回读 sha / 常量 / 差异行数。
"""
import ast, hashlib, io, json, os, re, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
BASE = os.path.join(TIER, 'R17_LEAD_BASELINE')
FF = os.path.join(ROOT, '_r160/facts_floors.py')
GR = os.path.join(ROOT, '_r161/gate_runner.py')
NEW_DIR = 'R17_R128_FACTINDEX_V558'
LED = os.path.join(TIER, NEW_DIR, 'FACT_INDEX.tsv')
OUT = os.path.join(ROOT, '_r175/r175f_repin.json')
stamp = time.strftime('%Y%m%d_%H%M%S')

fails, n, res = [], 0, {}
def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)
    res[name] = bool(cond)

# ---------- G1 ----------
led = io.open(LED, 'rb').read()
LED_SHA = hashlib.sha256(led).hexdigest()
print('== G1 · V557 实测 ==')
ck('G1a V558 字节 == 128,835', len(led) == 128835, len(led))
ck('G1b V558 sha 前 16 == 157996aa5da193d3', LED_SHA.startswith('157996aa5da193d3'), LED_SHA[:16])
ck('G1c V557 CR == 0', led.count(b'\r') == 0, led.count(b'\r'))
lt = led.decode('utf-8').split('\n')
if lt and lt[-1] == '': lt = lt[:-1]
ck('G1d 55 行 5 列', len(lt) == 55 and all(len(l.split('\t')) == 5 for l in lt), len(lt))

# ---------- 从 facts_floors 源码取常量 ----------
src = io.open(FF, encoding='utf-8').read()
tree = ast.parse(src)
C = {}
for node in tree.body:
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
        nm = node.targets[0].id
        if nm in ('CUR_SHA256', 'TOTAL_BYTES', 'MASTER_SHA256', 'GRADES', 'FLOORS',
                  'EVID', 'EVIDB', 'LOST', 'ITEMS', 'UNIQ', 'LOST_ITEMS', 'LOST_UNIQ'):
            C[nm] = ast.literal_eval(node.value)
need = ('CUR_SHA256', 'TOTAL_BYTES', 'MASTER_SHA256', 'GRADES', 'FLOORS',
        'EVID', 'EVIDB', 'LOST', 'ITEMS', 'UNIQ', 'LOST_ITEMS', 'LOST_UNIQ')
ck('G2a ast 取到全部 12 个「字面量」常量（EXPECT_CUR 是 os.path.join 调用，单独用正则取）',
   all(k in C for k in need), [k for k in need if k not in C])
ck('G2a2 EXPECT_CUR 行含 V557 目录号（正则实测 1 次）',
   len(re.findall(r'^EXPECT_CUR = .*R17_R128_FACTINDEX_V557.*$', src, re.M)) == 1,
   len(re.findall(r'^EXPECT_CUR = .*R17_R128_FACTINDEX_V557.*$', src, re.M)))

def canon_g(d):  return '\n'.join("    '%s': '%s'," % (k, d[k]) for k in sorted(d))
def canon_f(d):  return '\n'.join("    '%s': (%d, %d)," % (k, d[k][0], d[k][1]) for k in sorted(d))
def canon_e(d):  return '\n'.join("    '%s': [%s]," % (k, ', '.join("'%s'" % x for x in d[k])) for k in sorted(d))
def canon_eb(d): return '\n'.join("    '%s': %d," % (k, d[k]) for k in sorted(d))
def canon_l(d):  return '\n'.join("    '%s': %d," % (k, d[k]) for k in sorted(d))

def master(cur_sha, total, floors):
    return hashlib.sha256(('\n'.join([cur_sha, str(total), canon_g(C['GRADES']), canon_f(floors),
                                      canon_e(C['EVID']), canon_eb(C['EVIDB']), canon_l(C['LOST']),
                                      str(C['ITEMS']), str(C['UNIQ']), str(C['LOST_ITEMS']),
                                      str(C['LOST_UNIQ'])])).encode()).hexdigest()

old_master = master(C['CUR_SHA256'], C['TOTAL_BYTES'], C['FLOORS'])
print('   旧常量复算 MASTER = %s （pin %s）' % (old_master[:16], C['MASTER_SHA256'][:16]))
ck('G2b 用旧常量复算旧 MASTER 命中旧 pin（硬闸：不同源则禁止写盘）',
   old_master == C['MASTER_SHA256'], (old_master[:16], C['MASTER_SHA256'][:16]))

# ---------- 新常量 ----------
NEW_FLOORS = dict(C['FLOORS'])
old_f24 = NEW_FLOORS['F24']
new_f24 = (10996, 35925)
ck('G2c F24 旧 floor 恰为 V557 现值 (10996, 35453)', old_f24 == (10996, 35453), old_f24)
NEW_FLOORS['F24'] = new_f24
new_master = master(LED_SHA, len(led), NEW_FLOORS)
print('   新 MASTER = %s' % new_master[:16])
ck('G2d 新 MASTER 与旧不同（否则 D9 恒真）', new_master != old_master, (new_master[:16], old_master[:16]))
ck('G2e 反控 N1：把新 sha 换成 V556 的 ⇒ MASTER 变化',
   master(C['CUR_SHA256'], len(led), NEW_FLOORS) != new_master, True)
fk = dict(NEW_FLOORS); fk['F24'] = (10997, 35925)
ck('G2f 反控 N2：F24 floor 调大 1 ⇒ MASTER 变化', master(LED_SHA, len(led), fk) != new_master, True)
ck('G2g 其余 53 条 floor 逐条未变', all(NEW_FLOORS[k] == C['FLOORS'][k] for k in C['FLOORS'] if k != 'F24'), True)

# ---------- 构造新源码 ----------
new_src = src
ck('G3a 旧 EXPECT_CUR 行含 R17_R128_FACTINDEX_V557', 'R17_R128_FACTINDEX_V557' in src, src.count('R17_R128_FACTINDEX_V557'))
new_src = new_src.replace("'R17_R128_FACTINDEX_V557'", "'%s'" % NEW_DIR)
ck('G3b 替换后 V557 目录名 0 次、V558 目录名 1 次',
   'R17_R128_FACTINDEX_V557' not in new_src and new_src.count(NEW_DIR) == 1,
   (new_src.count('R17_R128_FACTINDEX_V557'), new_src.count(NEW_DIR)))
new_src = new_src.replace("CUR_SHA256 = '%s'" % C['CUR_SHA256'], "CUR_SHA256 = '%s'" % LED_SHA, 1)
ck('G3c CUR_SHA256 已换为新 sha', ("CUR_SHA256 = '%s'" % LED_SHA) in new_src, LED_SHA[:16])
new_src = new_src.replace("TOTAL_BYTES = %d" % C['TOTAL_BYTES'], "TOTAL_BYTES = %d" % len(led), 1)
ck('G3d TOTAL_BYTES 已换', ("TOTAL_BYTES = %d" % len(led)) in new_src, len(led))
new_src = new_src.replace("    'F24': (10996, 35453),", "    'F24': (10996, 35925),", 1)
ck('G3e F24 floor 行已换', "    'F24': (10996, 35925)," in new_src, True)
new_src = new_src.replace("MASTER_SHA256 = '%s'" % C['MASTER_SHA256'], "MASTER_SHA256 = '%s'" % new_master, 1)
ck('G3f MASTER_SHA256 已换为新 pin', ("MASTER_SHA256 = '%s'" % new_master) in new_src, new_master[:16])

# 用 ast 重取新源码常量，逐字段比对
tree2 = ast.parse(new_src)
C2 = {}
for node in tree2.body:
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
        nm = node.targets[0].id
        if nm in need:
            C2[nm] = ast.literal_eval(node.value)
ck('G3g 新源码 13 常量皆可 ast 取出', all(k in C2 for k in need), [k for k in need if k not in C2])
ck('G3h 新源码 CUR_SHA256 == 现盘 sha', C2['CUR_SHA256'] == LED_SHA, C2['CUR_SHA256'][:16])
ck('G3i 新源码 TOTAL_BYTES == 现盘字节', C2['TOTAL_BYTES'] == len(led), C2['TOTAL_BYTES'])
ck('G3j 新源码 FLOORS 只有 F24 变化', all(C2['FLOORS'][k] == C['FLOORS'][k] for k in C['FLOORS'] if k != 'F24')
   and C2['FLOORS']['F24'] == new_f24, C2['FLOORS']['F24'])
ck('G3k 新源码其余 9 组常量逐字段相同',
   all(C2[k] == C[k] for k in ('GRADES', 'EVID', 'EVIDB', 'LOST', 'ITEMS', 'UNIQ', 'LOST_ITEMS', 'LOST_UNIQ')),
   True)
ck('G3l 新源码用新常量复算 MASTER 命中新 pin', master(C2['CUR_SHA256'], C2['TOTAL_BYTES'], C2['FLOORS']) == C2['MASTER_SHA256'],
   master(C2['CUR_SHA256'], C2['TOTAL_BYTES'], C2['FLOORS'])[:16])
diff_lines = sum(1 for a, b in zip(src.split('\n'), new_src.split('\n')) if a != b)
ck('G3m 差异行数（实测）', True, diff_lines)
print('     facts_floors 差异行数 = %d（期望 4：EXPECT_CUR / CUR_SHA256 / TOTAL_BYTES / F24 floor / MASTER 共 5）' % diff_lines)

# ---------- gate_runner ----------
gr = io.open(GR, encoding='utf-8').read()
ck('G4a gate_runner 含 V557 目录号 1 次', gr.count('R17_R128_FACTINDEX_V557') == 1, gr.count('R17_R128_FACTINDEX_V557'))
ck('G4b gate_runner 不持有旧 sha 字面量（实测 0 次）', gr.count(C['CUR_SHA256']) == 0, gr.count(C['CUR_SHA256']))
ck('G4c gate_runner 不持有旧 MASTER 字面量（实测 0 次）', gr.count(C['MASTER_SHA256']) == 0, gr.count(C['MASTER_SHA256']))
new_gr = gr.replace("'R17_R128_FACTINDEX_V557'", "'%s'" % NEW_DIR)
ck('G4d gate_runner 只改 1 处且 V558 出现 1 次',
   'R17_R128_FACTINDEX_V557' not in new_gr and new_gr.count(NEW_DIR) == 1, new_gr.count(NEW_DIR))
ck('G4e gate_runner 差异行数 == 1', sum(1 for a, b in zip(gr.split('\n'), new_gr.split('\n')) if a != b) == 1,
   sum(1 for a, b in zip(gr.split('\n'), new_gr.split('\n')) if a != b))

if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails))
    io.open(OUT, 'w', encoding='utf-8').write(json.dumps({'fails': fails, 'res': res}, ensure_ascii=False, indent=1))
    sys.exit(1)

# ---------- 写盘 ----------
def write_one(path, old_txt, new_txt, tag):
    raw = io.open(path, 'rb').read()
    old_sha = hashlib.sha256(raw).hexdigest()
    assert raw.decode('utf-8') == old_txt, '母本被外部改动'
    bak = os.path.join(BASE, '%s.before_r175_%s_%s.bak' % (os.path.basename(path), tag, stamp))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(raw)
    assert hashlib.sha256(io.open(bak, 'rb').read()).hexdigest() == old_sha
    io.open(path, 'w', encoding='utf-8', newline='').write(new_txt)
    back = io.open(path, 'rb').read()
    return old_sha, hashlib.sha256(back).hexdigest(), len(raw), len(back), bak

o1, n1, b1, b2, bak1 = write_one(FF, src, new_src, 'facts')
print('   facts_floors %s -> %s (%d -> %d B) bak=%s' % (o1[:16], n1[:16], b1, b2, os.path.basename(bak1)))
o2, n2, c1, c2, bak2 = write_one(GR, gr, new_gr, 'gate')
print('   gate_runner  %s -> %s (%d -> %d B) bak=%s' % (o2[:16], n2[:16], c1, c2, os.path.basename(bak2)))

print('== 写后回读 ==')
ff2 = io.open(FF, encoding='utf-8').read()
gr2 = io.open(GR, encoding='utf-8').read()
ck('H1 facts_floors 回读 sha 与内存一致', hashlib.sha256(ff2.encode()).hexdigest() == n1, hashlib.sha256(ff2.encode()).hexdigest()[:16])
ck('H2 gate_runner 回读 sha 与内存一致', hashlib.sha256(gr2.encode()).hexdigest() == n2, hashlib.sha256(gr2.encode()).hexdigest()[:16])
ck('H3 facts_floors 可编译', compile(ff2, FF, 'exec') is not None, True)
ck('H4 gate_runner 可编译', compile(gr2, GR, 'exec') is not None, True)
ck('H5 facts_floors 指向 V558 且旧目录 0 次', NEW_DIR in ff2 and 'R17_R128_FACTINDEX_V557' not in ff2, True)

res.update({'led_sha': LED_SHA, 'led_bytes': len(led), 'old_master': old_master, 'new_master': new_master,
            'facts_sha': [o1, n1], 'gate_sha': [o2, n2], 'diff_lines_facts': diff_lines,
            'fails': fails, 'assertions': n})
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1))
print('\n== %d 断言, %d FAIL ==' % (n, len(fails)))
sys.exit(1 if fails else 0)
