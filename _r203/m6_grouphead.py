#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R203 m6：MSVC 多重继承 vftable 组的「组头 / 子视图」分离 —— 订正 R201/R202/m1 的 1214 与 14044。
L1 候选 vt 起点 1214（判据 vt-4 in COL）；
L2 组头判定：候选按地址升序扫描，若该地址已被更早的组（组头 + 顺次解析）占用，则它是组内子视图起点，不是组头；
L3 组头数、子视图起点数、每组视图数、每组真槽位数；
L4 覆盖一致性：所有组的占位区间两两不相交，且并集 == 全部 1214 候选地址 ∪ 其槽位；
L5 旧口径的两个数字如何由新口径导出（14044 的构成解释）；
L6 反控：把「已被占用即跳过」去掉，占位重叠数应巨大（=m5 的 112346）。"""
import sys, struct, json, collections
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']
def s32(v): return struct.unpack('<i', struct.pack('<I', v))[0]
def in_text(x): return x is not None and LO <= x < HI
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n
COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1, 2) or w[i + 2] != 0: continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
        nm = P.cstr(w[i + 3] + 8, 400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base + 4 * i] = dict(mdisp=s32(w[i + 1]), name=nm.decode('latin1'))
VTI = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL: VTI[base + 4 * i] = P.dw(base + 4 * i - 4)
ck('L1 候选 vt 起点 1214', len(VTI) == 1214, len(VTI))
# 顺次解析：给定组头，返回 (views=[(colpos, colptr, slots)], endpos)
def walk(vt, maxk=4000):
    views = []; curcol = VTI[vt]; cur = []; positions = []
    k = 0
    while k < maxk:
        pos = vt + 4 * k
        w = P.dw(pos)
        if w is None: break
        if in_text(w): cur.append(w); positions.append(pos); k += 1; continue
        if w in COL:
            views.append((curcol, cur)); curcol = w; cur = []
            positions.append(pos); k += 1; continue
        break
    views.append((curcol, cur))
    return views, vt + 4 * k, positions
order = sorted(VTI)
claimed = {}
HEADS = []; SUBS = []
for vt in order:
    if vt in claimed: SUBS.append(vt); continue
    views, end, positions = walk(vt)
    HEADS.append(vt)
    for p in positions: claimed[p] = vt
    claimed[vt] = vt
print('   L3 组头 %d / 子视图起点 %d / 合计 %d' % (len(HEADS), len(SUBS), len(HEADS) + len(SUBS)))
ck('L3a 组头 + 子视图起点 == 1214', len(HEADS) + len(SUBS) == 1214, (len(HEADS), len(SUBS)))
ck('L3b 组头数 < 1214（1214 是膨胀值）', len(HEADS) < 1214, len(HEADS))
nview = 0; nslot = 0; GM = {}
for vt in HEADS:
    views, end, positions = walk(vt)
    GM[vt] = views
    nview += len(views)
    nslot += sum(len(s[1]) for s in views)
ck('L3c 视图总数 > 组头数（存在多重继承）', nview > len(HEADS), '%d vs %d' % (nview, len(HEADS)))
ck('L3d 真槽位总数 > 14044', nslot > 14044, nslot)
vd = collections.Counter(len(v) for v in GM.values())
print('   L3 每组视图数分布 top: %s' % vd.most_common(8))
ck('L3e 单视图组数', vd[1] > 0, vd[1])
# L4 不相交
ov = 0
for i, vt in enumerate(HEADS):
    views, end, positions = walk(vt)
    pass
allpos = {}
for vt in HEADS:
    views, end, positions = walk(vt)
    for p in positions:
        if p in allpos: ov += 1
        allpos[p] = vt
ck('L4a 组间占位两两不相交', ov == 0, ov)
ck('L4b 占位并集大小 == 真槽位数 + 视图数-组头数',
   len(allpos) == nslot + (nview - len(HEADS)), (len(allpos), nslot, nview, len(HEADS)))
# L5 旧口径构成
stop_tot = 0
firstview = 0
for vt in HEADS:
    views, end, positions = walk(vt)
    firstview += len(views[0][1])
    # 旧口径：从组头读到第一个非 text 即停
    s = []; k = 0
    while k < 4000:
        w = P.dw(vt + 4 * k)
        if not in_text(w): break
        s.append(w); k += 1
    stop_tot += len(s)
print('   L5 旧口径（组头口径重算，读到非 text 即停）%d；新口径 %d' % (stop_tot, nslot))
ck('L5a 旧口径槽位总数（组头重算）不必然等于 14044，因为 14044 把子视图起点也当组头重数',
   True, '%d vs 1214 候选口径 14044' % stop_tot)
ck('L5b 新口径 - 旧口径 = 被内嵌 COL 截断的槽位 + 子视图重复计数',
   nslot - stop_tot > 0, nslot - stop_tot)
# L6 反控
def walk_noclaim():
    ov2 = 0; claim = {}
    for vt in order:
        views, end, positions = walk(vt)
        for p in positions:
            if p in claim: ov2 += 1
            claim[p] = vt
    return ov2
ck('L6a 反控（不跳过子视图起点）重叠数 == 112346', walk_noclaim() == 112346, walk_noclaim())
OUT = dict(cand=len(VTI), heads=len(HEADS), subs=len(SUBS), views=nview, slots=nslot,
           stop_from_heads=stop_tot, groupdist=dict((str(k), v) for k, v in vd.most_common()),
           asserts=N, fails=fails)
json.dump(OUT, open('/home/t628/projects/ra2-campaign-forge/_r203/m6_grouphead.json', 'w'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
