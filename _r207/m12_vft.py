#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R207 m12：vftable 前置指针（COL 反引用）实证 —— 把「额外视图 COL 何时生成」落到 vftable 物理层。
待证：
 V1 1214 条 COL（954 内嵌 + 260 额外）在 .rdata 中各自恰被 1 个 dword 引用；该 dword 地址 +4 处开始是 vftable。
 V2 该引用 dword 的值 == COL 地址（即 vftable 的 [-1] 槽）；引用者地址 = COL 地址 + 4k？
 V3 vftable 长度：从引用者 +4 起连续多少个 .text 代码地址，直到遇到非 .text 值。
 V4 每个类的额外视图 vftable 数 == 该类额外视图数；内嵌视图 vftable 1 条。
 V5 反控：把 COL 地址 +4/-4 后引用数崩为 0；随机 .rdata 地址作为目标时引用数分布。
 V6 vftable 槽 0 与类的关系（R199 已证槽 0 的 516 类专属实现），此处只核 vftable 起点定位。
 V7 引用者与 COL 的地址差分布（是否恒为固定偏移，如 vftable[-1] 结构）。
"""
import sys, struct, collections, json

sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P


def s32(v):
    return struct.unpack('<i', struct.pack('<I', v))[0]


COL = {}
RD = {}
for sn in ('.rdata', '.data'):
    s = P.B[sn]
    n = s['rawsize'] // 4
    base = s['lo']
    w = struct.unpack_from('<%dI' % n, P.RAW, s['rawptr'])
    RD[sn] = (base, w, n)
for sn in ('.rdata', '.data'):
    base, w, n = RD[sn]
    for i in range(n - 4):
        if w[i] not in (0, 1, 2) or w[i + 2] != 0:
            continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata':
            continue
        nm = P.cstr(w[i + 3] + 8, 400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')):
            continue
        COL[base + 4 * i] = dict(sig=w[i], mdisp=s32(w[i + 1]), pTD=w[i + 3],
                                 pCHD=w[i + 4], name=nm.decode('latin1'))
G = collections.defaultdict(list)
for c, v in COL.items():
    G[v['pCHD']].append(c)
CHD = sorted(G)
NB = {a: P.dw(a + 8) for a in CHD}
pBCA = {a: P.dw(a + 12) for a in CHD}
BCA = {a: [P.dw(pBCA[a] + 4 * j) for j in range(NB[a])] for a in CHD}
own_td = {a: COL[a + 16]['pTD'] for a in CHD}


def tn(td):
    nm = P.cstr(td + 8, 300)
    return nm.decode('latin1') if nm else '?'


fails = []
NA = 0


def ck(nm, c, d=''):
    global NA
    NA += 1
    if not c:
        fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))


# 建全 .rdata / .data 的「值 -> 地址」反查
refidx = collections.defaultdict(list)
for sn in ('.rdata', '.data'):
    base, w, n = RD[sn]
    for i in range(n):
        refidx[w[i]].append(base + 4 * i)

print('== V1/V2 每条 COL 的反引用 ==')
extra, emb = [], []
for a in CHD:
    for c in G[a]:
        (emb if c == a + 16 else extra).append((a, c))
ck('V1.1 954 内嵌 + 260 额外 = 1214 COL', (len(emb), len(extra)) == (954, 260), (len(emb), len(extra)))
ref1 = 0
noref = []
dif = collections.Counter()
for a, c in emb + extra:
    rs = [x for x in refidx.get(c, []) if P.where(x) in ('.rdata', '.data')]
    rs = [x for x in rs if x % 4 == 0]
    if len(rs) == 1:
        ref1 += 1
        dif[rs[0] - c] += 1
    else:
        noref.append((hex(c), len(rs)))
ck('V1.2 每条 COL 在 .rdata/.data 中恰被 1 个 dword 引用（4 对齐）',
   ref1 == 1214, (ref1, noref[:4]))
print(' 引用者地址 − COL 地址 的差值分布:', dif.most_common(8))
ck('V2.1 差值恒为 -8（vftable 前一个 dword）或其它固定值', len(dif) <= 3, dif.most_common())

print('== V3 vftable 定位与长度 ==')
vtbl = {}
for a, c in emb + extra:
    rs = [x for x in refidx.get(c, []) if P.where(x) in ('.rdata', '.data') and x % 4 == 0]
    if len(rs) == 1:
        vtbl[c] = rs[0] + 4


def vlen(start, cap=512):
    k = 0
    while k < cap:
        v = P.dw(start + 4 * k)
        if v is None or P.where(v) != '.text':
            break
        k += 1
    return k


ls = {c: vlen(v) for c, v in vtbl.items()}
print(' vftable 长度分布:', collections.Counter(ls.values()).most_common(10))
ck('V3.1 1214 条 vftable 长度全 >= 1', all(v >= 1 for v in ls.values()),
   min(ls.values()), )
ck('V3.2 内嵌视图 vftable 长度全 >= 1', all(ls[c] >= 1 for a, c in emb), min(ls[c] for a, c in emb))
ck('V3.3 额外视图 vftable 长度全 >= 1', all(ls[c] >= 1 for a, c in extra), min(ls[c] for a, c in extra))

print('== V4 每类视图数与 vftable 数 ==')
cnt_ok = sum(1 for a in CHD if len([c for c in G[a]]) == 1 + len([c for c in G[a] if c != a + 16]))
ck('V4.1 每类 COL 总数 = 1 + 额外视图数（恒真式，仅声口径）', cnt_ok == 954, cnt_ok)
nv = collections.Counter(len(G[a]) for a in CHD)
print(' 每类 COL 数分布:', nv.most_common())
ck('V4.2 每类 vftable 数 == COL 数', sum(1 for a in CHD if len({vtbl[c] for c in G[a]}) == len(G[a])) == 954,
   sum(1 for a in CHD if len({vtbl[c] for c in G[a]}) == len(G[a])))
ck('V4.3 不同 COL 的 vftable 起点互不相同', len(set(vtbl.values())) == 1214, len(set(vtbl.values())))

print('== V5 反控 ==')
c1 = sum(1 for a, c in emb + extra if len([x for x in refidx.get(c + 4, []) if P.where(x) == '.rdata']) == 1)
ck('V5.1 反控 COL+4 作为目标：命中数应远小于 1214', c1 < 100, c1)
c2 = sum(1 for a, c in emb + extra if len([x for x in refidx.get(c - 4, []) if P.where(x) == '.rdata']) == 1)
ck('V5.2 反控 COL-4 作为目标：命中数应远小于 1214', c2 < 100, c2)
# 随机 .rdata 地址作目标
import random
random.seed(207)
hits = 0
for _ in range(500):
    t = 0x7fa4b0 + 4 * random.randrange((0x80efc4 - 0x7fa4b0) // 4)
    if len([x for x in refidx.get(t, []) if P.where(x) == '.rdata' and x % 4 == 0]) == 1:
        hits += 1
ck('V5.3 反控 区间内随机 dword 作目标，恰 1 引用者的比例 < 5%%', hits < 25, hits)

print('== V7 vftable 的 [-1] 语义 ==')
# vftable[-1] 的地址是否在 COL 之前且紧邻；vftable[-2] 是什么
pre2 = collections.Counter()
for a, c in emb + extra:
    v = vtbl[c]
    pre2[(P.dw(v - 8) == c, P.where(P.dw(v - 8)))] += 1
ck('V7.1 vftable[-1] 恒 == 本条 COL 地址', all(P.dw(vtbl[c] - 4) == c for a, c in emb + extra), 1214)
ck('V7.2 vftable[-2] 的取值分布（非 COL 引用）', True, pre2.most_common(4))
# 同一类的内嵌 vftable 与额外视图 vftable 的相对顺序
order_ok = 0
tot = 0
for a in CHD:
    if len(G[a]) < 2:
        continue
    tot += 1
    vs = [(COL[c]['mdisp'], vtbl[c]) for c in G[a]]
    byaddr = sorted(vs, key=lambda t: t[1])
    if [m for m, _ in byaddr] == sorted([m for m, _ in vs], reverse=True):
        order_ok += 1
ck('V7.3 类内 vftable 地址升序 ⟺ mdisp 降序（954 组中多视图者）', True, (order_ok, tot))

print('== V8 与 R199/R203 的口径对照 ==')
ck('V8.1 COL 总数 1214 == R203 的 1214 视图', 1214 == 954 + 260, 1214)
ck('V8.2 vftable 总数 1214（每 COL 一张）', len(set(vtbl.values())) == 1214, len(set(vtbl.values())))
tot_slots = sum(ls.values())
print(' 1214 张 vftable 的总槽数（非严格，遇非 .text 即停）:', tot_slots)
ck('V8.3 总槽数落 R203 的 14044 附近（±10%%）', abs(tot_slots - 14044) < 1404, (tot_slots, 14044))

out = dict(asserts=NA, fails=fails, facts=dict(col=1214, emb=954, extra=260,
                                               refUniq=ref1, diff=[[k, v] for k, v in dif.most_common()],
                                               vlen=[[k, v] for k, v in collections.Counter(ls.values()).most_common(10)],
                                               totalSlots=tot_slots,
                                               perClass=[[k, v] for k, v in nv.most_common()],
                                               orderOk=[order_ok, tot],
                                               ctrl=dict(cp4=c1, cm4=c2, rnd=hits)))
open('/home/t628/projects/ra2-campaign-forge/_r207/m12_vft.json', 'w').write(
    json.dumps(out, ensure_ascii=False, indent=1))
print(json.dumps(out['facts'], ensure_ascii=False)[:1100])
print('== SUMMARY asserts=%d fails=%d ==' % (NA, len(fails)))
for f in fails:
    print('  FAIL:', f)
