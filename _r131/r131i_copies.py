#!/usr/bin/env python3
# R131 r131i: is 0x6bedb0 a TEMPLATE that got expanded more than once?
# Take the exact byte string of the wrapper body (0x6bedb0..end at first ret) and search
# .text for byte-identical copies. For each copy, find direct E8 call sites.
# This scopes R130's "only 2 call sites" claim: 2 callers OF THAT COPY, or 2 in the whole binary?
import json, struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
EXE='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT='/home/t628/projects/ra2-campaign-forge/_r131/r131i_copies.json'
pe=pefile.PE(EXE, fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase
secs={}
for s in pe.sections:
    nm=s.Name.rstrip(b'\x00').decode('latin-1')
    secs[nm]=(base+s.VirtualAddress, base+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData), s)
tlo,thi,ts=secs['.text']; data=ts.get_data()
md=Cs(CS_ARCH_X86, CS_MODE_32)

# body extent: from 0x6bedb0 up to and including the first ret 0xc
i0=0x6bedb0-tlo
end=None
for i in md.disasm(data[i0:i0+0x100], 0x6bedb0):
    if i.mnemonic=='ret':
        end=i.address+i.size; break
BODY=data[i0:end-tlo]
R={'body_va':hex(0x6bedb0),'body_end':hex(end),'body_len':len(BODY),'body_sha_hex':__import__('hashlib').sha256(BODY).hexdigest()[:16]}
print('body 0x%x..0x%x len=%d'%(0x6bedb0,end,len(BODY)))

# copy search over .text
hits=[]; k=data.find(BODY)
while k>=0:
    hits.append(tlo+k); k=data.find(BODY,k+1)
R['copies']=[hex(h) for h in hits]
print('byte-identical copies:',R['copies'])

# all direct E8 calls to each copy
def callers(target):
    out=[]
    for p in range(len(data)-5):
        if data[p]==0xe8:
            rel=struct.unpack('<i', data[p+1:p+5])[0]
            if tlo+p+5+rel==target: out.append(tlo+p)
    return out
R['callers']={hex(c):[hex(x) for x in callers(c)] for c in hits}
for c in hits: print('copy 0x%x callers:'%c,[hex(x) for x in callers(c)])

# control: a byte string that must appear exactly once (the loop head imm already known)
ctl=struct.pack('<I',0x7f3710); n=data.count(ctl)
R['control_imm_0x7f3710_count']=n
print('control imm32 0x7f3710 count:',n)
# control 2: a mutated probe -- flip one byte in the middle; must find 0 copies
m=bytearray(BODY); m[len(m)//2]^=0xff
R['mutated_copies']=data.count(bytes(m))
print('mutated probe copies:',R['mutated_copies'])
json.dump(R,open(OUT,'w'),ensure_ascii=False,indent=1)
