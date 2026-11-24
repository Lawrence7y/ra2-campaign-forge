"""T4 supplement: identify FactoryClass-family vtables by RTTI chain scan and
verify GetSize dual-check for each named class."""
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
from re_helper import Bin, EVID
b=Bin(); L=[]
r=b.sec(".rdata"); buf=b.pe.__data__[r["raw"]:r["raw"]+r["rawsize"]]; base=r["va"]
# find TypeDescriptors by names, then COLs pointing to them, then vtables pointing to COLs
names=[b".?AVBuildingClass@@", b".?AVCellClass@@", b".?AVTechnoClass@@", b".?AVTerrainClass@@",
       b".?AVFactoryClass@@", b".?AVBuildingFactoryClass@@", b".?AVUnitFactoryClass@@",
       b".?AVInfantryFactoryClass@@", b".?AVAircraftFactoryClass@@"]
L.append("RTTI name -> vtable -> GetSize (slot12 B8 imm32 C3) + push-size count")
L.append("="*88)
L.append("sections: "+", ".join("%s:%08X..%08X"%(s['name'],s['va'],s['va']+s['rawsize']) for s in b.sections))
for name in names:
    td_hits=[]
    for sec in b.sections:
        if sec['name']=='.text': continue
        sbuf=b.pe.__data__[sec['raw']:sec['raw']+sec['rawsize']]
        sbase=sec['va']; off=0
        while True:
            i=sbuf.find(name,off)
            if i<0: break
            td=sbase+i-8
            tp=td.to_bytes(4,'little')
            for s2 in b.sections:
                if s2['name']=='.text': continue
                b2=b.pe.__data__[s2['raw']:s2['raw']+s2['rawsize']]; base2=s2['va']; off2=0
                while True:
                    j=b2.find(tp,off2)
                    if j<0: break
                    col=base2+j-0xC; cp=col.to_bytes(4,'little')
                    for s3 in b.sections:
                        if s3['name']=='.text': continue
                        b3=b.pe.__data__[s3['raw']:s3['raw']+s3['rawsize']]; base3=s3['va']; off3=0
                        while True:
                            k=b3.find(cp,off3)
                            if k<0: break
                            vt=base3+k+4
                            if vt%4==0:
                                try:
                                    gs=b.u32(vt+0x30); code=b.read(gs,8)
                                    if code[0]==0xB8 and code[5]==0xC3:
                                        sz=struct.unpack('<I',code[1:5])[0]
                                        td_hits.append((td,col,vt,gs,sz))
                                except Exception: pass
                            off3=k+1
                    off2=j+1
            off=i+1
    nm=name.decode('ascii',errors='replace')
    L.append("%-40s hits=%d"%(nm,len(td_hits)))
    seen=set()
    for td,col,vt,gs,sz in td_hits:
        if (vt,gs,sz) in seen: continue
        seen.add((vt,gs,sz))
        t=b.sec('.text'); tb=b.pe.__data__[t['raw']:t['raw']+t['rawsize']]
        pat=b'\x68'+sz.to_bytes(4,'little'); o=0; ph=[]
        while True:
            q=tb.find(pat,o)
            if q<0: break
            ph.append(t['va']+q); o=q+1
        L.append("  vt=%08X col=%08X td=%08X GetSize=%08X size=0x%X(%d) push_sites=%d %s"%(
            vt,col,td,gs,sz,sz,len(ph)," ".join(hex(x) for x in ph[:12])))
out=os.path.join(EVID,"t4_factory_getsize.txt")
with open(out,"w",encoding="utf-8") as f:f.write("\n".join(L)+"\n")
print("wrote",out,"lines",len(L))
