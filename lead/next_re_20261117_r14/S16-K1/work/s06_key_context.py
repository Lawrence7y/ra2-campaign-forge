"""Step 6 (fixed): key push site VAs from E04 are raw imm32 byte positions;
map to containing instruction via linear disasm of loader."""
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
from re_lib import *

b=Bin()
start=0x6CEA20; end=start+1085
insns=disasm_range(b,start,end)

keys={
 'RechargeTime':0x6CED61,'ManualControl':0x6CED4D,'SidebarImage':0x6CEDAB,
 'UseChargeDrain':0x6CED37,'AuxBuilding':0x6CED09,'PreDependent':0x6CEC92,
 'LineMultiplier':0x6CEC0A,'Range':0x6CEBF0,'SpecialSound':0x6CEB76,
 'ShowTimer':0x6CEB47,'PostClick':0x6CEB31,'PreClick':0x6CEB17,
 'AIDefendAgainst':0x6CEAF9,'FlashSidebarTabFrames':0x6CEAE3,
 'DisableableFromShell':0x6CEAC9,'IsPowered':0x6CEAAB,
 'Type':0x6CEC27,'Action':0x6CEA95,'StartSound':0x6CEBB2,
}
def containing(rawva):
    for i in insns:
        if i.id==0: continue
        if i.address<=rawva<i.address+i.size: return i
    return None
out=[]
for name,raw in keys.items():
    ins=containing(raw)
    if ins is None:
        out.append(f"\n### {name}: raw {raw:08X} not inside any instruction"); continue
    k=insns.index(ins)
    out.append(f"\n### {name}: raw imm32 {raw:08X} in insn {ins.address:08X} ({ins.mnemonic} {ins.op_str})")
    for j in range(max(0,k-3),min(len(insns),k+20)):
        out.append((">> " if j==k else "   ")+fmt(insns[j]))
text="\n".join(out)
open(os.path.join(os.path.dirname(__file__),'..','EVIDENCE','E06_ini_key_context.txt'),'w',encoding='utf-8').write(text)
print("wrote",len(text))
