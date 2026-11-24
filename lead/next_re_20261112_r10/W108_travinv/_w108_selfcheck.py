import struct
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
d=open(EXE,"rb").read(); BASE=0x400000
def off(va): return va-BASE
def i32(va): return struct.unpack_from("<i",d,off(va))[0]
def scan_e8(target):
    hits=[]
    txt_va=0x401000; txt_rp=0x1000; n=0x3DF38D
    for i in range(n-5):
        if d[txt_rp+i]==0xE8:
            rel=struct.unpack_from("<i",d,txt_rp+i+1)[0]
            va=BASE+txt_va+i
            if va+5+rel==target: hits.append(va)
    return hits

print("=== Does the unlink caller 0x005687F0 also call any traverser? ===")
F=0x005687F0
for t,name in ((0x47C520,"TRAV_520"),(0x47C4D0,"TRAV_4D0"),(0x47C550,"TRAV_550")):
    hs=[a for a in scan_e8(t) if F <= a < F+0x600]
    print("  %-10s call sites inside 0x005687F0 body: %s" % (name, hs if hs else "NONE"))
print()
print("=== Full call inventory inside 0x005687F0 (E8/E9 rel32) ===")
print("(Ghidra says this function spans 0x005687F0 .. ~0x00568B5x; decompile showed 3 calls)")
for i in range(0, 0x600):
    va=F+i
    op=d[off(va)]
    if op in (0xE8,0xE9):
        rel=i32(va+1); tgt=va+5+rel
        print("  0x%08X %s -> 0x%08X" % (va, "call" if op==0xE8 else "jmp ", tgt))
