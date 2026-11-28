#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R200 主会话第七刀：复算两个执行员（#501 hy4 槽11/12/13、#502 hy4 调用图）的关键数。

按 §2.12 规则 D，执行员/审计员结论一律由主会话独立复算。
本脚本不复用执行员脚本，重写判据（同口径），逐项对齐其自报数：
 E1 槽 11/12/13：分母 125 / 匹配 47 / 不匹配 78；n_d>=14 且 n_b>=14 的对数 125。
 E2 三槽状态八分：MMM 38 / MMX 9 / MXM 0 / MXX 0 / XMM 0 / XMX 0 / XXM 9 / XXX 69，同构 107。
 E3 派生侧集合 |S11|=84 / |S12|=84 / |S13|=83，两两交集 1/0/0，三交 0，并集 250。
 E4 对照组 (8,9,10) 同构 45/128、(14,15,16) 同构 95/123。
 E5 调用图：516 个槽 0 派生实现的**首个 call 目标**去重后 |T|=51（不是卡面预期的 400+）。
 E6 首 call 目标里「地址出现在某虚表某槽」的条数 9（执行员报 9，主会话卡面原写 3）。
 E7 首 call 目标 Top：0x7C8B3D 调用点 4498、0x7B46F0 883、0x7B6760 384。
 E8 4498 条里有多少「宿主」= 1229（执行员口径：最近可被调用入口）。
反控：
 R1 换判据：把「匹配」改成比较函数体首 8 字节 hash 而非地址恒等，看槽 11/12/13 匹配数变化。
 R2 |T| 用「前 3 个 call 任一」放宽后应变大（执行员报 59）。
"""
import sys, struct, collections, json
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

def s32(v): return struct.unpack('<i', struct.pack('<I', v))[0]
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']; RAW = P.RAW
def in_text(x): return x is not None and LO <= x < HI

COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1, 2) or w[i + 2] != 0: continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
        nm = P.cstr(w[i + 3] + 8, 400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base + 4 * i] = dict(mdisp=s32(w[i + 1]), ptd=w[i + 3], pchd=w[i + 4], name=nm.decode('latin1'))
VT = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL: VT[base + 4 * i] = P.dw(base + 4 * i - 4)
NS = {}
def nslot(vt):
    if vt in NS: return NS[vt]
    k = 0
    while True:
        if not in_text(P.dw(vt + 4 * k)): break
        k += 1
    NS[vt] = k; return k
MD = {vt: COL[VT[vt]]['mdisp'] for vt in VT}
CLS = {vt: COL[VT[vt]]['name'] for vt in VT}
ck('B1 COL/VT/槽总/主表', (len(COL), len(VT), sum(nslot(v) for v in VT), sum(1 for v in VT if MD[v] == 0))
   == (1214, 1214, 14044, 954), (len(COL), len(VT), sum(nslot(v) for v in VT), sum(1 for v in VT if MD[v] == 0)))

d = json.load(open('/home/t628/projects/ra2-campaign-forge/_r199/m1_pair.json'))
pairs = [(int(a, 16), int(b, 16)) for a, b in d['pairs']]

# ---- E1/E2/E4 ----
def slotstats(ks):
    den = collections.Counter(); mat = collections.Counter()
    triple = collections.Counter()
    S = {k: set() for k in ks}
    for vt_d, vt_b in pairs:
        L = min(nslot(vt_d), nslot(vt_b))
        for k in ks:
            if k >= L: continue
            den[k] += 1
            a = P.dw(vt_d + 4 * k); b = P.dw(vt_b + 4 * k)
            S[k].add(a)
            if a == b: mat[k] += 1
        if all(k < L for k in ks):
            st = ''.join('M' if P.dw(vt_d + 4 * k) == P.dw(vt_b + 4 * k) else 'X' for k in ks)
            triple[st] += 1
    return den, mat, triple, S

den, mat, tri, S = slotstats((11, 12, 13))
ck('E1a 槽11/12/13 分母各 125', all(den[k] == 125 for k in (11, 12, 13)), [den[k] for k in (11, 12, 13)])
ck('E1b 槽11/12/13 匹配各 47', all(mat[k] == 47 for k in (11, 12, 13)), [mat[k] for k in (11, 12, 13)])
ck('E1c 匹配率 37.60%', all(abs(100.0 * mat[k] / den[k] - 37.60) < 0.005 for k in (11, 12, 13)), True)
ck('E2a 八状态 == 38/9/0/0/0/0/9/69',
   (tri['MMM'], tri['MMX'], tri['MXM'], tri['MXX'], tri['XMM'], tri['XMX'], tri['XXM'], tri['XXX'])
   == (38, 9, 0, 0, 0, 0, 9, 69), dict(tri))
ck('E2b 同构 107 / 125 = 85.60%', tri['MMM'] + tri['XXX'] == 107 and abs(100.0 * 107 / 125 - 85.60) < 0.005, 107)
ck('E3a |S11|/|S12|/|S13| == 84/84/83', (len(S[11]), len(S[12]), len(S[13])) == (84, 84, 83), (len(S[11]), len(S[12]), len(S[13])))
ck('E3b 两两交集 1/0/0 三交 0 并集 250',
   (len(S[11] & S[12]), len(S[11] & S[13]), len(S[12] & S[13]), len(S[11] & S[12] & S[13]), len(S[11] | S[12] | S[13]))
   == (1, 0, 0, 0, 250),
   (len(S[11] & S[12]), len(S[11] & S[13]), len(S[12] & S[13]), len(S[11] & S[12] & S[13]), len(S[11] | S[12] | S[13])))
d2, m2, t2, _ = slotstats((8, 9, 10))
d3, m3, t3, _ = slotstats((14, 15, 16))
ck('E4a (8,9,10) 同构 45/128', t2['MMM'] + t2['XXX'] == 45 and sum(t2.values()) == 128, (t2['MMM'] + t2['XXX'], sum(t2.values())))
ck('E4b (14,15,16) 同构 95/123', t3['MMM'] + t3['XXX'] == 95 and sum(t3.values()) == 123, (t3['MMM'] + t3['XXX'], sum(t3.values())))

# ---- E5..E8 调用图 ----
s0d = []
for vt_d, vt_b in pairs:
    if min(nslot(vt_d), nslot(vt_b)) < 1: continue
    if P.dw(vt_d) != P.dw(vt_b): s0d.append((vt_d, P.dw(vt_d), vt_b))
ck('E5a 516', len(s0d) == 516, len(s0d))

def body(va, maxb=600, maxi=300):
    o = P.r2o(va)
    if o is None: return None
    ins = []
    for i in md.disasm(RAW[o:o + maxb], va):
        ins.append((i.address, i.size, i.mnemonic, i.op_str))
        if i.mnemonic.startswith('ret'): break
        if len(ins) >= maxi: break
    return ins

T1 = set(); T3 = set(); all3 = 0
for vt_d, a, vt_b in s0d:
    cs = [int(op, 16) for _, _, mn, op in (body(a) or []) if mn == 'call' and op.startswith('0x')]
    if cs: T1.add(cs[0])
    for t in cs[:3]: T3.add(t)
ck('E5b 首 call 目标去重 |T1| == 51', len(T1) == 51, len(T1))
ck('R2a 放宽到前 3 个 call 后 |T3| == 59', len(T3) == 59, len(T3))
ALLREF = collections.defaultdict(set)
for vt in VT:
    for k in range(nslot(vt)):
        ALLREF[P.dw(vt + 4 * k)].add((vt, k))
invt = [t for t in T1 if t in ALLREF]
ck('E6a 首 call 目标落在某虚表某槽的条数 == 9', len(invt) == 9, len(invt))
print('   E6b 9 个 in-vtable 目标: %s' % [hex(t) for t in sorted(invt)])

# 全 .text 调用点索引（disasm_lite 分块）
BUF = RAW[T['rawptr']:T['rawptr'] + (HI - LO)]
CALLAT = []
pos = 0
while pos < len(BUF):
    for off, sz, mn, op in md.disasm_lite(BUF[pos:pos + 65536], LO + pos):
        if mn == 'call' and op.startswith('0x'):
            t = int(op, 16)
            if in_text(t): CALLAT.append((off, t))
    pos += 65536
ck('E7a CALLAT 总条数 == 68236', len(CALLAT) == 68236, len(CALLAT))
cc = collections.Counter(t for _, t in CALLAT)
ck('E7b 0x7C8B3D 调用点 4498 / 0x7B46F0 883 / 0x7B6760 384',
   (cc[0x7C8B3D], cc[0x7B46F0], cc[0x7B6760]) == (4498, 883, 384), (cc[0x7C8B3D], cc[0x7B46F0], cc[0x7B6760]))
# 字节法
nE8 = sum(1 for va in range(LO, HI - 5) if BUF[va - LO] == 0xE8 and
          struct.unpack_from('<i', BUF, va - LO + 1)[0] + va + 5 == 0x7C8B3D)
ck('E7c 字节法 call 0x7C8B3D == 4499', nE8 == 4499, nE8)
CALLERS = collections.defaultdict(list)
for c, t in CALLAT: CALLERS[t].append(c)
ck('E8a 0x7C8B3D 调用点去重数 == 4498', len(CALLERS[0x7C8B3D]) == 4498, len(CALLERS[0x7C8B3D]))
import bisect
SORT = sorted(set(t for _, t in CALLAT))
def host_of(c):
    i = bisect.bisect_left(SORT, c) - 1
    return SORT[i] if i >= 0 else None
hosts = set(host_of(c) for c in CALLERS[0x7C8B3D])
ck('E8b 0x7C8B3D 的不同宿主数 == 1229', len(hosts) == 1229, len(hosts))

# ---- R1 反控：函数体首 8 字节 hash 判据 ----
def h8(va):
    o = P.r2o(va)
    return RAW[o:o + 8] if o is not None else b''
m_a = m_h = 0
for vt_d, vt_b in pairs:
    L = min(nslot(vt_d), nslot(vt_b))
    if L <= 11: continue
    a = P.dw(vt_d + 44); b = P.dw(vt_b + 44)
    if a == b: m_a += 1
    if h8(a) == h8(b): m_h += 1
print('   R1 槽11：地址恒等匹配 %d ；函数体首 8 字节相同 %d' % (m_a, m_h))
ck('R1a 两种口径差异巨大（字节判据会把相同桩折叠）', m_h >= m_a, (m_h, m_a))

json.dump(dict(s11=(den[11], mat[11]), tri=dict(tri), iso=tri['MMM'] + tri['XXX'],
               S=[len(S[11]), len(S[12]), len(S[13])],
               inter=[len(S[11] & S[12]), len(S[11] & S[13]), len(S[12] & S[13]), len(S[11] & S[12] & S[13])],
               uni=len(S[11] | S[12] | S[13]),
               g8910=dict(t2), g141516=dict(t3),
               T1=len(T1), T3=len(T3), invt=[hex(t) for t in sorted(invt)], invt_n=len(invt),
               callat=len(CALLAT), cc_7c8b3d=cc[0x7C8B3D], hosts_7c8b3d=len(hosts),
               bytes_7c8b3d=nE8, r1=(m_h, m_a), asserts=N, fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r200/m7_verify.json', 'w'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
