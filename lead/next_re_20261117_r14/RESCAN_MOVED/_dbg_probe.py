# -*- coding: utf-8 -*-
"""全 .text 精确探针：真实 M2（call → mov [ebp/esp±x],eax → cmp/test 同一栈槽 → jcc）"""
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import *

pe = pefile.PE(r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe')
IB = pe.OPTIONAL_HEADER.ImageBase
sec = next(s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.text')
VA = IB + sec.VirtualAddress
D = sec.get_data()
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True; md.skipdata = True
ins = list(md.disasm(D, VA))
print('total insns', len(ins))

import capstone.x86 as cx86
JCC = set(getattr(cx86, n) for n in dir(cx86)
          if n.startswith('X86_INS_J') and n != 'X86_INS_JMP'
          and isinstance(getattr(cx86, n), int))


def slot(op):
    if op.type != X86_OP_MEM:
        return None
    if op.mem.base not in (cx86.X86_REG_EBP, cx86.X86_REG_ESP):
        return None
    return (op.mem.base, op.mem.index, op.mem.disp)


strict = 0
loose = 0
for i, x in enumerate(ins):
    if x.id != X86_INS_CALL:
        continue
    if i + 3 >= len(ins):
        continue
    b, c, d = ins[i + 1], ins[i + 2], ins[i + 3]
    if not (b.id == X86_INS_MOV and b.operands[0].type == X86_OP_MEM
            and b.operands[1].type == X86_OP_REG
            and b.operands[1].reg == X86_REG_EAX and slot(b.operands[0])):
        continue
    loose += 1
    if loose <= 8:
        print('LOOSE %08X call %s ; %s %s ; %s %s' % (
            x.address, x.op_str, b.mnemonic, b.op_str, c.mnemonic, c.op_str))
    k = slot(b.operands[0])
    if c.id in (X86_INS_CMP, X86_INS_TEST) and len(c.operands) == 2:
        if slot(c.operands[0]) == k and c.operands[1].type in (X86_OP_IMM, X86_OP_REG):
            if d.id in JCC:
                strict += 1
                if strict <= 8:
                    print('STRICT %08X call %s ; %s %s ; %s %s ; %s %s' % (
                        x.address, x.op_str, b.mnemonic, b.op_str,
                        c.mnemonic, c.op_str, d.mnemonic, d.op_str))
print('loose(mov after call)', loose, 'strict(+same-slot cmp +jcc right after)', strict)
