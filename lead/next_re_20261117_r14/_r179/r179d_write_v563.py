# -*- coding: utf-8 -*-
"""r179d：V562 -> V563，把 F35 limitations 里那条路径的**双反斜杠**改成单反斜杠。

同族判据：与 r179b 修的 5 处双百分号是同一类缺陷 —— 写盘源码按「转义串」的习惯写
（r139g 用 u'...\\\\work\\\\...'），而落盘路径不做反转义，于是两字节原样落盘。
本文件内同一路径在 evidence 列（第 4 列）是单反斜杠、在 limitations 列（第 5 列）是双 ⇒
两处形态不一致，双写形态不可解析。修后与 evidence 列同形。
"""
import csv, hashlib, io, os, shutil, sys

TIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(TIER, 'R17_LEAD_BASELINE')
SRC = os.path.join(TIER, 'R17_R130_FACTINDEX_V562', 'FACT_INDEX.tsv')
DST_DIR = os.path.join(TIER, 'R17_R131_FACTINDEX_V563')
DST = os.path.join(DST_DIR, 'FACT_INDEX.tsv')
SHA562 = 'c51b6de3d6ee70ddd830db40b44581316adacb9845d15528d233d812b67b0de8'
PASS = FAIL = 0


def ck(n, c, d=''):
    global PASS, FAIL
    if c:
        PASS += 1; print('PASS %s  %s' % (n, d))
    else:
        FAIL += 1; print('FAIL %s  %s' % (n, d))


def parse(t): return list(csv.reader(io.StringIO(t), delimiter='\t'))
def render(rows):
    b = io.StringIO(); csv.writer(b, delimiter='\t', lineterminator='\n').writerows(rows); return b.getvalue()


raw = open(SRC, 'rb').read()
sha0 = hashlib.sha256(raw).hexdigest()
ck('A1 SRC sha == V562', sha0 == SHA562, sha0[:16])
ck('A2 SRC bytes 133312', len(raw) == 133312, len(raw))
ck('A3 SRC CR=0', raw.count(b'\r') == 0, raw.count(b'\r'))
txt = raw.decode('utf-8')
rows = parse(txt)
ck('B1 渲染回环 == 原文', render(rows) == txt)
m = {r[0]: r for r in rows[1:]}
ck('B2 54 行 5 列', len(rows) - 1 == 54 and all(len(r) == 5 for r in rows))

tot = sum(c.count('\\\\') for r in rows[1:] for c in r)
ck('C1 全文双反斜杠恰 2 处', tot == 2, tot)
ck('C2 都在 F35 第 5 列', m['F35'][4].count('\\\\') == 2, m['F35'][4].count('\\\\'))
ck('C3 其余 53 行 0 处', all('\\\\' not in ''.join(r) for r in rows[1:] if r[0] != 'F35'))
ev = m['F35'][3]
ck('C4 evidence 列里同一路径是单反斜杠（形态不一致的对照）',
   'RULING_R15_20261119\\work\\strict_panel.py' in ev and '\\\\' not in ev, None)
lim0 = m['F35'][4]
b0 = len(lim0.encode())
ck('C5 改前 F35.lim = 11502 B', b0 == 11502, b0)

lim1 = lim0.replace('\\\\', '\\')
ck('D1 替换后双反斜杠 0 处', lim1.count('\\\\') == 0)
ck('D2 字节 11502 -> 11500', len(lim1.encode()) == 11500, len(lim1.encode()))
ck('D3 字符数减 2', len(lim0) - len(lim1) == 2, len(lim0) - len(lim1))
ck('D4 改后路径与 evidence 列同形',
   'RULING_R15_20261119\\work\\strict_panel.py' in lim1, None)
ck('D5 剩余单反斜杠数 = 原单 + 2', lim1.count('\\') == lim0.count('\\') - 2, (lim1.count('\\'), lim0.count('\\')))

newrows = [rows[0]] + [[r[0], r[1], r[2], r[3], lim1 if r[0] == 'F35' else r[4]] for r in rows[1:]]
newraw = render(newrows).encode('utf-8')
ck('E1 CR=0 / LF=55', newraw.count(b'\r') == 0 and newraw.count(b'\n') == 55, newraw.count(b'\n'))
ck('E2 字节 133310（−2）', len(newraw) == 133310, len(newraw))
nm = {r[0]: r for r in parse(newraw.decode('utf-8'))[1:]}
chg = [(r[0], i) for r in parse(newraw.decode('utf-8'))[1:] for i in range(5) if nm[r[0]][i] != m[r[0]][i]]
ck('F1 变化单元恰 1 个（F35 第 5 列）', chg == [('F35', 4)], chg)
ck('F2 其余 53 行 × 5 列逐单元相同',
   all(nm[k][i] == m[k][i] for k in m if k != 'F35' for i in range(5)))
ck('F3 F35 statement 一字未动', nm['F35'][1] == m['F35'][1])

bak = os.path.join(BASE, 'R179_FACTINDEX_V562.before_r179d.bak')
if not os.path.exists(bak): shutil.copy2(SRC, bak)
ck('G1 母本备份 sha 可复算', hashlib.sha256(open(bak, 'rb').read()).hexdigest() == sha0)
if FAIL:
    print('ABORT 未写盘'); sys.exit(1)
if '--dry' in sys.argv:
    print('--dry 全通过'); sys.exit(0)
os.makedirs(DST_DIR, exist_ok=True)
open(DST, 'wb').write(newraw)
rb = open(DST, 'rb').read()
ck('H1 回读一致', rb == newraw)
ck('H2 母本未改', hashlib.sha256(open(SRC, 'rb').read()).hexdigest() == sha0)
print('V563 = %d B / %s' % (len(rb), hashlib.sha256(rb).hexdigest()))
print('---- %d PASS / %d FAIL ----' % (PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)
