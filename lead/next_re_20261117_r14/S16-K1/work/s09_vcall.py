"""Step 9: channel-B function discovery in atlas hole 0x4F8300..0x4F9400,
and HouseClass::Update virtual dispatch tracing."""
import sys, os, struct, json, re
sys.path.insert(0, os.path.dirname(__file__))
from re_lib import *

b=Bin(); out=[]
cm=json.load(open(os.path.join(os.path.dirname(__file__),'calls_map.json')))
calls={int(k,16):[int(x,16) for x in v] for k,v in cm['calls'].items()}
jmps={int(k,16):[int(x,16) for x in v] for k,v in cm['jmps'].items()}
emit=out.append

lo,hi=0x4F8300,0x4F9400
cands=set()
for t in list(calls)+list(jmps):
    if lo<=t<hi: cands.add(t)
emit("=== channel-B function-entry candidates in atlas hole 0x4F8300..0x4F9400 ===")
for t in sorted(cands):
    emit(f"  target {t:08X}: called from {[hex(x) for x in calls.get(t,[])]}, jumped from {[hex(x) for x in jmps.get(t,[])]}")
    emit("    bytes: "+b.read(t,16).hex())

# Find House vftable base containing 0x4F8440 at 0x7EA8FC
emit("\n=== locate vftable base for HouseClass::Update vslot ===")
slotva=0x7EA8FC
for back in range(1,80):
    base=slotva-4*back
    colva=base-4
    try: sig,off,cd,ptd,pcd=struct.unpack('<IIIII',b.read(colva,20))
    except Exception: continue
    if sig==0 and 0x400000<=ptd<0xB80000:
        try: name=cstr(b,ptd+8,100)
        except Exception: continue
        emit(f"  vftable base {base:08X}, slot index {back}, COL {colva:08X}, TD {ptd:08X} name={name!r}")
        break

# Find code patterns that call [reg+slot*4] with slot from above (retry common slots if not found)
emit("\n=== direct call/jmp targets into 0x4F8440 via vtable: find all `call [reg+disp]` with disp plausible ===")
# scan linear .text for 'call dword ptr [reg + 0x??]' where disp in 0..0x400 and reg loaded from 0x7EA8xx; simplified:
# Instead find imm32 refs to vftable base in .text
for baseguess in (0x7EA8FC-4*back,):
    refs=imm32_refs(b,baseguess,'.text')
    emit(f"  imm32 refs to vftable base {baseguess:08X}: {[hex(x) for x in refs[:30]]}")

text="\n".join(out)
open(os.path.join(os.path.dirname(__file__),'..','EVIDENCE','E09_house_vcall.txt'),'w',encoding='utf-8').write(text)
print(text[:11000])
