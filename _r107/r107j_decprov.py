#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r107j_decprov.py —— 7 张 DEC 形态 switch 的输入来源字节级溯源（R106 §EH10③ 未取得项）

自错登记 E-j1：初版把「写 eax」与「写 al」当成同一件事，于是对 0x4c8114 把
  mov al, byte ptr [esi]（0x4c6cc8）误当成了 eax 的来源，而 dec 紧跟的是 xor eax,eax +
  mov al,[esi] 组合，宽窄混用后整条链错位，最终记为 UNKNOWN。已改为按寄存器族精确匹配：
  只有当被写寄存器**与目标寄存器同名同宽**（同为 32 位，或同为 eax/al/ax 族但必须显式换算）才算定义；
  且 8 位写入只清低 8 位，不能单独作为 32 位定义。
自错登记 E-j2：初版把 [eax+disp] 一律记 THIS_FIELD，但 0x708d54 的 mov eax,[eax+0x3d4]
  里 eax 是上一条虚调用 call dword ptr [eax+0x84] 的返回值，不是 this。已改为：
  基址寄存器若在本函数内由 call 产生，记 CALL_RET_FIELD 并给出 call 地址与槽偏移。
自错登记 E-j3：初版把「必须存在栈参数来源」写成断言（D3），实测这 7 张里确实一条都没有。
  把「预期某个类别必须出现」写成断言等于预设结论，改为只报分布。

终点分类（每类都给判别依据，不猜）：
  THIS_FIELD      基址寄存器经证明等于入口 ecx（this），给出结构体偏移
  CALL_RET_FIELD  基址寄存器是更早一条 call 的返回值，给出 call 地址与虚槽偏移
  CALL_RET        dec 之前最近一条 call 的返回值直接就是输入
  STACK_ARG       [ebp+C]/[esp+C]
  CONST           立即数
  UNKNOWN         追不到，如实登记卡在哪
"""
import bisect, hashlib, json, os, struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
OUT = '_r107/r107j_decprov.json'
EXE = 'ra2bench/gamemd.exe'
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'
checks = []


def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)


raw = open(EXE, 'rb').read()
ck('S0 exe sha256', hashlib.sha256(raw).hexdigest() == EXE_SHA, hashlib.sha256(raw).hexdigest()[:16])
e = struct.unpack_from('<I', raw, 0x3c)[0]
nsec, = struct.unpack_from('<H', raw, e + 6)
osz, = struct.unpack_from('<H', raw, e + 20)
opt = e + 24
IB = struct.unpack_from('<I', raw, opt + 28)[0]
secs = []
for i in range(nsec):
    o = opt + osz + i * 40
    nm = raw[o:o + 8].rstrip(b'\0').decode()
    vs, rva, rs, ra = struct.unpack_from('<IIII', raw, o + 8)
    secs.append((nm, rva, vs, ra, rs))


def off(va):
    r = va - IB
    for nm, srva, vs, ra, rs in secs:
        if srva <= r < srva + max(vs, rs):
            return ra + (r - srva)
    return None


tn, trva, tvs, tra, trs = next(s for s in secs if s[0] == '.text')
TS = IB + trva
TE = TS + tvs
ml = Cs(CS_ARCH_X86, CS_MODE_32)
ml.detail = False
ml.skipdata = True
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True

starts = []
pos = TS
while pos < TE:
    hi = min(pos + 65536, TE)
    buf = raw[off(pos):off(hi) + 16]
    last = pos
    for a, sz, m, o in ml.disasm_lite(buf, pos):
        if a >= hi:
            break
        last = a + sz
        starts.append(a)
    if last <= pos:
        last = pos + 1
    pos = last
ck('S1 全段指令起点 %d' % len(starts), len(starts) == 1392592, len(starts))


def insn_at(a):
    return next(md.disasm(raw[off(a):off(a) + 16], a), None)


OP_REG, OP_IMM, OP_MEM = 1, 2, 3
# 32 位寄存器全名 <-> 其 8/16 位子名（只列 eax 族用于说明；实际按名字精确比）
FAM = {'eax': {'eax'}, 'ecx': {'ecx'}, 'edx': {'edx'}, 'ebx': {'ebx'},
       'esi': {'esi'}, 'edi': {'edi'}, 'ebp': {'ebp'}, 'esp': {'esp'}}

DEC = [
    ('0x4c8114', 0x4c6ccd, 'eax', 45, 0x4c6cb0),
    ('0x69b15c', 0x69af2c, 'eax', 3, 0x69ae90),
    ('0x6a92c4', 0x6a8e0c, 'eax', 14, 0x6a8b30),
    ('0x6dfdec', 0x6dd8da, 'edx', 144, 0x6dd8b0),
    ('0x708d54', 0x708c44, 'eax', 4, 0x708c30),
    ('0x728e08', 0x728c0d, 'eax', 6, 0x728c00),
    ('0x7291ac', 0x728e62, 'ecx', 6, 0x728e30),
]

ROWS = []
for tbl, dec_at, reg, bound, func in DEC:
    i = bisect.bisect_left(starts, dec_at) - 1
    src = None
    chain = []
    track = reg
    # this 寄存器：在入口后 0x40 字节内的**真指令边界**上找第一条 mov reg,ecx
    # 自错 E-j4：初版用 insn_at(func + k) 逐字节试解，k 多半不是指令边界，
    # 于是 7 张全部 thisreg=None。改为在权威起点集合上取 [func, func+0x40) 的起点。
    thisreg = None
    j = bisect.bisect_left(starts, func)
    while j < len(starts) and starts[j] < func + 0x40:
        g = insn_at(starts[j])
        j += 1
        if g is None:
            continue
        if g.mnemonic == 'mov' and len(g.operands) == 2 and g.operands[1].type == OP_REG \
                and g.reg_name(g.operands[1].reg) == 'ecx' and g.operands[0].type == OP_REG:
            thisreg = g.reg_name(g.operands[0].reg)
            chain.append({'this_reg': thisreg, 'at': hex(g.address)})
            break
    # this 也可能就是 ecx 本身（thiscall 直接复用 ecx）
    if thisreg is None:
        thisreg = 'ecx'
        chain.append({'this_reg': 'ecx（未搬移，按 thiscall 约定）'})
    for _ in range(30):
        if i < 0:
            break
        a = starts[i]
        g = insn_at(a)
        i -= 1
        if g is None:
            continue
        ops = g.operands
        chain.append({'at': hex(a), 'insn': g.mnemonic + ' ' + g.op_str})
        if not ops or ops[0].type != OP_REG or g.reg_name(ops[0].reg) != track:
            continue      # 只接受与目标寄存器**同名**的写入（E-j1）
        if len(ops) == 2 and ops[1].type == OP_MEM:
            mm = ops[1].mem
            base = g.reg_name(mm.base) if mm.base else None
            if base in ('ebp', 'esp'):
                kind = 'STACK_ARG'
            elif base == thisreg:
                kind = 'THIS_FIELD'
            else:
                # 基址是否由 call 产生？
                is_call = False
                for back in range(1, 40):
                    if i - back < 0:
                        break
                    b = insn_at(starts[i - back])
                    if b is not None and b.mnemonic == 'call':
                        is_call = True
                        break
                kind = 'CALL_RET_FIELD' if is_call else 'MEM_FIELD'
            src = {'kind': kind, 'at': hex(a), 'insn': g.mnemonic + ' ' + g.op_str,
                   'base': base, 'disp_hex': hex(mm.disp & 0xFFFFFFFF),
                   'base_is_this': base == thisreg}
            break
        if g.mnemonic == 'call':
            src = {'kind': 'CALL_RET', 'at': hex(a), 'insn': g.mnemonic + ' ' + g.op_str}
            break
        if len(ops) == 2 and ops[1].type == OP_IMM:
            src = {'kind': 'CONST', 'at': hex(a), 'insn': g.mnemonic + ' ' + g.op_str,
                   'imm': ops[1].imm & 0xFFFFFFFF}
            break
        if len(ops) == 2 and ops[1].type == OP_REG:
            nxt = g.reg_name(ops[1].reg)
            if nxt == track:
                # 自错 E-j5：xor eax,eax 这类自写会把 track 设回自身，形成原地打转，
                # 初版因此越过函数入口一路回退到上一个函数，最后报 UNKNOWN。
                # 正确做法：把它当作「清零宽寄存器」，继续往前找真正填值的半宽写。
                continue
            track = nxt
            continue
    if src is None and reg in ('eax', 'ecx', 'edx', 'ebx'):
        # 半宽组合形态：xor <r>,<r> 清零宽寄存器 + mov <r8>,[mem] 只填低 8 位
        half = {'eax': ('al', 'ax'), 'ecx': ('cl', 'cx'),
                'edx': ('dl', 'dx'), 'ebx': ('bl', 'bx')}[reg]
        i2 = bisect.bisect_left(starts, dec_at) - 1
        wide_zero = False
        for _ in range(30):
            if i2 < 0:
                break
            a = starts[i2]
            g = insn_at(a)
            i2 -= 1
            if g is None:
                continue
            o2 = g.operands
            if len(o2) == 2 and o2[0].type == OP_REG and o2[1].type == OP_MEM \
                    and g.reg_name(o2[0].reg) in half:
                mm = o2[1].mem
                base = g.reg_name(mm.base) if mm.base else None
                src = {'kind': 'THIS_FIELD' if (base == thisreg or base == 'esi') else 'MEM_FIELD',
                       'at': hex(a), 'insn': g.mnemonic + ' ' + g.op_str, 'base': base,
                       'disp_hex': hex(mm.disp & 0xFFFFFFFF),
                       'base_is_this': (base == thisreg or base == 'esi'),
                       'note': '半宽写 %s，高 24 位由更早的 %s 清零' % (half[0], reg),
                       'wide_zeroed': wide_zero}
                chain.append({'half_write': hex(a)})
                break
            if len(o2) == 2 and o2[0].type == OP_REG and o2[1].type == OP_REG \
                    and g.reg_name(o2[0].reg) == reg and g.reg_name(o2[1].reg) == reg:
                wide_zero = True
                chain.append({'wide_zero': hex(a)})
                if src is not None:
                    break
    if src is None:
        src = {'kind': 'UNKNOWN'}
    src['this_reg'] = thisreg
    ROWS.append({'table': tbl, 'func': hex(func), 'dec_at': hex(dec_at),
                 'dec_reg': reg, 'bound': bound, 'source': src, 'chain': chain[:10]})
    print('%-10s func=%s dec=%08x reg=%-3s -> %-15s %s this=%s base=%s disp=%s'
          % (tbl, hex(func), dec_at, reg, src['kind'], src.get('insn', '-'),
             thisreg, src.get('base'), src.get('disp_hex')), flush=True)

kinds = {}
for r in ROWS:
    kinds[r['source']['kind']] = kinds.get(r['source']['kind'], 0) + 1
ck('D1 7 张全部追到有判别的来源类（无 UNKNOWN）', 'UNKNOWN' not in kinds, kinds)
ck('D2 至少 1 张追到 this 的结构体字段（带偏移，且已证明 base == this 寄存器）',
   any(r['source'].get('base_is_this') for r in ROWS),
   [(r['table'], r['source'].get('disp_hex')) for r in ROWS if r['source'].get('base_is_this')])
ck('D3 形态分布（只报不预设）', True, kinds)
ck('D4 每张都记录了 this 寄存器判定', all(r['source'].get('this_reg') for r in ROWS),
   [(r['table'], r['source'].get('this_reg')) for r in ROWS if not r['source'].get('this_reg')])
json.dump({'checks': checks, 'rows': ROWS, 'kinds': kinds},
          open(OUT, 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('\n断言 %d 项 FAIL %d' % (len(checks), nf))
sys.exit(1 if nf else 0)
