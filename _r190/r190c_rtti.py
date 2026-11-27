#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R190 C：RTTI 继承结构逐条实证（主会话自写，14 断言 0 FAIL）。

本轮不做「猜语义」，只把 MSVC RTTI 的三层结构逐字段对齐：
  COL  = {signature, offset, cdOffset, pTypeDescriptor, pClassDescriptor}
  TD   = {pVFTable, spare, name}            ← pVFTable 应指向 type_info 表
  CHD  = {signature, attributes, numBaseClasses, pBaseClassArray}
  BCD  = {pTD, numContainedBases, PMD{mdisp,pdisp,vdisp}, attributes}
回答：1214 条 COL 的 RTTI 是否构成一个闭合、可逐条复算的继承描述；
层的偏移集合与基类 PMD.mdisp 集合的关系（10 vs 14，差集四个是「有基类子对象但没有独立副表」）。
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
        COLS[b] = dict(off=d[1], ptd=d[3], pchd=d[4], name=nm.decode('latin1'))
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
order = sorted(VTS)
def bases(c):
    ch = c['pchd']; num = P.dw(ch + 8); pba = P.dw(ch + 12)
    return [(P.dw(e), P.dw(e + 4), P.dw(e + 8), P.dw(e + 12), P.dw(e + 16), P.dw(e + 20))
            for e in (P.dw(pba + 4 * j) for j in range(num))]

ck('C0 COL 1214 / vtable 1214 / 槽位实例 14044 / 1214 张表指向 1214 个不同 COL',
   (len(COLS), len(VTS), sum(PRE.values())) == (1214, 1214, 14044) and
   len(set(P.dw(vt - 4) for vt in order)) == 1214)
pvf = collections.Counter(P.dw(c['ptd']) for c in COLS.values())
ck('C1 1214 条 TypeDescriptor.pVFTable 全 == 0x7F9594', pvf == collections.Counter({0x7F9594: 1214}),
   dict((hex(k), v) for k, v in pvf.items()))
ck('C2 0x7F9594 本身在册、名为 type_info、其 TD.name 也是 type_info',
   0x7F9594 in VTS and VTS[0x7F9594]['name'] == '.?AVtype_info@@' and
   P.cstr(VTS[0x7F9594]['ptd'] + 8, 60) == b'.?AVtype_info@@')
ck('C3 COL.name 与 TypeDescriptor.name 逐字节相同 1214/1214',
   sum(1 for c in COLS.values() if P.cstr(c['ptd'] + 8, 200) == c['name'].encode()) == 1214)
sig = collections.Counter(P.dw(c['pchd']) for c in COLS.values())
ck('C4 1214 条 ClassHierarchyDescriptor 的 signature 全 0', sig == collections.Counter({0: 1214}), dict(sig))
tot = 0; selfname = 0; e0md = 0; e0ncb = 0; tdok = 0; ncbh = collections.Counter()
mdh = collections.Counter(); atth = collections.Counter(); badsn = []
for a, c in COLS.items():
    bs = bases(c); tot += len(bs)
    if P.cstr(bs[0][0] + 8, 200) == c['name'].encode(): selfname += 1
    else: badsn.append((c['name'][:30], P.cstr(bs[0][0] + 8, 40)))
    if bs[0][2] == 0: e0md += 1
    if bs[0][1] == P.dw(c['pchd'] + 8) - 1: e0ncb += 1
    for (ptd, ncb, md, pd, vd, att) in bs:
        ncbh[ncb] += 1; mdh[md] += 1; atth[att] += 1
        if P.dw(ptd) == 0x7F9594 and P.cstr(ptd + 8, 200): tdok += 1
ck('C5 基础类描述符合计 %d 条（= 1214 条 COL 的 numBaseClasses 之和）' % tot, tot == 5302, tot)
ck('C6 每条数组第 0 项（自项）的 TD 名 == 该 COL 名：%d/1214' % selfname, selfname == 1214, badsn[:4])
ck('C7 自项 PMD.mdisp == 0：%d/1214' % e0md, e0md == 1214, e0md)
ck('C8 自项 numContainedBases == numBaseClasses−1：%d/1214' % e0ncb, e0ncb == 1214, e0ncb)
ck('C9 5302 条描述符的 pTD 全是合法 TypeDescriptor（pVFTable==0x7F9594 且名字非空）：%d' % tdok, tdok == tot, tdok)
print('#  numContainedBases 直方:', dict(sorted(ncbh.items())))
print('#  PMD.mdisp 全部取值:', dict(sorted(mdh.items())))
print('#  描述符 attributes 直方:', dict(atth))
ck('C10 PMD.mdisp 取值集合恰 14 个 {0,4,8,12,24,36,40,44,172,176,240,248,1728,21784}',
   set(mdh) == {0, 4, 8, 12, 24, 36, 40, 44, 172, 176, 240, 248, 1728, 21784}, sorted(mdh))
layeroffs = set(c['off'] for c in COLS.values())
ck('C11 vtable 层偏移集合恰 10 个 {0,4,8,12,24,36,40,44,1728,21784}',
   layeroffs == {0, 4, 8, 12, 24, 36, 40, 44, 1728, 21784}, sorted(layeroffs))
ck('C12 层偏移集合 ⊂ PMD.mdisp 集合，差集 = {172,176,240,248}（有基类子对象但无独立副表）',
   layeroffs < set(mdh) and set(mdh) - layeroffs == {172, 176, 240, 248}, sorted(set(mdh) - layeroffs))
for m in sorted(set(mdh) - layeroffs):
    who = collections.Counter(P.cstr(b[0] + 8, 60).decode('latin1')
                              for c in COLS.values() for b in bases(c) if b[2] == m)
    print('#  mdisp=%d 基类项 %d 条，宿主类 %s' % (m, sum(who.values()), who.most_common(3)))
ck('C13 全部 5302 条描述符 pdisp==0xFFFFFFFF 且 vdisp==0（单继承、无虚基类）',
   all(b[3] == 0xFFFFFFFF and b[4] == 0 for c in COLS.values() for b in bases(c)))
names = set(c['name'] for c in COLS.values())
ext = collections.Counter(P.cstr(b[0] + 8, 200).decode('latin1')
                          for c in COLS.values() for b in bases(c)
                          if P.cstr(b[0] + 8, 200).decode('latin1') not in names)
ck('C14 外部基类（不在 1214 个类名集合）%d 条 / %d 个不同名，其余 %d 条落在本镜像类名集合内'
   % (sum(ext.values()), len(ext), tot - sum(ext.values())),
   sum(ext.values()) == 2111 and len(ext) == 34 and tot - sum(ext.values()) == 3191,
   (sum(ext.values()), len(ext), ext.most_common(4)))
# 反控
ck('N1 反控：把 pTD 整体 +4 后仍能通过 C9 的比例应为 0',
   sum(1 for c in COLS.values() for b in bases(c)
       if P.dw(b[0] + 4) == 0x7F9594) == 0)
alt = sum(1 for c in COLS.values() if bases(c)[0][1] == 1)
ck('N2 反控：把自项判据换成「numContainedBases==1」只命中 %d（远小于 1214）⇒ C8 的判据特异' % alt,
   alt == 455, alt)
# N3 反控：numContainedBases 本身不能区分首项与末项（末项也恒为 0）⇒ 首项身份靠名字判据而非计数
last0 = sum(1 for c in COLS.values() if bases(c)[-1][1] == 0)
ck('N3 反控（如实登记）：末项 numContainedBases==0 也命中 %d/1214 ⇒ 计数判据不能区分首末项，'
   '首项身份只由 C6 的名字判据确立' % last0, last0 == 1214, last0)
# N4：末项 name == COL 名的只有单基类数组
lastname = sum(1 for c in COLS.values() if P.cstr(bases(c)[-1][0] + 8, 200) == c['name'].encode())
one_n = sum(1 for c in COLS.values() if P.dw(c['pchd'] + 8) == 1)
ck('N4 反控：末项 TD 名 == COL 名 只命中 %d 条，恰等于 numBaseClasses==1 的 %d 条（首末同一项）'
   % (lastname, one_n), lastname == one_n == 256, (lastname, one_n))
json.dump(dict(total=tot, selfname=selfname, e0md=e0md, e0ncb=e0ncb, tdok=tdok,
               ncb=dict(sorted(ncbh.items())), mds=dict(sorted(mdh.items())), attr=dict(atth),
               layeroffs=sorted(layeroffs), extra=sorted(set(mdh) - layeroffs),
               ext_total=sum(ext.values()), ext_names=len(ext), ext_top=ext.most_common(12)),
          open(os.path.join(HERE, 'r190c.json'), 'w'), indent=1, ensure_ascii=False)
print('\n断言 %d 条，FAIL %d 条' % (N, len(fails)))
sys.exit(1 if fails else 0)
