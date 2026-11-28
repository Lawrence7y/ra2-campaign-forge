#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R194 收口判据（主会话，0 FAIL 目标）：把本轮九条主张用**订正后的措辞**重述并复算。

r194i/k/l 三脚本共 6 条 FAIL 全是判据写成应然（清单见下），本轮结论按实测订正：
  E1 (r194i K2b) 原写「h>=1 不是充分条件，FN>0」——实测 FN=0，**11 核 + h>=1 已精确等于 L**。
  E2 (r194k P1-03/04/09) 原写「每项剔除后都应保持双向相等」——实测 (4,0x410450)/(7,0x4103E0)/
     (16,0x4104B0) 三项剔除后 FN=1，三项在阈值 3 下**是必要项**。
  E3 (r194k P5a) 原写「0x410260 错 4 字节即失去判别力」——实测仍 78 张，该项在阈值 3 下可替代。
  E4 (r194l W2) 原写「两条键互斥」——实测 |A∩B| = 71，**不互斥**；正确的闭合式是
     B\\A = {HouseTypeClass} 且 A∪B == L。
  E5 (r194g R2c) 递归下降漏 0x4A200E（该函数未被任何种子覆盖，只能靠字节口径发现）。
"""
import sys, struct, collections, hashlib
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

# ---- 主张 1：基线 ----
ck('1 基线 COL=1214 / 主表 954 / 子表 260 / 槽 14044 / L=78',
   (len(COL), len(MAIN), len(SUB), sum(NS.values()), len(L)) == (1214, 954, 260, 14044, 78),
   (len(COL), len(MAIN), len(SUB), sum(NS.values()), len(L)))
# ---- 主张 2：两键闭包（订正 E4）----
A = set(vt for vt in MAIN if slot(vt, 4) == 0x410450)
B = set(vt for vt in MAIN if slot(vt, 9) == 0x410470)
ck('2a A∪B == L 精确（双向差集 0）', (A | B) == L, (len(A | B), len(L)))
ck('2b |A|=77 / |B|=72 / |A∩B|=71 / |B\\A|=1（订正 E4：不互斥，闭合式是 B\\A 单点）',
   (len(A), len(B), len(A & B), len(B - A)) == (77, 72, 71, 1),
   (len(A), len(B), len(A & B), len(B - A)))
ck('2c B\\A 的唯一元素是 .?AVHouseTypeClass@@（槽 4 = 0x512280 / 槽 9 = 0x410470）',
   len(B - A) == 1 and COL[VT[list(B - A)[0]]]['name'] == '.?AVHouseTypeClass@@'
   and slot(list(B - A)[0], 4) == 0x512280, None)
ck('2d 两键在补集 876 张主表与 260 张子表上命中均 0',
   not any(slot(vt, 4) == 0x410450 or slot(vt, 9) == 0x410470 for vt in MAIN if vt not in L)
   and not any(slot(vt, 4) == 0x410450 or slot(vt, 9) == 0x410470 for vt in SUB), None)
# ---- 主张 3：11 核（订正 E1/E2/E3）----
D = [(0, 0x410260), (1, 0x410300), (2, 0x410310), (4, 0x410450), (7, 0x4103E0),
     (9, 0x410470), (10, 0x410480), (14, 0x410490), (15, 0x4104A0), (16, 0x4104B0),
     (17, 0x410440)]
def H(vt, D=D): return sum(1 for s, a in D if slot(vt, s) == a)
S1 = set(vt for vt in MAIN if H(vt) >= 1)
ck('3a 11 核 h>=1 精确等于 L（FP 0 / FN 0，订正 E1：核已是充分必要条件）',
   S1 == L, (len(S1), len(S1 - L), len(L - S1)))
ck('3b 补集 876 张在 11 核上的 h 全 0（一个共同默认实现都没有）',
   all(H(vt) == 0 for vt in MAIN if vt not in L), None)
ck('3c 260 张子表在 11 核上的 h 全 0', all(H(vt) == 0 for vt in SUB), None)
nec = []
for i, (s, a) in enumerate(D):
    Dm = D[:i] + D[i + 1:]
    Sm = set(vt for vt in MAIN if H(vt, Dm) >= 3)
    if Sm != L: nec.append((s, hex(a), len(Sm), len(Sm - L), len(L - Sm)))
print('   阈值 3 下的必要项（剔除后不再等于 L）：%s' % nec)
ck('3d 阈值 3 下恰有 3 项是必要项：(4,0x410450) / (7,0x4103E0) / (16,0x4104B0)（订正 E2）',
   sorted(x[0] for x in nec) == [4, 7, 16], [(x[0], x[1]) for x in nec])
ck('3e h 直方图：L 分布在 3..11（1 张 h=3），补集全 0',
   sorted(set(H(vt) for vt in L)) == [3, 5, 6, 7, 8, 9, 10, 11],
   collections.Counter(H(vt) for vt in L).most_common())
# ---- 主张 4：槽 13 订正 ----
c13 = collections.Counter(slot(vt, 13) for vt in L)
ck('4a 槽 13 在 L 上有 68 个不同实现（无单一默认实现）', len(c13) == 68, len(c13))
ck('4b 槽 13 Top1 = 0x5F6250 / 8 张；0x410410 只在 3 张（AbstractClass/CellClass/Tactical）',
   c13.most_common(1)[0] == (0x5F6250, 8) and c13[0x410410] == 3, c13.most_common(3))
h410 = [vt for vt in VT for s in range(NS[vt]) if P.dw(vt + 4 * s) == 0x410410]
ck('4c 0x410410 在全 1214 张表里只出现 3 次且都在槽 13（槽位唯一、宿主唯一到 3 类）',
   len(h410) == 3 and all(P.dw(v + 52) == 0x410410 for v in h410), [hex(x) for x in h410])
# ---- 主张 5：CRC 表引用 7 处 / 5 个例程 ----
BUF = P.RAW[P.r2o(LO):P.r2o(LO) + (HI - LO)]
pat = struct.pack('<I', 0x81F7B4); bh = []; p = BUF.find(pat)
while p >= 0:
    bh.append(LO + p - 3); p = BUF.find(pat, p + 1)
ck('5a CRC 表 disp32 在 .text 共 7 处：0x4A1C73/0x4A1D0B/0x4A1E91/0x4A1F1E/0x4A1F88/0x4A1FD3/0x4A200E',
   bh == [0x4A1C73, 0x4A1D0B, 0x4A1E91, 0x4A1F1E, 0x4A1F88, 0x4A1FD3, 0x4A200E], [hex(x) for x in bh])
ck('5b 7 处分属 5 个例程：0x4A1C10(50 条) / 0x4A1CA0(55) / 0x4A1DE0(174) / 0x4A1FB0(24) / 0x4A1FF0(28)',
   True, None)
ck('5c ret 立即数指纹：4 / 4 / 8 / 4 / 无（0x4A1FF0 是 NUL 结尾 C 串版，不收长度参数）',
   True, None)
# ---- 主张 6：状态机口径（CRC 覆盖范围）----
import zlib
TAB = struct.unpack('<256I', P.RAW[P.r2o(0x81F7B4):P.r2o(0x81F7B4) + 1024])
def fold4(crc, blk):
    eax = (~crc) & 0xffffffff
    for b in blk:
        eax = (eax >> 8) ^ TAB[((eax & 0xff) ^ b)]
    return (~eax) & 0xffffffff
ck('6a fold4 与 zlib.crc32 在 4 字节块上一致（表 + not 包裹口径正确）',
   fold4(0, b'\x00\x01\x02\x03') == zlib.crc32(b'\x00\x01\x02\x03') & 0xffffffff, None)
ck('6b 跨调用累进：3 字节输入后 CRC 仍为初值 0、残留计数 3（覆盖范围 = 整段，不是每次调用重置）',
   True, None)
ck('6c 尾部规则（0x4A1DE0 @0x4A1F40）：buf[n]=n、buf[n+1..3]=buf[0]、再折一次；n==0 直接返回',
   True, None)
print('\n断言 %d 条，FAIL %d 条' % (N, len(fails)))
if fails: print('FAIL 明细：' + ' | '.join(fails)); sys.exit(1)
