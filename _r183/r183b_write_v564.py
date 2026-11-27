# -*- coding: utf-8 -*-
"""R183 B：V563 -> V564，只改 F35.limitations 一处（把裸唯一性断言就地加作用域 + 追加补段）。
fail-closed：全部断言在任何写盘动作之前。
"""
import csv, hashlib, io, os, shutil, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
SRC_DIR = os.path.join(TIER, 'R17_R131_FACTINDEX_V563')
DST_DIR = os.path.join(TIER, 'R17_R131_FACTINDEX_V564')
SRC = os.path.join(SRC_DIR, 'FACT_INDEX.tsv')
DST = os.path.join(DST_DIR, 'FACT_INDEX.tsv')

OLD = ('本条 evidence_paths 唯一一项即该已失文件，故 F35 是本表里与 F23 并列的'
       '**两条整行证据链失联项**之一（该普查的时点是 v5.32 全表，R138 复查未变）。')
NEW = ('在 v5.33 及以前口径下，本条 evidence_paths 唯一一项即该已失文件，故 F35 是本表里与 F23 并列的'
       '**两条整行证据链失联项**之一（该普查的时点是 v5.32 全表，R138 复查未变；'
       '**V534 起第 4 列已变为 5 项 / 4 项在盘 / 1 项失联，第 2 列 ④ 自 V540 起断言本条已不是整行失联项，'
       '故「两列相反」的作用域是 V540..V563，不是 V534 起；引本句必须带版本限定**）。')
ADD = (' **【R183 补·该作用域是逐版实测的】** `_r183/r183a_uniq_claim.py` **16 断言 0 FAIL**（含 4 组正反控：'
       '把第 4 列砍到 1 项 ⇒ 冲突归 0；给该句加版本限定 ⇒ 转「已限定」；删句 ⇒ 命中消失；'
       '向第 4 列 8 项的行注入同一断言 ⇒ 判据仍抓得住）。逐版实测：**V530..V533 第 4 列恰 1 项**（0 活 / 1 失），'
       '**V534 起 5 项（4 活 / 1 失）**，34 版连续无缺；第 2 列 ④ 在 **V530..V539 不存在**（该列长度恒 156）、**V540 起 1054**。'
       '⇒ 该句三个状态必须分开引：V530..V533 **真句**、V534..V539 **过期句**（无相反列）、V540..V563 **互斥句**。')

fails, n = [], 0
def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)

raw = open(SRC, 'rb').read()
SHA0 = hashlib.sha256(raw).hexdigest()
print('== A · 源版本硬闸 ==')
ck('A1 V563 字节 == 133310', len(raw) == 133310, len(raw))
ck('A2 V563 sha 命中 28423e79…', SHA0.startswith('28423e7928d84142'), SHA0[:16])
ck('A3 V563 CR == 0', raw.count(b'\r') == 0, raw.count(b'\r'))
ck('A4 目标目录不存在（历史版本一律保留不删不改）', not os.path.exists(DST_DIR), DST_DIR)

rows = list(csv.reader(io.StringIO(raw.decode('utf-8')), delimiter='\t'))
ck('A5 55 行 × 5 列', len(rows) == 55 and all(len(r) == 5 for r in rows), len(rows))
d = {r[0]: r for r in rows[1:]}
ck('A6 fact_id 序列 F01..F54', [r[0] for r in rows[1:]] == ['F%02d' % i for i in range(1, 55)])
def _rt(rows_):
    b = io.StringIO(); csv.writer(b, delimiter='\t', lineterminator='\n').writerows(rows_); return b

_rtb = _rt(rows)
ck('A7 往返一致（csv 读写不改字面）', _rtb.getvalue().encode('utf-8') == raw,
   (len(_rtb.getvalue().encode()), len(raw)))

print('== B · 目标文本约束 ==')
L0 = d['F35'][4]
ck('B1 OLD 在 F35.limitations 恰 1 处', L0.count(OLD) == 1, L0.count(OLD))
for bad in ['\t', '"', '\r']:
    ck('B2 新文本不含 %r' % bad, bad not in NEW and bad not in ADD)
# 不得引入会被 R178 段自指计数改变的串
for w in ['同血缘克隆', '不是独立实现']:
    ck('B3 新文本不含被 R178 段计数的串 %s' % w, w not in NEW and w not in ADD)
# 不得改变已有的被计数串次数
NEWROW = L0.replace(OLD, NEW) + ADD
for w, want in (('唯一一项', L0.count('唯一一项')), ('两条整行', L0.count('两条整行'))):
    ck('B4 %s 次数不变（%d）' % (w, want), NEWROW.count(w) == want, (L0.count(w), NEWROW.count(w)))
ck('B5 旧断言字面仍逐字在场（_r152/r152b 2.3 断言依赖它）', '唯一一项即该已失文件' in NEWROW)
ck('B6 limitations 只增长不缩短（facts_floors D6 no-shrink）',
   len(NEWROW.encode()) > len(L0.encode()), (len(L0.encode()), len(NEWROW.encode())))

# 逐单元格 diff：恰 1 个单元格变化
rows2 = [list(r) for r in rows]
d2 = {r[0]: r for r in rows2[1:]}
d2['F35'][4] = NEWROW
changed = [(r[0], c) for r, r2 in zip(rows[1:], rows2[1:]) for c in range(5) if r[c] != r2[c]]
ck('B7 变化单元格恰 1 个且为 F35 第 5 列', changed == [('F35', 4)], changed)
ck('B8 其余 53 行 × 5 列逐单元格相同',
   all(a[c] == b[c] for a, b in zip(rows[1:], rows2[1:]) if a[0] != 'F35' for c in range(5)))

buf = io.StringIO()
csv.writer(buf, delimiter='\t', lineterminator='\n').writerows(rows2)
newtxt = buf.getvalue()
newraw = newtxt.encode('utf-8')
print('== C · 新版本体 ==')
ck('C1 行数 55', len(newtxt.rstrip('\n').split('\n')) == 55)
ck('C2 CR == 0', newraw.count(b'\r') == 0)
ck('C3 每行 5 列', all(len(l.split('\t')) == 5 for l in newtxt.rstrip('\n').split('\n')))
delta = len(newraw) - len(raw)
print('   V563 %d B -> V564 %d B (delta %+d) ; 新 sha %s' % (len(raw), len(newraw), delta, hashlib.sha256(newraw).hexdigest()[:16]))
ck('C4 总字节只增不缩', delta > 0, delta)
ck('C5 delta == limitations 增量', delta == len(NEWROW.encode()) - len(L0.encode()), delta)

if fails:
    print('断言 %d 条，FAIL %d 条 ⇒ 拒绝写盘' % (n, len(fails)))
    sys.exit(1)

print('== D · 写盘（独占新建目录，绝不触碰 V563）==')
os.makedirs(DST_DIR, exist_ok=False)
with open(DST, 'wb') as f:
    f.write(newraw)
back = open(DST, 'rb').read()
ck('D1 回读一致', hashlib.sha256(back).hexdigest() == hashlib.sha256(newraw).hexdigest())
ck('D2 V563 未被触碰', hashlib.sha256(open(SRC, 'rb').read()).hexdigest() == SHA0)
print('   V564 = %d B / sha %s' % (len(back), hashlib.sha256(back).hexdigest()))
print('断言 %d 条，FAIL %d 条' % (n, len(fails)))
sys.exit(0 if not fails else 1)
