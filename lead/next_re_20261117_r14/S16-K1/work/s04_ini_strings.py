"""Step 4: find SuperWeaponTypeClass INI keys and their code xrefs."""
import sys, os, struct, re
sys.path.insert(0, os.path.dirname(__file__))
from re_lib import *

b=Bin(); out=[]
emit=out.append

keys=['RechargeTime','Type','Action','Range','PostClick','PreClick','AuxBuilding',
      'SW.AuxBuildings','SidebarImage','SpecialSound','StartSound','UseChargeDrain',
      'IsPowered','DisableableFromShell','FlashSidebarTabFrames','AIDefendAgainst',
      'PreDependent','ShowTimer','ManualControl','LineMultiplier','SidebarImageFile']
emit("=== exact/NUL-terminated ASCII string hits ===")
strva={}
for key in keys:
    hits=find_bytes(b,key.encode())
    # filter to plausible standalone strings (preceded by non-alnum, followed by NUL or separator)
    good=[]
    for h in hits:
        if 0x7E0000<=h<0xB80000:
            good.append(h)
    strva[key]=good
    emit(f"{key:<26s} {len(hits):3d} total, {len(good):3d} data -> "+" ".join(f"{x:08X}" for x in good[:12]))

emit("\n=== all 'push <va>' xrefs to candidate key strings in .text ===")
# build map from imm32 value -> sites using raw byte scan for each VA (4 bytes little-endian)
for key,vas in strva.items():
    for va in vas:
        refs=imm32_refs(b,va,'.text')
        if refs:
            emit(f"{key:<26s} va={va:08X} refs={len(refs)} -> "+" ".join(f"{x:08X}" for x in refs[:20]))

text="\n".join(out)
open(os.path.join(os.path.dirname(__file__),'..','EVIDENCE','E04_ini_strings.txt'),'w',encoding='utf-8').write(text)
print(text)
