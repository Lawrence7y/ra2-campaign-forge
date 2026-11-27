#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R191 主会话复算 v2（规则 D：执行员 #462 与我的 v1 各错，逐条用原始字节裁定）。

裁定三件事：
V1 BCD 结构尺寸 24 B、attributes 在 +20（用"自项 BCD 之后紧跟基类数组"这一
   结构事实作硬证，而不是引用规范）
V2 1,013 个直接槽的聚集结构（槽级 vs 出现级两个口径分开算，避免混淆）
V3 attributes 是否能解释 {172,176,240,248} 四档（反例计数 + 结论）
V4 缺席是结构性的还是类特有的（判别性检验：同一 pTD 在别的派生类里有没有副表）
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

def wview(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n

COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wview(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1) or w[i + 2] != 0: continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
        nm = P.cstr(w[i + 3] + 8, 200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base + 4 * i] = dict(mdisp=w[i + 1], ptd=w[i + 3], pchd=w[i + 4],
                                 name=nm.decode('latin1'))
VT = {}
for sn in ('.rdata', '.data'):
    base, w, n = wview(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL:
            VT[base + 4 * i] = P.dw(base + 4 * i - 4)
def nslot(vt):
    k = 0
    while in_text(P.dw(vt + 4 * k)): k += 1
    return k
NS = {vt: nslot(vt) for vt in VT}
ck('V0 基线条数 COL=1214 / VT=1214 / 槽=14044',
   (len(COL), len(VT), sum(NS.values())) == (1214, 1214, 14044),
   (len(COL), len(VT), sum(NS.values())))
group = collections.defaultdict(list)
for vt in sorted(VT): group[COL[VT[vt]]['name']].append(vt)

# ---------------- V1 BCD 结构 24 B / attributes@+20 ----------------
# 结构硬证一：基类数组的 [0] 恒等于"自项 BCD"（1214/1214）
evid = 0; evid_tot = 0
for colva, c in COL.items():
    pchd = c['pchd']; arr = P.dw(pchd + 12)
    nb = P.dw(pchd + 8)
    selfbcd = None
    for j in range(nb):
        b = P.dw(arr + 4 * j)
        if b is not None and P.dw(b) == c['ptd'] and P.dw(b + 8) == 0:
            selfbcd = b; break
    evid_tot += 1
    if selfbcd is not None and P.dw(arr) == selfbcd:
        evid += 1
ck('V1a 基类数组[0] == 自项BCD 1214/1214', evid == 1214 and evid_tot == 1214,
   (evid, evid_tot))

# 结构硬证二：相邻 BCD 的地址差（在连续分配处）实测步长 24，不是 20
step = collections.Counter()
for colva, c in COL.items():
    nb = P.dw(c['pchd'] + 8); arr = P.dw(c['pchd'] + 12)
    addrs = [P.dw(arr + 4 * j) for j in range(nb)]
    for a, b2 in zip(addrs, addrs[1:]):
        if a and b2: step[b2 - a] += 1
neg24 = step[-24]
ck('V1b 相邻 BCD 地址差为 -24 的出现次数 = 2879（步长 24 的证据）', neg24 == 2879, neg24)
print('V1b2 相邻 BCD 地址差 Top5:', step.most_common(5))

# 正对照：把 +20 与 +24 各当 attributes，看哪个落在 62 条 tier 上都稳定可读、
# 哪个在多数类上等于"另一个对象的内容"（越界的标志）
v20 = collections.Counter(); v24 = collections.Counter()
for colva, c in COL.items():
    nb = P.dw(c['pchd'] + 8); arr = P.dw(c['pchd'] + 12)
    for j in range(nb):
        b = P.dw(arr + 4 * j)
        v20[P.dw(b + 20)] += 1
        v24[P.dw(b + 24)] += 1
ck('V1c +20 取值只有少量小整数（attributes 形态，实测三值）',
   sorted(v20) == [0, 2, 9], dict(v20))
print('V1d +20 分布:', dict(v20), '| +24 分布 Top6:', v24.most_common(6))
ck('V1e +24 取值远大于 attributes 形态（说明越界）', max(v24) > 0x10000, hex(max(v24)))

# 自项 BCD 五字段闭合（正确约束：自项 PMD.mdisp == 0，不是 COL.mdisp）
selfok = 0
for colva, c in COL.items():
    nb = P.dw(c['pchd'] + 8); arr = P.dw(c['pchd'] + 12)
    for j in range(nb):
        b = P.dw(arr + 4 * j)
        if (P.dw(b) == c['ptd'] and P.dw(b + 4) == nb - 1 and P.dw(b + 8) == 0
                and P.dw(b + 12) == 0xFFFFFFFF and P.dw(b + 16) == 0):
            selfok += 1; break
ck('V1e 自项 BCD 五字段闭合 1214/1214', selfok == 1214, selfok)

# ---------------- V2 直接槽聚集（两口径分开） ----------------
def is_adj(va):
    o = P.r2o(va); raw = P.RAW[o:o + 4]
    return (raw[0:3] == b'\x83\x6c\x24' or raw[0:3] == b'\x81\x6c\x24') and raw[3] == 0x04
direct = []; adj = []
for vt in sorted(VT):
    if COL[VT[vt]]['mdisp'] == 0: continue
    for k in range(NS[vt]):
        v = P.dw(vt + 4 * k)
        (adj if is_adj(v) else direct).append((vt, k, v))
ck('V2a 调整器 305 / 直接槽 1013', (len(adj), len(direct)) == (305, 1013), (len(adj), len(direct)))

cnt = collections.Counter(v for _, _, v in direct)
ck('V2b 直接槽目标地址去重 = 278', len(cnt) == 278, len(cnt))
ck('V2c 被 >=2 槽共用的目标 = 47', sum(1 for a, c in cnt.items() if c >= 2) == 47,
   sum(1 for a, c in cnt.items() if c >= 2))
ck('V2d 这 47 个目标吃掉 782 个槽', sum(c for a, c in cnt.items() if c >= 2) == 782,
   sum(c for a, c in cnt.items() if c >= 2))
ck('V2e 复用率 782/1013 = 77.19%', abs(sum(c for a, c in cnt.items() if c >= 2) / 1013 - 0.7719) < 5e-4)
top = cnt.most_common(5)
print('V2f Top5:', [(hex(a), c) for a, c in top])
ck('V2g Top5 用量 = [78,78,78,76,75]', [c for a, c in top] == [78, 78, 78, 76, 75], [c for a, c in top])

# 同槽号匹配（R190 F5 口径）vs 任意槽号匹配（本轮新口径）
def match(vt, k, v, same_index):
    for vt2 in group[COL[VT[vt]]['name']]:
        if vt2 == vt: continue
        rng = [k] if same_index else range(NS[vt2])
        for k2 in rng:
            if k2 < NS[vt2] and P.dw(vt2 + 4 * k2) == v:
                return (vt2, k2)
    return None
si = [(vt, k, v) for vt, k, v in direct if match(vt, k, v, True)]
an = [(vt, k, v) for vt, k, v in direct if match(vt, k, v, False)]
ck('V2h 同槽号匹配 = 0 槽（R190 F5 口径复现）', len(si) == 0, len(si))
ck('V2i 任意槽号匹配 = 1 槽', len(an) == 1, len(an))
if an:
    vt, k, v = an[0]
    print('V2j 唯一命中:', hex(vt), '槽', k, hex(v), COL[VT[vt]]['name'],
          '-> 对方', match(vt, k, v, False))
# 该命中是不是"跨组越界读数"（对方表块是否紧邻本表块）
if an:
    vt, k, v = an[0]; other = match(vt, k, v, False)[0]
    print('V2k 两表是否同组不同块:', hex(vt), hex(other),
          '本表槽数', NS[vt], '对方槽数', NS[other])

# 直接槽值出现在主表的槽（槽级 vs 出现级）
main_hits_slot = 0; main_hits_occ = 0
for vt, k, v in direct:
    hit = False
    for vt2 in VT:
        if COL[VT[vt2]]['mdisp'] != 0: continue
        for k2 in range(NS[vt2]):
            if P.dw(vt2 + 4 * k2) == v:
                main_hits_occ += 1; hit = True
    if hit: main_hits_slot += 1
ck('V2l 直接槽值出现在主表：槽级 1', main_hits_slot == 1, main_hits_slot)
print('V2m 同一槽的出现次数(出现级) =', main_hits_occ)

# ---------------- V3 attributes 能否解释四档 ----------------
TIERS = (172, 176, 240, 248)
LAYERS = (0, 4, 8, 12, 24, 36, 40, 44, 1728, 21784)
tier_bcd = []; layer_bcd = []
for colva, c in COL.items():
    nb = P.dw(c['pchd'] + 8); arr = P.dw(c['pchd'] + 12)
    for j in range(nb):
        b = P.dw(arr + 4 * j)
        mm = P.dw(b + 8); a = P.dw(b + 20)
        td = P.dw(b); nm = P.cstr(td + 8, 120) if td else None
        rec = dict(bcd=b, mdisp=mm, attr=a, ptd=td,
                   tdname=(nm.decode('latin1') if nm else None), owner=c['name'])
        if mm in TIERS: tier_bcd.append(rec)
        elif mm in LAYERS: layer_bcd.append(rec)
ck('V3a tier 条目 62 / layer 条目 5240', (len(tier_bcd), len(layer_bcd)) == (62, 5240),
   (len(tier_bcd), len(layer_bcd)))
ta = collections.Counter(r['attr'] for r in tier_bcd)
la = collections.Counter(r['attr'] for r in layer_bcd)
print('V3b tier attributes:', dict(ta), '| layer attributes:', dict(la))
ck('V3c tier 62/62 attributes == 0', ta == {0: 62}, dict(ta))
ck('V3d layer attributes 分布实测 = {0:4488, 2:740, 9:12}', dict(la) == {0: 4488, 2: 740, 9: 12}, dict(la))
ck('V3e attributes 取值集合 layer 与 tier 的交集非空（都存在 0）', ta[0] > 0 and la[0] > 0,
   (ta[0], la[0]))
print('V3f 判别性检验：tier 62/62 与 layer 4488/5240 都是 attributes==0，'
      '即 attributes 在"有副表"与"无副表"两组上分布几乎相同 ⇒ 不能解释缺席')
# 判别性：若 attributes 能解释缺席，则"无副表"组的 attributes 应显著不同于"有副表"组
ck('V3g attributes 不能解释缺席（两组 0 值占比都 > 85%）',
   ta[0] / len(tier_bcd) > 0.85 and la[0] / len(layer_bcd) > 0.85,
   (round(ta[0] / len(tier_bcd), 4), round(la[0] / len(layer_bcd), 4)))

# ---------------- V4 缺席是结构性还是类特有 ----------------
# 对 tier 每个条目：同一 pTD 是否在**别的**派生类里作为非 0 基类出现，
# 且那个派生类的表组里真的存在 mdisp == 该基类偏移的副表
col_by_ptd = {}
for colva, c in COL.items(): col_by_ptd.setdefault(c['ptd'], []).append(colva)
reuse = []; norese = []
def other_classes_with_sub(rec):
    """与 V4c 完全同一判据：别的派生类里有同 pTD 同 mdisp 的基对象，
    且那个类的表组里真的存在 mdisp == 该偏移的副表。"""
    for colva, c in COL.items():
        if c['name'] == rec['owner']: continue
        nb = P.dw(c['pchd'] + 8); arr = P.dw(c['pchd'] + 12)
        for j in range(nb):
            b = P.dw(arr + 4 * j)
            if P.dw(b) == rec['ptd'] and P.dw(b + 8) == rec['mdisp']:
                has = any(COL[VT[v]]['mdisp'] == rec['mdisp'] for v in group[c['name']])
                if has: return (colva, c['name'], True)
                break
    return None
for r in tier_bcd:
    got = other_classes_with_sub(r)
    (reuse if got else norese).append((r, got))
print('V4a 同类基对象在别的派生类里"有副表"的条目数:', len(reuse))
print('V4b 在别的派生类里也"无副表"或未出现:', len(norese))
ck('V4c 62 条 tier 条目里，能在别的派生类找到同偏移副表的 = 0', len(reuse) == 0, len(reuse))
# 对称反控：同一条判据作用在 layer 上必须能命中（否则判据本身失效）
lhit = sum(1 for r in layer_bcd[:200] if other_classes_with_sub(r))
ck('V4d 对称反控：同一判据用在 layer 前 200 条上命中 > 0', lhit > 0, lhit)

print(f'\n== SUMMARY ==\n  checks={N}  fails={len(fails)}')
for f in fails: print('  FAIL:', f)
json.dump(dict(cols=len(COL), vts=len(VT), slots=sum(NS.values()),
               adj=len(adj), direct=len(direct), uniq=len(cnt), shared=47,
               top=[[hex(a), c] for a, c in top],
               same_index=len(si), any_index=len(an),
               main_slot=main_hits_slot, main_occ=main_hits_occ,
               bcd_evidence=[evid, evid_tot], attr20=dict(v20),
               tier_attr=dict(ta), layer_attr=dict(la),
               tier_n=len(tier_bcd), layer_n=len(layer_bcd),
               v4_reuse=len(reuse), v4_none=len(norese), v4_layerhit=lhit,
               checks=N, fails=fails),
          open(os.path.join(HERE, 'r191a_v2.json'), 'w'), indent=1, ensure_ascii=False)
sys.exit(1 if fails else 0)
