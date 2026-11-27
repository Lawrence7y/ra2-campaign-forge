# -*- coding: utf-8 -*-
"""R177 门禁重钉：facts_floors（EXPECT_CUR / CUR_SHA256 / TOTAL_BYTES / FLOORS['F29'] / MASTER_SHA256）
与 gate_runner（LEDGER 目录号）。纪律：断言全在写盘之前；先 ast 取旧常量复算旧 MASTER 命中原值作硬闸。"""
import ast, hashlib, os, re, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
FF = os.path.join(ROOT, '_r160/facts_floors.py')
GR = os.path.join(ROOT, '_r161/gate_runner.py')
NEWDIR = 'R17_R128_FACTINDEX_V560'
OLD_DIR_EXPECT = 'R17_R128_FACTINDEX_V559'
NEWTSV = os.path.join(ROOT, 'lead/next_re_20261117_r14', NEWDIR, 'FACT_INDEX.tsv')
BASE = os.path.join(ROOT, 'lead/next_re_20261117_r14/R17_LEAD_BASELINE')
P = F = 0
def ck(n, c, d=''):
    global P, F
    if c: P += 1; print('PASS', n, d)
    else: F += 1; print('FAIL', n, d)

raw = open(NEWTSV, 'rb').read()
newsha = hashlib.sha256(raw).hexdigest()
ck('A1 new sha', newsha == 'ede48f3c3204804013658046b17ebc7cff23e5b5ec024407a2f79555147ce6a4', newsha[:16])
ck('A2 new bytes', len(raw) == 130510, '%d' % len(raw))

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
ck('B1 all 12 ast-literal constants', set(got) == want, repr(sorted(want - set(got))))
_m = re.search(r"EXPECT_CUR = os\.path\.join\(TIER, '([^']+)', 'FACT_INDEX\.tsv'\)", src)
ck('B2 EXPECT_CUR literal parsed', _m is not None and _m.group(1) == OLD_DIR_EXPECT,
   _m.group(1) if _m else 'None')

def master(sha, total, floors):
    return hashlib.sha256(('\n'.join([sha, str(total), ns['canon_g'](got['GRADES']), ns['canon_f'](floors),
                                      ns['canon_e'](got['EVID']), ns['canon_eb'](got['EVIDB']),
                                      ns['canon_l'](got['LOST']), str(got['ITEMS']), str(got['UNIQ']),
                                      str(got['LOST_ITEMS']), str(got['LOST_UNIQ'])])).encode()).hexdigest()

oldm = master(got['CUR_SHA256'], got['TOTAL_BYTES'], got['FLOORS'])
ck('C1 HARD GATE old constants reproduce old MASTER', oldm == got['MASTER_SHA256'], oldm[:16])
ck('C2 old sha is V559', got['CUR_SHA256'] == 'e4642d554d8ba9f1dab25b6a2b456e365252051035f9104003b58ff622d489e9')
ck('C3 old total 129405', got['TOTAL_BYTES'] == 129405)
ck('C4 old F29 floor (3435,14222)', got['FLOORS']['F29'] == (3435, 14222), repr(got['FLOORS']['F29']))
ck('C5 only F29 floor changes in plan', True)
newfl = dict(got['FLOORS']); newfl['F29'] = (3435, 15259)
ck('C6 new F29 floor matches measured', newfl['F29'] == (3435, 15259))

# 逐 fid 实测：D6 是「不许缩」⇒ 新的实测值必须 >= 新 floor，且其余 53 fid 实测未变
import csv, io
rows = list(csv.reader(io.StringIO(raw.decode('utf-8')), delimiter='\t'))
data = rows[1:]
shrink = []
for r in data:
    fid = r[0]
    if fid not in newfl: continue
    fs, fl = newfl[fid]
    s, l = len(r[1].encode()), len(r[4].encode())
    if s < fs or l < fl: shrink.append((fid, s, fs, l, fl))
ck('C7 no fact below new floors', shrink == [], repr(shrink[:3]))
changed = [r[0] for r in data if (len(r[1].encode()), len(r[4].encode())) != (got['FLOORS'][r[0]] if r[0] in got['FLOORS'] else (len(r[1].encode()), len(r[4].encode())))]
print('  facts whose bytes differ from old floor:', changed)

gsrc = open(GR, encoding='utf-8').read()
ck('D1 gate_runner holds old dir once', gsrc.count(OLD_DIR_EXPECT) == 1, '%d' % gsrc.count(OLD_DIR_EXPECT))
ck('D2 gate_runner holds new dir zero times', gsrc.count(NEWDIR) == 0, '%d' % gsrc.count(NEWDIR))
ck('D3 gate_runner does NOT hold old sha literal', gsrc.count(got['CUR_SHA256']) == 0)
ck('D4 gate_runner does NOT hold old MASTER literal', gsrc.count(got['MASTER_SHA256']) == 0)

m_new = master(newsha, len(raw), newfl)
ck('E1 new master differs from old', m_new != got['MASTER_SHA256'], m_new[:16])
ck('E2-neg sha changes master', master(got['CUR_SHA256'], len(raw), newfl) != m_new)
ck('E3-neg total changes master', master(newsha, len(raw) + 1, newfl) != m_new)
for i in (0, 1):
    f2 = dict(newfl); f2['F29'] = tuple(newfl['F29'][j] + (1 if j == i else 0) for j in range(2))
    ck('E4-neg F29[%d] changes master' % i, master(newsha, len(raw), f2) != m_new)

if F:
    print('ABORT before write: %d FAIL' % F); sys.exit(1)

ts = time.strftime('%Y%m%d_%H%M%S')
def backup(p, tag):
    bp = os.path.join(BASE, os.path.basename(p) + '.before_r177%s_%s.bak' % (tag, ts))
    with open(bp, 'xb') as f:
        f.write(open(p, 'rb').read())
    return bp

bf = backup(FF, 'ff'); bg = backup(GR, 'gr')
ck('F1 facts backup identical', open(bf, 'rb').read() == src.encode())
ck('F2 gate backup identical', open(bg, 'rb').read() == gsrc.encode())

newsrc = src.replace(oldm and '', '')  # no-op guard
newsrc = src
newsrc = newsrc.replace("EXPECT_CUR = os.path.join(TIER, '%s', 'FACT_INDEX.tsv')" % OLD_DIR_EXPECT,
                        "EXPECT_CUR = os.path.join(TIER, '%s', 'FACT_INDEX.tsv')" % NEWDIR)
newsrc = newsrc.replace("CUR_SHA256 = '%s'" % got['CUR_SHA256'], "CUR_SHA256 = '%s'" % newsha)
newsrc = newsrc.replace("TOTAL_BYTES = %d" % got['TOTAL_BYTES'], "TOTAL_BYTES = %d" % len(raw))
newsrc = newsrc.replace("MASTER_SHA256 = '%s'" % got['MASTER_SHA256'], "MASTER_SHA256 = '%s'" % m_new)
newsrc = newsrc.replace("    'F29': (3435, 14222),", "    'F29': (3435, 15259),")
newgr = gsrc.replace(OLD_DIR_EXPECT, NEWDIR)

# 只改这些，别的行一字不动
def diff_lines(a, b):
    la, lb = a.split('\n'), b.split('\n')
    return [(i + 1, la[i] if i < len(la) else '', lb[i] if i < len(lb) else '')
            for i in range(max(len(la), len(lb))) if (i >= len(la) or i >= len(lb) or la[i] != lb[i])]
dl = diff_lines(src, newsrc); dlg = diff_lines(gsrc, newgr)
print('  facts_floors changed lines: %d' % len(dl))
for ln, o, n in dl: print('    L%-4d %s' % (ln, n.strip()[:110]))
print('  gate_runner changed lines: %d' % len(dlg))
for ln, o, n in dlg: print('    L%-4d %s' % (ln, n.strip()[:110]))
ck('G1 facts changed lines == 5', len(dl) == 5, len(dl))
ck('G2 gate_runner changed lines == 1', len(dlg) == 1, len(dlg))
ck('G3 new src holds new sha', newsrc.count(newsha) == 1)
ck('G4 new src holds new dir once', newsrc.count(NEWDIR) == 1)
ck('G5 new src has no old dir', newsrc.count(OLD_DIR_EXPECT) == 0)
ck('G6 new gr has new dir once', newgr.count(NEWDIR) == 1)

with open(FF, 'wb') as f:
    f.write(newsrc.encode('utf-8'))
with open(GR, 'wb') as f:
    f.write(newgr.encode('utf-8'))
ck('H1 facts readback sha', hashlib.sha256(open(FF, 'rb').read()).hexdigest() == hashlib.sha256(newsrc.encode()).hexdigest())
ck('H2 gate readback', open(GR, 'rb').read() == newgr.encode('utf-8'))
print('---- %d PASS / %d FAIL ----' % (P, F))
sys.exit(1 if F else 0)
