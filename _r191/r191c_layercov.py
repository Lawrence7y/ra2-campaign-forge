#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R191 补充：四档宿主的"层覆盖集合"逐类摊开（把"为什么无副表"落成可核对的数据）。

不猜语义。只回答一个可以用磁盘数据直接核对的问题：
  对每一条 tier 条目（宿主类 X 有一个 mdisp=k 的基类子对象，k in {172,176,240,248}），
  X 自己的表组实际覆盖了哪些 mdisp？k 在不在里面？
并把同类对照（layer 条目）用同一形状摊开，作为对称反控。
"""
import sys, os, struct, collections, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '_r185'))
import pe185 as P

fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

TEXT = P.B['.text']; LO = TEXT['lo']; HI = TEXT['hi_file']
def in_text(x): return x is not None and LO <= x < HI

def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n

COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1) or w[i + 2] != 0: continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
        nm = P.cstr(w[i + 3] + 8, 200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base + 4 * i] = dict(mdisp=w[i + 1], ptd=w[i + 3], pchd=w[i + 4],
                                 name=nm.decode('latin1'))
VT = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL:
            VT[base + 4 * i] = P.dw(base + 4 * i - 4)
def nslot(vt):
    k = 0
    while in_text(P.dw(vt + 4 * k)): k += 1
    return k
NS = {vt: nslot(vt) for vt in VT}
group = collections.defaultdict(list)
for vt in sorted(VT): group[COL[VT[vt]]['name']].append(vt)
ck('S0 基线 COL=1214/VT=1214/槽=14044/组=954/多表组=94',
   (len(COL), len(VT), sum(NS.values()), len(group),
    sum(1 for v in group.values() if len(v) > 1)) == (1214, 1214, 14044, 954, 94))

# 每个名字组的 mdisp 集合
gmd = {nm: sorted(COL[VT[vt]]['mdisp'] for vt in lst) for nm, lst in group.items()}
# 每组有几张表 == 几个 mdisp（一一对应？）
ck('S1 每组 mdisp 个数 == 组内表数（无重复 mdisp）',
   all(len(gmd[nm]) == len(group[nm]) for nm in group))
# 每组 mdisp 是否 0..k 里选出的层偏移子集
LAY = {0, 4, 8, 12, 24, 36, 40, 44, 1728, 21784}
ck('S2 所有组的 mdisp 取值都落在 10 个层偏移内',
   all(set(v) <= LAY for v in gmd.values()),
   sorted({m for v in gmd.values() for m in v}))

TIERS = (172, 176, 240, 248)
tier = []; layer = []
for colva, c in COL.items():
    nb = P.dw(c['pchd'] + 8); arr = P.dw(c['pchd'] + 12)
    for j in range(nb):
        b = P.dw(arr + 4 * j)
        mm = P.dw(b + 8)
        td = P.dw(b)
        nm = P.cstr(td + 8, 120)
        rec = dict(owner=c['name'], ptd=td, tdname=(nm.decode('latin1') if nm else None),
                   mdisp=mm, col=colva)
        if mm in TIERS: tier.append(rec)
        elif mm in LAY and mm != 0: layer.append(rec)
ck('S3 tier 62 条 / layer 5240 条', (len(tier), len(layer)) == (62, 5240),
   (len(tier), len(layer)))

# 按 (宿主类, mdisp) 去重后摊开——这才是"每个类少了几张表"的真实分母
tier_u = sorted({(r['owner'], r['mdisp'], r['tdname']) for r in tier})
layer_u = sorted({(r['owner'], r['mdisp'], r['tdname']) for r in layer})
ck('S4 tier 去重后 (宿主,mdisp,基类) 组合数（实测记录）', True, len(tier_u))
print('S5 tier 去重组合:')
for o, m, t in tier_u:
    print(f'   {o:34s} mdisp={m:5d} base={t:32s} 该组实际层={gmd[o]}')

# 关键量：tier 的 mdisp 是否出现在宿主自己的层集合里
in_host = sum(1 for o, m, t in tier_u if m in gmd[o])
ck('S6 tier 的 mdisp 出现在宿主自己层集合里的组合数 = 0', in_host == 0, in_host)
# 对称反控：layer 的同形检验必须绝大多数命中
lay_in = sum(1 for o, m, t in layer_u if m in gmd[o])
ck('S7 对称反控：layer 的 mdisp 在宿主层集合里命中的组合数 > 0', lay_in > 0,
   (lay_in, len(layer_u)))
print(f'S8 layer 命中率 = {lay_in}/{len(layer_u)} = {lay_in/len(layer_u):.4f}')

# tier 宿主类一共几个、各自缺哪几档
hosts = sorted({o for o, m, t in tier_u})
print(f'S9 tier 宿主类 {len(hosts)} 个: {hosts}')
missing = {o: sorted(m for oo, m, t in tier_u if oo == o) for o in hosts}
ck('S10 记录各宿主缺的档', True, missing)

# 宿主层集合的规模 vs 全镜像层集合规模
ck('S11 tier 宿主的层集合样本（实测记录）', True, {o: gmd[o] for o in hosts})

# 基类自身是否有独立主表
for t in ('.?AVStageClass@@', '.?AVBounceClass@@', '.?AVFlasherClass@@'):
    ck(f'S12 基类 {t} 自身在册且有主表(mdisp==0)',
       t in gmd and 0 in gmd[t], gmd.get(t))

print(f'\n== SUMMARY ==\n  checks={N}  fails={len(fails)}')
for f in fails: print('  FAIL:', f)
json.dump(dict(tier_unique=len(tier_u), layer_unique=len(layer_u),
               in_host=in_host, layer_in=lay_in,
               hosts=hosts, missing=missing,
               gmd_hosts={o: gmd[o] for o in hosts},
               tier_rows=[[o, m, t] for o, m, t in tier_u],
               checks=N, fails=fails),
          open(os.path.join(HERE, 'r191c.json'), 'w'), indent=1, ensure_ascii=False)
sys.exit(1 if fails else 0)
