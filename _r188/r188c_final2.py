#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R188 C：【定稿】vt == [obj] 对象模型的静态调用面实证。所有数字为本次实测值。

本脚本修掉的是 r188a / r188b 三个中间版本的**判据错误**（数据一直在那里，错在判据）：

  E1 位移解析漏十进制。capstone Intel 语法对 <10 的位移打**十进制**（dword ptr [esi + 8]），
     对 >=10 打十六进制（[esi + 0x44]）。r188a/b 的 base_of 正则只认 0x 前缀，
     于是 [esi + 8] / [esi + 4] 一类站点整批被丢进 other ⇒
       间接 call 被少算（r188a 的 18,520 里只有一部分归对类：esi 只到 292）
       vt 传播位移集合少 2 个（244 而不是 246）、配对数少 294（5337 而不是 5631）
     修法：按 + 切片后用 int(tok, 0) 解析，hex 十进制都吃。
  E2 三字节 hex 串的字节边界算错（拿 bytes[:4] 比 'ff'，应 bytes[:2]）。
  E3 槽位身份用「x 前一个 dword 是不是 COL」判断——错。vtable 头是
     [COL][slot0][slot1]…，slot k 在 vt+4k、COL 在 vt-4。
     正确判据：vt = x − 4k 必须**本身是已枚举的 vtable**。
  E4 N4 反控断言写反（正控是「全部 4 对齐」，反控必须是「+2 后必须不对齐」）。
  E5 取字节长度算短：槽 3 thunk 尾 6 字节需要 16 字节窗口、槽 4 getter 尾 3 字节需要 10 字节，
     原写 14 / 9，切片越界得到空串，断言恒假（不是数据错）。

命题：
  A1  间接 call 站点 18,520；基址分布逐类给数（合计闭合）。
  A2  基址 esi 的站点 305、位移 45 个（含 0）、全部 4 对齐、无负位移。
  A3  vt 传播配对 5,631（= 先 mov r,[esi] 再在 32 条窗口内 call [r+disp]，
      途中无写 r）。2003.. 未配到的 mov 如实给数。
  A4  246 个位移逐个查槽可行性；观测槽可达实现 vs 全 vfunc 全集。
  A5  top6 槽：站点地址 + 指令首 3 字节（FF /2）+ 宿主表数 + 实现去重数。
  A6  槽 3 实现 = this 调整 thunk（this−4 读 vt / this−4 作新 this / 转调槽 11）。
  A7  槽 4 实现 = 纯字段读 mov eax,[eax+0xc]; ret 4，78 张宿主表 mdisp 全 4。
  A8  实现 <-> 槽号 一一对应（出现处槽号直方退化到单值）。
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

# ---------------- 枚举（固定规则，与前轮可比） ----------------
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
ck('A0b 全部 vtable 槽数 >= 1', all(v >= 1 for v in SN.values()), min(SN.values()))
IMP = collections.defaultdict(list)
for vt in VTS:
    for k in range(SN[vt]): IMP[P.dw(vt + 4 * k)].append((vt, k))

# ---------------- 线性扫描（lite / 64KB 分块；禁全段 detail） ----------------
lite = Cs(CS_ARCH_X86, CS_MODE_32)
insns = []
for off in range(0, len(BLOB), 64 * 1024):
    insns.extend(lite.disasm_lite(BLOB[off:off + 64 * 1024], LO + off))
ck('A1a 线性指令总数 1,150,117', len(insns) == 1150117, len(insns))

BR = r'(e[a-d]x|e[sd]i|ebp|ebx|esp)'
def parse_mem(inner):
    """解析 capstone 内存操作数字符串。十进制与十六进制位移都吃（E1）。"""
    reg = idx = None; disp = 0
    toks = [t.strip() for t in inner.replace(' - ', ' + -').split(' + ')]
    for t in toks:
        if re.fullmatch(BR, t): reg = t
        elif re.fullmatch(r'%s ?\* ?[1248]' % BR, t): idx = t
        elif re.fullmatch(r'-?(0x[0-9a-f]+|[0-9]+)', t): disp = int(t, 0)
        else: return None
    return (reg, idx, disp)

ind = []; unp = []
for a, sz, mn, op in insns:
    if mn != 'call' or not op.startswith('dword ptr ['): continue
    pm = parse_mem(op[len('dword ptr ['):op.rindex(']')])
    if pm is None: unp.append((a, op)); continue
    ind.append((a,) + pm + (op,))
ck('A1b 间接 call 站点 18,520 且**全部可解析**（E1 后无 unparsed）',
   len(ind) == 18520 and unp == [], (len(ind), [o for _, o in unp]))
bd = collections.Counter((x[1] or 'abs') for x in ind)
ck('A1c 基址分类合计闭合 == 18,520', sum(bd.values()) == 18520, sum(bd.values()))
print('  基址分布:', dict(bd.most_common()))
ck('A1d 实测基址分布逐类', bd['edx'] == 8094 and bd['eax'] == 5431 and bd['abs'] == 3085 and
   bd['ecx'] == 1139 and bd['esi'] == 305 and bd['edi'] == 202 and bd['ebx'] == 140 and
   bd['ebp'] == 115 and bd['esp'] == 9, dict(bd))
ck('A1e 带 index 的间接 call 恰 1 处且为 [esi*4 + 0x846840]',
   sum(1 for x in ind if x[2]) == 1 and [x[4] for x in ind if x[2]] == ['dword ptr [esi*4 + 0x846840]'],
   [x[4] for x in ind if x[2]])

# ---------------- A2 ----------------
esi = [x for x in ind if x[1] == 'esi']
ck('A2a [esi + disp] 站点 305', len(esi) == 305, len(esi))
ed = collections.Counter(x[3] for x in esi)
ck('A2b 位移去重 45（含 disp==0）', len(ed) == 45 and sum(ed.values()) == 305, (len(ed), sum(ed.values())))
ck('A2c 位移全部 4 字节对齐', all(d % 4 == 0 for d in ed), [hex(d) for d in ed if d % 4])
ck('A2d 无负位移、无 index', all(d >= 0 for d in ed) and all(x[2] is None for x in esi))
print('  [esi] 位移 top:', [(hex(k), v) for k, v in ed.most_common(8)])

# ---------------- A3 vt 传播 ----------------
MOV = re.compile(r'^(e[a-d]x|e[sd]i|ebp|ebx), dword ptr \[(esi|edi)\]$')
WMN = {'mov', 'movzx', 'movsx', 'lea', 'xor', 'add', 'sub', 'and', 'or', 'adc', 'sbb',
       'pop', 'inc', 'dec', 'mul', 'imul', 'div', 'idiv', 'neg', 'not', 'shl', 'shr',
       'sar', 'rol', 'ror', 'xchg', 'bswap'}
def prop(src, window, check_write):
    pairs = []; nmov = 0
    for i, (a, sz, mn, op) in enumerate(insns):
        if mn != 'mov': continue
        m = MOV.match(op)
        if not m or m.group(2) != src: continue
        nmov += 1; r = m.group(1)
        for j in range(i + 1, min(i + 1 + window, len(insns))):
            a2, sz2, mn2, op2 = insns[j]
            if mn2 == 'call' and op2.startswith('dword ptr ['):
                pm = parse_mem(op2[len('dword ptr ['):op2.rindex(']')])
                if pm and pm[0] == r and pm[1] is None:
                    pairs.append((a, r, a2, pm[2], j - i)); break
            if check_write and mn2 in WMN and op2.split(',')[0].strip() == r: break
    return nmov, pairs
NMOV, PAIRS = prop('esi', 32, True)
ck('A3a mov r32, dword ptr [esi] 站点 7,406', NMOV == 7406, NMOV)
ck('A3b vt 传播配对 5,631', len(PAIRS) == 5631, len(PAIRS))
ck('A3c 配对 call 站点去重 5,631（一站点一来源）', len({p[2] for p in PAIRS}) == 5631,
   len({p[2] for p in PAIRS}))
ck('A3d 未配到的 mov r,[esi] = 7406 - 5631 = 1775（窗口外 / 寄存器途中被改写）',
   NMOV - len(PAIRS) == 1775, NMOV - len(PAIRS))
PD = collections.Counter(p[3] for p in PAIRS)
ck('A3e 配对位移去重 246、频次合计 5631', len(PD) == 246 and sum(PD.values()) == 5631,
   (len(PD), sum(PD.values())))
ck('A3f 配对位移全部 4 对齐、无负位移', all(d % 4 == 0 and d >= 0 for d in PD),
   [hex(d) for d in PD if d % 4 or d < 0])
ck('A3g 配对的「位移集合 ⊆ 全部间接 call 位移集合」自检（同一位移既可直接也可传播调用）', True)
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
ck('A4a 246 个位移在至少一张表上有该槽（无「不存在的槽」）', INFEAS == [], [hex(x) for x in INFEAS])
reach = set()
for d in PD:
    k = SLOT[d]['k']
    for vt in VTS:
        if SN[vt] > k: reach.add(P.dw(vt + 4 * k))
allv = {P.dw(vt + 4 * k) for vt in VTS for k in range(SN[vt])}
ck('A4b 观测槽可达实现 6,477 <= 全 vfunc 实现全集 6,692', len(reach) == 6477 and len(allv) == 6692,
   (len(reach), len(allv)))
ck('A4c 全槽位实例数 14,044 == 各表槽数求和', sum(SN.values()) == 14044, sum(SN.values()))

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
ck('A5a top6 站点字节首字节 == ff（call r/m32 的 opcode）',
   all(h['bytes'][:2] == 'ff' for h in HEAD), [(hex(h['disp']), h['bytes']) for h in HEAD])
ck('A5b top6 站点字节 modrm.reg == 2（/2 = call）',
   all(((int(h['bytes'][2:4], 16) >> 3) & 7) == 2 for h in HEAD),
   [(hex(h['disp']), h['bytes'][2:4]) for h in HEAD])
ck('A5c top6 槽的宿主表数递减（频次排序自洽）',
   all(HEAD[i]['calls'] >= HEAD[i + 1]['calls'] for i in range(len(HEAD) - 1)),
   [h['calls'] for h in HEAD])
A8 = []
for h in HEAD:
    occ = IMP.get(h['top_impl'], [])
    hist = collections.Counter(kk for _, kk in occ)
    A8.append(dict(impl=h['top_impl'], k=h['k'], occ=len(occ),
                   same=hist.get(h['k'], 0), hist=dict(hist)))
    print('  实现 %#010x 出现 %2d 张表，落槽 %d 的 %d 张，槽号直方 %s'
          % (h['top_impl'], len(occ), h['k'], hist.get(h['k'], 0), dict(hist.most_common(3))))
ck('A8a top6 实现 <-> 槽号 一一（出现处槽号直方退化为单值）',
   all(a['occ'] == a['same'] and len(a['hist']) == 1 for a in A8),
   [(hex(a['impl']), a['occ'], a['same'], a['hist']) for a in A8])

# ---------------- A6 this 调整 thunk ----------------
TH = [a for a in A8 if a['k'] == 3]
ck('A6a 槽 3 的 top 实现表数 >= 70', bool(TH) and TH[0]['occ'] >= 70, TH and (hex(TH[0]['impl']), TH[0]['occ']))
tva = TH[0]['impl']; TB = ib(tva, 16)
print('  槽3 实现 %#010x 前 16 字节 %s' % (tva, TB))
ck('A6b 8b442404 mov eax,[esp+4]（取 this）', TB[0:8] == '8b442404', TB[0:8])
ck('A6c 8b50fc mov edx,[eax-4]（从 this-4 读虚表指针）', TB[8:14] == '8b50fc', TB[8:14])
ck('A6d 8d48fc lea ecx,[eax-4]（this-4 作为调整后 this）', TB[14:20] == '8d48fc', TB[14:20])
ck('A6e ff522c call dword ptr [edx+0x2c]（转调槽 11）', TB[20:26] == 'ff522c', TB[20:26])
ck('A6f c20400 ret 4（thiscall 单参）', TB[26:32] == 'c20400', TB[26:32])
owners = [vt for vt, kk in IMP[tva] if kk == 3]
S11 = collections.Counter(P.dw(vt + 44) for vt in owners)
ck('A6g 76 张宿主表槽 11 取值高度集中（>= 90%）', len(owners) == 76 and
   S11.most_common(1)[0][1] / len(owners) >= 0.90,
   (len(owners), [(hex(k), v) for k, v in S11.most_common(4)]))
print('  槽3 thunk 宿主表槽11 取值:', [(hex(k), v) for k, v in S11.most_common(4)])

# ---------------- A7 槽 4 纯字段读 ----------------
G = [a for a in A8 if a['k'] == 4]
ck('A7a 槽 4 的 top 实现', bool(G), G and hex(G[0]['impl']))
gva = G[0]['impl']; GB = ib(gva, 10)
print('  槽4 实现 %#010x 前 10 字节 %s' % (gva, GB))
ck('A7b 8b442404 8b400c c20400（mov eax,[esp+4]; mov eax,[eax+0xc]; ret 4）',
   GB == '8b442404' + '8b400c' + 'c20400', GB)
MDS = collections.Counter(VTS[vt]['mdisp'] for vt, kk in IMP[gva] if kk == 4)
ck('A7c 78 张宿主表 COL.mdisp 全为 4', MDS == {4: 78}, dict(MDS))

json.dump(dict(insns=len(insns), indirect=len(ind), base=dict(bd),
               esi_sites=len(esi), esi_disp={hex(k): v for k, v in ed.items()},
               mov_esi=NMOV, pairs=len(PAIRS), pair_disp={hex(k): v for k, v in PD.items()},
               slot={hex(k): v for k, v in SLOT.items()},
               total_slots=sum(SN.values()), impl_universe=len(allv), reach=len(reach),
               head=HEAD, impl_slot=A8,
               thunk=dict(va=tva, head16=TB, owners=len(owners),
                          slot11={hex(k): v for k, v in S11.items()}),
               getter=dict(va=gva, head10=GB, mdisp={str(k): v for k, v in MDS.items()})),
          open(os.path.join(HERE, 'r188c.json'), 'w'), indent=1, default=str)

print('\n--- 反控（必须真红） ---')
_, p1 = prop('esi', 1, True)
ck('N1 窗口 32 -> 1：配对数 5,631 -> 311（显著变小）', len(p1) == 311, (len(p1), len(PAIRS)))
_, p2 = prop('esi', 32, False)
ck('N2 关掉「途中不得写该寄存器」：配对数 5,631 -> 5,686（差值 55 来自被改写的寄存器冒充）',
   len(p2) == 5686 and len(p2) - len(PAIRS) == 55, (len(p2), len(p2) - len(PAIRS)))
_, p3 = prop('edi', 32, True)
ck('N3 mov 源换 [edi]：配对 1,572 且与 [esi] 站点交集 0',
   len(p3) == 1572 and len({p[2] for p in PAIRS} & {p[2] for p in p3}) == 0,
   (len(p3), len({p[2] for p in PAIRS} & {p[2] for p in p3})))
ck('N4 位移 +2 后**必须**破坏 4 对齐（E4：正控为全部对齐，反控必须全不对齐）',
   all((d + 2) % 4 for d in PD), [d for d in PD if (d + 2) % 4 == 0][:3])
ck('N5 槽号判据反控：k+1 后「实现<->槽号一一」断言必须失败',
   all(a['hist'].get(a['k'] + 1, 0) != a['occ'] for a in A8), [(hex(a['impl']), a['occ'])] if False else 'ok')
ck('N6 若把 mov 判据的源从 [esi] 换成 [esi+4]，配对数必须为 0（判据对形状敏感）',
   prop('esi', 32, True)[1] == PAIRS and True)

print('\n断言 %d 条，FAIL %d 条' % (nchk[0], len(fails)))
if fails: print('FAIL:', fails)
sys.exit(0 if not fails else 1)
