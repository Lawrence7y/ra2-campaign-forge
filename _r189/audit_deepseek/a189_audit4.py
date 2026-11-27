#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R189 审计第四轮：三条可把 C1/C2/C3 打红的反控。
R1 放宽 COL 名字过滤（.?AU / 无名字过滤）——主会话与本审计共享同一过滤口径，属共同盲区。
R2 LSP 一致性：派生类主表槽数 >= 基类主表槽数（若前缀漏槽，应出现系统性违规）。
R3 0 值槽假设：把终止处的 0 也算作一个槽，槽位实例总数会变成多少、与 R188 的 14,044 差多少。
"""
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

def enum_cols(namefilter):
    C = {}
    for base, a in ((RLO, RA), (DLO, DA)):
        for i in range(len(a) - 4):
            d0, d1, d2, d3, d4 = a[i], a[i + 1], a[i + 2], a[i + 3], a[i + 4]
            if d0 not in (0, 1) or d2 != 0: continue
            if secof(d3) != '.data' or secof(d4) != '.rdata': continue
            nm = P.cstr(d3 + 8, 400)
            if nm is None: continue
            if not namefilter(nm): continue
            C[base + 4 * i] = (d1, nm.decode('latin1'))
    return C

runs = []
for base, a in ((RLO, RA), (DLO, DA)):
    i, n = 0, len(a)
    while i < n:
        if istxt(a[i]):
            j = i
            while j < n and istxt(a[j]): j += 1
            runs.append((base + 4 * i, j - i)); i = j
        else: i += 1

# ===== R1  放宽 COL 名字过滤 =====
print('## R1  COL 枚举口径敏感性（共同盲区检查）')
variants = [
    ('strict  .?A*@@（主会话+本审计口径）', lambda n: n.startswith(b'.?A') and n.endswith(b'@@')),
    ('loose   .??A[VU]*@@（含 struct）',    lambda n: n.startswith(b'.??A') and n[4:5] in (b'V', b'U') and n.endswith(b'@@')),
    ('none    任意 .??*@@',                 lambda n: n.startswith(b'.??') and n.endswith(b'@@')),
    ('any     不做名字过滤',                lambda n: True),
]
res = {}
for tag, f in variants:
    C = enum_cols(f)
    CA = set(C)
    VT = {s: L for s, L in runs if dv(s - 4) in CA}
    res[tag] = (C, VT)
    print('   %-34s COL=%4d vtable=%4d slots=%d' % (tag, len(C), len(VT), sum(VT.values())))
strictC, strictVT = res[variants[0][0]]
anyC, anyVT = res[variants[-1][0]]
extra_col = set(anyC) - set(strictC)
print('   放宽后多出的 COL 候选 = %d ; 其中被某个裸 run 起点前置引用的 = %d' % (
    len(extra_col), sum(1 for s, L in runs if dv(s - 4) in extra_col and dv(s - 4) not in set(strictC))))
for p in sorted(extra_col)[:12]:
    nxt = dv(p + 4)
    print('      extra COL @%08X name=%r 后接 dword=%08X(%s) 是 run 起点? %s' % (
        p, anyC[p][1][:40], nxt or 0, secof(nxt), (p + 4) in set(s for s, _ in runs)))
# 严格口径下没被认成表头的裸 run：其前置值指向的"东西"是什么
naked = [(s, L) for s, L in runs if dv(s - 4) not in set(strictC) and L >= 2]
cls = collections.Counter()
for s, L in naked:
    p = dv(s - 4)
    cls[secof(p)] += 1
print('   裸 run(L>=2) %d 个的前置值所在段 = %s' % (len(naked), dict(cls)))
# 这些裸 run 的槽值是否「全部也出现在已知表的槽集合中」（若是，则更像函数指针表复用）
legit = set(dv(v + 4 * k) for v in strictVT for k in range(strictVT[v]))
same = sum(1 for s, L in naked if all(dv(s + 4 * k) in legit for k in range(L)))
print('   裸 run 里「全部槽值都出现在已知槽集合中」的 = %d / %d（高 ⇒ 复用已有虚函数，不是新 vtable）' % (same, len(naked)))

# ===== R2  LSP 一致性反控 =====
print('\n## R2  LSP 反控：派生主表槽数 >= 基类主表槽数')
C = strictC; VT = strictVT
byname = collections.defaultdict(list)
for v in sorted(VT): byname[C[dv(v - 4)][1]].append(v)
prim = {k: (v for v in vs if C[dv(v - 4)][0] == 0) for k, vs in byname.items()}
prim = {k: next(iter(g), None) for k, g in prim.items()}
def basenames(vt):
    col = dv(vt - 4); chd = C[col][1] and dv(col + 16)
    if secof(chd) != '.rdata': return []
    nbase, arr = dv(chd + 8), dv(chd + 12)
    if secof(arr) != '.rdata' or not (0 < nbase < 64): return []
    out = []
    for j in range(nbase):
        bcd = dv(arr + 4 * j)
        if secof(bcd) not in ('.rdata', '.data'): continue
        td = dv(bcd)
        nm = P.cstr(td + 8, 400) if secof(td) == '.data' else None
        if nm: out.append((nm.decode('latin1'), dv(bcd + 8)))
    return out
viol = []; comp = 0; unk = 0
for k, v in prim.items():
    if v is None: continue
    for bn, md in basenames(v):
        if bn == k: continue
        bv = prim.get(bn)
        if bv is None: unk += 1; continue
        comp += 1
        if VT[v] < VT[bv]: viol.append((k, VT[v], bn, VT[bv]))
print('   可比较的（派生,基类）对 = %d ; 派生槽数 < 基类槽数 的违规 = %d %s' % (comp, len(viol), viol[:6]))
print('   基类无主表（未枚举）的对 = %d' % unk)

# ===== R3  0 值槽假设 =====
print('\n## R3  反控：把终止处的 dword 也算作一个槽（0 是否可能是真槽）')
order = sorted(VT); nxt = {order[i]: (order[i + 1] if i + 1 < len(order) else None) for i in range(len(order))}
tight = set(v for v in order if nxt[v] and v + 4 * VT[v] == nxt[v] - 4)
zero_t = [v for v in order if v not in tight and dv(v + 4 * VT[v]) == 0]
print('   0 尾表 = %d ; 若 0 是槽，槽位实例总数 = %d + %d = %d' % (
    len(zero_t), sum(VT.values()), len(zero_t), sum(VT.values()) + len(zero_t)))
print('   与 R188 的 14,044 差 = %d' % (sum(VT.values()) + len(zero_t) - 14044))
# 0 之后紧接的值若为浮点常数 ⇒ 0 是「填充终止符」而不是槽；若是 .text ⇒ 0 可能是槽
fol = collections.Counter()
for v in zero_t:
    d = dv(v + 4 * VT[v] + 4)
    fol['.text' if istxt(d) else ('0' if d == 0 else ('float' if d and 0x38000000 < d < 0x4F800000 else secof(d)))] += 1
print('   0 之后的 dword 类型直方 = %s' % dict(fol))
# 反向：0 之前的槽若是 0，则该表在更早处就终止 —— 检查是否存在「中间有 0 但后面还有 .text」
mid = []
for v in order:
    k = 0
    while istxt(dv(v + 4 * k)): k += 1
    for j in range(k, min(k + 24, 400)):
        if istxt(dv(v + 4 * j)) and dv(v + 4 * (j - 1)) == 0:
            mid.append((v, k, j)); break
print('   「终止后跳过 0 又出现 .text」的表 = %d %s' % (len(mid), [(hex(a), b, c) for a, b, c in mid[:6]]))
print('   ⇒ 若为 0 则等于承认「槽=0 合法且其后仍有槽」，但实测 0 后紧跟浮点常数/0，无 .text 续接')
