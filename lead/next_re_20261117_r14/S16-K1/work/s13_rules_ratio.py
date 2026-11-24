"""Step 13: RulesClass::ChargeToDrainRatio write site (Rules+0x760) -- auditable evidence."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from re_lib import *
b=Bin(); out=[]
out.append("=== ChargeToDrainRatio key string 0x83B828 xref in .text ===")
out.append("  push site: 0x671850 (imm32 raw), instruction boundary 0x671850")
out.append("=== disassembly 0x671830..0x671863 (skipdata=True) ===")
out.append(dump(b,0x671830,0x671864))
out.append("\n=== RulesClass+0x760 read sites in SW logic (from E11) ===")
for va in (0x6CBF5F,0x6CBF64,0x6CBF72,0x6CB99D,0x6CB9A3,0x6CBA10,0x6CBA1D):
    out.append(f"  {va:08X}: "+dump(b,va,va+8).splitlines()[0])
text="\n".join(out)
open(os.path.join(os.path.dirname(__file__),'..','EVIDENCE','E13_rules_charge_ratio.txt'),'w',encoding='utf-8').write(text)
print(text)
