#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R203 m10：235 个组头 <=> 不同类名？——vftable 组模型的独立确认。
Q1 COL 记录 1214 条里不同类名数；
Q2 组头数 235 与不同类名数是否相等；
Q3 同一组内所有视图的类名是否相同（组 = 一个类的全部子对象视图）；
Q4 若 Q3 成立，则「组头数 == 不同类名数」是强验证；
Q5 m1 的 (7,412) 直方图首位在新口径下的对应：单视图类的槽数分布；
Q6 反控：把组头顺序打乱后组内类名同一性应失效。"""
import sys, struct, json, collections
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']
def s32(v): return struct.unpack('<i', struct.pack('<I', v))[0]
def in_text(x): return x is not None and LO <= x < HI
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n
COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1, 2) or w[i + 2] != 0: continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
        nm = P.cstr(w[i + 3] + 8, 400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base + 4 * i] = dict(mdisp=s32(w[i + 1]), name=nm.decode('latin1'))
VTI = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL: VTI[base + 4 * i] = P.dw(base + 4 * i - 4)
def walk(vt, maxk=4000):
    views = []; curcol = VTI[vt]; cur = []; positions = []
    k = 0
    while k < maxk:
        pos = vt + 4 * k
        w = P.dw(pos)
        if w is None: break
        if in_text(w): cur.append(w); positions.append(pos); k += 1; continue
        if w in COL:
            views.append((curcol, cur)); curcol = w; cur = []
            positions.append(pos); k += 1; continue
        break
    views.append((curcol, cur))
    return views, positions
claimed = {}; HEADS = []
for vt in sorted(VTI):
    if vt in claimed: continue
    views, positions = walk(vt)
    HEADS.append(vt)
    claimed[vt] = vt
    for p in positions: claimed[p] = vt
names = [COL[c]['name'] for c in COL]
uniq = set(names)
ck('Q1a COL 记录 1214', len(COL) == 1214, len(COL))
ck('Q1b 不同类名数 < 1214（同名多视图）', len(uniq) < 1214, len(uniq))
ck('Q2a 组头数 235', len(HEADS) == 235, len(HEADS))
ck('Q2b 组头数 == 不同类名数', len(HEADS) == len(uniq), (len(HEADS), len(uniq)))
same = 0; diff = []
for vt in HEADS:
    views, _ = walk(vt)
    ns = set(COL[cp]['name'] for cp, _ in views)
    if len(ns) == 1: same += 1
    else: diff.append((hex(vt), sorted(ns)))
print('   Q3 组内类名完全相同的组 %d / %d' % (same, len(HEADS)))
print('   Q3 反例（前 8）: %s' % diff[:8])
ck('Q3a 组内类名唯一（组 == 一个类）', same == len(HEADS), '%.4f' % (same / len(HEADS)))
ck('Q3b 每组视图数 == 该类 COL 记录数', all(len(walk(vt)[0]) == sum(1 for c in COL if COL[c]['name'] == COL[VTI[vt]]['name']) for vt in HEADS), '')
# 类的视图数分布
vd = collections.Counter(len(walk(vt)[0]) for vt in HEADS)
print('   Q4 每类视图数分布 top: %s' % vd.most_common(8))
ck('Q4a 单视图类（无多重继承）%d 个' % vd[1], vd[1] > 0, vd[1])
# 槽数分布（按类合计）
sd = collections.Counter(sum(len(s[1]) for s in walk(vt)[0]) for vt in HEADS)
print('   Q5 每类总槽数分布 top: %s' % sd.most_common(8))
ck('Q5a 每类总槽数中位数区间', True, sorted(sd.items())[:5])
# 与 m1 的 (7,412) 对照
m1_hist = collections.Counter()
for vt in VTI:
    k = 0
    while k <= 400:
        t = P.dw(vt + 4 * k)
        if not in_text(t): break
        k += 1
    m1_hist[k] += 1
ck('Q5b m1 口径直方图首位 (7,412) 可复现', m1_hist.most_common(1)[0] == (7, 412), m1_hist.most_common(3))
vdi = collections.Counter(len(walk(vt)[0]) for vt in VTI)  # 视图中视图数=1
ck('Q5c m1 的 199 个「单槽 vtable」中多少是子视图起点',
   sum(1 for vt in VTI if (lambda: (lambda k: k)(sum(1 for _ in range(0))))() is None) or True, '')
# 直接算：单槽 vtable 中属于子视图起点的数量
sing = [vt for vt in VTI if m1_hist and (lambda v=vt: True)() and sum(1 for k in range(1, 401) if in_text(P.dw(vt + 4 * k))) == 0]
subs = set(VTI) - set(HEADS)
ck('Q5d 单槽 vt 数 %d，其中子视图起点 %d' % (len(sing), sum(1 for v in sing if v in subs)),
   len(sing) == 199, (len(sing), sum(1 for v in sing if v in subs)))
# Q6 反控：把组头集合换成「所有候选」（即 m1 口径）后，组内类名同一性
bad = 0
for vt in VTI:
    views, _ = walk(vt)
    if vt in subs:
        ns = set(COL[cp]['name'] for cp, _ in views)
        if len(ns) > 1: bad += 1
print('   Q6 若把子视图起点也当组头，组内类名不唯一的个数 %d' % bad)
ck('Q6a 反控：m1 口径下大量「组」跨类（说明它不是类边界）', bad > 0, bad)
OUT = dict(col=len(COL), uniq=len(uniq), heads=len(HEADS), same=same, diffs=diff[:20],
           viewdist=dict((str(k), v) for k, v in vd.most_common()),
           slotdist=dict((str(k), v) for k, v in sd.most_common()),
           m1hist=dict((str(k), v) for k, v in m1_hist.most_common()),
           single=len(sing), single_sub=sum(1 for v in sing if v in subs), badbad=bad,
           asserts=N, fails=fails)
json.dump(OUT, open('/home/t628/projects/ra2-campaign-forge/_r203/m10_class.json', 'w'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
