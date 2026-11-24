"""Step 8: call-frequency evidence chain for HasChargeProgressed 0x6CBCA0."""
import sys, os, struct, json
sys.path.insert(0, os.path.dirname(__file__))
from re_lib import *

b=Bin(); out=[]
cm=json.load(open(os.path.join(os.path.dirname(__file__),'calls_map.json')))
calls={int(k,16):[int(x,16) for x in v] for k,v in cm['calls'].items()}
rows,hdr=load_atlas()

emit=out.append
emit("=== raw call sites of 0x6CBCA0 and their containing atlas functions ===")
for site in calls.get(0x6CBCA0,[]):
    r=func_containing(rows,site)
    emit(f"  site {site:08X} in fn "+(f"{r[0]:08X}+{r[1]}" if r else "ATLAS GAP"))
    emit("    "+dump(b,site-0x40,site+0x30).replace("\n","\n    "))

emit("\n=== is 0x4F9370 dead? direct call sites and imm32 refs ===")
emit(f"  direct call sites: {calls.get(0x4F9370,[])}")
emit(f"  imm32 refs in .text: {[hex(x) for x in imm32_refs(b,0x4F9370,'.text')]}")

emit("\n=== vftables containing HouseClass::Update 0x4F8440 ===")
vft_hits=[]
for va in find_bytes(b,struct.pack('<I',0x4F8440)):
    # likely vftable slot; print surrounding 8 dwords if in .data/.rdata
    if 0x7E0000<=va<0xB80000:
        slots=[b.u32(va+4*i) for i in range(-3,5)]
        emit(f"  ref {va:08X} slots[-3..4]: "+" ".join(f"{x:08X}" for x in slots))
        vft_hits.append(va)

emit("\n=== direct callers of CurrentFrame increment site function ===")
# find all inc dword [0xA8ED84]
for pat,tag in [(b'\xff\x05\x84\xed\xa8\x00','inc dword [0xA8ED84]'),
                (b'\x83\x05\x84\xed\xa8\x00\x01','add dword [0xA8ED84],1')]:
    for h in find_bytes(b,pat,'.text'):
        r=func_containing(rows,h)
        emit(f"  {tag} @ {h:08X} in fn "+(f"{r[0]:08X}+{r[1]}" if r else "GAP"))

emit("\n=== call sites of main-loop function 0x55DE60 (if atlas) ===")
for t in (0x55DE60,0x55DE80,0x55DEC0):
    emit(f"  {t:08X}: {[hex(x) for x in calls.get(t,[])]}")

text="\n".join(out)
open(os.path.join(os.path.dirname(__file__),'..','EVIDENCE','E08_charge_callers.txt'),'w',encoding='utf-8').write(text)
print(text[:12000])
