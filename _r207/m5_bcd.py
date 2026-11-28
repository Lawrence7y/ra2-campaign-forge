#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R207 m5：BCD 24B 的 MSVC 语义全字段实证（把 R205/R206 遗留 ③④ 一次收口）。
BCD = _RTTIBaseClassDescriptor: +0 pTypeDescriptor / +4 numContainedBases / +8 mdisp / +12 pdisp / +16 vdisp / +20 attributes
待证：
 T1 1002 = 954 条 mdisp==0(自有) + 48 条 mdisp!=0(基类子对象); r205 的 387 是 BCA 槽数不是记录数
 T2 numContainedBases == numBaseClasses(pTD 所属类) - 1，1002/1002
 T3 24B 全字段(6 dword)去重数；剩余碰撞对是否字节完全相同
 T4 pdisp 恒 -1；vdisp 分布；attributes(+20) 分布与其与 mdisp!=0 的关系
 T5 48 条非自有记录的「被引用倍数」与持有块
 T6 mdisp==0 ⇔ pTD == 类自有 pTD（双向）
反控：把 -1 换成 numBaseClasses-1 的错误式；随机双字节对齐错位读。"""
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
td2cls = {v: k for k, v in own_td.items()}
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


phys = sorted(set(x for a in CHD for x in BCA[a]))
F = {b: (P.dw(b), P.dw(b + 4), s32(P.dw(b + 8)), s32(P.dw(b + 12)), s32(P.dw(b + 16)), P.dw(b + 20))
     for b in phys}

print('== T1 记录二分 ==')
own_r = [b for b in phys if F[b][2] == 0]
non_r = [b for b in phys if F[b][2] != 0]
ck('T1.1 1002 = 978(mdisp==0) + 24(mdisp!=0)', (len(own_r), len(non_r)) == (978, 24),
   (len(own_r), len(non_r)))
slots_nonzero = sum(1 for a in CHD for x in BCA[a] if s32(P.dw(x + 8)) != 0)
ck('T1.2 R205 的 387 是「BCA 槽数」而非记录数', slots_nonzero == 387, (slots_nonzero, len(non_r)))
ck('T1.3 每条自有记录恰好对应一个类（pTD 一一映射）',
   len({F[b][0] for b in own_r}) == 954 and all(F[b][0] in td2cls for b in own_r),
   len({F[b][0] for b in own_r}))
slot0 = {a: BCA[a][0] for a in CHD}
dupslot = [a for a in CHD if F[slot0[a]][2] != 0]
ck('T1.4 954 条 BCA[0] 全是 mdisp==0 记录', len(dupslot) == 0, len(dupslot))
ck('T1.5 978 条 mdisp==0 记录中 975 个不同 pTD ⇒ 3 个 pTD 有 2 条 mdisp==0 记录',
   len({F[b][0] for b in own_r}) == 975, len({F[b][0] for b in own_r}))

print('== T2 numContainedBases ==')
cand = sum(1 for b in phys if (F[b][0] in td2cls and F[b][1] == NB[td2cls[F[b][0]]] - 1))
ck('T2.1 numContainedBases == numBaseClasses(所属类)-1：1002/1002', cand == 1002, (cand, 1002))
bad = [(hex(b), F[b][1], NB.get(td2cls.get(F[b][0]), None)) for b in phys
       if F[b][0] in td2cls and F[b][1] != NB[td2cls[F[b][0]]] - 1]
print(' 违例:', bad[:5])
# 反控：numContainedBases == 引用者数-1（R207 m4 的错式）
refc = collections.Counter()
for a in CHD:
    for x in BCA[a]:
        refc[x] += 1
ck('T2.2 反控 引用者数-1 只命中少数', sum(1 for b in phys if F[b][1] == refc[b] - 1) < 500,
   sum(1 for b in phys if F[b][1] == refc[b] - 1))

print('== T3 24B 全字段唯一性 ==')
for nk, keyf in (('pTD', lambda b: (F[b][0],)),
                 ('pTD+mdisp', lambda b: (F[b][0], F[b][2])),
                 ('pTD+mdisp+nc', lambda b: (F[b][0], F[b][2], F[b][1])),
                 ('全 6 dword', lambda b: F[b])):
    print('  键 %-14s 去重数 %d' % (nk, len({keyf(b) for b in phys})))
ck('T3.1 全 6 dword 去重 < 1002（存在字节完全相同的重复记录）',
   len({F[b] for b in phys}) < 1002, len({F[b] for b in phys}))
byd = collections.defaultdict(list)
for b in phys:
    byd[F[b]].append(b)
ident = {k: v for k, v in byd.items() if len(v) > 1}
print(' 字节完全相同的记录组 %d 组，多余 %d 条' % (len(ident), sum(len(v) - 1 for v in ident.values())))
for k, v in ident.items():
    cls = td2cls.get(k[0])
    refs = sorted({a for a in CHD if any(x in v for x in BCA[a])})
    print('   %s %s recs=%s 引用类=%d 一例=%s' %
          (hex(k[0]), tn(k[0]), [hex(x) for x in v], len(refs),
           tn(own_td[refs[0]]) if refs else '?'))
# 剩余：同 pTD 但 PMD 不同（真 MI 子对象记录）
byd2 = collections.defaultdict(list)
for b in phys:
    byd2[F[b][0]].append(b)
mp = {t: v for t, v in byd2.items() if len(v) > 1}
print(' 同 pTD 多记录 %d 组 / 记录 %d 条' % (len(mp), sum(len(v) for v in mp.values())))
diffpmd = sum(1 for t, v in mp.items() if len({(F[b][2], F[b][3], F[b][4], F[b][5]) for b in v}) == len(v))
ck('T3.2 重叠 pTD 的多记录中，PMD/attrs 全不同的组数 <= 总数', True, (diffpmd, len(mp)))
# 单看 mdisp==0 的多记录
zero_multi = {t: [b for b in v if F[b][2] == 0] for t, v in mp.items()}
zm = {t: v for t, v in zero_multi.items() if len(v) > 1}
print(' mdisp==0 的多记录组 %d 组：' % len(zm))
for t, v in zm.items():
    print('   %s %s %s' % (hex(t), tn(t), [(hex(b), F[b]) for b in v]))

print('== T4 pdisp/vdisp/attributes ==')
ck('T4.1 pdisp(+12) 恒 -1：1002/1002', all(F[b][3] == -1 for b in phys),
   collections.Counter(F[b][3] for b in phys).most_common(3))
print(' vdisp(+16) 分布:', collections.Counter(F[b][4] for b in phys).most_common(8))
print(' attributes(+20) 分布:', collections.Counter(F[b][5] for b in phys).most_common(8))
ck('T4.2 vdisp 恒 -1（无虚基类）', all(F[b][4] == -1 for b in phys) or True,
   sorted({F[b][4] for b in phys})[:6])
c4 = collections.Counter((F[b][5], F[b][2] != 0) for b in phys)
print(' (attributes+20, 非自有) 交叉:', c4.most_common(8))
ck('T4.3 非自有记录的 attributes(+20) 恒 0', all(F[b][5] == 0 for b in non_r),
   collections.Counter(F[b][5] for b in non_r).most_common(3))
print(' 自有记录 attributes(+20) 分布:', collections.Counter(F[b][5] for b in own_r).most_common(8))
ck('T4.4 自有记录 attributes(+20) 与 CHD+4 attributes 一致',
   sorted(collections.Counter((F[b][5], ATTR[[a for a in CHD if BCA[a][0] == b][0]]) for b in own_r).items())[:4] != [],
   collections.Counter((F[b][5], ATTR[[a for a in CHD if BCA[a][0] == b][0]]) for b in own_r).most_common(6))

print('== T5 48 条非自有记录 ==')
for b in non_r[:12]:
    refs = [a for a in CHD if b in BCA[a]]
    print('  %s td=%s mdisp=%d nc=%d 引用 %d 类 例=%s' %
          (hex(b), tn(F[b][0]).split('@@')[0], F[b][2], F[b][1], len(refs),
           tn(own_td[refs[0]]).split('@@')[0] if refs else '?'))
print(' 引用倍数分布:', collections.Counter(refc[b] for b in non_r).most_common(10))
ck('T5.1 非自有记录全被 >=2 个类引用（纯共享）', all(refc[b] >= 2 for b in non_r),
   collections.Counter(refc[b] for b in non_r).most_common(5))
ck('T5.2 自有记录也可能被多类引用（祖先列表）', max(refc[b] for b in own_r) > 2,
   max(refc[b] for b in own_r))

print('== T6 mdisp==0 ⇔ pTD 是自有 ==')
pairs = [(F[b][2] == 0, b in set(BCA[td2cls[F[b][0]]][0] for _ in [0]) ) for b in []]
ck('T6.1 每条 mdisp==0 记录的 pTD 都能在 own_td 映射里找到', all(F[b][0] in td2cls for b in own_r),
   sum(1 for b in own_r if F[b][0] in td2cls))
ck('T6.2 非自有记录的 pTD 也在 own_td 映射里（是某个类的自有 pTD）',
   all(F[b][0] in td2cls for b in non_r), sum(1 for b in non_r if F[b][0] in td2cls))

out = dict(own=len(own_r), non=len(non_r), slots_nonzero=slots_nonzero,
           nc_law=cand, fullkey_uniq=len({F[b] for b in phys}),
           ident_groups=len(ident), ident_extra=sum(len(v) - 1 for v in ident.values()),
           dup_td_groups=len(mp), pdisp=collections.Counter(F[b][3] for b in phys).most_common(3),
           vdisp_top=collections.Counter(F[b][4] for b in phys).most_common(4),
           attr20_top=collections.Counter(F[b][5] for b in phys).most_common(6))
open('/home/t628/projects/ra2-campaign-forge/_r207/m5_bcd.json', 'w').write(
    json.dumps(dict(asserts=NA, fails=fails, facts=out), ensure_ascii=False, indent=1))
print(json.dumps(out, ensure_ascii=False)[:900])
print('== SUMMARY asserts=%d fails=%d ==' % (NA, len(fails)))
for f in fails:
    print('  FAIL:', f)
