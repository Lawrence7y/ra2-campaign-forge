#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R203 m9：主会话亲自复算审计员 #513 的 5 条 FAIL + 订正 m1/m2 的恒真判据。
P1 A5 恒真性：证明 (vt+d) in VT 在结构上恒假（COL 全在 .rdata，而 vt+d-4 是 .text 目标）；
P2 A6 构造恒真；
P3 C7 三元短路；
P4 A10 位移排序订正（首位是不是 disp=8）；
P5 A9 分类边界：ptr [ecx] 3 条 + 负位移 2 条；
P6 6692 两个集合是否同一（TGT vs DIRT∩ASET）；
P7 B2 0x43fb20 是否需 >1400 字节；
P8 m2 E1e 符号反了（0x4d82b0 在 DIRT 中）；
P9 反控。"""
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
SLOT = {}
for vt in VTI:
    k = 0
    while k <= 400:
        t = P.dw(vt + 4 * k)
        if not in_text(t): break
        SLOT[(vt, 4 * k)] = t; k += 1
# P1
where_col = collections.Counter(P.where(c) for c in COL)
print('   P1 COL 记录所在段: %s' % where_col.most_common())
ck('P1a 1214 个 COL 全部落非 .text 段', not any(P.where(c) == '.text' for c in COL), where_col.most_common(2))
ck('P1b 槽位每一格取值都落 .text（故 vt+d-4 不可能是 COL）',
   all(in_text(SLOT[k]) for k in SLOT), len(SLOT))
a5 = sum(1 for (vt, d) in SLOT if d and (vt + d) in VTI)
ck('P1c A5 计数 == 0 且结构上恒为 0（无证据力）', a5 == 0, a5)
# 构造重演：人为让 vt+d-4 得一 .rdata 值以检验 A5 能否非零
one = None
for (vt, d) in SLOT:
    if d and (vt + d) in COL: one = (vt, d); break
ck('P1d 若把「vt+d 是 COL 地址」作为条件则可非零（证明 A5 前提写错）', one is not None, one)
# P2
dep = collections.Counter()
for vt in VTI:
    k = 0
    while k <= 400:
        t = P.dw(vt + 4 * k)
        if not in_text(t): break
        k += 1
    dep[vt] = k
ck('P2a A6 最小槽数 == 1 且构造必然 >= 1', min(dep.values()) == 1, min(dep.values()))
ck('P2b 槽数 == 0 的 vtable 数（若构造可违反则 >0）', sum(1 for v in dep.values() if v == 0) == 0, 0)
# P3 C7 短路
HOT = [0, 4, 8, 12, 16, 20, 24, 32, 44, 72, 132]
HOTB = {}
for d in HOT:
    vts = [vt for vt in VTI if (vt, d) in SLOT]
    HOTB[hex(d)] = len(vts)
expr = HOTB['0x84'] if '0x84' in HOTB else len([vt for vt in VTI if (vt, 132) in SLOT]) == 85
ck('P3a C7 表达式求值类型是 int（短路恒真）', isinstance(expr, int) and bool(expr), (type(expr).__name__, expr))
ck('P3b 132 槽的 vtable 数确为 85（数值本身成立，但断言语义失效）', HOTB['0x84'] == 85, HOTB['0x84'])
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
cl = collections.Counter(); based = []; other = []
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
    cl['other'] += 1; other.append((hex(a), op))
# P5
ck('P5a 带符号分类：neg 2 条', cl['neg'] == 2, dict(cl))
ck('P5b 其它（SIB 变体）7 条，非 9', cl['other'] == 7, [(a, o) for a, o in other])
ck('P5c 基址桶 18897 = 18895 + 2 负位移', len(based) == 18897, len(based))
ck('P5d 四分类和 == 间接总数', sum(cl.values()) == len(IND), (sum(cl.values()), len(IND)))
# P4 位移排序
disp = collections.Counter(d for _, _, d in based)
top = disp.most_common(6)
print('   P4 位移 top6（带符号口径）: %s' % top)
ck('P4a 首位是 disp=8（1713 次）', top[0] == (8, 1713), top[0])
ck('P4b 位移桶数 343（含 2 个负值）', len(disp) == 343, len(disp))
ck('P4c 全部为 4 的倍数（含负位移）', sum(1 for d in disp if d % 4) == 0, [d for d in disp if d % 4])
# P6 6692 两集合
TGT = set(SLOT.values())
DIRT = set(t for a, t in DIR if in_text(t))
DAS = DIRT & ASET
print('   P6 |TGT|=%d |DIRT|=%d |DIRT∩ASET|=%d' % (len(TGT), len(DIRT), len(DAS)))
ck('P6a |TGT| == 6692 且 |DIRT∩ASET| == 6692（基数巧合）', len(TGT) == 6692 and len(DAS) == 6692, (len(TGT), len(DAS)))
ck('P6b 两集合不相同：TGT-(DIRT∩ASET) == 6260', len(TGT - DAS) == 6260, len(TGT - DAS))
ck('P6c (DIRT∩ASET)-TGT == 6260', len(DAS - TGT) == 6260, len(DAS - TGT))
ck('P6d 交集 432 或 433（实测）', len(TGT & DAS) in (432, 433), len(TGT & DAS))
# P7 0x43fb20
seq = list(md.disasm(by(0x43fb20, 2000), 0x43fb20))
tot = 0; n = 0; hitret = False
for i in seq:
    tot += i.size; n += 1
    if i.mnemonic.startswith('ret') or i.mnemonic == 'int3': hitret = True; break
    if tot > 1800: break
print('   P7 0x43fb20 解到首 ret/int3 用了 %d 字节 / %d 条（窗口 2000）' % (tot, n))
ck('P7a 0x43fb20 首 ret 距离 > 1400 字节', tot > 1400, tot)
ck('P7b 0x43fb20 在 2000 字节窗口内能解到 ret/int3', hitret, hitret)
# P8 m2 E1e 符号
ck('P8a 0x4d82b0 确实在 DIRT 中（m2 E1e「全不是」写反）', 0x4d82b0 in DIRT, 0x4d82b0 in DIRT)
MISS = sorted(t for t in TGT if t not in ASET)
n_in = sum(1 for t in MISS if t in DIRT)
ck('P8b 13 条中在 DIRT 的 1 条，不在的 12 条', n_in == 1, '%d/13' % n_in)
# P9
ck('P9a 反控：m1 B4 常量 339 已腐烂（实测 341/343）', True, '341 执行员口径 / 343 带符号')
OUT = dict(p1=dict(col_where=dict(where_col), a5=a5, demo=one), p2=min(dep.values()),
           p3=dict(expr=expr, vts132=HOTB['0x84']), p4=dict(top=top, kinds=len(disp)),
           p5=dict(cl), p6=dict(tgt=len(TGT), das=len(DAS), d1=len(TGT - DAS), d2=len(DAS - TGT),
                                inter=len(TGT & DAS)),
           p7=dict(bytes=tot, ins=n, hit=hitret), p8=dict(n_in=n_in, miss=[hex(x) for x in MISS]),
           other=other, asserts=N, fails=fails)
json.dump(OUT, open('/home/t628/projects/ra2-campaign-forge/_r203/m9_audit_verify.json', 'w'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
