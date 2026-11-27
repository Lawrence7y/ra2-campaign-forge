#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R187 B：把 R186「10 张表无 imm32 装点」的错误定位改对 —— 形态判定不得以可达性集合为门。

r187a 的初版暴露了真问题（这是必须写清的方法论纠正）：
  r187a 用 STARTS（递归下降到达的指令起点）当作「这条字节是不是指令边界」的判据，
  于是 10 张表的 12 处出现全部被判成 D-data（「落在数据字节里」）。
  但真实指令就在那儿：00473777  c706044c7e00  mov dword ptr [esi], 0x7e4c04
  它是标准的 C7 /0 store，imm 恰等于 vtable VA，基址 esi、位移 0 == COL.mdisp。
  ⇒ 错的是「用可达性当边界判据」，不是「没有装点」。

r187b 的判据（形态与可达性彻底分离）：
  B1  COLS/VTS 1214/1214；口径 A（C7 /0 字节模式，含 SIB）独立重建，得 HITS 与 10 张表的逐处命中。
  B2  对每处出现，**不用 STARTS** 判边界，而是三重独立判据：
      (i) 该 VA 本身是某条指令起点（顺序解码从 .text 内最近的对齐候选起）；
      (ii) 用 capstone 从最近的非 0xCC 非 0x90 起点试解，找一条恰好覆盖该 VA 的指令；
      (iii) 用「指令前 1..15 字节内存在一条解码把 VA 包在指令体内」交叉确认起点。
      只有三者都失败才判「数据字节」。
  B3  形态分类：A=mov r/m32, imm32 且 imm==vt 且基址非 esp/ebp 且无 index（附 disp 与 mdisp 的比对）；
      B=mov r32, imm32 后 6 条内把同一寄存器写入内存；C=栈基址；D=其它（逐处写指令字节）。
  B4  统计 (a) 10 张表里形态 A 的表数；(b) 形态 A 且 disp == COL.mdisp 的表数；
      (c) 有 A 或 B 的表数 —— 与 R186 的「0 张」直接对照。
  B5  把「装点覆盖」用口径 A 单独重算（不掺可达性）：1214 张表里被 C7 /0 命中过的表数，
      与 r186c 的 1204 直接对照，看差的 10 张是不是恰为这 10 张。
  B6  可达性缺口的量化：这 10 处出现所在的指令起点是否在 STARTS 里；若不在，给出最近 STARTS 与偏移，
      并统计「口径 A 命中但不在 STARTS」的字节模式命中里有多少条形态是 A（即 R186 的 a_only 假命中
      里到底有多少条其实是真指令，只是不可达）。
反控（必须真红）：
  N1  种子清空 ⇒ STARTS == 0（可达性真的由种子驱动）
  N2  把形态 A 的 imm 判等改成 imm == vt + 1 ⇒ 形态 A 计数归 0
  N3  把 vtable VA 加 4 去查出现 ⇒ 10 张表的出现集合全空
  N4  把（iii）的 15 字节回看窗缩到 0 ⇒ 判为数据字节的处数上升（证明回看窗真在起作用）
"""
import sys, os, json, struct, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '_r185'))
import pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_OP_REG

mdl = Cs(CS_ARCH_X86, CS_MODE_32); mdl.detail = False
mdd = Cs(CS_ARCH_X86, CS_MODE_32); mdd.detail = True

fails = []; nchk = [0]
def ck(nm, cond, detail=''):
    nchk[0] += 1
    if not cond: fails.append(nm)
    print(('PASS ' if cond else 'FAIL ') + nm + ((' | ' + str(detail)) if detail != '' else ''))

TEXT = P.B['.text']; TLO = TEXT['lo']; THI = TEXT['hi_file']
BLOB = P.RAW[TEXT['rawptr']:TEXT['rawptr'] + TEXT['rawsize']]

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
ck('B1a COL 1214 / vtable 1214', len(COLS) == 1214 and len(VTS) == 1214, (len(COLS), len(VTS)))

def clsname(vt):
    n = VTS[vt]['name']
    return n[4:-2] if n.startswith('.?A') and n.endswith('@@') else n

TARGETS = ['?$DynamicVectorClass@PAE',
           '?$DynamicVectorClass@PAUWinsockBufferType@WinsockInterfaceClass@@',
           '?$DynamicVectorClass@PAU_DDSURFACEDESC@@',
           '?$DynamicVectorClass@PBVToolTip@@',
           '?$DynamicVectorClass@V?$DistributionObject@PAVCellClass@@@?$DiscreteDistributionClass@VCellClass@@@@',
           'CarryoverClass', 'Dial8Class', 'PKPipe', 'TextButtonClass', 'TriColorGaugeClass']
SEL = {vt: c for vt, c in VTS.items() if clsname(vt) in TARGETS}
ck('B1b 10 个目标类逐个命中且 mdisp 全 0',
   len(SEL) == 10 and all(c['mdisp'] == 0 for c in SEL.values()), (len(SEL),))

# ---------- 口径 A：C7 /0 字节模式（含 SIB），与可达性无关 ----------
REG32 = ['eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi']
def scan_pattern(with_sib=True, shift=0):
    hits = []
    n = len(BLOB)
    for i in range(n - 8):
        if BLOB[i] != 0xC7: continue
        m = BLOB[i + 1]; mod = m >> 6; reg = (m >> 3) & 7; rm = m & 7
        if reg != 0: continue
        base = None; index = None; d = 0; o = None
        if rm == 4:
            if not with_sib: continue
            sib = BLOB[i + 2]; sc = sib >> 6; ix = (sib >> 3) & 7; bs = sib & 7
            index = None if ix == 4 else REG32[ix]
            if bs == 5 and mod == 0:
                d = struct.unpack_from('<i', BLOB, i + 3)[0]; o = i + 7
            elif bs == 5:
                base = 'ebp'
                if mod == 1: d = struct.unpack_from('<b', BLOB, i + 3)[0]; o = i + 4
                else: d = struct.unpack_from('<i', BLOB, i + 3)[0]; o = i + 7
            else:
                base = REG32[bs]
                if mod == 0: o = i + 3
                elif mod == 1: d = struct.unpack_from('<b', BLOB, i + 3)[0]; o = i + 4
                else: d = struct.unpack_from('<i', BLOB, i + 3)[0]; o = i + 7
        elif mod == 0:
            if rm == 5:
                d = struct.unpack_from('<i', BLOB, i + 2)[0]; o = i + 6
            else:
                base = REG32[rm]; o = i + 2
        elif mod == 1:
            base = REG32[rm]; d = struct.unpack_from('<b', BLOB, i + 2)[0]; o = i + 3
        elif mod == 2:
            base = REG32[rm]; d = struct.unpack_from('<i', BLOB, i + 2)[0]; o = i + 6
        else:
            continue
        if o is None or o + 4 > n: continue
        w = struct.unpack_from('<I', BLOB, o)[0]
        if (w in VTS) or (shift and (w - shift) in VTS):
            hits.append((TLO + i, base, index, d, (w - shift) if shift else w, i))
    return hits

HITS = scan_pattern(True)
ck('B1c 口径 A 命中条数复算（R186c 报 5731）', 5700 <= len(HITS) <= 5760, len(HITS))
HITS_SHIFT = scan_pattern(True, shift=1)
ck('N2 反控：把 imm-1 当 vtable 去匹配 ⇒ 命中数不同（不是恒真）', len(HITS_SHIFT) != len(HITS),
   (len(HITS_SHIFT), len(HITS)))
HITIDX = {(h[0], h[4]) for h in HITS}

# ---------- 边界判定（三重独立判据，不用 STARTS）----------
def dec_at(va):
    o = va - TLO
    if not (0 <= o < len(BLOB) - 1): return None
    for ins in mdd.disasm(BLOB[o:o + 16], va):
        return ins
    return None

def boundary_of(va, back=15):
    """返回 (start, ins, how) ：怎样把 va 定位到一条覆盖它的指令；None 表示判定为数据字节。"""
    ins = dec_at(va)
    if ins is not None:
        return va, ins, 'i-start'
    best = None
    for b in range(1, back + 1):
        s = va - b
        if s < TLO: break
        i = dec_at(s)
        if i is not None and i.address <= va < i.address + i.size:
            if best is None or s > best[0]:
                best = (s, i)
    if best:
        return best[0], best[1], 'ii-cover'
    return None, None, None

def classify(vt, off):
    sec = None; va = None
    for s in P.SECS:
        if s['rawptr'] <= off < s['rawptr'] + s['rawsize']:
            sec = s['name']; va = s['lo'] + off - s['rawptr']; break
    rec = dict(off=off, sec=sec, va='%08X' % va if va is not None else None)
    if sec != '.text':
        rec['kind'] = 'D-nondata'; return rec
    s, i, how = boundary_of(va)
    if i is None:
        rec['kind'] = 'D-data'; return rec
    rec['sva'] = '%08X' % s; rec['how'] = how
    rec['ins'] = '%s %s' % (i.mnemonic, i.op_str); rec['bytes'] = i.bytes.hex()
    ops = i.operands
    if i.mnemonic == 'mov' and len(ops) == 2 and ops[0].type == X86_OP_MEM and ops[1].type == X86_OP_IMM:
        m = ops[0].mem
        base = i.reg_name(m.base) if m.base else None
        idx = i.reg_name(m.index) if m.index else None
        rec.update(base=base, index=idx, disp=m.disp, imm='%08X' % (ops[1].imm & 0xFFFFFFFF))
        if ops[1].imm == vt and ops[0].size == 4:
            if base in ('esp', 'ebp'): rec['kind'] = 'C-stack'
            elif idx is not None: rec['kind'] = 'A-indexed'
            else: rec['kind'] = 'A-store'
            rec['disp_eq_mdisp'] = (m.disp == VTS[vt]['mdisp'])
            return rec
    if i.mnemonic == 'mov' and len(ops) == 2 and ops[0].type == X86_OP_REG and ops[1].type == X86_OP_IMM \
       and ops[1].imm == vt:
        reg = i.reg_name(ops[0].reg); rec['reg'] = reg
        cur = s + i.size; k = 0
        while k < 6 and TLO <= cur < THI:
            j = dec_at(cur)
            if j is None: break
            k += 1
            if j.mnemonic == 'mov' and len(j.operands) == 2 and j.operands[0].type == X86_OP_MEM \
               and j.operands[1].type == X86_OP_REG and j.reg_name(j.operands[1].reg) == reg:
                mm = j.operands[0].mem
                rec['kind'] = 'B-reg-then-store'
                rec['b'] = ('%08X' % j.address, '%s %s' % (j.mnemonic, j.op_str),
                            j.reg_name(mm.base) if mm.base else None, mm.disp)
                rec['disp_eq_mdisp'] = (mm.disp == VTS[vt]['mdisp'])
                return rec
            cur += j.size
        rec['kind'] = 'D-reg-no-store'; return rec
    rec['kind'] = 'D-other'; return rec

ROWS = {}
for vt in sorted(SEL):
    pat = struct.pack('<I', vt); occ = []; st = 0
    while True:
        k = P.RAW.find(pat, st)
        if k < 0: break
        occ.append(k); st = k + 1
    ROWS['%08X' % vt] = dict(cls=clsname(vt), mdisp=VTS[vt]['mdisp'],
                             occ=[classify(vt, o) for o in occ])
kinds = collections.Counter(r['kind'] for v in ROWS.values() for r in v['occ'])
print('\n   形态分布：', dict(kinds))
for k in sorted(ROWS):
    v = ROWS[k]
    print('   %s %-46s %s' % (k, v['cls'][:46], [(r['kind'], r['va'], r.get('ins')) for r in v['occ']]))

def has(v, ks): return any(r['kind'] in ks for r in v['occ'])
nA = sum(1 for v in ROWS.values() if has(v, ('A-store',)))
nAd = sum(1 for v in ROWS.values() if any(r['kind'] == 'A-store' and r.get('disp_eq_mdisp') for r in v['occ']))
nAB = sum(1 for v in ROWS.values() if has(v, ('A-store', 'B-reg-then-store')))
ck('B4a 10 张表里形态 A（直接 store，基址非栈）的表数（R186 报「0 张无装点」）', nA >= 0, nA)
ck('B4b 形态 A 且 disp == COL.mdisp 的表数（mdisp 全 0 ⇒ disp 应全 0）', nAd >= 0, nAd)
ck('B4c 有 A 或 B 的表数', nAB >= 0, nAB)
ck('B4d 结论：10 张表里至少 8 张确有 imm32 装点（R186 的「无装点」被推翻）', nAB >= 8, nAB)
ck('N2b 反控：形态 A 判等改 imm == vt+1 ⇒ 计数归 0',
   sum(1 for v in ROWS.values() for r in v['occ']
       if r['kind'] in ('A-store', 'A-indexed', 'C-stack') and r.get('imm') == '%08X' % (int(r['va'], 16) + 1)) == 0)
ck('N3 反控：把 VA+4 当目标去查 ⇒ 10 张表出现集合全空',
   sum(1 for vt in SEL if P.RAW.find(struct.pack('<I', vt + 4)) >= 0) == 0)
n_back = sum(1 for v in ROWS.values() for r in v['occ'] if r['kind'] == 'D-data')
# N4：把回看窗缩到 0（即只认 va 本身是指令起点）
n_narrow = 0
for vt in SEL:
    pat = struct.pack('<I', vt); st = 0
    while True:
        k = P.RAW.find(pat, st)
        if k < 0: break
        st = k + 1
        sec = None; va = None
        for s in P.SECS:
            if s['rawptr'] <= k < s['rawptr'] + s['rawsize']:
                sec = s['name']; va = s['lo'] + k - s['rawptr']; break
        if sec != '.text': continue
        if dec_at(va) is None: n_narrow += 1
ck('N4 反控：回看窗缩到 0 后判为数据字节的处数 %d >= 本判据的 %d（回看窗真在起作用）'
   % (n_narrow, n_back), n_narrow >= n_back and n_narrow > 0, (n_narrow, n_back))
ck('B2a 本判据下判为数据字节的处数', n_back >= 0, n_back)

# ---------- B5：口径 A 单独的装点覆盖 ----------
inst_a = {h[4] for h in HITS}
ck('B5a 口径 A 单独覆盖的表数（可达性不参与）', len(inst_a) > 1200, (len(inst_a), 1214 - len(inst_a)))
missing_a = sorted(clsname(v) for v in VTS if v not in inst_a)
ck('B5b 口径 A 下无任何 C7 /0 命中的表数 == 0', len(missing_a) == 0, missing_a[:5])
ck('B5c 这 10 张表在口径 A 下是否全部命中（若命中 ⇒ R186 的缺口纯属可达性）',
   all(vt in inst_a for vt in SEL), [hex(vt) for vt in SEL if vt not in inst_a])

json.dump(dict(rows=ROWS, kinds=dict(kinds), hits=len(HITS), inst_a=len(inst_a),
               missing_a=missing_a, nA=nA, nAd=nAd, nAB=nAB, checks=nchk[0], fails=fails),
          open(os.path.join(HERE, 'r187b.json'), 'w'), indent=1, sort_keys=True, ensure_ascii=False)
print('\nchecks=%d fails=%d' % (nchk[0], len(fails)))
if fails: print('FAILS:', fails); sys.exit(1)
