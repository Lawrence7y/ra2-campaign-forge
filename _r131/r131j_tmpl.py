#!/usr/bin/env python3
# R131 r131j: is 0x6bedb0 a template instantiated inline at several sites?
# Dump the three candidate inline instantiations and compute the longest common prefix
# with 0x6bedb0. Also dump the canonical QI-then-Release tail at 0x437f74 and 0x67e5da.
import json
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
EXE='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT='/home/t628/projects/ra2-campaign-forge/_r131/r131j_tmpl.json'
pe=pefile.PE(EXE, fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase
ts=[s for s in pe.sections if s.Name.rstrip(b'\x00')==b'.text'][0]
tlo=base+ts.VirtualAddress; data=ts.get_data()
md=Cs(CS_ARCH_X86, CS_MODE_32)
def dump(va,n):
    o=va-tlo; out=[]
    for i in md.disasm(data[o:o+n], va):
        out.append('%08x %-20s %-9s %s'%(i.address,i.bytes.hex(),i.mnemonic,i.op_str))
    return out
R={}
for name,va,n in [('A_0x6bedb0',0x6bedb0,0x80),('B_0x41c250',0x41c250,0x80),
                  ('C_0x437f50',0x437f50,0x90),('D_0x67e5a2',0x67e5a2,0x90),
                  ('E_0x517b48',0x517b48,0x80),('F_0x67d0be',0x67d0be,0x70)]:
    R[name]=dump(va,n)
    print('===== %s ====='%name)
    for l in R[name]: print('  '+l)

# longest common prefix of bytes between A and B
a=data[0x6bedb0-tlo:0x6bedb0-tlo+0x100]; b=data[0x41c250-tlo:0x41c250-tlo+0x100]
n=0
while n<min(len(a),len(b)) and a[n]==b[n]: n+=1
R['lcp_A_B']=n
print('LCP bytes A(0x6bedb0) vs B(0x41c250):',n, '-> A diverges at 0x%x, B at 0x%x'%(0x6bedb0+n,0x41c250+n))
# same for A vs E
e=data[0x517b48-tlo:0x517b48-tlo+0x100]
n2=0
while n2<min(len(a),len(e)) and a[n2]==e[n2]: n2+=1
R['lcp_A_E']=n2
print('LCP A vs E(0x517b48):',n2)
json.dump(R,open(OUT,'w'),ensure_ascii=False,indent=1)
