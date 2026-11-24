import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-K1\work")
from re_lib import *
import capstone
lines=[]
def p(x=""): lines.append(str(x))
for name,fn in [("Warhead resolver 0x75E3B0",0x75E3B0),("BulletType resolver 0x46C790",0x46C790)]:
    at=ATLAS_FN.get(fn); sz=at[0] if at else 0x80
    p(f"=== {name} size={sz} ===")
    for i in disasm(fn,min(sz,0x100)):
        extra=""
        if i.mnemonic=="mov" and len(i.operands)==2 and i.operands[1].type==2:
            s=cstr(i.operands[1].imm&0xFFFFFFFF,40)
            if s and all(0x20<ord(c)<0x7F for c in s) and len(s)>2: extra=f" ; '{s}'"
        p("  "+fmt_insn(i)+extra)
    p()
open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-K1\EVIDENCE\resolvers.txt","w",encoding="utf-8").write("\n".join(lines))
print("done")
