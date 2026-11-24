"""Exact count of +0x184 accesses by disassembling the whole AnimClass::AI/Update function."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import Bin, md, insn_text, write_text
import capstone
b=Bin(); m=md(detail=True,skipdata=True)
out=[]
# AnimClass::AI/Update 0x423AC0 is large; disassemble generously
for fn,label,nb in [(0x423AC0,"AnimClass::AI/Update",0x2000),
                     (0x421EA0,"AnimClass::ctor",0x400),
                     (0x422C70,"AnimClass::DrawIfVisible",0x40)]:
    out.append("=== %s @%08X ==="%(label,fn))
    n=0
    for i in m.disasm(b.read(fn,nb),fn):
        if i.id==0: continue
        for op in i.operands:
            if op.type==capstone.x86.X86_OP_MEM and op.mem.base!=0:
                if (op.mem.disp & 0xFFFFFFFF)==0x184:
                    w = bool(op.access & capstone.CS_AC_WRITE)
                    out.append("  %08X %s W=%s  %s"%(i.address,insn_text(i),w,i.bytes.hex()))
                    n+=1
    out.append("  total +0x184 accesses: %d"%n)
write_text("T3_anim184_exact.txt","\n".join(out)+"\n")
print("\n".join(out))
