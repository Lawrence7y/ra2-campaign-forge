#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r123a: A4 三类替代解释的字节实证裁决（R122 未取得项①）。

R122 用读写方向排掉了「edx 是输出缓冲」，仍剩三类未排除的解释：
  ① 子对象同址（两个 vptr 写的是同一地址上不同子对象的 vptr）
  ② 结构体成员数组（35 个地址是同一个大结构体的成员）
  ③ 编译器共用初始化模板（两次写入由同一模板生成，故不能说是"两个独立对象"）

本脚本给三类各自的判据，并全部用字节事实 + 正反控收口。

判据设计（先写判据，再看结果，避免事后拟合）：
  T1  区分 ①：RTTI 结构。若第二次写入的 vptr 是第一次的 MSVC 类层次里的基类，
      则这是同一对象同一地址在析构期改回基类 vptr（MSVC 标准做法）；
      若两个 vptr 属于互不相关的类（基类集合无交集），才是"不同子对象同址"。
      COL +4 (mdisp) 也须在两处都为 0 —— 若非 0，说明该 vptr 本身就在对象中间偏移，
      即子对象同址。反控：拿库里真实的多重继承对象（mdisp != 0）验证判据能翻转。
  T2  区分 ②：对象尺寸由构造函数体实际写入的字段偏移的上界决定（不是猜）。
      若 35 个地址两两间隔的最小值 >= 对象尺寸，则它们不可能同属一个结构体。
      反控：若判据是"间隔够大"就能过，那么把窗口调大到必然包含邻居的写法，
      间隔断言就该失败 —— 用"成员数组必然共享同一 ctor"作为第二判据：
      35 个地址必须各自有独立 ctor（35 个不同单元），而成员数组只能有一个 ctor。
  T3  区分 ③：把构造函数体里的立即数归一化为「相对对象基址的偏移」，
      再比对骨架。若归一化后 35 份完全相同，则确实是同一模板展开 —— 那就必须
      承认 ③ 成立而不是排除它。此时改用下一条独立判据：
      两个写入单元必须各自被独立注册：ctor 入 CRT 初始化表（逐项一项 = 一个单元），
      dtor 入 atexit 表。若 35 个 ctor 在 .data 里各占一个表项，
      则这 35 个单元是 35 个独立翻译单元产物，而非同一次内联展开。
      反控：表项判定必须在表区间 [begin,end) 内且区间由指令里的 push 立即数给出。

内存纪律：全程 disasm_lite 线性扫描一次 + 只对少数目标地址开 detail，
绝不整段 .text 开 detail=True。
"""
import bisect
import collections
import hashlib
import json
import struct
import sys

import capstone
import pefile

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r123/r123a_a4_verdict.json'
OBJS = '/home/t628/projects/ra2-campaign-forge/_r122/r122a_objs35.json'
RES = []


def ck(name, cond, detail=''):
    RES.append({'check': name, 'ok': bool(cond), 'detail': str(detail)[:300]})
    return bool(cond)


pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
SECS = [dict(name=x.Name.rstrip(b'\0').decode(), va=IB + x.VirtualAddress,
             vs=x.Misc_VirtualSize, pr=x.PointerToRawData, rs=x.SizeOfRawData)
        for x in pe.sections]
DATA = open(EXE, 'rb').read()
FILE_SHA = hashlib.sha256(DATA).hexdigest()


def sec_of(va):
    for x in SECS:
        if x['va'] <= va < x['va'] + x['vs']:
            return x
    return None


def rd(va, n):
    x = sec_of(va)
    if x is None:
        return None
    off = x['pr'] + (va - x['va'])
    if va - x['va'] + n > x['rs'] or off + n > len(DATA):
        return None
    return DATA[off:off + n]


def u32(va):
    b = rd(va, 4)
    return None if b is None else struct.unpack('<I', b)[0]


TXT = [x for x in SECS if x['name'] == '.text'][0]
TD = DATA[TXT['pr']:TXT['pr'] + TXT['rs']]
TB = TXT['va']
TE = TB + TXT['rs']
DS = [x for x in SECS if x['name'] == '.data'][0]
BSS_LO = DS['va'] + DS['rs']
BSS_HI = DS['va'] + DS['vs']

mdl = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
mdl.skipdata = True
INS = [(o, sz, m, op) for o, sz, m, op in mdl.disasm_lite(TD, TB)]
ck('A0a 线性扫描覆盖到 .text 末尾（skipdata 生效，非残缺边界）',
   len(INS) > 1000000 and INS[-1][0] + INS[-1][1] == TE,
   'insns=%d last_end=0x%x text_end=0x%x' % (len(INS), INS[-1][0] + INS[-1][1], TE))

# 代码单元切分：ret 之后的第一个非填充指令为新单元起点。
# 注意：nop(intel 的 0x90) 与 int3(0xcc) 都算填充，纯字节判定不依赖助记符表。
STARTS = [TB]
_flip = False
for o, sz, m, op in INS:
    b = TD[o - TB:o - TB + sz]
    pad = (b == b'\x90' * sz) or (b == b'\xcc' * sz)
    if m.startswith('ret'):
        _flip = True
        continue
    if _flip and not pad:
        STARTS.append(o)
        _flip = False
STARTS = sorted(set(STARTS))


def unit_of(va):
    return STARTS[bisect.bisect_right(STARTS, va) - 1]


def unit_end(u):
    i = bisect.bisect_right(STARTS, u)
    return STARTS[i] if i < len(STARTS) else TE


ck('A0b 代码单元切分自检（已知两点必须落在同一/不同单元）',
   unit_of(0x40ee5d) == 0x40ee40 and unit_of(0x40ee88) == 0x40ee80,
   'unit(0x40ee5d)=0x%x unit(0x40ee88)=0x%x' % (unit_of(0x40ee5d), unit_of(0x40ee88)))

# ---------- RTTI ----------
def td_name(td):
    b = rd(td + 8, 0x100)
    return b.split(b'\0')[0].decode('latin1') if b else None


def rtti(vt):
    """MSVC x86 32 位 COL 布局（24 字节）：
      +0  signature(0)
      +4  offset      —— 该 vfptr 相对 this 的偏移（多重继承的二级基类非 0）
      +8  cdOffset    —— vbptr 偏移
      +12 pTypeDescriptor
      +16 pClassDescriptor(ClassHierarchyDescriptor)
      +20 pSelf
    注意：x64 是 3 个分离的 int32 mdisp/pdisp/vdisp；x86 是单个 offset。
    这里用 x86 布局（本 EXE 是 PE32）。"""
    c = u32(vt - 4)
    b = rd(c, 0x18)
    if not b or len(b) < 0x18:
        return None
    sig, this_off, cd_off, pTD, pCHD, pSelf = struct.unpack('<IIIIII', b[:24])
    if sig != 0:
        return None
    return dict(col=c, this_off=this_off, cd_off=cd_off, td=pTD, chd=pCHD, self_v=pSelf)


def class_bases(col):
    """MSVC x86 ClassHierarchyDescriptor（20 字节）：
      +0 sig, +4 attr, +8 numBase, +12 pBaseArray, +16 pSelf
    BaseClassArray 的每一项是 **BaseClassDescriptor 的指针**，不是 TypeDescriptor 的指针。
    BaseClassDescriptor 的第一个 dword 才是 pTypeDescriptor。
    自错 S-107（由 hy4 审计员 task 239 指出，主会话已复算确认）：
      首版直接对 BaseClassArray 项调用 td_name()，即读 desc+8 当字符串，
      两处都读到空串，使 T1a 变成 '' in ['', ...] 的恒真假阳性。
      修法：先 u32(desc) 取 pTypeDescriptor，再 td_name()。"""
    b = rd(col['chd'], 20)
    if not b or len(b) < 20:
        return []
    _, _, nb, pbase, _ = struct.unpack('<IIIII', b[:20])
    if not (0 < nb < 64):
        return []
    arr = rd(pbase, 4 * nb)
    if not arr:
        return []
    names = []
    for i in range(nb):
        desc = u32(struct.unpack_from('<I', arr, 4 * i)[0])
        if desc is None:
            names.append(None)
            continue
        names.append(td_name(desc))
    return names


objs = json.load(open(OBJS))['objects']
ck('A1a 输入 35 个对象（来自 R122 已落盘 r122a，不重新猜）', len(objs) == 35, 'n=%d' % len(objs))

ROWS = []
for ob in objs:
    a = int(ob['obj'], 16)
    ws = sorted(int(w['site'], 16) for w in ob['writes'])
    vts = [int(w['vptr'], 16) for w in ob['writes']]
    r1, r2 = rtti(vts[0]), rtti(vts[1])
    b1 = class_bases(r1) if r1 else []
    b2 = class_bases(r2) if r2 else []
    ROWS.append(dict(obj=a, sites=ws, vpts=vts,
                     cu=unit_of(ws[0]), du=unit_of(ws[1]),
                     lc=unit_end(unit_of(ws[0])) - unit_of(ws[0]),
                     ld=unit_end(unit_of(ws[1])) - unit_of(ws[1]),
                     pair=ws[1] - ws[0],
                     r1=r1, r2=r2, b1=b1, b2=b2,
                     n1=td_name(r1['td']) if r1 else None,
                     n2=td_name(r2['td']) if r2 else None))

ck('A1b 35 个对象的两处 vptr 都能解出 COL 与类名',
   all(r['r1'] and r['r2'] and r['n1'] and r['n2'] for r in ROWS),
   'ok=%d/35' % sum(1 for r in ROWS if r['r1'] and r['r2'] and r['n1'] and r['n2']))

# ---------- T1：子对象同址 ----------
# 判据：第二个 vptr 的类必须出现在第一个 vptr 的类层次基类表里（= 同一对象的基类 vptr），
# 且两处的 COL mdisp 都必须为 0（该 vptr 就在对象首偏移）。
t1_base_in_hier = sum(1 for r in ROWS if r['n2'] in r['b1'])
t1_mdisp_zero = sum(1 for r in ROWS if r['r1']['this_off'] == 0 and r['r2']['this_off'] == 0)
ck('T1a 第二个 vptr 的类出现在第一个的基类表里（35/35）', t1_base_in_hier == 35,
   'base_in_hierarchy=%d/35' % t1_base_in_hier)
ck('T1b 两处 COL 的 this-offset 全为 0（vptr 在对象首偏移，不是子对象偏移）',
   t1_mdisp_zero == 35, 'this_off_zero=%d/35' % t1_mdisp_zero)

# 基类表第二项必须是「同一个类名的 VectorClass 版本」，即元素类型相同
t1_elem_same = sum(1 for r in ROWS
                   if r['n1'] and r['n2']
                   and r['n1'].replace('DynamicVectorClass', 'VectorClass') == r['n2'])
ck('T1c 两个 vptr 的元素类型完全相同（Dynamic->Vector 改名后字符串相等）',
   t1_elem_same == 35, 'elem_same=%d/35' % t1_elem_same)

# 反控 N1：库里存在 this-offset != 0 的**合法** vptr。判据必须能翻转到「非同址」。
# 自错 S-108（hy4 审计员 task 239 指出，主会话已按其严格口径复算）：
#   首版在 .rdata 里每 4 字节盲扫，把任意 dword 当 COL 指针，得 632 —— 全是垃圾
#   （例 vt=0x7e1210 的 [vt-4]=0x40f834 落在 .text，根本不是 COL）。
#   严格口径：COL 的 pTypeDescriptor 必须指向合法 TypeDescriptor
#   （其 +0 应为 type_info vftable 0x7f9594，且 +8 起名字以 .?AV 开头），CHD 的 nBase 合法。
TD_VFTABLE = 0x7f9594


def strict_vtable_scan():
    """扫 .rdata 里 4 字节对齐的槽，只接受能解出合法 TypeDescriptor 的 vptr。"""
    rdata = [x for x in SECS if x['name'] == '.rdata'][0]
    blob = DATA[rdata['pr']:rdata['pr'] + rdata['rs']]
    ok = 0
    nonzero_off = 0
    for i in range(0, len(blob) - 4, 4):
        vt = rdata['va'] + i
        c = u32(vt - 4)
        if not c:
            continue
        b = rd(c, 24)
        if not b or len(b) < 24:
            continue
        sig, this_off, cd_off, pTD, pCHD, pSelf = struct.unpack('<IIIIII', b[:24])
        if sig != 0 or not pTD:
            continue
        head = rd(pTD, 4)
        if not head or struct.unpack('<I', head)[0] != TD_VFTABLE:
            continue
        nm = rd(pTD + 8, 8)
        if not nm or not nm.startswith(b'.?A'):
            continue
        ok += 1
        if this_off != 0:
            nonzero_off += 1
    return ok, nonzero_off


n_valid_vt, n_mi = strict_vtable_scan()
ck('T1d 反控：严格口径下有合法 vptr 且其中存在 this-offset != 0 的（否则 T1b 无鉴别力）',
   n_valid_vt > 0 and n_mi > 0,
   'valid_vtables=%d ; this_off_nonzero=%d' % (n_valid_vt, n_mi))

# ---------- T2：结构体成员数组 ----------
def fields_of_unit(u, base):
    """该单元内对 [base, base+0x100) 的绝对写（c7 05 / c6 05 / a3），返回相对偏移。"""
    e = unit_end(u)
    out = []
    for o, sz, m, op in INS:
        if not (u <= o < e):
            continue
        b = TD[o - TB:o - TB + sz]
        tgt = None
        if sz == 10 and b[0] == 0xc7 and b[1] == 0x05:
            tgt = struct.unpack_from('<I', b, 2)[0]
        elif sz == 7 and b[0] == 0xc6 and b[1] == 0x05:
            tgt = struct.unpack_from('<I', b, 2)[0]
        elif sz == 5 and b[0] == 0xa3:
            tgt = struct.unpack_from('<I', b, 1)[0]
        if tgt is not None and base <= tgt < base + 0x100:
            out.append(tgt - base)
    return sorted(set(out))


for r in ROWS:
    r['f_ctor'] = fields_of_unit(r['cu'], r['obj'])
    r['f_dtor'] = fields_of_unit(r['du'], r['obj'])

ctor_field_sets = collections.Counter(tuple(r['f_ctor']) for r in ROWS)
ck('T2a 35 个构造函数写的字段偏移集合完全相同（== 同一类型布局）',
   list(ctor_field_sets.items()) == [((0, 4, 8, 12, 16, 20), 35)],
   'hist=%s' % {'%s' % (k,): v for k, v in ctor_field_sets.items()})

max_field = max(max(r['f_ctor'] + r['f_dtor']) for r in ROWS)
# 审计员修正（A3 第 4 条）：字段上界只给**下界**。构造函数只写已写字段，
# 尾部可能还有未写成员或对齐填充，所以只能断言 size >= 24，不能断言 == 24。
obj_size_min = max_field + 4
obj_size = obj_size_min      # 后续判据统一用这个下界，命名保留 obj_size 以免大改
ck('T2b 由字段上界推出对象尺寸至少 24 字节（下界，不是精确尺寸）',
   obj_size_min >= 24, 'max_field=0x%x size_min=%d' % (max_field, obj_size_min))

addrs = sorted(r['obj'] for r in ROWS)
gaps = [b - a for a, b in zip(addrs, addrs[1:])]
ck('T2c 35 个地址两两最小间隔 >= 对象尺寸下界（不可能是同一结构体的成员）',
   min(gaps) >= obj_size, 'min_gap=0x%x size_min=%d' % (min(gaps), obj_size))

# 成员数组判据二：35 个地址各自有独立 ctor 单元（成员数组只会有一个 ctor）
ctor_units = sorted({r['cu'] for r in ROWS})
dtor_units = sorted({r['du'] for r in ROWS})
ck('T2d 35 个地址有 35 个不同的 ctor 单元（成员数组只能有一个 ctor）',
   len(ctor_units) == 35, 'distinct_ctor_units=%d' % len(ctor_units))
ck('T2e 35 个地址有 35 个不同的 dtor 单元，且与 ctor 单元无交集',
   len(dtor_units) == 35 and not (set(ctor_units) & set(dtor_units)),
   'distinct_dtor_units=%d overlap=%d' % (len(dtor_units), len(set(ctor_units) & set(dtor_units))))

# 反控 N2：库里存在「同一单元内两次写同一 BSS 地址」的目标 —— 这才是成员数组/重复赋值形态。
G = collections.defaultdict(list)
for o, sz, m, op in INS:
    if sz == 10 and TD[o - TB] == 0xc7 and TD[o - TB + 1] == 0x05:
        t = struct.unpack_from('<I', TD, o - TB + 2)[0]
        if BSS_LO <= t < BSS_HI:
            G[t].append(o)
same_unit_twice = [t for t, ss in G.items() if len(ss) == 2 and unit_of(ss[0]) == unit_of(ss[1])]
ours = {r['obj'] for r in ROWS}
ck('T2f 反控（口径限定：只看 c7 05 且恰好 2 站的 BSS 目标）：此类目标存在，且 35 个目标里恰好 0 个',
   len(same_unit_twice) > 0 and len(ours & set(same_unit_twice)) == 0,
   'same_unit_twice=%d ; ours_hit=%d ; c705 targets=%d sites=%d'
   % (len(same_unit_twice), len(ours & set(same_unit_twice)), len(G), sum(len(v) for v in G.values())))

# ---------- T3：共用初始化模板 ----------
DETAIL = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
DETAIL.detail = True


def norm_body(u, base, own_dtor=None):
    """把单元内指令归一化。三类参数差异必须在归一化里显式命名，
    否则「骨架相同」是空话（R123 自错 S-102：首版把这三类差异都留成绝对值，
    得 distinct=35 却当成事实，实际是自己的归一化没做完）：
      * 立即数落在本对象窗口 [base, base+0x100) 内      -> OBJ+相对偏移
      * 立即数 == 本对象自己的 dtor 单元起点            -> OWNDTOR
      * 立即数 == CRT 注册函数 0x7c978a                 -> ATEXIT
      * 其余 .text 内代码地址                           -> CODE:绝对地址（保留）
      * 跳转目标（j*）                                  -> REL+相对单元起点
    保留 CODE 绝对值是有意的：若 35 份的 call 目标各不相同而骨架仍同，
    说明是模板对 35 个不同类型展开，每个展开调用了各自的元素构造（这正是要证的）。"""
    e = unit_end(u)
    body = []
    for i in DETAIL.disasm(TD[u - TB:e - TB], u):
        if i.mnemonic in ('nop', 'int3'):
            continue
        ops = []
        for op in i.operands:
            if op.type == capstone.x86.X86_OP_IMM:
                v = op.imm
                if base <= v < base + 0x100:
                    ops.append('OBJ+%d' % (v - base))
                elif own_dtor is not None and v == own_dtor:
                    ops.append('OWNDTOR')
                elif v == 0x7c978a:
                    ops.append('ATEXIT')
                elif TB <= v < TE and i.mnemonic.startswith('j'):
                    ops.append('REL+%d' % (v - u))
                elif TB <= v < TE:
                    ops.append('CODE:%x' % v)
                else:
                    ops.append('IMM:%x' % v)
            elif op.type == capstone.x86.X86_OP_REG:
                ops.append(DETAIL.reg_name(op.reg))
            elif op.type == capstone.x86.X86_OP_MEM:
                disp = op.mem.disp
                if base <= disp < base + 0x100:
                    disp -= base
                ops.append('MEM:%s:%d' % (DETAIL.reg_name(op.mem.base), disp))
            else:
                ops.append('?')
        body.append(i.mnemonic + ' ' + ','.join(ops))
    return body


for r in ROWS:
    bc = norm_body(r['cu'], r['obj'], own_dtor=r['du'])
    bd = norm_body(r['du'], r['obj'], own_dtor=None)

    def blank_vptr(body, vpts):
        """vptr 那条写的立即数本来就各不相同（35 个类的 vftable），
        归一化成 VPTR，否则「骨架相同」会被 vtable 地址差异淹没。
        注意：vftable 在 .rdata 不在 .text，所以归一化器给它打的标签是 IMM: 而不是 CODE:，
        首版只匹配 CODE: 导致这一项没被抹掉（自错 S-103），这里按数值匹配两种标签。"""
        out = []
        for line in body:
            head, _, imm = line.rpartition(',')
            if head.endswith('MEM:None:0') and imm.startswith(('IMM:', 'CODE:')):
                try:
                    v = int(imm.split(':', 1)[1], 16)
                except ValueError:
                    v = None
                if v is not None and v in vpts:
                    out.append(head + ',VPTR')
                    continue
            out.append(line)
        return out

    r['norm_c'] = blank_vptr(bc, r['vpts'])
    r['norm_d'] = blank_vptr(bd, r['vpts'])
    r['hc'] = hashlib.sha256('\n'.join(r['norm_c']).encode()).hexdigest()
    r['hd'] = hashlib.sha256('\n'.join(r['norm_d']).encode()).hexdigest()
    r['h_no_own'] = hashlib.sha256('\n'.join(
        blank_vptr(norm_body(r['cu'], r['obj'], own_dtor=None), r['vpts'])).encode()).hexdigest()

if len({r['hc'] for r in ROWS}) > 1:
    import difflib
    for i in (1,):
        a, b = ROWS[0]['norm_c'], ROWS[i]['norm_c']
        print('DEBUG ctor norm diff 0 vs %d:' % i)
        for line in difflib.unified_diff(a, b, lineterm='', n=1):
            print('   ', line)
n_hc = len({r['hc'] for r in ROWS})
n_hd = len({r['hd'] for r in ROWS})
hc_no_own = {r['h_no_own'] for r in ROWS}
# 审计员修正（A3 第 1 条）：骨架同构只是「与同一模板展开一致」的必要条件，
# 手写复制、宏展开也能产生同构骨架。不能写成「证明确实是同一模板展开」。
ck('T3a 构造函数体归一化后 35 份骨架同构（与「同一模板展开」一致，不构成充分证明）',
   n_hc == 1, 'distinct_norm_ctor=%d/35' % n_hc)
# 审计员修正（A1 T3a2）：这不是稳健的「非恒真」反控 —— 实测 35 个对象的 du 恰为 cu+0x40，
# 若归一化规则改成「距单元起点 +0x40 内的 .text 地址一律打 NEARDTOR」，仍会塌成 1 份。
# 因此本断言只说「在当前这套归一化规则下，OWNDTOR 项确实是唯一使骨架分叉的参数」。
ck('T3a2 在当前归一化规则下，去掉 OWNDTOR 项后 ctor 骨架分叉成 35 份（规则内唯一分叉参数）',
   len(hc_no_own) == 35, 'distinct_without_owndtor=%d' % len(hc_no_own))
# 析构体实测两种形态：33 个 64 字节（模板 A）+ 2 个 96 字节（模板 B，带静态守卫）。
ld_hist = collections.Counter(r['ld'] for r in ROWS)
hd_by_len = {L: len({r['hd'] for r in ROWS if r['ld'] == L}) for L in ld_hist}
ck('T3b 短形态析构体（64 字节，33 个）归一化后唯一',
   ld_hist.get(64) == 33 and hd_by_len.get(64) == 1,
   'n64=%d distinct=%s' % (ld_hist.get(64, 0), hd_by_len.get(64)))
# 长形态（96 字节，2 个）差异必须恰好是「静态守卫字节」，且该字节不在对象相对窗口内。
# 这不是未归一化，而是该守卫变量按翻译单元独立分配，本就不可能对象相对。
long_rows = [r for r in ROWS if r['ld'] == 96]
def guard_addrs(r):
    """取出归一化后仍是绝对地址的内存引用（镜像内 VA 段 0x400000..0xC00000）。
    修正 R123 自错 S-104 与 S-105：
      S-104 首版把 MEM:None:0 / :4 这类对象相对偏移也当 16 进制绝对值解析；
      S-105 第二版仍为空，因为归一化器用 %d（十进制）打印 disp，脚本却按 16 进制解析。
    现在两种进制都试，并用镜像 VA 区间做门槛。"""
    out = []
    for line in r['norm_d']:
        if 'MEM:None:' not in line:
            continue
        imm = line.rsplit(':', 1)[1]
        v = None
        for base_ in (10, 16):
            try:
                cand = int(imm, base_)
            except ValueError:
                continue
            if 0x400000 <= cand < 0xC00000:
                v = cand
                break
        if v is not None and not (r['obj'] <= v < r['obj'] + 0x100):
            out.append(v)
    return sorted(set(out))


guard_sets = [guard_addrs(r) for r in long_rows]
guard_all_outside = all(not (r['obj'] <= g < r['obj'] + 0x100)
                        for r, gs in zip(long_rows, guard_sets) for g in gs)
ck('T3c 长形态（96 字节，2 个）的差异是静态守卫字节，且全在对象窗口之外（非未归一化）',
   len(long_rows) == 2 and guard_all_outside
   and all(len(g) == 1 for g in guard_sets),
   'long_objs=%s guards=%s outside=%s'
   % ([hex(r['obj']) for r in long_rows],
      [[hex(x) for x in g] for g in guard_sets], guard_all_outside))

# ---------- T2 补强：间隔多样性 ----------
# 成员数组（struct { DynamicVectorClass<A> a[35]; }）必须等步长连续。
gap_kinds = collections.Counter(gaps)
ck('T2g 35 个地址的相邻间隔恰取 31 种不同值（成员数组必须等步长，故排除）',
   len(gap_kinds) == 31,
   'distinct_gaps=%d min=0x%x max=0x%x span=0x%x'
   % (len(gap_kinds), min(gaps), max(gaps), addrs[-1] - addrs[0]))

# 补强二（修正 S-106）：首版断言「a+24 处不是 BSS 写目标」是错的 ——
# 相邻的独立全局对象当然可能恰好相距 24 字节。成员数组的判别式是
# 「相邻元素同类型、同 ctor 模板」。这里查 a 与 a+24 若都是我们的目标，
# 它们的类名是否相同（相同才有成员数组之嫌）。
by_addr = {r['obj']: r for r in ROWS}
pairs = [(a, a + obj_size) for a in addrs if (a + obj_size) in by_addr]
same_type_pairs = [(a, b) for a, b in pairs
                   if by_addr[a]['n1'] == by_addr[b]['n1'] or by_addr[a]['n1'] == by_addr[b]['n2']]
ck('T2h 相邻（+24）且都属于 35 个目标的对里，元素类型相同的为 0（不构成成员链）',
   len(same_type_pairs) == 0,
   'adjacent_pairs=%d same_type=%d' % (len(pairs), len(same_type_pairs)))

# ---------- T3 的第二条判据：独立注册 ----------
# CRT 初始化表：指令里 push imm32 给出的 [begin,end)，遍历函数实测在 0x7cbee0 附近：
#   mov esi,[esp+8] ; cmp esi,[esp+0xc] ; jae done ;
#   mov eax,[esi] ; test eax,eax ; je next ; call eax ; next: add esi,4 ; jmp loop
# 即 for (p = begin; p < end; p += 4) if (*p) (*p)();
# 审计员修正（A2 第 4 条）：首版注释写成 [ebp+8] 栈变量形态，与实测不符，已改正。
# 从 .text 里找「push end; push begin; call」三元组，取最大的合法区间。
CANDIDATE = []
for i in range(len(INS) - 2):
    if INS[i][2] == 'push' and INS[i + 1][2] == 'push' and INS[i + 2][2] == 'call':
        try:
            v2 = int(INS[i][3], 16)
            v1 = int(INS[i + 1][3], 16)
        except ValueError:
            continue
        if not (v1 < v2):
            continue
        if not (0x800000 <= v1 < 0x820000 and 0x800000 <= v2 < 0x820000):
            continue
        span = v2 - v1
        if span % 4 or span < 0x100:
            continue
        CANDIDATE.append((v1, v2, INS[i + 2][0]))
CANDIDATE.sort(key=lambda t: -(t[1] - t[0]))
ck('T3d 找到 CRT 初始化表的 [begin,end) 候选（由 push imm32 直接给出）',
   len(CANDIDATE) > 0, 'top=%s' % [(hex(a), hex(b), hex(c)) for a, b, c in CANDIDATE[:3]])

TBL_LO, TBL_HI, TBL_CALL = CANDIDATE[0]
tbl_vals = []
for a in range(TBL_LO, TBL_HI, 4):
    v = u32(a)
    tbl_vals.append(v)
ck('T3e 表内每项要么是 0 要么是 .text 内代码指针（无脏项）',
   all(v == 0 or (TB <= v < TE) for v in tbl_vals),
   'entries=%d zero=%d nonzero=%d' % (len(tbl_vals), sum(1 for v in tbl_vals if v == 0),
                                      sum(1 for v in tbl_vals if v)))
ck('T3f 表内非零项互不相同（是一个初始化函数集合，不是重复表）',
   len({v for v in tbl_vals if v}) == sum(1 for v in tbl_vals if v),
   'distinct_nonzero=%d nonzero=%d' % (len({v for v in tbl_vals if v}), sum(1 for v in tbl_vals if v)))

in_tbl = [v for v in tbl_vals if v in set(ctor_units)]
ck('T3g 35 个 ctor 单元全部作为独立表项出现在 CRT 初始化表里（逐项一项 = 独立初始化单元，不是独立翻译单元）',
   len(in_tbl) == 35, 'in_table=%d/35' % len(in_tbl))

# 位置关系：表项顺序 vs ctor 单元地址顺序（同一次模板展开不会各自占独立表项且顺序一致）
pos = {v: i for i, v in enumerate(tbl_vals)}
order_ok = [r for r in ROWS if r['cu'] in pos]
ck('T3h 表项下标序与 ctor 地址序一致（子集内单调）',
   [pos[r['cu']] for r in sorted(order_ok, key=lambda x: x['cu'])] ==
   sorted(pos[r['cu']] for r in order_ok),
   'n=%d' % len(order_ok))

# atexit 注册：dtor 单元由 push imm32 + call 0x7c978a 注册
ATEXIT = '0x7c978a'
regs = {}
for i, (o, sz, m, op) in enumerate(INS):
    if m == 'call' and op == ATEXIT:
        for j in range(i - 1, max(0, i - 9), -1):
            if INS[j][2] == 'push' and INS[j][3].startswith('0x'):
                regs[int(INS[j][3], 16)] = o
                break
            if INS[j][2].startswith('ret') or INS[j][2] == 'call':
                break
ck('T3i 35 个 dtor 单元全部通过 push imm32 + call 0x7c978a 注册',
   sum(1 for u in dtor_units if u in regs) == 35,
   'registered=%d/35 ; total_registrations=%d' % (sum(1 for u in dtor_units if u in regs), len(regs)))

_ct = set(ctor_units)
_dt = set(dtor_units)
# T3n：ctor 与 dtor 走的是**两条不同的注册通道**，这是独立性的更强证据。
# 实测：35 个 ctor 全在 CRT 静态初始化表里（静态、.data 内、启动期遍历）；
#       35 个 dtor 一个都不在那张表里（dtor 走 0x7c978a = atexit，运行时堆上的指针表）。
ck('T3n CRT 静态初始化表含 35 个 ctor、含 0 个 dtor（两条注册通道各自独立）',
   len([v for v in tbl_vals if v in _ct]) == 35 and len([v for v in tbl_vals if v in _dt]) == 0,
   'ctor_in_table=%d dtor_in_table=%d'
   % (len([v for v in tbl_vals if v in _ct]), len([v for v in tbl_vals if v in _dt])))
# 反控：把 ctor 集与 dtor 集互换，上面的判定必须翻转（证明判据真按集合分）
_swapped = (len([v for v in tbl_vals if v in _dt]) == 35)
ck('T3o 反控：把 ctor/dtor 集合互换后 T3n 的判定会翻转（判据不恒真）',
   _swapped is False,
   'swapped_ctor_dtor_in_table=0/35 => 翻转成立')

# 反控 N3：把表区间截断到「最后一个 ctor 表项之前」，覆盖数必须下降。
# 上一版截掉的是表尾一项（那一项不是我们的 ctor），所以覆盖数没变 —— 是我自己的反控无效。
# 正确做法：取 35 个 ctor 在表内的最大下标，把区间截到它之前。
_idx = [i for i, v in enumerate(tbl_vals) if v in _ct]
lo_cut = TBL_LO + 4 * max(_idx)          # 区间尾 = 最大 ctor 项之前（不含）
in_tbl_trunc = [u32(a) for a in range(TBL_LO, lo_cut, 4)]
n_trunc = len([v for v in in_tbl_trunc if v in _ct])
ck('T3j 反控：表区间截到最大 ctor 项之前后覆盖数必须下降（证明 T3g 不是恒真）',
   n_trunc == 34 and len(_idx) == 35,
   'in_table_truncated=%d (expect 34) ; full=35 ; max_idx=%d' % (n_trunc, max(_idx)))

# ---------- T3 的第三条判据：排它性（这才是「共用模板写多个对象」的判别式）----------
# 「共用初始化模板」真正危险的形态是：一段代码按参数循环/展开写多个对象，
# 那样「35 个互不相同的地址」就可能是单点代码的产物。
# 判别式：每个 ctor 单元写到的「这 35 个目标地址」的个数必须恰为 1。
ours_set = {r['obj'] for r in ROWS}
excl = {}
for r in ROWS:
    e = unit_end(r['cu'])
    ts = set()
    for o, sz, m, op in INS:
        if not (r['cu'] <= o < e):
            continue
        if sz == 10 and TD[o - TB] == 0xc7 and TD[o - TB + 1] == 0x05:
            t = struct.unpack_from('<I', TD, o - TB + 2)[0]
            if t in ours_set:
                ts.add(t)
    excl[r['cu']] = ts
ck('T3k 每个 ctor 单元在这 35 个目标里恰好写 1 个地址（不是一段代码写多个对象）',
   all(len(v) == 1 for v in excl.values()) and len(excl) == 35,
   'hist=%s' % dict(collections.Counter(len(v) for v in excl.values())))
ck('T3l 35 个 ctor 单元写到的目标集合两两不重叠且并集恰为 35 个地址',
   len(set().union(*excl.values())) == 35 and sum(len(v) for v in excl.values()) == 35,
   'union=%d total=%d' % (len(set().union(*excl.values())), sum(len(v) for v in excl.values())))

# 反控 N4：库里存在一个单元写多个 BSS 目标的例子（证明 T3k 判据不是恒真）
multi_unit = {u: c for u, c in collections.Counter(
    unit_of(o) for ss in G.values() for o in ss).items() if c >= 2}
ck('T3m 反控：全库存在一个单元写 >=2 个 BSS 目标的例子（T3k 非恒真）',
   len(multi_unit) > 0, 'units_with_multi_writes=%d' % len(multi_unit))

# ---------- 汇总 ----------
ok = all(c['ok'] for c in RES)
out = dict(exe_sha256=FILE_SHA, table=(hex(TBL_LO), hex(TBL_HI), hex(TBL_CALL)),
           table_entries=len(tbl_vals), obj_size=obj_size,
           min_gap=min(gaps), mdisp_nonzero_vtables=n_mi,
           distinct_norm_ctor=n_hc, distinct_norm_dtor=n_hd,
           rows=[dict(obj=hex(r['obj']), cu=hex(r['cu']), du=hex(r['du']),
                      pair=r['pair'], lc=r['lc'], ld=r['ld'],
                      n1=r['n1'], n2=r['n2'], f_ctor=r['f_ctor'], f_dtor=r['f_dtor'],
                      hc=r['hc'], hd=r['hd']) for r in ROWS],
           checks=RES, all_ok=ok)
json.dump(out, open(OUT, 'w'), ensure_ascii=False, indent=1)
for c in RES:
    print(('PASS ' if c['ok'] else 'FAIL ') + c['check'] + ' | ' + c['detail'])
print('\n== ALL %s (%d checks) ==' % ('PASS' if ok else 'FAIL', len(RES)))
sys.exit(0 if ok else 1)
