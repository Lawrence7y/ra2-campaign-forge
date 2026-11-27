# -*- coding: utf-8 -*-
"""r178e：V560 -> V561，只在 F35.limitations 末尾追加 r178c_seg.txt 的内容。

fail-closed：全部断言在写盘之前；写盘后回读校验。
编码纪律：新文件必须与 V560 同规约（csv.writer / delimiter=TAB / lineterminator=LF），
          且除 F35.limitations 外**逐单元**相同。
"""
import csv, glob, hashlib, io, os, shutil, sys

TIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(TIER, 'R17_LEAD_BASELINE')
SRC = glob.glob(os.path.join(TIER, 'R17_R*_FACTINDEX_V560'))[0] + '/FACT_INDEX.tsv'
DST_DIR = os.path.join(TIER, 'R17_R129_FACTINDEX_V561')
DST = os.path.join(DST_DIR, 'FACT_INDEX.tsv')
SEGF = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'r178c_seg.txt')
S1, S2 = '同血缘克隆', '不是独立实现'
PASS = FAIL = 0


def ck(n, c, d=''):
    global PASS, FAIL
    if c:
        PASS += 1; print('PASS %s  %s' % (n, d))
    else:
        FAIL += 1; print('FAIL %s  %s' % (n, d))


def dm(t):
    dep = [0] * len(t); d = 0
    for i, ch in enumerate(t):
        if ch == '「':
            d += 1; dep[i] = d; continue
        dep[i] = d
        if ch == '」':
            d = max(0, d - 1)
    return dep


def counts(t, s):
    dep = dm(t)
    ps = [i for i in range(len(t)) if t.startswith(s, i)]
    return len(ps), sum(1 for p in ps if dep[p] == 0)


def parse(txt):
    return list(csv.reader(io.StringIO(txt), delimiter='\t'))


def render(rows):
    buf = io.StringIO()
    csv.writer(buf, delimiter='\t', lineterminator='\n').writerows(rows)
    return buf.getvalue()


raw = open(SRC, 'rb').read()
sha0 = hashlib.sha256(raw).hexdigest()
txt = raw.decode('utf-8')
ck('A1 SRC sha is V560', sha0 == 'ede48f3c3204804013658046b17ebc7cff23e5b5ec024407a2f79555147ce6a4', sha0[:16])
ck('A2 SRC bytes 130510', len(raw) == 130510, len(raw))
ck('A3 SRC CR=0', raw.count(b'\r') == 0, raw.count(b'\r'))

seg = open(SEGF, encoding='utf-8').read()
ck('B1 新段无 CR', '\r' not in seg)
ck('B2 新段无 TAB', '\t' not in seg)
ck('B3 新段无反引号', '`' not in seg)
ck('B4 新段无 ASCII 双引号（否则会触发 CSV 转义）', '"' not in seg, seg.count('"'))
ck('B5 新段以 【R178 开头', seg.startswith('【R178 补·'), seg[:12])
ck('B6 新段以 。结尾', seg.endswith('。'), seg[-8:])
ck('B7 新段「」配对且末深度 0', seg.count('「') == seg.count('」') and dm(seg)[-1] == 0,
   (seg.count('「'), seg.count('」'), dm(seg)[-1]))
t1, b1 = counts(seg, S1); t2, b2 = counts(seg, S2)
ck('B8 新段甲总 1 裸 0', (t1, b1) == (1, 0), (t1, b1))
ck('B9 新段乙总 2 裸 0', (t2, b2) == (2, 0), (t2, b2))
ck('B10 新段字节数', len(seg.encode('utf-8')) == 2806, len(seg.encode('utf-8')))

rows = parse(txt)
hdr, data = rows[0], rows[1:]
m = {r[0]: r for r in data}
ck('C1 54 数据行 / 5 列', len(data) == 54 and all(len(r) == 5 for r in data), len(data))
ck('C2 渲染回环 == 磁盘原文（同规约）', render(rows) == txt,
   (len(render(rows)), len(txt)))

f35 = m['F35']
lim0 = f35[4]
ct1, cb1 = counts(f35[1], S1); ct2, cb2 = counts(f35[1], S2)
lt1, lb1 = counts(lim0, S1); lt2, lb2 = counts(lim0, S2)
print('  改前 F35 stmt 甲/乙 t,b = %d/%d, %d/%d' % (ct1, cb1, ct2, cb2))
print('  改前 F35 lim  甲/乙 t,b = %d/%d, %d/%d' % (lt1, lb1, lt2, lb2))
ck('C3 改前 stmt 裸 (1,1) 总 (1,1)', (ct1, cb1, ct2, cb2) == (1, 1, 1, 1), (ct1, cb1, ct2, cb2))
ck('C4 改前 lim 甲总 5 裸 0', (lt1, lb1) == (5, 0), (lt1, lb1))
ck('C5 改前 lim 乙总 8 裸 1', (lt2, lb2) == (8, 1), (lt2, lb2))
ck('C6 改前 lim 无 R178 段', '【R178 补·' not in lim0, lim0.count('【R178 补·'))

# 构造 V561
lim1 = lim0 + ' ' + seg
ct1b, cb1b = counts(f35[1], S1); ct2b, cb2b = counts(f35[1], S2)
lt1b, lb1b = counts(lim1, S1); lt2b, lb2b = counts(lim1, S2)
print('  改后 F35 lim  甲/乙 t,b = %d/%d, %d/%d' % (lt1b, lb1b, lt2b, lb2b))
ck('D1 改后 stmt 裸计数不变 (1,1)', (cb1b, cb2b) == (1, 1), (cb1b, cb2b))
ck('D2 改后 lim 裸计数不变 (0,1) —— 双向不动点', (lb1b, lb2b) == (0, 1), (lb1b, lb2b))
ck('D3 改后 lim 总计数 = 改前 + 段内数：甲 5+1=6', lt1b == lt1 + t1, (lt1b, lt1, t1))
ck('D4 改后 lim 总计数 = 改前 + 段内数：乙 8+2=10', lt2b == lt2 + t2, (lt2b, lt2, t2))
ck('D5 段内声明值 (1,1)/(6,10) 与实测重合',
   (cb1b, cb2b) == (1, 1) and (lt1b, lt2b) == (6, 10), (cb1b, cb2b, lt1b, lt2b))

newrows = [hdr] + [[r[0],
                    r[1],
                    r[2],
                    r[3],
                    lim1 if r[0] == 'F35' else r[4]] for r in data]
newtxt = render(newrows)
newraw = newtxt.encode('utf-8')
ck('E1 新文件 CR=0', newraw.count(b'\r') == 0, newraw.count(b'\r'))
ck('E2 新文件 LF = 55（同 V560）', newraw.count(b'\n') == 55, newraw.count(b'\n'))
ck('E3 字节增量 = 段字节 + 1 个分隔空格', len(newraw) - len(raw) == len(seg.encode('utf-8')) + 1,
   (len(newraw) - len(raw), len(seg.encode('utf-8'))))

new_parse = parse(newtxt)
nm = {r[0]: r for r in new_parse[1:]}
chg = [(r[0], i) for r in new_parse[1:] for i in range(5) if nm[r[0]][i] != m[r[0]][i]]
ck('F1 变化单元恰 1 个且为 F35 第 5 列', chg == [('F35', 4)], chg)
ck('F2 其余 53 行 × 5 列逐单元相同',
   all(nm[k][i] == m[k][i] for k in m if k != 'F35' for i in range(5)))

# 备份 + 写盘
os.makedirs(DST_DIR, exist_ok=True)
bakd = os.path.join(BASE, 'R178_FACTINDEX_V560.before_r178.bak')
if not os.path.exists(bakd):
    shutil.copy2(SRC, bakd)
ck('G1 母本备份已存在且 sha 相同',
   hashlib.sha256(open(bakd, 'rb').read()).hexdigest() == sha0)

if FAIL:
    print('ABORT %d FAIL，未写盘' % FAIL); sys.exit(1)
if '--dry' in sys.argv:
    print('--dry：A..F 全通过，未写盘。'); print('---- %d PASS / %d FAIL (dry) ----' % (PASS, FAIL)); sys.exit(0)

with open(DST, 'wb') as f:
    f.write(newraw)
rb = open(DST, 'rb').read()
ck('H1 回读等于写入内容', rb == newraw)
ck('H2 回读 CR=0', rb.count(b'\r') == 0)
ck('H3 母本未被改动', hashlib.sha256(open(SRC, 'rb').read()).hexdigest() == sha0)
newsha = hashlib.sha256(rb).hexdigest()
print()
print('V561 = %d B / sha256 %s' % (len(rb), newsha))
print('F35.limitations: %d -> %d chars, %d -> %d bytes'
      % (len(lim0), len(lim1), len(lim0.encode()), len(lim1.encode())))
print('F35.statement bytes 不变 = %d' % len(f35[1].encode()))
print('---- %d PASS / %d FAIL ----' % (PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)
