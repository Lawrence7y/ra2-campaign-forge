import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-K1\work")
from re_lib import *
import capstone
lines=[]
def p(x=""): lines.append(str(x))
# key BulletClass own methods (not inherited stubs at 0x41xxxx/0x5fxxxx)
METHODS=[("slot3_0x46B560",0x46B560),("slot6_0x46AFB0",0x46AFB0),("slot8_0x46B5C0",0x46B5C0),
 ("slot10_0x4684E0",0x4684E0),("Draw_0x468090",0x468090),("0x466660",0x466660),
 ("0x468000",0x468000),("0x468670",0x468670),("0x46B5A0",0x46B5A0),("0x46B5B0",0x46B5B0)]
for name,fn in METHODS:
    at=ATLAS_FN.get(fn); sz=at[0] if at else 0x120
    ins=disasm(fn,min(sz,0x600))
    p(f"\n=== {name} fn={hex(fn)} size={sz} ===")
    for i in ins[:10]: p("  "+fmt_insn(i))
    p("  ...")
    # all field accesses in 0x40..0x160 with base reg name
    hits=[]
    for i in ins:
        for op in i.operands:
            if op.type==capstone.x86.X86_OP_MEM and op.mem.index==0 and 0x40<=op.mem.disp<0x160:
                bn=MD.reg_name(op.mem.base) if op.mem.base is not None else "abs"
                hits.append(f"[{bn}+0x{op.mem.disp:X}]({i.mnemonic}.{op.size})@{i.address:X}")
    p("  ACC: "+" ".join(hits[:50]))
open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-K1\EVIDENCE\bullet_methods2.txt","w",encoding="utf-8").write("\n".join(lines))
print("done",len(lines))
