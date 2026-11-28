#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R199 第十三刀：复算审计员 #499 的四条订正（§2.12 规则 D：审计结论必须主会话亲自复算）。

审计指出的四条：
 A1 M4 定性句「k>=14 继承率普遍 >=73%」不成立：k>=14 共 327 槽，其中 69 槽 <73%。
 A2 M11 打乱反控的分母不等结构（3513 vs 9853），+60pp 落差是口径伪影：
    等结构约束（nslot_d >= nslot_b）下 3262/10276 = 31.74%；按槽长精确配对 4480/8782 = 51.01%。
 A3 Q1 的「排除槽 0 后不匹配为 0 的配对数」有三个数（全槽 0 / 排除槽0 60 / 排除槽0..5 405），
    但含真空值（23 对 L==1、190 对 L<=6）；有效值 = 排除槽0 仅 L>=2 的 580 对 → 37；
    排除槽0..5 仅 L>=7 的 413 对 → 215。
 A4 Q2 分层稳健：槽0..5 968/3157 = 30.66% vs 槽6+ 5273/6696 = 78.75%（差 48.09pp）；
    但槽 6+ 内仍有 69/327 槽 <73%，第二层低谷为槽 8/10/11/12/13/25/27/31/34/35。
另验 A5 M2 附加：95 个 d2 的基类 pTD 全部没有被任何 COL 引用（0/95）。
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
        COL[base + 4 * i] = dict(mdisp=s32(w[i + 1]), ptd=w[i + 3], pchd=w[i + 4],
                                 name=nm.decode('latin1'))
VT = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL: VT[base + 4 * i] = P.dw(base + 4 * i - 4)
NS = {}
def nslot(vt):
    if vt in NS: return NS[vt]
    k = 0
    while True:
        if not in_text(P.dw(vt + 4 * k)): break
        k += 1
    NS[vt] = k; return k
MD = {vt: COL[VT[vt]]['mdisp'] for vt in VT}
PTD = {vt: COL[VT[vt]]['ptd'] for vt in VT}
MAIN = [vt for vt in VT if MD[vt] == 0]

CHD = {}
for c, cc in COL.items():
    v = cc['pchd']
    if v in CHD: continue
    CHD[v] = dict(n=P.dw(v + 8), arr=P.dw(v + 12))
BCDS = {}
for v, d in CHD.items():
    arr = d['arr']; lst = None
    if P.where(arr) not in ('None', 'other') and d['n'] is not None and 0 < d['n'] <= 64:
        lst = [P.dw(arr + 4 * j) for j in range(d['n'])]
        if any(x is None for x in lst): lst = None
    d['bcds'] = lst
    for b in (lst or []):
        BCDS[b] = dict(ptd=P.dw(b), ncb=P.dw(b + 4), mdisp=s32(P.dw(b + 8)), chd=v)
def direct_children(bcds, i):
    out = []; n = len(bcds); lim = i + BCDS[bcds[i]]['ncb']; j = i + 1
    while j <= lim and j < n:
        out.append(j); j = j + BCDS[bcds[j]]['ncb'] + 1
    return out
TD2VT = {PTD[vt]: vt for vt in MAIN}

pairs = []; d2 = []
for vt in MAIN:
    col = COL[VT[vt]]; ch = CHD.get(col['pchd'])
    if not ch or not ch['bcds']: continue
    kids = direct_children(ch['bcds'], 0)
    if not kids: continue
    z = [j for j in kids if BCDS[ch['bcds'][j]]['mdisp'] == 0]
    if len(z) != 1: continue
    bp = BCDS[ch['bcds'][z[0]]]['ptd']
    if bp in TD2VT: pairs.append((vt, TD2VT[bp]))
    else: d2.append(bp)
ck('B0a 603 对 / 95 个 d2', (len(pairs), len(d2)) == (603, 95), (len(pairs), len(d2)))

# A5：d2 的基类 pTD 是否被任何 COL 引用
colptd = set(c['ptd'] for c in COL.values())
ck('A5a 95 个 d2 基类 pTD 无任何 COL 引用（0/95）', sum(1 for b in d2 if b in colptd) == 0,
   sum(1 for b in d2 if b in colptd))

# A1：k>=14 的槽里有几个 <73%
den = collections.Counter(); mat = collections.Counter()
for vt_d, vt_b in pairs:
    L = min(nslot(vt_d), nslot(vt_b))
    for k in range(L):
        den[k] += 1
        if P.dw(vt_d + 4 * k) == P.dw(vt_b + 4 * k): mat[k] += 1
k14 = [k for k in den if k >= 14]
low14 = [k for k in k14 if mat[k] / den[k] < 0.73]
print('   A1 k>=14 槽数=%d，其中 <73%% 的=%d（%.1f%%）；den>=20 时 <73%% 的 %d/%d：%s'
      % (len(k14), len(low14), 100.0 * len(low14) / len(k14),
         len([k for k in k14 if den[k] >= 20 and mat[k] / den[k] < 0.73]),
         len([k for k in k14 if den[k] >= 20]),
         sorted([k for k in k14 if den[k] >= 20 and mat[k] / den[k] < 0.73])))
ck('A1a k>=14 里确有 <73% 的槽', len(low14) > 0, (len(low14), len(k14)))
ck('A1b k>=14 低槽数介于 60 与 80 之间', 60 <= len(low14) <= 80, len(low14))

# A2：等结构反控
def rate(pairs_):
    m = l = 0
    for vt_d, vt_b in pairs_:
        L = min(nslot(vt_d), nslot(vt_b))
        for k in range(L):
            l += 1
            if P.dw(vt_d + 4 * k) == P.dw(vt_b + 4 * k): m += 1
    return m, l
rm, rl = rate(pairs)
shuf = [(vt_d, MAIN[(i * 137 + 11) % len(MAIN)]) for i, (vt_d, _) in enumerate(pairs)]
sm, sl = rate(shuf)
print('   A2 真实 %d/%d=%.2f%%  原口径打乱 %d/%d=%.2f%%'
      % (rm, rl, 100.0 * rm / rl, sm, sl, 100.0 * sm / sl))
ck('A2a 打乱分母 != 真实分母', sl != rl, (sl, rl))
# 约束 nslot_d >= nslot_b
shuf2 = [(vt_d, MAIN[(i * 137 + 11) % len(MAIN)]) for i, (vt_d, _) in enumerate(pairs)
         if nslot(vt_d) >= nslot(MAIN[(i * 137 + 11) % len(MAIN)])]
s2m, s2l = rate(shuf2)
print('   A2b 约束 nslot_d>=nslot_b 的打乱 %d/%d=%.2f%%（对数 %d）'
      % (s2m, s2l, 100.0 * s2m / s2l, len(shuf2)))
ck('A2b 等结构打乱率在 25%~40%', 25 <= 100.0 * s2m / s2l <= 40, round(100.0 * s2m / s2l, 2))
# 按槽长精确配对：对每个派生，挑一个 nslot 相同（或最接近）的其它主表
byslot = collections.defaultdict(list)
for vt in MAIN: byslot[nslot(vt)].append(vt)
shuf3 = []
for vt_d, _ in pairs:
    cand = byslot.get(nslot(vt_d), [])
    cand = [v for v in cand if v != vt_d]
    shuf3.append((vt_d, cand[0] if cand else MAIN[(MAIN.index(vt_d) * 137 + 11) % len(MAIN)]))
s3m, s3l = rate(shuf3)
print('   A2c 同槽长精确配对 %d/%d=%.2f%%' % (s3m, s3l, 100.0 * s3m / s3l))
ck('A2c 同槽长配对率在 45%~58%', 45 <= 100.0 * s3m / s3l <= 58, round(100.0 * s3m / s3l, 2))

# A3：排除槽后的不匹配为 0 的配对数（含真空与有效值）
def count_zero(a, b_):
    tot = 0; vac = 0
    for vt_d, vt_b in pairs:
        L = min(nslot(vt_d), nslot(vt_b))
        if L <= a: vac += 1; continue
        ok = True
        for k in range(a, min(b_, L)):
            if P.dw(vt_d + 4 * k) != P.dw(vt_b + 4 * k): ok = False; break
        if ok: tot += 1
    return tot, vac
z0, _ = count_zero(0, 10 ** 6)
z1, v1 = count_zero(1, 10 ** 6)
z6, v6 = count_zero(6, 10 ** 6)
print('   A3 排除槽0 后不匹配=0 的对=%d（真空 %d 对，有效分母 %d）' % (z1, v1, 603 - v1))
print('        排除槽0..5 后=%d（真空 %d 对，有效分母 %d）' % (z6, v6, 603 - v6))
ck('A3a 全槽零不匹配配对 = 0', z0 == 0, z0)
ck('A3b 排除槽0 后为 60（含 23 对真空）', (z1, v1) == (60, 23), (z1, v1))
ck('A3c 排除槽0..5 后为 405（含 190 对真空）', (z6, v6) == (405, 190), (z6, v6))
ck('A3d 有效值 37 / 215', (z1 - v1, z6 - v6) == (37, 215), (z1 - v1, z6 - v6))

# A4：分层
def merge(klo, khi):
    m = l = 0
    for k in den:
        if klo <= k <= khi:
            m += mat[k]; l += den[k]
    return m, l
m1, l1 = merge(0, 5); m2, l2 = merge(6, 10 ** 6)
print('   A4 槽0..5 %d/%d=%.2f%%  槽6+ %d/%d=%.2f%%  差 %.2fpp'
      % (m1, l1, 100.0 * m1 / l1, m2, l2, 100.0 * m2 / l2, 100.0 * m2 / l2 - 100.0 * m1 / l1))
ck('A4a 两段合并率 30.66 / 78.75', (round(100.0 * m1 / l1, 2), round(100.0 * m2 / l2, 2)) == (30.66, 78.75),
   (round(100.0 * m1 / l1, 2), round(100.0 * m2 / l2, 2)))
lowt = sorted([k for k in den if k >= 6 and den[k] >= 100 and mat[k] / den[k] < 0.73])
print('   A4b 槽6+ 里 den>=100 且 <73%% 的槽: %s' % lowt)
ck('A4b 含槽 8/10/11/12/13', set([8, 10, 11, 12, 13]) <= set(lowt), lowt)

# 槽 0 匹配与「槽1+ 全匹配」是否互斥
both = 0; s0m = 0
for vt_d, vt_b in pairs:
    L = min(nslot(vt_d), nslot(vt_b))
    if L < 2: continue
    if P.dw(vt_d) == P.dw(vt_b):
        s0m += 1
        if all(P.dw(vt_d + 4 * k) == P.dw(vt_b + 4 * k) for k in range(1, L)): both += 1
print('   A3e 槽0 匹配 %d 对，其中槽1+ 全匹配 %d 对（交集）' % (s0m, both))
ck('A3e 交集 = 0', both == 0, both)

# M10：入口判据敏感性
bt = P.RAW[T['rawptr']:T['rawptr'] + (HI - LO)]
hits = [LO + i for i in range(len(bt) - 2) if bt[i:i + 3] == b'\x33\xc0\xc3']
for name, prevs in (('prev=90', {0x90}), ('{00,90,CC}', {0x00, 0x90, 0xCC}),
                    ('{90,C3,C2,CC}', {0x90, 0xC3, 0xC2, 0xCC}),
                    ('{90,C3,C2,CC,EB}', {0x90, 0xC3, 0xC2, 0xCC, 0xEB})):
    n = sum(1 for h in hits if h == LO or bt[h - LO - 1] in prevs)
    print('   M10 入口判据 %-16s => %d' % (name, n))
ck('M10 命中 249', len(hits) == 249, len(hits))

print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
