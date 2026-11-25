# -*- coding: utf-8 -*-
"""R129k2：重建撤回存档表（纯 LF，行尾 CR 单独记一列）。

r129k 已把五条假声称从产物里删掉，但它写的存档表混进 1 个 CR（其中一条原行是 CRLF 结尾），
K5 断言当场抓到。本脚本不碰产物、只重建存档表：撤回前原文取自 r129 的 wx 备份（那是权威副本），
故存档内容不依赖已改动过的产物。
"""
import io, os, sys, glob, hashlib

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BK = os.path.join(R14, 'R17_LEAD_BASELINE')
RET = os.path.join(R14, 'R129_RETRACTED.tsv')
DR = os.path.join(R14, 'DISC_RECHECK.tsv')
ck = []
def add(n, ok, d=''):
    ck.append((n, bool(ok), d))

rows = [l.split('\t') for l in io.open(DR, encoding='utf-8').read().split('\n') if l][1:]
byid = {r[0]: r for r in rows if len(r) == 7}
TARGET = ['3', '4', '22', '27', '28']

baks = {}
for p in glob.glob(os.path.join(BK, 'r129_retract_*.bak')):
    # S-190：首版用 split('_')[2]，但文件名是 r129_retract_<key>.<ts>.bak ⇒ [2] 落在 key 里含点的整段。
    key = os.path.basename(p)[len('r129_retract_'):].split('.')[0]
    baks[key] = p
add('L0 恰有 4 份撤回前备份', len(baks) == 4, sorted(baks))

FILEDROP = {}
recs = []
for i in TARGET:
    ap = os.path.join(ROOT, byid[i][4].strip().replace('\\', '/'))
    key = hashlib.sha256(ap.encode()).hexdigest()[:8]
    bp = baks.get(key)
    add('L1 id %s 能按 sha256(绝对路径) 前缀 %s 找到撤回前备份' % (i, key), bp is not None, key)
    if not bp: continue
    old = io.open(bp, 'rb').read()
    txt = old.decode('utf-8')
    hit = [l for l in txt.split('\n') if l.startswith('DISC_RECHECK ') and ('discipline=%s ' % i) in l]
    add('L2 id %s 备份里恰 1 条本纪律自述行' % i, len(hit) == 1, len(hit))
    if len(hit) != 1: continue
    d = hit[0]
    has_cr = d.endswith('\r')
    cur = io.open(ap, 'rb').read()
    add('L3 id %s 当前产物已不含该行（撤回已生效）' % i,
        not any(('discipline=%s ' % i) in l for l in cur.decode('utf-8').split('\n')
                if l.startswith('DISC_RECHECK ')))
    # S-191：首版按「单行」断言字节差，但 id 3 与 4 共用同一产物 ⇒ 一个文件掉了两行。
    # 且删行时连其后的 \n 一并去掉（CRLF 行的 \r 留在行内），故每行掉 len(d)+1 字节。
    # 改为按文件汇总断言（见下方 L4' 段），此处只登记单行长度。
    FILEDROP.setdefault(ap, [old, cur, []])[2].append(len(d.encode('utf-8')) + 1)
    recs.append((i, hashlib.sha256(old).hexdigest(),
                 byid[i][4].strip(), d.rstrip('\r'), 'CRLF' if has_cr else 'LF'))

for ap, (old, cur, drops) in FILEDROP.items():
    add('L4 %s 当前字节数 = 备份字节数 - 各被删行（含行尾换行）之和 %d'
        % (os.path.basename(ap), sum(drops)),
        len(cur) == len(old) - sum(drops),
        {'now': len(cur), 'old': len(old), 'drops': drops})

hdr = '纪律号\t撤回前产物sha256\t产物路径\t撤回的自述行原文\t原行行尾\n'
body = ''.join('%s\t%s\t%s\t%s\t%s\n' % r for r in recs)
with io.open(RET, 'w', encoding='utf-8', newline='\n') as f:
    f.write(hdr + body)
rb = io.open(RET, 'rb').read()
add('L5 存档表纯 LF、6 行（1 表头 + 5 记录）',
    rb.count(b'\r') == 0 and len(rb.decode('utf-8').strip().split('\n')) == 6,
    {'cr': rb.count(b'\r'), 'lines': len(rb.decode('utf-8').strip().split('\n'))})
add('L6 五条原文逐字在表里', all(('\t' + r[3] + '\t') in rb.decode('utf-8') for r in recs) and len(recs) == 5)

bad = [c for c in ck if not c[1]]
for n, ok, d in ck:
    print(('  PASS ' if ok else '  FAIL ') + n + (('  | ' + str(d)) if d != '' else ''))
print('%d/%d PASS' % (len(ck) - len(bad), len(ck)))
sys.exit(1 if bad else 0)
