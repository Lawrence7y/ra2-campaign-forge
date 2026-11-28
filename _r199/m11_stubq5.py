#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R199 主会话第十一刀：执行员 B 的 Q5/Q6 结论复算（其主张「39 张表全部无 mdisp==0 直基类」被 m10 测反）。

本刀逐表给出：
 K1 每张含桩表的 mdisp==0 直基类主表 vt_b（用 pTD 对齐），无则标 none。
 K2 每个桩槽位 k 与 vt_b 的比较：k < nslot(vt_b)? 若是，vt_b 在 k 处是什么地址、是否也是桩、
    是否落 .text；若不是，标 out_of_range。
 K3 三分类计数，与执行员 B 报的 a=0/b=0/c=205 对比。
 K4 反向：这些表的派生表（CHD 直接子结点 mdisp==0 的类）在同槽是否填桩。
 K5 若 vt_b 在 k 处有真实现，给出该实现的体首 3 字节，说明基类不是桩。
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
TD2VT = {}
for vt in MAIN: TD2VT[PTD[vt]] = vt

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

STUB = 0x4C9150
tabs = []
for vt in VT:
    ks = [k for k in range(nslot(vt)) if P.dw(vt + 4 * k) == STUB]
    if ks: tabs.append((vt, ks))
ck('K0a 39 张表 / 205 槽位', (len(tabs), sum(len(k) for _, k in tabs)) == (39, 205),
   (len(tabs), sum(len(k) for _, k in tabs)))

a = b = c = 0; rows = []
for vt, ks in tabs:
    col = COL[VT[vt]]; ch = CHD.get(col['pchd'])
    vb = None
    if ch and ch['bcds']:
        for j in direct_children(ch['bcds'], 0):
            if BCDS[ch['bcds'][j]]['mdisp'] == 0:
                vb = TD2VT.get(BCDS[ch['bcds'][j]]['ptd']); break
    nb = nslot(vb) if vb else 0
    det = []
    for k in ks:
        if vb is None or k >= nb:
            c += 1; det.append((k, 'out_of_range' if vb else 'nobase', None))
        else:
            t = P.dw(vb + 4 * k)
            if t == STUB: a += 1; det.append((k, 'stub', hex(t)))
            else: b += 1; det.append((k, 'real', hex(t)))
    rows.append(dict(cls=CLS[vt], vt=hex(vt), n=nslot(vt), base=CLS[vb] if vb else None,
                     nb=nb, det=[(k, s, h) for k, s, h in det]))
print('   K3 三分类: a(基类同槽也是桩)=%d  b(基类同槽真实现)=%d  c(基类无对应槽/无基类)=%d （执行员报 0/0/205）'
      % (a, b, c))
ck('K3a a+b+c == 205', a + b + c == 205, (a, b, c))
ck('K3b 有基类且基类同槽是真实实现的槽位 > 0（推翻执行员 c=205）', b > 0, b)
print('   K1/K2 逐表:')
for r in rows:
    print('        %-42s vt=%s n=%-3d 基类=%-40s nb=%-3d 桩槽=%s'
          % (r['cls'], r['vt'], r['n'], str(r['base'])[:40], r['nb'], [(k, s) for k, s, _ in r['det']][:8]))
ck('K1a 39 张里有 mdisp==0 直基类主表的张数 > 0', sum(1 for r in rows if r['base']) > 0,
   sum(1 for r in rows if r['base']))

# K5 基类同槽真实现的体首 3 字节
addr = collections.Counter()
for vt, ks in tabs:
    col = COL[VT[vt]]; ch = CHD.get(col['pchd']); vb = None
    if ch and ch['bcds']:
        for j in direct_children(ch['bcds'], 0):
            if BCDS[ch['bcds'][j]]['mdisp'] == 0:
                vb = TD2VT.get(BCDS[ch['bcds'][j]]['ptd']); break
    if not vb: continue
    for k in ks:
        if k < nslot(vb): addr[P.dw(vb + 4 * k)] += 1
print('   K5 基类同槽实现地址分布: %s' % [(hex(x), v, RAW[P.r2o(x):P.r2o(x) + 3].hex() if P.r2o(x) else '?') for x, v in addr.most_common(10)])
ck('K5a 基类同槽实现地址去重数', True, len(addr))

# K4 派生方向
der = 0; der_tot = 0
for vt, ks in tabs:
    col = COL[VT[vt]]; ch = CHD.get(col['pchd'])
    if not ch or not ch['bcds']: continue
    kids = []
    n = len(ch['bcds']); j = 1
    while j <= BCDS[ch['bcds'][0]]['ncb'] and j < n:
        kids.append(j); j = j + BCDS[ch['bcds'][j]]['ncb'] + 1
    for j in kids:
        if BCDS[ch['bcds'][j]]['mdisp'] != 0: continue
        vk = TD2VT.get(BCDS[ch['bcds'][j]]['ptd'])
        if not vk: continue
        for k in ks:
            if k < nslot(vk):
                der_tot += 1
                if P.dw(vk + 4 * k) == STUB: der += 1
print('   K4 派生表同槽填桩: %d/%d' % (der, der_tot))
ck('K4a 派生方向样本数 >= 0', der_tot >= 0, der_tot)

json.dump(dict(a=a, b=b, c=c, rows=rows,
               base_slot_impls=[[hex(x), v] for x, v in addr.most_common(20)],
               der=[der, der_tot], asserts=N, fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r199/m11_stubq5.json', 'w'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
