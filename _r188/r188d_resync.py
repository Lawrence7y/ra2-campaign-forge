#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R188 D：【定稿】用**逐字节重同步**的线性扫描重做 vt == [obj] 静态调用面实证。

## 为什么要重做（本轮最实质的发现）
r188a / r188b / r188c 三个中间版本用的都是「按 64KB 分块、每块内 md.disasm_lite 一直解到解不动」
的扫描。capstone 的 disasm_lite 遇到不可解字节就**返回**（不抛异常、不前进），
于是每块都在第一个坏字节处**提前终止**，块尾那一段字节根本没被解码。
实测：62 块里 53 块提前终止，消费字节率 3,360,178 / 4,063,232 = **82.70%**。

后果：站点数**取决于分块边界**——
  64KB 分块不计重同步：间接 call 19,482（esi 310）
  我 r188a 的 base_of 又漏了十进制位移：18,520（esi 292）
  逐字节重同步（真覆盖 100%）：间接 call 22,731（esi 326）
三个数都能"自洽地"报出来，但没有一个是「.text 上真实的站点总数」。
R186 的审计 #448 已指出过 82.70% 这件事（_r186/r186d，D2a 断言 PASS），
但当时只用它来解释 C7 字节模式口径，**没有回头拦住指令级站点统计**。
⇒ 本轮把这个方法学缺陷单独记为事实条目，此后一切「站点计数」必须报重同步口径。

## 判据（与 r188c 相同的四条已修正错误，另加 resync）
  E1 位移解析必须吃十进制（capstone 对 <10 打十进制，如 [esi + 8]）。
  E2 hex 串字节边界按 2 字符 = 1 字节切。
  E3 槽位身份：vt = x − 4k 本身必须是已枚举 vtable（COL 在 vt−4，不在 x−4）。
  E4 对齐性是正控（全部对齐），反控必须是「+2 后全部不对齐」。
  E5 取字节要够长（thunk 16 字节、getter 10 字节）。
  E6 扫描必须重同步：坏字节处前进 1 字节继续，不得整段放弃。

命题 A1–A8 与反控 N1–N7。
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
def ib(va, n): return P.RAW[P.r2o(va):P.r2o(va) + n].hex()

# ---------------- 枚举 ----------------
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
ck('A0a COL 1214 / vtable 1214', len(COLS) == 1214 and len(VTS) == 1214, (len(COLS), len(VTS)))
def slot_count(vt):
    k = 0
    while True:
        d = P.dw(vt + 4 * k)
        if d is None or not (LO <= d < HI): return k
        k += 1
        if k > 4000: return k
SN = {vt: slot_count(vt) for vt in VTS}
IMP = collections.defaultdict(list)
for vt in VTS:
    for k in range(SN[vt]): IMP[P.dw(vt + 4 * k)].append((vt, k))
ck('A0b 全部 vtable 槽数 >= 1', all(v >= 1 for v in SN.values()), min(SN.values()))

# ---------------- E6 重同步扫描 ----------------
lite = Cs(CS_ARCH_X86, CS_MODE_32)
CH = 64 * 1024
def build(resync):
    """分块扫描；resync=True 时在坏字节处前进 1 字节继续（真覆盖 100%）。
       E6：disasm_lite 遇不可解字节是**返回**而非抛异常，不重同步就会整段放弃。"""
    pos = 0; out = []; holes = 0
    while pos < len(BLOB):
        end = min(pos + CH, len(BLOB)); last = None
        for a, sz, mn, op in lite.disasm_lite(BLOB[pos:end], LO + pos):
            last = pos + (a - (LO + pos)) + sz
            out.append((a, sz, mn, op))
        if last is None: pos += 1; holes += 1
        elif last >= end: pos = end
        elif resync: pos = last + 1; holes += 1
        else: pos = end
    return out, holes
INSNS, HOLES = build(True)
NAIVE, NHOLES = build(False)
ck('A1a 重同步后指令 1,394,134 条、坏字节 97 处', len(INSNS) == 1394134 and HOLES == 97,
   (len(INSNS), HOLES))
ck('A1b 不计重同步只有 1,197,422 条（少 196,712 条）', len(NAIVE) == 1197422,
   (len(NAIVE), len(INSNS) - len(NAIVE)))
ck('A1c 重同步使指令数严格增加', len(INSNS) > len(NAIVE), len(INSNS) - len(NAIVE))

BR = r'(e[a-d]x|e[sd]i|ebp|ebx|esp)'
def parse_mem(inner):
    reg = idx = None; disp = 0
    for t in [x.strip() for x in inner.replace(' - ', ' + -').split(' + ')]:
        if re.fullmatch(BR, t): reg = t
        elif re.fullmatch(r'%s ?\* ?[1248]' % BR, t): idx = t
        elif re.fullmatch(r'-?(0x[0-9a-f]+|[0-9]+)', t): disp = int(t, 0)
        else: return None
    return (reg, idx, disp)
def calls(ins):
    out = []; unp = 0
    for a, sz, mn, op in ins:
        if mn != 'call' or not op.startswith('dword ptr ['): continue
        pm = parse_mem(op[len('dword ptr ['):op.rindex(']')])
        if pm is None: unp += 1; continue
        out.append((a,) + pm + (op,))
    return out, unp

IND, UNP = calls(INSNS)
ck('A1d 间接 call 站点 22,731、全部可解析', len(IND) == 22731 and UNP == 0, (len(IND), UNP))
bd = collections.Counter((x[1] or 'abs') for x in IND)
ck('A1e 基址分类合并 == 22,731', sum(bd.values()) == 22731, sum(bd.values()))
ck('A1f 基址分布逐类实测', bd['edx'] == 9852 and bd['eax'] == 6715 and bd['abs'] == 3832 and
   bd['ecx'] == 1445 and bd['esi'] == 326 and bd['edi'] == 261 and bd['ebx'] == 163 and
   bd['ebp'] == 128 and bd['esp'] == 9, dict(bd))
print('  基址分布:', dict(bd.most_common()))
NAIVE_IND, _ = calls(NAIVE)
ck('A1g 方法学反控：不计重同步 → 19,482（少 3,249 个站点），说明站点数取决于分块策略',
   len(NAIVE_IND) == 19482, (len(NAIVE_IND), len(IND) - len(NAIVE_IND)))

# ---------------- A2 ----------------
esi = [x for x in IND if x[1] == 'esi']
ck('A2a [esi + disp] 站点 326', len(esi) == 326, len(esi))
ed = collections.Counter(x[3] for x in esi)
ck('A2b 位移去重 49、频次合计 326', len(ed) == 49 and sum(ed.values()) == 326,
   (len(ed), sum(ed.values())))
ck('A2c 位移全部 4 对齐、无负位移、无 index',
   all(d % 4 == 0 and d >= 0 for d in ed) and all(x[2] is None for x in esi),
   [hex(d) for d in ed if d % 4 or d < 0])
print('  [esi] 位移 top:', [(hex(k), v) for k, v in ed.most_common(8)])

# ---------------- A3 vt 传播 ----------------
MOV = re.compile(r'^(e[a-d]x|e[sd]i|ebp|ebx), dword ptr \[(esi|edi)\]$')
WMN = {'mov', 'movzx', 'movsx', 'lea', 'xor', 'add', 'sub', 'and', 'or', 'adc', 'sbb',
       'pop', 'inc', 'dec', 'mul', 'imul', 'div', 'idiv', 'neg', 'not', 'shl', 'shr',
       'sar', 'rol', 'ror', 'xchg', 'bswap'}
def prop(ins, src, window, check_write):
    pairs = []; nmov = 0
    for i, (a, sz, mn, op) in enumerate(ins):
        if mn != 'mov': continue
        m = MOV.match(op)
        if not m or m.group(2) != src: continue
        nmov += 1; r = m.group(1)
        for j in range(i + 1, min(i + 1 + window, len(ins))):
            a2, sz2, mn2, op2 = ins[j]
            if mn2 == 'call' and op2.startswith('dword ptr ['):
                pm = parse_mem(op2[len('dword ptr ['):op2.rindex(']')])
                if pm and pm[0] == r and pm[1] is None:
                    pairs.append((a, r, a2, pm[2], j - i)); break
            if check_write and mn2 in WMN and op2.split(',')[0].strip() == r: break
    return nmov, pairs
NMOV, PAIRS = prop(INSNS, 'esi', 32, True)
ck('A3a mov r32,[esi] 站点 9,128', NMOV == 9128, NMOV)
ck('A3b vt 传播配对 6,965', len(PAIRS) == 6965, len(PAIRS))
ck('A3c 配对 call 站点去重 6,965', len({p[2] for p in PAIRS}) == 6965, len({p[2] for p in PAIRS}))
ck('A3d 未配到 = 9128 − 6965 = 2163', NMOV - len(PAIRS) == 2163, NMOV - len(PAIRS))
PD = collections.Counter(p[3] for p in PAIRS)
ck('A3e 配对位移去重 267、频次合计 6,965', len(PD) == 267 and sum(PD.values()) == 6965,
   (len(PD), sum(PD.values())))
ck('A3f 配对位移全部 4 对齐、无负位移', all(d % 4 == 0 and d >= 0 for d in PD),
   [hex(d) for d in PD if d % 4 or d < 0])
print('  配对寄存器:', dict(collections.Counter(p[1] for p in PAIRS).most_common()))

# ---------------- A4 ----------------
SLOT = {}; INFEAS = []
for d, c in PD.items():
    k = d // 4
    tbls = [vt for vt in VTS if SN[vt] > k]
    impls = {P.dw(vt + 4 * k) for vt in tbls}
    SLOT[d] = dict(k=k, calls=c, tables=len(tbls), impls=len(impls),
                   top=(max(((v, sum(1 for x in tbls if P.dw(x + 4 * k) == v)) for v in impls),
                            key=lambda z: z[1]) if impls else (None, 0)))
    if not tbls: INFEAS.append(d)
ck('A4a 245 个位移在至少一张表上有该槽', INFEAS == [], [hex(x) for x in INFEAS])
reach = set()
for d in PD:
    k = SLOT[d]['k']
    for vt in VTS:
        if SN[vt] > k: reach.add(P.dw(vt + 4 * k))
allv = {P.dw(vt + 4 * k) for vt in VTS for k in range(SN[vt])}
ck('A4b 观测槽可达实现 <= 全 vfunc 全集', len(reach) <= len(allv), (len(reach), len(allv)))
ck('A4c 全槽位实例数 == 各表槽数求和', sum(SN.values()) == 14044, sum(SN.values()))
print('  全槽位实例 %d / 实现去重 %d / 观测槽可达 %d' % (sum(SN.values()), len(allv), len(reach)))

# ---------------- A5/A8 ----------------
TOP = sorted(PD, key=lambda x: -PD[x])[:6]
HEAD = []
for d in TOP:
    k = SLOT[d]['k']; site = [p for p in PAIRS if p[3] == d][0]
    HEAD.append(dict(disp=d, k=k, calls=PD[d], site=site[2], bytes=ib(site[2], 3),
                     tables=SLOT[d]['tables'], impls=SLOT[d]['impls'],
                     top_impl=SLOT[d]['top'][0], top_n=SLOT[d]['top'][1]))
    print('  槽 %3d disp=%#5x calls=%3d 首站点 %#010x 字节 %s 表数 %4d 实现 %3d 最常见 %#x(%d 表)'
          % (k, d, PD[d], site[2], ib(site[2], 3), SLOT[d]['tables'], SLOT[d]['impls'],
             SLOT[d]['top'][0], SLOT[d]['top'][1]))
ck('A5a top6 站点首字节 ff', all(h['bytes'][:2] == 'ff' for h in HEAD),
   [(hex(h['disp']), h['bytes']) for h in HEAD])
ck('A5b top6 modrm.reg == 2（/2 = call）',
   all(((int(h['bytes'][2:4], 16) >> 3) & 7) == 2 for h in HEAD),
   [(hex(h['disp']), h['bytes'][2:4]) for h in HEAD])
A8 = []
for h in HEAD:
    occ = IMP.get(h['top_impl'], []); hist = collections.Counter(kk for _, kk in occ)
    A8.append(dict(impl=h['top_impl'], k=h['k'], occ=len(occ), same=hist.get(h['k'], 0),
                   hist=dict(hist)))
    print('  实现 %#010x 出现 %2d 张表、落槽 %d 的 %d 张，直方 %s'
          % (h['top_impl'], len(occ), h['k'], hist.get(h['k'], 0), dict(hist.most_common(3))))
ck('A8a top6 实现 <-> 槽号 一一（直方退化单值）',
   all(a['occ'] == a['same'] and len(a['hist']) == 1 for a in A8),
   [(hex(a['impl']), a['occ'], a['hist']) for a in A8])

# ---------------- A6 thunk ----------------
TH = [a for a in A8 if a['k'] == 3]
ck('A6a 槽 3 top 实现表数 >= 70', bool(TH) and TH[0]['occ'] >= 70,
   TH and (hex(TH[0]['impl']), TH[0]['occ']))
tva = TH[0]['impl']; TB = ib(tva, 16)
print('  槽3 实现 %#010x 前 16 字节 %s' % (tva, TB))
ck('A6b 8b442404 mov eax,[esp+4]', TB[0:8] == '8b442404', TB[0:8])
ck('A6c 8b50fc mov edx,[eax-4]（从 this-4 读虚表指针）', TB[8:14] == '8b50fc', TB[8:14])
ck('A6d 8d48fc lea ecx,[eax-4]（this-4 作调整后 this）', TB[14:20] == '8d48fc', TB[14:20])
ck('A6e ff522c call [edx+0x2c]（转调槽 11）', TB[20:26] == 'ff522c', TB[20:26])
ck('A6f c20400 ret 4', TB[26:32] == 'c20400', TB[26:32])
owners = [vt for vt, kk in IMP[tva] if kk == 3]
S11 = collections.Counter(P.dw(vt + 44) for vt in owners)
ck('A6g 76 张宿主表槽 11 取值 >= 90% 集中', len(owners) == 76 and
   S11.most_common(1)[0][1] / len(owners) >= 0.90,
   (len(owners), [(hex(k), v) for k, v in S11.most_common(4)]))
print('  槽3 宿主表槽11:', [(hex(k), v) for k, v in S11.most_common(4)])

# ---------------- A7 getter ----------------
G = [a for a in A8 if a['k'] == 4]
ck('A7a 槽 4 top 实现', bool(G), G and hex(G[0]['impl']))
gva = G[0]['impl']; GB = ib(gva, 10)
print('  槽4 实现 %#010x 前 10 字节 %s' % (gva, GB))
ck('A7b 8b442404 8b400c c20400', GB == '8b442404' + '8b400c' + 'c20400', GB)
MDS = collections.Counter(VTS[vt]['mdisp'] for vt, kk in IMP[gva] if kk == 4)
ck('A7c 78 张宿主表 COL.mdisp 全为 4', MDS == {4: 78}, dict(MDS))

json.dump(dict(insns=len(INSNS), holes=HOLES, naive_insns=len(NAIVE),
               indirect=len(IND), naive_indirect=len(NAIVE_IND), base=dict(bd),
               esi_sites=len(esi), esi_disp={hex(k): v for k, v in ed.items()},
               mov_esi=NMOV, pairs=len(PAIRS), pair_disp={hex(k): v for k, v in PD.items()},
               slot={hex(k): dict(v, top=list(v['top'])) for k, v in SLOT.items()},
               total_slots=sum(SN.values()), impl_universe=len(allv), reach=len(reach),
               head=HEAD, impl_slot=A8,
               thunk=dict(va=tva, head16=TB, owners=len(owners),
                          slot11={hex(k): v for k, v in S11.items()}),
               getter=dict(va=gva, head10=GB, mdisp={str(k): v for k, v in MDS.items()})),
          open(os.path.join(HERE, 'r188d.json'), 'w'), indent=1, default=str)

print('\n--- 反控 ---')
_, p1 = prop(INSNS, 'esi', 1, True)
ck('N1 窗口 32->1：6,965 -> 384（显著变小）', len(p1) == 384, (len(p1), len(PAIRS)))
_, p2 = prop(INSNS, 'esi', 32, False)
ck('N2 关掉写入检查：6,965 -> 7,047（+82，被改写寄存器冒充）', len(p2) == 7047 and len(p2) - len(PAIRS) == 82,
   (len(p2), len(p2) - len(PAIRS)))
_, p3 = prop(INSNS, 'edi', 32, True)
ck('N3 mov 源换 [edi]：配对与 [esi] 站点交集 0',
   len({p[2] for p in PAIRS} & {p[2] for p in p3}) == 0,
   (len(p3), len({p[2] for p in PAIRS} & {p[2] for p in p3})))
ck('N4 位移 +2 后必须全部破坏 4 对齐', all((d + 2) % 4 for d in PD),
   [d for d in PD if (d + 2) % 4 == 0][:3])
ck('N5 槽号 k+1 后「实现<->槽号一一」必须失败',
   all(a['hist'].get(a['k'] + 1, 0) != a['occ'] for a in A8))
_, pn = prop(NAIVE, 'esi', 32, True)
ck('N6 用不计重同步的指令表跑同一配对：6,965 -> 5,840（少 1,125，证明覆盖缺陷污染配对结论）',
   len(pn) == 5840, (len(pn), len(PAIRS), len(PAIRS) - len(pn)))
ck('N7 坏字节数 97 与坏字节前进 1 字节的重同步次数一致（无整块放弃）', HOLES == 97, HOLES)

print('\n断言 %d 条，FAIL %d 条' % (nchk[0], len(fails)))
if fails: print('FAIL:', fails)
sys.exit(0 if not fails else 1)
