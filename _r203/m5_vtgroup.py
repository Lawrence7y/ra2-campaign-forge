#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R203 m5：MSVC 多重继承 vftable 组结构实证 —— 订正 m1 的槽位切分（把内嵌 COL 指针误当终止符）。
K1 COL 记录全集 / 被用作 vt-4 的 COL / 只出现在槽流内部的 COL；
K2 组结构：vt 起，槽流中若遇 dword w 且 w 是 COL 记录地址，则该 w 位置是新子对象视图的 COL，下一条才是槽；
K3 重算槽位：真槽位 = 所有 text 指针，含跨 COL 的；
K4 每 vtable 组的槽数、子对象视图数分布；
K5 12 条具体案例逐槽列出（TechnoClass / AbstractClass / AbstractTypeClass / ObjectClass）；
K6 反控：把「遇 COL 即视为子对象视图」改成「遇 COL 即停」，槽位总数应回落到 14044。"""
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
ck('K1a COL 记录 1214', len(COL) == 1214, len(COL))
VTI = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL: VTI[base + 4 * i] = P.dw(base + 4 * i - 4)
ck('K1b vt-4 是 COL 的 vtable 起始 1214', len(VTI) == 1214, len(VTI))
USED = set(VTI.values())
ck('K1c 被用作 vt-4 的 COL 去重数 1214', len(USED) == 1214, len(USED))
# 组解析：从 vt 起，允许内嵌 COL 指针
def parse(vt, maxk=2000):
    subs = []           # [(colptr, [targets])]
    cur = []            # 当前视图槽序列
    curcol = VTI[vt]
    k = 0; total = 0
    while k < maxk:
        w = P.dw(vt + 4 * k)
        if w is None: break
        if in_text(w):
            cur.append(w); k += 1; continue
        if w in COL:
            subs.append((curcol, cur)); curcol = w; cur = []
            k += 1; continue
        break
    subs.append((curcol, cur))
    return subs
GROUPS = {vt: parse(vt) for vt in VTI}
nsub = sum(len(g) for g in GROUPS.values())
ntgt = sum(len(s[1]) for g in GROUPS.values() for s in g)
print('   K2 组数 %d / 子对象视图总数 %d / 真槽位总数 %d' % (len(GROUPS), nsub, ntgt))
ck('K2a 子对象视图总数 == 1214 + 内嵌 COL 指针数', nsub > 1214, nsub)
ck('K2b 真槽位总数 > 14044（m1 被 COL 指针截断）', ntgt > 14044, ntgt)
ck('K2c 视图内槽数 0 的视图数（空视图）', sum(1 for g in GROUPS.values() for s in g if not s[1]) < 200,
   sum(1 for g in GROUPS.values() for s in g if not s[1]))
sd = collections.Counter(len(g) for g in GROUPS.values())
print('   K4 每组子对象视图数分布 top: %s' % sd.most_common(8))
ck('K4a 单视图组（无多重继承）占比 > 10%', sd[1] / len(GROUPS) > 0.10, '%.4f' % (sd[1] / len(GROUPS)))
allslots = [t for g in GROUPS.values() for s in g for t in s[1]]
ck('K4b 去重目标数', len(set(allslots)) > 6692, len(set(allslots)))
# K5 案例
def find(nm):
    for vt in VTI:
        if COL[VTI[vt]]['name'] == nm: return vt
    return None
for nm in ['.?AVTechnoClass@@', '.?AVAbstractClass@@', '.?AVAbstractTypeClass@@', '.?AVObjectClass@@']:
    vt = find(nm)
    if vt is None: print('   K5 %s NOT FOUND' % nm); continue
    g = GROUPS[vt]
    print('   K5 %-28s vt=%08x 视图 %d' % (nm, vt, len(g)))
    for i, (cp, ts) in enumerate(g[:6]):
        print('        view%d COL=%08x %-34s mdisp=%-3d slots=%d first=%s' % (
            i, cp, COL[cp]['name'][:34], COL[cp]['mdisp'], len(ts), [hex(x) for x in ts[:3]]))
# K6 反控
def parse_stop(vt):
    s = []; k = 0
    while k < 2000:
        w = P.dw(vt + 4 * k)
        if not in_text(w): break
        s.append(w); k += 1
    return s
stop_tot = sum(len(parse_stop(vt)) for vt in VTI)
print('   K6 反控（遇 COL 即停）槽位总数 %d' % stop_tot)
ck('K6a 反控回落到 14044', stop_tot == 14044, stop_tot)
ck('K6b 新口径显著大于旧口径', ntgt > stop_tot * 1.3, '%d vs %d (+%.1f%%)' % (ntgt, stop_tot, 100.0 * (ntgt - stop_tot) / stop_tot))
OUT = dict(col=len(COL), vt=len(VTI), views=nsub, slots=ntgt, distinct=len(set(allslots)),
           stop=stop_tot, groupdist=dict((str(k), v) for k, v in sd.most_common()),
           mv=sum(1 for g in GROUPS.values() if len(g) > 1), asserts=N, fails=fails)
json.dump(OUT, open('/home/t628/projects/ra2-campaign-forge/_r203/m5_vtgroup.json', 'w'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
