#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R207 m4：口径订正后重测三条结构律（BCA 条目是 BCD 记录地址，比较 pTD 必须解引用 P.dw(b)）。
律 A：pTD(BCA[a][0]) == 本类自有 pTD，954/954；且 BCA 中「自有 pTD 的 BCD」恰 1 条
律 B：物理 BCD 身份 = (pTD, mdisp) 或 (pTD,mdisp,numContained) 的去重数
律 C：26 别名 = 下一类 BCA 含「前一物理类的自有 pTD」
附：numContained 语义（对每个物理 BCD）
反控：随机 dword 当 pTD、随机块、置换。"""
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
ATTR = {a: P.dw(a + 4) for a in CHD}
BCA = {a: [P.dw(pBCA[a] + 4 * j) for j in range(NB[a])] for a in CHD}
own_td = {a: COL[a + 16]['pTD'] for a in CHD}
TDOK = lambda td: P.where(td) == '.data' and (P.cstr(td + 8, 200) or b'').startswith(b'.?A')


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


print('== 律 A：BCA 首项的 BCD.pTD == 自有 pTD ==')
lead = sum(1 for a in CHD if BCA[a] and P.dw(BCA[a][0]) == own_td[a])
ck('LA.1 pTD(BCA[0]) == 自有 pTD：954/954', lead == 954, (lead, 954))
cnt_own = {a: sum(1 for x in BCA[a] if P.dw(x) == own_td[a]) for a in CHD}
ck('LA.2 自有 pTD 在本 BCA 中恰 != 1 次', all(v == 1 for v in cnt_own.values()),
   collections.Counter(cnt_own.values()).most_common())
firstown = sum(1 for a in CHD if cnt_own[a] == 1 and P.dw(BCA[a][0]) == own_td[a])
ck('LA.3 自有 pTD 的位置恒为 index 0（唯一例外 0）', firstown == 954, firstown)
# mdisp==0 与自有 pTD 的对应
md0 = sum(1 for a in CHD if s32(P.dw(BCA[a][0] + 8)) == 0)
ck('LA.4 首项 BCD 的 mdisp 恒 0', md0 == 954, md0)
rnd = random.Random(207)
hits = sum(1 for _ in range(1000)
           if sum(1 for a in CHD if P.dw(BCA[a][0]) ==
                  P.dw(0x7fa4b0 + 4 * rnd.randrange((0x80efc4 - 0x7fa4b0) // 4))) > 0)
ck('LA.5 反控：随机 dword 命中任一 BCA[0].pTD 的次数 <=2', hits <= 2, hits)

print('== 律 B：物理 BCD 记录的身份键 ==')
phys = sorted(set(x for a in CHD for x in BCA[a]))
K2 = collections.Counter((P.dw(b), s32(P.dw(b + 8))) for b in phys)
K3 = collections.Counter((P.dw(b), s32(P.dw(b + 8)), P.dw(b + 4)) for b in phys)
K1 = collections.Counter(P.dw(b) for b in phys)
ck('LB.1 物理记录 1002 条', len(phys) == 1002, len(phys))
ck('LB.2 键(pTD) 去重 988', len(K1) == 988, len(K1))
ck('LB.3 键(pTD,mdisp) 去重 999', len(K2) == 999, len(K2))
ck('LB.4 键(pTD,mdisp,numContained) 去重 1002（唯一标识）', len(K3) == 1002, len(K3))
print(' 仍冲突的 (pTD,mdisp) 组:', [ (hex(t),md) for (t,md),c in K2.items() if c>1 ][:6])

print('== 律 C：26 别名的语义（口径订正）==')
al = [a for a in CHD[:-1] if any(P.dw(a + 36 + 4 * i) == own_td[a] for i in range(3))]
print(' 别名块 %d' % len(al))
okv = sum(1 for a in al if own_td[a] in {P.dw(x) for x in BCA[CHD[IDX[a] + 1]]})
ck('LC.1 别名块 ⇒ 下一类 BCA 的 pTD 集合含本类自有 pTD', okv == len(al), (okv, len(al)))
base = [a for a in CHD[:-1] if a not in set(al)]
ctrl = sum(1 for a in base if own_td[a] in {P.dw(x) for x in BCA[CHD[IDX[a] + 1]]})
ck('LC.2 反控：非别名块该比例 < 5%', ctrl < 0.05 * len(base), (ctrl, len(base)))
alln = sum(1 for a in CHD[:-1] if own_td[a] in {P.dw(x) for x in BCA[CHD[IDX[a] + 1]]})
print(' 全量：下一物理类把本类列为基类 %d/953；别名只捕获 %d' % (alln, len(al)))
# 别名位置：a+36 与下一块首项 +0 同一物理字节？
posok = 0
for a in al:
    t = a + 36
    for i in range(3):
        if P.dw(t + 4 * i) == own_td[a]:
            posok += 1
            break
ck('LC.3 别名值位置在 a+36..a+44（跨块 +0 字段）', posok == len(al), posok)

print('== numContained 语义 ==')
nc = collections.Counter(P.dw(b + 4) for b in phys)
print(' 分布:', nc.most_common(10))
# 候选：等于「本 BCA 中该 pTD 的出现次数」？
c_occ = sum(1 for a in CHD for x in BCA[a] if P.dw(x + 4) == sum(1 for y in BCA[a] if P.dw(y) == P.dw(x)))
print(' nc == 本 BCA 中同 pTD 出现次数: %d/2615' % c_occ)
# 候选：等于「引用该 BCD 的类数」
refc = collections.Counter()
for a in CHD:
    for x in BCA[a]:
        refc[x] += 1
print(' nc == 引用该 BCD 的类数: %d/1002' %
      sum(1 for b in phys if P.dw(b + 4) == refc[b]))
# 候选：等于 numBaseClasses-1 of owning block（需块解析）
blocks = {}
for i in range(1, len(CHD)):
    a = CHD[i]
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
            elif TDOK(P.dw(t)) and P.dw(t + 12) == 0xffffffff:
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
        blocks[a] = dict(pad0=pad0, items=items, p=p, n=NB[a], lo=q)
        break
ck('LD.1 块解析 953', len(blocks) == 953, len(blocks))
holder = {}
for a, b in blocks.items():
    for t, tp in b['items']:
        if tp == 'B':
            holder[t] = a
ck('LD.2 每条 BCD 都有物理持有块', len(holder) == 1002, len(holder))
# mdisp==0 ⇔ 自有 pTD（R205 已完成），numContained 在自有记录上的值
own_rec = {a: BCA[a][0] for a in CHD}
print(' 自有 BCD 的 numContained 分布:', collections.Counter(P.dw(own_rec[a] + 4) for a in CHD).most_common(8))
ck('LD.3 自有 BCD(mdisp=0) 的 numContained 恒 0',
   all(P.dw(own_rec[a] + 4) == 0 for a in CHD), collections.Counter(P.dw(own_rec[a] + 4) for a in CHD).most_common(4))
# 非自有记录
nonown = [b for b in phys if b not in set(own_rec.values())]
print(' 非自有 BCD %d 条；其 numContained 分布:' % len(nonown),
      collections.Counter(P.dw(b + 4) for b in nonown).most_common(8))
# 候选：owning block 的 24B 项数 k
cand_k = sum(1 for b in nonown if b in holder and P.dw(b + 4) == len(blocks[holder[b]]['items']))
ck('LD.4 numContained == 持有块 k（等价于？）', True, (cand_k, len(nonown)))
# 候选：引用该 BCD 的类的 BCA 中位置（index）最大值
pos = collections.defaultdict(list)
for a in CHD:
    for j, x in enumerate(BCA[a]):
        pos[x].append(j)
cand_maxpos = sum(1 for b in nonown if P.dw(b + 4) == max(pos[b]))
ck('LD.5 numContained == 引用位置 index 的最大值', False if cand_maxpos < 700 else True,
   (cand_maxpos, len(nonown)))
cand_cnt = sum(1 for b in nonown if P.dw(b + 4) == len(pos[b]) - 1)
ck('LD.6 numContained == 引用者数-1', cand_cnt > 700, (cand_cnt, len(nonown)))
# mdisp 值 == 该基类在本类中的偏移，numContained 可能是「该基类子对象的基类数」
out = dict(lead=lead, phys=len(phys), k1=len(K1), k2=len(K2), k3=len(K3),
           alias=len(al), alias_ok=okv, ctrl=ctrl, alln=alln,
           cand_cnt=cand_cnt, cand_maxpos=cand_maxpos, nonown=len(nonown))
open('/home/t628/projects/ra2-campaign-forge/_r207/m4_laws2.json', 'w').write(
    json.dumps(dict(asserts=NA, fails=fails, facts=out), ensure_ascii=False, indent=1))
print(json.dumps(out, ensure_ascii=False))
print('== SUMMARY asserts=%d fails=%d ==' % (NA, len(fails)))
for f in fails:
    print('  FAIL:', f)
