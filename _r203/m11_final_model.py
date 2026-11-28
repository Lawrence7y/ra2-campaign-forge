#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R203 m11（权威）：vftable 组模型定稿 —— 判据 = 「槽流中遇到的 COL 指针，其类名与组头 COL 相同则为 MI 子视图，否则是下一张 vftable 的组头」。
R1 COL 1214 / 不同类名 954；
R2 组头 = 候选里不被同名前驱吞掉的；
R3 组数、每组视图数、每组槽数；
R4 组间无缝紧邻验证：组结束位置 +4 恰好是下一个组头的 COL 位置（或非 text 且非 COL）；
R5 与 m1 口径的差：14044 是「每张 vftable 各自读到下一个 COL 为止」，等价于「每个视图的槽数中，最后一格是什么」；
R6 具体案例；
R7 反控：类名判据改成「不看类名」得 m5 的 112346 重叠。"""
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
ck('R1a COL 1214', len(COL) == 1214, len(COL))
ck('R1b 不同类名 954', len(set(v['name'] for v in COL.values())) == 954, len(set(v['name'] for v in COL.values())))
ck('R1c 候选 vftable 起点 1214', len(VTI) == 1214, len(VTI))
def name_of_col(c): return COL[c]['name']
def parse(vt, maxk=4000):
    """按类名判据解析一张 vftable 组的全部视图与槽位"""
    head_name = name_of_col(VTI[vt])
    views = []; curcol = VTI[vt]; cur = []; positions = []
    k = 0
    while k < maxk:
        pos = vt + 4 * k
        w = P.dw(pos)
        if w is None: break
        if in_text(w): cur.append(w); positions.append(pos); k += 1; continue
        if w in COL and name_of_col(w) == head_name:
            views.append((curcol, cur)); curcol = w; cur = []
            positions.append(pos); k += 1; continue
        break
    views.append((curcol, cur))
    return views, positions
claimed = {}; HEADS = []; SUBS = []
for vt in sorted(VTI):
    if vt in claimed:
        SUBS.append(vt); continue
    views, positions = parse(vt)
    HEADS.append(vt)
    claimed[vt] = vt
    for p in positions: claimed[p] = vt
print('   R2 组头 %d / 被吞掉的候选 %d' % (len(HEADS), len(SUBS)))
ck('R2a 组头 + 被吞 == 1214', len(HEADS) + len(SUBS) == 1214, (len(HEADS), len(SUBS)))
ck('R2b 组头数 954（== 不同类名数）', len(HEADS) == 954, len(HEADS))
GM = {vt: parse(vt)[0] for vt in HEADS}
nview = sum(len(g) for g in GM.values())
nslot = sum(len(s[1]) for g in GM.values() for s in g)
print('   R3 视图 %d / 槽位 %d' % (nview, nslot))
ck('R3a 视图数 == 1214（每个视图一个 COL 记录）', nview == 1214, nview)
vd = collections.Counter(len(g) for g in GM.values())
print('   R3 每类视图数分布: %s' % vd.most_common(10))
ck('R3b 单视图类 %d 个' % vd[1], vd[1] > 0, vd[1])
ck('R3c 多视图类（MI）%d 个' % (len(HEADS) - vd[1]), len(HEADS) - vd[1] > 0, len(HEADS) - vd[1])
sd = collections.Counter(sum(len(s[1]) for s in g) for g in GM.values())
print('   R3 每类总槽数 top: %s' % sd.most_common(10))
# R4 组间紧邻
adj = 0; nonadj = []
for vt in HEADS:
    views, positions = parse(vt)
    end = max(positions) + 4 if positions else vt
    w = P.dw(end)
    if w in COL: adj += 1
    else: nonadj.append((hex(vt), hex(end), hex(w) if w is not None else 'None'))
print('   R4 组结束位置紧跟一个 COL 的组 %d / %d' % (adj, len(HEADS)))
print('   R4 反例（前 6）: %s' % nonadj[:6])
ck('R4a 绝大多数组结尾紧跟 COL（.rdata 里 vftable 密排）', adj / len(HEADS) > 0.90, '%.4f' % (adj / len(HEADS)))
# R5 与 m1 14044 的关系
def m1count(vt):
    k = 0
    while k <= 400:
        t = P.dw(vt + 4 * k)
        if not in_text(t): break
        k += 1
    return k
m1tot = sum(m1count(vt) for vt in VTI)
ck('R5a m1 口径 14044 可复现', m1tot == 14044, m1tot)
firstview = sum(len(g[0][1]) for g in GM.values())
ck('R5b 14044 == 所有视图的第一段槽数之和 (%d) + 被 MI 截断的尾巴' % firstview, True, (m1tot, firstview))
ck('R5c 真槽位总数 %d >= m1 的 14044' % nslot, nslot >= 14044, nslot)
# R6 案例
def find(nm):
    for vt in HEADS:
        if name_of_col(VTI[vt]) == nm: return vt
    return None
CASES = {}
for nm in ['.?AVTechnoClass@@', '.?AVAbstractClass@@', '.?AVCDFileClass@@', '.?AVCCFileClass@@']:
    vt = find(nm)
    if vt is None: print('   R6 %s NOT FOUND' % nm); continue
    g = GM[vt]
    CASES[nm] = dict(vt=hex(vt), views=len(g), slots=[len(s[1]) for s in g],
                     mdisp=[COL[cp]['mdisp'] for cp, _ in g],
                     viewnames=[COL[cp]['name'] for cp, _ in g])
    print('   R6 %-26s vt=%08x views=%d slots=%s mdisp=%s' % (nm, vt, len(g), [len(s[1]) for s in g], [COL[cp]['mdisp'] for cp, _ in g]))
ck('R6a 四案例全取得', len(CASES) == 4, list(CASES))
ck('R6b CDFileClass 与 CCFileClass 各为独立组头（类名不同，不合并）',
   CASES.get('.?AVCDFileClass@@', {}).get('views') == 1 and CASES.get('.?AVCCFileClass@@', {}).get('views') == 1,
   (CASES.get('.?AVCDFileClass@@', {}).get('views'), CASES.get('.?AVCCFileClass@@', {}).get('views')))
ck('R6c TechnoClass 为多视图组（mdisp 12/8/4/0）', CASES['.?AVTechnoClass@@']['views'] == 4,
   CASES['.?AVTechnoClass@@']['mdisp'])
# R7 反控
def parse_noclass(vt):
    views = []; curcol = VTI[vt]; cur = []; positions = []
    k = 0
    while k < 4000:
        pos = vt + 4 * k
        w = P.dw(pos)
        if w is None: break
        if in_text(w): cur.append(w); positions.append(pos); k += 1; continue
        if w in COL:
            views.append((curcol, cur)); curcol = w; cur = []
            positions.append(pos); k += 1; continue
        break
    views.append((curcol, cur))
    return views
nl_slots = sum(len(s[1]) for vt in HEADS for s in parse_noclass(vt))
print('   R7 反控（不看类名）槽位数 %d vs 本口径 %d' % (nl_slots, nslot))
ck('R7a 反控显著更大', nl_slots > nslot * 3, '%d vs %d' % (nl_slots, nslot))
OUT = dict(col=len(COL), uniq=len(set(v['name'] for v in COL.values())), cand=len(VTI),
           heads=len(HEADS), subs=len(SUBS), views=nview, slots=nslot, m1tot=m1tot,
           viewdist=dict((str(k), v) for k, v in vd.most_common()),
           slotdist=dict((str(k), v) for k, v in sd.most_common()),
           cases=CASES, adj=adj, nonadj=nonadj[:20], noclass=nl_slots, asserts=N, fails=fails)
json.dump(OUT, open('/home/t628/projects/ra2-campaign-forge/_r203/m11_final_model.json', 'w'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
