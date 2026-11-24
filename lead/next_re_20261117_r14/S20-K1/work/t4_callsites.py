"""T4 update-entry + T5 draw-interface: direct call-site scan (E8 rel32) for key funcs."""
import struct, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import Bin, write_tsv, write_text

b=Bin(); TLO,THI=b.sec_range(".text"); text=b.section_bytes(".text")
targets={
 0x423AC0:"AnimClass::AI/Update(v23)",
 0x62DF20:"PSys::Update_A(0x62DF20)",
 0x62E070:"PSys::Update_B(0x62E070)",
 0x5F3E70:"ParticleClass::AI(v23 default?)",
 0x62CEC0:"ParticleClass::Draw(v69)",
 0x62E280:"PSys::Draw(v69)",
 0x422CA0:"AnimClass::Draw(v69)",
 0x6D3D10:"Map::DrawIt",
 0x6D8DB0:"Object draw coordinator",
}
# build call target map in one pass
calls={}
pos=0
while True:
    j=text.find(b"\xE8",pos)
    if j<0: break
    pos=j+1; va=TLO+j
    if va+5>THI: break
    rel=struct.unpack_from("<i",text,j+1)[0]
    tgt=va+5+rel
    calls.setdefault(tgt,[]).append(va)

rows=[]; out=[]
for t,name in targets.items():
    sites=calls.get(t,[])
    out.append("%08X %-32s direct callers=%d: %s"%(t,name,len(sites),",".join("%08X"%s for s in sites[:20])))
    for s in sites: rows.append(["%08X"%t,name,"%08X"%s])
write_tsv("T4_update_callsites.tsv","target\tname\tcaller",rows)
write_text("T4_update_callsites.txt","\n".join(out)+"\n")
print("\n".join(out))
