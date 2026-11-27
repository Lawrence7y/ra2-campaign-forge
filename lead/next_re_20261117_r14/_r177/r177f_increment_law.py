#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r177f：复算审计员 #420 的「增量 = 该补段自身字面出现数，不是常数 1」。
拆段 + 逐版计数 + 行级 sha；正反控成对。
"""
import csv, glob, hashlib, os, re, sys

TIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = '同血缘克隆'; B = '不是独立实现'
ok = fail = 0
def chk(c, m, extra=''):
    global ok, fail
    if c: ok += 1; print('  PASS ' + m + (('  ' + str(extra)) if extra else ''))
    else: fail += 1; print('  FAIL ' + m + (('  ' + str(extra)) if extra else ''))

def load(v):
    d = glob.glob(os.path.join(TIER, 'R17_R*_FACTINDEX_V%d' % v))[0]
    return os.path.join(d, 'FACT_INDEX.tsv')

V = {v: load(v) for v in range(553, 560)}
rows = {v: {r[0]: r for r in csv.reader(open(p, encoding='utf-8'), delimiter='\t')} for v, p in V.items()}

print('=== A. 逐版 limitations 计数（复算 #419/#420）===')
tab = {}
for v in range(553, 560):
    lim = rows[v]['F35'][4]
    tab[v] = (lim.count(A), lim.count(B), len(lim))
    print('  V%d  A=%d B=%d len=%d' % (v, tab[v][0], tab[v][1], tab[v][2]))
chk(tab[559][0] == 5 and tab[559][1] == 8, 'V559 实测 5 / 8（与我 r177a 及 #419/#420 一致）')
chk(tab[553][0] == 1 and tab[553][1] == 3, 'V553 实测 1 / 3')

print()
print('=== B. 增量（必须证明不是常数 1）===')
deltas = {}
for v in range(554, 560):
    dA = tab[v][0] - tab[v - 1][0]; dB = tab[v][1] - tab[v - 1][1]
    deltas[v] = (dA, dB)
    print('  V%d->V%d  dA=%+d dB=%+d' % (v - 1, v, dA, dB))
chk(deltas[554] == (0, 2), 'V553->V554 = +0/+2（不是 +1/+1 ⇒ 常数律假）', deltas[554])
chk(deltas[555] == (3, 2), 'V554->V555 = +3/+2', deltas[555])
chk(deltas[556] == (1, 1), 'V555->V556 = +1/+1', deltas[556])
chk(all(deltas[v] == (0, 0) for v in (557, 558, 559)), 'V556..V559 三版增量全 0/0（未追加 F35 补段）')
chk(len(set(deltas.values())) > 1, '增量不是单一常数 ⇒ 「每追加一段 +1」被实测推翻')

print()
print('=== C. 增量归属：每个新增段自身含多少字面 ===')
def segs(lim):
    """按 【 切段，返回 (段头20字, 段全文)"""
    parts = re.split(r'(?=【)', lim)
    return [(p[:24], p) for p in parts if p.strip()]

for v in (553, 554, 555, 556):
    lim = rows[v]['F35'][4]
    ss = segs(lim)
    print('  V%d 段数=%d' % (v, len(ss)))
    for h, p in ss:
        ca, cb = p.count(A), p.count(B)
        if ca or cb:
            print('      %-26s A=%d B=%d len=%d' % (h.replace('\n', ' '), ca, cb, len(p)))

print()
print('=== D. V554 新增段是否解释了 +0/+2 ===')
def segmap(lim):
    """按段头（到第一个 】 为止）建索引 —— S-642：不能用全文等值当段身份，
    同一段在后续版本里被改动一个标点就会全长不等，被误判成「新增段」。"""
    out = {}
    for p in re.split(r'(?=【)', lim):
        if not p.strip():
            continue
        h = p.split('】')[0] + '】'
        out[h] = out.get(h, '') + p
    return out

def delta_attrib(v_old, v_new):
    a, b = segmap(rows[v_old]['F35'][4]), segmap(rows[v_new]['F35'][4])
    added = [h for h in b if h not in a]
    changed = [h for h in b if h in a and a[h] != b[h]]
    da = sum(b[h].count(A) - a.get(h, '').count(A) for h in b)
    db = sum(b[h].count(B) - a.get(h, '').count(B) for h in b)
    return added, changed, da, db

for vo, vn in ((553, 554), (554, 555), (555, 556)):
    added, changed, da, db = delta_attrib(vo, vn)
    print('  V%d->V%d 新增段=%r 改动段=%r 段内增量 A=%+d B=%+d' % (vo, vn, added, changed, da, db))
    chk((da, db) == deltas[vn], 'V%d->V%d 按段头归属的增量 == 实测增量 %r' % (vo, vn, deltas[vn]))
    # 新增段自身的字面数（若同时有改动段，差值 = 新增段 - 改动段里被删的字面）
    for h in added:
        print('      新增段 %-30s A=%d B=%d len=%d' % (h, rows[vn]['F35'][4].count(h) and segmap(rows[vn]['F35'][4])[h].count(A), segmap(rows[vn]['F35'][4])[h].count(B), len(segmap(rows[vn]['F35'][4])[h])))

print()
print('=== E. F35 行逐字节相同（V556..V559）===')
h = {}
for v in (556, 557, 558, 559):
    line = rows[v]['F35']
    blob = '\t'.join(line).encode()
    h[v] = hashlib.sha256(blob).hexdigest()
    print('  V%d row sha=%s len=%d' % (v, h[v][:12], len(blob)))
chk(len(set(h.values())) == 1, 'V556..V559 F35 行 sha256 全同 ⇒ 四版计数必然相同')

print()
print('=== F. 审计员点名的三种同类污染量，逐个复算 ===')
sec = {}
for v in (553, 554, 555, 556, 557, 558, 559):
    sec[v] = rows[v]['F35'][4].count('次')
print('  limitations 内「次」出现数：', {v: sec[v] for v in sec})
chk(sec[553] < sec[554] < sec[555] < sec[559], '「次」总数随补段单调上涨（553<554<555<559）')
chk((sec[553], sec[554], sec[555], sec[559]) == (3, 15, 22, 30),
    '四值恰为 3/15/22/30（审计员报数复算成立）', (sec[553], sec[554], sec[555], sec[559]))
lim559 = rows[559]['F35'][4]
chk('184 字符' in lim559, '「184 字符」在 V559 limitations 在场')
chk('695 字符' in lim559, '「695 字符」在 V559 limitations 在场')

print()
print('=== G. F29 处同一律的独立验证（R170 段自称 2 次 vs 实测 3 次）===')
def f29(v):
    return rows[v]['F29'] if v in rows else None
V29 = {v: {r[0]: r for r in csv.reader(open(load(v), encoding='utf-8'), delimiter='\t')} for v in (549, 550, 559)}
T = '6 个不同桩体'
for v in (549, 550, 559):
    st, lim = V29[v]['F29'][1], V29[v]['F29'][4]
    print('  V%d  statement=%d limitations=%d' % (v, st.count(T), lim.count(T)))
chk(V29[549]['F29'][4].count(T) == 2, 'V549 limitations = 2（R170 落盘前）')
chk(V29[550]['F29'][4].count(T) == 3, 'V550 limitations = 3（R170 落盘后，+1 = 该段自身引文）')
seg170 = [p for _, p in segs(V29[559]['F29'][4]) if p.startswith('【R170')]
chk(len(seg170) == 1 and seg170[0].count(T) == 1, 'R170 段自身含该串恰 1 次 ⇒ 增量归属成立')
chk('limitations **2** 次' in seg170[0], 'R170 段逐字自称 limitations 2 次（而落盘后实测 3 次）')
chk('合计 **3** 次' in seg170[0], 'R170 段逐字自称合计 3 次（而落盘后实测 4 次）')

print()
print('=== H. 反控 ===')
chk(A not in '同血缘' , '反控：「同血缘」不含完整计数串')
chk(lim559.count(A + 'XX') == 0, '反控：变体 0 命中')

print()
print('RESULT: %d PASS / %d FAIL' % (ok, fail))
sys.exit(1 if fail else 0)
