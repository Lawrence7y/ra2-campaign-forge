#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R191 定性刀：为什么 {172,176,240,248} 四档没有副表 —— 反面判据把两条候选解释都否掉，
再用"同一基类在不同宿主里是否都缺席"这条判别性检验收口。

候选解释一（R190 隐含）：基类没有 COL / 指向镜像外 ⇒ 无独立 vtable ⇒ 无副表。
   已被 T5d 否掉：12 个无 COL 的基类（含 StageClass）在 layer 档 4/8/12 上**确实有副表**。
候选解释二：宿主类的层集合就是"基类链上实际声明了虚函数的那几层"。检验方式：
   对每个 tier 条目，看宿主自己有没有**别的**层含有同一个基类（不是同一偏移 pTD）。
判别性检验（本轮的核心）：
   E1 tier 基底类（StageClass/BounceClass/FlasherClass）在**有 COL 的宿主**里，
      是否也一律缺席？如果一律缺席 ⇒ 这是基类自身属性，与宿主无关。
   E2 该基底类在 layer 档的基类里有没有出现（ControlVirtualBase 类）？
      若出现过且有副表 ⇒ 「同一基类有时有副表有时没有」⇒ 缺席不是基类属性，是偏移属性。
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
gmd = {nm: sorted(COL[VT[vt]]['mdisp'] for vt in lst) for nm, lst in group.items()}
ck('E0 基线', (len(COL), len(VT), sum(NS.values()), len(group)) == (1214, 1214, 14044, 954))

# 全量 BCD：谁把谁当基类、在什么偏移
bases = collections.defaultdict(list)   # pTD -> [(owner_name, mdisp)]
for colva, c in COL.items():
    nb = P.dw(c['pchd'] + 8); arr = P.dw(c['pchd'] + 12)
    for j in range(nb):
        b = P.dw(arr + 4 * j)
        if b is None: continue
        bases[P.dw(b)].append((c['name'], P.dw(b + 8)))

VF = 0x7F9594
TD = {}
for sn in ('.data', '.rdata'):
    base, w, n = wv(sn)
    for i in range(n - 2):
        if w[i] != VF: continue
        va = base + 4 * i
        nm = P.cstr(va + 8, 160)
        if nm and nm.startswith(b'.?A') and nm.endswith(b'@@'):
            TD[va] = nm.decode('latin1')

TIERS = {172, 176, 240, 248}
tier_base = sorted({TD.get(ptd, hex(ptd)) for ptd, lst in bases.items()
                    if any(m in TIERS for _, m in lst)})
print('E1 四档对应的基底类:', tier_base)

# E1 对每个基底类：它在全镜像被引用时，偏移取值分布
for nm in tier_base:
    ptd = [k for k, v in TD.items() if v == nm][0]
    offs = collections.Counter(m for _, m in bases[ptd])
    owners = sorted({o for o, _ in bases[ptd]})
    print(f'E2 {nm}: 被引用 {len(bases[ptd])} 次，偏移分布 {dict(offs)}，宿主 {len(owners)} 个')
    ck(f'E2 {nm} 的偏移全在四档内（即从不以 layer 偏移出现）',
       set(offs) <= TIERS, sorted(set(offs) - TIERS))

# E3 反过来：layer 档（4/8/12/24/36/40/44/1728/21784）上的基底类有哪些
layer_bases = collections.Counter()
for ptd, lst in bases.items():
    if any(m in (4, 8, 12, 24, 36, 40, 44, 1728, 21784) for _, m in lst):
        layer_bases[TD.get(ptd, hex(ptd))] += 1
print('E3 layer 档基底类（前 20）:', layer_bases.most_common(20))
ck('E3 记录 layer 档基底类个数', True, len(layer_bases))

# E4 判别刀：存在「同一个基底类在 layer 档出现且宿主有副表」的类吗？
ok_pair = []
for ptd, lst in bases.items():
    for owner, m in lst:
        if m in (4, 8, 12, 24, 36, 40, 44, 1728, 21784) and m in gmd.get(owner, []):
            ok_pair.append((TD.get(ptd), owner, m))
ck('E4 同一基底类在 layer 档、且宿主确有该层副表的组合数 > 0', len(ok_pair) > 0, len(ok_pair))
# 与四档对照：四档里有「宿主确有该层副表」的吗
bad_pair = [(TD.get(ptd), owner, m) for ptd, lst in bases.items()
            for owner, m in lst if m in TIERS and m in gmd.get(owner, [])]
ck('E5 四档里"宿主确有该层副表"的组合数 = 0', len(bad_pair) == 0, len(bad_pair))

# E6 四档宿主的层集合内容（把缺席落成可核对数据）
hosts = sorted({o for ptd, lst in bases.items() for o, m in lst if m in TIERS})
print('E6 四档宿主:', hosts)
for h in hosts:
    print(f'   {h:34s} layers={gmd[h]}')
ck('E7 四档宿主的层集合里最大元素 <= 12 以外的都是 1728',
   all(set(gmd[h]) <= {0, 4, 8, 12, 1728} for h in hosts),
   {h: gmd[h] for h in hosts})

# E8 四档基类的 TD 是否有 vtable（TD.pVFTable 已是 type_info，看 COL 存在性即可）
no_col = set(TD) - {c['ptd'] for c in COL.values()}
ck('E8 四档基底类全部无 COL（无自己的 vtable）',
   all([k for k, v in TD.items() if v == nm][0] in no_col for nm in tier_base))
# 但 layer 档里也有无 COL 的基底类且确有副表 —— 这是"无 COL 不构成解释"的硬证
layer_nocol = sorted({TD.get(ptd) for ptd, lst in bases.items()
                      if ptd in no_col and any(m in (4, 8, 12, 24, 36, 40, 44) for _, m in lst)})
print('E9 layer 档里"无 COL 但有副表"的基底类:', layer_nocol)
ck('E9 这类基底类个数 > 0（硬证：无 COL 不等于无副表）', len(layer_nocol) > 0, len(layer_nocol))
for nm in layer_nocol[:4]:
    ptd = [k for k, v in TD.items() if v == nm][0]
    for owner, m in bases[ptd][:3]:
        got = any(COL[VT[v]]['mdisp'] == m for v in group[owner])
        print(f'   {nm} 作为 {owner} 的基类 @mdisp={m} → 宿主有该层副表: {got}')
        ck(f'E10 {nm}@{m} in {owner} 有副表', got)

print(f'\n== SUMMARY ==\n  checks={N}  fails={len(fails)}')
for f in fails: print('  FAIL:', f)
json.dump(dict(tier_base=tier_base, layer_bases_top=layer_bases.most_common(20),
               ok_pairs=len(ok_pair), bad_pairs=len(bad_pair),
               hosts={h: gmd[h] for h in hosts},
               layer_nocol=layer_nocol, checks=N, fails=fails),
          open(os.path.join(HERE, 'r191e.json'), 'w'), indent=1, ensure_ascii=False)
sys.exit(1 if fails else 0)
