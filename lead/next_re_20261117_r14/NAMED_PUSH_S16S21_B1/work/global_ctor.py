# -*- coding: utf-8 -*-
"""全局容器 vptr 安装点函数身份：构造器 vs 析构器。"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import np_core
from np_core import *
from capstone import *

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ctxt import back_func_start, dump

OP_DELETE = 0x7C8B3D

for wa, vt in [(0x004E6EFD, 0x007E9FE4), (0x004E6F28, 0x007EA004),
               (0x0071A3ED, 0x007F5114), (0x0071A418, 0x007F5134)]:
    fs = back_func_start(wa)
    print("\n" + "=" * 80)
    print("write %s -> vt %s ; func_start=%s" % (hx(wa), hx(vt), hx(fs) if fs else "?"))
    if not fs: continue
    insns = list(np_core._md.disasm(va_read(fs, 0x120), fs))
    has_del = any(i.id == X86_INS_CALL and i.operands and i.operands[0].type == X86_OP_IMM
                  and (i.operands[0].imm & 0xFFFFFFFF) == OP_DELETE for i in insns)
    print("  has_operator_delete=%s rets=%d callers=%d %s"
          % (has_del, sum(1 for i in insns if i.id == X86_INS_RET),
             len(find_direct_calls(fs)), [hx(c) for c in find_direct_calls(fs)[:5]]))
    dump(fs, min(fs + 0x60, wa + 0x20), "install func head")
