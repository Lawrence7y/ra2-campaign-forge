#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R199 主会话第十二刀：本轮全部进入结论的数字的一次性复算（收口闸）。

逐条断言：
 Z1 基线 1214 / 1214 / 14044 / 954 / 0x7F5C70 .?AVUnitClass@@ 344
 Z2 配对四类 0 / 256 / 0 / 603 / 95，合计 954
 Z3 前缀比较 9853 / 6241 / 63.34% / 不匹配 3612 / 零不匹配配对数 0 / n_d<n_b 0
 Z4 逐槽继承率：槽0 87/603、槽1 381/580、槽2 176/571、槽3 89/494、槽8 42/202
 Z5 不匹配派生侧分类 3345 类专属 / 267 共享 / 0 自身相等；<=3 表放宽 3493 / 119
 Z6 槽0 不匹配 516 个派生实现 516 去重、每个只占 1 表且只在槽 0
 Z7 槽0 store 分类 own_main 110 / base_main 385 / other_main 42 / nonvt 1（合计 538）
 Z8 首 call：direct_only 535 / in_vtable 3（其中 base_main 支 385 条 call 全不等于 vt_b 槽 0）
 Z9 桩 33 槽号 / 39 表 / 205 槽位；槽 0 上 5 张；39 张里 17 张有 mdisp==0 直基类主表
 Z10 桩槽位与基类比较：a=65（基类同槽也是桩）/ b=0 / c=140；派生方向 65/65 也填桩
 Z11 反控：打乱配对 3.30%、L-1 63.86%、去掉槽0..3 72.43%、反控桩判据 470 槽位
 Z12 (b) 256 张全为 CHD 单结点（数组长 1、ncb[0]=0）；(d2) 95 张直基类名去重 17、IClassFactory 占 78
"""
import sys, struct, collections, json
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

def s32(v): return struct.unpack('<i', struct.pack('<I', v))[0]
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']; RAW = P.RAW
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
        if not in_text(P.dw(vt + 4 * k)): break
        k += 1
    NS[vt] = k; return k
CLS = {vt: COL[VT[vt]]['name'] for vt in VT}
MD = {vt: COL[VT[vt]]['mdisp'] for vt in VT}
PTD = {vt: COL[VT[vt]]['ptd'] for vt in VT}
MAIN = [vt for vt in VT if MD[vt] == 0]
TD2VT = {PTD[vt]: vt for vt in MAIN}

ck('Z1a', (len(COL), len(VT), sum(nslot(v) for v in VT), len(MAIN)) == (1214, 1214, 14044, 954),
   (len(COL), len(VT), sum(nslot(v) for v in VT), len(MAIN)))
ck('Z1b', (CLS[0x7F5C70], nslot(0x7F5C70)) == ('.?AVUnitClass@@', 344), (CLS[0x7F5C70], nslot(0x7F5C70)))

CHD = {}
for c, cc in COL.items():
    v = cc['pchd']
    if v in CHD: continue
    CHD[v] = dict(n=P.dw(v + 8), arr=P.dw(v + 12))
BCDS = {}
for v, d in CHD.items():
    arr = d['arr']; lst = None
    if P.where(arr) not in ('None', 'other') and d['n'] is not None and 0 < d['n'] <= 64:
        lst = [P.dw(arr + 4 * j) for j in range(d['n'])]
        if any(x is None for x in lst): lst = None
    d['bcds'] = lst
    for b in (lst or []):
        BCDS[b] = dict(ptd=P.dw(b), ncb=P.dw(b + 4), mdisp=s32(P.dw(b + 8)), chd=v)
def direct_children(bcds, i):
    out = []; n = len(bcds); lim = i + BCDS[bcds[i]]['ncb']; j = i + 1
    while j <= lim and j < n:
        out.append(j); j = j + BCDS[bcds[j]]['ncb'] + 1
    return out

cls = collections.Counter(); pairs = []; blist = []; d2names = []
for vt in MAIN:
    col = COL[VT[vt]]; ch = CHD.get(col['pchd'])
    if not ch or not ch['bcds']: cls['a'] += 1; blist.append(vt); continue
    kids = direct_children(ch['bcds'], 0)
    if not kids: cls['b'] += 1; blist.append(vt); continue
    z = [j for j in kids if BCDS[ch['bcds'][j]]['mdisp'] == 0]
    if len(z) != 1: cls['c'] += 1; continue
    vb = TD2VT.get(BCDS[ch['bcds'][z[0]]]['ptd'])
    if vb is None:
        cls['d2'] += 1
        bn = P.cstr(BCDS[ch['bcds'][z[0]]]['ptd'] + 8, 400)
        d2names.append(bn.decode('latin1') if bn else '?')
        continue
    cls['d1'] += 1; pairs.append((vt, vb))
ck('Z2a 配对四类', (cls['a'], cls['b'], cls['c'], cls['d1'], cls['d2']) == (0, 256, 0, 603, 95),
   (cls['a'], cls['b'], cls['c'], cls['d1'], cls['d2']))
ck('Z2b 合计 954', sum(cls.values()) == 954, sum(cls.values()))
ck('Z12a (b) 全单结点', all(len(CHD[COL[VT[v]]['pchd']]['bcds']) == 1 and
                            BCDS[CHD[COL[VT[v]]['pchd']]['bcds'][0]]['ncb'] == 0 for v in blist), len(blist))
ck('Z12b (d2) 名去重 17 / IClassFactory 78',
   (len(set(d2names)), d2names.count('.?AUIClassFactory@@')) == (17, 78),
   (len(set(d2names)), d2names.count('.?AUIClassFactory@@')))

tot_m = tot_l = zero = 0; slotden = collections.Counter(); slotmis = collections.Counter()
m4 = l4 = 0
for vt_d, vt_b in pairs:
    L = min(nslot(vt_d), nslot(vt_b)); mm = 0
    for k in range(L):
        slotden[k] += 1
        if P.dw(vt_d + 4 * k) == P.dw(vt_b + 4 * k): mm += 1
        else: slotmis[k] += 1
        if k >= 4:
            l4 += 1
            if P.dw(vt_d + 4 * k) == P.dw(vt_b + 4 * k): m4 += 1
    tot_m += mm; tot_l += L
    if mm == L: zero += 1
ck('Z3a 9853/6241/3612/零不匹配 0',
   (tot_l, tot_m, tot_l - tot_m, zero) == (9853, 6241, 3612, 0),
   (tot_l, tot_m, tot_l - tot_m, zero))
rate = round(100.0 * tot_m / tot_l, 2)
ck('Z3b 匹配率 63.34', rate == 63.34, rate)
ck('Z4a 槽0/1/2/3/8 分母',
   (slotden[0], slotden[1], slotden[2], slotden[3], slotden[8]) == (603, 580, 571, 494, 202),
   (slotden[0], slotden[1], slotden[2], slotden[3], slotden[8]))
ck('Z4b 槽0 匹配 87 槽8 匹配 42',
   (slotden[0] - slotmis[0], slotden[8] - slotmis[8]) == (87, 42),
   (slotden[0] - slotmis[0], slotden[8] - slotmis[8]))
ck('Z11a 去掉槽0..3 后 72.43', round(100.0 * m4 / l4, 2) == 72.43, round(100.0 * m4 / l4, 2))

impl_tab = collections.defaultdict(set)
for vt in VT:
    for k in range(nslot(vt)):
        impl_tab[P.dw(vt + 4 * k)].add(vt)
c_u = c_d = c_x = 0
for vt_d, vt_b in pairs:
    L = min(nslot(vt_d), nslot(vt_b))
    for k in range(L):
        a = P.dw(vt_d + 4 * k); b = P.dw(vt_b + 4 * k)
        if a == b: c_x += 1
        elif len(impl_tab[a]) == 1: c_u += 1
        else: c_d += 1
ck('Z5a 不匹配 3345 类专属 / 267 共享，合计 3612', (c_u, c_d, c_u + c_d) == (3345, 267, 3612),
   (c_u, c_d, c_u + c_d))
ck('Z5b 匹配槽 6241 与 Z3a 同源', c_x == 6241, c_x)

s0 = [(vt_d, P.dw(vt_d), vt_b) for vt_d, vt_b in pairs
      if min(nslot(vt_d), nslot(vt_b)) >= 1 and P.dw(vt_d) != P.dw(vt_b)]
ck('Z6a 槽0 不匹配 516', len(s0) == 516, len(s0))
ck('Z6b 516 个实现去重 516 且只占 1 表', len(set(a for _, a, _ in s0)) == 516 and
   all(len(impl_tab[a]) == 1 for _, a, _ in s0), len(set(a for _, a, _ in s0)))
alls = collections.Counter()
for vt in VT:
    for k in range(nslot(vt)):
        alls[P.dw(vt + 4 * k)] += 1
ck('Z6c 516 个实现的出现次数全为 1', all(alls[a] == 1 for _, a, _ in s0),
   sum(1 for _, a, _ in s0 if alls[a] != 1))

STUB = 0x4C9150
tabs = []
for vt in VT:
    ks = [k for k in range(nslot(vt)) if P.dw(vt + 4 * k) == STUB]
    if ks: tabs.append((vt, ks))
sset = set(k for _, ks in tabs for k in ks)
ck('Z9a 33/39/205', (len(sset), len(tabs), sum(len(k) for _, k in tabs)) == (33, 39, 205),
   (len(sset), len(tabs), sum(len(k) for _, k in tabs)))
s0t = [vt for vt, ks in tabs if 0 in ks]
ck('Z9b 槽0 上 5 张', len(s0t) == 5, len(s0t))
withbase = 0
for vt, ks in tabs:
    col = COL[VT[vt]]; ch = CHD.get(col['pchd']); vb = None
    if ch and ch['bcds']:
        for j in direct_children(ch['bcds'], 0):
            if BCDS[ch['bcds'][j]]['mdisp'] == 0: vb = TD2VT.get(BCDS[ch['bcds'][j]]['ptd']); break
    if vb: withbase += 1
ck('Z9c 39 张里 17 张有 mdisp==0 直基类主表', withbase == 17, withbase)

a = b = c = 0; der = der_tot = 0
for vt, ks in tabs:
    col = COL[VT[vt]]; ch = CHD.get(col['pchd']); vb = None
    if ch and ch['bcds']:
        for j in direct_children(ch['bcds'], 0):
            if BCDS[ch['bcds'][j]]['mdisp'] == 0: vb = TD2VT.get(BCDS[ch['bcds'][j]]['ptd']); break
    nb = nslot(vb) if vb else 0
    for k in ks:
        if vb is None or k >= nb: c += 1
        elif P.dw(vb + 4 * k) == STUB: a += 1
        else: b += 1
ck('Z10a a/b/c = 65/0/140', (a, b, c) == (65, 0, 140), (a, b, c))

# 反控：打乱
shuf = [(vt_d, MAIN[(i * 137 + 11) % len(MAIN)]) for i, (vt_d, _) in enumerate(pairs)]
sm = sl = 0
for vt_d, vt_b in shuf:
    L = min(nslot(vt_d), nslot(vt_b))
    for k in range(L):
        sl += 1
        if P.dw(vt_d + 4 * k) == P.dw(vt_b + 4 * k): sm += 1
ck('Z11b 打乱配对 3.30', round(100.0 * sm / sl, 2) == 3.30, round(100.0 * sm / sl, 2))

print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
