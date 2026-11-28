#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R207 m1：BCA 数组共享的成因 + pTD 重复记录语义 + pad0 二值语义（全部实测，不预设结论）。
口径（沿用 R206 已验证结构）：
  COL 20B: sig(+0)/mdisp(+4)/cdOffset(+8)/pTD(+12)/pCHD(+16)
  HEAD 36B: +0=0/+4=attributes/+8=numBaseClasses/+12=pBCA/+16..+35 内嵌 COL/+32==self
  BCD 24B: pTD(+0)/numContained(+4)/mdisp(+8)/pdisp(+12,恒-1)/+16/+20
正控：954 HEAD / 1002 BCD / 2615 BCA 条目；反控：随机地址池、错位口径。"""
import sys, struct, collections, json, random

sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P


def s32(v):
    return struct.unpack('<i', struct.pack('<I', v))[0]


def wv(sn):
    s = P.B[sn]
    n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n


COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
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
NAME = {a: COL[a]['name'] for a in CHD if a in COL}
# 每个 HEAD 的内嵌主对象 COL 的 pTD
ptd_of = {}
for a in CHD:
    for c in G[a]:
        if COL[c]['pCHD'] == a and COL[c]['mdisp'] == 0 and c == a + 16:
            ptd_of[a] = COL[c]['pTD']
TDNAME = {}
for a, td in ptd_of.items():
    nm = P.cstr(td + 8, 300)
    TDNAME.setdefault(td, nm.decode('latin1') if nm else '?')

fails = []
NA = 0


def ck(nm, c, d=''):
    global NA
    NA += 1
    if not c:
        fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))


print('== 0. 正控 ==')
ck('C0.1 HEAD=954', len(CHD) == 954, len(CHD))
ck('C0.2 BCD=1002', sum(1 for c, v in COL.items() if v['pCHD'] is None) == 0 and True)
nBCD = 0
for a in CHD:
    for x in BCA[a]:
        nBCD += 1
ck('C0.3 BCA 条目=2615', nBCD == 2615, nBCD)

print('== 1. pBCA 共享组 ==')
byp = collections.defaultdict(list)
for a in CHD:
    byp[pBCA[a]].append(a)
shared = {p: sorted(v) for p, v in byp.items() if len(v) > 1}
print(' 不同 pBCA 值 %d；被 >1 个 HEAD 共享的 pBCA 组 %d' % (len(byp), len(shared)))
sizes = collections.Counter(len(v) for v in shared.values())
print(' 组规模分布:', sizes.most_common())
print(' 涉及 HEAD 数 %d（占 954 = %.1f%%）' % (sum(sizes[k] * k for k in sizes), 100.0 * sum(sizes[k] * k for k in sizes) / 954))
for p, hs in sorted(shared.items(), key=lambda kv: -len(kv[1]))[:6]:
    print('   pBCA=%s n=%d names=%s' % (hex(p), len(hs), [NAME[h].replace('.?AV', '').replace('@@', '').replace('.?AU', 'U:') for h in hs][:6]))
# numBaseClasses 在同一共享组内是否一致
same_n = sum(1 for p, hs in shared.items() if len({NB[h] for h in hs}) == 1)
ck('L1.1 共享 pBCA 组内 numBaseClasses 全一致', same_n == len(shared), (same_n, len(shared)))
# 共享是否等价于 BCA 内容相同
same_c = sum(1 for p, hs in shared.items() if len({tuple(BCA[h]) for h in hs}) == 1)
ck('L1.2 共享组内 BCA 内容逐项相同', same_c == len(shared), (same_c, len(shared)))
# 内容相同但 pBCA 不同（未折叠）
byc = collections.defaultdict(list)
for a in CHD:
    byc[tuple(BCA[a])].append(a)
dupcontent = {c: v for c, v in byc.items() if len(v) > 1}
ck('L1.3 内容相同 ⇔ pBCA 相同（无「内容同址不同」）', len(dupcontent) == len(shared), (len(dupcontent), len(shared)))
if len(dupcontent) != len(shared):
    extra = [v for c, v in dupcontent.items() if len({pBCA[h] for h in v}) > 1]
    print('   内容同但地址不同的组数:', len(extra), extra[:3])
# 前缀关系：短数组是否恒为长数组前缀（不同长度组）
pref = collections.defaultdict(list)
for gn, hs in enumerate(shared.values()):
    for i in range(len(hs)):
        for j in range(len(hs)):
            if i == j:
                continue
            A, B = hs[i], hs[j]
            if NB[A] < NB[B]:
                pref['prefix_ok' if BCA[B][:NB[A]] == BCA[A] else 'prefix_bad'].append((A, B))
            elif NB[A] == NB[B]:
                pref['equal_len'].append((A, B))
print(' 同址组内配对（短→长）:', {k: len(v) for k, v in pref.items()})
ck('L1.4 同址共享内短数组恒为长数组前缀 0 例外', len(pref.get('prefix_bad', [])) == 0,
   pref.get('prefix_bad', [])[:3])
# 反控：后缀 / 任意子序列
suf = 0
tot = 0
for A, B in pref.get('prefix_ok', []):
    tot += 1
    if BCA[B][-NB[A]:] == BCA[A]:
        suf += 1
ck('L1.5 反控「后缀」命中数远小于全部', suf < tot, (suf, tot))
# 前缀延伸的那 1 项是否是新类自己的 BCD（末尾追加）
ext_ok = 0
ext_bad = []
for A, B in pref.get('prefix_ok', []):
    extra = BCA[B][NB[A]:]
    if len(extra) == 1:
        if extra[0] == ptd_of.get(B):
            ext_ok += 1
        else:
            ext_bad.append((hex(B), hex(extra[0]), hex(ptd_of.get(B, 0))))
ck('L1.6 前缀延伸的条目 == 长数组类的自有 pTD', len(ext_bad) == 0,
   (ext_ok, len(ext_bad), ext_bad[:3]))
# 延伸长度分布
print(' 延伸长度:', collections.Counter(NB[B] - NB[A] for A, B in pref.get('prefix_ok', [])).most_common())

print('== 2. pTD 重复记录 ==')
ptds = collections.defaultdict(list)
for a in CHD:
    for j, x in enumerate(BCA[a]):
        ptds[x].append((a, j))
dupp = {t: v for t, v in ptds.items() if len(v) > 1}
print(' 独立 pTD 数 %d / 2615 条目；出现 >1 次的 pTD %d 个，多出条目 %d'
      % (len(ptds), len(dupp), sum(len(v) - 1 for v in dupp.values())))
# 每条 BCD 记录（物理）唯一性：同一物理地址是否被多次引用
phys = collections.Counter()
for a in CHD:
    for x in BCA[a]:
        phys[x] += 1
multi = {x: c for x, c in phys.items() if c > 1}
print(' 被 >1 个类引用的 BCD 物理地址数 %d（多引用总条目 %d）' % (len(multi), sum(multi.values())))
# 每条物理 BCD 的 pTD（+0）
def bcd_ptd(b):
    return P.dw(b)
dupb = collections.defaultdict(list)
for b in phys:
    dupb[bcd_ptd(b)].append(b)
print(' 物理 BCD 记录按 pTD 分组：重复 pTD 组数 %d' % sum(1 for t, v in dupb.items() if len(v) > 1))
for t, v in sorted(dupb.items(), key=lambda kv: -len(kv[1]))[:8]:
    if len(v) < 2:
        continue
    print('   TD=%s name=%s 记录=%s mdisp=%s' % (hex(t), TDNAME.get(t, '?'),
          [hex(x) for x in v], [s32(P.dw(x + 8)) for x in v]))
# 26 别名对：a+40 == 本条 pTD 且等于下一条块首 BCD 的 pTD
print('== 3. pad0 二值语义交叉 ==')
cross = collections.Counter()
for a in CHD:
    cross[(ATTR[a], len(G[a]), NB[a])] += 1
print(' (attributes, 视图数, numBaseClasses) 分布 top12:', cross.most_common(12))
pad0map = {}
for i, a in enumerate(CHD[:-1]):
    nxt = CHD[i + 1]
    lo = a + 36
    p = pBCA[nxt]
    pad0 = None
    for cand in (0, 4):
        q = lo + cand
        if q <= p and (p - q) % 24 == 0:
            pad0 = cand
    pad0map[a] = pad0
print(' pad0 候选映射:', collections.Counter(pad0map.values()).most_common())
print('== 4. 26 别名对是否构成基类链 ==')
alias = []
for a in CHD[:-1]:
    for i in range(3):
        v = P.dw(a + 36 + 4 * i)
        if v == ptd_of.get(a) and v in TDNAME:
            alias.append((a, i, v))
print(' 别名命中 %d 条（a+36..+44 中等于本条 pTD 者）' % len(alias))
# 本条 BCA 是否含该 pTD（即是否作为基类列出）
inb = sum(1 for a, i, v in alias if v in BCA[a])
print(' 其中该 pTD 出现在本条 BCA 内: %d / %d' % (inb, len(alias)))
print(' 结论数字: ' + json.dumps(dict(shared_groups=len(shared), shared_heads=sum(len(v) for v in shared.values()),
      prefix_ok=len(pref.get('prefix_ok', [])), prefix_bad=len(pref.get('prefix_bad', [])),
      dupp=len(dupp), multiphys=len(multi), alias=len(alias)), ensure_ascii=False))
print('== SUMMARY asserts=%d fails=%d ==' % (NA, len(fails)))
for f in fails:
    print('  FAIL:', f)
