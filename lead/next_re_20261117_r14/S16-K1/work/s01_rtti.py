"""Step 1: independent RTTI discovery for the two SW classes."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from re_lib import *

b=Bin()
out=[]
out.append("IMAGEBASE %08X  sections:"%b.base)
for s in b.secs:
    out.append("  %-8s va=%08X vsize=%08X raw=%08X rawsize=%08X"%(s['name'],s['va'],s['vsize'],s['raw'],s['rawsize']))

for needle in ('SuperClass','SuperWeaponTypeClass'):
    tds=rtti_type_descriptors(b,needle)
    out.append(f"\n=== TypeDescriptor name contains {needle}: {len(tds)} ===")
    for td in tds:
        out.append("  TD %08X name=%r pVF=%08X sec=%s"%(td['va'],td['name'],td['pvf'],td['sec']))
        vfts=rtti_vftables(b,td['va'])
        out.append("    VFTables via COL: %d"%len(vfts))
        for v in vfts:
            out.append("      COL %08X vft=%08X off=%d cd=%d nslots=%d"%(v['col_va'],v['vftable_va'],v['offset'],v['cd'],len(v['slots'])))
            out.append("      slots[0..15]: "+" ".join("%08X"%x for x in v['slots'][:16]))

text="\n".join(out)
open(os.path.join(os.path.dirname(__file__),'..','EVIDENCE','E01_rtti.txt'),'w',encoding='utf-8').write(text)
print(text)
