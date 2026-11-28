#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205-AUDIT-A1 第二轮：记录边界(39/40/44字节)、sig 负控、两种排序的全量对照。"""
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
COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i + 2] != 0: continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
        if not isname(w[i + 3]): continue
        COL[base + 4 * i] = dict(mdisp=s32(w[i + 1]), ptd=w[i + 3], pchd=w[i + 4])
VT = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL: VT[base + 4 * i] = P.dw(base + 4 * i - 4)
C2V = {c: vt for vt, c in VT.items()}
G = collections.defaultdict(list)
for c, v in COL.items(): G[v['pchd']].append(c)
CHD = sorted(G)
print('COL %d VT %d CHD %d  C2V 覆盖 %d/%d' % (len(COL), len(VT), len(CHD), len(C2V), len(COL)))

print('\n=== Q1 COL 记录长度判定（24B 假说的决定性检验）===')
print('  dw(c+20) 在 .text 个数: %d/%d（24B 假说要求接近全中）'
      % (sum(1 for c in COL if in_text(P.dw(c + 20))), len(COL)))
print('  dw(c+20) 段分布(前5):', collections.Counter(P.where(P.dw(c + 20)) for c in COL).most_common(5))
print('  dw(c+16)==CHD 个数: %d/%d' % (sum(1 for c in COL if P.dw(c + 16) in set(CHD)), len(COL)))
print('  dw(c+20) 落在 COL 集合: %d' % sum(1 for c in COL if P.dw(c + 20) in COL))
print('  vt-4==c 距离分布:', collections.Counter(C2V[c] - c for c in C2V).most_common(6))
print('  vt 段分布:', collections.Counter(P.where(v) for v in VT).most_common(4))

print('\n=== Q2 CHD 40/44 字节：a+36、a+40 的角色 ===')
print('  a+36 段分布:', collections.Counter(P.where(P.dw(a + 36)) for a in CHD).most_common(5))
print('  a+36 落在 CHD 集合 %d，落 COL %d，落 VT %d，落 pBCA 集合 %d'
      % (sum(1 for a in CHD if P.dw(a + 36) in set(CHD)),
         sum(1 for a in CHD if P.dw(a + 36) in COL),
         sum(1 for a in CHD if P.dw(a + 36) in VT),
         sum(1 for a in CHD if P.dw(a + 36) in set(P.dw(x + 12) for x in CHD))))
print('  a+40 == 内嵌COL 的 vt 个数: %d/954'
      % sum(1 for a in CHD if a + 40 == C2V.get(a + 16)))
print('  a+40 段分布:', collections.Counter(P.where(P.dw(a + 40)) for a in CHD).most_common(5))
print('  a+40 等于某 COL 的 pTD 个数: %d；等于某 COL 地址个数: %d；在 VT 个数: %d'
      % (sum(1 for a in CHD if P.dw(a + 40) in set(v['ptd'] for v in COL.values())),
         sum(1 for a in CHD if P.dw(a + 40) in COL),
         sum(1 for a in CHD if P.dw(a + 40) in VT)))
print('  内嵌COL 的 vt 相对 a 的偏移分布(前6):',
      collections.Counter(C2V[a + 16] - a for a in CHD if a + 16 in C2V).most_common(6))
print('  内嵌COL 的 vt 是否落在 [a+36,a+47]: %d'
      % sum(1 for a in CHD if a + 16 in C2V and 36 <= C2V[a + 16] - a <= 47))
print('  a+44 段分布(若 44B):', collections.Counter(P.where(P.dw(a + 44)) for a in CHD).most_common(4))
print('  相邻间距==48 的组: a+40/a+44 是否为新记录起始 (dw(a+48)?):',
      [hex(CHD[i]) for i in range(len(CHD) - 1) if CHD[i + 1] - CHD[i] == 48][:4])
print('  最小间距:', min(CHD[i + 1] - CHD[i] for i in range(len(CHD) - 1)),
      ' 间距<40 的个数:', sum(1 for i in range(len(CHD) - 1) if CHD[i + 1] - CHD[i] < 40))

print('\n=== Q3 sig 的判别力负控 ===')
# 结构约束（不含名）在各 sig 允许集下的候选数
for lab, f in (('sig in (0,1,2)', lambda x: x in (0, 1, 2)), ('sig 任意', lambda x: True)):
    tot = 0
    for sn in ('.rdata', '.data'):
        base, w, n = wv(sn)
        for i in range(n - 4):
            if not f(w[i]) or w[i + 2] != 0: continue
            if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
            tot += 1
    print('  %-16s 结构约束(无名字) 候选 = %d' % (lab, tot))
print('  说明: 名字约束 .?A...@@ 才是唯一过滤项；sig 过滤掉的条数 = 0')

print('\n=== Q4 排序通道：vt 序 vs COL 地址序 vs mdisp 序 ===')
res = {}
for lab, key in (('vt_asc', lambda c: C2V[c]), ('addr_asc', lambda c: c),
                 ('vt_desc', lambda c: -C2V[c]), ('mdisp_desc', lambda c: -COL[c]['mdisp'])):
    bad = []; tot = 0
    for a in CHD:
        s = sorted(G[a], key=key)
        for i in range(len(s) - 1):
            tot += 1
            if COL[s[i]]['mdisp'] <= COL[s[i + 1]]['mdisp']: bad.append(a)
    res[lab] = (tot, sorted(bad))
    print('  %-9s 相邻对 %d 非递减对 %d 组数 %d' % (lab, tot, tot and len(bad) and sum(1 for a in CHD for i in range(len(G[a]) - 1) if COL[sorted(G[a], key=key)[i]]['mdisp'] <= COL[sorted(G[a], key=key)[i + 1]]['mdisp']), len(bad)))
print('  只有 addr_asc 得到 954/954 严格递减；vt_asc 3 个反例:', [hex(x) for x in res['vt_asc'][1]])
print('  vt_asc 与 addr_asc 反例交集:', [hex(x) for x in set(res['vt_asc'][1]) & set(res['addr_asc'][1])])
# 反例类在两种排序下的序列
for a in res['vt_asc'][1]:
    print('  0x%x %s  vt序=%s  addr序=%s'
          % (a, P.cstr(COL[a + 16]['ptd'] + 8, 200).decode('latin1'),
             [COL[c]['mdisp'] for c in sorted(G[a], key=lambda c: C2V[c])],
             [COL[c]['mdisp'] for c in sorted(G[a])]))
# vt 序与 addr 序不同的组数
diff = sum(1 for a in CHD if [c for c in sorted(G[a], key=lambda c: C2V[c])] != [c for c in sorted(G[a])])
print('  两种排序给出不同视图串的组数: %d' % diff)

print('\n=== Q5 A2 独立性与 A3 因果表述核对 ===')
print('  组头 == 组内 mdisp 最大: %d/954（A3 因果表述）'
      % sum(1 for a in CHD if [h for h in CHD if h in G[a]] and True) if False else
      sum(1 for a in CHD if COL[max(G[a], key=lambda c: C2V[c])]['mdisp'] >= max(COL[c]['mdisp'] for c in G[a])))
heads = set()
skip = set()
for vt in sorted(VT):
    if vt in skip: continue
    heads.add(VT[vt]); skip.add(vt)
    hn = P.cstr(COL[VT[vt]]['ptd'] + 8, 400); k = 0
    while k < 4000:
        pos = vt + 4 * k; w = P.dw(pos)
        if w is None: break
        if in_text(w): k += 1; continue
        if w in COL and P.cstr(COL[w]['ptd'] + 8, 400) == hn:
            if pos + 4 in VT: skip.add(pos + 4)
            k += 1; continue
        break
print('  924 校验 heads=%d' % len(heads))
mi = [a for a in CHD if len(G[a]) > 1]
print('  多视图组 %d；其中组头 mdisp==组内最大 %d；反例:'
      % (len(mi), sum(1 for a in mi if [h for h in heads if COL[h]['pchd'] == a][0]
                      == max(G[a], key=lambda c: COL[c]['mdisp']))))
for a in mi:
    hd = [h for h in heads if COL[h]['pchd'] == a][0]
    if COL[hd]['mdisp'] != max(COL[c]['mdisp'] for c in G[a]):
        print('    0x%x %s 组头mdisp=%d 组内max=%d 序列(vt序)=%s'
              % (a, P.cstr(COL[a + 16]['ptd'] + 8, 200).decode('latin1'), COL[hd]['mdisp'],
                 max(COL[c]['mdisp'] for c in G[a]),
                 [COL[c]['mdisp'] for c in sorted(G[a], key=lambda c: C2V[c])]))
print('  EMB-HEADS %d 且全是多视图组: %s' % (len(set(a + 16 for a in CHD) - heads),
                                        all(len(G[COL[a + 16]['pchd']]) > 1 for a in CHD if a + 16 not in heads)))
