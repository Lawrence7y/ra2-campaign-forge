import sys,json,struct
from collections import defaultdict
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
R=P.RAW; seg=P.B['.text']; lo=seg['lo']; rp=seg['rawptr']; rs=seg['rawsize']
mdl=Cs(CS_ARCH_X86,CS_MODE_32); mdl.detail=False; mdl.skipdata=True
# A) build vtable slot map: all .rdata/.data dword V with dw(V-4)==COL-ish; here: find slot targets set
# COL detection reuse R218 criterion: dw(V-4) in .data range 0x800040? use set of vtable starts from previous rounds
import re
# simpler: collect all dwords in .data/.rdata that are COL: they point to .text and V-4 points to COL record.
# Use: V such that dw(V-4) is a valid COL addr (points into .data and its +0x10 is pTD string). Too heavy.
# Instead: check membership by scanning for the exact immediate bytes in .rdata/.data: value == target
def refs_imm32(target):
    hits=[]
    pat=struct.pack('<I',target)
    for sname in ('.rdata','.data'):
        s=P.B.get(sname)
        if not s: continue
        seg_bytes=R[s['rawptr']:s['rawptr']+s['rawsize']]
        st=0
        while True:
            k=seg_bytes.find(pat,st)
            if k<0: break
            hits.append((sname, s['lo']+k)); st=k+1
            if len(hits)>400: return hits
    return hits
for t in (0x7c7371,0x7c7350,0x8758e4,0x87b170,0x876ff4,0x879b30,0x87bd90,0x87c484):
    h=refs_imm32(t)
    print("imm32 refs to %#x: %d"%(t,len(h)), [x[1] for x in h[:8]])
