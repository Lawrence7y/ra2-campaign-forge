from pehelp import *
import struct
tlo,thi=text_bounds()
def callers(target):
    out=[]
    for va in range(tlo,thi):
        if u8(va)!=0xE8: continue
        b=read(va,5)
        if len(b)<5: continue
        t=va+5+struct.unpack('<i',b[1:5])[0]
        if t==target: out.append(va)
    return out
# trace chain: who calls 0x4a8730, and 0x4e1390
for tgt in [0x4a8730, 0x4e1390]:
    cs=callers(tgt)
    print(f"callers of {tgt:#x}: {[hex(x) for x in cs]}")
    for va in cs:
        print(f"  ctx {va:#x}")
        for ins in disasm(max(tlo,va-30),45,count=14):
            print("    ",fmt(ins))
