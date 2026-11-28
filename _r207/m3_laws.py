#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R207 m3：把 R207 发现钉成可证伪的三条结构律（全部实测）。
律 A：BCA 首项 == 本类自有 pTD（954/954？反控：随机置换）
律 B：物理 BCD 记录的身份 = 三元组 (pTD, mdisp, numContained)，1002 条两两不同（⇒ 5 个重复 pTD 组 14 条多余记录不是 COMDAT 折叠，而是同一基类在不同 mdisp 上的独立记录）
律 C：26 别名的语义 = 「下一类把前一物理类列为直接基类」（ptd_of[prev] ∈ BCA[next]），且反控「ptd_of[prev] ∈ BCA[prev]」为 0
附：numContained 语义试探（== 该 pTD 在本 BCA 中出现的次数？== 派生类数？）"""
import sys, struct, collections, json, random

sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P


def s32(v):
    return struct.unpack('<i', struct.pack('<I', v))[0]


COL = {}
for sn in ('.rdata', '.data'):
    s = P.B[sn]
    n = s['rawsize'] // 4
    base = s['lo']
    w = struct.unpack_from('<%dI' % n, P.RAW, s['rawptr'])
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
IDX = {a: i for i, a in enumerate(CHD)}
NB = {a: P.dw(a + 8) for a in CHD}
pBCA = {a: P.dw(a + 12) for a in CHD}
BCA = {a: [P.dw(pBCA[a] + 4 * j) for j in range(NB[a])] for a in CHD}
own_td = {}
for a in CHD:
    for c in G[a]:
        if c == a + 16:
            own_td[a] = COL[c]['pTD']


def tdname(td):
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


print('== 律 A：BCA 首项 == 自有 pTD ==')
lead = sum(1 for a in CHD if BCA[a] and BCA[a][0] == own_td[a])
ck('LA.1 BCA[0] == 自有 pTD', lead == 954, (lead, 954))
# 反控：BCA[0] 出现在 BCA[1:] 中的条目数（是否自身也可为基类，MI 镜像）
self_in_rest = sum(1 for a in CHD if BCA[a][0] in BCA[a][1:])
print(' 该类自身 pTD 又出现在自己 BCA 其余位置:', self_in_rest)
# 位置唯一性：BCA 中 own_td 出现次数
cnt = collections.Counter()
for a in CHD:
    cnt[a] = sum(1 for x in BCA[a] if x == own_td[a])
ck('LA.2 自有 pTD 在本 BCA 中恰出现 1 次（位置 0）', all(cnt[a] == 1 for a in CHD),
   collections.Counter(cnt.values()).most_common())
# 反控：随机 1000 个 .rdata dword 当作 pTD 时落在 BCA[0] 的比例
rnd = random.Random(207)
hits = 0
for _ in range(1000):
    v = P.dw(0x7fa4b0 + 4 * rnd.randrange((0x80efc4 - 0x7fa4b0) // 4))
    hits += sum(1 for a in CHD if BCA[a] and BCA[a][0] == v)
ck('LA.3 反控：区间内随机 dword 命 BCA[0] 的条数 ~0', hits < 5, hits)

print('== 律 B：BCD 记录身份 = (pTD, mdisp, numContained) ==')
phys = sorted(set(x for a in CHD for x in BCA[a]))
tri = {}
for b in phys:
    k = (P.dw(b), s32(P.dw(b + 8)), P.dw(b + 4))
    tri.setdefault(k, []).append(b)
ck('LB.1 1002 条物理 BCD 三元组两两不同（=1002 个键）', len(tri) == len(phys) == 1002, (len(tri), len(phys)))
# 逐字段反控：单字段去重
ck('LB.2 反控 单 pTD 去重=988（14 条多余）',
   len({P.dw(b) for b in phys}) == 988, len({P.dw(b) for b in phys}))
ck('LB.3 反控 (pTD,numContained) 去重数 > 988（mdisp 必要）',
   len({(P.dw(b), P.dw(b + 4)) for b in phys}) > 988,
   len({(P.dw(b), P.dw(b + 4)) for b in phys}))
# mdisp 分布
md = collections.Counter(s32(P.dw(b + 8)) for b in phys)
print(' mdisp 分布 top8:', md.most_common(8), ' 不同值数', len(md))
# 律 B 的推论：同一 (pTD,mdisp) 是否唯一（numContained 是否冗余）
ck('LB.4 (pTD,mdisp) 去重数 == 1002（numContained 冗余于身份）',
   len({(P.dw(b), s32(P.dw(b + 8))) for b in phys}) == 1002,
   len({(P.dw(b), s32(P.dw(b + 8))) for b in phys}))
# 5 个重复 pTD 组的 mdisp 差异
bytd = collections.defaultdict(list)
for b in phys:
    bytd[P.dw(b)].append(b)
dups = {t: v for t, v in bytd.items() if len(v) > 1}
print(' 重复 pTD 组（pTD → [(mdisp, 引用类数)]）：')
for t, v in sorted(dups.items(), key=lambda kv: -len(kv[1])):
    refs = collections.defaultdict(int)
    for b in v:
        for a in CHD:
            if b in BCA[a]:
                refs[b] += 1
    print('  %s %-34s %s' % (hex(t), tdname(t),
          [(s32(P.dw(b + 8)), refs[b]) for b in sorted(v)]))

print('== 律 C：26 别名 = 下一类列前一物理类为直接基类 ==')
al = [a for a in CHD[:-1] if any(P.dw(a + 36 + 4 * i) == own_td.get(a) for i in range(3))]
print(' 别名块 %d 个' % len(al))
ok = 0
detail = []
for a in al:
    nxt = CHD[IDX[a] + 1]
    if own_td[a] in BCA[nxt]:
        ok += 1
        if len(detail) < 5:
            detail.append((tdname(own_td[a]), tdname(own_td[nxt])))
ck('LC.1 别名块 ⇒ 下一类 BCA 含本条自有 pTD', ok == len(al), (ok, len(al), detail))
# 反控：非别名块中「下一类 BCA 含本条 pTD」的比例
base = [a for a in CHD[:-1] if a not in set(al)]
ctrl = sum(1 for a in base if own_td[a] in BCA[CHD[IDX[a] + 1]])
ck('LC.2 反控：非别名块该比例显著小', ctrl < 50, (ctrl, len(base)))
# 全量口径：954 类中「下一物理类以本类为基类」的总数（与别名 26 对比）
alln = sum(1 for a in CHD[:-1] if own_td[a] in BCA[CHD[IDX[a] + 1]])
print(' 全量：下一物理类以本类为基类 %d / 953（别名只捕获其中 %d）' % (alln, len(al)))

print('== numContained 语义试探 ==')
c1 = sum(1 for b in phys if P.dw(b + 4) == sum(1 for x in [b] if True))
# 候选 1：numContained == 有多少类的 BCA 含该 pTD（派生类数）
der = collections.Counter()
for a in CHD:
    for x in BCA[a][1:]:
        der[P.dw(x)] += 1
ck('LD.1 numContained != 派生类数', sum(1 for b in phys if P.dw(b + 4) == der[P.dw(b)]) < 200,
   sum(1 for b in phys if P.dw(b + 4) == der[P.dw(b)]))
# 候选 2：numContained == 持有块 BCA 长度 - 1
holder = {}
# 用「块内 B 项」重建持有块
blocks = {}
for i, a in enumerate(CHD[1:], 1):
    lo = CHD[i - 1] + 36
    p = pBCA[a]
    for pad0 in (0, 4):
        q = lo + pad0
        if q > p or (p - q) % 24:
            continue
        items = []
        for j in range((p - q) // 24):
            t = q + 24 * j
            if t in COL and COL[t]['pCHD'] == a:
                items.append((t, 'C'))
            elif P.where(P.dw(t)) == '.data' and (P.cstr(P.dw(t) + 8, 200) or b'').startswith(b'.?A') \
                    and P.dw(t + 12) == 0xffffffff:
                items.append((t, 'B'))
            else:
                items = None
                break
        if items is None:
            continue
        if [P.dw(p + 4 * j) for j in range(NB[a])] != BCA[a]:
            continue
        if a - (p + 4 * NB[a]) not in (4, 8):
            continue
        blocks[a] = dict(pad0=pad0, items=items, p=p, n=NB[a])
        break
for a, b in blocks.items():
    for t, tp in b['items']:
        if tp == 'B':
            holder[t] = a
ck('LD.2 块解析仍 953', len(blocks) == 953, len(blocks))
c2 = sum(1 for b in phys if b in holder and P.dw(b + 4) == NB[holder[b]] - 1)
ck('LD.3 numContained == 持有块的 numBaseClasses-1', c2 > 900, (c2, len(phys)))
c3 = sum(1 for b in phys if b in holder and P.dw(b + 4) == len(BCA[holder[b]]))
print(' numContained 取值分布:', collections.Counter(P.dw(b + 4) for b in phys).most_common(8))
# 候选 3：numContained == 引用该类（pTD）作为基类的直接派生类数（class 级）
ck('LD.4 numContained 与 mdisp 相关：mdisp==0 者 numContained 恒 0',
   all(P.dw(b + 4) == 0 for b in phys if s32(P.dw(b + 8)) == 0),
   collections.Counter(P.dw(b + 4) for b in phys if s32(P.dw(b + 8)) == 0).most_common())

print('== 汇总 ==')
out = dict(lead=lead, tri_uniq=len(tri), ptd_uniq=len({P.dw(b) for b in phys}),
           dup_groups=len(dups), alias=len(al), alias_next_ok=ok, ctrl_next=ctrl,
           alln=alln, nc_holder=c2, blocks=len(blocks))
open('/home/t628/projects/ra2-campaign-forge/_r207/m3_laws.json', 'w').write(
    json.dumps(dict(asserts=NA, fails=fails, facts=out), ensure_ascii=False, indent=1))
print(json.dumps(out, ensure_ascii=False))
print('== SUMMARY asserts=%d fails=%d ==' % (NA, len(fails)))
for f in fails:
    print('  FAIL:', f)
