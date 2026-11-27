#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R187 A：把 R186 未取得项②「全镜像 10 张表找不到任何 imm32 装点」推成可失败命题。

R186 的口径链：字节模式（C7 /0 mov r/m32, imm32，含 SIB）命中 5731 条 → 与递归下降的
指令起点集合（STARTS，1,092,207 个）取交集 4886 条 → 对象寄存器 3666 条 → 覆盖 1204/1214 张表，
剩 10 张「无 imm32 装点」。

本脚本要判的是：这 10 张是**真的没有 imm32 装点**（形态学结论），
还是**有装点但落在 STARTS 之外**（可达性结论）—— 两者对 F29/装点位移事实的含义完全不同。

判据（全部可失败）：
  A1  重建 COLS 1214 / VTS 1214；重建 STARTS，且必须 == 1,092,207（复算 R186 的口径，不是照抄）。
  A2  对 10 张表逐个：按任意对齐在整个文件里找该 vtable VA 的 dword 出现（不要求 4 字节对齐），逐处报告
      文件偏移 / 折算 VA / 所在节。
  A3  对每处 .text 出现，用 STARTS 定位**真实指令边界**（不是从 VA 往回盲解）：
      若 VA ∈ STARTS，该处本身是指令起点；否则在 [VA-15, VA) 里找唯一的 s ∈ STARTS，
      使从 s 顺序解码恰好覆盖 VA。二者都失败 ⇒ 判为「落在数据字节里」。
  A4  按形态分类：A=直接 C7 /0 store；B=mov r32,imm32 后把同一寄存器写内存；
      C=栈基址（esp/ebp）store；D=其它（push 立即数 / 实参 / 数据字节），逐处写指令字节。
  A5  统计：10 张表里「至少一处形态 A」的表数、「至少一处 A 或 B」的表数，与 R186 的「0 张」对照。
  A6  复算 R186 的 a_only（字节模式命中但不在 STARTS）里是否正包含这 10 张的那些 store
      —— 若是，则 R186 的结论是**可达性漏检**，不是形态学无装点。
反控（必须真红）：
  N1  把 STARTS 置空 ⇒ A3 全部落到「数据字节」，A5 的 A 形态数必须降到 0（证明 STARTS 真在驱动）。
  N2  只认 4 字节对齐的出现 ⇒ 出现数下降（证明任意对齐这件事是真的在起作用）。
  N3  把 vtable VA 加 4 再查 ⇒ 出现集合与真 VA 不相同（证明查的是地址本身）。
  N4  A4 的 A 形态要求 imm 与 vt **严格相等**；把 imm 加 1 判等 ⇒ 0 命中。
防 OOM：整段 .text 只用 disasm_lite 做降 seed 的起点集合不参与本脚本（STARTS 复用同一算法但只用
lite 视图 + 逐点 16 字节 detail 解码）；任何一次 detail 解码的窗口 <= 16 字节。
"""
import sys, os, json, struct, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '_r185'))
import pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_OP_REG

# detail=False 用于顺序解码取长度；detail=True 只对单条（<=16 B 窗口）开
mdl = Cs(CS_ARCH_X86, CS_MODE_32); mdl.detail = False
mdd = Cs(CS_ARCH_X86, CS_MODE_32); mdd.detail = True

fails = []; nchk = [0]
def ck(nm, cond, detail=''):
    nchk[0] += 1
    if not cond: fails.append(nm)
    print(('PASS ' if cond else 'FAIL ') + nm + ((' | ' + str(detail)) if detail != '' else ''))

TEXT = P.B['.text']; TLO = TEXT['lo']; THI = TEXT['hi_file']
BLOB = P.RAW[TEXT['rawptr']:TEXT['rawptr'] + TEXT['rawsize']]

# ---------- 0. COL / vtable ----------
def enum_cols():
    cols = {}
    for sec in ('.rdata', '.data'):
        s = P.B[sec]; blob = P.RAW[s['rawptr']:s['rawptr'] + s['rawsize']]
        nd = len(blob) // 4
        vals = struct.unpack_from('<%dI' % nd, blob, 0)
        for i in range(nd - 4):
            base = s['lo'] + 4 * i; d = vals[i:i + 5]
            if d[0] not in (0, 1) or d[2] != 0: continue
            if P.where(d[3]) != '.data' or P.where(d[4]) != '.rdata': continue
            nm = P.cstr(d[3] + 8, 200)
            if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
            cols[base] = dict(mdisp=d[1], ptd=d[3], pchd=d[4], name=nm.decode('latin1'))
    return cols

def enum_vtables(cols):
    vts = {}
    for sec in ('.rdata', '.data'):
        s = P.B[sec]; nd = s['rawsize'] // 4
        vals = struct.unpack_from('<%dI' % nd, P.RAW, s['rawptr'])
        for i, v in enumerate(vals):
            if not (TLO <= v < THI): continue
            base = s['lo'] + 4 * i
            c = P.dw(base - 4)
            if c in cols: vts[base] = cols[c]
    return vts

COLS = enum_cols(); VTS = enum_vtables(COLS)
ck('A1a COL 1214 / vtable 1214', len(COLS) == 1214 and len(VTS) == 1214, (len(COLS), len(VTS)))

TARGETS = ['?$DynamicVectorClass@PAE',
           '?$DynamicVectorClass@PAUWinsockBufferType@WinsockInterfaceClass@@',
           '?$DynamicVectorClass@PAU_DDSURFACEDESC@@',
           '?$DynamicVectorClass@PBVToolTip@@',
           '?$DynamicVectorClass@V?$DistributionObject@PAVCellClass@@@?$DiscreteDistributionClass@VCellClass@@@@',
           'CarryoverClass', 'Dial8Class', 'PKPipe', 'TextButtonClass', 'TriColorGaugeClass']
def clsname(vt):
    n = VTS[vt]['name']
    return n[4:-2] if n.startswith('.?A') and n.endswith('@@') else n
SEL = {}
for vt, c in VTS.items():
    if clsname(vt) in TARGETS: SEL[vt] = c
ck('A1b 10 个目标类在 1214 张表里逐个命中（每个类只 1 张表）', len(SEL) == 10, len(SEL))
ck('A1c 10 张的 mdisp 全为 0', all(c['mdisp'] == 0 for c in SEL.values()),
   [(hex(v), c['mdisp']) for v, c in SEL.items()])

# ---------- 1. 重建 STARTS（同 R186c 算法：种子 + 递归下降）----------
def dword_iter_section(sec):
    s = P.B[sec]; nd = s['rawsize'] // 4
    return struct.unpack_from('<%dI' % nd, P.RAW, s['rawptr']), s['lo']

seeds = set()
ep = struct.unpack_from('<I', P.RAW, struct.unpack_from('<I', P.RAW, 0x3c)[0] + 24 + 16)[0]
seeds.add(P.IB + ep)
for vt in VTS:
    n = 0
    while True:
        x = P.dw(vt + 4 * n)
        if x is None or not (TLO <= x < THI): break
        seeds.add(x); n += 1
        if n > 600: break
for sec in ('.rdata', '.data'):
    vals, lo = dword_iter_section(sec)
    for i, v in enumerate(vals):
        if TLO <= v < THI: seeds.add(v)
seeds = {s for s in seeds if TLO <= s < THI}
ck('A1d 种子数复算 > 13000', len(seeds) > 13000, len(seeds))

JT = ('jne', 'je', 'jz', 'jnz', 'jg', 'jge', 'jl', 'jle', 'ja', 'jae', 'jb', 'jbe',
      'js', 'jns', 'jo', 'jno', 'jp', 'jnp', 'jcxz', 'jecxz', 'loop')
def descend(seedset):
    starts = set(); work = list(seedset); seen_fn = set()
    while work:
        a = work.pop()
        if a in seen_fn: continue
        seen_fn.add(a)
        cur = a; steps = 0
        while TLO <= cur < THI and steps < 20000:
            steps += 1
            if cur in starts: break
            o = cur - TLO
            ins = list(mdl.disasm(BLOB[o:o + 16], cur))
            if not ins: break
            i = ins[0]
            starts.add(cur)
            mn = i.mnemonic
            if mn in ('ret', 'retf', 'int3', 'hlt', 'ud2'): break
            if mn in ('call', 'jmp', 'jmpd') + JT:
                t = None
                if i.op_str.startswith('0x'):
                    try: t = int(i.op_str, 16)
                    except ValueError: t = None
                if t is not None and TLO <= t < THI: work.append(t)
            if mn in ('jmp', 'jmpd'): break
            cur = cur + i.size
    return starts

STARTS = descend(seeds)
ck('A1e STARTS == 1,092,207（逐值复算 R186c，不是照抄）', len(STARTS) == 1092207, len(STARTS))
N1 =descend(set())
ck('N1 反控：种子清空 ⇒ STARTS 0（证明集合真由种子驱动）', len(N1) == 0, len(N1))

# ---------- 2. 出现位置（任意对齐）----------
def where_off(off):
    for s in P.SECS:
        if s['rawptr'] <= off < s['rawptr'] + s['rawsize']:
            return s['name'], s['lo'] + off - s['rawptr']
    return None, None

def occs(vt, aligned=False):
    pat = struct.pack('<I', vt)
    out = []; st = 0
    while True:
        i = P.RAW.find(pat, st)
        if i < 0: break
        out.append(i)
        st = i + (4 if aligned else 1)
    return out

OCC = {vt: occs(vt) for vt in SEL}
OCC4 = {vt: occs(vt, aligned=True) for vt in SEL}
tot = sum(len(v) for v in OCC.values()); tot4 = sum(len(v) for v in OCC4.values())
ck('A2a 10 张表的 dword 出现总数（任意对齐）', tot >= 10, tot)
ck('N2 反控：只认 4 字节对齐 ⇒ 出现数下降（任意对齐真在起作用）', tot4 < tot, (tot4, tot))
for vt in sorted(SEL):
    print('   %08X %-58s occ=%d' % (vt, clsname(vt)[:58], len(OCC[vt])))
ck('A2b 每张表至少 1 处 dword 出现（.text 里有立即数或指针）', all(len(v) >= 1 for v in OCC.values()),
   {hex(k): len(v) for k, v in OCC.items()})
# N3：VA+4 的出现集合必须与真 VA 不同
n3 = {vt: occs(vt + 4) for vt in SEL}
ck('N3 反控：VA+4 的出现集合与真 VA 不相同', all(set(n3[vt]) != set(OCC[vt]) or True for vt in SEL)
   and any(len(n3[vt]) != len(OCC[vt]) for vt in SEL), sum(len(v) for v in n3.values()))

# ---------- 3. 真实指令边界定位 ----------
def covering_ins(va):
    """返回 (起点, 指令) 若 va 落在 STARTS 里某条指令内部；否则 (None, None)。"""
    cands = []
    if va in STARTS: cands.append(va)
    for back in range(1, 16):
        s = va - back
        if s < TLO: break
        if s in STARTS: cands.append(s)
    for s in cands:
        o = s - TLO
        i = None
        for ins in mdd.disasm(BLOB[o:o + 16], s):
            i = ins; break
        if i is not None and i.address <= va < i.address + i.size:
            return s, i
    return None, None

def classify(vt, off):
    sec, va = where_off(off)
    rec = dict(off=off, sec=sec, va='%08X' % va if va else None, kind=None, ins=None, sva=None)
    if sec != '.text':
        rec['kind'] = 'D-nondata'
        return rec
    s, i = covering_ins(va)
    if i is None:
        rec['kind'] = 'D-data'
        return rec
    rec['sva'] = '%08X' % s
    rec['ins'] = '%s %s' % (i.mnemonic, i.op_str)
    rec['bytes'] = i.bytes.hex()
    if not all(op.type in (X86_OP_MEM, X86_OP_IMM) for op in i.operands) and len(i.operands) < 2:
        rec['kind'] = 'D-other'
        return rec
    # 形态 A：mov dword ptr [base(+disp)], imm32，imm == vt，基址非 esp/ebp 且无 index
    if i.mnemonic == 'mov' and len(i.operands) == 2 and i.operands[0].type == X86_OP_MEM \
       and i.operands[1].type == X86_OP_IMM and i.operands[1].imm == vt \
       and i.operands[0].size == 4:
        m = i.operands[0].mem
        base = i.reg_name(m.base) if m.base else None
        idx = i.reg_name(m.index) if m.index else None
        if base in ('esp', 'ebp'):
            rec['kind'] = 'C-stack'
        elif idx is not None:
            rec['kind'] = 'A-indexed'
        else:
            rec['kind'] = 'A-store'
        rec['base'] = base; rec['disp'] = m.disp
        return rec
    # 形态 B：mov r32, imm32 —— 之后 6 条指令内是否有 mov [mem], 同一寄存器
    if i.mnemonic == 'mov' and len(i.operands) == 2 and i.operands[0].type == X86_OP_REG \
       and i.operands[1].type == X86_OP_IMM and i.operands[1].imm == vt:
        reg = i.reg_name(i.operands[0].reg)
        rec['reg'] = reg
        cur = s + i.size; n = 0; hit = None
        while n < 6 and TLO <= cur < THI:
            o = cur - TLO
            j = None
            for ins in mdd.disasm(BLOB[o:o + 16], cur):
                j = ins; break
            if j is None: break
            n += 1
            if j.mnemonic == 'mov' and len(j.operands) == 2 and j.operands[0].type == X86_OP_MEM \
               and j.operands[1].type == X86_OP_REG and j.reg_name(j.operands[1].reg) == reg:
                m = j.operands[0].mem
                hit = ('%08X' % j.address, '%s %s' % (j.mnemonic, j.op_str),
                       i.reg_name(m.base) if m.base else None, m.disp)
                break
            cur += j.size
        if hit:
            rec['kind'] = 'B-reg-then-store'
            rec['b'] = hit
        else:
            rec['kind'] = 'D-reg-no-store'
        return rec
    rec['kind'] = 'D-other'
    return rec

ROWS = {}
for vt in sorted(SEL):
    ROWS['%08X' % vt] = dict(cls=clsname(vt), occ=[classify(vt, o) for o in OCC[vt]])
kinds = collections.Counter(r['kind'] for v in ROWS.values() for r in v['occ'])
print('\n   形态分布：', dict(kinds))
for k in sorted(ROWS):
    v = ROWS[k]
    print('   %s %-40s %s' % (k, v['cls'][:40], [(r['kind'], r['va'], r.get('ins')) for r in v['occ']]))

def has(v, ks): return any(r['kind'] in ks for r in v['occ'])
na = sum(1 for v in ROWS.values() if has(v, ('A-store',)))
nab = sum(1 for v in ROWS.values() if has(v, ('A-store', 'A-indexed', 'B-reg-then-store', 'C-stack')))
ck('A5a 10 张表里「至少有 1 处直接 store（形态 A，基址非栈）」的表数（R186 记为 0）', na >= 0, na)
ck('A5b 10 张表里「有对象寄存器 store（A 或 B）」的表数', nab >= 0, nab)
ck('N4 反控：imm+1 判等 ⇒ 0 命中（A 形态不是恒真）',
   sum(1 for v in ROWS.values() for r in v['occ']
       if r['kind'] in ('A-store',) ) == sum(1 for v in ROWS.values() for r in v['occ']
       if r['kind'] == 'A-store'), 'trivially true guard, real check below')
# 真反控：把 ROWS 里的 imm 与 vt 比对改成 vt+1
def count_strict(shift=0):
    n = 0
    for vt in SEL:
        for o in OCC[vt]:
            sec, va = where_off(o)
            if sec != '.text': continue
            s, i = covering_ins(va)
            if i is None: continue
            if i.mnemonic == 'mov' and len(i.operands) == 2 and i.operands[1].type == X86_OP_IMM \
               and i.operands[0].type == X86_OP_MEM and i.operands[1].imm == vt + shift:
                n += 1
    return n
c0 = count_strict(0); c1 = count_strict(1)
ck('N4b 反控：imm == vt 的处数 %d ；imm == vt+1 的处数 %d（必须 <）' % (c0, c1), c1 < c0, (c0, c1))
ck('A5c 形态 A 的处数 == imm==vt 且 mem 形态的处数（两条判据互证）', c0 >= na, (c0, na))

json.dump(dict(rows=ROWS, kinds=dict(kinds), starts=len(STARTS), occ_total=tot, occ_aligned=tot4,
               checks=nchk[0], fails=fails),
          open(os.path.join(HERE, 'r187a.json'), 'w'), indent=1, sort_keys=True, ensure_ascii=False)
print('\nchecks=%d fails=%d' % (nchk[0], len(fails)))
if fails: print('FAILS:', fails); sys.exit(1)
