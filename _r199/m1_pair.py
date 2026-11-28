#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R199 主会话第一刀：主虚表「前缀继承一致性」基线的独立复算（用于复算执行员 A 的数字）。
口径全部字节读：
 A1 COL 24B: +0 in {0,1,2}, +8==0, +12 -> .data, +16 -> .rdata, 名串在 pTD+8 (上限 400)。
 A2 vt: dword[vt] 落 .text 且 dword[vt-4] 是 COL。nslot = 连续落 .text 的 dword 数。
 A3 主表 = COL.mdisp==0，共 954。
 A4 CHD: +0==0, +8=n, +12=BCD 指针数组; BCD 24B: +0 pTD, +4 ncb, +8 mdisp(s32)。
 A5 直接子结点链 j=i+1; while j<=i+ncb[i]: 子结点 j; j += ncb[j]+1。
判据：
 P1 基线四数 1214/1214/14044/954。
 P2 配对统计四类 (a)(b)(c)(d)，(d) 再分 (d1)(d2)。
 P3 前缀比较：配对 (C,B) 的 min(n_d,n_b) 槽逐槽比，得总匹配率。
反控：
 R2 打乱配对（用确定性下标置换）后匹配率必须显著下降。
 R3 前缀长度 L-1 时匹配率变化。
"""
import sys, struct, collections, json
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P

fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

def s32(v): return struct.unpack('<i', struct.pack('<I', v))[0]
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']
def in_text(x): return x is not None and LO <= x < HI

COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1, 2) or w[i + 2] != 0: continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
        nm = P.cstr(w[i + 3] + 8, 400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base + 4 * i] = dict(mdisp=s32(w[i + 1]), ptd=w[i + 3], pchd=w[i + 4],
                                 name=nm.decode('latin1'))
VT = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL: VT[base + 4 * i] = P.dw(base + 4 * i - 4)
NS = {}
def nslot(vt):
    if vt in NS: return NS[vt]
    k = 0
    while True:
        t = P.dw(vt + 4 * k)
        if not in_text(t): break
        k += 1
    NS[vt] = k; return k
MAIN = [vt for vt in VT if COL[VT[vt]]['mdisp'] == 0]
ck('P1a COL==1214', len(COL) == 1214, len(COL))
ck('P1b VT==1214', len(VT) == 1214, len(VT))
ck('P1c 槽总==14044', sum(nslot(v) for v in VT) == 14044, sum(nslot(v) for v in VT))
ck('P1d 主表==954', len(MAIN) == 954, len(MAIN))
ck('P1e 0x7F5C70 类名/槽数', (COL[VT[0x7F5C70]]['name'], nslot(0x7F5C70)) == ('.?AVUnitClass@@', 344),
   (COL[VT[0x7F5C70]]['name'], nslot(0x7F5C70)))

# --- CHD/BCD 与直接子结点
CHD = {}
for c, cc in COL.items():
    v = cc['pchd']
    if v in CHD: continue
    CHD[v] = dict(n=P.dw(v + 8), arr=P.dw(v + 12))
BCDS = {}
for v, d in CHD.items():
    arr = d['arr']; lst = []
    if P.where(arr) in ('None', 'other') or d['n'] is None or d['n'] > 64:
        d['bcds'] = None; continue
    for j in range(d['n']):
        b = P.dw(arr + 4 * j)
        if b is None: lst = None; break
        lst.append(b)
    d['bcds'] = lst
    for b in (lst or []):
        BCDS[b] = dict(ptd=P.dw(b), ncb=P.dw(b + 4), mdisp=s32(P.dw(b + 8)), chd=v)
ck('A4a CHD 数>0 且 BCD 去重>0', len(CHD) > 900 and len(BCDS) > 2000, (len(CHD), len(BCDS)))

def direct_children(bcds, i):
    """结点 i 的直接子结点下标列表。"""
    out = []; n = len(bcds)
    lim = i + BCDS[bcds[i]]['ncb']
    j = i + 1
    while j <= lim and j < n:
        out.append(j)
        j = j + BCDS[bcds[j]]['ncb'] + 1
    return out

# TD -> 主表 vt 索引（用 pTD 对齐，因为不同 COL 可共享 pTD）
TD2VT = {}
for vt in MAIN: TD2VT[COL[VT[vt]]['ptd']] = vt
ck('P2a pTD 到主表一一对应（954 个不同 pTD）', len(TD2VT) == len(MAIN), (len(TD2VT), len(MAIN)))

cls = collections.Counter(); pairs = []; d2_names = []
for vt_d in MAIN:
    col = COL[VT[vt_d]]; chd = col['pchd']
    d = CHD.get(chd)
    if d is None or d['bcds'] is None: cls['a'] += 1; continue
    bcds = d['bcds']
    if not bcds: cls['b'] += 1; continue
    ch = direct_children(bcds, 0)
    if not ch: cls['b'] += 1; continue
    z = [j for j in ch if BCDS[bcds[j]]['mdisp'] == 0]
    if len(z) != 1: cls['c'] += 1; continue
    bptd = BCDS[bcds[z[0]]]['ptd']
    vt_b = TD2VT.get(bptd)
    if vt_b is None:
        cls['d2'] += 1
        if len(d2_names) < 40: d2_names.append((col['name'], hex(vt_d)))
        continue
    cls['d1'] += 1; pairs.append((vt_d, vt_b))
ck('P2b 四类合计==954', sum(cls.values()) == 954, dict(cls))
print('   P2c (d2) 例: ' + str(d2_names[:10]))

# --- 前缀比较
def cmp_pre(vt_d, vt_b, L=None):
    nd, nb = nslot(vt_d), nslot(vt_b)
    l = min(nd, nb) if L is None else L
    m = 0; mm = []
    for k in range(l):
        a = P.dw(vt_d + 4 * k); b = P.dw(vt_b + 4 * k)
        if a is not None and a == b: m += 1
        else: mm.append(k)
    return m, l, mm, nd, nb

tot_m = tot_l = 0; zero = 0; nz = 0; slotmis = collections.Counter()
ndltnb = 0; slotden = collections.Counter()
for vt_d, vt_b in pairs:
    m, l, mm, nd, nb = cmp_pre(vt_d, vt_b)
    tot_m += m; tot_l += l
    if not mm: zero += 1
    else: nz += 1
    if nd < nb: ndltnb += 1
    for k in range(l): slotden[k] += 1
    for k in mm: slotmis[k] += 1
ck('P3a 配对数 = d1', len(pairs) == cls['d1'], (len(pairs), cls['d1']))
rate = round(100.0 * tot_m / tot_l, 2) if tot_l else 0
print('   P3b 配对=%d 不匹配0的对=%d 不匹配>0的对=%d 总比较槽=%d 总匹配=%d 匹配率=%.2f%%' %
      (len(pairs), zero, nz, tot_l, tot_m, rate))
print('   P3c n_d<n_b 的配对数=%d' % ndltnb)
top = slotmis.most_common(25)
print('   P3d 不匹配最多槽号 Top25 (槽号, 不匹配配对数, 该槽分母):')
for k, v in top: print('        %-4d %-5d %-5d' % (k, v, slotden[k]))
ck('P3e 槽0 不匹配数', True, (slotmis.get(0, 0), slotden.get(0, 0)))
ck('P3f 槽1 不匹配数', True, (slotmis.get(1, 0), slotden.get(1, 0)))
ck('P3g 槽2 不匹配数', True, (slotmis.get(2, 0), slotden.get(2, 0)))

# 反控 R2 打乱配对
shuf = []
for i, (vt_d, _) in enumerate(pairs):
    shuf.append((vt_d, MAIN[(i * 137 + 11) % len(MAIN)]))
sm = sl = 0
for vt_d, vt_b in shuf:
    m, l, mm, nd, nb = cmp_pre(vt_d, vt_b); sm += m; sl += l
srate = round(100.0 * sm / sl, 2) if sl else 0
print('   R2 打乱配对匹配率=%.2f%% (真实 %.2f%%)' % (srate, rate))
ck('R2a 打乱匹配率显著低于真实', srate < rate - 20, (srate, rate))
# 反控 R3 L-1
m1 = l1 = 0
for vt_d, vt_b in pairs:
    nd, nb = nslot(vt_d), nslot(vt_b); l = min(nd, nb) - 1
    if l <= 0: continue
    m, _, _, _, _ = cmp_pre(vt_d, vt_b, l); m1 += m; l1 += l
print('   R3 L-1 匹配率=%.2f%%' % (round(100.0 * m1 / l1, 2) if l1 else 0))
ck('R3a L-1 匹配率 >= 真实（末槽多为真实现）', (100.0 * m1 / l1 if l1 else 0) >= rate - 1, True)

json.dump(dict(cls=dict(cls), pairs=[[hex(a), hex(b)] for a, b in pairs],
               zero=zero, nz=nz, tot_l=tot_l, tot_m=tot_m, rate=rate, shuf_rate=srate,
               slotmis={str(k): [v, slotden[k]] for k, v in slotmis.items()},
               ndltnb=ndltnb, d2_names=d2_names, asserts=N, fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r199/m1_pair.json', 'w'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
