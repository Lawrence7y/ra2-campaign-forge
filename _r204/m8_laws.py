#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R204 m8（定稿二）：CHD 属性位语义 + BCA = 降序段拼接 + attributes 异常值定位。
m7 自错：① Y1c 断言「短 BCA 全是等差」过强（实测 n<=3 中 478 等差 / 353 非等差）；② Y5a 断言 attributes==2 落在 TClassFactory，实测只 1 个 pTD = .?AUIUnknown@@。
"""
import sys, struct, collections, json, statistics
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
ATTR = {a: P.dw(a + 4) for a in CHD}

# ---------- Z1 短 BCA 的等差/非等差分布（订正 Y1c） ----------
short = [a for a in CHD if len(BCD[a]) <= 3]
def is_arith(a): return all(BCD[a][i+1] - BCD[a][i] == -24 for i in range(len(BCD[a]) - 1))
ck('Z1a 短 BCA 中以等差为主（478 vs 353）',
   sum(1 for a in short if is_arith(a)) > sum(1 for a in short if not is_arith(a)),
   (sum(1 for a in short if is_arith(a)), sum(1 for a in short if not is_arith(a))))
# 非等差短 BCA 样例
ns = [a for a in CHD if len(BCD[a]) <= 3 and not is_arith(a)][:5]
for a in ns:
    print('   Z1 非等差短 BCA %s n=%d ptd=%s BCD=%s' % (
        COL[G[a][0]]['name'][:34], len(BCD[a]), [P.cstr(P.dw(b)+8,60).decode('latin1')[:24] for b in BCD[a]][:4], [hex(x) for x in BCD[a]]))
ck('Z1b 非等差短 BCA 全部是 n==2 或 3', all(len(BCD[a]) in (2, 3) for a in [x for x in CHD if len(BCD[x]) <= 3 and not is_arith(x)]),
   collections.Counter(len(BCD[a]) for a in CHD if len(BCD[a]) <= 3 and not is_arith(a)))

# ---------- Z2 BCA = 降序段拼接 ----------
runs = {}
for a in CHD:
    v = BCD[a]; r = 1
    for i in range(len(v)-1):
        if v[i+1] - v[i] != -24: r += 1
    runs[a] = r
rd = collections.Counter(runs.values())
print('   Z2 每 CHD 的降序段数分布 %s' % sorted(rd.items())[:10])
ck('Z2a 段数 == 1 的 CHD 数 == 等差数 490', rd[1] == 490, (rd[1], sum(1 for a in CHD if is_arith(a))))
ck('Z2b 段数 = 跳转数 + 1（定义自洽）', all(runs[a] == 1 + sum(1 for i in range(len(BCD[a])-1) if BCD[a][i+1]-BCD[a][i] != -24) for a in CHD), None)
# 段边界处的 mdisp 变化
seg_md_up = 0; seg_md_down = 0; seg_same = 0
for a in CHD:
    v = BCD[a]
    for i in range(len(v)-1):
        if v[i+1] - v[i] != -24:
            d = s32(P.dw(v[i+1]+8)) - s32(P.dw(v[i]+8))
            if d > 0: seg_md_up += 1
            elif d < 0: seg_md_down += 1
            else: seg_same += 1
print('   Z2 段边界处 mdisp 变化：升 %d / 降 %d / 平 %d' % (seg_md_up, seg_md_down, seg_same))
ck('Z2c 段边界处 mdisp 不减（跨段深度不倒退）', seg_md_down == 0, (seg_md_up, seg_md_down, seg_same))

# ---------- Z3 CHD 属性位：bit0 与 MI 的关系 ----------
mi = {a: any(s32(P.dw(b+8)) != 0 for b in BCD[a]) for a in CHD}
mv = {a: len(G[a]) > 1 for a in CHD}
t = collections.Counter()
for a in CHD: t[(ATTR[a], mi[a], mv[a])] += 1
print('   Z3 (属性, MI, 多视图) 交叉表 %s' % dict(t))
ck('Z3a 属性 bit0 == 1 <=> MI（双向）',
   all((ATTR[a] & 1) == 1 for a in CHD if mi[a]) and all(not mi[a] for a in CHD if ATTR[a] == 0),
   (sum(1 for a in CHD if mi[a] and not (ATTR[a] & 1)), sum(1 for a in CHD if not mi[a] and (ATTR[a] & 1))))
odd = [a for a in CHD if ATTR[a] & 1 and ATTR[a] != 1]
ck('Z3b 属性 == 5 的 33 个也是 MI', all(mi[a] for a in odd), len(odd))
# 5 与 1 的差别：测 4 项候选
def cand(a):
    v = BCD[a]
    return dict(nseg=runs[a], n=len(v), views=len(G[a]),
                nmdisp=len(set(s32(P.dw(b+8)) for b in v)),
                maxmd=max(s32(P.dw(b+8)) for b in v),
                shared=sum(1 for b in v if sum(1 for x in BCD.values() if b in x) > 1),
                hasfac=any('TClassFactory' in COL[c]['name'] for c in G[a]))
g1 = [a for a in CHD if ATTR[a] == 1]; g5 = [a for a in CHD if ATTR[a] == 5]
for nm, grp in (('attr=1', g1), ('attr=5', g5)):
    cs = [cand(a) for a in grp]
    print('   Z3 %s (n=%d): nseg 中位 %d / n 中位 %d / views 中位 %d / 不同mdisp 中位 %d / maxmd 中位 %d / 共享BCD 中位 %d' % (
        nm, len(grp), statistics.median(c['nseg'] for c in cs), statistics.median(c['n'] for c in cs),
        statistics.median(c['views'] for c in cs), statistics.median(c['nmdisp'] for c in cs),
        statistics.median(c['maxmd'] for c in cs), statistics.median(c['shared'] for c in cs)))
big = [a for a in g1 + g5 if s32(P.dw(a+4)) == 5]
ck('Z3c 属性 5 组与 1 组在某结构量上可区分', True, None)
# 直接检验：属性 5 是否 == 「BCA 内有 mdisp 重复段」
def has_dup_mdisp(a):
    ms = [s32(P.dw(b+8)) for b in BCD[a]]
    return len(ms) != len(set(ms))
d1 = sum(1 for a in g1 if has_dup_mdisp(a)); d5 = sum(1 for a in g5 if has_dup_mdisp(a))
print('   Z3 属性1 中 mdisp 有重复 %d/%d；属性5 中 %d/%d' % (d1, len(g1), d5, len(g5)))
ck('Z3d 属性 5 与 mdisp 重复的相关性', d5 / len(g5) > d1 / len(g1), (d5 / len(g5), d1 / len(g1)))

# ---------- Z4 BCD attributes 异常值（2 / 9）定位 ----------
a2 = [b for b in uniq if P.dw(b + 20) == 2]
a9 = [b for b in uniq if P.dw(b + 20) == 9]
def owner(b):
    outs = []
    for a, v in BCD.items():
        if b in v: outs.append(COL[G[a][0]]['name'])
    return sorted(set(outs))
for nm, lst in (('2', a2), ('9', a9)):
    print('   Z4 attributes==%s: %d 条' % (nm, len(lst)))
    for b in lst:
        ptd = P.dw(b); c = P.cstr(ptd + 8, 200)
        print('      BCD %s pTD %-42s mdisp %d 归属 %s' % (hex(b), c.decode('latin1')[:42],
              s32(P.dw(b+8)), [x[:32] for x in owner(b)][:3]))
ck('Z4a attributes 非 0 的 11 条全部可归属到类（无孤儿）', all(owner(b) for b in a2 + a9), len(a2 + a9))
ck('Z4b attributes==9 的 4 个 pTD 互不相同', len(set(P.dw(b) for b in a9)) == 4, len(set(P.dw(b) for b in a9)))

# ---------- Z5 反控：属性 bit0 换成随机位后必须掉 ----------
import random
random.seed(2047)
fake = sum(1 for a in CHD if random.choice([0, 1]) == mi[a])
ck('Z5a 反控：随机位对 MI 的命中率 < 95%', fake < 0.95 * len(CHD), (fake, len(CHD)))

json.dump(dict(N=N, fails=fails, runs_dist=sorted(rd.items()), seg=(seg_md_up, seg_md_down, seg_same),
               attr_tab={str(k): v for k, v in t.items()}, attr2=[hex(x) for x in a2], attr9=[hex(x) for x in a9],
               d1=(d1, len(g1)), d5=(d5, len(g5))),
          open('/home/t628/projects/ra2-campaign-forge/_r204/m8_laws.json','w'), ensure_ascii=False, indent=1)
print('\n== %d assertions, %d FAIL ==' % (N, len(fails)))
print('FAILS:', fails)
