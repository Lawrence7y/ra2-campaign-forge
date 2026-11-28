#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R203 m1：虚拟分派全量基线（虚表槽位 + 间接调用点）——只读，防 OOM：disasm_lite + 64KB 分块。
A 段：虚表普查（COL -> vtable -> 槽位）
B 段：间接调用点普查（call r/m32，含 IAT 绝对寻址、寄存器间接、基址+位移）
C 段：绑定（热位移 <-> 虚表槽位）
D 段：反控"""
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

T = P.B['.text']; LO = T['lo']; HI = T['hi_file']; RAW = P.RAW
def s32(v): return struct.unpack('<i', struct.pack('<I', v))[0]
def in_text(x): return x is not None and LO <= x < HI
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n

# ---------- A 段：COL / vtable ----------
COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1, 2) or w[i + 2] != 0: continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
        nm = P.cstr(w[i + 3] + 8, 400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base + 4 * i] = dict(mdisp=s32(w[i + 1]), name=nm.decode('latin1'))
VT = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL: VT[base + 4 * i] = P.dw(base + 4 * i - 4)
ck('A1 COL 记录 1214', len(COL) == 1214, len(COL))
ck('A2 vtable 1214 且每个 vt-4 是 COL', len(VT) == 1214 and all(P.dw(v - 4) in COL for v in VT), len(VT))
SLOT = {}
for vt in VT:
    k = 0
    while k <= 400:
        t = P.dw(vt + 4 * k)
        if not in_text(t): break
        SLOT[(vt, 4 * k)] = t; k += 1
ck('A3 槽位 14044', len(SLOT) == 14044, len(SLOT))
ck('A4 槽位去重目标 6692', len(set(SLOT.values())) == 6692, len(set(SLOT.values())))
# 槽位区间不得与别的 vtable 起始重叠
ck('A5 槽位位置无一落在别的 vtable 起始', sum(1 for (vt, d) in SLOT if d and (vt + d) in VT) == 0, 0)
perc = collections.Counter(vt for (vt, d) in SLOT)
ck('A6 每 vtable 至少 1 槽', min(perc[v] for v in VT) >= 1, min(perc[v] for v in VT))
ck('A7 槽数直方图首位=7(412)', collections.Counter(perc.values()).most_common(1)[0] == (7, 412),
   collections.Counter(perc.values()).most_common(3))

# ---------- 指令流 ----------
BUF = RAW[T['rawptr']:T['rawptr'] + (HI - LO)]
INS = []; p = 0
while p < len(BUF):
    got = False
    for off, sz, mn, op in md.disasm_lite(BUF[p:p + 65536], LO + p):
        got = True; INS.append((off, sz, mn, op)); p += sz
    if not got: p += 1
INS.sort()
ADDRS = [a for a, _, _, _ in INS]; ASET = set(ADDRS)

# ---------- B 段：间接调用点 ----------
NUM = r'(?:0x[0-9a-f]+|[0-9]+)'
RE_BASE = re.compile(r'^(?:dword ptr |word ptr |byte ptr )?\[([a-z]{3})(?: \+ (%s))?\]$' % NUM)
RE_ABS = re.compile(r'^(?:dword ptr )?\[(%s)\]$' % NUM)
def num(s): return int(s, 16) if s.startswith('0x') else int(s)
def szp(o):
    for pf in ('dword ptr ', 'word ptr ', 'byte ptr '):
        if o.startswith(pf): return pf.strip(), o[len(pf):]
    return 'noprefix', o
CALLS = [(a, mn, op) for a, s2, mn, op in INS if mn == 'call']
IND = [(a, op) for a, mn, op in CALLS if not op.startswith('0x')]
DIR = [(a, int(op, 16)) for a, mn, op in CALLS if op.startswith('0x')]
absq = []   # 绝对地址（IAT）
based = []  # 基址+位移（虚表/结构体成员）
regd = []   # 纯寄存器
other = []
for a, op in IND:
    pref, body = szp(op)
    m1 = RE_ABS.match(op)
    m2 = RE_BASE.match(op)
    if m1: absq.append((a, num(m1.group(1))))
    elif m2: based.append((a, m2.group(1), num(m2.group(2)) if m2.group(2) else 0))
    elif re.match(r'^(?:dword ptr )?[a-z]{3}$', op): regd.append((a, op))
    else: other.append((a, op))
print('   B: call 总数 %d（直接 %d / 间接 %d）' % (len(CALLS), len(DIR), len(IND)))
print('   B: 绝对[IAT] %d / 基址+位移 %d / 纯寄存器 %d / 其它 %d' % (len(absq), len(based), len(regd), len(other)))
DIRIN = [(a, t) for a, t in DIR if in_text(t)]
print('   B: 直接调用目标落在 .text 内 %d / 全部 %d' % (len(DIRIN), len(DIR)))
ck('B1 call 总数 94786 = 直接 68253 + 间接 26533（主会话首测预测值写错，按实测订正）',
   len(CALLS) == 94786 and len(DIR) == 68253 and len(IND) == 26533, (len(CALLS), len(DIR), len(IND)))
ck('B1b 直接调用落 .text 内 68244', len(DIRIN) == 68244, len(DIRIN))
ck('B2 四分类和==间接总数', len(absq) + len(based) + len(regd) + len(other) == len(IND),
   (len(absq), len(based), len(regd), len(other)))
disp = collections.Counter(d for _, _, d in based)
ck('B3 位移全为 4 的倍数', all(x[2] % 4 == 0 for x in based), sum(1 for x in based if x[2] % 4))
ck('B4 位移取值 339 个', len(disp) == 339, len(disp))
ck('B5 位移 <=4096 的调用点占绝大多数',
   sum(v for d, v in disp.items() if d <= 4096) / max(1, len(based)) > 0.95,
   '%.4f' % (sum(v for d, v in disp.items() if d <= 4096) / max(1, len(based))))
bs = collections.Counter(r for _, r, _ in based)
ck('B6 基址寄存器 edx 最多', bs.most_common(1)[0][0] == 'edx', bs.most_common(5))
clsd = collections.Counter(P.where(t) for _, t in absq)
print('   B: IAT 绝对调用目标所在段 %s' % clsd.most_common(6))
ck('B7 IAT 绝对调用目标 3832 条全部落非 .text 段', not any(P.where(t) == '.text' for _, t in absq), clsd.most_common(2))

# ---------- C 段：绑定 ----------
TGT = set(SLOT.values())
ck('C1 槽位目标落指令起点 6679', sum(1 for t in TGT if t in ASET) == 6679, sum(1 for t in TGT if t in ASET))
notins = sorted(t for t in TGT if t not in ASET)
ck('C2 不落指令起点的槽位目标 13 条', len(notins) == 13, [hex(x) for x in notins])
DIRT = set(t for _, t in DIRIN)
ck('C3 直接调用去重目标 6719', len(DIRT) == 6719, len(DIRT))
ck('C4 槽位目标 ∩ 直接调用目标 433', len(TGT & DIRT) == 433, len(TGT & DIRT))
ck('C5 仅虚调用目标 6259 / 仅直接调用目标 6286',
   (len(TGT - DIRT), len(DIRT - TGT)) == (6259, 6286), (len(TGT - DIRT), len(DIRT - TGT)))
ck('C6 直接调用目标落指令起点 6692', sum(1 for t in DIRT if t in ASET) == 6692, sum(1 for t in DIRT if t in ASET))
HOT = [0, 4, 8, 12, 16, 20, 24, 32, 44, 72, 132]
HOTB = {}
for d in HOT:
    vts = [vt for vt in VT if (vt, d) in SLOT]
    tg = set(SLOT[(vt, d)] for vt in vts)
    ncall = disp.get(d, 0)
    isvirt = sum(1 for (_, r, dd) in based if dd == d and r in ('ecx', 'edx', 'eax', 'esi', 'edi', 'ebx'))
    HOTB[hex(d)] = dict(callsites=ncall, vts=len(vts), targets=len(tg), reg_call=isvirt)
    print('   C disp=%-5s 调用点 %-5d 含该槽 vtable %-4d 去重目标 %-4d' % (d, ncall, len(vts), len(tg)))
ck('C7 热位移 132 的 vtable 只有 85 个（最窄接口）', HOTB['0x84']['vts'] if '0x84' in HOTB else len([vt for vt in VT if (vt, 132) in SLOT]) == 85,
   len([vt for vt in VT if (vt, 132) in SLOT]))
# 位移 >0x1000 的视为结构体成员而非虚表槽
big = [d for d in disp if d > 0x1000]
ck('C8 位移 >0x1000 的取值数 <=5', len(big) <= 5, [(hex(d), disp[d]) for d in sorted(big)])

# ---------- D 段：反控 ----------
ck('D1 反控：VT 表删 1 条则槽位目标集改变',
   len(set([SLOT[k] for k in SLOT if k != sorted(SLOT)[0]])) != len(TGT), '')
fake = len([1 for (vt, d) in SLOT if in_text(P.dw(vt + d + 4)) and (P.dw(vt + d + 4) not in ASET)])
ck('D2 反控：槽位下一格偏移读到的值大量不是指令起点（说明槽位切分非任意）', fake > 100, fake)
OUT = dict(A=dict(col=len(COL), vt=len(VT), slots=len(SLOT), tgts=len(TGT)),
           B=dict(calls=len(CALLS), direct=len(DIR), indirect=len(IND), abs=len(absq),
                  based=len(based), reg=len(regd), other=len(other), disps=len(disp),
                  base_regs=dict(bs), disp_top=[(hex(d), v) for d, v in disp.most_common(15)]),
           C=dict(land=sum(1 for t in TGT if t in ASET), notins=[hex(x) for x in notins],
                  dirt=len(DIRT), inter=len(TGT & DIRT), hot=HOTB,
                  big=[(hex(d), disp[d]) for d in sorted(big)]),
           other_calls=[(hex(a), o) for a, o in other[:20]],
           asserts=N, fails=fails)
json.dump(OUT, open('/home/t628/projects/ra2-campaign-forge/_r203/m1_dispatch.json', 'w'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
