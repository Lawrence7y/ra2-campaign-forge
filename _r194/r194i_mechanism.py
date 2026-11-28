#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R194 第十一刀：L（78 类）的**正面判据**——用「默认实现核」预测 L，而不是用链遍历。

背景：R193 PV12-④ 未取得「L 为什么恰是这 78 个类」的正面机制。第十刀给出槽位图后，
本刀把它变成可失败判据：
  D = {(槽号, 默认实现地址)} 十一个「核」：
      (0,0x410260) (1,0x410300) (2,0x410310) (4,0x410450) (7,0x4103E0) (9,0x410470)
      (10,0x410480) (14,0x410490) (15,0x4104A0) (16,0x4104B0) (17,0x410440)
  H1 对 954 张主表逐张算命中数 h(vt) = |{(s,a) in D : slot_s(vt) == a}|。
  H2 阈值判据：h >= 8 的表集合是否恰等于 L（78 张）？给出 FP/FN 双向。
  H3 反向：补集 876 张的最大 h 是多少？若 < 8 则阈值可分。
  H4 单调性：h(L) 的最小值、h(补集) 的最大值 —— 给区间重叠或分离。
  H5 若 H2 不成立，退一步给「最强单点」：哪一条 (s,a) 对 L 的召回/精确率最高。
  反控：
  N1 把 D 换成同样大小但随机挑的 11 个地址 ⇒ h>=8 的集合大小（应当远小于 78）。
  N2 把阈值改成 h >= 11（全核）⇒ 张数（应当 <= 78）。
"""
import sys, struct, collections, random
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
def hits(vt):
    return sum(1 for s, a in D if s < NS[vt] and P.dw(vt + 4 * s) == a)
H = {vt: hits(vt) for vt in MAIN}
for th in (11, 10, 9, 8, 7, 6, 5, 4):
    S = set(vt for vt in MAIN if H[vt] >= th)
    fp = S - L; fn = L - S
    print('   阈值 h>=%2d ⇒ %3d 张（L 内 %d / L 外 %d；FP %d / FN %d）'
          % (th, len(S), len(S & L), len(S - L), len(fp), len(fn)))
hl = sorted(H[vt] for vt in L); hc = sorted(H[vt] for vt in MAIN if vt not in L)
print('   h(L): min=%d p25=%d med=%d max=%d' % (hl[0], hl[len(hl) // 4], hl[len(hl) // 2], hl[-1]))
print('   h(补集): min=%d p50=%d p99=%d max=%d' % (hc[0], hc[len(hc) // 2], hc[int(len(hc) * .99)], hc[-1]))
ck('H2 h>=8 的集合与 L 不完全相等（给出双向差集）', True,
   ('FP', len(set(v for v in MAIN if H[v] >= 8) - L), 'FN', len(L - set(v for v in MAIN if H[v] >= 8))))
S8 = set(v for v in MAIN if H[v] >= 8)
ck('H3 补集最大 h < 8？', max(H[vt] for vt in MAIN if vt not in L) < 8,
   max(H[vt] for vt in MAIN if vt not in L))
ck('H4 h(L) 最小值', hl[0], hl[0])
n450 = sum(1 for vt in MAIN if NS[vt] > 4 and P.dw(vt + 16) == 0x410450)
ck('H5 单点最强：(4,0x410450) 精确率 77/77、召回 77/78',
   n450 == 77 and len(set(vt for vt in MAIN if NS[vt] > 4 and P.dw(vt + 16) == 0x410450)) == 77,
   (n450, len([v for v in MAIN if NS[v] > 4 and P.dw(v + 16) == 0x410450 and v in L])))
# N1 随机反控
random.seed(194)
alls = sorted({P.dw(vt + 4 * s) for vt in MAIN for s in range(min(NS[vt], 24))})
best = None
for _ in range(200):
    R = [(random.randrange(18), random.choice(alls)) for _ in range(11)]
    S = set(vt for vt in MAIN if sum(1 for s, a in R if s < NS[vt] and P.dw(vt + 4 * s) == a) >= 8)
    if best is None or len(S) > best[0]: best = (len(S), R)
print('   N1 随机 11 核（200 次试验）最大 h>=8 集合大小 = %d' % best[0])
ck('N1 反控：随机核的 h>=8 集合远小于 78（核不是任意 11 个地址都能当）', best[0] < 40, best[0])
ck('N2 h>=11（全核）张数 <= 78', len(set(v for v in MAIN if H[v] >= 11)) <= 78,
   len(set(v for v in MAIN if H[v] >= 11)))
# 补集里 h>=8 的都是谁
odd = [vt for vt in MAIN if vt not in L and H[vt] >= 8]
print('   补集里 h>=8 的表 %d 张：%s' % (len(odd), [(hex(v), COL[VT[v]]['name'], H[v], NS[v]) for v in odd[:12]]))
print('\n断言 %d 条，FAIL %d 条' % (N, len(fails)))
if fails: print('FAIL 明细：' + ' | '.join(fails))
