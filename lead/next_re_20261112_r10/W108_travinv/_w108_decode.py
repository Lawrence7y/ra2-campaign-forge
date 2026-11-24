import struct
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
d=open(EXE,"rb").read()
BASE=0x400000
def off(va): return va-BASE
def b(va,n=16): return " ".join("%02X"%x for x in d[off(va):off(va)+n])
def i32(va): return struct.unpack_from("<i",d,off(va))[0]
print("=== 0x005688C0 .. 0x00568900 raw ===")
print(b(0x005688C0,0x40))
print()
print("=== decode window 0x005688E4..0x005688F0 ===")
for va in (0x005688E0,0x005688E4,0x005688EA,0x005688EB,0x005688EC):
    print("0x%08X: %s"%(va,b(va,8)))
print()
tgt = 0x005688EB+5+i32(0x005688EB+1)
print("E8 at 0x005688EB -> rel=0x%08X -> target 0x%08X"%(i32(0x005688EB+1)&0xFFFFFFFF,tgt))
print()
print("=== operator bytes of the 4 functions (head) ===")
for va,n,label in ((0x0047C520,0x30,"TRAV_520"),(0x0047C4D0,0x48,"TRAV_4D0"),
                   (0x0047C550,0x38,"TRAV_550"),(0x0047EA90,0x40,"UNLINK")):
    print("%-10s 0x%08X: %s"%(label,va,b(va,n)))
