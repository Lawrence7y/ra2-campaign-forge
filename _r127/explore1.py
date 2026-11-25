import os,struct,collections
import pefile,capstone
EXE='ra2bench/gamemd.exe'
pe=pefile.PE(EXE); IB=pe.OPTIONAL_HEADER.ImageBase
secs={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
T=secs['.text']; T_LO=T.VirtualAddress+IB
raw=pe.get_data(T.VirtualAddress,T.Misc_VirtualSize)
def find_push(va):
    pat=b'\x68'+struct.pack('<I',va)
    out=[];st=0
    while True:
        k=raw.find(pat,st)
        if k<0:break
        out.append(T_LO+k); st=k+1
    return out
for va in (0x7f7c70,0x818858,0x7f7c80,0x820270,0x7f7c90,0x817bc0):
    print(hex(va), [hex(x) for x in find_push(va)])
