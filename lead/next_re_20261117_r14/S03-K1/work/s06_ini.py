"""S03-K1 step6: INI parsing convergence + hash return + RULE dialog evidence."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from re_lib import *
b=Bin(); E=os.path.join(os.path.dirname(__file__),'..','EVIDENCE'); out=[]

out.append("===== INIClass::Load 0x4741F0 (convergence for both INI paths) =====\n"+dump(b,0x4741F0,0x474280))
out.append("\n===== INIClass::Load inner 0x525A60 head =====\n"+dump(b,0x525A60,0x525AC0))
out.append("\n===== hash 0x4A1DE0 tail (return value) =====\n"+dump(b,0x4A1F20,0x4A1F60))

# RULE 0x52CD70: enumerate direct calls to key APIs inside its range
insns=disasm_range(b,0x52CD70,0x52D500,skipdata=True)
out.append("\n===== RULE 0x52CD70 key calls (FindFirstFile IAT, CCFileClass ctor, INIClass::Load, DialogBox) =====")
for ins in insns:
    if ins.id==0: continue
    if ins.mnemonic=='call' or ('call' in ins.mnemonic):
        op=ins.op_str
        # direct known targets
        if op in ('0x4739f0','0x4741f0','0x46ce10') or '7e1208' in op or '7e120c' in op:
            out.append(f"  {ins.address:08X} {ins.mnemonic} {op}")
    if ins.mnemonic=='call' and op.startswith('0x') and int(op,16)==0x46ce10:
        out.append(f"  [merge] {ins.address:08X}")

# find DialogBox / DialogBoxParam IAT refs in RULE range by scanning op_str with dword ptr [0x...]
out.append("\n===== DialogBox indirect calls in RULE 0x52CD70..0x52D500 =====")
for ins in insns:
    if ins.id==0: continue
    if 'call' in ins.mnemonic and 'dword ptr' in ins.op_str:
        out.append(f"  {ins.address:08X} {ins.mnemonic} {ins.op_str}")

# BATTLE 0x52CB90 key calls similarly
insns2=disasm_range(b,0x52CB90,0x52CD70,skipdata=True)
out.append("\n===== BATTLE 0x52CB90 key calls =====")
for ins in insns2:
    if ins.id==0: continue
    if ins.mnemonic=='call' and ins.op_str in ('0x4739f0','0x4741f0','0x46ce10'):
        out.append(f"  {ins.address:08X} {ins.mnemonic} {ins.op_str}")

open(os.path.join(E,'E07_ini_convergence.txt'),'w',encoding='utf-8').write("\n".join(out))
print("\n".join(out))
