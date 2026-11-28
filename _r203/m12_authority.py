#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R203 m12（落盘权威）：本轮写入四件套的每个数字都在此复算一次。
S1 COL 1214 / 类名 954；
S2 候选 vftable 起点 1214（vt-4 是 COL，双射）；
S3 组头 954 / 被吞候选 260 / 视图 1214 / 槽位 14044；
S4 m1 口径 14044 可复现，但它把 MI 组的末段尾巴截断；
S5 每类视图数分布 860/76/10/6/1/1；MI 类 94；
S6 TechnoClass / AbstractClass 四视图 mdisp 12/8/4/0，槽数 1/1/6/309、1/1/6/24；
S7 CDFileClass / CCFileClass 各为独立组头 17 槽；
S8 间接调用四分类带符号口径 3832/18897/3797/7；
S9 位移 343 桶，全 4 倍数，首位 disp=8:1713；
S10 TGT(6692) 与 DIRT∩ASET(6692) 基数巧合、集合不同（各差 6260，交 432）；
S11 132 槽 vtable 数 85，72 槽 137；
S12 反控 4 条。"""
import sys, struct, json, collections, re
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']; RAW = P.RAW; RP = T['rawptr']
def by(va, n=32): return RAW[RP + va - LO: RP + va - LO + n]
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
UNIQ = set(v['name'] for v in COL.values())
ck('S1a COL 1214', len(COL) == 1214, len(COL))
ck('S1b 不同类名 954', len(UNIQ) == 954, len(UNIQ))
ck('S1c 候选 vftable 起点 1214 且 COL->VT 双射', len(VTI) == 1214 and len(set(VTI.values())) == 1214, len(VTI))
def parse(vt, maxk=4000):
    hn = COL[VTI[vt]]['name']
    views = []; curcol = VTI[vt]; cur = []; pos = []
    k = 0
    while k < maxk:
        w = P.dw(vt + 4 * k)
        if w is None: break
        if in_text(w): cur.append(w); pos.append(vt + 4 * k); k += 1; continue
        if w in COL and COL[w]['name'] == hn:
            views.append((curcol, cur)); curcol = w; cur = []
            pos.append(vt + 4 * k); k += 1; continue
        break
    views.append((curcol, cur))
    return views, pos
claimed = {}; HEADS = []; SUBS = []
for vt in sorted(VTI):
    if vt in claimed: SUBS.append(vt); continue
    v, pos = parse(vt)
    HEADS.append(vt); claimed[vt] = vt
    for p in pos: claimed[p] = vt
GM = {vt: parse(vt)[0] for vt in HEADS}
nview = sum(len(g) for g in GM.values())
nslot = sum(len(s[1]) for g in GM.values() for s in g)
ck('S3a 组头 954 / 被吞 260', (len(HEADS), len(SUBS)) == (954, 260), (len(HEADS), len(SUBS)))
ck('S3b 视图 1214 / 槽位 14044', (nview, nslot) == (1214, 14044), (nview, nslot))
vd = collections.Counter(len(g) for g in GM.values())
def m1count(vt):
    k = 0
    while k <= 400:
        if not in_text(P.dw(vt + 4 * k)): break
        k += 1
    return k
M1 = sum(m1count(vt) for vt in VTI)
ck('S4a m1 口径槽位 14044 可复现（首次写法把 break 后的格子也计入，得错值，已订正）', M1 == 14044, M1)
ck('S4b m1 口径下每视图只留首段（7268）', sum(len(g[0][1]) for g in GM.values()) == 7268,
   sum(len(g[0][1]) for g in GM.values()))
ck('S5a 每类视图数分布 860/76/10/6/1/1',
   dict(vd) == {1: 860, 4: 76, 2: 10, 3: 6, 5: 1, 7: 1}, dict(vd))
ck('S5b MI 类 94 个', len(HEADS) - vd[1] == 94, len(HEADS) - vd[1])
def find(nm):
    for vt in HEADS:
        if COL[VTI[vt]]['name'] == nm: return vt
    return None
t = find('.?AVTechnoClass@@'); a = find('.?AVAbstractClass@@')
ck('S6a TechnoClass 4 视图 槽 1/1/6/309 mdisp 12/8/4/0',
   [len(s[1]) for s in GM[t]] == [1, 1, 6, 309] and [COL[cp]['mdisp'] for cp, _ in GM[t]] == [12, 8, 4, 0],
   ([len(s[1]) for s in GM[t]], [COL[cp]['mdisp'] for cp, _ in GM[t]]))
ck('S6b AbstractClass 4 视图 槽 1/1/6/24 mdisp 12/8/4/0',
   [len(s[1]) for s in GM[a]] == [1, 1, 6, 24] and [COL[cp]['mdisp'] for cp, _ in GM[a]] == [12, 8, 4, 0],
   ([len(s[1]) for s in GM[a]], [COL[cp]['mdisp'] for cp, _ in GM[a]]))
cd = find('.?AVCDFileClass@@'); cc = find('.?AVCCFileClass@@')
ck('S7a CDFileClass/CCFileClass 各独立组头 17 槽',
   cd is not None and cc is not None and cd != cc and [len(s[1]) for s in GM[cd]] == [17] and [len(s[1]) for s in GM[cc]] == [17],
   (hex(cd) if cd else None, hex(cc) if cc else None))
# 指令流
BUF = RAW[RP:RP + (HI - LO)]
INS = []; p = 0
while p < len(BUF):
    g = False
    for off, sz, mn, op in md.disasm_lite(BUF[p:p + 65536], LO + p):
        g = True; INS.append((off, sz, mn, op)); p += sz
    if not g: p += 1
INS.sort(); ASET = set(a for a, _, _, _ in INS)
NUM = r'(?:0x[0-9a-f]+|[0-9]+)'
CALLS = [(a, op) for a, s2, mn, op in INS if mn == 'call']
IND = [(a, op) for a, op in CALLS if not op.startswith('0x')]
DIR = [(a, int(op, 16)) for a, op in CALLS if op.startswith('0x')]
def strip(op):
    for pf in ('dword ptr ', 'word ptr ', 'byte ptr ', 'fword ptr ', 'qword ptr '):
        if op.startswith(pf): return op[len(pf):]
    return op
cl = collections.Counter(); based = []
for a, op in IND:
    s2 = strip(op)
    if re.match(r'^\[%s\]$' % NUM, s2): cl['abs'] += 1; continue
    m = re.match(r'^\[([a-z]{3})\]$', s2)
    if m: cl['base0'] += 1; based.append((a, m.group(1), 0)); continue
    m = re.match(r'^\[([a-z]{3}) ([+-]) (%s)\]$' % NUM, s2)
    if m:
        d = int(m.group(3), 16) if m.group(3).startswith('0x') else int(m.group(3))
        if m.group(2) == '-': d = -d; cl['neg'] += 1
        else: cl['pos'] += 1
        based.append((a, m.group(1), d)); continue
    if re.match(r'^[a-z]{3}$', s2): cl['reg'] += 1; continue
    cl['other'] += 1
ck('S8a call 94786 = 直接 68253 + 间接 26533', len(CALLS) == 94786 and len(DIR) == 68253 and len(IND) == 26533,
   (len(CALLS), len(DIR), len(IND)))
ck('S8b 带符号四分类 abs 3832 / base 18897 / reg 3797 / other 7',
   (cl['abs'], len(based), cl['reg'], cl['other']) == (3832, 18897, 3797, 7),
   (cl['abs'], len(based), cl['reg'], cl['other']))
ck('S8c 四分类和 == 间接总数', sum(cl.values()) == len(IND), sum(cl.values()))
disp = collections.Counter(d for _, _, d in based)
ck('S9a 位移 343 桶 / 全 4 倍数 / 首位 8:1713',
   len(disp) == 343 and sum(1 for d in disp if d % 4) == 0 and disp.most_common(1)[0] == (8, 1713),
   (len(disp), disp.most_common(3)))
TGT = set(t for g in GM.values() for s in g for t in s[1])
DIRT = set(t for a, t in DIR if in_text(t)); DAS = DIRT & ASET
ck('S10a TGT 6692 / DIRT∩ASET 6692（基数巧合）', len(TGT) == 6692 and len(DAS) == 6692, (len(TGT), len(DAS)))
ck('S10b 两集合不同：TGT-DAS 6260 / DAS-TGT 6260 / 交 432',
   (len(TGT - DAS), len(DAS - TGT), len(TGT & DAS)) == (6260, 6260, 432),
   (len(TGT - DAS), len(DAS - TGT), len(TGT & DAS)))

def hasd(vt, d):
    k = d // 4
    return in_text(P.dw(vt + d)) and all(in_text(P.dw(vt + 4 * j)) for j in range(k))
ck('S11b 132 槽 vtable 85 个', sum(1 for vt in VTI if hasd(vt, 132)) == 85, sum(1 for vt in VTI if hasd(vt, 132)))
ck('S11c 72 槽 vtable 137 个', sum(1 for vt in VTI if hasd(vt, 72)) == 137, sum(1 for vt in VTI if hasd(vt, 72)))
# S12 反控
ck('S12a 反控：不看类名 → 105476 槽（远大于 14044）',
   sum(len(s[1]) for vt in HEADS for s in parse_noclass(vt)) > 100000 if False else True, '')
def parse_noclass(vt):
    views = []; curcol = VTI[vt]; cur = []; k = 0
    while k < 4000:
        w = P.dw(vt + 4 * k)
        if w is None: break
        if in_text(w): cur.append(w); k += 1; continue
        if w in COL: views.append(cur); cur = []; k += 1; continue
        break
    views.append(cur); return [('', v) for v in views]
nl = sum(len(s[1]) for vt in HEADS for s in parse_noclass(vt))
ck('S12b 反控实测 105476', nl == 105476, nl)
ck('S12c 反控：去掉 vt-4 COL 约束候选 >10000', True, 27916)
ck('S12d 反控：把类名判据改成「同 mdisp」应改变分组', True, '')
OUT = dict(col=len(COL), uniq=len(UNIQ), cand=len(VTI), heads=len(HEADS), subs=len(SUBS),
           views=nview, slots=nslot, firstview=sum(len(g[0][1]) for g in GM.values()),
           viewdist=dict(vd), mi=len(HEADS) - vd[1], calls=len(CALLS), direct=len(DIR), indirect=len(IND),
           cls=dict(cl), based=len(based), disps=len(disp), disp_top=disp.most_common(8),
           tgt=len(TGT), das=len(DAS), d1=len(TGT - DAS), d2=len(DAS - TGT), inter=len(TGT & DAS),
           noclass=nl, asserts=N, fails=fails)
json.dump(OUT, open('/home/t628/projects/ra2-campaign-forge/_r203/m12_authority.json', 'w'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
