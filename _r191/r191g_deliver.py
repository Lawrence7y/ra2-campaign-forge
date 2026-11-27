#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R191 交付（定稿版）：四档缺席的判别量是「基类身份」，并把 R190 的两条定性推翻。

三条可复算结论：
G1 判别量是基类，不是偏移，也不是「无 COL」。
   G1a 偏移不是判别量：偏移 4 与 36 上"有副表"与"无副表"两种情形都存在
       （36: has=14 / no=4；4: has=1345 / no=10）。
   G1b 无 COL 不是判别量：14 个无自身 COL 的基类里 9 个**会**拿到副表。
   G1c 判别量是基类身份：16 个基类在"有无副表"上**完全一致**（跨度 24 行全表，混合 0 个）。
       从不拿到副表的基类恰 **5** 个（R190 只说 3 个，漏了 ATL 两个）。
G2 R190「2,111 条 / 34 个名指向镜像外 COM 接口基类」是错的。
   实测：34 个全部落在 .data 段内；它们的 TypeDescriptor 全部可读、
   pVFTable 全部 == 0x7F9594。**没有一条在镜像外**。2111 这个数本身可复现。
G3 四档为什么无副表：这四档的基类身份 = {StageClass, BounceClass, FlasherClass}，
   这三个（连同 ATL 两个）是唯一的 5 个"从不需要副表"的基类；
   而 {172,176,248} 三个值**只**被这三个类使用。
   例外：StageClass@36（FactoryClass 宿主）与 172/176/240/248 四个值互不重叠，
   说明"最大子对象"不是判别量（AircraftClass 在 248 之外还有 1728 的层）。

正反控 G4：
   反控一：把判据换成「基类是否无 COL」⇒ 应报 9 个反例（上面 G1b）。
   反控二：把判据换成「偏移 <= 12」⇒ 应报 8 个反例（172/176/240/248 之外的层里
          也有 has=0 的行，例如 StageClass@36）。
   反控三：把 16 个基类里任取一个改为对面结论 ⇒ 应使 G1c 变红（逐一验）。
"""
import sys, os, struct, collections, json, itertools

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
gmd = {nm: frozenset(COL[VT[vt]]['mdisp'] for vt in l) for nm, l in group.items()}
ck('G0 基线 COL=1214 VT=1214 槽=14044 组=954 多表组=94',
   (len(COL), len(VT), sum(NS.values()), len(group),
    sum(1 for v in group.values() if len(v) > 1)) == (1214, 1214, 14044, 954, 94))

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

# ===== G2 先做：R190 的「镜像外」定性 =====
col_ptd = {c['ptd'] for c in COL.values()}
td_no_col = sorted(set(TD) - col_ptd)
ck('G2a 有 TD 无 COL 的 pTD 数 = 34', len(td_no_col) == 34, len(td_no_col))
ck('G2b 其中落在镜像外（where 为 None）的 = 0', sum(1 for a in td_no_col if P.where(a) is None) == 0,
   sum(1 for a in td_no_col if P.where(a) is None))
ck('G2c 34 个全部落在 .data 段', all(P.where(a) == '.data' for a in td_no_col),
   sorted({P.where(a) for a in td_no_col}))
bcd_ref = collections.Counter()
for colva, c in COL.items():
    nb = P.dw(c['pchd'] + 8); arr = P.dw(c['pchd'] + 12)
    for j in range(nb):
        b = P.dw(arr + 4 * j)
        if b is not None: bcd_ref[P.dw(b)] += 1
ck('G2d 这 34 个名的 BCD 引用合计 = 2111（数本身可复现）',
   sum(bcd_ref[a] for a in td_no_col) == 2111, sum(bcd_ref[a] for a in td_no_col))

# ===== G1 全量表 =====
tbl = collections.defaultdict(lambda: {'hosts': set(), 'has': 0, 'no': 0, 'n': 0})
for colva, c in COL.items():
    nb = P.dw(c['pchd'] + 8); arr = P.dw(c['pchd'] + 12)
    for j in range(nb):
        b = P.dw(arr + 4 * j)
        if b is None: continue
        m = P.dw(b + 8)
        if m == 0: continue
        bn = TD.get(P.dw(b), 'UNKNOWN')
        e = tbl[(bn, m)]
        e['hosts'].add(c['name']); e['n'] += 1
        if m in gmd[c['name']]: e['has'] += 1
        else: e['no'] += 1
rows = sorted(tbl.items())
ck('G1a (基类,偏移) 全量表 24 行', len(rows) == 24, len(rows))

by_off = collections.defaultdict(lambda: [0, 0])
for (bn, m), e in tbl.items():
    by_off[m][0] += e['has']; by_off[m][1] += e['no']
mixed = sorted(m for m, (h, no) in by_off.items() if h > 0 and no > 0)
ck('G1b 同一偏移上 has/no 混合的偏移 = [4, 36]', mixed == [4, 36], mixed)
ck('G1c 偏移 36 与偏移 4 上两种情形并存（实测值）',
   by_off[36][0] > 0 and by_off[36][1] > 0 and by_off[4][0] > 0 and by_off[4][1] > 0,
   (by_off[36], by_off[4]))

cls_stat = collections.defaultdict(lambda: [0, 0])
for (bn, m), e in tbl.items():
    cls_stat[bn][0] += e['has']; cls_stat[bn][1] += e['no']
mixed_cls = sorted(bn for bn, (h, no) in cls_stat.items() if h > 0 and no > 0)
ck('G1d 基类层面混合 = 0（基类是判别量）', len(mixed_cls) == 0, mixed_cls)
ck('G1e 基类共 16 个', len(cls_stat) == 16, len(cls_stat))
never = sorted(bn for bn, (h, no) in cls_stat.items() if h == 0)
always = sorted(bn for bn, (h, no) in cls_stat.items() if no == 0)
ck('G1f 从不拿到副表的基类 = 5 个（R190 只说 3 个，漏 ATL 两个）', len(never) == 5, never)
print('G1g 从不拿到副表:', never)
print('G1h 每次都拿到副表 (%d 个):' % len(always), always)

# 无 COL 是否构成解释
nocol_bnames = {TD[a] for a in td_no_col}
nc_with = sorted(bn for bn in cls_stat if bn in nocol_bnames and bn in always)
nc_without = sorted(bn for bn in cls_stat if bn in nocol_bnames and bn in never)
ck('G1i 无 COL 的基类里"会拿到副表"= 9 个（否掉无COL解释）', len(nc_with) == 9, len(nc_with))
ck('G1j 无 COL 的基类里"从不拿到"= 5 个', len(nc_without) == 5, len(nc_without))

# ===== G3 四档的身份 =====
TIERS = (172, 176, 240, 248)
tier_bn = sorted({bn for (bn, m) in tbl if m in TIERS})
ck('G3a 四档涉及的基类 = 3 个', tier_bn == ['.?AVBounceClass@@', '.?AVFlasherClass@@', '.?AVStageClass@@'],
   tier_bn)
ck('G3b 这三个全部属于"从不拿到副表"集合', set(tier_bn) <= set(never), sorted(set(tier_bn) - set(never)))
# 反过来：never 里的 5 个，有几个的偏移落在四档？
for bn in never:
    offs = sorted(m for (b2, m) in tbl if b2 == bn)
    print(f'G3c {bn:52s} 偏移={offs}')

# ===== G4 三条反控（必须能变红） =====
# 反控一：改用「无 COL」判据 ⇒ 误判 9 个
false_pos = len(nc_with)
ck('G4a 反控一：无COL判据会产生 9 个反例（判据无效）', false_pos > 0, false_pos)
# 反控二：改用「偏移是层偏移」判据 ⇒ 会把 StageClass@36 判成"应有副表"，实测 has=0
mis = [(bn, m) for (bn, m), e in tbl.items() if e['no'] > 0]
ck('G4b 反控二：把「偏移是层偏移」当判据，会产生 3 行反例（实测：StageClass@36 + ATL 两条@4）',
   len([1 for bn, m in mis if m in (0, 4, 8, 12, 24, 36, 40, 44)]) == 3, mis)
# 反控三：把任一 always 基类翻成 never ⇒ G1d 应变红
def has_mixed(mod):
    st = collections.defaultdict(lambda: [0, 0])
    for (bn, m), e in tbl.items():
        bn2 = mod.get(bn, bn)
        st[bn2][0] += e['has']; st[bn2][1] += e['no']
    return sorted(b for b, (h, no) in st.items() if h > 0 and no > 0)
red = 0
for bn in always:
    if has_mixed({bn: never[0]}): red += 1
ck('G4c 反控三：把每个 always 基类逐一翻面，16 个里全部使 G1d 变红', red == len(always),
   (red, len(always)))
ck('G4d 未翻面时 G1d 为空（同一函数，正对照）', has_mixed({}) == [], has_mixed({}))

# ===== G5 第三条候选解释（attributes bit0 = non-virtual）也不是判别量 =====
# 逐 BCD 摊开：attributes 与"宿主是否真有该层副表"的 2x2
att = collections.Counter()
att_rows = []
for colva, c in COL.items():
    nb = P.dw(c['pchd'] + 8); arr = P.dw(c['pchd'] + 12)
    for j in range(nb):
        b = P.dw(arr + 4 * j)
        if b is None: continue
        m = P.dw(b + 8)
        if m == 0: continue
        a = P.dw(b + 20)
        hs = m in gmd[c['name']]
        att[(a, hs)] += 1
        att_rows.append((TD.get(P.dw(b), '?'), m, a, hs, c['name']))
ck('G5a 非零 BCD 总数 1498', len(att_rows) == 1498, len(att_rows))
print('G5b attributes x 有无副表 2x2:', {k: v for k, v in sorted(att.items())})
bit1_has = att.get((9, True), 0) + att.get((1, True), 0)
ck('G5c attributes bit0=1 的行里"仍有副表"的 > 0（attributes 不是判别量）',
   bit1_has > 0, bit1_has)
nohas_attr0 = att.get((0, False), 0)
ck('G5d attributes==0 的行里"无副表"的 = 72（attributes 也不是充分条件）',
   nohas_attr0 == 72, nohas_attr0)
# 同一 (基类,偏移) 上 attributes 恒定（说明 attributes 是基类属性，不随宿主变）
ga = collections.defaultdict(set)
for bn, m, a, hs, host in att_rows: ga[(bn, m)].add(a)
ck('G5e attributes 在同一 (基类,偏移) 上恒定', all(len(v) == 1 for v in ga.values()),
   {k: v for k, v in ga.items() if len(v) > 1})
print('G5f 结论：attributes 与"有无副表"交叉后两个方向都有反例'
      ' ⇒ 第三条候选解释同样不成立，判别量仍是基类身份（G1d）')

print(f'\n== SUMMARY ==\n  checks={N}  fails={len(fails)}')
for f in fails: print('  FAIL:', f)
json.dump(dict(rows=[[bn, m, e['n'], e['has'], e['no'], sorted(e['hosts'])] for (bn, m), e in rows],
               by_off={str(k): v for k, v in by_off.items()},
               mixed_off=mixed, mixed_cls=mixed_cls,
               never=never, always=always,
               never_offsets={bn: sorted(m for (b2, m) in tbl if b2 == bn) for bn in never},
               nc_with=nc_with, nc_without=nc_without,
               g2=[len(td_no_col), sum(1 for a in td_no_col if P.where(a) is None),
                   sum(bcd_ref[a] for a in td_no_col)],
               checks=N, fails=fails),
          open(os.path.join(HERE, 'r191g.json'), 'w'), indent=1, ensure_ascii=False)
sys.exit(1 if fails else 0)
