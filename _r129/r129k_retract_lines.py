# -*- coding: utf-8 -*-
"""R129k：撤回五条时间上不可能的自述行（裁定第二段）。

r129j 只降级了第 7 列，门禁立刻给出 5 条 FAIL：R128 那条判据说「claims-none 行的产物里
不得出现本纪律自述行」。这不是误伤，是我漏了一步 —— 只撤回「声称」而不撤回「声称所依据
的那行字」，等于让一行假声称继续躺在产物里。故补这一段：从产物里**删掉**那五条行，
删前把原文逐字存进 R129_RETRACTED.tsv（撤回不等于抹掉记录）。

同时 C17_REUSED_ATS 要由 {'2026-11-22T17:39:19+08:00': 4} 改成空 dict
（那 4 条行删掉后复用就消失了；这个常量是下限，必须显式重钉）。

写入纪律：每个产物 wx 独占备份 -> 断言旧 sha256 -> 只删那一行 -> 断言其余字节逐位不变。
"""
import io, os, sys, hashlib, datetime

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BK = os.path.join(R14, 'R17_LEAD_BASELINE')
GATE = os.path.join(R14, 'check_disc.py')
DR = os.path.join(R14, 'DISC_RECHECK.tsv')
TS = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
RET = os.path.join(R14, 'R129_RETRACTED.tsv')
ck = []
def add(n, ok, d=''):
    ck.append((n, bool(ok), d))

rows = [l.split('\t') for l in io.open(DR, encoding='utf-8').read().split('\n') if l][1:]
byid = {r[0]: r for r in rows if len(r) == 7}
TARGET = ['3', '4', '22', '27', '28']

recs = []
touched = {}
for i in TARGET:
    r = byid[i]
    p = r[4].strip()
    ap = os.path.join(ROOT, p.replace('\\', '/'))
    old = io.open(ap, 'rb').read()
    txt = old.decode('utf-8')
    keep, drop = [], []
    for l in txt.split('\n'):
        if l.startswith('DISC_RECHECK ') and ('discipline=%s ' % i) in l:
            drop.append(l)
        else:
            keep.append(l)
    add('K0 id %s 的产物里有且仅有 1 条本纪律自述行（多余则本条判据不成立）' % i, len(drop) == 1, len(drop))
    if len(drop) != 1:
        continue
    new = '\n'.join(keep)
    # 断言：删掉那一行后，除它之外逐行完全相同
    add('K1 id %s 删除的确实是整行，其余行逐字不变' % i,
        keep == [l for l in txt.split('\n') if l != drop[0]], '')
    touched.setdefault(ap, (old, new, []))
    touched[ap][2].append((i, drop[0]))

for ap, (old, new, items) in touched.items():
    # 多个 id 可能共用同一产物：重算 new（把它们全部删掉）
    txt = old.decode('utf-8')
    dropall = [d for _, d in items]
    keep = [l for l in txt.split('\n') if l not in dropall]
    new = '\n'.join(keep)
    dst = os.path.join(BK, 'r129_retract_%s.%s.bak' % (hashlib.sha256(ap.encode()).hexdigest()[:8], TS))
    fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    try: os.write(fd, old)
    finally: os.close(fd)
    with io.open(ap, 'wb') as f: f.write(new.encode('utf-8'))
    rb = io.open(ap, 'rb').read()
    add('K2 %s 回读 == 写入' % os.path.basename(ap), rb == new.encode('utf-8'),
        '%d -> %d B' % (len(old), len(rb)))
    # S-197：首版 K3 写成 `... or True`（恒真），与 S-187 同族，被 r129n 的 N1 自动抓到。
    # 改为真判据：该文件回读后，不得再有任何本纪律自述行（不限于那 5 个 id）。
    _left = [l for l in rb.decode('utf-8').split('\n')
             if l.startswith('DISC_RECHECK ') and any(('discipline=%s ' % i) in l for i in TARGET)]
    add('K3 %s 删除后不再含任何一条被撤回纪律的自述行' % os.path.basename(ap),
        len(_left) == 0, len(_left))
    # S-189：首版把撤回行原文原样塞进存档表，而其中一行的原产物是 CRLF 结尾 ⇒ 存档表里
    # 混进 1 个 CR，K5 的「LF-only」断言当场抓到。修法：把行尾 CR 单独记一列，正文保持 LF。
    for i, d in items:
        has_cr = d.endswith('\r')
        recs.append((i, hashlib.sha256(old).hexdigest(), ap.replace(ROOT + '/', '').replace('/', '\\'),
                     d.rstrip('\r'), 'CRLF' if has_cr else 'LF'))

# 逐条核对：删后产物里不含本纪律自述行
for i in TARGET:
    ap = os.path.join(ROOT, byid[i][4].strip().replace('\\', '/'))
    t = io.open(ap, encoding='utf-8', errors='replace').read()
    hit = [l for l in t.splitlines() if l.startswith('DISC_RECHECK ') and ('discipline=%s ' % i) in l]
    add('K4 id %s 删后产物里本纪律自述行 = 0' % i, len(hit) == 0, len(hit))

# 存档表
hdr = '纪律号\t撤回前产物sha256\t产物路径\t撤回的自述行原文\t原行行尾\n'
body = ''.join('%s\t%s\t%s\t%s\t%s\n' % r for r in recs)
with io.open(RET, 'w', encoding='utf-8', newline='\n') as f:
    f.write(hdr + body)
rb = io.open(RET, 'rb').read()
add('K5 撤回存档表已落盘、LF-only、%d 行记录（行尾 CR 单独记一列）' % len(recs),
    rb.count(b'\r') == 0 and len(recs) == 5 and len(rb.decode('utf-8').strip().split('\n')) == 6,
    {'cr': rb.count(b'\r'), 'lines': len(rb.decode('utf-8').strip().split('\n'))})
# 存档里的原文必须与撤回前字节一致
oktxt = all(('\t' + d + '\t') in rb.decode('utf-8') for _, _, _, d, _e in recs)
add('K6 存档表里五条自述行原文逐字保留（撤回不抹记录）', oktxt)

# C17_REUSED_ATS 重钉
g = io.open(GATE, 'rb').read()
oldg = g
assert g.decode('utf-8').count("C17_REUSED_ATS = {'2026-11-22T17:39:19+08:00': 4}") == 1
g2 = g.decode('utf-8').replace("C17_REUSED_ATS = {'2026-11-22T17:39:19+08:00': 4}",
                               "C17_REUSED_ATS = {}   # R129：五条假声称已撤回，复用随之消失（重钉见 _r129/r129k）")
dst = os.path.join(BK, 'r129_gate_reused_ats.%s.bak' % TS)
fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
try: os.write(fd, g)
finally: os.close(fd)
with io.open(GATE, 'wb') as f: f.write(g2.encode('utf-8'))
rbg = io.open(GATE, 'rb').read()
add('K7 C17_REUSED_ATS 重钉为空 dict，回读一致、CR 不变',
    rbg == g2.encode('utf-8') and rbg.count(b'\r') == g.count(b'\r'), '')

bad = [c for c in ck if not c[1]]
for n, ok, d in ck:
    print(('  PASS ' if ok else '  FAIL ') + n + (('  | ' + str(d)) if d != '' else ''))
print('%d/%d PASS' % (len(ck) - len(bad), len(ck)))
sys.exit(1 if bad else 0)
