import sys; sys.path.insert(0,".")
import np_core
from np_core import *
from ctxt import back_func_start, dump
OP_DEL=0x7C8B3D
for wa in (0x006CE717,0x006CE74D,0x006CE83B,0x006CEFED):
    fs=back_func_start(wa)
    print("\n== write %s -> func %s ==" % (hx(wa), hx(fs) if fs else "?"))
    if not fs: continue
    insns=list(np_core._md.disasm(va_read(fs,0x100), fs))
    has_del=any(i.id==X86_INS_CALL and i.operands and i.operands[0].type==X86_OP_IMM and (i.operands[0].imm&0xFFFFFFFF)==OP_DEL for i in insns)
    print("   has_operator_delete=%s atexit=%s callers=%s" % (has_del, is_atexit_registered(fs), [hx(c) for c in find_direct_calls(fs)[:5]]))
    dump(fs, min(fs+0x50, wa+0x18), "head")
