#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R194 第十二刀：核 D 的充分性/必要性双向判据 + 未命中表的身份（收口第十一刀的 FN 尾巴）。

  K1 阈值扫描 h>=1..11，逐档给 TP/FP/FN。
  K2 h>=1 ⇒ 集合与 L 的关系（若 h>=1 就有 FP>0，则核只对 L 是必要条件而非充分条件）。
  K3 FN 逐个点名：h < 5 的 L 表是哪些类（按 COL 修饰名 + 槽数 + 逐核命中位图）。
  K4 反控：把 D 的 11 项逐项剔除，测「去掉某一项后 h>=1 的 FP 与 FN」，找出哪几项是真正的判别项。
  K5 补集 876 张在 11 个核上的命中分布（应当是全 0，已在第十一刀给出 max=0，此处给完整直方图）。
"""
import sys, struct, collections
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']
def in_text(x): return x is not None and LO <= x < HI
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n
COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1) or w[i + 2] != 0: continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
        nm = P.cstr(w[i + 3] + 8, 200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base + 4 * i] = dict(mdisp=w[i + 1], pchd=w[i + 4], name=nm.decode('latin1'))
VT = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL: VT[base + 4 * i] = P.dw(base + 4 * i - 4)
def nslot(vt):
    k = 0
    while in_text(P.dw(vt + 4 * k)): k += 1
    return k
NS = {vt: nslot(vt) for vt in VT}
MAIN = [vt for vt in VT if COL[VT[vt]]['mdisp'] == 0]
def chain(colva):
    c = COL[colva]; n = P.dw(c['pchd'] + 8); arr = P.dw(c['pchd'] + 12); out = []
    for j in range(n):
        b = P.dw(arr + 4 * j)
        if b is None or P.where(b) in ('None', 'other'): continue
        ptd = P.dw(b)
        if ptd is None: continue
        nm = P.cstr(ptd + 8, 160)
        out.append(nm.decode('latin1') if nm else None)
    return out
L = set(vt for vt in MAIN if '.?AVAbstractClass@@' in chain(VT[vt]))
D = [(0, 0x410260), (1, 0x410300), (2, 0x410310), (4, 0x410450), (7, 0x4103E0),
     (9, 0x410470), (10, 0x410480), (14, 0x410490), (15, 0x4104A0), (16, 0x4104B0),
     (17, 0x410440)]
def hit(vt, s, a): return s < NS[vt] and P.dw(vt + 4 * s) == a
def H(vt, D=D): return sum(1 for s, a in D if hit(vt, s, a))
print('   K1 阈值扫描（954 张主表；L=78）：')
for th in range(11, 0, -1):
    S = set(vt for vt in MAIN if H(vt) >= th)
    print('     h>=%2d  %3d 张  TP %3d  FP %2d  FN %2d' % (th, len(S), len(S & L), len(S - L), len(L - S)))
S1 = set(vt for vt in MAIN if H(vt) >= 1)
ck('K2 h>=1 ⇒ 集合被 L 完全包含（FP=0）：核是 L 的**必要**条件，可在 954 张主表上零误报筛出',
   not (S1 - L), (len(S1), len(S1 & L), len(S1 - L)))
ck('K2b 但 h>=1 不是充分条件：FN = %d 张（核不覆盖全部 L）' % len(L - S1), len(L - S1) > 0, len(L - S1))
FN = sorted(L - S1)
print('   K3 未命中任何核的 L 表 %d 张：' % len(FN))
for vt in FN:
    print('     %08X %-34s 槽%3d 链=%s' % (vt, COL[VT[vt]]['name'], NS[vt],
          ','.join(x.replace('.?AV', '').replace('@@', '') for x in chain(VT[vt])[-3:])))
ck('K3a 未命中核的表全是槽数 < 18 的类（核涉及的槽号 0..17 越界）',
   all(NS[vt] < 18 for vt in FN), [(hex(v), NS[v]) for v in FN])
print('   K4 逐项剔除（h>=1 口径下的 FP/FN 变化）：')
for i, (s, a) in enumerate(D):
    Dm = D[:i] + D[i + 1:]
    Sm = set(vt for vt in MAIN if H(vt, Dm) >= 1)
    print('     剔除 (%2d,%s) ⇒ 命中 %3d 张  FP %2d  FN %2d'
          % (s, hex(a), len(Sm), len(Sm - L), len(L - Sm)))
    if len(Sm - L) > 0:
        print('        FP 样例：%s' % [(hex(v), COL[VT[v]]['name']) for v in sorted(Sm - L)[:5]])
c = collections.Counter(H(vt) for vt in MAIN if vt not in L)
print('   K5 补集 876 张的 h 直方图：%s' % dict(sorted(c.items())))
ck('K5a 补集在 11 核上全 0（鉴别力来自这 11 个默认实现的组合，而非任何单个地址）',
   dict(c) == {0: 876}, dict(sorted(c.items())))
c2 = collections.Counter(H(vt) for vt in L)
print('   K5b L 的 h 直方图：%s' % dict(sorted(c2.items())))
print('\n断言 %d 条，FAIL %d 条' % (N, len(fails)))
if fails: print('FAIL 明细：' + ' | '.join(fails))
