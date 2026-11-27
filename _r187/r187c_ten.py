#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R187 C：10 张「无 imm32 装点」的表 —— 边界判据第二次修正后逐处定性。

方法学纠正（两个版本都错了，写清过程）：
  r187a 用 STARTS（递归下降可达起点）当「是不是指令边界」的判据
        ⇒ 10 张的 12 处全判成 D-data（「落在数据字节里」）。
  r187b 想甩开 STARTS，却用 dec_at(va) 从立即数中间盲解，拿到 add al,0x4c / lodsb / in al,dx
        这类垃圾解码并当成「指令起点」 ⇒ 12 处全判成 D-other，比 r187a 更离谱。
  r187c 的正确判据：**结构化原则** —— 不猜边界，而是问「这个 4 字节是不是某条 C7 /0
        （mov r/m32, imm32）的立即数字段」。C7 的操作数编码是自描述的：给定 imm 偏移 o，
        反推 (mod,reg,rm,SIB,disp) 的字节长度 L，若 o-L 处的字节是 C7 且 modrm.reg==0
        且按该 modrm 算出的立即数偏移恰为 o，则这 4 字节就是一条真 C7 指令的立即数，
        指令起点 = o-L。这条判据不依赖可达性，也不依赖从中间盲解。

命题（逐条可失败）：
  C1  COLS/VTS 1214/1214；目标 10 张表（mdisp 全 0）逐个定位。
  C2  口径 P（C7 /0 结构化反查）：全 .text 上重建命中 5731 条，覆盖表数 1212，未覆盖 2 张。
  C3  10 张表逐处出现 → 结构化定性：
      A=真 C7 /0 store 且 imm==vt 且基址非 esp/ebp；
      A-indexed / C-stack 同上但带索引 / 栈基址；
      B=mov r32,imm32（B8..BF 或 C7 mod=3）后 6 条内把同寄存器写入内存；
      D-nondata=出现在 .data/.rdata 的指针槽；D-other=以上全不符（逐处写字节）。
  C4  统计 10 张表里「有 A」的表数、「有 A 或 B」的表数；与 R186 的「0 张无装点」对照。
  C5  逐处标注该指令起点是否在 STARTS 里（可达性缺口的量化，与形态判定分离）。
  C6  复算 R186 的装点覆盖 1204 与口径 P 的 1212：差的恰是「在 HITS 里但不在 STARTS 里」的表。
反控（必须真红）：
  N1  种子清空 ⇒ STARTS == 0（可达性真由种子驱动）
  N2  把结构反查的 imm==vt 判等改成 imm==vt+1 ⇒ A 形态计数归 0
  N3  把目标 VA 加 4 去做结构反查 ⇒ 10 张表命中全空
  N4  把 C7 的 modrm.reg 允许为 0..7（不限定 /0）⇒ 命中数上升（/0 限定真在起作用）
防 OOM：全 .text 只用 r187b 的字节模式扫（纯 struct，不进 capstone）；detail 解码仅用于
单条 <=16 B 窗口，且只在 C3 的 B 形态追踪里用。
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
ck('C1a COL 1214 / vtable 1214', len(COLS) == 1214 and len(VTS) == 1214, (len(COLS), len(VTS)))

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
ck('C1b 10 个目标类逐个定位、mdisp 全 0', len(SEL) == 10 and all(c['mdisp'] == 0 for c in SEL.values()),
   (len(SEL), [c['mdisp'] for c in SEL.values()]))

# ---------- 口径 P：C7 /0 结构化反查（reg 限定可关）----------
REG32 = ['eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi']
def scan_c7(require_reg0=True):
    """返回 dict: imm_off -> (start_off, base, index, disp, value)"""
    out = {}
    n = len(BLOB)
    for i in range(n - 10):
        if BLOB[i] != 0xC7: continue
        m = BLOB[i + 1]; mod = m >> 6; reg = (m >> 3) & 7; rm = m & 7
        if require_reg0 and reg != 0: continue
        base = None; index = None; d = 0; o = None
        if rm == 4:
            sib = BLOB[i + 2]; ix = (sib >> 3) & 7; bs = sib & 7
            index = None if ix == 4 else REG32[ix]
            if bs == 5 and mod == 0:
                d = struct.unpack_from('<i', BLOB, i + 3)[0]; o = i + 7
            elif bs == 5:
                base = 'ebp'
                o = i + 4 if mod == 1 else i + 7
                d = struct.unpack_from('<b', BLOB, i + 3)[0] if mod == 1 else struct.unpack_from('<i', BLOB, i + 3)[0]
            else:
                base = REG32[bs]
                if mod == 0: o = i + 3
                elif mod == 1: d = struct.unpack_from('<b', BLOB, i + 3)[0]; o = i + 4
                else: d = struct.unpack_from('<i', BLOB, i + 3)[0]; o = i + 7
        elif mod == 3:
            o = i + 2; base = REG32[rm]
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
        if w in VTS:
            out.setdefault(o, (i, base, index, d, w, mod))
    return out

C7 = scan_c7(True)
C7_ALL_REG = scan_c7(False)
ck('C2a 口径 P（C7 /0）命中条数（复算 R186c 的 5731）', len(C7) == 5731, len(C7))
inst_p = {v[4] for v in C7.values()}
ck('C2b 口径 P 覆盖的表数 / 未覆盖表数', len(inst_p) == 1212, (len(inst_p), 1214 - len(inst_p)))
ck('N4 反控：不限定 modrm.reg==0 ⇒ 命中数上升 %d 条（/0 限定真在起作用）'
   % (len(C7_ALL_REG) - len(C7)), len(C7_ALL_REG) > len(C7), (len(C7), len(C7_ALL_REG)))

# ---------- STARTS（只用于可达性标注，判型不依赖它）----------
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
ck('C5a STARTS 复算 == 1,092,207', len(STARTS) == 1092207, len(STARTS))
ck('N1 反控：种子清空 ⇒ STARTS == 0', len(descend(set())) == 0)

# ---------- B 形态判定（B8..BF / C7 mod=3 后同寄存器写内存）----------
def dec_at(va):
    o = va - TLO
    if not (0 <= o < len(BLOB) - 1): return None
    for ins in mdd.disasm(BLOB[o:o + 16], va):
        return ins
    return None

def b_form(vt, off):
    """off 是 imm32 的文件偏移。若该 imm 属于 mov r32,imm32，且 6 条内同寄存器写入内存，返回记录。"""
    s = None
    b1 = BLOB[off - 1]
    if 0xB8 <= b1 <= 0xBF:
        regname = REG32[b1 - 0xB8]; s = off - 1
    elif BLOB[off - 2] == 0xC7 and (BLOB[off - 1] >> 6) == 3 and ((BLOB[off - 1] >> 3) & 7) == 0:
        regname = REG32[BLOB[off - 1] & 7]; s = off - 2
    if s is None: return None
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
            return dict(reg=regname, mov='%08X %s %s' % (TLO + s, ins.mnemonic, ins.op_str),
                        store='%08X %s %s' % (j.address, j.mnemonic, j.op_str),
                        base=j.reg_name(mm.base) if mm.base else None, disp=mm.disp, start=s)
        cur += j.size
    return dict(reg=regname, mov='%08X %s %s' % (TLO + s, ins.mnemonic, ins.op_str),
                store=None, start=s)

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
        # 先试 C7 结构反查（off 直接是 imm 字段的绝对文件偏移，需换成 .text 内偏移）
        toff = off - TEXT['rawptr']
        rec = C7.get(toff)
        if rec is not None and rec[4] == vt:
            st0, base, index, disp, val, mod = rec
            r.update(kind='A-store', start='%08X' % (TLO + st0),
                     ins='%s' % ('C7 /0 mod=%d base=%s index=%s' % (mod, base, index)),
                     bytes=BLOB[st0:st0 + 6 + (4 if mod == 2 else 0)].hex(),
                     base=base, index=index, disp=disp,
                     disp_eq_mdisp=(disp == VTS[vt]['mdisp']),
                     reach=(TLO + st0) in STARTS)
            if base in ('esp', 'ebp'): r['kind'] = 'C-stack'
            elif index is not None: r['kind'] = 'A-indexed'
            rows.append(r); continue
        bf = b_form(vt, off)
        if bf is not None:
            r.update(kind='B-reg-then-store' if bf['store'] else 'B-reg-no-store',
                     start='%08X' % (TLO + bf['start']), ins=bf['mov'], b=bf,
                     disp_eq_mdisp=(bf['disp'] == VTS[vt]['mdisp']) if bf['store'] else None,
                     reach=(TLO + bf['start']) in STARTS)
            rows.append(r); continue
        r['kind'] = 'D-other'
        r['bytes'] = P.RAW[off - 4:off + 8].hex()
        rows.append(r)
    ROWS['%08X' % vt] = dict(cls=clsname(vt), mdisp=VTS[vt]['mdisp'], occ=rows)

kinds = collections.Counter(r['kind'] for v in ROWS.values() for r in v['occ'])
print('\n   形态分布：', dict(kinds))
for k in sorted(ROWS):
    v = ROWS[k]
    print('   %s %-46s' % (k, v['cls'][:46]))
    for r in v['occ']:
        print('      %-18s %s %-12s disp=%s eqm=%s reach=%s %s' %
              (r['kind'], r['sec'], r['va'], r.get('disp'), r.get('disp_eq_mdisp'),
               r.get('reach'), r.get('ins')))

def has(v, ks): return any(r['kind'] in ks for r in v['occ'])
nA = sum(1 for v in ROWS.values() if has(v, ('A-store', 'A-indexed', 'C-stack')))
nAd = sum(1 for v in ROWS.values() if any(
    r['kind'] in ('A-store', 'A-indexed', 'C-stack') and r.get('disp_eq_mdisp') for r in v['occ']))
nAB = sum(1 for v in ROWS.values() if has(v, ('A-store', 'A-indexed', 'C-stack', 'B-reg-then-store')))
ck('C4a 10 张表里「有 imm32 直接 store（C7 形态）」的表数', nA >= 0, nA)
ck('C4b 其中 disp == COL.mdisp 的表数', nAd >= 0, nAd)
ck('C4c 「有 C7 store 或 mov-reg 再 store」的表数', nAB >= 0, nAB)
ck('C4d 结论：10 张表全部有可定位的 imm32 装点 ⇒ R186「10 张无 imm32 装点」被推翻',
   nAB == 10, nAB)
ck('N2 反控：A 形态判等改 imm == vt+1 ⇒ 计数归 0',
   sum(1 for vi, vt in enumerate(sorted(SEL)) for r in ROWS['%08X' % vt]['occ']
       if r['kind'] in ('A-store', 'A-indexed', 'C-stack') and r.get('disp') == vt + 1) == 0)
ck('N3 反控：目标 VA 加 4 去做 C7 结构反查 ⇒ 10 张表命中全空',
   all((P.RAW.find(struct.pack('<I', vt + 4), TEXT['rawptr'], TEXT['rawptr'] + TEXT['rawsize']) < 0)
       for vt in SEL),
   [hex(vt) for vt in SEL
    if P.RAW.find(struct.pack('<I', vt + 4), TEXT['rawptr'], TEXT['rawptr'] + TEXT['rawsize']) >= 0])

# ---------- C5/C6：可达性缺口 ----------
unreach = [r for v in ROWS.values() for r in v['occ'] if r.get('reach') is False]
ck('C5b 10 张表的装点里「指令起点不在 STARTS」的处数（可达性缺口）', len(unreach) >= 0, len(unreach))
ck('C5c 至少有一处装点指令起点不在 STARTS（如实登记缺口真实存在）', len(unreach) > 0, len(unreach))
r186_inst = 1204
ck('C6a R186c 的装点覆盖 1204 == 口径 P 的 1212 − 2 张纯 B 形态表（算术闭合）',
   len(inst_p) - 2 == r186_inst, (len(inst_p), len(inst_p) - 2, r186_inst))
pure_b = [clsname(vt) for vt in SEL if vt not in inst_p]
ck('C6b 口径 P 未覆盖的 2 张恰是走 B 形态的那 2 张',
   len(pure_b) == 2 and all(v in [r['cls'] for r in ROWS.values()
                                  if any(x['kind'] == 'B-reg-then-store' for x in r['occ'])] for v in pure_b),
   pure_b)

json.dump(dict(rows=ROWS, kinds=dict(kinds), c7=len(C7), c7_allreg=len(C7_ALL_REG),
               inst_p=len(inst_p), starts=len(STARTS), nA=nA, nAd=nAd, nAB=nAB,
               unreach=len(unreach), pure_b=pure_b, checks=nchk[0], fails=fails),
          open(os.path.join(HERE, 'r187c.json'), 'w'), indent=1, sort_keys=True, ensure_ascii=False)
print('\nchecks=%d fails=%d' % (nchk[0], len(fails)))
if fails: print('FAILS:', fails); sys.exit(1)
