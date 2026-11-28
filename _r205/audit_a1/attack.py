#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205-AUDIT-A1 独立复核：只读，重写自己的判据再对一次数。
判据变体：
  VA = 纯字段模式（不约束 sig）：dw(c+8)==0 且 pTD 在 .data 且 name 以 .?A 开头 @@ 结尾 且 pCHD 在 .rdata
  VB = 主会话判据（sig in (0,1,2)）
  VC = vftable 通道（dw(vt) in .text 且 dw(vt-4) 是 VA 记录）-> COL 集合
组内视图顺序用两条独立通道：
  ORDER_VT  = 按视图 COL 自身 vftable 地址（.rdata 地址序）排序
  ORDER_PARS= 复刻主会话 parse()（从组头 vt 起 4 字节步进，遇同类名 COL 切分）
"""
import sys, struct, collections
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P

def s32(v): return struct.unpack('<i', struct.pack('<I', v & 0xFFFFFFFF))[0]
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']
def in_text(x): return x is not None and LO <= x < HI
def isname(p):
    b = P.cstr(p + 8, 400)
    return b is not None and b.startswith(b'.?A') and b.endswith(b'@@')

def scan(allow_sig):
    out = {}
    for sn in ('.rdata', '.data'):
        base, w, n = wv(sn)
        for i in range(n - 4):
            if (w[i] not in allow_sig) if allow_sig else False: continue
            if w[i + 2] != 0: continue
            if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
            if not isname(w[i + 3]): continue
            out[base + 4 * i] = dict(sig=w[i], mdisp=s32(w[i + 1]), cd=w[i + 2],
                                     ptd=w[i + 3], pchd=w[i + 4])
    return out

VA = scan(None); VB = scan((0, 1, 2))
# vftable 通道
VT = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and (base + 4 * i - 4) and P.dw(base + 4 * i - 4) in VA:
            VT[base + 4 * i] = P.dw(base + 4 * i - 4)
VC = set(VT.values())
print('=== P0 段表 / 集合基数 ===')
print('sections:', [(s['name'], hex(s['lo']), s['rawsize'], s['vsize']) for s in P.SECS])
print('VA(纯字段) %d  VB(主会话 sig<=2) %d  VC(vftable 可达 COL) %d' % (len(VA), len(VB), len(VC)))
print('VA==VB 地址集一致:', set(VA) == set(VB), ' VB==VC 地址集一致:', set(VB) == VC)
print('VA 中 sig 分布:', collections.Counter(v['sig'] for v in VA.values()).most_common())
print('VA 中 sig!=0 的条数:', sum(1 for v in VA.values() if v['sig'] != 0))
print('VA 中 cd!=0 条数:', sum(1 for v in VA.values() if v['cd'] != 0))
print('VA 中 mdisp 分布(前8):', collections.Counter(v['mdisp'] for v in VA.values()).most_common(8))
print('VA 中 pTD 段分布:', collections.Counter(P.where(v['ptd']) for v in VA.values()).most_common())
print('VA 中 pCHD 段分布:', collections.Counter(P.where(v['pchd']) for v in VA.values()).most_common())
print('VA 中名字首现重复数: 条数 %d / 唯一名 %d' % (len(VA), len(set(P.cstr(v['ptd'] + 8, 400) for v in VA.values()))))

# 每个 COL 的 vftable 地址（c+24 应为 vt）
COL2VT = collections.defaultdict(list)
for vt, c in VT.items(): COL2VT[c].append(vt)
print('VC 中每 COL 的 vt 个数分布:', collections.Counter(len(v) for v in COL2VT.values()).most_common())
print('COL+24 == vt 的比例: %d/%d' % (sum(1 for c, vs in COL2VT.items() for vt in vs if vt == c + 24), len(VT)))

G = collections.defaultdict(list)
for c, v in VA.items(): G[v['pchd']].append(c)
CHD = sorted(G)
print('\n=== P1 A1: 954 个 pCHD 的 40 字节结构 ===')
def bca(a):
    p = P.dw(a + 12); n = P.dw(a + 8)
    if p is None or P.where(p) != '.rdata' or n is None or n > 64: return None
    return [P.dw(p + 4 * j) for j in range(n)]
TAB = {}
TAB['+0==0'] = sum(1 for a in CHD if P.dw(a) == 0)
TAB['+4 attr'] = collections.Counter(P.dw(a + 4) for a in CHD)
TAB['+8==len(BCA)'] = sum(1 for a in CHD if (bca(a) is not None and P.dw(a + 8) == len(bca(a))))
TAB['+12 pBCA 段'] = collections.Counter(P.where(P.dw(a + 12)) for a in CHD)
TAB['+16 是 VA 记录'] = sum(1 for a in CHD if a + 16 in VA)
TAB['+16 sig==0'] = sum(1 for a in CHD if a + 16 in VA and VA[a + 16]['sig'] == 0)
TAB['+20 mdisp==0'] = sum(1 for a in CHD if a + 16 in VA and VA[a + 16]['mdisp'] == 0)
TAB['+24 cd==0'] = sum(1 for a in CHD if a + 16 in VA and VA[a + 16]['cd'] == 0)
TAB['+28 pTD 段'] = collections.Counter(P.where(P.dw(a + 28)) for a in CHD)
TAB['+32 == 自身 CHD'] = sum(1 for a in CHD if P.dw(a + 32) == a)
TAB['+36 == a+16(COL 自指针)'] = sum(1 for a in CHD if P.dw(a + 36) == a + 16)
TAB['+40 in .text(vftable)'] = sum(1 for a in CHD if in_text(P.dw(a + 40)))
TAB['a+40 在 VT 且映射回 a+16'] = sum(1 for a in CHD if VT.get(a + 40) == a + 16)
for k, v in TAB.items(): print(' ', k, '=', v, '/', len(CHD))
print('  CHD 是否与 COL 地址重叠:', len(set(CHD) & set(VA)))
print('  CHD 是否与内嵌 COL 地址重叠:', len(set(CHD) & set(a + 16 for a in CHD)))
print('  偏移 16/20/24/28 处是 VA 记录的个数:',
      [sum(1 for a in CHD if a + off in VA) for off in (12, 16, 20, 24, 28)])
print('  样例 a=0x%x 原始 11 个 dword:' % CHD[0],
      [hex(P.dw(CHD[0] + 4 * k)) for k in range(11)])
print('  +8 与 BCA 长度不一致的个数:', sum(1 for a in CHD if bca(a) is None or P.dw(a + 8) != len(bca(a))))

print('\n=== P2 A1/A2: 组头/内嵌 COL 集合关系 ===')
HEADS = []
skip = set()
for vt in sorted(VT):
    if vt in skip: continue
    HEADS.append(VT[vt]); skip.add(vt)
    # 复刻 parse 只为了标记被吞伪起点
    hn = P.cstr(VA[VT[vt]]['ptd'] + 8, 400)
    k = 0
    while k < 4000:
        pos = vt + 4 * k; w = P.dw(pos)
        if w is None: break
        if in_text(w): k += 1; continue
        if w in VA and P.cstr(VA[w]['ptd'] + 8, 400) == hn:
            if pos + 4 in VT: skip.add(pos + 4)
            k += 1; continue
        break
EMB = set(a + 16 for a in CHD)
HS = set(HEADS)
print('HEADS %d  EMB %d  交集 %d  差(HEADS-EMB) %d  差(EMB-HEADS) %d'
      % (len(HS), len(EMB), len(HS & EMB), len(HS - EMB), len(EMB - HS)))
diffv = [h for h in HS - EMB if len(G[VA[h]['pchd']]) == 1]
print('  HEADS-EMB 中组内视图数==1 的个数(应为0):', len(diffv))
samev = [h for h in HS & EMB if len(G[VA[h]['pchd']]) > 1]
print('  HEADS 与 EMB 相同但视图数>1 的个数(应为0):', len(samev))
# 每组 mdisp==0 的视图数
z = collections.Counter(sum(1 for c in G[a] if VA[c]['mdisp'] == 0) for a in CHD)
print('  每组 mdisp==0 视图数分布:', z.most_common())
print('  EMB 全部是所在组视图:', sum(1 for a in CHD if a + 16 in G[a]), '/', len(CHD))
print('  EMB 的 mdisp 分布:', collections.Counter(VA[a + 16]['mdisp'] for a in CHD).most_common(3))
# 组头 mdisp 是否为组内最大
mx_ok = 0; mx_bad = []
for a in CHD:
    grp = G[a]
    if len(grp) == 1: continue
    hd = [h for h in HS if VA[h]['pchd'] == a]
    if len(hd) != 1: continue
    h = hd[0]
    m = max(VA[c]['mdisp'] for c in grp)
    if VA[h]['mdisp'] == m: mx_ok += 1
    else: mx_bad.append((a, h, P.cstr(VA[h]['ptd'] + 8, 200).decode('latin1'),
                         [VA[c]['mdisp'] for c in sorted(grp, key=lambda c: COL2VT[c][0])], VA[h]['mdisp'], m))
print('  多视图组 %d 个，其中组头 mdisp==组内最大 的个数 %d，反例 %d 个:'
      % (sum(1 for a in CHD if len(G[a]) > 1), mx_ok, len(mx_bad)))
for r in mx_bad:
    print('    0x%x %s 序列=%s 组头mdisp=%d 组内最大=%d' % (r[0], r[1], r[3], r[5], r[4]))

print('\n=== P2b 40 字节记录的边界证据 ===')
print('  dw(a+36) 分布(前6):', collections.Counter(P.dw(a + 36) for a in CHD).most_common(6))
print('  dw(a+36) 在 .text 个數:', sum(1 for a in CHD if in_text(P.dw(a + 36))))
print('  dw(a+40) 段分布:', collections.Counter(P.where(P.dw(a + 40)) for a in CHD).most_common(5))
print('  a - pBCA 差值分布(前6):',
      collections.Counter(a - (P.dw(a + 12) or 0) for a in CHD).most_common(6))
print('  a+16 的 vt(来自 VTI) 与 a+16+20=a+36 是否相邻: 嵌入COL有vt %d/954'
      % sum(1 for a in CHD if a + 16 in COL2VT))
print('  嵌入COL 的 vt 段分布:', collections.Counter(P.where(COL2VT[a + 16][0]) for a in CHD).most_common())
print('  嵌入COL 的 vt == a+20 的个数(应为0):', sum(1 for a in CHD if COL2VT.get(a + 16, [0])[0] == a + 20))
print('  嵌入COL 的 pTD == CHD+28 的个数(同义反复检验):',
      sum(1 for a in CHD if VA[a + 16]['ptd'] == P.dw(a + 28)), '/954')
d36 = [a for a in CHD if P.dw(a + 36) != 0]
print('  a+36 != 0 的样例:', [(hex(a), hex(P.dw(a + 36)), P.where(P.dw(a + 36))) for a in d36[:5]])
for a in CHD[:3]:
    print('  布局窗口 a=0x%x: %s' % (a, [hex(P.dw(a + 4 * k)) for k in range(-6, 11)]))

print('\n=== P2c 260 个非组头 COL 的定位方式 ===')
nonhead = sorted(set(VA) - HS)
print('  非组头 COL %d 个' % len(nonhead))
print('  非组头 COL 是否都满足 VT[vt-4] 映射: %d' % sum(1 for c in nonhead if c in COL2VT))
print('  非组头 COL 的 mdisp 分布(前6):', collections.Counter(VA[c]['mdisp'] for c in nonhead).most_common(6))
print('  非组头 COL 的 pCHD 组大小分布:', collections.Counter(len(G[VA[c]['pchd']]) for c in nonhead).most_common())

print('\n=== P3 A6: 组内 mdisp 递减（两条独立排序通道）===')
def seq_by_vt(a):
    return [c for c in sorted(G[a], key=lambda c: COL2VT[c][0])]
bad_vt = []; tot_vt = 0
for a in CHD:
    s = seq_by_vt(a)
    for i in range(len(s) - 1):
        tot_vt += 1
        if VA[s[i]]['mdisp'] <= VA[s[i + 1]]['mdisp']:
            bad_vt.append(a)
print('  ORDER_VT: 相邻对总数 %d，非严格递减组数 %d' % (tot_vt, len(bad_vt)))
for a in bad_vt:
    s = seq_by_vt(a)
    h = [x for x in HS if VA[x]['pchd'] == a][0]
    print('    0x%x %s 序列=%s 组头vt=0x%x 视图vt=%s'
          % (a, P.cstr(VA[h]['ptd'] + 8, 200).decode('latin1'),
             [VA[c]['mdisp'] for c in s], COL2VT[h][0], [hex(COL2VT[c][0]) for c in s]))
# parse 通道
bad_ps = 0; tot_ps = 0; parse_mismatch = []
for h in HEADS:
    a = VA[h]['pchd']; vt = COL2VT[h][0]; hn = P.cstr(VA[h]['ptd'] + 8, 400)
    cur = h; views = []; k = 0
    while k < 4000:
        pos = vt + 4 * k; w = P.dw(pos)
        if w is None: break
        if in_text(w): k += 1; continue
        if w in VA and P.cstr(VA[w]['ptd'] + 8, 400) == hn:
            views.append(cur); cur = w; k += 1; continue
        break
    views.append(cur)
    if set(views) != set(G[a]): parse_mismatch.append((a, len(views), len(G[a])))
    for i in range(len(views) - 1):
        tot_ps += 1
        if VA[views[i]]['mdisp'] <= VA[views[i + 1]]['mdisp']: bad_ps += 1
print('  ORDER_PARS: 相邻对总数 %d，非严格递减对 %d' % (tot_ps, bad_ps))
print('  parse 视图集 != 按 vt 排序组集合 的组数(应为0): %d %s' % (len(parse_mismatch), parse_mismatch[:5]))
print('  两通道非递减组集合一致:', sorted(set(bad_vt)) == sorted(set(x[0] for x in parse_mismatch)) or len(bad_vt) == len(set(bad_vt)))

print('\n=== P4 A5: BCA/BCD ===')
BCA = {a: bca(a) for a in CHD}
uniq = set()
for v in BCA.values():
    for x in v:
        if x is not None: uniq.add(x)
allref = [x for v in BCA.values() for x in v]
print('  BCD 去重 %d，引用总数 %d' % (len(uniq), len(allref)))
lay = collections.Counter()
for b in uniq:
    lay[(P.where(P.dw(b)) == '.data', P.where(P.dw(b + 24)) == '.rdata')] += 1
print('  BCD 布局 (pTD 在 .data, +24 pCHD 在 .rdata) 分布:', lay.most_common())
print('  BCD numContained 分布:', collections.Counter(P.dw(b + 4) for b in uniq).most_common(6))
m0 = sorted(b for b in uniq if s32(P.dw(b + 8)) == 0)
own = set(P.dw(a + 28) for a in CHD)
dup = [b for b in m0 if P.dw(b) in own]; extra = [b for b in m0 if P.dw(b) not in own]
print('  mdisp==0 去重 %d = 自有 %d + 非自有 %d' % (len(m0), len(dup), len(extra)))
print('  自有覆盖 pTD 数 %d；有 2 条记录的 pTD:', len(set(P.dw(b) for b in dup)),
      [(hex(t), P.cstr(t + 8, 200).decode('latin1')) for t, c in collections.Counter(P.dw(b) for b in dup).items() if c > 1])
names954 = set(P.cstr(VA[a + 16]['ptd'] + 8, 400).decode('latin1') for a in CHD)
print('  954 类名集大小 %d' % len(names954))
print('  22 条非自有明细:')
refc = collections.Counter(allref)
for b in extra:
    nm = P.cstr(P.dw(b) + 8, 200).decode('latin1')
    print('    0x%x %s 引用=%d 在954名集=%s 在COL.pTD集=%s'
          % (b, nm, refc[b], nm in names954, P.dw(b) in set(v['ptd'] for v in VA.values())))
print('  非自有 .?AU 前缀 %d 条；名字在 954 名集内 %d 条'
      % (sum(1 for b in extra if P.cstr(P.dw(b) + 8, 200).decode('latin1').startswith('.?AU')),
         sum(1 for b in extra if P.cstr(P.dw(b) + 8, 200).decode('latin1') in names954)))
print('  非自有被 BCA 引用总次数 %d；引用它们的类个数 %d'
      % (sum(refc[b] for b in extra), len(set(a for a in CHD if any(x in set(extra) for x in BCA[a])))))
print('  非自有 numContained 分布:', collections.Counter(P.dw(b + 4) for b in extra).most_common())
print('  自有 numContained 分布(前5):', collections.Counter(P.dw(b + 4) for b in dup).most_common(5))

print('\n=== P5 A4: sig 判别力 ===')
print('  COL sig Counter(VA):', collections.Counter(v['sig'] for v in VA.values()).most_common())
print('  若允许 sig 任意值, COL 数仍为 %d（增大=%d）' % (len(VA), len(VA) - len(VB)))
print('  BCD 里是否存在 sig 字段? +12/+16/+20 分布:',
      collections.Counter(P.dw(b + 20) for b in uniq).most_common(4))

print('\n=== P6 A6 地址核对 + 组头独立定义 + 排序依赖性 ===')
CARD = {'.?AVOverlayClass@@': 0x807598, '.?AVSmudgeClass@@': 0x809848, '.?AVTerrainClass@@': 0x80c370}
for a in CHD:
    nm = P.cstr(VA[a + 16]['ptd'] + 8, 200).decode('latin1')
    if nm in CARD:
        grp = sorted(G[a], key=lambda c: COL2VT[c][0])
        print('  %s: CHD=0x%x 卡片地址=0x%x 组内 COL 地址=%s mdisp=%s vt=%s'
              % (nm, a, CARD[nm], [hex(c) for c in grp], [VA[c]['mdisp'] for c in grp],
                 [hex(COL2VT[c][0]) for c in grp]))
        print('     卡片地址落在: 组内COL=%s CHD=%s 组内vt=%s 组内CHD+16=%s'
              % (CARD[nm] in grp, CARD[nm] == a, CARD[nm] in [COL2VT[c][0] for c in grp],
                 CARD[nm] in [c + 16 for c in grp]))
# 组头的独立定义：每组 vt 最小的视图
IND = set()
for a in CHD:
    IND.add(min(G[a], key=lambda c: COL2VT[c][0]))
print('  独立定义(min vt/组) 得到的组头 %d 个；与 parse 组头集一致: %s；差集 %d'
      % (len(IND), IND == HS, len(IND ^ HS)))
print('  parse 组头 == 组内 min-vt 视图 的个数 %d/954' % len(HS & IND))
# 排序依赖性：三种排序各有多少非递减对
for label in ('vt_asc', 'vt_desc', 'addr_asc', 'mdisp_desc'):
    bad = 0; tot = 0
    for a in CHD:
        grp = G[a]
        if label == 'vt_asc': s = sorted(grp, key=lambda c: COL2VT[c][0])
        elif label == 'vt_desc': s = sorted(grp, key=lambda c: -COL2VT[c][0])
        elif label == 'addr_asc': s = sorted(grp)
        else: s = sorted(grp, key=lambda c: -VA[c]['mdisp'])
        for i in range(len(s) - 1):
            tot += 1
            if VA[s[i]]['mdisp'] <= VA[s[i + 1]]['mdisp']: bad += 1
    print('  排序 %-9s 相邻对 %d 非严格递减对 %d' % (label, tot, bad))
# 异常 mdisp
odd = sorted([(VA[c]['mdisp'], hex(c), P.cstr(VA[c]['ptd'] + 8, 200).decode('latin1'))
              for c in VA if VA[c]['mdisp'] > 40], key=lambda x: -x[0])
print('  mdisp>40 的 COL 记录 %d 条:' % len(odd))
for r in odd: print('    mdisp=%d @%s %s' % r)
# dw(a+36) 语义探测
s36 = set(P.dw(a + 36) for a in CHD if P.dw(a + 36))
print('  dw(a+36) 非零 %d 个唯一值；落在 CHD 集合 %d，落在 COL 集合 %d，落在 vt 集合 %d'
      % (len(s36), len(s36 & set(CHD)), len(s36 & set(VA)), len(s36 & set(VT))))
print('  dw(a+40) 落在 vt 集合 %d，落在 COL 集合 %d' % (sum(1 for a in CHD if P.dw(a + 40) in VT),
                                                     sum(1 for a in CHD if P.dw(a + 40) in VA)))
print('  954 CHD 排序相邻间距分布(前8):',
      collections.Counter(CHD[i + 1] - CHD[i] for i in range(len(CHD) - 1)).most_common(8))
print('  间距==36 / 40 的个数: %d / %d' % (sum(1 for i in range(len(CHD) - 1) if CHD[i + 1] - CHD[i] == 36),
                                          sum(1 for i in range(len(CHD) - 1) if CHD[i + 1] - CHD[i] == 40)))
# A2: 内嵌 COL 是否在 1214 视图集内、是否唯一 mdisp==0
print('  EMB ⊂ VA: %d/954；组内 mdisp==0 计数==1: %d/954；该唯一条 == CHD+16: %d/954'
      % (sum(1 for a in CHD if a + 16 in VA),
         sum(1 for a in CHD if sum(1 for c in G[a] if VA[c]['mdisp'] == 0) == 1),
         sum(1 for a in CHD if [c for c in G[a] if VA[c]['mdisp'] == 0] == [a + 16])))

print('\n=== P7 卡片地址 0x807598/0x809848/0x80c370 到底是什么 ===')
for va in (0x807598, 0x809848, 0x80c370):
    w0 = [P.dw(va + 4 * k) for k in range(8)]
    print('  va=0x%x 段=%s 前8dword=%s 是COL=%s 是CHD=%s 是vt=%s'
          % (va, P.where(va), [hex(x) if x else '0' for x in w0],
             va in VA, va in set(CHD), va in VT))
    if va in VA:
        print('     -> COL name=%s mdisp=%d pchd=0x%x'
              % (P.cstr(VA[va]['ptd'] + 8, 200).decode('latin1'), VA[va]['mdisp'], VA[va]['pchd']))
    for a in CHD:
        if a - 8 <= va <= a + 48:
            print('     -> 距 CHD 0x%x 的偏移 %+d (类名 %s)'
                  % (a, va - a, P.cstr(VA[a + 16]['ptd'] + 8, 200).decode('latin1')))
    for c in VA:
        if c - 8 <= va <= c + 28:
            print('     -> 距 COL 0x%x 的偏移 %+d (mdisp=%d 类名 %s)'
                  % (c, va - c, VA[c]['mdisp'], P.cstr(VA[c]['ptd'] + 8, 200).decode('latin1')))
for nm in CARD:
    hit = [(hex(c), VA[c]['mdisp'], hex(VA[c]['pchd']))
           for c in VA if P.cstr(VA[c]['ptd'] + 8, 200).decode('latin1') == nm]
    print('  %s 全部 COL: %s' % (nm, hit))
    ch = [hex(a) for a in CHD if P.cstr(VA[a + 16]['ptd'] + 8, 200).decode('latin1') == nm]
    print('      其 CHD: %s' % ch)

print('\n=== P8 A1 记录边界：+36/+40 语义与前后文 ===')
t36 = [P.dw(a + 36) for a in CHD if P.dw(a + 36)]
print('  dw(a+36) 非零 %d 条，唯一目标 %d，目标在 .rdata %d'
      % (len(t36), len(set(t36)), sum(1 for x in t36 if P.where(x) == '.rdata')))
print('  (a+36)-a 差值分布(前6):', collections.Counter(P.dw(a + 36) - a for a in CHD if P.dw(a + 36)).most_common(6))
tg = sorted(set(t36))[:6]
for t in tg:
    print('    目标 0x%x 段=%s 前6dword=%s' % (t, P.where(t), [hex(P.dw(t + 4 * k) or 0) for k in range(6)]))
print('  dw(a+40) 为 0 的个数:', sum(1 for a in CHD if P.dw(a + 40) == 0))
print('  dw(a+40) 在 .data 的个数 %d；作为 pTD 出现 %d'
      % (sum(1 for a in CHD if P.where(P.dw(a + 40)) == '.data'),
         sum(1 for a in CHD if P.dw(a + 40) in set(v['ptd'] for v in VA.values()))))
print('  a-4 / a-8 / a-12 的段分布:', collections.Counter(P.where(P.dw(a - 4)) for a in CHD).most_common(4),
      collections.Counter(P.where(P.dw(a - 8)) for a in CHD).most_common(4))
print('  a-4 为 0 的个数 %d；a-8 为 0 的个数 %d'
      % (sum(1 for a in CHD if P.dw(a - 4) == 0), sum(1 for a in CHD if P.dw(a - 8) == 0)))
# a+16 处 COL 的 pCHD 回指是唯一自洽证据？检查 a+16 是否被其它 CHD 或结构引用
print('  a+16 是否同时落入任何别的 CHD 的 [a,a+40) 窗口:',
      sum(1 for a in CHD for b in CHD if b != a and b <= a + 16 < b + 40))
print('  CHD[a] 窗口两两重叠计数:',
      sum(1 for i in range(len(CHD) - 1) if CHD[i] + 40 > CHD[i + 1]))
# 若 CHD 只有 16 字节，则 a+16 应属于另一条记录；检查 a+16 是否曾是独立 CHD
print('  a+16 出现在 CHD 集合中的个数:', sum(1 for a in CHD if a + 16 in set(CHD)))
print('  a+16 出现在 COL 集合中的个数:', sum(1 for a in CHD if a + 16 in VA))

print('\n=== P9 A2/A3 独立定义交叉核对 ===')
print('  EMB == 组内 max-vt 视图: %d/954'
      % sum(1 for a in CHD if a + 16 == max(G[a], key=lambda c: COL2VT[c][0])))
print('  组头 == 组内 min-vt 视图: %d/954'
      % sum(1 for a in CHD if [h for h in HS if VA[h]['pchd'] == a][0] == min(G[a], key=lambda c: COL2VT[c][0])))
print('  组头 == 组内 max-mdisp 视图: %d/954'
      % sum(1 for a in CHD if [h for h in HS if VA[h]['pchd'] == a][0] == max(G[a], key=lambda c: VA[c]['mdisp'])))
print('  组头 == 组内 max-addr 视图: %d/954'
      % sum(1 for a in CHD if [h for h in HS if VA[h]['pchd'] == a][0] == max(G[a])))
print('  视图数>1 的组: %d；HEADS-EMB %d；EMB-HEADS %d'
      % (sum(1 for a in CHD if len(G[a]) > 1), len(HS - EMB), len(EMB - HS)))
print('  941 检验：多视图组内是否有重复 mdisp:',
      sum(1 for a in CHD if len(set(VA[c]["mdisp"] for c in G[a])) != len(G[a])))

print('\n=== P10 异常 mdisp 的 5 条是否影响任何计数 ===')
odd5 = [c for c in VA if VA[c]['mdisp'] > 40]
for c in odd5:
    a = VA[c]['pchd']
    print('  0x%x mdisp=%d 名=%s 组大小=%d 组内mdisp=%s 是组头=%s 是EMB=%s'
          % (c, VA[c]['mdisp'], P.cstr(VA[c]['ptd'] + 8, 200).decode('latin1'), len(G[a]),
             [VA[x]['mdisp'] for x in sorted(G[a], key=lambda x: COL2VT[x][0])], c in HS, c == a + 16))
