# -*- coding: utf-8 -*-
"""r179b：V561 -> V562，把 F24/F29 limitations 里 5 处字面双百分号改成单百分号。

fail-closed：全部断言在写盘之前；写盘后回读校验。
改动面：恰 2 个单元格（F24 第 5 列 −2 B、F29 第 5 列 −3 B），全文 −5 B。
编码规约沿用 V561（csv.writer / delimiter=TAB / lineterminator=LF），故 V560 起的引号转义
逐字节保持，不引入新的规约变更。
"""
import csv, hashlib, io, os, shutil, sys

TIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(TIER, 'R17_LEAD_BASELINE')
SRC_DIR = os.path.join(TIER, 'R17_R129_FACTINDEX_V561')
SRC = os.path.join(SRC_DIR, 'FACT_INDEX.tsv')
DST_DIR = os.path.join(TIER, 'R17_R130_FACTINDEX_V562')
DST = os.path.join(DST_DIR, 'FACT_INDEX.tsv')
SHA561 = 'dd2c55c6f8aeadf3195bf1dc7fc9bf39ce70ed5ad771c76d52b80e86fe25fee7'
PASS = FAIL = 0


def ck(n, c, d=''):
    global PASS, FAIL
    if c:
        PASS += 1; print('PASS %s  %s' % (n, d))
    else:
        FAIL += 1; print('FAIL %s  %s' % (n, d))


def parse(txt):
    return list(csv.reader(io.StringIO(txt), delimiter='\t'))


def render(rows):
    buf = io.StringIO()
    csv.writer(buf, delimiter='\t', lineterminator='\n').writerows(rows)
    return buf.getvalue()


raw = open(SRC, 'rb').read()
sha0 = hashlib.sha256(raw).hexdigest()
ck('A1 SRC sha == V561 pin', sha0 == SHA561, sha0[:16])
ck('A2 SRC bytes 133317', len(raw) == 133317, len(raw))
ck('A3 SRC CR=0', raw.count(b'\r') == 0, raw.count(b'\r'))
txt = raw.decode('utf-8')

rows = parse(txt)
ck('B1 渲染回环 == 磁盘原文（同规约，V560 起的引号转义保持）', render(rows) == txt,
   (len(render(rows)), len(txt)))
hdr, data = rows[0], rows[1:]
m = {r[0]: r for r in data}
ck('B2 54 数据行 / 全 5 列', len(data) == 54 and all(len(r) == 5 for r in data), len(data))

# 改动前的精确计数（一次取证）
tot = sum(c.count('%%') for r in data for c in r)
ck('C1 全文双写恰 5 处', tot == 5, tot)
ck('C2 F24.lim 恰 2 处', m['F24'][4].count('%%') == 2, m['F24'][4].count('%%'))
ck('C3 F29.lim 恰 3 处', m['F29'][4].count('%%') == 3, m['F29'][4].count('%%'))
ck('C4 其余 52 行双写 0 处',
   all(r[0] in ('F24', 'F29') for r in data if '%%' in ''.join(r)), None)
lim24_0, lim29_0 = m['F24'][4], m['F29'][4]
b24_0, b29_0 = len(lim24_0.encode()), len(lim29_0.encode())
ck('C5 改前 F24.lim / F29.lim 字节 = (36142, 15259)', (b24_0, b29_0) == (36142, 15259), (b24_0, b29_0))
ck('C6 改前 statement 字节 = F24 11349 / F29 3435',
   (len(m['F24'][1].encode()), len(m['F29'][1].encode())) == (11349, 3435), None)

lim24_1 = lim24_0.replace('%%', '%')
lim29_1 = lim29_0.replace('%%', '%')
ck('D1 F24 替换后双写 0、单 % 增 2',
   lim24_1.count('%%') == 0 and lim24_1.count('%') == lim24_0.count('%') - 2,
   (lim24_1.count('%'), lim24_0.count('%')))
ck('D2 F29 替换后双写 0、单 % 增 3',
   lim29_1.count('%%') == 0 and lim29_1.count('%') == lim29_0.count('%') - 3,
   (lim29_1.count('%'), lim29_0.count('%')))
ck('D3 F24 字节 36142 -> 36140', len(lim24_1.encode()) == 36140, len(lim24_1.encode()))
ck('D4 F29 字节 15259 -> 15256', len(lim29_1.encode()) == 15256, len(lim29_1.encode()))
ck('D5 两个替换过的百分比语义不变（数值与正文叙事文档一致）',
   all(s in lim24_1 for s in ('6.03%', '3.64%')) and all(s in lim29_1 for s in ('88.5%', '50%', '81.82%')), None)
ck('D6 除这 5 个字符外两单元格逐字相同（长度差 = 删掉的字符数）',
   len(lim24_0) - len(lim24_1) == 2 and len(lim29_0) - len(lim29_1) == 3,
   (len(lim24_0) - len(lim24_1), len(lim29_0) - len(lim29_1)))

newrows = [hdr] + [[r[0], r[1], r[2], r[3],
                    lim24_1 if r[0] == 'F24' else lim29_1 if r[0] == 'F29' else r[4]] for r in data]
newtxt = render(newrows)
newraw = newtxt.encode('utf-8')
ck('E1 新文件 CR=0', newraw.count(b'\r') == 0, newraw.count(b'\r'))
ck('E2 新文件 LF = 55', newraw.count(b'\n') == 55, newraw.count(b'\n'))
ck('E3 字节 = 133312（−5）', len(newraw) == 133312, len(newraw))
ck('E4 引号转义规约未变：双引号对数与 V561 相同',
   newraw.count(b'""') == raw.count(b'""'), (newraw.count(b'""'), raw.count(b'""')))

newp = parse(newtxt)
nm = {r[0]: r for r in newp[1:]}
chg = [(r[0], i) for r in newp[1:] for i in range(5) if nm[r[0]][i] != m[r[0]][i]]
ck('F1 变化单元恰 2 个：F24 第 5 列 + F29 第 5 列', chg == [('F24', 4), ('F29', 4)], chg)
ck('F2 其余 52 行 × 5 列逐单元格相同',
   all(nm[k][i] == m[k][i] for k in m if k not in ('F24', 'F29') for i in range(5)))
ck('F3 两个 statement 一字未动',
   nm['F24'][1] == m['F24'][1] and nm['F29'][1] == m['F29'][1])
ck('F4 grade / evidence 四列未动',
   all(nm[k][i] == m[k][i] for k in ('F24', 'F29') for i in (0, 2, 3)))

os.makedirs(DST_DIR, exist_ok=True)
bakd = os.path.join(BASE, 'R179_FACTINDEX_V561.before_r179.bak')
if not os.path.exists(bakd):
    shutil.copy2(SRC, bakd)
ck('G1 母本备份可复算 sha', hashlib.sha256(open(bakd, 'rb').read()).hexdigest() == sha0)

if FAIL:
    print('ABORT %d FAIL，未写盘' % FAIL); sys.exit(1)
if '--dry' in sys.argv:
    print('--dry：全通过，未写盘。'); print('---- %d PASS / %d FAIL (dry) ----' % (PASS, FAIL)); sys.exit(0)

with open(DST, 'wb') as f:
    f.write(newraw)
rb = open(DST, 'rb').read()
ck('H1 回读等于写入内容', rb == newraw)
ck('H2 回读 CR=0', rb.count(b'\r') == 0)
ck('H3 母本 V561 一字未改', hashlib.sha256(open(SRC, 'rb').read()).hexdigest() == sha0)
print()
print('V562 = %d B / sha256 %s' % (len(rb), hashlib.sha256(rb).hexdigest()))
print('F24.lim %d -> %d B ; F29.lim %d -> %d B ; 全文 %d -> %d B'
      % (b24_0, len(lim24_1.encode()), b29_0, len(lim29_1.encode()), len(raw), len(rb)))
print('---- %d PASS / %d FAIL ----' % (PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)
