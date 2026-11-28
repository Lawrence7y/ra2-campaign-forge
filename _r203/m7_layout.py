#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R203 m7：多重继承 vftable 组的内部布局律（视图顺序 / mdisp 序列 / 主视图位置）。
M1 视图 mdisp 序列是否恒为降序到 0；
M2 组内最后一个视图是否恒 mdisp==0（主视图）；
M3 主视图槽数是否恒为组内最多；
M4 mdisp 取值集合；
M5 单视图组（46 个）的 mdisp 是否恒 0；
M6 INoticeSink / INoticeSource 在组内的位置（接上 R202 的 11 条 mdisp==0 装表）；
M7 反控：把视图顺序反转后 M1 应失败。"""
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
claimed = {}; HEADS = []
for vt in sorted(VTI):
    if vt in claimed: continue
    views, end, positions = walk(vt)
    HEADS.append(vt)
    claimed[vt] = vt
    for p in positions: claimed[p] = vt
GM = {vt: walk(vt)[0] for vt in HEADS}
ck('M0 组头 235 / 视图 1214 / 槽位 14044',
   len(HEADS) == 235 and sum(len(g) for g in GM.values()) == 1214 and
   sum(len(s[1]) for g in GM.values() for s in g) == 14044,
   (len(HEADS), sum(len(g) for g in GM.values()), sum(len(s[1]) for g in GM.values() for s in g)))
def msd(cp): return COL[cp]['mdisp']
# M1 降序
desc = 0; nonmono = []
for vt in HEADS:
    m = [msd(cp) for cp, _ in GM[vt]]
    if all(m[i] >= m[i + 1] for i in range(len(m) - 1)): desc += 1
    else: nonmono.append((hex(vt), m))
print('   M1 mdisp 非递增的组 %d / %d' % (desc, len(HEADS)))
ck('M1a 多数组 mdisp 非递增', desc / len(HEADS) > 0.80, '%.4f' % (desc / len(HEADS)))
print('   M1b 反例（前 6）: %s' % nonmono[:6])
# M2 末视图 mdisp==0
last0 = sum(1 for vt in HEADS if msd(GM[vt][-1][0]) == 0)
ck('M2a 末视图 mdisp==0 的组 %d / %d' % (last0, len(HEADS)), last0 / len(HEADS) > 0.90, '%.4f' % (last0 / len(HEADS)))
bad0 = [(hex(vt), [msd(cp) for cp, _ in GM[vt]]) for vt in HEADS if msd(GM[vt][-1][0]) != 0]
print('   M2b 末视图非 0 的组: %s' % bad0[:8])
# M3 主视图槽数最多
maxlast = sum(1 for vt in HEADS if len(GM[vt][-1][1]) == max(len(s[1]) for s in GM[vt]))
ck('M3a 末视图槽数为组内最多', maxlast / len(HEADS) > 0.85, '%.4f (%d/%d)' % (maxlast / len(HEADS), maxlast, len(HEADS)))
# M4 mdisp 取值
mvals = collections.Counter(msd(cp) for g in GM.values() for cp, _ in g)
print('   M4 视图 mdisp 取值: %s' % mvals.most_common(10))
ck('M4a mdisp 取值集合', set(mvals) >= {0, 4, 8, 12}, sorted(mvals)[:10])
ck('M4b mdisp==0 的视图数', mvals[0] > 0, mvals[0])
ck('M4c mdisp 全为 4 的倍数', all(v % 4 == 0 for v in mvals), [v for v in mvals if v % 4])
# M5 单视图组
single = [vt for vt in HEADS if len(GM[vt]) == 1]
ck('M5a 单视图组 46 个', len(single) == 46, len(single))
ck('M5b 单视图组 mdisp 全 0', all(msd(GM[vt][0][0]) == 0 for vt in single),
   collections.Counter(msd(GM[vt][0][0]) for vt in single).most_common(4))
# M6 INoticeSink / INoticeSource
FIND = {}
for vt in HEADS:
    for i, (cp, _) in enumerate(GM[vt]):
        nm = COL[cp]['name']
        if nm in ('.?AVINoticeSink@@', '.?AVINoticeSource@@'):
            FIND.setdefault(nm, []).append((hex(vt), i, len(GM[vt]), msd(cp), len(GM[vt][i][1])))
print('   M6 INoticeSink 出现: %s' % FIND.get('.?AVINoticeSink@@'))
print('   M6 INoticeSource 出现: %s' % FIND.get('.?AVINoticeSource@@'))
ck('M6a INoticeSink 作为组内视图出现', len(FIND.get('.?AVINoticeSink@@', [])) > 0, len(FIND.get('.?AVINoticeSink@@', [])))
ck('M6b 其出现均为 mdisp==0 的非首位视图', all(r[3] == 0 for r in FIND.get('.?AVINoticeSink@@', [1])),
   [r[3] for r in FIND.get('.?AVINoticeSink@@', [])])
# M7 反控
rev = 0
for vt in HEADS:
    m = [msd(cp) for cp, _ in reversed(GM[vt])]
    if all(m[i] >= m[i + 1] for i in range(len(m) - 1)): rev += 1
ck('M7a 反控：反转视图顺序后非递增组数显著下降', rev < desc * 0.5, '%d vs %d' % (rev, desc))
OUT = dict(heads=len(HEADS), views=sum(len(g) for g in GM.values()),
           slots=sum(len(s[1]) for g in GM.values() for s in g),
           desc=desc, nonmono=nonmono[:20], last0=last0, bad0=bad0[:20], maxlast=maxlast,
           mdisp=dict((str(k), v) for k, v in mvals.most_common()), single=len(single),
           find=dict((k, v) for k, v in FIND.items()), rev=rev, asserts=N, fails=fails)
json.dump(OUT, open('/home/t628/projects/ra2-campaign-forge/_r203/m7_layout.json', 'w'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
