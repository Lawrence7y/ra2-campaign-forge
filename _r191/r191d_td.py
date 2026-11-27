#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R191 交付：R190「2,111 条 / 34 个名指向镜像外 COM 接口基类」这条定性被推翻 ——
它们全部在镜像内、TD 可读、只是没有 COL（无独立 vtable 的基类）。

测量：
T1 TD（TypeDescriptor）全量扫描（.data + .rdata，判据 pVFTable==0x7F9594），
   与 1,214 条 COL 的 pTD 集合做三向比对（有COL有TD / 有COL无TD / 有TD无COL）
T2 「有TD无COL」的那批名字，逐个给 TD 地址 + 所在段 + BCD 引用数
T3 反面判据：这批 pTD 是否真的"镜像外"（where() 是否 None）——R190 的原话检验
T4 对称反控：随便挑 30 条"有COL"的 pTD，同判据必须给出同结论（在镜像内）
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
ck('T0 COL 记录 1214 条', len(COL) == 1214, len(COL))

# ---- T1 TD 全量扫描 ----
VF = 0x7F9594
TD = {}
for sn in ('.data', '.rdata'):
    base, w, n = wv(sn)
    for i in range(n - 2):
        if w[i] != VF: continue
        va = base + 4 * i
        nm = P.cstr(va + 8, 160)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        TD[va] = nm.decode('latin1')
ck('T1a TD 记录数（pVFTable==0x7F9594 且 name 合式）', True, len(TD))
col_ptd = {c['ptd'] for c in COL.values()}
ck('T1b COL 引用的不同 pTD 数（实测记录）', True, len(col_ptd))
ck('T1c COL 引用的 pTD 全部落在 TD 集合内 1214/1214', col_ptd <= set(TD),
   len(col_ptd - set(TD)))
td_no_col = sorted(set(TD) - col_ptd)
ck('T1d 有 TD 但无 COL 的 pTD 数（实测记录）', True, len(td_no_col))
ck('T1e 有 TD 但无 COL 的名字数 = 34', len({TD[a] for a in td_no_col}) == 34,
   len({TD[a] for a in td_no_col}))

# ---- T3 「镜像外」这条原话的检验 ----
outside = [a for a in td_no_col if P.where(a) is None]
ck('T3a 这批 pTD 中"落在镜像外"的条数 = 0（R190 的"镜像外"不成立）',
   len(outside) == 0, len(outside))
segs = collections.Counter(P.where(a) for a in td_no_col)
ck('T3b 它们全部落在镜像内某段（实测分布）', sum(segs.values()) == len(td_no_col), dict(segs))

# ---- T2 每个无 COL 的名字：TD 地址 + 段 + BCD 引用数 ----
refs = collections.Counter()
bcd_total = 0
for colva, c in COL.items():
    nb = P.dw(c['pchd'] + 8); arr = P.dw(c['pchd'] + 12)
    for j in range(nb):
        b = P.dw(arr + 4 * j)
        if b is None: continue
        bcd_total += 1
        refs[P.dw(b)] += 1
ck('T2a 基础类描述符总数 5302', bcd_total == 5302, bcd_total)
rows = [(TD[a], a, P.where(a), refs.get(a, 0)) for a in td_no_col]
rows.sort(key=lambda r: -r[3])
print('T2b 无 COL 的 TD（名 / TD地址 / 段 / 被 BCD 引用数）:')
for nm, a, s, r in rows:
    print(f'   {nm:40s} {hex(a):10s} {str(s):8s} refs={r}')
ref_sum = sum(r[3] for r in rows)
ck('T2c 这 34 个名的 BCD 引用合计（实测记录）', True, ref_sum)
ck('T2d 引用合计 = 2111（R190 报的 2111 条就是它们）', ref_sum == 2111, ref_sum)

# ---- T4 对称反控 ----
sample = sorted(col_ptd)[:30]
ck('T4a 对称反控：有 COL 的 pTD 前 30 条全部落在镜像内',
   all(P.where(a) is not None for a in sample), [P.where(a) for a in sample][:6])

# ---- T5 这些类有没有自己的子对象（即它们是真类还是纯接口标签） ----
# 有 TD 无 COL ⇒ 没有 vtable ⇒ 不可能有"独立副表"。这条是本轮对四档的解释基础。
ck('T5a 无 COL 的名字里含 StageClass/BounceClass/FlasherClass 三个',
   all(t in {TD[a] for a in td_no_col}
       for t in ('.?AVStageClass@@', '.?AVBounceClass@@', '.?AVFlasherClass@@')))
# 反向：所有"被当作基类且 mdisp 落在四档"的 pTD，是否全部属于"无 COL"集合
TIERS = (172, 176, 240, 248)
tier_ptd = set()
for colva, c in COL.items():
    nb = P.dw(c['pchd'] + 8); arr = P.dw(c['pchd'] + 12)
    for j in range(nb):
        b = P.dw(arr + 4 * j)
        if b is None: continue
        if P.dw(b + 8) in TIERS: tier_ptd.add(P.dw(b))
ck('T5b 四档基类的 pTD 集合大小（实测记录）', True, len(tier_ptd))
ck('T5c 四档的 pTD 全部属于"无 COL"集合（这是四档无副表的直接原因）',
   tier_ptd <= set(td_no_col), sorted(tier_ptd - set(td_no_col)))
# 但同一集合里也有 layer 档的基类吗？若有，则"无 COL"不是充分解释 —— 必须测
layer_ptd = set()
for colva, c in COL.items():
    nb = P.dw(c['pchd'] + 8); arr = P.dw(c['pchd'] + 12)
    for j in range(nb):
        b = P.dw(arr + 4 * j)
        if b is None: continue
        mm = P.dw(b + 8)
        if mm in (4, 8, 12, 24, 36, 40, 44, 1728, 21784): layer_ptd.add(P.dw(b))
ck('T5d 反向判据：layer 档的基类 pTD 里"有 COL"的占多数（否则解释不成立）',
   len(layer_ptd & col_ptd) > len(layer_ptd) / 2,
   (len(layer_ptd & col_ptd), len(layer_ptd)))
print('T5e layer 档基类 pTD：有COL',
      len(layer_ptd & col_ptd), '/ 总', len(layer_ptd))
print('T5f layer 档里"无 COL"的 pTD:', [TD.get(a, hex(a)) for a in sorted(layer_ptd - col_ptd)])

print(f'\n== SUMMARY ==\n  checks={N}  fails={len(fails)}')
for f in fails: print('  FAIL:', f)
json.dump(dict(cols=len(COL), tds=len(TD), col_ptd=len(col_ptd),
               td_no_col=len(td_no_col), td_no_col_names=len({TD[a] for a in td_no_col}),
               outside=len(outside), segs=dict(segs),
               bcd_total=bcd_total, ref_sum=ref_sum,
               rows=[[nm, hex(a), str(s), r] for nm, a, s, r in rows],
               tier_ptd=len(tier_ptd), tier_in_nocol=len(tier_ptd & set(td_no_col)),
               layer_ptd=len(layer_ptd), layer_with_col=len(layer_ptd & col_ptd),
               layer_no_col=[TD.get(a, hex(a)) for a in sorted(layer_ptd - col_ptd)],
               checks=N, fails=fails),
          open(os.path.join(HERE, 'r191d.json'), 'w'), indent=1, ensure_ascii=False)
sys.exit(1 if fails else 0)
