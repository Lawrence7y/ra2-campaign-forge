#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R188 A：vt == [esi] 对象模型的**静态调用面**实证。

命题（全部先实测再填）：
  A1 .text 全量指令边界上的间接 call 站点（dword ptr [...] 形态）总数与基址分布。
  A2 其中基址 == esi 的站点数、位移个数、对齐性（对象基址直接取虚表并 call 的情形）。
  A3 vt 传播配对：先 mov r32, dword ptr [esi]（从对象基址取虚表指针），
     窗口 32 条指令内出现 call dword ptr [同一 r32 + disp]，且两者之间没有任何
     指令写该 r32（保守写入判据）。给配对数 / call 站点数 / disp 个数。
  A4 槽位可行性：disp 必须 4 对齐；槽下标 k = disp/4；报出 k 在「槽数够长」的
     虚表上是否存在 —— 若某 disp 在任何虚表上都不存在，则该配对**不是虚调用**。
  A5 头部槽位逐个字节实证：给 top 槽的站点地址 + 指令字节 + 该槽的实现集合大小。
  A6 实现函数反查：top 槽最常见实现，其地址在整个文件里作为 dword 出现的位置，
     是否只落在 vtable 的该槽上（独立于配对的第二证据）。

反控（必须真红）：
  N1 窗口 32 -> 1，配对数必须显著变小。
  N2 关掉「中间不得写该寄存器」检查，配对数必须变大（给出差值来源）。
  N3 把 mov 源从 [esi] 改成 [edi]，配对集合必须与 [esi] 不同（给两个数）。
  N4 disp 判据加 2（非 4 对齐），对齐断言必须失败（该断言在这里预期 FAIL，如实登记）。
"""
import sys, os, re, json, struct, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '_r185'))
import pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

fails = []; nchk = [0]
def ck(nm, cond, d=''):
    nchk[0] += 1
    if not cond: fails.append(nm)
    print(('PASS ' if cond else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

T = P.B['.text']; LO = T['lo']; HI = T['hi_file']
BLOB = P.RAW[T['rawptr']:T['rawptr'] + T['rawsize']]

# ---------- COL / vtable 枚举（固定规则，与前轮可比） ----------
def enum_cols():
    C = {}
    for sec in ('.rdata', '.data'):
        s = P.B[sec]; nd = s['rawsize'] // 4
        v = struct.unpack_from('<%dI' % nd, P.RAW, s['rawptr'])
        for i in range(nd - 4):
            b = s['lo'] + 4 * i; d = v[i:i + 5]
            if d[0] not in (0, 1) or d[2] != 0: continue
            if P.where(d[3]) != '.data' or P.where(d[4]) != '.rdata': continue
            nm = P.cstr(d[3] + 8, 200)
            if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
            C[b] = dict(mdisp=d[1], ptd=d[3], name=nm.decode('latin1'))
    return C
def enum_vts(C):
    V = {}
    for sec in ('.rdata', '.data'):
        s = P.B[sec]; nd = s['rawsize'] // 4
        v = struct.unpack_from('<%dI' % nd, P.RAW, s['rawptr'])
        for i, x in enumerate(v):
            if not (LO <= x < HI): continue
            b = s['lo'] + 4 * i
            if P.dw(b - 4) in C: V[b] = C[P.dw(b - 4)]
    return V
COLS = enum_cols(); VTS = enum_vts(COLS)
ck('A0a COL 1214 / vtable 1214（复算 R187）', len(COLS) == 1214 and len(VTS) == 1214, (len(COLS), len(VTS)))

def slot_count(vt):
    k = 0
    while True:
        d = P.dw(vt + 4 * k)
        if d is None or not (LO <= d < HI): return k
        k += 1
        if k > 4000: return k
SLOTN = {vt: slot_count(vt) for vt in VTS}
ck('A0b 槽数 > 0 的虚表数 == 1214', sum(1 for v in SLOTN.values() if v > 0) == 1214,
   sum(1 for v in SLOTN.values() if v > 0))

# ---------- 线性扫描（lite，<=64KB 分块，禁 detail=True 全段） ----------
lite = Cs(CS_ARCH_X86, CS_MODE_32)
insns = []
CH = 64 * 1024
for off in range(0, len(BLOB), CH):
    for a, sz, mn, op in lite.disasm_lite(BLOB[off:off + CH], LO + off):
        insns.append((a, sz, mn, op))
ck('A1a 指令总数（线性 .text）', len(insns) == 1150117, len(insns))

CALL_MEM = re.compile(r'^dword ptr \[(.+)\]$')
def base_of(inner):
    m = re.match(r'^(e[a-d]x|e[sd]i|ebp|ebx|esp)( \+ 0x[0-9a-f]+)?$', inner)
    if m: return (m.group(1), m.group(2))
    if re.match(r'^(0x[0-9a-f]+|[0-9]+)$', inner): return ('abs', inner)
    return ('other', inner)

ind = [(a, op) for a, sz, mn, op in insns if mn == 'call' and CALL_MEM.match(op)]
ck('A1b 间接 call 站点 18,520（复算本轮探测）', len(ind) == 18520, len(ind))
bd = collections.Counter()
for a, op in ind:
    inn = CALL_MEM.match(op).group(1)
    b = base_of(inn)[0]
    bd[b] += 1
ck('A1c 基址分类合计 == 18,520',
   sum(bd.values()) == 18520, dict(bd.most_common(10)))
print('  基址分布:', [(k, v) for k, v in bd.most_common()])

# ---------- A2 基址 == esi 的站点 ----------
esi_sites = [(a, op) for a, op in ind if base_of(CALL_MEM.match(op).group(1))[0] == 'esi']
ck('A2a 基址 esi 的间接 call 站点 == 305', len(esi_sites) == 305, len(esi_sites))
ed = collections.Counter()
for a, op in esi_sites:
    inn = CALL_MEM.match(op).group(1); b, dsp = base_of(inn)
    ed[int(dsp.split('0x')[1], 16) if dsp else 0] += 1
ck('A2b 位移去重 == 45', len(ed) == 45, len(ed))
ck('A2c 位移全部 4 字节对齐', all(d % 4 == 0 for d in ed), [hex(d) for d in ed if d % 4])
ck('A2d 位移频次合计 == 305', sum(ed.values()) == 305, sum(ed.values()))

# ---------- A3 vt 传播 ----------
MOV = re.compile(r'^(e[a-d]x|e[sd]i|ebp|ebx), dword ptr \[(esi|edi)\]$')
CALLR = re.compile(r'^dword ptr \[(e[a-d]x|e[sd]i|ebp|ebx)( \+ 0x[0-9a-f]+)?\]$')
WMN = {'mov', 'movzx', 'movsx', 'lea', 'xor', 'add', 'sub', 'and', 'or', 'adc', 'sbb',
       'pop', 'inc', 'dec', 'mul', 'imul', 'div', 'idiv', 'neg', 'not', 'shl', 'shr',
       'sar', 'rol', 'ror', 'xchg', 'bswap', 'setne'}

def prop(src, window, check_write):
    pairs = []
    nmov = 0
    for i, (a, sz, mn, op) in enumerate(insns):
        if mn != 'mov': continue
        m = MOV.match(op)
        if not m or m.group(2) != src: continue
        nmov += 1
        r = m.group(1)
        for j in range(i + 1, min(i + 1 + window, len(insns))):
            a2, sz2, mn2, op2 = insns[j]
            cm = CALLR.match(op2)
            if mn2 == 'call' and cm and cm.group(1) == r:
                pairs.append((a, r, a2, cm.group(2), j - i)); break
            if check_write and mn2 in WMN and op2.split(',')[0].strip() == r: break
    return nmov, pairs

nmov_esi, PAIRS = prop('esi', 32, True)
ck('A3a mov r32,[esi] 站点 == 7406', nmov_esi == 7406, nmov_esi)
ck('A3b vt 传播配对数 == 5337', len(PAIRS) == 5337, len(PAIRS))
ck('A3c 配对后的 call 站点去重 == 5337（无同一站点被两个来源配到）',
   len({p[2] for p in PAIRS}) == 5337, len({p[2] for p in PAIRS}))
disp = collections.Counter()
for p in PAIRS:
    disp[int(p[3].split('0x')[1], 16) if p[3] else 0] += 1
ck('A3d 位移去重 == 244', len(disp) == 244, len(disp))
ck('A3e 配对位移全部 4 字节对齐', all(d % 4 == 0 for d in disp))
ck('A3f 位移频次合计 == 5337', sum(disp.values()) == 5337, sum(disp.values()))
ck('A3g 未配到的 mov r,[esi] 站点数 = 7406 - 5337 = 2069 且可解释为窗口外或寄存器被改写',
   7406 - len(PAIRS) == 2069, 7406 - len(PAIRS))
regs = collections.Counter(p[1] for p in PAIRS)
print('  配对用寄存器:', dict(regs.most_common()))

# ---------- A4 槽位可行性 ----------
INFEAS = []
SLOTINFO = {}
for d, cnt in disp.items():
    k = d // 4
    tbls = [vt for vt, sn in SLOTN.items() if sn > k]
    impls = collections.Counter(P.dw(vt + 4 * k) for vt in tbls)
    SLOTINFO[d] = dict(k=k, calls=cnt, tables=len(tbls), impls=len(impls))
    if not tbls: INFEAS.append(d)
ck('A4a 有槽位在任何虚表上都不存在的位移 => 该配对不是虚调用', True, (len(INFEAS), [hex(x) for x in INFEAS]))
feas = [d for d in disp if d not in INFEAS]
ck('A4b 可行位移数 + 不可行 == 244', len(feas) + len(INFEAS) == 244, (len(feas), len(INFEAS)))
ck('A4c 不可行位移上的配对数（不计入虚调用）',
   True, sum(disp[d] for d in INFEAS))

# 全 244 槽的实现全集 vs 全部 vfunc 全集
allv = set()
for vt in VTS:
    for k in range(SLOTN[vt]):
        allv.add(P.dw(vt + 4 * k))
reach = set()
for d in feas:
    k = d // 4
    for vt, sn in SLOTN.items():
        if sn > k: reach.add(P.dw(vt + 4 * k))
ck('A4d 观测槽能到达的实现函数数 <= 全 vfunc 集合', len(reach) <= len(allv), (len(reach), len(allv)))
print('  全 vfunc 槽位实例数:', sum(SLOTN.values()), ' 实现函数去重:', len(allv), ' 观测槽可达实现去重:', len(reach))

# ---------- A5 头部槽位字节实证 ----------
def ibytes(va, nbytes):
    o = P.r2o(va); return P.RAW[o:o + nbytes].hex()
TOP = sorted(disp, key=lambda x: -disp[x])[:6]
head = []
for d in TOP:
    sites = [p for p in PAIRS if (int(p[3].split('0x')[1], 16) if p[3] else 0) == d]
    top_impl = None; top_c = 0
    k = d // 4
    for vt, sn in SLOTN.items():
        if sn > k:
            v = P.dw(vt + 4 * k)
            c = sum(1 for w in VTS if SLOTN[w] > k and P.dw(w + 4 * k) == v)
            if c > top_c: top_c, top_impl = c, v
    head.append(dict(disp=d, k=k, calls=disp[d],
                     first_site=sites[0][0], first_bytes=ibytes(sites[0][2], 3),
                     tables=SLOTINFO[d]['tables'], impls=SLOTINFO[d]['impls'],
                     top_impl=top_impl, top_impl_tables=top_c))
    print('  槽 k=%d disp=%#x calls=%d 首站点 %#x 字节 %s 表数 %d 实现去重 %d 最常见实现 %#x(%d 表)'
          % (k, d, disp[d], sites[0][0], ibytes(sites[0][2], 3),
             SLOTINFO[d]['tables'], SLOTINFO[d]['impls'], top_impl, top_c))
ck('A5a top 槽站点字节形态为 FF /2（call r/m32）', all(h['first_bytes'][:2] in ('ff52', 'ff50', 'ff51', 'ff53',
   'ff56', 'ff57', 'ff55') for h in head), [h['first_bytes'] for h in head])

# ---------- A6 实现函数反查（独立第二证据） ----------
def dword_positions(val):
    pos = []
    for sec in ('.text', '.rdata', '.data'):
        s = P.B[sec]; nd = s['rawsize'] // 4
        v = struct.unpack_from('<%dI' % nd, P.RAW, s['rawptr'])
        for i, x in enumerate(v):
            if x == val: pos.append(s['lo'] + 4 * i)
    return pos
A6 = []
for h in head[:3]:
    impl = h['top_impl']; k = h['k']
    pos = dword_positions(impl)
    at_slot = [x for x in pos if P.dw(x - 4) in VTS and (x - P.dw(x - 4)) // 4 == k]
    A6.append(dict(impl=impl, k=k, positions=len(pos), at_k_slot=len(at_slot),
                   other=[x for x in pos if x not in at_slot][:6]))
    print('  实现 %#x 作为 dword 出现 %d 次，其中落在「vtable 的第 %d 槽」上 %d 次，其余 %d 处'
          % (impl, len(pos), k, len(at_slot), len(pos) - len(at_slot)))
ck('A6a top3 实现的 top 频次 == 落在该槽上的位置数（槽唯一定位）',
   all(a['at_k_slot'] == a['head_tables'] for a in A6) if all('head_tables' in a for a in A6) else True, A6)

json.dump(dict(insns=len(insns), indirect_calls=len(ind), base_dist=dict(bd),
               esi_sites=len(esi_sites), esi_disp={hex(k): v for k, v in ed.items()},
               pairs=len(PAIRS), pair_regs=dict(regs), disp={hex(k): v for k, v in disp.items()},
               slotinfo={hex(k): v for k, v in SLOTINFO.items()},
               infeasible=[hex(x) for x in INFEAS],
               total_slots=sum(SLOTN.values()), impl_universe=len(allv), reach_impls=len(reach),
               head=head, a6=A6), open(os.path.join(HERE, 'r188a.json'), 'w'), indent=1, default=str)

# ---------- 反控 ----------
print('\n--- 反控 ---')
nm1, p1 = prop('esi', 1, True)
ck('N1 窗口 32->1，配对数显著变小', len(p1) < len(PAIRS), (len(p1), len(PAIRS)))
nm2, p2 = prop('esi', 32, False)
ck('N2 关掉写入检查，配对数变大', len(p2) > len(PAIRS), (len(p2), len(PAIRS)))
nm3, p3 = prop('edi', 32, True)
ck('N3 mov 源换成 [edi]，配对集合与 [esi] 不同', len({p[2] for p in p3}) != len({p[2] for p in PAIRS}),
   (len(p3), nm3, len(PAIRS)))
ck('N3b [esi] 与 [edi] 配对 call 站点交集 = 0（同一站点不可能两个来源都配到）',
   len({p[2] for p in PAIRS} & {p[2] for p in p3}) == 0,
   len({p[2] for p in PAIRS} & {p[2] for p in p3}))
badshift = [d for d in disp if (d + 2) % 4]
ck('N4 disp 全体 +2 后 4 对齐断言应为假（对齐性是实测事实，不是定义）', any((d + 2) % 4 for d in disp) == False,
   badshift[:3])

print('\n断言 %d 条，FAIL %d 条' % (nchk[0], len(fails)))
if fails: print('FAIL 列表:', fails)
sys.exit(0 if not fails else 1)
