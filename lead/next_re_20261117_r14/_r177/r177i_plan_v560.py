# -*- coding: utf-8 -*-
"""R177：V559 -> V560。唯一改动 = F29.limitations 末尾追加「自指终止式」一段。
纪律：全部断言在写盘之前；母本只读；新目录独占创建；写后回读全量校验。"""
import csv, io, os, sys, hashlib, time

T = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
SRC = os.path.join(T, 'R17_R128_FACTINDEX_V559/FACT_INDEX.tsv')
DSTDIR = os.path.join(T, 'R17_R128_FACTINDEX_V560')
DST = os.path.join(DSTDIR, 'FACT_INDEX.tsv')
BASELINE = os.path.join(T, 'R17_LEAD_BASELINE')
P = F = 0
def ck(n, c, d=''):
    global P, F
    if c: P += 1; print('PASS', n, d)
    else: F += 1; print('FAIL', n, d)

raw = open(SRC, 'rb').read()
txt = raw.decode('utf-8')
ck('A1 src sha = V559 pin', hashlib.sha256(raw).hexdigest() ==
   'e4642d554d8ba9f1dab25b6a2b456e365252051035f9104003b58ff622d489e9')
ck('A2 src bytes 129405', len(raw) == 129405, '%d' % len(raw))
ck('A3 src CR=0', raw.count(b'\r') == 0)
ck('A4 src LF=55', raw.count(b'\n') == 55, '%d' % raw.count(b'\n'))

TARGET = '6 个不同桩体'
APPEND = ('**【R177 订正·本段的自指失效在此终止】** 上文「statement **1** 次、limitations **2** 次、'
          '合计 **3** 次」是**落盘前**读数：本段（R170 段）自身即含被计数的那个串 **1** 次 ⇒ 落盘后 '
          'limitations 实为 **3**、合计 **4**（逐版实测：V540–V544 limitations **1**、V545–V549 ***2**、'
          '**V550 起 3**，statement **恒 1**；_r177/r177e_f29_selfref.py 9 断言 0 FAIL）。**本订正段刻意'
          '只用「该串」指代、不复述本体** ⇒ 写入后 limitations 仍为 **3**、「合计 4」是**不动点**、不再随'
          '引用漂移。判据（跨家族审计员 #420 提出，主会话 _r177/r177f 22 断言复算成立）：**增量 = 新增段'
          '自身字面出现数，不是常数 1** —— V553→V554 为 **+0/+2**、V554→V555 为 **+3/+2**、V555→V556 为 '
          '**+1/+1**；段身份须按段头（到「】」为止）建索引，用全文等值当身份会把「被改动一个标点的旧段」'
          '误判成新增段（S-642，自测当场抓出，首版三断言全红）。')
# 关键反控：追加段自身不得含被计数的串本体（这就是终止式的全部内容）
ck('B1 APPEND 不含被计数串本体', APPEND.count(TARGET) == 0, '%d' % APPEND.count(TARGET))
ck('B2 APPEND 含指代「该串」', APPEND.count('该串') == 1, '%d' % APPEND.count('该串'))
ck('B3 APPEND 写死 limitations 3', APPEND.count('limitations 仍为 **3**') == 1)
ck('B4 APPEND 写死合计 4', APPEND.count('合计 4') == 1)

rows = list(csv.reader(io.StringIO(txt), delimiter='\t'))
idx = {r[0]: i for i, r in enumerate(rows)}
i29 = idx['F29']
ck('C1 F29 行找到', rows[i29][0] == 'F29')
ck('C2 src F29.lim 不含 APPEND', rows[i29][4].count(APPEND) == 0)
ck('C3 src F29.lim 该串恰 3 次', rows[i29][4].count(TARGET) == 3, '%d' % rows[i29][4].count(TARGET))
ck('C4 src F29.stmt 该串恰 1 次', rows[i29][1].count(TARGET) == 1, '%d' % rows[i29][1].count(TARGET))

new_rows = [list(r) for r in rows]
new_rows[i29][4] = new_rows[i29][4] + APPEND
buf = io.StringIO()
w = csv.writer(buf, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_MINIMAL)
for r in new_rows:
    w.writerow(r)
new = buf.getvalue()
# 回环：重解析后逐单元等于 new_rows（含含引号/换行字段）
back = list(csv.reader(io.StringIO(new), delimiter='\t'))
ck('D1 重解析行数 55', len(back) == 55, '%d' % len(back))
ck('D2 重解析逐单元等于构造值', back == new_rows)
ck('D3 54 数据行 5 列', all(len(r) == 5 for r in back[1:]) and len(back) == 55)

diff = [(a[0], [k for k in range(5) if a[k] != b[k]]) for a, b in zip(rows, back) if a != b]
ck('D4 差分行恰 F29、差列恰 limitations', diff == [('F29', [4])], repr(diff))
same = sum(1 for a, b in zip(rows, back) if a == b)
ck('D5 其余 54 行逐单元相同', same == 54, '%d' % same)

ck('E1 无行被缩短', all(len(back[i][1].encode()) >= len(rows[i][1].encode()) and
                      len(back[i][4].encode()) >= len(rows[i][4].encode()) for i in range(55)))
ck('E2 F29.lim 只增不减', len(back[i29][4].encode()) > len(rows[i29][4].encode()),
   '%d -> %d' % (len(rows[i29][4].encode()), len(back[i29][4].encode())))
ck('E3 新 F29.lim 该串仍 3 次（终止式）', back[i29][4].count(TARGET) == 3, '%d' % back[i29][4].count(TARGET))
ck('E4 声明值 3 与实测值一致（不动点）', back[i29][4].count(TARGET) == 3)
ck('E5 总量增加', len(new.encode()) > len(raw), '%+d B' % (len(new.encode()) - len(raw)))
ck('E6 无 CR', '\r' not in new)
ck('E7 母本未被改', hashlib.sha256(open(SRC, 'rb').read()).hexdigest() ==
   'e4642d554d8ba9f1dab25b6a2b456e365252051035f9104003b58ff622d489e9')

# 反控：把 APPEND 里「该串」换成串本体，终止式应失效（计数变 4 != 声明 3）
bad = APPEND.replace('该串', TARGET)
ck('F1 反控：若复述本体则实测变 4 ≠ 声明 3',
   (rows[i29][4] + bad).count(TARGET) == 4 and (rows[i29][4] + bad).count(TARGET) != 3)

if F:
    print('ABORT: %d FAIL before write' % F); sys.exit(1)

ts = time.strftime('%Y%m%d_%H%M%S')
bpath = os.path.join(BASELINE, 'FACT_INDEX_V559.before_r177_%s.tsv' % ts)
with open(bpath, 'xb') as f:
    f.write(raw)
ck('G1 备份独占创建', os.path.getsize(bpath) == len(raw))
ck('G2 备份逐字节相同', open(bpath, 'rb').read() == raw)
ck('G3 目标目录尚不存在', not os.path.exists(DST))
os.mkdir(DSTDIR)
data = new.encode('utf-8')
with open(DST, 'xb') as f:
    f.write(data)
rb = open(DST, 'rb').read()
ck('H1 回读字节数', len(rb) == len(data), '%d' % len(rb))
ck('H2 回读逐字节相同', rb == data)
ck('H3 回读 CR=0', rb.count(b'\r') == 0)
ck('H4 回读 LF=55', rb.count(b'\n') == 55, '%d' % rb.count(b'\n'))
sha = hashlib.sha256(rb).hexdigest()
print('V560 = %d B / %s' % (len(rb), sha))
print('delta = %+d B' % (len(rb) - len(raw)))
print('F29.lim bytes %d ; F29.stmt bytes %d' % (len(back[i29][4].encode()), len(back[i29][1].encode())))
print('---- %d PASS / %d FAIL ----' % (P, F))
sys.exit(1 if F else 0)
