#!/usr/bin/env python3
# R131 r131l: read the GUID constants used by the two template instantiations and by the
# surrounding CoCreateInstance sites; print canonical string + section + raw hex.
import json, struct
import pefile
EXE='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT='/home/t628/projects/ra2-campaign-forge/_r131/r131l_guids.json'
pe=pefile.PE(EXE, fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase
secs={}
for s in pe.sections:
    nm=s.Name.rstrip(b'\x00').decode('latin-1')
    secs[nm]=(base+s.VirtualAddress, base+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData), s)
def raw(va,n=16):
    for nm,(lo,hi,s) in secs.items():
        if lo<=va<hi:
            o=va-(base+s.VirtualAddress); d=s.get_data()
            if o<0 or o+n>min(s.SizeOfRawData,len(d)): return None,nm
            return d[o:o+n],nm
    return None,None
def canon(va):
    g,nm=raw(va)
    if g is None: return {'va':hex(va),'section':nm,'raw':None}
    d1,d2,d3=struct.unpack('<IHH',g[:8])
    return {'va':hex(va),'section':nm,'raw':g.hex(),
            'str':'{%08X-%04X-%04X-%s-%s}'%(d1,d2,d3,g[8:10].hex().upper(),g[10:].hex().upper())}
IUNK=bytes.fromhex('0000000000000000c000000000000046')
ICF =bytes.fromhex('0100000000000000c000000000000046')
IPS =bytes.fromhex('0000000100000000C000000000000046')  # IPersist {0000010C-...}? placeholder
VAS=[0x817ba0,0x817bb0,0x817bc0,0x817bd0,0x818c08,0x83d598,0x7e9500,0x7e9540]
R={}
print('%-12s %-9s %-40s %s'%('va','section','canonical','match'))
for va in VAS:
    c=canon(va); rawb,_=raw(va)
    c['is_IUnknown']= rawb==IUNK if rawb else None
    c['is_IClassFactory']= rawb==ICF if rawb else None
    R[hex(va)]=c
    m='IUnknown' if c.get('is_IUnknown') else ('IClassFactory' if c.get('is_IClassFactory') else '')
    print('%-12s %-9s %-40s %s'%(c['va'],c.get('section'),c.get('str'),m))
    print('     raw=%s'%c.get('raw'))
# byte diff between the two instantiations over the 106-byte body
ts=[s for s in pe.sections if s.Name.rstrip(b'\x00')==b'.text'][0]
tlo=base+ts.VirtualAddress; data=ts.get_data()
A=data[0x6bedb0-tlo:0x6bedb0-tlo+106]; B=data[0x41c250-tlo:0x41c250-tlo+106]
diff=[i for i in range(106) if A[i]!=B[i]]
R['body_diff_offsets']=diff
R['body_diff_bytes']=[(i,'%02x'%A[i],'%02x'%B[i]) for i in diff]
print('byte diff offsets between 0x6bedb0 and 0x41c250 (106-byte body):',diff)
json.dump(R,open(OUT,'w'),ensure_ascii=False,indent=1)
