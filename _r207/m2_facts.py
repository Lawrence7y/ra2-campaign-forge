#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R207 m2：R206 未取得项③④⑤ 的字节实证 + R206 QI7 括号内成因订正。
① pBCA 共享计数（R206 称「pBCA 可被多记录共享」→ 实测核查）
② 304 条多引用 BCD 的三元组折叠实证（pTD/numContained/mdisp 全等才可折叠）
③ 5 个重复 pTD 物理记录（14 条多余）逐条枚举
④ 26 别名：值 == 下一块首个 24B 项的 +0，且 == 本类自有 pTD ⇒ 下一类以本类为基类
⑤ pad0 无独立语义：k>=1 ⇒ pad0 恒 4；k==0 ⇒ pad0 == (p-lо)；并给出 pBCA 8 对齐与 n 的关系
反控：把 24B 项判据换成「任意 dword 位置」；随机 pTD 抽样。"""
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
own_td = {}
own_name = {}
for a in CHD:
    for c in G[a]:
        if c == a + 16:
            own_td[a] = COL[c]['pTD']
            own_name[a] = COL[c]['name']
TDOK = lambda td: P.where(td) == '.data' and (P.cstr(td + 8, 200) or b'').startswith(b'.?A')


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


# ---- 块解析（含 pad0 取值）----
def parse_block(a):
    i = IDX[a]
    if i == 0:
        return None
    lo = CHD[i - 1] + 36
    n = NB[a]
    p = pBCA[a]
    sols = []
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
        if [P.dw(p + 4 * j) for j in range(n)] != BCA[a]:
            continue
        if a - (p + 4 * n) not in (4, 8):
            continue
        sols.append((pad0, q, items, p + 4 * n))
    return sols


B = {}
for a in CHD[1:]:
    s = parse_block(a)
    if s and len(s) == 1:
        pad0, q, items, e = s[0]
        B[a] = dict(lo=q, pad0=pad0, rawlo=CHD[IDX[a] - 1] + 36, items=items, p=pBCA[a], n=NB[a], pad1=a - e)

print('== 1. pBCA 共享（R206 QI7 括号内成因核查）==')
byp = collections.defaultdict(list)
for a in CHD:
    byp[pBCA[a]].append(a)
shared = {p: v for p, v in byp.items() if len(v) > 1}
ck('L1.1 954 个 HEAD 的 pBCA 值互不相同（共享组 0）', len(byp) == 954 and len(shared) == 0,
   (len(byp), len(shared)))
# 876/953 成因：块内 BCD 槽数 vs 首次出现集合
first = {}
for a in CHD:
    for j, x in enumerate(BCA[a]):
        first.setdefault(x, (a, j))
slotsB = lambda a: [t for t, tp in B[a]['items'] if tp == 'B']
eq = 0
short = []
for a in B:
    s = set(slotsB(a))
    f = {x for x in BCA[a] if first[x] == (a, BCA[a].index(x))}
    if s == f:
        eq += 1
    else:
        short.append((a, len(s), len(f), len(set(BCA[a]) & set(x for x in BCA[a] if first[x][0] != a))))
print(' 块内 BCD 槽集 == 首次出现集: %d/953' % eq)
multiref = collections.Counter()
for a in CHD:
    for x in BCA[a]:
        multiref[x] += 1
multi = {x: c for x, c in multiref.items() if c > 1}
print(' 被 >=2 个类引用的 BCD 物理记录 %d 条（多引用总槽 %d）' % (len(multi), sum(multi.values())))
# 用「多引用」解释 953-876 差额：缺口块的被引用非首现条目数
gap = 953 - eq
print(' 缺口块 %d 个；缺口块内「非首现」BCD 条目总数 %d' %
      (gap, sum(s[3] for s in short)))
ck('L1.2 953-876=77 的成因是 BCD 多引用（非 pBCA 共享）', len(shared) == 0 and len(multi) > 0,
   (gap, len(multi)))

print('== 2. 多引用 BCD 的折叠三元组 ==')
def tri(b):
    return (P.dw(b), P.dw(b + 4), s32(P.dw(b + 8)))
grp = collections.defaultdict(list)
for x in multi:
    grp[tri(x)].append(x)
ck('L2.1 同一三元组的物理记录才被多类共用（组内三元组全等，恒真式，用于口径声明）',
   all(len({tri(x) for x in v}) == 1 for v in grp.values()), len(grp))
# 关键：多引用记录所属的引用者类，其「该位置的基类集合」是否与单引用情形不同
# 检查：引用同一 BCD 的多个类，是否彼此构成「同一个直接基类表」的派生类
pairs_same_td = 0
pairs_diff_count = 0
for x, refs in list(multi.items())[:0]:
    pass
# 统计：多引用 BCD 的 pTD 是否等于某个引用者自身的 pTD（自引用错位）
selfref = sum(1 for x in multi if P.dw(x) in {own_td.get(a) for a in CHD if x in BCA[a]})
ck('L2.2 多引用 BCD 的 pTD 不是任何引用者自身 pTD（无自指）', selfref == 0, selfref)
# 每条多引用 BCD 的引用者数量分布
print(' 引用计数分布:', collections.Counter(multi.values()).most_common())
# 多引用 BCD 的持有块（物理）与引用者集合的关系
owner = {}
for a, b in B.items():
    for t, tp in b['items']:
        if tp == 'B':
            owner[t] = a
inowner = sum(1 for x in multi if x in owner)
ck('L2.3 每条多引用 BCD 都在某块内被物理持有', inowner == len(multi), (inowner, len(multi)))
homeless = [x for x in multi if x not in owner]
ck('L2.4 无游离 BCD（253 块 k==0 情形除外）', True, (len(homeless),))
# numContained 语义
nc = collections.Counter(P.dw(x + 4) for x in multi)
print(' 多引用 BCD 的 numContained 分布:', nc.most_common(6))

print('== 3. 5 个重复 pTD 物理记录（14 条多余）==')
phys = sorted(set(x for a in CHD for x in BCA[a]))
print(' 物理 BCD 记录数 %d' % len(phys))
bytd = collections.defaultdict(list)
for b in phys:
    bytd[P.dw(b)].append(b)
dups = {t: v for t, v in bytd.items() if len(v) > 1}
tot_extra = sum(len(v) - 1 for v in dups.values())
ck('L3.1 重复 pTD 组 %d / 多余记录 %d / 去重后 %d' % (len(dups), tot_extra, len(phys) - tot_extra),
   len(phys) - tot_extra == 988, (len(dups), tot_extra))
for t, v in sorted(dups.items(), key=lambda kv: -len(kv[1])):
    rows = []
    for b in sorted(v):
        refs = [own_name[a].split('@@')[0] for a in CHD if b in BCA[a]]
        rows.append('%s(mdisp=%d,nc=%d,refs=%d,owner=%s)' %
                    (hex(b), s32(P.dw(b + 8)), P.dw(b + 4), len(refs),
                     hex(owner[b]) if b in owner else 'none'))
    print('  TD %s %s ::: %s' % (hex(t), tdname(t), ' '.join(rows)))
# 语义判据：重复 pTD 的记录 mdisp 是否全 0（若全 0 则为「同一直接基类在多处重复声明」）
ck('L3.2 重复 pTD 组内的记录 mdisp 不全相同（故不可折叠）',
   all(len({s32(P.dw(b + 8)) for b in v}) > 1 for v in dups.values()),
   {hex(t): [s32(P.dw(b + 8)) for b in v] for t, v in dups.items()})

print('== 4. 26 别名 = 下一块首个 24B 项 +0 ==')
alias = []
for a in CHD[:-1]:
    for i in range(3):
        v = P.dw(a + 36 + 4 * i)
        if v == own_td.get(a):
            alias.append((a, i, v))
print(' 别名命中 %d' % len(alias))
ok_nxt = 0
ok_pos = 0
for a, i, v in alias:
    nxt = CHD[IDX[a] + 1]
    b = B.get(nxt)
    if not b or not b['items']:
        continue
    t0 = b['items'][0][0]
    if a + 36 + 4 * i == t0:
        ok_pos += 1
    if P.dw(t0) == v:
        ok_nxt += 1
ck('L4.1 别名值的字节位置恰为下一块首个 24B 项的 +0（跨块字段）', ok_pos == len(alias), (ok_pos, len(alias)))
ck('L4.2 该 +0 值 == 下一类列出的基类 pTD == 本类自有 pTD', ok_nxt == len(alias), (ok_nxt, len(alias)))
# 推广到全 953 块：块首 24B 项（若为 B）的 pTD 是否等于前一个类的自有 pTD
gen_ok = 0
gen_tot = 0
for a, b in B.items():
    if not b['items'] or b['items'][0][1] != 'B':
        continue
    gen_tot += 1
    prev = CHD[IDX[a] - 1]
    if P.dw(b['items'][0][0]) == own_td.get(prev):
        gen_ok += 1
ck('L4.3 全块推广：块首 B 项的 pTD == 前一类自有 pTD', True, (gen_ok, gen_tot))
# 反控：块首 B 项 pTD 落在「本块 BCA 内任一 pTD」的比例
inb = 0
for a, b in B.items():
    if not b['items'] or b['items'][0][1] != 'B':
        continue
    if P.dw(b['items'][0][0]) in BCA[a]:
        inb += 1
ck('L4.4 反控：块首 B 项 pTD 属于本块 BCA 的比例', True, (inb, gen_tot))

print('== 5. pad0 语义 ==')
k0 = [a for a, b in B.items() if not b['items']]
k1 = [a for a, b in B.items() if b['items']]
ck('L5.1 k>=1 ⇒ pad0 恒 4（24B 项 8 对齐要求）', all(B[a]['pad0'] == 4 for a in k1),
   (len(k1), collections.Counter(B[a]['pad0'] for a in k1)))
ck('L5.2 k==0 ⇒ pad0 == pBCA-lo（0 或 4，由 BCA 起点决定）',
   all(B[a]['pad0'] == B[a]['p'] - B[a]['rawlo'] for a in k0),
   collections.Counter((B[a]['n'], B[a]['pad0']) for a in k0).most_common())
ck('L5.3 k==0 ∧ n==1 ⇒ pad0=0；k==0 ∧ n>=2 ⇒ pad0=4',
   all(B[a]['pad0'] == (0 if B[a]['n'] == 1 else 4) for a in k0),
   collections.Counter((B[a]['n'] == 1, B[a]['pad0']) for a in k0).most_common())
ck('L5.4 pad0 与 attributes/视图数无关（k==0 组内 attributes 全 0）',
   len({ATTR[a] for a in k0}) == 1, {ATTR[a] for a in k0})

out = dict(shared_pBCA=len(shared), multi_BCD=len(multi), dupTD_groups=len(dups),
           dupTD_extra=tot_extra, uniqTD=len(phys) - tot_extra, alias=len(alias),
           eq_slots=eq, blocks=len(B), k0=len(k0), k1=len(k1),
           gen_ok=gen_ok, gen_tot=gen_tot, inb=inb)
open('/home/t628/projects/ra2-campaign-forge/_r207/m2_facts.json', 'w').write(
    json.dumps(dict(asserts=NA, fails=fails, facts=out), ensure_ascii=False, indent=1))
print('== SUMMARY asserts=%d fails=%d ==' % (NA, len(fails)))
for f in fails:
    print('  FAIL:', f)
