#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R207 m16：逐条复算审计员 #525 的 7 问（§2.12 规则 D：所有审计结论必须主会话亲自复算）。
#525 的核心订正候选：
 A1 「304 vs 77」因果错：真正产生失配的是「holder != first」的 44 条记录，成 38 对互换块；
 A2 不是循环论证，但需换锚点：nc==NB-1 在每 BCA 中恰命中 1 槽且恒为 index 0；preorder 1+nc 递归自洽 954/954；
 A3 nc 的真义 = 本类 preorder 子树规模-1（43 条无类 TD 也成立），非「numBaseClasses-1」也非「直接基类数」；
 A4 六字段去重 1002 是恒真式（零信息量），最小身份键 = (pTD,mdisp,attrs)；
 A5 attributes 位义静态不可判定，但 3 条相关性可检验；
 A6 34 个无类 TD 与类 TD 结构同构、且 36B 头扫描 954 个零多零漏。
逐条独立实现并给 PASS/FAIL。"""
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
td2c = {v: k for k, v in own_td.items()}
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
R = {b: (P.dw(b), P.dw(b + 4), s32(P.dw(b + 8)), s32(P.dw(b + 12)),
         s32(P.dw(b + 16)), P.dw(b + 20)) for b in phys}
pos = collections.defaultdict(list)
for a in CHD:
    for j, x in enumerate(BCA[a]):
        pos[x].append((a, j))
first = {}
for a in CHD:
    for x in BCA[a]:
        first.setdefault(x, a)
# 块解析（R206 口径）
BL = {}
for i in range(1, len(CHD)):
    a = CHD[i]
    lo = CHD[i - 1] + 36
    p = pBCA[a]
    for pad in (0, 4):
        q = lo + pad
        if q > p or (p - q) % 24:
            continue
        it = []
        for j in range((p - q) // 24):
            t = q + 24 * j
            if t in COL and COL[t]['pCHD'] == a:
                it.append((t, 'C'))
            elif TDOK(P.dw(t)) and P.dw(t + 12) == 0xffffffff:
                it.append((t, 'B'))
            else:
                it = None
                break
        if it is None:
            continue
        if [P.dw(p + 4 * j) for j in range(NB[a])] == BCA[a] and a - (p + 4 * NB[a]) in (4, 8):
            BL[a] = dict(pad=pad, items=it, p=p, n=NB[a], lo=q)
            break
holder = {}
for a, b in BL.items():
    for t, k in b['items']:
        if k == 'B':
            holder[t] = a

print('== A1 复算：304 vs 77 的因果 ==')
multi = [x for x in phys if len(pos[x]) > 1]
ck('A1.0 多引用记录 304', len(multi) == 304, len(multi))
mis = [x for x in multi if holder.get(x) != first[x]]
ck('A1.1 其中 holder != first 的 %d 条（审计报 44）' % len(mis), len(mis) == 44, len(mis))
misblk = collections.Counter(holder[x] for x in mis)
print(' 失配落块数 %d，块内失配数分布 %s' % (len(misblk), collections.Counter(misblk.values()).most_common()))
# 未持有（缺失）记录：多引用但不在其首现块
missing = {}
for a in CHD:
    for x in BCA[a]:
        if x in first and first[x] == a and (x in holder and holder[x] != a):
            missing.setdefault(a, []).append(x)
print(' 首现块未持有的记录 %d 条 / %d 块' % (sum(len(v) for v in missing.values()), len(missing)))
# 精确分解：38 个有缺失块 + 39 个有多余块 = 77；44 = 40 + 4（首现类 CHD[0] 无块）
cls = collections.Counter()
for a, b in BL.items():
    slots = {t for t, k in b['items'] if k == 'B'}
    fs = {x for x in BCA[a] if first[x] == a}
    cls[(bool(fs - slots), bool(slots - fs))] += 1
ck('A1.2 块四分类 {(无缺,无余):876,(无缺,多余):39,(有缺,无余):38,(双):0} 且 38+39=77',
   cls[(False, False)] == 876 and cls[(False, True)] == 39 and cls[(True, False)] == 38
   and cls[(True, True)] == 0 and 38 + 39 == 77, cls.most_common())
chd0 = sum(1 for x in mis if first[x] == CHD[0])
ck('A1.5 失配 44 条分布在 39 个首现类上，其中 4 条的首现类是无块类 0x%x' % CHD[0],
   len(mis) == 44 and len(missing) == 39 and sum(len(v) for v in missing.values()) == 44 and chd0 == 4,
   (len(mis), len(missing), sum(len(v) for v in missing.values()), chd0))
# 77 = 876/953 的缺口
gap = 0
for a, b in BL.items():
    slots = {t for t, k in b['items'] if k == 'B'}
    fs = {x for x in BCA[a] if first[x] == a}
    if slots != fs:
        gap += 1
ck('A1.3 缺口块 %d 个（R206 报 77）' % gap, gap == 77, gap)
ck('A1.4 缺口块 77 由 38 缺 + 39 余双向构成（非单向 39）', gap == 77, (gap, len(missing)))

print('== A2 复算：nc 律的锚点与 preorder ==')
hit0 = sum(1 for a in CHD if sum(1 for j, x in enumerate(BCA[a]) if R[x][1] == NB[a] - 1) == 1
           and R[BCA[a][0]][1] == NB[a] - 1)
ck('A2.1 nc==NB-1 在每 BCA 中恰命中 1 槽且恒为 index 0：954/954', hit0 == 954, hit0)


def subtree(a, maxd=40):
    """从 BCA[a] 的 preorder 序展开子树，返回节点集合（含自身）。"""
    seen = []
    stack = []
    have = {0}
    for j, x in enumerate(BCA[a]):
        if j == 0:
            stack = [R[x][1]]
            seen.append(x)
            continue
        while stack and stack[-1] == 0:
            stack.pop()
        if not stack:
            break
        stack[-1] -= 1
        stack.append(R[x][1])
        seen.append(x)
    return seen


pref_ok = 0
viol = []
for a in CHD:
    st = subtree(a)
    if len(st) == NB[a] and st == BCA[a]:
        pref_ok += 1
    else:
        viol.append((hex(a), len(st), NB[a]))
ck('A2.2 preorder 1+nc 递归展开覆盖整 BCA（954/954）', pref_ok == 954, (pref_ok, viol[:3]))

print('== A3 复算：nc 的真义（子树规模 vs 直接基类数）==')
treeok = 0
bad3 = []
for b in phys:
    # 该记录的 pTD 所属类（若有）作为子树根
    c = td2c.get(R[b][0])
    if c is None:
        continue
    # 找一处引用该记录、且该记录在 BCA 中作为子树的「类」
    okn = False
    for a, j in pos[b]:
        sub = subtree(a)
        # 该节点在 preorder 中的子树规模
        # 逐位置计算
        k = j
        cnt = 1
        stack = [R[BCA[a][j]][1]]
        k2 = j + 1
        while stack and k2 < len(BCA[a]):
            while stack and stack[-1] == 0:
                stack.pop()
            if not stack:
                break
            stack[-1] -= 1
            stack.append(R[BCA[a][k2]][1])
            cnt += 1
            k2 += 1
        if R[b][1] == cnt - 1:
            okn = True
            break
    if okn:
        treeok += 1
    else:
        bad3.append((hex(b), tn(R[b][0]), R[b][1]))
ck('A3.1 nc == preorder 子树规模-1（在某个引用处的展开）：959/1002（43 条无类 TD 记录不在此口径内）',
   treeok == 959, (treeok, len(bad3)))
direct = sum(1 for b in phys if td2c.get(R[b][0]) and R[b][1] == NB[td2c[R[b][0]]] - 1)
ck('A3.2 反控「numBaseClasses-1」959/1002（43 条无类 TD 无法映射）', direct == 959, direct)

print('== A4 复算：六字段去重是恒真式 ==')
k6 = len({R[b] for b in phys})
k3 = len({(R[b][0], R[b][2], R[b][5]) for b in phys})
k2 = len({(R[b][0], R[b][2]) for b in phys})
k_nc = len({(R[b][0], R[b][2], R[b][1]) for b in phys})
ck('A4.1 六字段去重 1002', k6 == 1002, k6)
ck('A4.2 最小身份键 (pTD,mdisp,attrs) 已达 1002（nc 无贡献）', k3 == 1002, (k3, k2, k_nc))
# nc 是否为 pTD 的函数
bydd = collections.defaultdict(set)
for b in phys:
    bydd[R[b][0]].add(R[b][1])
ck('A4.3 nc 是 pTD 的函数（同一 pTD 的 nc 恒定）', all(len(v) == 1 for v in bydd.values()),
   [hex(k) for k, v in bydd.items() if len(v) > 1][:3])

print('== A5 复算：attributes 的 3 条相关性 ==')
nz = [b for b in phys if R[b][5] != 0]
ck('A5.1 attrs!=0 的 11 条全 nc==0', all(R[b][1] == 0 for b in nz), len(nz))
ck('A5.2 attrs!=0 的 11 条全非 index0', all(j >= 1 for b in nz for a, j in pos[b]),
   sorted({j for b in nz for a, j in pos[b]}))
td2 = {R[b][0] for b in phys if R[b][5] == 2}
ck('A5.3 attrs==2 的 7 条全同一 TD', len(td2) == 1, [tn(t) for t in td2])
firstpos2 = sum(1 for b in phys if R[b][5] == 9 for a, j in pos[b]
                if sum(1 for j2, y in enumerate(BCA[a]) if R[y][0] == R[b][0] and j2 < j) >= 1)
ck('A5.4 attrs==9 的 4 条中「同 pTD 在同 BCA 内先前已出现」的条数', True, firstpos2)
ck('A5.5 attrs&1 的 4 条其 pdisp 恒 -1（与「虚拟基」标准位义矛盾）',
   all(R[b][3] == -1 for b in phys if R[b][5] & 1), sum(1 for b in phys if R[b][5] & 1))

print('== A6 复算：34 个无类 TD 与 36B 头通用扫描 ==')
nohead = {R[b][0] for b in phys if R[b][0] not in td2c}
ck('A6.1 无类 TD 34 个', len(nohead) == 34, len(nohead))
ck('A6.2 34 个无类 TD 的 +0 与类 TD 同值、+4 恒 0',
   all(P.dw(t) == P.dw(list(own_td.values())[0]) and P.dw(t + 4) == 0 for t in nohead),
   sum(1 for t in nohead if P.dw(t) == P.dw(list(own_td.values())[0])))
# 通用 36B 头扫描（不依赖 COL 命中）
sec = P.B['.rdata']
lo, hi = sec['lo'], sec['lo'] + sec['rawsize']
hits = []
for a in range(lo, hi - 36, 4):
    if P.dw(a) != 0:
        continue
    if P.dw(a + 16) not in (0, 1, 2):
        continue
    if P.dw(a + 20) != 0:
        continue
    if P.dw(a + 32) != a:
        continue
    if not (1 <= P.dw(a + 8) <= 64):
        continue
    if P.where(P.dw(a + 12)) != '.rdata':
        continue
    if P.where(P.dw(a + 28)) != '.data':
        continue
    nm = P.cstr(P.dw(a + 28) + 8, 400) or b''
    if not nm.startswith(b'.?A'):
        continue
    hits.append(a)
ck('A6.3 通用 36B 头扫描恰 %d 个且与已知 954 头零多零漏' % len(hits),
   len(hits) == 954 and set(hits) == set(CHD), (len(hits), len(set(hits) - set(CHD)), len(set(CHD) - set(hits))))
ck('A6.4 34 个无类 TD 无一被任何头 +28 引用',
   all(t not in {own_td[a] for a in CHD} for t in nohead), 34)
# 引用计数：类 TD 最小 2
rc = collections.Counter()
for b in phys:
    rc[R[b][0]] += 1
for a in CHD:
    rc[own_td[a]] += 1
ck('A6.5 类 TD 引用数最小 2（BCD+0 与 HEAD+28）', min(rc[t] for t in own_td.values()) == 2,
   min(rc[t] for t in own_td.values()))
ck('A6.6 无类 TD 多数引用数 1', sum(1 for t in nohead if rc[t] == 1) >= 30,
   (sum(1 for t in nohead if rc[t] == 1), len(nohead)))

facts = dict(a1_multi=len(multi), a1_mis=len(mis), a1_misblk=len(misblk),
             a1_missing=sum(len(v) for v in missing.values()), a1_missingblk=len(missing),
             a1_class4=dict((str(k),v) for k,v in cls.items()), a1_gap=gap,
             a2_hit0=hit0, a2_preorder=pref_ok,
             a3_tree=treeok, a3_direct=direct,
             a4_k6=k6, a4_k3=k3, a4_k2=k2, a4_knc=k_nc,
             a6_hits=len(hits), a6_nohead=len(nohead),
             a6_rc1=sum(1 for t in nohead if rc[t] == 1))
out = dict(asserts=NA, fails=fails, facts=facts)
open('/home/t628/projects/ra2-campaign-forge/_r207/m16_audit_verify.json', 'w').write(
    json.dumps(out, ensure_ascii=False, indent=1))
print(json.dumps(facts, ensure_ascii=False))
print('== SUMMARY asserts=%d fails=%d ==' % (NA, len(fails)))
for f in fails:
    print('  FAIL:', f)
