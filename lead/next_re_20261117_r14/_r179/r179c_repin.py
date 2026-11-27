# -*- coding: utf-8 -*-
"""r179c：门禁重钉 fail-closed —— V561 -> V562（百分号双写订正，全文 −5 B）。

改 facts_floors.py 五点：EXPECT_CUR 目录号、CUR_SHA256、TOTAL_BYTES、FLOORS['F24']、FLOORS['F29']
（另加 MASTER_SHA256）。改 gate_runner.py 一点：LEDGER 目录号。

纪律（S-582）：
  ① 全部断言在写盘之前；
  ② 先 ast 取旧常量，用旧常量复算旧 MASTER，命中旧 MASTER_SHA256 才允许动手（硬闸）；
  ③ 逐条验证其余 52 条 floor 一字未动；
  ④ 反向验证：显式传 V561 必须 D0/D6/D8 三红。
"""
import ast, csv, hashlib, io, os, re, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
FF = os.path.join(ROOT, '_r160/facts_floors.py')
GR = os.path.join(ROOT, '_r161/gate_runner.py')
OLD_DIR = 'R17_R129_FACTINDEX_V561'
NEW_DIR = 'R17_R130_FACTINDEX_V562'
NEWTSV = os.path.join(ROOT, 'lead/next_re_20261117_r14', NEW_DIR, 'FACT_INDEX.tsv')
NEW_SHA = 'PLACEHOLDER'
PASS = FAIL = 0


def ck(n, c, d=''):
    global PASS, FAIL
    if c:
        PASS += 1; print('PASS %s  %s' % (n, d))
    else:
        FAIL += 1; print('FAIL %s  %s' % (n, d))


raw = open(NEWTSV, 'rb').read()
newsha = hashlib.sha256(raw).hexdigest()
ck('A1 V562 bytes = 133312', len(raw) == 133312, len(raw))
ck('A2 V562 CR=0', raw.count(b'\r') == 0, raw.count(b'\r'))
ck('A3 V562 双写 0 处', raw.count(b'%%') == 0, raw.count(b'%%'))

src = open(FF, encoding='utf-8').read()
tree = ast.parse(src)
ns = {}
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name.startswith('canon_'):
        exec(compile(ast.Module(body=[node], type_ignores=[]), FF, 'exec'), ns)
want = {'GRADES', 'FLOORS', 'EVID', 'EVIDB', 'LOST', 'ITEMS', 'UNIQ', 'LOST_ITEMS', 'LOST_UNIQ',
        'MASTER_SHA256', 'CUR_SHA256', 'TOTAL_BYTES'}
got = {}
for node in tree.body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        n = node.targets[0].id
        if n in want:
            got[n] = ast.literal_eval(node.value)
ck('B1 ast 取到全部 12 个常量', set(got) == want, repr(sorted(want - set(got))))
m = re.search(r"EXPECT_CUR = os\.path\.join\(TIER, '([^']+)', 'FACT_INDEX\.tsv'\)", src)
ck('B2 EXPECT_CUR 现指 V561', m is not None and m.group(1) == OLD_DIR, m.group(1) if m else None)
ck('B3 旧 CUR_SHA256 = V561 sha',
   got['CUR_SHA256'] == 'dd2c55c6f8aeadf3195bf1dc7fc9bf39ce70ed5ad771c76d52b80e86fe25fee7')
ck('B4 旧 TOTAL_BYTES = 133317', got['TOTAL_BYTES'] == 133317, got['TOTAL_BYTES'])
ck('B5 旧 FLOORS[F24] = (11349, 36142)', got['FLOORS']['F24'] == (11349, 36142), repr(got['FLOORS']['F24']))
ck('B6 旧 FLOORS[F29] = (3435, 15259)', got['FLOORS']['F29'] == (3435, 15259), repr(got['FLOORS']['F29']))


def master(sha, total, floors):
    return hashlib.sha256(('\n'.join([
        sha, str(total), ns['canon_g'](got['GRADES']), ns['canon_f'](floors),
        ns['canon_e'](got['EVID']), ns['canon_eb'](got['EVIDB']),
        ns['canon_l'](got['LOST']), str(got['ITEMS']), str(got['UNIQ']),
        str(got['LOST_ITEMS']), str(got['LOST_UNIQ'])])).encode()).hexdigest()


oldm = master(got['CUR_SHA256'], got['TOTAL_BYTES'], got['FLOORS'])
ck('C1 硬闸：旧常量复算旧 MASTER 命中', oldm == got['MASTER_SHA256'], oldm[:16])
if oldm != got['MASTER_SHA256']:
    print('ABORT 硬闸未命中，拒绝写盘'); sys.exit(1)

rows = list(csv.reader(io.StringIO(raw.decode('utf-8')), delimiter='\t'))
data = rows[1:]
mm = {r[0]: r for r in data}
ck('D1 F24.F29 statement 字节未变',
   (len(mm['F24'][1].encode()), len(mm['F29'][1].encode())) == (11349, 3435),
   (len(mm['F24'][1].encode()), len(mm['F29'][1].encode())))
ck('D2 F24.lim = 36140 / F29.lim = 15256',
   (len(mm['F24'][4].encode()), len(mm['F29'][4].encode())) == (36140, 15256),
   (len(mm['F24'][4].encode()), len(mm['F29'][4].encode())))

newfl = dict(got['FLOORS'])
newfl['F24'] = (len(mm['F24'][1].encode()), len(mm['F24'][4].encode()))
newfl['F29'] = (len(mm['F29'][1].encode()), len(mm['F29'][4].encode()))
moved = [k for k in newfl if newfl[k] != got['FLOORS'][k]]
ck('D3 floor 变化项恰 (F24, F29)', sorted(moved) == ['F24', 'F29'], moved)

shrink = []
for r in data:
    fid = r[0]
    if fid not in newfl: continue
    fs, fl = newfl[fid]
    if len(r[1].encode()) < fs or len(r[4].encode()) < fl:
        shrink.append(fid)
ck('D4 用新表复算 54 条 floor 全不缩水', shrink == [], shrink[:5])

m_new = master(newsha, len(raw), newfl)
ck('E1 新 MASTER 与旧不同', m_new != got['MASTER_SHA256'], m_new[:16])

gsrc = open(GR, encoding='utf-8').read()
ck('F1 gate_runner 旧目录号恰 1 次', gsrc.count(OLD_DIR) == 1, gsrc.count(OLD_DIR))
ck('F2 gate_runner 新目录号 0 次', gsrc.count(NEW_DIR) == 0, gsrc.count(NEW_DIR))
ck('F3 gate_runner 不持有旧 sha 字面量', gsrc.count(got['CUR_SHA256']) == 0)
ck('F4 gate_runner 不持有旧 MASTER 字面量', gsrc.count(got['MASTER_SHA256']) == 0)

ff_new = src
ff_new = ff_new.replace("os.path.join(TIER, '%s', 'FACT_INDEX.tsv')" % OLD_DIR,
                        "os.path.join(TIER, '%s', 'FACT_INDEX.tsv')" % NEW_DIR, 1)
ff_new = ff_new.replace("CUR_SHA256 = '%s'" % got['CUR_SHA256'], "CUR_SHA256 = '%s'" % newsha, 1)
ff_new = ff_new.replace("TOTAL_BYTES = %d" % got['TOTAL_BYTES'], "TOTAL_BYTES = %d" % len(raw), 1)
ff_new = ff_new.replace("    'F24': (%d, %d)," % got['FLOORS']['F24'],
                        "    'F24': (%d, %d)," % newfl['F24'], 1)
ff_new = ff_new.replace("    'F29': (%d, %d)," % got['FLOORS']['F29'],
                        "    'F29': (%d, %d)," % newfl['F29'], 1)
ff_new = ff_new.replace("MASTER_SHA256 = '%s'" % got['MASTER_SHA256'],
                        "MASTER_SHA256 = '%s'" % m_new, 1)
# 只改这几处：逐行 diff 必须恰 5 行
a, b = src.split('\n'), ff_new.split('\n')
ck('G1 facts 源行数不变', len(a) == len(b), (len(a), len(b)))
diff = [i for i in range(len(a)) if a[i] != b[i]]
# S-658 订正：旧稿写「恰 5 行」，是按 R178「只改一列 floor」的惯例想当然；
# 本轮 floor 变两条（F24 + F29），差异行实为 6 行。判据改为「等于列出的六个常量行」。
_want6 = ["EXPECT_CUR = os.path.join(", "CUR_SHA256 = '", "TOTAL_BYTES = ",
          "    'F24': (", "    'F29': (", "MASTER_SHA256 = '"]
ck('G2 facts 差异行恰 6 行且逐行属于五个重钉点 + MASTER',
   len(diff) == 6 and all(any(a[i].startswith(w) or a[i].startswith(w.lstrip()) for w in _want6) for i in diff),
   [a[i][:34] for i in diff])
gr_new = gsrc.replace(OLD_DIR, NEW_DIR)
ga, gb = gsrc.split('\n'), gr_new.split('\n')
gdiff = [i for i in range(len(ga)) if ga[i] != gb[i]]
ck('G3 gate_runner 差异行恰 1 行', len(gdiff) == 1, [ga[i][:60] for i in gdiff])
ck('G4 反向：新 MASTER 不等于旧、新 sha 不等于旧', m_new != got['MASTER_SHA256'] and newsha != got['CUR_SHA256'])

if FAIL:
    print('ABORT %d FAIL，未写盘' % FAIL); sys.exit(1)

import shutil
BASE = os.path.join(ROOT, 'lead/next_re_20261117_r14/R17_LEAD_BASELINE')
for p in (FF, GR):
    bp = os.path.join(BASE, 'R179_%s.before_r179.bak' % os.path.basename(p))
    if not os.path.exists(bp):
        fd = os.open(bp, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
        with os.fdopen(fd, 'wb') as f:
            f.write(open(p, 'rb').read())
    ck('H %s 备份可复算' % os.path.basename(p),
       hashlib.sha256(open(bp, 'rb').read()).hexdigest() == hashlib.sha256(open(p, 'rb').read()).hexdigest())

if '--dry' in sys.argv:
    print('--dry：全通过，未写盘。新 MASTER = %s' % m_new)
    print('---- %d PASS / %d FAIL (dry) ----' % (PASS, FAIL)); sys.exit(0)

open(FF, 'w', encoding='utf-8', newline='').write(ff_new)
open(GR, 'w', encoding='utf-8', newline='').write(gr_new)
ck('I1 facts 回读 == 构造内容', open(FF, encoding='utf-8', newline='').read() == ff_new)
ck('I2 gate_runner 回读 == 构造内容', open(GR, encoding='utf-8', newline='').read() == gr_new)
print('新 MASTER = %s' % m_new)
print('---- %d PASS / %d FAIL ----' % (PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)
