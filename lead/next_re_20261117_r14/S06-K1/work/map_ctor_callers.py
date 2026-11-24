from pehelp import *
import struct
# E8 rel32 callers of 0x565090
target=0x565090
pat=bytearray()
rel=target-(0x401000+5)
# easier: scan all E8 in .text, compute target
callers=[]
tlo,thi=text_bounds()
for va in range(tlo, thi):
    if u8(va)!=0xE8: continue
    b=read(va,5)
    if len(b)<5: continue
    t=va+5+struct.unpack('<i',b[1:5])[0]
    if t==target: callers.append(va)
print("callers of ctor 0x565090:", [hex(x) for x in callers])
for va in callers:
    print(f"--- context {va:#x} ---")
    for ins in disasm(max(tlo,va-40), 60, count=20):
        mark=' <<<' if ins.address==va else ''
        print("   ",fmt(ins),mark)
