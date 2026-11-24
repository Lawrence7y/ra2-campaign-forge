"""S03-K1 step7: base-class fields (file handle +0x14, filename pointer +0x18) + full CC ctor."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from re_lib import *
b=Bin(); E=os.path.join(os.path.dirname(__file__),'..','EVIDENCE'); out=[]

out.append("===== RawFileClass::Open 0x65CBF0 head (filename @ +0x18, CreateFileA) =====\n"+dump(b,0x65CBF0,0x65CC70))
out.append("\n===== CCFileClass base ctor 0x47AA30 head (inherited fields) =====\n"+dump(b,0x47AA30,0x47AAB0))
out.append("\n===== CCFileClass ctor full 0x4739F0..0x473AE0 =====\n"+dump(b,0x4739F0,0x473AE0))
# writes to [esi+0x14]/[esi+0x18] across ccfile cluster (base-class fields used via CCFile this)
out.append("\n===== [reg+0x14]/[reg+0x18] uses in rawfile open =====\n")
for ins in disasm_range(b,0x65CBF0,0x65CC70,skipdata=True):
    if ins.id and ('0x14]' in ins.op_str or '0x18]' in ins.op_str):
        out.append(f"  {ins.address:08X} {ins.mnemonic} {ins.op_str}")

open(os.path.join(E,'E09_basefields.txt'),'w',encoding='utf-8').write("\n".join(out))
print("\n".join(out[:150]))
