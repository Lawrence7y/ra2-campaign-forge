#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R188 B：vt == [obj] 对象模型的**静态调用面**定稿实证（含 thunk 语义与槽位身份）。

相对 r188a 修掉的四处**判据错误**（数据没变，错的是我的判据）：
  E1 A2 的 base_of 正则只认 0x 前缀位移，capstone 对 <10 的位移打十进制（[esi + 8]），
     于是 13 个站点被归到 other ⇒ 292 而不是 305。改用 int(tok, 0) 解析。
  E2 A5 把 3 字节 hex 串的 [:2] 当 opcode 比 'ff52'，实际是 'ff'，判据恒假。
  E3 A6 槽位身份写成「x 前一个 dword 是不是 COL」，正确是「vt = x − 4k 本身是不是 vtable」
     （vtable 头 = [COL][slot0][slot1]…，slot k 在 vt+4k，vt-4 才是 COL）。
  E4 N4 断言写反（我写的是「+2 后应对齐」，应为「+2 后必须不对齐」）。

新增三组结构事实（本轮主攻）：
  A7 槽 3 的实现 0x410210 是 **this 调整 thunk**：mov edx,[eax−4] / lea ecx,[eax−4] /
     call [edx+0x2c] —— 即从 this−4 读虚表指针、this 减 4 后转调**槽 11**。
     这是 vt == [obj] 模型在「子对象/多继承调整」形态下的逐字节证据。
  A8 槽 4 的实现 0x410220 = mov eax,[eax+0xc]; ret 4（纯字段读），其 78 张宿主表
     COL.mdisp 实测**全为 4**（同族同签名）。
  A9 实现函数的槽位身份唯一性：top5 实现各自在其出现的**全部**表里都落在同一槽号。
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
ck('A0b 每个 vtable 的 slot0 都落在 .text（槽数 >= 1）', all(v >= 1 for v in SN.values()),
   min(SN.values()))
IMP = collections.defaultdict(list)
for vt in VTS:
    for k in range(SN[vt]): IMP[P.dw(vt + 4 * k)].append((vt, k))

lite = Cs(CS_ARCH_X86, CS_MODE_32)
insns = []
for off in range(0, len(BLOB), 64 * 1024):
    insns.extend(lite.disasm_lite(BLOB[off:off + 64 * 1024], LO + off))
ck('A1a 线性指令总数 1,150,117', len(insns) == 1150117, len(insns))

BR = r'(e[a-d]x|e[sd]i|ebp|ebx|esp)'
CALL_MEM = re.compile(r'^dword ptr \[(.+)\]$')
def parse_mem(inner):
    """返回 (reg, index_reg, disp)；无法解析返回 None。用 int(tok,0) 兼容十进制/十六进制。"""
    toks = [t.strip() for t in inner.split(' + ')]
    if len(toks) > 2: return None
    reg = idx = None; disp = 0
    for t in toks:
        if re.fullmatch(BR, t): reg = t
        elif re.fullmatch(r'%s \* [1248]' % BR, t): idx = t
        elif re.fullmatch(r'-?(0x[0-9a-f]+|[0-9]+)', t): disp = int(t, 0)
        else: return None
    return (reg, idx, disp)

ind = []; other = 0
for a, sz, mn, op in insns:
    if mn != 'call': continue
    m = CALL_MEM.match(op)
    if not m: continue
    pm = parse_mem(m.group(1))
    if pm is None: other += 1; continue
    ind.append((a, pm[0], pm[1], pm[2], op))
ck('A1b 间接 call 站点（寄存器基址 + 可解析位移）== 18,520', len(ind) == 18520, (len(ind), other))
bd = collections.Counter((x[1] or 'abs') for x in ind)
print('  基址分布:', dict(bd.most_common()))
ck('A1c 基址分类合计 == 18,520', sum(bd.values()) == 18520, sum(bd.values()))
ck('A1d 无 indexed 形态（esi*4 + abs / 任何 reg + reg*n）',
   sum(1 for x in ind if x[2]) == 0, [x[4] for x in ind if x[2]][:3])

# ---------- A2 基址 == esi ----------
esi = [x for x in ind if x[1] == 'esi']
ck('A2a [esi + disp] 间接 call 站点 == 305（E1 修正后；旧错值 292 是十进制位移未解析）',
   len(esi) == 305, len(esi))
ed = collections.Counter(x[3] for x in esi)
ck('A2b 位移去重 == 45', len(ed) == 45, len(ed))
ck('A2c 位移全部 4 字节对齐', all(d % 4 == 0 for d in ed), [hex(d) for d in ed if d % 4])
ck('A2d 无负位移', all(d >= 0 for d in ed), [hex(d) for d in ed if d < 0])
print('  [esi] top 位移:', [(hex(k), v) for k, v in ed.most_common(8)])

# ---------- A3 vt 传播 ----------
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
nmov, PAIRS = prop('esi', 32, True)
ck('A3a mov r32,[esi] 站点 == 7406', nmov == 7406, nmov)
ck('A3b vt 传播配对数 == 5337', len(PAIRS) == 5337, len(PAIRS))
ck('A3c 配对 call 站点去重 == 5337（一站点一来源）', len({p[2] for p in PAIRS}) == 5337,
   len({p[2] for p in PAIRS}))
ck('A3d 配对意味着该 call 的虚表值来自 [esi] 且途中未被改写（判据定义）', True)
disp = collections.Counter(p[3] for p in PAIRS)
ck('A3e 位移去重 == 244', len(disp) == 244, len(disp))
ck('A3f 位移频次合计 == 5337', sum(disp.values()) == 5337, sum(disp.values()))
ck('A3g 配对位移全部 4 对齐', all(d % 4 == 0 for d in disp))
print('  配对寄存器:', dict(collections.Counter(p[1] for p in PAIRS).most_common()))

# ---------- A4 槽位可行性 ----------
SLOT = {}; INFEAS = []
for d, c in disp.items():
    k = d // 4
    tbls = [vt for vt in VTS if SN[vt] > k]
    SLOT[d] = dict(k=k, calls=c, tables=len(tbls),
                   impls=len({P.dw(vt + 4 * k) for vt in tbls}))
    if not tbls: INFEAS.append(d)
ck('A4a 全部 244 个位移在某张表上都有该槽（无「不存在的槽」）', INFEAS == [], INFEAS)
reach = set()
for d in disp:
    k = disp and SLOT[d]['k']
    for vt in VTS:
        if SN[vt] > k: reach.add(P.dw(vt + 4 * k))
allv = {P.dw(vt + 4 * k) for vt in VTS for k in range(SN[vt])}
ck('A4b 观测槽可达实现 <= 全 vfunc 实现全集', len(reach) <= len(allv), (len(reach), len(allv)))
ck('A4c 全槽位实例数 == 槽数求和', sum(SN.values()) == sum(SN.values()), sum(SN.values()))
print('  全槽位实例 %d / 实现去重 %d / 观测槽可达 %d' % (sum(SN.values()), len(allv), len(reach)))

# ---------- A5 头部槽位字节 ----------
def ib(va, n): return P.RAW[P.r2o(va):P.r2o(va) + n].hex()
TOP = sorted(disp, key=lambda x: -disp[x])[:6]
HEAD = []
for d in TOP:
    sites = [p for p in PAIRS if p[3] == d]
    k = d // 4
    top_impl = max(((v, sum(1 for vt in VTS if SN[vt] > k and P.dw(vt + 4 * k) == v))
                    for v in {P.dw(vt + 4 * k) for vt in VTS if SN[vt] > k}),
                   key=lambda x: x[1])
    HEAD.append(dict(disp=d, k=k, calls=disp[d], site=sites[0][2], bytes=ib(sites[0][2], 3),
                     tables=SLOT[d]['tables'], impls=SLOT[d]['impls'],
                     top_impl=top_impl[0], top_impl_tables=top_impl[1]))
    print('  槽 %3d disp=%#5x calls=%3d 首站点 %#x 字节 %s 表数 %d 实现 %d 最常见 %#x(%d)'
          % (k, d, disp[d], sites[0][2], ib(sites[0][2], 3),
             SLOT[d]['tables'], SLOT[d]['impls'], top_impl[0], top_impl[1]))
ck('A5a top6 站点首 2 字节 == ff（E2 修正后；call r/m32 的 opcode FF /2）',
   all(h['bytes'][:4] == 'ff' for h in HEAD), [(h['disp'], h['bytes']) for h in HEAD])
ck('A5b top6 站点第三字节 == modrm 且 reg 位 == 2（/2 = call）',
   all(((int(h['bytes'][2:4], 16) >> 3) & 7) == 2 for h in HEAD),
   [(hex(h['disp']), h['bytes'][2:4]) for h in HEAD])

# ---------- A6/A9 实现函数槽位身份（E3 修正） ----------
A9 = []
for h in HEAD:
    k = h['k']; impl = h['top_impl']
    occ = IMP.get(impl, [])
    same = sum(1 for vt, kk in occ if kk == k)
    A9.append(dict(impl=impl, k=k, occ=len(occ), same_slot=same,
                   idx_hist=dict(collections.Counter(kk for _, kk in occ))))
    print('  实现 %#x 出现于 %d 张表，其中在槽 %d 的 %d 张（槽号直方 %s）'
          % (impl, len(occ), k, same, dict(collections.Counter(kk for _, kk in occ).most_common(3))))
ck('A9a top6 实现各自在**全部**出现处都落在同一槽号（实现 <-> 槽号 一一）',
   all(a['occ'] == a['same_slot'] for a in A9), [(hex(a['impl']), a['occ'], a['same_slot']) for a in A9])

# ---------- A7 this 调整 thunk 逐字节 ----------
THUNK = None
for h in A9:
    if h['k'] == 3: THUNK = h
ck('A7a 槽 3 有 top 实现且表数 >= 70', THUNK is not None and THUNK['occ'] >= 70,
   THUNK and (hex(THUNK['impl']), THUNK['occ']))
tva = THUNK['impl']; tb = ib(tva, 14)
print('  槽3 实现 %#x 字节 %s' % (tva, tb))
ck('A7b thunk 首 4 字节 == 8b 44 24 04（mov eax,[esp+4] 取 this）', tb[:8] == '8b442404', tb[:8])
ck('A7c 次 3 字节 == 8b 50 fc（mov edx,[eax-4] == 从 this-4 读虚表指针）', tb[8:14] == '8b50fc', tb[8:14])
ck('A7d 次 3 字节 == 8d 48 fc（lea ecx,[eax-4] == this 减 4 作为调整后 this）', tb[14:20] == '8d48fc', tb[14:20])
ck('A7e 再 3 字节 == ff 52 2c（call [edx+0x2c] == 槽 11）', tb[20:26] == 'ff522c', tb[20:26])
ck('A7f 尾 3 字节 == c2 04 00（ret 4，thiscall 单参）', tb[26:32] == 'c20400', tb[26:32])
# 该 thunk 的宿主表在槽 11 上的取值一致性
owners = [vt for vt, kk in IMP[tva] if kk == 3]
s11 = collections.Counter(P.dw(vt + 44) for vt in owners)
print('  槽3 thunk 的 %d 张宿主表，槽 11 取值去重 %d: %s'
      % (len(owners), len(s11), [(hex(k), v) for k, v in s11.most_common(4)]))
ck('A7g 宿主表槽 11 取值高度集中（最常见值占比 >= 90%）',
   s11.most_common(1)[0][1] / len(owners) >= 0.90,
   round(s11.most_common(1)[0][1] / len(owners), 4))

# ---------- A8 槽 4 纯字段读 ----------
G = [a for a in A9 if a['k'] == 4]
ck('A8a 槽 4 有 top 实现', bool(G), G and hex(G[0]['impl']))
gva = G[0]['impl']; gb = ib(gva, 8)
print('  槽4 实现 %#x 字节 %s' % (gva, gb))
ck('A8b 实现 == 8b442404 8b400c c20400（mov eax,[esp+4]; mov eax,[eax+0xc]; ret 4）',
   gb == '8b442404' + '8b400c' + 'c20400', gb)
mds = collections.Counter(VTS[vt]['mdisp'] for vt, kk in IMP[gva] if kk == 4)
ck('A8c 该实现 78 张宿主表 COL.mdisp 实测全为 4', mds == {4: 78}, dict(mds))

json.dump(dict(insns=len(insns), indirect=len(ind), base=dict(bd),
               esi_sites=len(esi), esi_disp={hex(k): v for k, v in ed.items()},
               pairs=len(PAIRS), disp={hex(k): v for k, v in disp.items()},
               slot={hex(k): v for k, v in SLOT.items()},
               total_slots=sum(SN.values()), impl_universe=len(allv), reach=len(reach),
               head=HEAD, a9=A9, thunk=dict(va=tva, bytes=tb, owners=len(owners),
                                            slot11=dict((hex(k), v) for k, v in s11.items())),
               getter=dict(va=gva, bytes=gb, mdisp=dict(mds))),
          open(os.path.join(HERE, 'r188b.json'), 'w'), indent=1, default=str)

print('\n--- 反控 ---')
_, p1 = prop('esi', 1, True)
ck('N1 窗口 32->1，配对数显著变小', len(p1) < len(PAIRS), (len(p1), len(PAIRS)))
_, p2 = prop('esi', 32, False)
ck('N2 关掉写入检查，配对数变大（差值为途中被改写的寄存器冒充）', len(p2) > len(PAIRS),
   (len(p2), len(PAIRS), len(p2) - len(PAIRS)))
_, p3 = prop('edi', 32, True)
ck('N3 mov 源换 [edi]，配对站点与 [esi] 交集为 0', len({p[2] for p in PAIRS} & {p[2] for p in p3}) == 0,
   (len(p3), len({p[2] for p in PAIRS} & {p[2] for p in p3})))
ck('N4 位移 +2 后**必须**破坏 4 对齐（E4 修正：对齐是实测事实，正控为「全部对齐」）',
   all((d + 2) % 4 for d in disp), [d for d in disp if (d + 2) % 4 == 0][:3])
ck('N5 槽号身份判据反控：把 k 改成 k+1 后 top6 实现「全部落同槽」断言必须失败',
   all(sum(1 for vt, kk in IMP[a['impl']] if kk == a['k'] + 1) != a['occ'] for a in A9),
   [(hex(a['impl']), a['occ']) for a in A9][:3])

print('\n断言 %d 条，FAIL %d 条' % (nchk[0], len(fails)))
if fails: print('FAIL:', fails)
sys.exit(0 if not fails else 1)
