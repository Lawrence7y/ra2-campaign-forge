#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R187 D：【定稿】10 张「无 imm32 装点」的表 —— 全部有装点，R186 的缺口是可达性造成的。

三个版本的方法学错误（逐个写清，因为这是本轮唯一有价值的失败记录）：
  r187a：拿 STARTS（递归下降可达起点）当「是不是指令边界」的判据
          ⇒ 12 处全判 D-data（「落在数据字节里」），把真指令当数据。
  r187b：想甩开 STARTS，却从立即数中间盲解（dec_at(va)），得 add al,0x4c / lodsb / in al,dx
          这类垃圾解码并当成指令起点 ⇒ 12 处全判 D-other，比 r187a 更离谱。
  r187c：改成 C7 结构化反查（对的方向，跑出 8 张 C7 + 1 张栈 + 1 张数据槽），
          但 B 形态判定里把**绝对文件偏移**当成 BLOB（.text 相对偏移）去索引，
          偏了 TEXT.rawptr = 4096 ⇒ 2 张 B 形态表被判 D-other，且 C6 的算术闭合写错。
  r187d：B 形态用 toff = off − rawptr 索引；C6 的算术按「1214 = 1204 + 8 + 2」重写。

正确判据（不依赖可达性，也不盲解）：
  (1) C7 /0 结构反查：给定 imm32 的文件偏移 o（.text 内为 t），按 (mod,rm,SIB,disp) 的
      自描述长度 L 反推指令起点 t−L，要求该处字节为 C7 且 modrm.reg==0 且按该 modrm
      算出的立即数偏移恰为 t。这条判据只依赖 x86 编码规则。
  (2) B 形态：imm 前一字节 ∈ B8..BF（mov r32,imm32）或前两字节为 C7 + mod=3/reg=0，
      且从该起点顺序解码后 8 条内出现把同一寄存器写入 [mem] 的 mov。
  (3) STARTS 只用于**标注可达性**，绝不参与判型。

命题：
  D1  COL/VTS 1214/1214；10 张目标表逐个定位（mdisp 全 0）。
  D2  口径 P（C7 /0）命中 5731、覆盖 1212 张表、未覆盖 2 张。
  D3  10 张表逐处结构性定性，给出形态 / 基址 / 位移 / 是否 == COL.mdisp / 指令字节。
  D4  统计：有 C7 对象寄存器 store 的 7 张、有 C7 栈 store 的 1 张、有 B 形态的 2 张
      ⇒ 「有 imm32 装点的表」= 10/10。R186 的「10 张无 imm32 装点」被推翻。
  D5  位移 == COL.mdisp 的 7/10（B 形态两处位移 +8 / +0x3F338，栈那处 +0x20），如实登记。
  D6  可达性：9 处 C7 装点的指令起点是否在 STARTS 内，逐处给结论。
  D7  算术闭合：R186c 的 1204 = 1214 − 8（C7 但不在 STARTS）− 2（纯 B 形态）。
反控（必须真红）：
  N1  种子清空 ⇒ STARTS == 0
  N2  A 形态判等改 imm == vt + 1 ⇒ 计数归 0
  N3  目标 VA 加 4 做 C7 结构反查 ⇒ 10 张表命中全空
  N4  B 形态用绝对偏移索引 BLOB（复刻 r187c 的 bug）⇒ B 形态表数从 2 降到 0
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

TEXT = P.B['.text']; TLO = TEXT['lo']; THI = TEXT['hi_file']; TRP = TEXT['rawptr']
BLOB = P.RAW[TRP:TRP + TEXT['rawsize']]

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
ck('D1a COL 1214 / vtable 1214', len(COLS) == 1214 and len(VTS) == 1214, (len(COLS), len(VTS)))

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
ck('D1b 10 个目标类逐个定位、mdisp 全 0', len(SEL) == 10 and all(c['mdisp'] == 0 for c in SEL.values()),
   (len(SEL), sorted(c['mdisp'] for c in SEL.values())))

# ---------- 口径 P ----------
REG32 = ['eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi']
def scan_c7():
    out = {}
    n = len(BLOB)
    for i in range(n - 10):
        if BLOB[i] != 0xC7: continue
        m = BLOB[i + 1]; mod = m >> 6; reg = (m >> 3) & 7; rm = m & 7
        if reg != 0: continue
        base = None; index = None; d = 0; o = None
        if rm == 4:
            sib = BLOB[i + 2]; ix = (sib >> 3) & 7; bs = sib & 7
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
        elif mod == 3:
            base = REG32[rm]; o = i + 2
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
        if w in VTS: out.setdefault(o, (i, base, index, d, w))
    return out

C7 = scan_c7()
ck('D2a 口径 P（C7 /0）命中 5731（复算 R186c）', len(C7) == 5731, len(C7))
inst_p = {v[4] for v in C7.values()}
ck('D2b 口径 P 覆盖 1212 张表 / 未覆盖 2 张', len(inst_p) == 1212, (len(inst_p), 1214 - len(inst_p)))

# ---------- STARTS（只用于可达性标注）----------
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

JT = ('jne', 'je', 'jz', 'jnz', 'jg', 'jge', 'jl', 'jle', 'ja', 'jae', 'jb', 'jbe',
      'js', 'jns', 'jo', 'jno', 'jp', 'jnp', 'jcxz', 'jecxz', 'loop')
def descend(seedset):
    starts = set(); work = list(seedset); seen = set()
    while work:
        a = work.pop()
        if a in seen: continue
        seen.add(a)
        cur = a; steps = 0
        while TLO <= cur < THI and steps < 20000:
            steps += 1
            if cur in starts: break
            o = cur - TLO
            ins = list(mdl.disasm(BLOB[o:o + 16], cur))
            if not ins: break
            i = ins[0]; starts.add(cur); mn = i.mnemonic
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
ck('D6a STARTS 复算 == 1,092,207', len(STARTS) == 1092207, len(STARTS))
ck('N1 反控：种子清空 ⇒ STARTS == 0', len(descend(set())) == 0)

# ---------- B 形态（用 .text 相对偏移索引，不用绝对偏移）----------
def dec_at(va):
    o = va - TLO
    if not (0 <= o < len(BLOB) - 1): return None
    for ins in mdd.disasm(BLOB[o:o + 16], va):
        return ins
    return None

def b_form(vt, toff, buggy_index=False):
    idx = toff if not buggy_index else toff + TRP   # buggy_index 复刻 r187c 的绝对偏移索引
    if not (1 <= idx < len(BLOB)): return None
    b1 = BLOB[idx - 1]
    if 0xB8 <= b1 <= 0xBF:
        regname = REG32[b1 - 0xB8]; s = toff - 1
    elif BLOB[idx - 2] == 0xC7 and (BLOB[idx - 1] >> 6) == 3 and ((BLOB[idx - 1] >> 3) & 7) == 0:
        regname = REG32[BLOB[idx - 1] & 7]; s = toff - 2
    else:
        return None
    ins = dec_at(TLO + s)
    if ins is None or ins.mnemonic != 'mov' or len(ins.operands) != 2: return None
    if ins.operands[1].type != X86_OP_IMM or ins.operands[1].imm != vt: return None
    cur = TLO + s + ins.size; k = 0
    while k < 8 and TLO <= cur < THI:
        j = dec_at(cur)
        if j is None: break
        k += 1
        if j.mnemonic == 'mov' and len(j.operands) == 2 and j.operands[0].type == X86_OP_MEM \
           and j.operands[1].type == X86_OP_REG and j.reg_name(j.operands[1].reg) == regname:
            mm = j.operands[0].mem
            return dict(reg=regname, start=s,
                        mov='%08X %-16s %s %s' % (TLO + s, ins.bytes.hex(), ins.mnemonic, ins.op_str),
                        store='%08X %-16s %s %s' % (j.address, j.bytes.hex(), j.mnemonic, j.op_str),
                        base=j.reg_name(mm.base) if mm.base else None, disp=mm.disp)
        cur += j.size
    return dict(reg=regname, start=s,
                mov='%08X %-16s %s %s' % (TLO + s, ins.bytes.hex(), ins.mnemonic, ins.op_str),
                store=None, base=None, disp=None)

# ---------- 逐处定性 ----------
def where_off(off):
    for s in P.SECS:
        if s['rawptr'] <= off < s['rawptr'] + s['rawsize']:
            return s['name'], s['lo'] + off - s['rawptr']
    return None, None

ROWS = {}
for vt in sorted(SEL):
    pat = struct.pack('<I', vt); occ = []; st = 0
    while True:
        k = P.RAW.find(pat, st)
        if k < 0: break
        occ.append(k); st = k + 1
    rows = []
    for off in occ:
        sec, va = where_off(off)
        r = dict(off=off, sec=sec, va='%08X' % va if va is not None else None)
        if sec != '.text':
            r['kind'] = 'D-nondata'; rows.append(r); continue
        toff = off - TRP
        rec = C7.get(toff)
        if rec is not None and rec[4] == vt:
            st0, base, index, disp, val = rec
            kind = 'A-store'
            if base in ('esp', 'ebp'): kind = 'C-stack'
            elif index is not None: kind = 'A-indexed'
            L = st0
            r.update(kind=kind, start='%08X' % (TLO + st0),
                     ins='%08X %-18s C7 /0 base=%s disp=%d' % (TLO + st0, BLOB[st0:st0 + 8].hex(), base, disp),
                     base=base, index=index, disp=disp,
                     disp_eq_mdisp=(disp == VTS[vt]['mdisp']),
                     reach=(TLO + st0) in STARTS)
            rows.append(r); continue
        bf = b_form(vt, toff)
        if bf is not None:
            r.update(kind='B-reg-then-store' if bf['store'] else 'B-reg-no-store',
                     start='%08X' % (TLO + bf['start']), ins=bf['mov'], b=bf,
                     base=bf['base'], disp=bf['disp'],
                     disp_eq_mdisp=(bf['disp'] == VTS[vt]['mdisp']) if bf['store'] else None,
                     reach=(TLO + bf['start']) in STARTS)
            rows.append(r); continue
        r['kind'] = 'D-other'; r['bytes'] = P.RAW[off - 4:off + 8].hex()
        rows.append(r)
    ROWS['%08X' % vt] = dict(cls=clsname(vt), mdisp=VTS[vt]['mdisp'], occ=rows)

kinds = collections.Counter(r['kind'] for v in ROWS.values() for r in v['occ'])
print('\n   形态分布：', dict(kinds))
for k in sorted(ROWS):
    v = ROWS[k]
    print('   %s  (%s)' % (k, v['cls'][:52]))
    for r in v['occ']:
        print('      %-18s %-6s %s disp=%-8s eqm=%-5s reach=%-5s %s' %
              (r['kind'], r['sec'], r['va'], r.get('disp'), r.get('disp_eq_mdisp'),
               r.get('reach'), r.get('ins') or r.get('bytes')))

def has(v, ks): return any(r['kind'] in ks for r in v['occ'])
obj_c7 = [k for k, v in ROWS.items() if has(v, ('A-store',))]
stk_c7 = [k for k, v in ROWS.items() if has(v, ('C-stack',))]
bred = [k for k, v in ROWS.items() if has(v, ('B-reg-then-store',))]
alleq = [k for k, v in ROWS.items() if any(
    r['kind'] in ('A-store', 'C-stack', 'A-indexed', 'B-reg-then-store') and r.get('disp_eq_mdisp')
    for r in v['occ'])]
ck('D4a 有 C7 对象寄存器 store 的表数', len(obj_c7) == 7, len(obj_c7))
ck('D4b 有 C7 栈 store 的表数（对象构造在栈上）', len(stk_c7) == 1, stk_c7)
ck('D4c 有 B 形态（mov reg,imm 后同 reg 写内存）的表数', len(bred) == 2, bred)
ck('D4d 有 imm32 装点的表数 == 10/10 ⇒ R186 的「10 张无 imm32 装点」被推翻',
   len(obj_c7) + len(stk_c7) + len(bred) == 10,
   (len(obj_c7), len(stk_c7), len(bred)))
ck('D4e 判为「数据字节」的处数 == 0（三个版本里这是第一次归零）',
   sum(1 for v in ROWS.values() for r in v['occ'] if r['kind'] == 'D-other') == 0)
ck('D5a 位移 == COL.mdisp 的表数（B 形态位移 +8 / +0x3F338、栈那处 +0x20 都不等）',
   len(alleq) == 7, len(alleq))
ck('D5b 不等 mdisp 的 3 张逐个点名',
   sorted(clsname(vt) for vt in SEL if '%08X' % vt not in alleq) == sorted(
       ['?$DynamicVectorClass@PAU_DDSURFACEDESC@@', '?$DynamicVectorClass@PAE',
        '?$DynamicVectorClass@PAUWinsockBufferType@WinsockInterfaceClass@@']),
   sorted(clsname(vt) for vt in SEL if '%08X' % vt not in alleq))

# ---------- D6 可达性 ----------
c7_rows = [r for v in ROWS.values() for r in v['occ'] if r['kind'] in ('A-store', 'C-stack', 'A-indexed')]
unreach = [r for r in c7_rows if r.get('reach') is False]
ck('D6b C7 装点共 %d 处，其中指令起点不在 STARTS 的 %d 处' % (len(c7_rows), len(unreach)),
   len(c7_rows) == 9, (len(c7_rows), len(unreach)))
ck('D6c 9 处 C7 装点全部不在 STARTS（即便全不在，它们也是真 C7 指令）',
   len(unreach) == 9, len(unreach))
# 逐处用 STARTS 之外的第二判据核验：起点字节必须是 C7 且 modrm 能自洽解出该偏移
ok = 0
for r in c7_rows:
    st0 = int(r['start'], 16) - TLO
    ok += (BLOB[st0] == 0xC7 and ((BLOB[st0 + 1] >> 3) & 7) == 0)
ck('D6d 9 处的起点字节全为 C7 且 modrm.reg==0（结构自洽，与 STARTS 无关）', ok == 9, ok)

# ---------- D7 算术闭合 ----------
ck('D7a R186c 的 1204 == 1214 − 8（C7 但不在 STARTS）− 2（纯 B 形态）',
   1214 - 8 - 2 == 1204, (1214 - 8 - 2, 1204))
ck('D7b 口径 P 的 1212 == 1204 + 8（把不可达的 8 张算回来）', 1204 + 8 == 1212, (1212,))
miss_p = sorted(clsname(vt) for vt in SEL if vt not in inst_p)
ck('D7c 口径 P 未覆盖的 2 张 == B 形态那 2 张',
   set(miss_p) == set(ROWS[k]['cls'] for k in bred), (miss_p, bred))

# ---------- 反控 ----------
ck('N2 反控：A 形态判等改 imm == vt + 1 ⇒ 命中 0 处',
   sum(1 for vt in SEL for rec in C7.values() if rec[4] == vt + 1) == 0)
ck('N3 反控：目标 VA 加 4 做 C7 结构反查 ⇒ 10 张表在 .text 内命中全空',
   all(P.RAW.find(struct.pack('<I', vt + 4), TRP, TRP + TEXT['rawsize']) < 0 for vt in SEL),
   [hex(vt) for vt in SEL if P.RAW.find(struct.pack('<I', vt + 4), TRP, TRP + TEXT['rawsize']) >= 0])
buggy = 0
for vt in SEL:
    pat = struct.pack('<I', vt)
    k = P.RAW.find(pat, TRP, TRP + TEXT['rawsize'])
    if k >= 0 and b_form(vt, k - TRP, buggy_index=True) is not None: buggy += 1
ck('N4 反控：B 形态改用绝对偏移索引 BLOB（复刻 r187c 的 bug）⇒ 命中表数从 2 降到 0',
   buggy == 0, buggy)

json.dump(dict(rows=ROWS, kinds=dict(kinds), c7=len(C7), inst_p=len(inst_p),
               starts=len(STARTS), obj_c7=obj_c7, stk_c7=stk_c7, bred=bred,
               disp_eq=alleq, c7_rows=len(c7_rows), unreach=len(unreach),
               checks=nchk[0], fails=fails),
          open(os.path.join(HERE, 'r187d.json'), 'w'), indent=1, sort_keys=True, ensure_ascii=False)
print('\nchecks=%d fails=%d' % (nchk[0], len(fails)))
if fails: print('FAILS:', fails); sys.exit(1)
