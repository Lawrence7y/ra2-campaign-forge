from pehelp import *
import struct
tlo,thi=text_bounds()
# find calls to 0x4a8730 (DisplayClass ctor) and check ecx source
def callers(target):
    out=[]
    for va in range(tlo,thi):
        if u8(va)!=0xE8: continue
        b=read(va,5)
        if len(b)<5: continue
        t=va+5+struct.unpack('<i',b[1:5])[0]
        if t==target: out.append(va)
    return out
for tgt in [0x4a8730, 0x565090]:
    cs=callers(tgt)
    print(f"callers {tgt:#x}: {[hex(x) for x in cs]}")
    for va in cs:
        print(f" context {va:#x}:")
        for ins in disasm(max(tlo,va-20),30,count=10):
            print("   ",fmt(ins))
# search immediate store to [0x87f7e8]
pat=struct.pack('<I',0x87f7e8)
print("\nraw dword xrefs to 0x87f7e8 in .text (first 20):")
xs=list(find_bytes(pat,section='.text'))
print([hex(x) for x in xs[:20]], "count", len(xs))
