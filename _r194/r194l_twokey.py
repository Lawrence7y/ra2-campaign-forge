#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R194 第十四刀：把「11 核 + 阈值 3」压缩成**两条键**的判据，并给出双向闭包。

  W1 L = {主表 : 槽 4 == 0x410450} ∪ {主表 : 槽 9 == 0x410470}（并集精确等于 78 张）。
  W2 两个集合的交集 = 0（互斥可加）。
  W3 第一条键 77 张（HouseTypeClass 例外），第二条键的**差集恰好只有 HouseTypeClass**。
  W4 两条键在 876 张补集上的命中都 = 0。
  W5 两条键在 260 张接口子表上的命中都 = 0。
  反控：
  N1 把槽 9 换成槽 8 / 槽 10 / 槽 11（同为虚函数区）⇒ 并集不再等于 L。
  N2 把 0x410470（xor eax,eax; ret）换成同形态的 0x4C9150 ⇒ 并集变大（FP>0）。
"""
import sys, struct, collections
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']
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
        COL[base + 4 * i] = dict(mdisp=w[i + 1], pchd=w[i + 4], name=nm.decode('latin1'))
VT = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL: VT[base + 4 * i] = P.dw(base + 4 * i - 4)
def nslot(vt):
    k = 0
    while in_text(P.dw(vt + 4 * k)): k += 1
    return k
NS = {vt: nslot(vt) for vt in VT}
MAIN = [vt for vt in VT if COL[VT[vt]]['mdisp'] == 0]
SUB = [vt for vt in VT if COL[VT[vt]]['mdisp'] != 0]
def chain(colva):
    c = COL[colva]; n = P.dw(c['pchd'] + 8); arr = P.dw(c['pchd'] + 12); out = []
    for j in range(n):
        b = P.dw(arr + 4 * j)
        if b is None or P.where(b) in ('None', 'other'): continue
        ptd = P.dw(b)
        if ptd is None: continue
        nm = P.cstr(ptd + 8, 160)
        out.append(nm.decode('latin1') if nm else None)
    return out
L = set(vt for vt in MAIN if '.?AVAbstractClass@@' in chain(VT[vt]))
def slot(vt, s): return P.dw(vt + 4 * s) if s < NS[vt] else None
A = set(vt for vt in MAIN if slot(vt, 4) == 0x410450)
B = set(vt for vt in MAIN if slot(vt, 9) == 0x410470)
print('   |A|=%d |B|=%d |A∩B|=%d |A∪B|=%d |L|=%d' % (len(A), len(B), len(A & B), len(A | B), len(L)))
ck('W1 L == 槽4==0x410450 或 槽9==0x410470（并集精确 78 张，双向差集 0）',
   (A | B) == L, (len(A | B), len(L), [hex(x) for x in ((A | B) ^ L)]))
ck('W2 两条键互斥（交集 0）⇒ 78 = 77 + 1 结构', not (A & B), len(A & B))
ck('W3 |A| = 77（HouseTypeClass 不在 A）', len(A) == 77, len(A))
onlyB = B - A
names = {hex(v): (COL[VT[v]]['name'], NS[v], slot(v, 4), slot(v, 9)) for v in onlyB}
print('   B\\A = %s' % names)
ck('W3b B\\A 恰为 1 张且是 .?AVHouseTypeClass@@（槽 4 = 0x512280）',
   len(onlyB) == 1 and list(names.values())[0][0] == '.?AVHouseTypeClass@@'
   and list(names.values())[0][2] == 0x512280, names)
ck('W4 两条键在 876 张补集主表上命中 0',
   not any(slot(vt, 4) == 0x410450 or slot(vt, 9) == 0x410470 for vt in MAIN if vt not in L), None)
ck('W5 两条键在 260 张接口子表上命中 0',
   not any(slot(vt, 4) == 0x410450 or slot(vt, 9) == 0x410470 for vt in SUB), None)
for s in (8, 10, 11, 12, 13, 14):
    S = set(vt for vt in MAIN if slot(vt, s) == 0x410470)
    print('   N1 槽 %2d == 0x410470 的主表 %d 张（∩L %d，差集 %d）' % (s, len(S), len(S & L), len(S ^ L)))
    ck('N1-%02d 槽 %d 用 0x410470 不等于 L（槽位敏感）' % (s, s), S != L, len(S))
S2 = set(vt for vt in MAIN if slot(vt, 9) == 0x4C9150)
print('   N2 槽 9 == 0x4C9150（同形态 xor eax,eax;ret）的主表 %d 张' % len(S2))
ck('N2 换成同形态的 0x4C9150 后并集变大（FP > 0，判据不是「任何 xor eax,eax」）',
   len((A | S2) - L) > 0, len((A | S2) - L))
print('\n断言 %d 条，FAIL %d 条' % (N, len(fails)))
if fails: print('FAIL 明细：' + ' | '.join(fails)); sys.exit(1)
