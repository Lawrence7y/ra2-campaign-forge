#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R189 审计第二轮：非循环/可失效判据取证。"""
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
naked = [(s, L) for s, L in runs if dv(s - 4) not in COLADD]
order = sorted(VT); nxt = {order[i]: (order[i + 1] if i + 1 < len(order) else None) for i in range(len(order))}
tight = [v for v in order if nxt[v] and v + 4 * VT[v] == nxt[v] - 4]
loose = [v for v in order if nxt[v] and v + 4 * VT[v] != nxt[v] - 4]

# --- A. 未对齐立即数扫描：vtable 地址是否被 .text 用作 vptr 立即数 ---
print('## A  .text 立即数扫描（按字节偏移，不要求 4 对齐）')
tb = bytes(P.RAW[T['rawptr']:T['rawptr'] + T['rawsize']])
def nocc(va):
    pat = struct.pack('<I', va); c = 0; p = tb.find(pat)
    while p >= 0: c += 1; p = tb.find(pat, p + 1)
    return c
vt_hit = [v for v in order if nocc(v)]
nk2 = [(s, L) for s, L in naked if L >= 2]
nk_hit = [s for s, L in nk2 if nocc(s)]
print('   1214 张表：地址在 .text 出现为立即数的 %d 张（%.1f%%）' % (len(vt_hit), 100.0 * len(vt_hit) / 1214))
print('   裸 run(len>=2) %d 个：地址出现在 .text 的 %d 个（作为基线；真 vtable 应显著更高）' % (len(nk2), len(nk_hit)))
print('   出现次数直方（已知表）=%s' % dict(sorted(collections.Counter(nocc(v) for v in order).items())[:8]))
# 早前 4 对齐扫描得到 669 ⇒ 说明 545 张的立即数未对齐，是扫描口径问题而非缺失引用
al = sum(1 for x in TA if x in VT)
print('   对照：4 字节对齐扫描命中 %d 张（上一轮数字），说明未对齐才是正确口径' % al)
# --- B. 结构：COL 记录地址 ∩ vtable 地址 ---
print('\n## B  COL 记录地址与 vtable 地址是否可混淆')
print('   |COLADD ∩ VT| = %d' % len(COLADD & set(VT)))
print('   每条 COL 记录首 dword 值域 = %s（记录以 sig∈{0,1} 开头，永不可能是 .text ⇒ 结构上不可能被当成 vtable）' % (
    dict(collections.Counter(dv(c) for c in COLADD))))
print('   ⇒ "截断点 dword 指向的记录首 dword ∈{0,1}" 这一条本身就是可失效判据（若指向 vtable，首 dword 必落 .text）')
ok = [v for v in order if dv(v + 4 * VT[v]) in COLADD and dv(dv(v + 4 * VT[v])) in (0, 1)
      and secof(dv(dv(v + 4 * VT[v]) + 12)) == '.data' and secof(dv(dv(v + 4 * VT[v]) + 16)) == '.rdata']
print('   判据 Q1「stop 值 ∈ COLADD 且目标记录 sig∈{0,1} 且 +12→.data 且 +16→.rdata」通过数 = %d / 1214' % len(ok))
print('   同一判据在 235 张非 COL 终点表上通过数 = %d（0 ⇒ 判据有判别力，不是恒真）' % sum(
    1 for v in order if v not in set(tight) and dv(v + 4 * VT[v]) in COLADD))
# --- C. 979 的类名分裂 ---
print('\n## C  979 张紧排表：下一块是谁的 COL')
same = [v for v in tight if COLS[dv(v - 4)][1] == COLS[dv(v + 4 * VT[v])][1]]
diff = [v for v in tight if v not in set(same)]
print('   同类名（下一块 = 本类另一个子对象 vtable）= %d ; 异类名（下一块 = 别的类的首表）= %d' % (len(same), len(diff)))
print('   同类名的 mdisp 配对 (本表→下一块) = %s' % dict(collections.Counter(
    (COLS[dv(v - 4)][0], COLS[dv(v + 4 * VT[v])][0]) for v in same)))
byname = collections.defaultdict(list)
for v in order: byname[COLS[dv(v - 4)][1]].append(v)
multi = {k: sorted(v) for k, v in byname.items() if len(v) >= 2}
dec = sum(1 for k, vs in multi.items() if all(COLS[dv(vs[i] - 4)][0] > COLS[dv(vs[i + 1] - 4)][0] for i in range(len(vs) - 1)))
inc = sum(1 for k, vs in multi.items() if all(COLS[dv(vs[i] - 4)][0] < COLS[dv(vs[i + 1] - 4)][0] for i in range(len(vs) - 1)))
print('   同名多表类 %d（共 %d 张）：地址升序下 mdisp 严格递减 %d 类、严格递增 %d 类' % (
    len(multi), sum(len(v) for v in multi.values()), dec, inc))
k0 = [k for k, vs in multi.items() if k.startswith('.?AVAbstractClass@@')]
for k in k0:
    print('   例 %s : %s' % (k, [(hex(v), VT[v], COLS[dv(v - 4)][0]) for v in multi[k]]))
k1 = [k for k, vs in multi.items() if k.startswith('.?AVBuildingClass@@')]
for k in k1:
    print('   例 %s : %s' % (k, [(hex(v), VT[v], COLS[dv(v - 4)][0]) for v in multi[k]]))
# --- D. Q2 命中点是不是别的结构 ---
print('\n## D  Q2：非紧排空隙里 .text 值 dword 的性质')
runstart = set(s for s, _ in runs); runlen = dict(runs)
legit = set(dv(v + 4 * k) for v in order for k in range(VT[v]))
tot = 0; info = collections.Counter()
for v in loose:
    stop = v + 4 * VT[v]; end = nxt[v] - 4
    for k in range((end - stop) >> 2):
        va = stop + 4 * k; w = dv(va)
        if not istxt(w): continue
        tot += 1
        info['是真实槽目标' if w in legit else '非真实槽目标'] += 1
        info['命中点本身是 run 起点' if va in runstart else '命中点不是 run 起点'] += 1
        info['命中点的前值∈COLADD(即另一张表头)' if dv(va - 4) in COLADD else '命中点前值非 COL'] += 1
        info['命中目标的 4 个槽中前 2 个合法' if all(istxt(dv(w + 4 * j)) for j in range(2)) else '命中目标处不成串'] += 1
print('   命中总数 %d ; %s' % (tot, dict(info)))
# --- E. 零尾空隙的真实内容 ---
print('\n## E  0 尾表的空隙内容抽样（检验"空隙非纯 0"）')
zerot = [v for v in order if v not in set(tight) and v != order[-1] and dv(v + 4 * VT[v]) == 0]
pure = 0; samp = []
for v in zerot:
    stop = v + 4 * VT[v]; end = nxt[v] - 4
    ws = [dv(stop + 4 * k) for k in range((end - stop) >> 2)]
    if all(w == 0 for w in ws): pure += 1
    if len(samp) < 3: samp.append((v, VT[v], end - stop, ws[:12]))
print('   0 尾表 %d ; 空隙全 0 的 %d ; 抽 3 例:' % (len(zerot), pure))
for v, n, g, ws in samp:
    print('      vt=%08X slots=%d gap=%dB words=%s' % (v, n, g, ['%08X' % x for x in ws]))
# --- F. 非紧排空隙大小 vs 块宽恒等式 ---
print('\n## F  C1「块之间无空隙」的量化')
print('   相邻块转移 1213 次：间隙 0 的 %d 次 ; 间隙 >=4 的 %d 次（占 %.1f%%）' % (
    len(tight), len(loose), 100.0 * len(loose) / 1213))
print('   ⇒ C1「块之间无空隙」在 %d/1213 次转移上为假；与 C5「235 张块间空隙恒>0」自相矛盾' % len(loose))
