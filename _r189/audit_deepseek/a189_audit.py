#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R189 跨家族只读复核（deepseek）终版。判据自写，不复用 r189b/c/d 代码形状。

独立锚点：先在 .rdata/.data 里找「极大 .text 连续 dword 串」(run)，再问 run 起点前
4 字节的**值**是不是一条 COL 记录地址（看值，不看位置）。
非循环判据：用 .text 内对 .rdata 的 vptr 赋值立即数做独立 vtable 普查。
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
RA, DA = ld(RS), ld(DS); TA = ld(T)
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
def byt(va):
    o = P.r2o(va); return None if o is None else P.RAW[o]

print('# .text[%08X,%08X) .rdata[%08X,%08X) .data[%08X,%08X)' % (TLO, THI, RLO, RHI, DLO, DHI))

# ===== 1. COL =====
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
print('\n## 1  COL=%d mdisp==0=%d' % (len(COLS), sum(1 for v in COLS.values() if v[0] == 0)))

# ===== 2. run 枚举 =====
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
print('\n## 2  run=%d vtable=%d slots=%d 裸run=%d' % (len(runs), len(VT), sum(VT.values()), len(naked)))
print('   槽数直方 top=%s' % sorted(collections.Counter(VT.values()).items(), key=lambda x: -x[1])[:6])

# ===== 3. 非循环普查：.text 里的 vptr 赋值立即数 =====
print('\n## 3  vptr 赋值普查（非循环判据）')
tset = set(TA)
cand_all = set(VT) | set(s for s, L in naked)
hit_known = sorted(set(VT) & tset); hit_naked = sorted(set(s for s, L in naked) & tset)
print('   .rdata/.data 内 run 起点共 %d（已知表 %d + 裸 run %d）' % (len(cand_all), len(VT), len(naked)))
print('   其地址作为立即数出现在 .text：已知表 %d/%d ; 裸 run %d/%d' % (
    len(hit_known), len(VT), len(hit_naked), len(naked)))
print('   裸 run 命中例: %s' % [(hex(a), VT.get(a), [hex(dv(a + 4 * k)) for k in range(min(4, L))]) for a, L in
                          [(s, L) for s, L in naked if s in tset]][:6])
# .text 内所有落 .rdata/.data 的立即数 → 目标去重
imm = collections.Counter(x for x in TA if RLO <= x < RHI or DLO <= x < DHI)
imm_tab = {x: c for x, c in imm.items() if x in VT}
imm_nontab = {x: c for x, c in imm.items() if x not in VT}
print('   .text 里落 .rdata/.data 的 dword 去重后=%d ; 其中命中已知表头=%d ; 未命中=%d' % (
    len(imm), len(imm_tab), len(imm_nontab)))
# 未命中的，目标处是否本身是「.text 串起点」（可能是无 RTTI 的 vtable/函数表）
nrunstart = set(s for s, L in runs)
imm_like_vt = {x: c for x, c in imm_nontab.items() if x in nrunstart}
print('   未命中里「目标处仍是 .text 串起点」的=%d 例: %s' % (
    len(imm_like_vt), [(hex(x), c, 'slots=%d' % dict(runs)[x]) for x, c in list(imm_like_vt.items())[:6]]))

# ===== 4. 紧排 =====
tight = [vt for vt in order if nxt[vt] is not None and vt + 4 * VT[vt] == nxt[vt] - 4]
loose = [vt for vt in order if nxt[vt] is not None and vt + 4 * VT[vt] != nxt[vt] - 4]
lastvt = order[-1]
st = collections.Counter()
for vt in order:
    d = dv(vt + 4 * VT[vt])
    if vt in tight: st['tight'] += 1
    elif vt == lastvt: st['last'] += 1
    elif d == 0: st['zero'] += 1
    elif secof(d) == '.data': st['.data'] += 1
    else: st['other'] += 1
gaps = [nxt[vt] - 4 - (vt + 4 * VT[vt]) for vt in loose]
print('\n## 4  紧排=%d 非紧排(有后继)=%d 末张=1 分档=%s' % (len(tight), len(loose), dict(st)))
print('   非紧排空隙 min=%d max=%d <=0=%d' % (min(gaps), max(gaps), sum(1 for g in gaps if g <= 0)))

# ===== 5. Q1 / C2：邻接判据 + 语义判别 =====
print('\n## 5  Q1/C2')
print('   r189c 判据 VT.get(stop+4)==dv(stop)，而 VT[a] 定义即 dv(a-4) ⇒ 展开为 dv(stop)==dv(stop) 恒真')
print('   等价断言只是 "(stop+4) ∈ VT"；不含 COL 语义信息。独立复算 stop+4∈run起点(不看COL) 亦 %d/979。' % sum(
    1 for vt in tight if (vt + 4 * VT[vt] + 4) in set(s for s, L in runs)))
same = []; diff = []
for vt in tight:
    stop = vt + 4 * VT[vt]
    a = COLS[dv(vt - 4)]; b = COLS[dv(stop)]
    (same if a[1] == b[1] else diff).append((vt, a[1], a[0], b[0]))
print('   979 张紧排表：终点 COL 的类名 == 本表类名的 %d 张（同类多子对象表）; 异类名 %d 张' % (len(same), len(diff)))
print('   同类名的 (本表 mdisp, 下一块 mdisp) 配对=%s' % dict(collections.Counter((x[2], x[3]) for x in same)))
byname = collections.defaultdict(list)
for vt in order: byname[COLS[dv(vt - 4)][1]].append(vt)
multi = {k: sorted(v) for k, v in byname.items() if len(v) >= 2}
okg = sum(1 for k, vs in multi.items() if all(vs[i + 1] - 4 == vs[i] + 4 * VT[vs[i]] for i in range(len(vs) - 1)))
print('   同名多表类=%d（占 %d 张表）单表类=%d ; 多表类内严格相邻=%d ; 断裂=%d' % (
    len(multi), sum(len(v) for v in multi.values()), len(byname) - len(multi), okg, len(multi) - okg))
mono = sum(1 for k, vs in multi.items() if all(COLS[dv(vs[i] - 4)][0] < COLS[dv(vs[i + 1] - 4)][0] for i in range(len(vs) - 1)))
print('   多表类内 mdisp 严格递增的类=%d / %d' % (mono, len(multi)))
# 判据的失效性：若同类名比例高，则「下一张表是另一张表」仍真，但「与嵌套子对象无关」的说辞不成立
print('   ⇒ 判据判别力：同类名 %d 张的下一块确实是**同类的另一个子对象 vtable**，其 COL 指针插在中间；' % len(same))
print('      异类名 %d 张的下一块是**另一个类**的首表。两者都证明「截断点 dword 指向一条 COL 记录而非 vtable」，' % len(diff))
print('      但只有异类名那部分能否定「嵌套子对象」这层语义。')

# ===== 6. Q2：非紧排空隙 =====
print('\n## 6  Q2 非紧排空隙里的 .text 值')
legit = collections.Counter(dv(vt + 4 * k) for vt in order for k in range(VT[vt]))
hits = []; allz = 0; zero_then_text = []
for vt in loose:
    stop = vt + 4 * VT[vt]; end = nxt[vt] - 4
    ws = [(stop + 4 * k, dv(stop + 4 * k)) for k in range((end - stop) >> 2)]
    if all(w == 0 for _, w in ws): allz += 1
    for k, (va, w) in enumerate(ws):
        if istxt(w): hits.append((vt, VT[vt], stop, end, va, w, k, len(ws)))
print('   非紧排有后继=%d 空隙全0=%d 含.text值 dword=%d 涉及表=%d' % (
    len(loose), allz, len(hits), len({h[0] for h in hits})))
print('   这 %d 个命中里：出现在 14044 个真实槽目标集合中的=%d ; 4 字节对齐=%d ; 目标首字节 ascii 可打印=%d' % (
    len(hits), sum(1 for h in hits if h[5] in legit), sum(1 for h in hits if h[5] % 4 == 0),
    sum(1 for h in hits if byt(h[5]) is not None and 32 <= byt(h[5]) < 127)))
print('   真实槽目标(14044)中 ascii 可打印首字节占比=%.4f ; 命中中占比=%.4f' % (
    sum(c for v, c in legit.items() if byt(v) is not None and 32 <= byt(v) < 127) / sum(legit.values()),
    sum(1 for h in hits if byt(h[5]) is not None and 32 <= byt(h[5]) < 127) / len(hits)))
tb = collections.Counter(byt(v) for v in legit)
print('   真槽首字节 top8=%s ; 命中首字节=%s' % (tb.most_common(8),
      sorted(collections.Counter(byt(h[5]) for h in hits).items(), key=lambda x: -x[1])[:10]))
for vt, ns, stop, end, va, w, k, gw in hits[:4]:
    asc = ''.join(chr(b) if 32 <= b < 127 else '.' for b in struct.pack('<I', w))
    print('   例 vt=%08X slots=%d gap=%dB hit@%08X val=%08X ascii=%r 在真实槽集合中=%s 计数=%d' % (
        vt, ns, end - stop, va, w, asc, w in legit, legit.get(w, 0)))
# 结构性论证：若命中是漏槽，则该块内应有「槽 → 非 .text → 槽」的空洞布局；检查命中之后紧邻是不是下一块
print('   结构性论证：这 8 张表若真漏槽，则块内需出现 [槽][非.text][槽] 空洞；下检命中后是否直接接下一块：')
for vt in sorted({h[0] for h in hits}):
    stop = vt + 4 * VT[vt]; end = nxt[vt] - 4
    hs = [h for h in hits if h[0] == vt]
    last_hit = max(h[4] for h in hs)
    print('      vt=%08X slots=%d gap=%dB hit 数=%d 最晚命中@+%dB 距下一块=%dB' % (
        vt, VT[vt], end - stop, len(hs), last_hit - stop, end - (last_hit + 4)))
# 0 尾表之后仍有 .text 值的 3 张
print('   0 尾表(186)之后仍有 .text 值的：')
for vt in [v for v in order if v not in tight and v != lastvt and dv(v + 4 * VT[v]) == 0]:
    stop = vt + 4 * VT[vt]; end = nxt[vt] - 4
    hs = [(stop + 4 * k, dv(stop + 4 * k)) for k in range(1, (end - stop) >> 2) if istxt(dv(stop + 4 * k))]
    if hs:
        zero_then_text.append((vt, stop, end, hs))
        print('      vt=%08X slots=%d gap=%dB 命中=%s 命中值为真实槽目标? %s' % (
            vt, VT[vt], end - stop, [(hex(a), hex(w)) for a, w in hs],
            [w in legit for a, w in hs]))
print('   ⇒ 0 尾表命中数=%d' % len(zero_then_text))

# ===== 7. C4：854 构成 =====
S854 = [vt for vt in order if istxt(dv(vt + 4 * VT[vt] + 8))]
t854 = [vt for vt in S854 if vt in tight]; l854 = [vt for vt in S854 if vt not in tight]
ge2 = [vt for vt in tight if VT[nxt[vt]] >= 2]
print('\n## 7  C4  854 构成: 合计=%d 紧排中=%d 非紧排中=%d ; 紧排"下一表槽数>=2"=%d 同集=%s' % (
    len(S854), len(t854), len(l854), len(ge2), set(ge2) == set(t854)))
print('   7 张非紧排命中的 d(stop) 形态（若为浮点常数则确非槽）：')
for vt in l854:
    stop = vt + 4 * VT[vt]
    print('      vt=%08X slots=%d d(stop)=%08X(%s, float=%.6g) d(+4)=%08X(%s) d(+8)=%08X(.text) gap=%dB' % (
        vt, VT[vt], dv(stop), secof(dv(stop)), struct.unpack('<f', struct.pack('<I', dv(stop)))[0],
        dv(stop + 4), secof(dv(stop + 4)), dv(stop + 8), nxt[vt] - 4 - stop))

# ===== 8. F02/F03/F29 =====
print('\n## 8  F02 / F03 / F29')
BT = 0x7E3EBC
stop = BT + 4 * VT[BT]
print('   F02 vt=%08X slots=%d 块=[%08X COL=%08X][%08X..%08X] 宽=%dB' % (
    BT, VT[BT], BT - 4, dv(BT - 4), BT, stop - 1, 4 + 4 * VT[BT]))
print('      本表 COL=%s mdisp=%d ; 终点 COL=%08X = %s mdisp=%d ; 终点+4=%08X 是表头=%s slots=%d' % (
    COLS[dv(BT - 4)][1][:40], COLS[dv(BT - 4)][0], dv(stop), COLS[dv(stop)][1][:44],
    COLS[dv(stop)][0], stop + 4, (stop + 4) in VT, VT.get(stop + 4, -1)))
vals = [dv(BT + 4 * i) for i in range(VT[BT])]
print('      槽值不同数=%d 全 .text=%s 含 0=%d 两槽号与值:' % (len(set(vals)), all(istxt(v) for v in vals), sum(1 for v in vals if v == 0)))
for va, exp in ((0x7E3FE0, 0x43F180), (0x7E4068, 0x449440)):
    print('         %08X -> %08X (exp %08X) #%d 在界内=%s' % (
        va, dv(va), exp, (va - BT) // 4, 0 <= (va - BT) // 4 < VT[BT]))
TF = [vt for vt in order if 'TClassFactory@' in COLS[dv(vt - 4)][1]]
print('   F29 TClassFactory=%d 槽数直方=%s mdisp!=0=%d 槽数全为5=%s' % (
    len(TF), dict(sorted(collections.Counter(VT[vt] for vt in TF).items())),
    sum(1 for vt in TF if COLS[dv(vt - 4)][0] != 0), all(VT[vt] == 5 for vt in TF)))
tfnames = collections.Counter(COLS[dv(vt - 4)][1] for vt in TF)
print('      77 张覆盖的不同类名=%d ; 每类名表数直方=%s' % (
    len(tfnames), dict(collections.Counter(tfnames.values()))))

print('\n## 9  汇总 COL=%d vtable=%d slots=%d tight=%d zero=%d data=%d other=%d last=1 loose=%d d2text=%d' % (
    len(COLS), len(VT), sum(VT.values()), len(tight), st['zero'], st['.data'], st['other'], len(loose), len(S854)))
