"""Step 2: vtable slot 11/12 verification + ctor discovery via vftable writes."""
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
from re_lib import *

b=Bin(); out=[]

def emit(s=''): out.append(str(s))

emit("=== GetSize/WhatAmI slot disassembly ===")
for name,va in [('SuperClass::WhatAmI v[11]',0x6CE200),('SuperClass::GetSize v[12]',0x6CE210),
                ('SWType::WhatAmI v[11]',0x6CE900),('SWType::GetSize v[12]',0x6CE910)]:
    emit(f"\n--- {name} @ {va:08X} ---")
    emit(dump(b,va,va+24))

emit("\n\n=== writes of main vftable immediate in .text (push/mov imm32) ===")
for vft,name in [(0x7F3FE8,'SuperClass'),(0x7F4090,'SuperWeaponTypeClass')]:
    hits=imm32_refs(b,vft,'.text')
    emit(f"\n{name} vft {vft:08X}: {len(hits)} raw imm32 hits")
    for h in hits:
        emit(f"  {h:08X}: "+dump(b,h-4,h+8).replace('\n',' | '))

emit("\n\n=== TClassFactory Create slots (first 6) ===")
for va in (0x6BF450,0x6BF460,0x6BF470,0x6BF480,0x6BF490,0x6BF4A0, # SWType factory
           0x6BF5D0,0x6BF640): # SuperClass factory
    try:
        emit(f"\n--- {va:08X} ---")
        emit(dump(b,va,va+96))
    except Exception as e:
        emit(f"  error {e}")

text="\n".join(out)
open(os.path.join(os.path.dirname(__file__),'..','EVIDENCE','E02_vftable_slots.txt'),'w',encoding='utf-8').write(text)
print(text)
