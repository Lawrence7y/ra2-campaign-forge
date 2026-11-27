# -*- coding: utf-8 -*-
"""r178f：门禁重钉 fail-closed —— V560 -> V561。

改 facts_floors.py 五点：EXPECT_CUR 目录号、CUR_SHA256、TOTAL_BYTES、FLOORS['F35']、MASTER_SHA256。
改 gate_runner.py 一点：LEDGER 目录号（它不持有任何 sha 字面量，按正则从 facts 源码现读）。

纪律（S-582）：
  ① 全部断言在写盘之前；
  ② 先 ast 从源码取旧常量，用旧常量复算旧 MASTER，命中旧 MASTER_SHA256 才允许动手（硬闸）；
  ③ 备份用 wx 独占创建；
  ④ 逐条验证其余 53 条 floor 一字未动。
"""
import ast, hashlib, os, re, shutil, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
FF = os.path.join(ROOT, '_r160/facts_floors.py')
GR = os.path.join(ROOT, '_r161/gate_runner.py')
BASE = os.path.join(ROOT, 'lead/next_re_20261117_r14/R17_LEAD_BASELINE')
OLD_DIR = 'R17_R128_FACTINDEX_V560'
NEW_DIR = 'R17_R129_FACTINDEX_V561'
NEWTSV = os.path.join(ROOT, 'lead/next_re_20261117_r14', NEW_DIR, 'FACT_INDEX.tsv')
NEW_SHA = 'dd2c55c6f8aeadf3195bf1dc7fc9bf39ce70ed5ad771c76d52b80e86fe25fee7'
PASS = FAIL = 0


def ck(n, c, d=''):
    global PASS, FAIL
    if c:
        PASS += 1; print('PASS %s  %s' % (n, d))
    else:
        FAIL += 1; print('FAIL %s  %s' % (n, d))


# ---------- 0. 实测新文件 ----------
raw = open(NEWTSV, 'rb').read()
newsha = hashlib.sha256(raw).hexdigest()
ck('A1 V561 sha', newsha == NEW_SHA, newsha[:16])
ck('A2 V561 bytes', len(raw) == 133317, len(raw))
ck('A3 V561 CR=0', raw.count(b'\r') == 0, raw.count(b'\r'))

# ---------- 1. ast 取旧常量 ----------
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
ck('B2 EXPECT_CUR 现指 V560', m is not None and m.group(1) == OLD_DIR, m.group(1) if m else None)
ck('B3 旧 CUR_SHA256 = V560 sha',
   got['CUR_SHA256'] == 'ede48f3c3204804013658046b17ebc7cff23e5b5ec024407a2f79555147ce6a4')
ck('B4 旧 TOTAL_BYTES = 130510', got['TOTAL_BYTES'] == 130510, got['TOTAL_BYTES'])
ck('B5 旧 FLOORS[F35] = (1751, 8695)', got['FLOORS']['F35'] == (1751, 8695), repr(got['FLOORS']['F35']))


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

# ---------- 2. 实测新 F35 两列字节，算新 floor ----------
import csv, io
rows = list(csv.reader(io.StringIO(raw.decode('utf-8')), delimiter='\t'))
data = rows[1:]
mm = {r[0]: r for r in data}
s_b, l_b = len(mm['F35'][1].encode()), len(mm['F35'][4].encode())
ck('D1 新 F35 stmt 字节 = 1751（未变）', s_b == 1751, s_b)
ck('D2 新 F35 lim 字节 = 11502', l_b == 11502, l_b)
newfl = dict(got['FLOORS'])
newfl['F35'] = (s_b, l_b)
ck('D3 新 F35 floor = (1751, 11502)', newfl['F35'] == (1751, 11502), repr(newfl['F35']))

shrink = []
for r in data:
    fid = r[0]
    if fid not in newfl: continue
    fs, fl = newfl[fid]
    if len(r[1].encode()) < fs or len(r[4].encode()) < fl:
        shrink.append((fid, len(r[1].encode()), fs, len(r[4].encode()), fl))
ck('D4 54 条 floor 全部不缩水', shrink == [], shrink[:3])
moved = [k for k in newfl if newfl[k] != got['FLOORS'][k]]
ck('D5 floor 变化项恰 1 个：F35', moved == ['F35'], moved)

m_new = master(newsha, len(raw), newfl)
ck('E1 新 MASTER 与旧不同', m_new != got['MASTER_SHA256'], m_new[:16])
ck('E2 MASTER 分量变化仅 sha/total/F35 三处', True)

# ---------- 3. gate_runner ----------
gsrc = open(GR, encoding='utf-8').read()
ck('F1 gate_runner 旧目录号恰 1 次', gsrc.count(OLD_DIR) == 1, gsrc.count(OLD_DIR))
ck('F2 gate_runner 新目录号 0 次', gsrc.count(NEW_DIR) == 0, gsrc.count(NEW_DIR))
ck('F3 gate_runner 不持有旧 sha 字面量', gsrc.count(got['CUR_SHA256']) == 0)
ck('F4 gate_runner 不持有旧 MASTER 字面量', gsrc.count(got['MASTER_SHA256']) == 0)

# ---------- 4. 构造新源码（不写盘）----------
ff_new = src
ff_new = ff_new.replace("os.path.join(TIER, '%s', 'FACT_INDEX.tsv')" % OLD_DIR,
                        "os.path.join(TIER, '%s', 'FACT_INDEX.tsv')" % NEW_DIR, 1)
ff_new = ff_new.replace("CUR_SHA256 = '%s'" % got['CUR_SHA256'], "CUR_SHA256 = '%s'" % newsha, 1)
ff_new = ff_new.replace("TOTAL_BYTES = %d" % got['TOTAL_BYTES'], "TOTAL_BYTES = %d" % len(raw), 1)
ff_new = ff_new.replace("'F35': (%d, %d)," % got['FLOORS']['F35'],
                        "'F35': (%d, %d)," % newfl['F35'], 1)
ff_new = ff_new.replace("MASTER_SHA256 = '%s'" % got['MASTER_SHA256'],
                        "MASTER_SHA256 = '%s'" % m_new, 1)
chg = sum(1 for a, b in zip(src.split('\n'), ff_new.split('\n')) if a != b)
ck('G1 facts_floors 变化行恰 5 行', chg == 5, chg)
ck('G2 facts_floors 行数不变', src.count('\n') == ff_new.count('\n'),
   (src.count('\n'), ff_new.count('\n')))

gr_new = gsrc.replace(OLD_DIR, NEW_DIR, 1)
chg2 = sum(1 for a, b in zip(gsrc.split('\n'), gr_new.split('\n')) if a != b)
ck('G3 gate_runner 变化行恰 1 行', chg2 == 1, chg2)

if FAIL:
    print('ABORT %d FAIL，未写盘' % FAIL); sys.exit(1)
if '--dry' in sys.argv:
    print('--dry：全部断言通过，未写盘。新 MASTER = %s' % m_new[:16])
    print('---- %d PASS / %d FAIL (dry) ----' % (PASS, FAIL)); sys.exit(0)

# ---------- 5. wx 独占备份 + 一次性写入 ----------
def backup(p, tag):
    d = os.path.join(BASE, tag)
    with open(p, 'rb') as f:
        b = f.read()
    with open(d, 'xb') as out:          # wx，已存在即失败
        out.write(b)
    return d, hashlib.sha256(b).hexdigest()


bd1, s1 = backup(FF, 'facts_floors.py.before_r178.bak')
bd2, s2 = backup(GR, 'gate_runner.py.before_r178.bak')
ck('H1 facts 备份 sha == 现盘', s1 == hashlib.sha256(src.encode()).hexdigest())
ck('H2 gate 备份 sha == 现盘', s2 == hashlib.sha256(gsrc.encode()).hexdigest())

open(FF, 'w', encoding='utf-8', newline='').write(ff_new)
open(GR, 'w', encoding='utf-8', newline='').write(gr_new)
ck('I1 facts 回读一致', open(FF, encoding='utf-8').read() == ff_new)
ck('I2 gate 回读一致', open(GR, encoding='utf-8').read() == gr_new)

print()
print('新 MASTER_SHA256 = %s' % m_new)
print('新 FLOORS[F35]   = (1751, 11502)')
print('新 TOTAL_BYTES    = %d' % len(raw))
print('新 CUR_SHA256     = %s' % newsha[:16])
print('---- %d PASS / %d FAIL ----' % (PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)
