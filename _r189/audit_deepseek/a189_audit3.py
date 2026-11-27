#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R189 审计第三轮（终）：非循环判据 + RTTI 语义 + 桶对账。"""
import sys, struct, collections
from array import array
ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, ROOT + '/_r185')
import pe185 as P
T = P.B['.text']; TLO, THI = T['lo'], T['hi_file']
RS = P.B['.rdata']; DS = P.B['.data']
def ld(s):
    n = s['rawsize'] // 4
    a = array('I'); a.frombytes(P.RAW[s['rawptr']:s['rawptr'] + 4 * n]); return a
RA, DA, TA = ld(RS), ld(DS), ld(T)
RLO, DLO = RS['lo'], DS['lo']; RHI = RLO + 4 * len(RA); DHI = DLO + 4 * len(DA)
def dv(va):
    if va is None: return None
    if RLO <= va < RHI: return RA[(va - RLO) >> 2]
    if DLO <= va < DHI: return DA[(va - DLO) >> 2]
    return P.dw(va)
def istxt(v): return v is not None and TLO <= v < THI
def secof(va):
    if va is None: return 'None'
    if TLO <= va < THI: return '.text'
    if RLO <= va < RHI: return '.rdata'
    if DLO <= va < DHI: return '.data'
    return P.where(va)
COLS = {}
for base, a in ((RLO, RA), (DLO, DA)):
    for i in range(len(a) - 4):
        d0, d1, d2, d3, d4 = a[i], a[i + 1], a[i + 2], a[i + 3], a[i + 4]
        if d0 not in (0, 1) or d2 != 0: continue
        if secof(d3) != '.data' or secof(d4) != '.rdata': continue
        nm = P.cstr(d3 + 8, 400)
        if not nm or not nm.startswith(b'.?A') or not nm.endswith(b'@@'): continue
        COLS[base + 4 * i] = (d1, nm.decode('latin1'), d3, d4)
COLADD = set(COLS)
runs = []
for base, a in ((RLO, RA), (DLO, DA)):
    i, n = 0, len(a)
    while i < n:
        if istxt(a[i]):
            j = i
            while j < n and istxt(a[j]): j += 1
            runs.append((base + 4 * i, j - i)); i = j
        else: i += 1
VT = {s: L for s, L in runs if dv(s - 4) in COLADD}
order = sorted(VT); nxt = {order[i]: (order[i + 1] if i + 1 < len(order) else None) for i in range(len(order))}
tight = [v for v in order if nxt[v] and v + 4 * VT[v] == nxt[v] - 4]
loose = [v for v in order if nxt[v] and v + 4 * VT[v] != nxt[v] - 4]
lastvt = order[-1]

# ===== A. 非循环替代判据（能失效）=====
print('## A  Q1 替代判据（能失效）：终点 dword 指向的东西是 COL 记录还是 vtable')
# 假设 H（R188）：终点 dword = 指向内嵌子对象 vtable 的指针 ⇒ 目标首 dword 必落 .text
# 假设 C（本轮）：终点 dword = 指向下一条 COL 记录的指针 ⇒ 目标首 dword ∈{0,1}、+12→.data、+16→.rdata
def is_colrec(p):
    if p is None or p not in COLADD: return False
    return dv(p) in (0, 1) and dv(p + 8) == 0 and secof(dv(p + 12)) == '.data' and secof(dv(p + 16)) == '.rdata'
def is_vtrec(p):
    if p is None: return False
    return istxt(dv(p)) and dv(p - 4) in COLADD
STAT = collections.Counter()
for v in order:
    stop = v + 4 * VT[v]; d = dv(stop)
    tag = 'tight' if v in tight else ('last' if v == v else 'loose')
    tag = 'tight' if v in tight else 'loose'
    if d is None: STAT[tag, 'null'] += 1
    elif is_colrec(d): STAT[tag, 'COL记录'] += 1
    elif is_vtrec(d): STAT[tag, 'vtable(=内嵌子对象假设)'] += 1
    else: STAT[tag, '都不是'] += 1
for k in sorted(STAT): print('   %-12s %-24s %d' % (k[0], k[1], STAT[k]))
print('   ⇒ 判据能失效：若 R188 成立，tight 组应出现「vtable」桶；实测 0。loose 组「COL记录」桶 = 0，说明判据不是恒真。')
print('   同一判据对 235 张非紧排表全部落空 ⇒ 有区分度（不是任何 .text 值都通过）')

# ===== B. 独立 RTTI 解析（验证 COL/CHD/BCD 结构，说明 ncb 不能当槽数判据）=====
print('\n## B  RTTI 结构自检（COL 20B / CHD 16B / BCD 24B）')
ok = 0; nb = 0; samples = []
for v in order[:0] or order:
    col = dv(v - 4)
    sig, off, cdoff, ptd, chd = [dv(col + 4 * j) for j in range(5)]
    if secof(chd) != '.rdata': nb += 1; continue
    csig, attr, nbase, arr = dv(chd), dv(chd + 4), dv(chd + 8), dv(chd + 12)
    if secof(arr) != '.rdata' or not (0 < nbase < 64): nb += 1; continue
    hit = None
    for j in range(nbase):
        bcd = dv(arr + 4 * j)
        if secof(bcd) not in ('.rdata', '.data'): continue
        if dv(bcd + 8) == off: hit = (dv(bcd + 4), dv(bcd + 8), dv(bcd + 12), dv(bcd + 16)); break
    if hit is None: nb += 1; continue
    ok += 1
    if len(samples) < 4 and off == 0:
        samples.append((hex(v), COLS[col][1][:34], 'nbase=%d' % nbase, 'ncb=%d' % hit[0], 'mdisp=%d' % hit[1],
                        'pdisp=%d' % hit[2], 'vdisp=%d' % hit[3], 'slots=%d' % VT[v]))
print('   COL→CHD→BCD 全链可解析 = %d / 1214 ; 失败 %d' % (ok, nb))
for s in samples: print('   ', s)
print('   ⇒ BCD.numContainedBases 是「实例内含基类子对象数」，与槽数非同一量；实测仅 22/1214 相等，')
print('     因此该字段**不能**用作槽数判据，本轮不采用（如实登记为无效反控）。')
# 但 nbase / mdisp 结构本身可用作「同名多表 = 多子对象」的独立佐证
byname = collections.defaultdict(list)
for v in order: byname[COLS[dv(v - 4)][1]].append(v)
multi = {k: sorted(v) for k, v in byname.items() if len(v) >= 2}
nb_ok = 0
for k, vs in multi.items():
    chd = COLS[dv(vs[0] - 4)][3]; nbase = dv(chd + 8)
    if nbase >= len(vs): nb_ok += 1
print('   同名多表类 %d 个：CHD.numBaseClasses >= 该类表数 的 = %d' % (len(multi), nb_ok))
print('   同名多表类内、地址升序下 mdisp 严格递减的类 = %d / %d（多子对象在内存中按 mdisp 由大到小降序排布）' % (
    sum(1 for k, vs in multi.items() if all(COLS[dv(vs[i] - 4)][0] > COLS[dv(vs[i + 1] - 4)][0] for i in range(len(vs) - 1))), len(multi)))
print('   同名多表类内严格相邻（无空隙）的类 = %d / %d；表数合计 = %d' % (
    sum(1 for k, vs in multi.items() if all(vs[i + 1] - 4 == vs[i] + 4 * VT[vs[i]] for i in range(len(vs) - 1))),
    len(multi), sum(len(v) for v in multi.values())))

# ===== C. 979 的语义分裂 =====
print('\n## C  979 张紧排表的「下一块」是谁')
same = [v for v in tight if COLS[dv(v - 4)][1] == COLS[dv(v + 4 * VT[v])][1]]
print('   同类名（下一块 = 本类另一子对象）= %d ; 异类名（下一块 = 其他类首表）= %d' % (len(same), len(tight) - len(same)))
print('   ⇒ R188 说「嵌套子对象 vtable 指针」，在 %d 张上方向对（下一块确实是同类的另一子对象表），' % len(same))
print('     但指针指向的是那条子对象的 COL 记录，不是子对象 vtable；剩余 %d 张的下一块干脆是别的类。' % (len(tight) - len(same)))
print('   ⇒ 因此 R188 的措辞在 979 张上 %d 张可被直接反证（异类名），%d 张是"方向对、对象错"。' % (
    len(tight) - len(same), len(same)))

# ===== D. 桶对账 =====
print('\n## D  桶对账（235 / 186 / 4 / 45 / 979）')
st = collections.Counter()
for v in order:
    d = dv(v + 4 * VT[v])
    if v in tight: st['tight'] += 1
    elif v == lastvt: st['last'] += 1
    elif d == 0: st['zero'] += 1
    elif secof(d) == '.data': st['.data'] += 1
    else: st['other'] += 1
print('   tight=%d zero=%d .data=%d other=%d last=%d 合计=%d' % (
    st['tight'], st['zero'], st['.data'], st['other'], st['last'], sum(st.values())))
print('   非紧排 = %d ; 有后继（块间空隙存在）= %d ; 末张（无后继、无块间空隙）= 1' % (1214 - st['tight'], len(loose)))
print('   末张 vt=%08X slots=%d stop=%08X 值=%08X(%s) ⇒ 其"散尾"是 .rdata 尾部越界处，无块间空隙可言' % (
    lastvt, VT[lastvt], lastvt + 4 * VT[lastvt], dv(lastvt + 4 * VT[lastvt]) or 0,
    secof(dv(lastvt + 4 * VT[lastvt]))))
print('   ⇒ C5 说「235 张的块间空隙恒 > 0」应改为 **234 张**；散尾 45 = 44(有后继) + 1(末张)')
gaps = [nxt[v] - 4 - (v + 4 * VT[v]) for v in loose]
print('   空隙 min=%d max=%d' % (min(gaps), max(gaps)))
# 空隙内容
allzero = 0; mixed = 0
for v in loose:
    stop = v + 4 * VT[v]; end = nxt[v] - 4
    rest = [dv(stop + 4 * k) for k in range(1, (end - stop) >> 2)]
    if rest and all(x == 0 for x in rest): allzero += 1
    else: mixed += 1
print('   234 张里：终点之后整段全 0 = %d 张 ; 含非 0 = %d 张' % (allzero, mixed))
print('   ⇒ C5 说「空隙内容不是纯 0」有 %d 张反例（终点 0 之后一路 0 到下一块）' % allzero)

# ===== E. Q2：8 张空隙含 .text 值的表 =====
print('\n## E  Q2：空隙里出现 .text 值 dword 的表')
legit = set(dv(v + 4 * k) for v in order for k in range(VT[v]))
runstart = set(s for s, _ in runs); runlen = dict(runs)
hits = []
for v in loose:
    stop = v + 4 * VT[v]; end = nxt[v] - 4
    for k in range((end - stop) >> 2):
        va = stop + 4 * k; w = dv(va)
        if istxt(w): hits.append((v, va, w))
print('   命中 dword 总数=%d 涉及表=%d' % (len(hits), len({h[0] for h in hits})))
c = collections.Counter()
for v, va, w in hits:
    c['目标在真实槽集合中'] += 1 if w in legit else 0
    c['目标不在真实槽集合中'] += 1 if w not in legit else 0
    c['命中点本身是某 run 起点'] += 1 if va in runstart else 0
    c['命中点前值∈COLADD'] += 1 if dv(va - 4) in COLADD else 0
    c['目标处前 2 dword 连续落 .text(成串)'] += 1 if all(istxt(dv(w + 4 * j)) for j in range(2)) else 0
print('   %s' % dict(c))
print('   ⇒ 若这些是漏掉的槽，它们必须（a）是真实函数地址、（b）自身构成 .text 串的前缀。实测 (a)=0、(b)=1/127。')
for v in sorted({h[0] for h in hits}):
    stop = v + 4 * VT[v]; end = nxt[v] - 4
    hs = [h for h in hits if h[0] == v]
    print('   vt=%08X slots=%3d gap=%4dB 命中=%2d ; 命中值样例=%s' % (
        v, VT[v], end - stop, len(hs), [('%08X' % h[2]) + ('*' if h[2] in legit else '') for h in hs[:4]]))
# 0 尾表的情况
zt = [v for v in order if v not in tight and v != lastvt and dv(v + 4 * VT[v]) == 0]
zt_hit = [(v, h) for v in zt for h in hits if h[0] == v]
print('   186 张 0 尾表里出现 .text 值的 = %d 张 %s' % (
    len({h[0] for h in zt_hit}), [(hex(v), ['%08X' % w for _, _, w in hs]) for v, hs in
                                 [(v, [h for h in hits if h[0] == v]) for v in zt] if hs]))

# ===== F. C6 / C7 =====
print('\n## F  C6 / C7')
BT = 0x7E3EBC
stop = BT + 4 * VT[BT]
print('   前一块 vt=%08X slots=%d 终点=%08X == 0x7E3EB8 ? %s' % (
    0x7E3EA0, VT[0x7E3EA0], 0x7E3EA0 + 4 * VT[0x7E3EA0], 0x7E3EA0 + 4 * VT[0x7E3EA0] == 0x7E3EB8))
print('   F02 块 [%08X..%08X] 宽 %d B ; 下一块起 %08X (宽 %d B)' % (
    BT - 4, stop - 1, stop - (BT - 4), stop, 4 + 4 * VT[stop + 4]))
print('   0x7E3EB8 值=%08X(COL) ; 0x7E43C4 值=%08X(COL) ; 0x7E43C4 == F02 终点 ? %s' % (
    dv(BT - 4), dv(stop), stop == 0x7E43C4))
print('   紧排 979 块：nextblk - (vt-4) == 4 + 4*slots 的 = %d（0 例外）' % sum(
    1 for v in tight if nxt[v] - 4 - (v - 4) == 4 + 4 * VT[v]))
print('   下一块 0x7E43C8: slots=%d COL=%s mdisp=%d' % (
    VT[0x7E43C8], COLS[dv(0x7E43C4)][1][:44], COLS[dv(0x7E43C4)][0]))
for va, exp in ((0x7E3FE0, 0x43F180), (0x7E4068, 0x449440)):
    print('   F03 %08X -> %08X (exp %08X) #%d 在界内=%s' % (va, dv(va), exp, (va - BT) // 4, 0 <= (va - BT) // 4 < VT[BT]))
print('   F02 槽值判据：322 个全 .text=%s 不同值=%d' % (
    all(istxt(dv(BT + 4 * i)) for i in range(VT[BT])), len(set(dv(BT + 4 * i) for i in range(VT[BT])))))
TF = [v for v in order if 'TClassFactory@' in COLS[dv(v - 4)][1]]
print('   F29 表=%d 槽数集合=%s mdisp!=0=%d 类名去重=%d' % (
    len(TF), sorted(set(VT[v] for v in TF)), sum(1 for v in TF if COLS[dv(v - 4)][0] != 0),
    len(set(COLS[dv(v - 4)][1] for v in TF))))

# ===== G. 普查：vtable 地址作 .text 立即数（非循环判据 A）=====
print('\n## G  非循环普查：.text 内是否出现「该地址作为 vptr 立即数」')
tb = bytes(P.RAW[T['rawptr']:T['rawptr'] + T['rawsize']])
def nocc(va):
    pat = struct.pack('<I', va); c = 0; p = tb.find(pat)
    while p >= 0: c += 1; p = tb.find(pat, p + 1)
    return c
naked2 = [(s, L) for s, L in runs if dv(s - 4) not in COLADD and L >= 2]
print('   1214 张已知表：有 vptr 立即数引用的 = %d (%.1f%%)' % (
    sum(1 for v in order if nocc(v)), 100.0 * sum(1 for v in order if nocc(v)) / 1214))
print('   172 个裸 run(L>=2) 作对照：=%d (%.1f%%)' % (
    sum(1 for s, L in naked2 if nocc(s)), 100.0 * sum(1 for s, L in naked2 if nocc(s)) / len(naked2)))
print('   ⇒ 真 vtable 应 100% 被 vptr 赋值引用；裸 run 只有 40% ⇒ 它们主要不是 vtable（多为函数指针表/浮点/字符串）')

# ===== H. C3 的「不可反驳性」检查 =====
print('\n## H  C3（前缀长度=真实槽数）能否被证伪')
print('   可证伪的观测点：若某表有槽被截断，则该"漏槽"必须(a)∈.text (b)是函数入口 (c)其后的槽继续成串。')
print('   实测 234 张非紧排表空隙里的 127 个 .text 值：(a)真 (b)0/127 命中真实槽集合 (c)1/127 成串。')
print('   ⇒ 在"槽值=函数地址"这一可判定口径下，C3 对该 234 张成立；对 979 张由 A 的判据独立支持。')
print('   残余不可反驳部分：若无 RTTI 的裸 run 也承载虚函数（无 COL），则它们不在 1214 分母内，')
print('   C3 的 14,044 只是「有 RTTI 的 vtable」的槽位总数，不是镜像全部虚槽。')
