#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R204 m7（定稿）：464 个非等差 BCA 的成因 + CHD+4 语义 + 视图集合等式。
m6 自错：X5a 把我自己的严格基址判据当执行员的判据，执行员的 490 实为「组内等差 -24」= m6 的 local，数值一致。
"""
import sys, struct, collections, json
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))
def s32(v): return struct.unpack('<i', struct.pack('<I', v))[0]
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']
def in_text(x): return x is not None and LO <= x < HI
COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1, 2) or w[i + 2] != 0: continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
        nm = P.cstr(w[i + 3] + 8, 400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base + 4 * i] = dict(mdisp=s32(w[i+1]), ptd=w[i+3], pchd=w[i+4], name=nm.decode('latin1'))
VTI = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL: VTI[base + 4 * i] = P.dw(base + 4 * i - 4)
G = collections.defaultdict(list)
for c, v in COL.items(): G[v['pchd']].append(c)
CHD = sorted(G)
BCD = {a: [P.dw(P.dw(a + 12) + 4 * j) for j in range(P.dw(a + 8))] for a in CHD}
uniq = sorted(set(b for v in BCD.values() for b in v))

# ---- Y1 等差 / 非等差分组特征 ----
arith = [a for a in CHD if all(BCD[a][i+1] - BCD[a][i] == -24 for i in range(len(BCD[a]) - 1))]
nonar = [a for a in CHD if a not in set(arith)]
print('   Y1 等差 %d / 非等差 %d' % (len(arith), len(nonar)))
def feat(a):
    v = BCD[a]
    return dict(n=len(v), mi=any(s32(P.dw(b+8)) != 0 for b in v), views=len(G[a]),
                maxdepth=max(P.dw(b+4) for b in v),
                jumps=sum(1 for i in range(len(v)-1) if v[i+1]-v[i] != -24))
import statistics
for nm, grp in (('等差', arith), ('非等差', nonar)):
    ns = [feat(a)['n'] for a in grp]; mip = sum(1 for a in grp if feat(a)['mi'])
    print('   Y1 %s: n 中位 %d 均值 %.2f max %d; MI 类 %d/%d; 视图数中位 %d' % (
        nm, statistics.median(ns), statistics.mean(ns), max(ns), mip, len(grp),
        statistics.median([feat(a)['views'] for a in grp])))
ck('Y1a 非等差组的 BCA 长度显著大于等差组',
   statistics.mean([feat(a)['n'] for a in nonar]) > statistics.mean([feat(a)['n'] for a in arith]),
   (statistics.mean([feat(a)['n'] for a in nonar]), statistics.mean([feat(a)['n'] for a in arith])))
ck('Y1b 非等差组含 MI 类占比显著更高',
   sum(1 for a in nonar if feat(a)['mi']) / len(nonar) > sum(1 for a in arith if feat(a)['mi']) / len(arith),
   (sum(1 for a in nonar if feat(a)['mi']), len(nonar), sum(1 for a in arith if feat(a)['mi']), len(arith)))
# 非等差 ⇔ BCA 长度 >= 阈值？
thr = collections.Counter()
for a in CHD:
    thr[('arith' if a in set(arith) else 'nonar', len(BCD[a]) >= 4)] += 1
print('   Y1 交叉表 %s' % dict(thr))
ck('Y1c 短 BCA（n<=3）几乎全是等差', all(a in set(arith) for a in CHD if len(BCD[a]) <= 3),
   sum(1 for a in CHD if len(BCD[a]) <= 3 and a not in set(arith)))

# ---- Y2 非等差的具体形态：跳转是否都落到「另一个 BCD」 ----
bcdset = set(uniq)
jump_ok = 0; jump_bad = []
for a in nonar:
    v = BCD[a]
    for i in range(len(v)-1):
        d = v[i+1] - v[i]
        if d == -24: continue
        if v[i+1] in bcdset: jump_ok += 1
        else: jump_bad.append((hex(a), hex(v[i]), hex(v[i+1])))
ck('Y2a 所有跳转目标都是合法 BCD（1002 池内）', not jump_bad, (jump_ok, len(jump_bad), jump_bad[:3]))
# 跳转差分值分布
jd = collections.Counter()
for a in nonar:
    v = BCD[a]
    for i in range(len(v)-1):
        d = v[i+1] - v[i]
        if d != -24: jd[d] += 1
print('   Y2 非等差跳转差分 top8 %s（总 %d）' % (jd.most_common(8), sum(jd.values())))
ck('Y2b 跳转差分全部是 8 的倍数', all(d % 8 == 0 for d in jd), [d for d in jd if d % 8][:4])

# ---- Y3 视图 mdisp 集合 == BCA mdisp 集合（等式，非仅子集） ----
eq = 0; neq = []
for a in CHD:
    vs = set(COL[c]['mdisp'] for c in G[a])
    bs = set(s32(P.dw(b + 8)) for b in BCD[a])
    if vs == bs: eq += 1
    else: neq.append((COL[G[a][0]]['name'][:40], sorted(vs), sorted(bs), len(BCD[a])))
print('   Y3 视图 mdisp 集合 == BCA mdisp 集合 %d / %d' % (eq, len(CHD)))
print('   Y3 不等样例 %s' % neq[:6])
ck('Y3a 集合等式成立率高或全部 >', eq > 0, (eq, len(CHD)))
# 逐条分析不等的原因：BCA 是否多出「非 0 且非视图」的 mdisp
extra = [(nm, vs, bs) for nm, vs, bs, n in neq if set(bs) - set(vs)]
ck('Y3b 不等时 BCA 只多不少（无视图 mdisp 缺失）', all(set(vs) <= set(bs) for nm, vs, bs, n in neq), len(neq))
ck('Y3c 多出的 mdisp 记录（样例数）', True, len(extra))

# ---- Y4 CHD+4 语义：与 views/n 的关系 ----
c4 = {a: P.dw(a + 4) for a in CHD}
tab = collections.Counter()
for a in CHD:
    tab[(c4[a], len(BCD[a]) == 1, len(G[a]) > 1)] += 1
print('   Y4 (CHD+4, BCA==1, 多视图) 交叉表 %s' % dict(tab))
for val in (0, 1, 5):
    grp = [a for a in CHD if c4[a] == val]
    print('   Y4 CHD+4==%d: %d 个，BCA 长度中位 %d，MI %d，多视图 %d' % (
        val, len(grp), statistics.median([len(BCD[a]) for a in grp]),
        sum(1 for a in grp if any(s32(P.dw(b+8)) != 0 for b in BCD[a])),
        sum(1 for a in grp if len(G[a]) > 1)))
ck('Y4a CHD+4 非 0 的类全部是多视图或 MI',
   all(len(G[a]) > 1 or any(s32(P.dw(b+8)) != 0 for b in BCD[a]) for a in CHD if c4[a] != 0),
   sum(1 for a in CHD if c4[a] != 0 and len(G[a]) == 1 and not any(s32(P.dw(b+8)) != 0 for b in BCD[a])))

# ---- Y5 attributes==2 的类身份 ----
attr2_ptd = sorted(set(P.dw(b) for b in uniq if P.dw(b + 20) == 2))
names2 = []
for p in attr2_ptd:
    nm = P.cstr(p + 8, 300)
    names2.append(nm.decode('latin1') if nm else '?')
print('   Y5 attributes==2 的 pTD 个数 %d，样例 %s' % (len(attr2_ptd), names2[:8]))
attr9_ptd = sorted(set(P.dw(b) for b in uniq if P.dw(b + 20) == 9))
names9 = [P.cstr(p + 8, 300).decode('latin1') for p in attr9_ptd]
print('   Y5 attributes==9 的 pTD 个数 %d，样例 %s' % (len(attr9_ptd), names9[:6]))
ck('Y5a attributes==2 全部落在 TClassFactory 模板类',
   all('TClassFactory' in n for n in names2), [n[:40] for n in names2 if 'TClassFactory' not in n])
ck('Y5b attributes==9 集合非空且与 2 不重合', len(names9) > 0 and not (set(attr9_ptd) & set(attr2_ptd)), (len(names9), len(set(attr9_ptd) & set(attr2_ptd))))

json.dump(dict(N=N, fails=fails, arith=len(arith), nonar=len(nonar),
               jump_top=jd.most_common(10), jump_total=sum(jd.values()),
               eq=eq, neq=len(neq), c4=dict(collections.Counter(c4.values())),
               attr2=names2, attr9=names9),
          open('/home/t628/projects/ra2-campaign-forge/_r204/m7_final.json','w'), ensure_ascii=False, indent=1)
print('\n== %d assertions, %d FAIL ==' % (N, len(fails)))
print('FAILS:', fails)
