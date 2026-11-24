
import sys, json, os
import pefile
from capstone import *
p = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe = pefile.PE(p)
image = pe.OPTIONAL_HEADER.ImageBase
raw = open(p,'rb').read()
def off(va):
    return pe.get_offset_from_rva(va-image)
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True
md.detail = False
entries = sys.argv[1:]
out={}
for s in entries:
    va=int(s,16)
    n=0; insns=[]
    for i in md.disasm(raw[off(va):off(va)+400], va):
        insns.append(f"{i.address:08X} {i.bytes.hex()}  {i.mnemonic} {i.op_str}")
        n+=1
        if i.mnemonic in ('ret','retf') or n>=40: break
    out[s]=insns
print(json.dumps(out,indent=1))
