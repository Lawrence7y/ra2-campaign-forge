from pehelp import *
import struct
tlo,thi=text_bounds()
def callers(target):
    out=[]
    for va in range(tlo,thi):
        if u8(va)!=0xE8: continue
        b=read(va,5)
        if len(b)==5 and va+5+struct.unpack('<i',b[1:5])[0]==target: out.append(va)
    return out
for tgt in [0x652960]:
    for va in callers(tgt):
        print(f"caller {va:#x}:")
        for ins in disasm(max(tlo,va-24),30,count=12):
            print("   ",fmt(ins))
