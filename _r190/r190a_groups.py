#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R190 A：同名多档 vtable 组的排布普查（主会话自写，含正反控）。

回答：
  A1 1,214 张表按 COL 修饰名分成多少组、组内表数分布
  A2 多表组内按地址升序 mdisp 是否严格递减、末项是否恒为 0（含 3 个反例）
  A3 组内相邻两表的块间距是否恒为 4（组内完全紧排）
  A4 紧排/零尾/.data 尾/散尾四档是否闭合到 1214
  A5 45 张散尾表的终点 dword 分档（是否落 .text / 浮点常量 / 4 字符 ASCII）
  A6 235 张非紧排表的块间空隙里落 .text 的 dword 有多少处、是否可能是漏数的槽
  A7 mdisp > 44 的异常表
  A8 单槽表的唯一槽值直方
"""
import sys, os, struct, collections, json, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '_r185'))
import pe185 as P

fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

T = P.B['.text']; LO = T['lo']; HI = T['hi_file']
COLS = {}
for sec in ('.rdata', '.data'):
    s = P.B[sec]; nd = s['rawsize'] // 4
    v = struct.unpack_from('<%dI' % nd, P.RAW, s['rawptr'])
    for i in range(nd - 4):
        b = s['lo'] + 4 * i; d = v[i:i + 5]
        if d[0] not in (0, 1) or d[2] != 0: continue
        if P.where(d[3]) != '.data' or P.where(d[4]) != '.rdata': continue
        nm = P.cstr(d[3] + 8, 200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COLS[b] = dict(mdisp=d[1], ptd=d[3], name=nm.decode('latin1'))
VTS = {}
for sec in ('.rdata', '.data'):
    s = P.B[sec]; nd = s['rawsize'] // 4
    v = struct.unpack_from('<%dI' % nd, P.RAW, s['rawptr'])
    for i, x in enumerate(v):
        if not (LO <= x < HI): continue
        b = s['lo'] + 4 * i
        if P.dw(b - 4) in COLS: VTS[b] = COLS[P.dw(b - 4)]
def pre(vt):
    k = 0
    while True:
        d = P.dw(vt + 4 * k)
        if d is None or not (LO <= d < HI): return k
        k += 1
PRE = {vt: pre(vt) for vt in VTS}
ck('A0 COL=1214 VTS=1214 slots=14044', (len(COLS), len(VTS), sum(PRE.values())) == (1214, 1214, 14044),
   (len(COLS), len(VTS), sum(PRE.values())))
order = sorted(VTS); nxt = {order[i]: (order[i + 1] if i + 1 < len(order) else None) for i in range(len(order))}
byname = collections.defaultdict(list)
for vt in order: byname[VTS[vt]['name']].append(vt)
mult = {k: v for k, v in byname.items() if len(v) > 1}
ck('A1 名字组 954；多表组 94（2 张 10 / 3 张 6 / 4 张 76 / 5 张 1 / 7 张 1）',
   len(byname) == 954 and len(mult) == 94 and
   collections.Counter(len(v) for v in byname.values()) == collections.Counter({1: 860, 2: 10, 3: 6, 4: 76, 5: 1, 7: 1}),
   (len(byname), len(mult), sorted(collections.Counter(len(v) for v in byname.values()).items())))
viol = []; lastnz = []
for nm, lst in mult.items():
    m = [VTS[vt]['mdisp'] for vt in lst]
    if not all(m[i] > m[i + 1] for i in range(len(m) - 1)): viol.append((nm, m))
    if m[-1] != 0: lastnz.append((nm, m))
ck('A2 多表组内按地址升序 mdisp 严格递减：91/94 满足，反例 3', len(mult) - len(viol) == 91 and len(viol) == 3,
   [v[0] for v in viol])
ck('A2b 组内末项恒为 0（0 反例）', len(lastnz) == 0, lastnz)
ck('A2c 三个反例的 mdisp 序列恰为 OverlayClass[12,4,8,0] / SmudgeClass[12,4,8,0] / TerrainClass[4,12,8,0]',
   [(v[0], v[1]) for v in sorted(viol)] == [('.?AVOverlayClass@@', [12, 4, 8, 0]),
                                            ('.?AVSmudgeClass@@', [12, 4, 8, 0]),
                                            ('.?AVTerrainClass@@', [4, 12, 8, 0])], sorted(viol))
pairs = [(nm, a, b) for nm, lst in mult.items() for a, b in zip(lst, lst[1:])]
gaps = collections.Counter(b - (a + 4 * PRE[a]) for nm, a, b in pairs)
ck('A3 组内相邻块间距 260/260 恒为 4', gaps == collections.Counter({4: 260}), (len(pairs), dict(gaps)))
ck('A3b 多表组在全局地址序里全部连续（非连续组 0）',
   all([order.index(vt) for vt in lst] == list(range(order.index(lst[0]), order.index(lst[0]) + len(lst)))
       for lst in mult.values()))
tight = zero = data = 0; scatter = []
for vt in order:
    stop = vt + 4 * PRE[vt]; nv = nxt[vt]
    if nv is not None and stop == nv - 4: tight += 1; continue
    d = P.dw(stop)
    if d == 0: zero += 1
    elif P.where(d) == '.data': data += 1
    else: scatter.append(vt)
ck('A4 979 紧排 / 186 零尾 / 4 .data 尾 / 45 散尾，合计 1214',
   (tight, zero, data, len(scatter)) == (979, 186, 4, 45), (tight, zero, data, len(scatter)))
tailinv = [(vt, vt + 4 * PRE[vt], P.dw(vt + 4 * PRE[vt])) for vt in scatter]
ck('A5 45 张散尾表的终点 dword 无一条落 .text（0/45）',
   sum(1 for x in tailinv if P.where(x[2]) == '.text') == 0,
   [(hex(a), hex(b), hex(c)) for a, b, c in tailinv if P.where(c) == '.text'])
def kind(d):
    b = struct.pack('<I', d)
    if all(0x20 <= c < 0x7f for c in b): return 'ascii4'
    f = struct.unpack('<f', b)[0]
    if math.isfinite(f) and 1e-4 <= abs(f) < 1e6: return 'float'
    return 'other'
kk = collections.Counter(kind(x[2]) for x in tailinv)
ck('A5b 45 张散尾终点 dword 分档 ascii4=%d float=%d other=%d，合计 45' % (kk['ascii4'], kk['float'], kk['other']),
   sum(kk.values()) == 45, dict(kk))
slotvals = collections.Counter()
for vt in order:
    for k in range(PRE[vt]): slotvals[P.dw(vt + 4 * k)] += 1
gap_hits = []
for vt in order:
    stop = vt + 4 * PRE[vt]; nv = nxt[vt]
    end = (nv - 4) if nv is not None else stop + 64
    if nv is not None and stop == nv - 4: continue
    for a in range(stop, end, 4):
        d = P.dw(a)
        if d is not None and LO <= d < HI: gap_hits.append((vt, a, d))
ck('A6 非紧排表块间空隙内落 .text 的 dword 合计 127 处、涉及 8 张表',
   len(gap_hits) == 127 and len(set(x[0] for x in gap_hits)) == 8,
   (len(gap_hits), len(set(x[0] for x in gap_hits))))
inter = [x for x in gap_hits if x[2] in slotvals]
ck('A6b 这 127 处里「值同时也是某张表真槽值」的 0 处 ⇒ 不是被漏数的槽', len(inter) == 0, len(inter))
out = [(vt, VTS[vt]['name'], VTS[vt]['mdisp']) for vt in order if VTS[vt]['mdisp'] > 44]
ck('A7 mdisp>44 的表恰 4 张：MouseClass 21784 / AircraftClass 1728 / TabClass 21784 / ScrollClass 21784',
   len(out) == 4 and sorted(x[2] for x in out) == [1728, 21784, 21784, 21784],
   [(hex(v), n[:30], m) for v, n, m in out])
one = [vt for vt in order if PRE[vt] == 1]
c1 = collections.Counter(P.dw(vt) for vt in one)
ck('A8 单槽表 %d 张（前两位 0x410590 78 / 0x410580 75）' % len(one),
   len(one) == 199 and c1.most_common(2) == [(0x410590, 78), (0x410580, 75)],
   (len(one), [(hex(k), v) for k, v in c1.most_common(4)]))
import random
random.seed(190)
bad_shuf = 0
for nm, lst in mult.items():
    m = [VTS[vt]['mdisp'] for vt in lst]; random.shuffle(m)
    if all(m[i] > m[i + 1] for i in range(len(m) - 1)): bad_shuf += 1
ck('N1 反控：组内 mdisp 随机打乱后严格递减的组数 %d（应远小于 91）' % bad_shuf, bad_shuf < 20, bad_shuf)
rev = sum(1 for nm, lst in mult.items()
          if all(VTS[lst[i]]['mdisp'] < VTS[lst[i + 1]]['mdisp'] for i in range(len(lst) - 1)))
ck('N2 反控：改为要求严格递增时满足组数 %d（应 0）' % rev, rev == 0, rev)
g2 = collections.Counter(b - (a + 4 * (PRE[a] + 1)) for nm, a, b in pairs)
ck('N3 反控：块间距算成「槽数+1」时恒为 4 的对数降到 %d（应 0）' % g2.get(4, 0), g2.get(4, 0) == 0, dict(g2))
json.dump(dict(groups=len(byname), multi=len(mult), strict_dec_pass=len(mult) - len(viol),
               viol=[v[0] for v in viol], gap4=len(pairs), tight=tight, zero=zero, data=data,
               scatter=len(scatter), tail_kinds=dict(kk), gap_text_dwords=len(gap_hits),
               gap_text_tables=len(set(x[0] for x in gap_hits)), gap_slot_value_intersect=len(inter),
               mdisp_outliers=[(hex(v), n, m) for v, n, m in out], one_slot=len(one)),
          open(os.path.join(HERE, 'r190a.json'), 'w'), indent=1, ensure_ascii=False)
print('\n断言 %d 条，FAIL %d 条' % (N, len(fails)))
sys.exit(1 if fails else 0)
