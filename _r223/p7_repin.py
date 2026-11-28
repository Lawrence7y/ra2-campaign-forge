# -*- coding: utf-8 -*-
"""R223 p7：FACT_INDEX 指针与门禁重钉（V604 -> V605）。先写版本目录（p6 已完成）、后改指针。"""
import hashlib, os, ast, json

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = ROOT + '/lead/next_re_20261117_r14'
BASE = ROOT + '/R17_LEAD_BASELINE'
FF = ROOT + '/_r160/facts_floors.py'
GR = ROOT + '/_r161/gate_runner.py'
PT = TIER + '/FACT_INDEX_CURRENT.md'
NEWD = 'R17_R131_FACTINDEX_V605'
OLDD = 'R17_R131_FACTINDEX_V604'
TSV = TIER + '/' + NEWD + '/FACT_INDEX.tsv'
raw = open(TSV, 'rb').read()
newsha = hashlib.sha256(raw).hexdigest()
fails = []


def ck(n, c, d=''):
    if not c:
        fails.append(n)
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''))


def bak(path, tag):
    b = open(path, 'rb').read()
    base = '%s/%s.before_r223_%s' % (BASE, os.path.basename(path), tag)
    for i in range(10):
        dst = base + (('_%d' % i) if i else '') + '_20261128.bak'
        if os.path.exists(dst):
            if open(dst, 'rb').read() == b:
                return b, dst
            continue
        fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(fd, 'wb') as f:
            f.write(b)
        return b, dst
    raise SystemExit('bak exhausted')


print('新 V604 sha=%s bytes=%d' % (newsha, len(raw)))
ck('P1 V605 CR=0 且字节增长', raw.count(b'\r') == 0 and len(raw) > 303399, len(raw))
ck('P1b sha != V604 22cfe5c4', not newsha.startswith('22cfe5c4'))

src = open(FF, encoding='utf-8').read()
tree = ast.parse(src)
G = {}
for node in tree.body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        nm = node.targets[0].id
        if nm in ('GRADES', 'FLOORS', 'EVID', 'EVIDB', 'LOST', 'ITEMS', 'UNIQ', 'LOST_ITEMS', 'LOST_UNIQ',
                  'CUR_SHA256', 'TOTAL_BYTES', 'MASTER_SHA256'):
            try:
                G[nm] = ast.literal_eval(node.value)
            except Exception as e:
                print('  skip', nm, e)
ck('P2 AST 取到 12 个常量', len(G) == 12, sorted(G))


def canon_g(d):
    return '\n'.join("    '%s': '%s'," % (k, d[k]) for k in sorted(d))


def canon_f(d):
    return '\n'.join("    '%s': (%d, %d)," % (k, d[k][0], d[k][1]) for k in sorted(d))


def canon_e(d):
    return '\n'.join("    '%s': [%s]," % (k, ', '.join("'%s'" % x for x in d[k])) for k in sorted(d))


def canon_l(d):
    return '\n'.join("    '%s': %d," % (k, d[k]) for k in sorted(d))


def master_of(cur, tot):
    return hashlib.sha256(('\n'.join([cur, str(tot), canon_g(G['GRADES']), canon_f(G['FLOORS']),
                                      canon_e(G['EVID']), canon_l(G['EVIDB']), canon_l(G['LOST']), str(G['ITEMS']),
                                      str(G['UNIQ']), str(G['LOST_ITEMS']), str(G['LOST_UNIQ'])])).encode()).hexdigest()


m_new = master_of(newsha, len(raw))
m_old = master_of('22cfe5c48b2138ed058533a4a9eb483d1cc345ea17cff540a1696c1665bb4f02', 303399)
ck('P3 正控 用旧 CUR/TOTAL 复算 == 旧 MASTER', m_old == G['MASTER_SHA256'], (m_old[:16], G['MASTER_SHA256'][:16]))
ck('P4 新 MASTER != 旧 MASTER', m_new != G['MASTER_SHA256'])
if fails:
    print('[ABORT-before-write]', fails)
    raise SystemExit(1)

b, dst = bak(FF, 'FF')
ck('P5 FF 备份已独占创建', os.path.exists(dst), dst)
s = b.decode()
reps = [("EXPECT_CUR = os.path.join(TIER, '%s', 'FACT_INDEX.tsv')" % OLDD,
         "EXPECT_CUR = os.path.join(TIER, '%s', 'FACT_INDEX.tsv')" % NEWD),
        ("CUR_SHA256 = '%s'" % G['CUR_SHA256'], "CUR_SHA256 = '%s'" % newsha),
        ('TOTAL_BYTES = %d' % G['TOTAL_BYTES'], 'TOTAL_BYTES = %d' % len(raw)),
        ("MASTER_SHA256 = '%s'" % G['MASTER_SHA256'], "MASTER_SHA256 = '%s'" % m_new)]
for old, new in reps:
    ck('P6 facts_floors 旧值命中 1 次 : %s…' % old[:44], s.count(old) == 1, s.count(old))
    s = s.replace(old, new)
open(FF, 'wb').write(s.encode())
chk = open(FF, 'rb').read().decode()
assert newsha in chk and ('TOTAL_BYTES = %d' % len(raw)) in chk and NEWD in chk and m_new in chk
print('[FF] EXPECT_CUR / CUR_SHA256 / TOTAL_BYTES / MASTER_SHA256 已重钉')

b, dst = bak(GR, 'GR')
ck('P7 GR 备份已独占创建', os.path.exists(dst), dst)
s = b.decode()
old = "LEDGER = os.path.join(TIER, '%s', 'FACT_INDEX.tsv')" % OLDD
ck('P8 gate_runner 旧 LEDGER 命中 1 次', s.count(old) == 1, s.count(old))
s = s.replace(old, "LEDGER = os.path.join(TIER, '%s', 'FACT_INDEX.tsv')" % NEWD)
open(GR, 'wb').write(s.encode())
print('[GR] LEDGER -> V604')

b, dst = bak(PT, 'PT')
ck('P9 指针文件备份已独占创建', os.path.exists(dst), dst)
s = b.decode()
old_sha = '22cfe5c48b2138ed058533a4a9eb483d1cc345ea17cff540a1696c1665bb4f02'
for old, new in [(OLDD, NEWD), (old_sha, newsha),
                 ('| 字节数 | 303399 |', '| 字节数 | %d |' % len(raw)),
                 ('| 声明轮次 | R222（V604） |', '| 声明轮次 | R223（V605） |')]:
    ck('P10 指针替换 %r' % old[:26], s.count(old) >= 1, s.count(old))
    s = s.replace(old, new)
s = s.replace('| 声明依据 |', '| 声明依据 | **R223 再升 V605**（`0x7c6620` 定性为网格记录 3x3 邻域冲突检查器且无任何外部引用=死代码；`0x7c7371` 状态块只有 12 B / 4 个偏移 obj+0x7d0/d4/d6/da；四张 4 项对齐表与各自 8 项 nibble 表成对同构、跨表同索引 4/4 全等且 4t-8t 恒 0x20；`.data` 320 dword 单调串经三条否证不是指针表），区间改为 **530..605**；', 1)
open(PT, 'wb').write(s.encode())
print('[PT] 指针 -> V604')

json.dump(dict(newsha=newsha, bytes=len(raw), master=m_new, old_master=G['MASTER_SHA256']),
          open(ROOT + '/_r223/p7.json', 'w'), indent=1)
print('[OK] 重钉完成 new_master=%s' % m_new[:16])
