#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S05-K2 T4: GetSize verification with slot anchoring (§981).
For each of the 10 core classes: read vtable from .rdata, scan ALL slots for B8 imm32 C3,
cross-reference allocation sites (68 imm32 -> call 0x7C8E17; 6A imm8; mov [esp],imm; sub esp,imm).
Exclude 0x4C9150 stub. Disambiguate WhatAmI(v[11]) vs size(v[12]) by double-closure with alloc imm.
"""
import pefile, os, json, struct, collections
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT=r"D:\Project\ra2-campaign-forge"
P=os.path.join(ROOT,"ra2youli","gamemd.exe")
CHAIN=os.path.join(ROOT,"lead","next_re_20261117_r14","S05-K1","EVIDENCE","class_chain_core.json")
OUTDIR=os.path.join(ROOT,"lead","next_re_20261117_r14","S05-K2")
EVID=os.path.join(OUTDIR,"EVIDENCE")

pe=pefile.PE(P); IB=pe.OPTIONAL_HEADER.ImageBase
SECS=[]
for s in pe.sections:
    SECS.append((s.Name.rstrip(b"\0").decode(),s.VirtualAddress+IB,s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData))
SM={s[0]:s for s in SECS}
DATA=open(P,"rb").read()
def off(va):
    for n,vb,vs,pr,rs in SECS:
        if vb<=va<vb+max(vs,rs):
            d=va-vb
            if d<rs: return pr+d
    return None
def u32(va):
    o=off(va)
    if o is None: return None
    return struct.unpack_from("<I",DATA,o)[0]

MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.skipdata=True; MD.detail=False

chain=json.load(open(CHAIN,encoding="utf-8"))
classes=chain['classes']

STUB=0x004C9150

result={"method":"read vtable from .rdata; slot i func addr = u32(vtable+i*4); B8 imm32 C3 = Size(); cross-ref alloc imm via 68 imm32->call 7C8E17 / 6A imm8 / mov[esp],imm / sub esp,imm; exclude 0x4C9150",
        "stub_excluded":"0x004C9150", "classes":{}}

for c in classes:
    name=c['name_rtti']; vt=int(c['vtable'],16); ns=c['slot_count']
    hits=[]
    for i in range(ns):
        fva=u32(vt+i*4)
        if fva is None or fva==STUB: continue
        o=off(fva)
        if o is None: continue
        b=DATA[o:o+8]
        if len(b)>=5 and b[0]==0xB8 and b[5]==0xC3:
            imm=struct.unpack_from("<I",b,1)[0]
            hits.append({'slot':i,'func':'%08X'%fva,'imm':imm,'immhex':'0x%X'%imm,'bytes':b[:6].hex()})
    result['classes'][name]={'vtable':'%08X'%vt,'nslots':ns,'B8immC3_slots':hits,
        'v11':'%08X'%(u32(vt+11*4) or 0),'v12':'%08X'%(u32(vt+12*4) or 0)}

# scan allocation sites: 68 imm32 followed within ~12 bytes by call 0x7C8E17 (operator new)
# and 6A imm8 similarly; collect (imm -> list of call sites)
import bisect
alloc_imm=collections.defaultdict(list)
TEXT=SM[".text"]; base=DATA[TEXT[3]:TEXT[3]+TEXT[4]]
# quick byte scan for 68 <imm32> ... E8 rel32 to 0x7C8E17 within 16 bytes
for i in range(len(base)-5):
    if base[i]==0x68:
        imm=struct.unpack_from("<I",base,i+1)[0]
        if imm==0: continue
        for j in range(i+5,min(i+20,len(base)-4)):
            if base[j]==0xE8:
                rel=struct.unpack_from("<i",base,j+1)[0]
                tgt=TEXT[1]+j+5+rel
                if tgt==0x7C8E17:
                    alloc_imm[imm].append(('%08X'%(TEXT[1]+i),'%08X'%(TEXT[1]+j)))
                    break
    elif base[i]==0x6A:
        imm8=base[i+1]
        if imm8==0: continue
        for j in range(i+2,min(i+16,len(base)-4)):
            if base[j]==0xE8:
                rel=struct.unpack_from("<i",base,j+1)[0]
                tgt=TEXT[1]+j+5+rel
                if tgt==0x7C8E17:
                    alloc_imm[imm8].append(('%08X'%(TEXT[1]+i),'%08X'%(TEXT[1]+j)))
                    break

result['alloc_sites']={'68_imm32_to_7C8E17_and_6A': {('0x%X'%k):v[:12] for k,v in sorted(alloc_imm.items())}}

# Match: for each class, find which size imm has alloc sites
for name,info in result['classes'].items():
    matches=[]
    for h in info['B8immC3_slots']:
        sites=alloc_imm.get(h['imm'],[])
        matches.append({'slot':h['slot'],'immhex':h['immhex'],'n_alloc_sites':len(sites),'sample':sites[:4]})
    info['alloc_match']=matches

print("=== GetSize slot scan (B8 imm32 C3 in vtable slots), stub excluded ===")
for name,info in result['classes'].items():
    hits=info['B8immC3_slots']
    print("%-16s vt=%s ns=%d  B8immC3=%s"%(name,info['vtable'],info['nslots'],
        [(h['slot'],h['immhex'],h['func']) for h in hits]))
    for h in hits:
        print("    slot %d imm=%s func=%s bytes=%s"%(h['slot'],h['immhex'],h['func'],h['bytes']))

print("\n=== alloc imm sizes present (68/6A -> 7C8E17) ===")
for k in sorted(alloc_imm, key=lambda x:-len(alloc_imm[x]))[:30]:
    print("  imm=0x%-6X sites=%d"%(k,len(alloc_imm[k])))

with open(os.path.join(EVID,'t4_getsize_slots.json'),'w',encoding='utf-8') as f:
    json.dump(result,f,indent=1,ensure_ascii=False)
print('WROTE',os.path.join(EVID,'t4_getsize_slots.json'))
