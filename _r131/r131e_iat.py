#!/usr/bin/env python3
# R131 r131e: name the three IAT slots used by the loop, read the export-name string at
# 0x840de4, and count imm32 refs of the IID 0x817bc0 (uniqueness control).
import json, struct
import pefile
EXE='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT='/home/t628/projects/ra2-campaign-forge/_r131/r131e_iat.json'
pe=pefile.PE(EXE, fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase
secs={}
for s in pe.sections:
    nm=s.Name.rstrip(b'\x00').decode('latin-1')
    secs[nm]=(base+s.VirtualAddress, base+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData), s)
tlo,thi,ts=secs['.text']; data=ts.get_data()
R={}
pe2=pefile.PE(EXE)
imp={}
for e in getattr(pe2,'DIRECTORY_ENTRY_IMPORT',[]):
    for i in e.imports:
        if i.address: imp[i.address]=(e.dll.decode(errors='replace'), (i.name.decode() if i.name else '#%d'%i.ordinal))
SLOTS=[0x7e1220,0x7e1224,0x7e1250,0x7e15d8,0x7e15fc,0x7e1600,0x7e1370,0x7e1384]
R['slots']={hex(s):imp.get(s) for s in SLOTS}
# neighbours for anti-collision control
R['neighbours']={hex(s+d):imp.get(s+d) for s in SLOTS for d in (+4,-4)}

def raw(va,n):
    for nm,(lo,hi,s) in secs.items():
        if lo<=va<hi:
            o=va-(base+s.VirtualAddress); d=s.get_data()
            if o<0 or o+n>min(s.SizeOfRawData,len(d)): return None
            return d[o:o+n]
    return None
def cstr(va,limit=96):
    b=raw(va,limit)
    if b is None: return None
    z=b.find(b'\x00')
    return b[:z].decode('latin-1') if z>0 else None

R['str_0x840de4']=cstr(0x840de4)
R['str_0x840de4_ctx']=raw(0x840dd0,64).hex() if raw(0x840dd0,64) else None
R['section_0x840de4']=[nm for nm,(lo,hi,s) in secs.items() if lo<=0x840de4<hi]

def imm_refs(val, width=4):
    pat=struct.pack('<I',val); out=[]; i=data.find(pat)
    while i>=0:
        out.append(tlo+i); i=data.find(pat,i+1)
    return out
R['refs_0x817bc0']=[hex(a) for a in imm_refs(0x817bc0)]
R['refs_0x840de4']=[hex(a) for a in imm_refs(0x840de4)]
R['refs_0x7f3710']=[hex(a) for a in imm_refs(0x7f3710)]
# controls: neighbouring IID-like constants must NOT collide
R['refs_0x817bd0']=[hex(a) for a in imm_refs(0x817bd0)]
print('slots:',json.dumps(R['slots'],indent=1))
print('neighbours:',json.dumps(R['neighbours'],indent=1))
print('str@0x840de4:',R['str_0x840de4'],'section',R['section_0x840de4'])
print('ctx bytes:',R['str_0x840de4_ctx'])
print('refs IID 0x817bc0:',R['refs_0x817bc0'])
print('refs 0x840de4:',R['refs_0x840de4'])
print('refs 0x7f3710:',R['refs_0x7f3710'])
print('refs 0x817bd0(control):',R['refs_0x817bd0'])
json.dump(R,open(OUT,'w'),ensure_ascii=False,indent=1)
