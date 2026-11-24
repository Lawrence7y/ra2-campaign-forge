import struct
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
d=open(EXE,"rb").read(); BASE=0x400000
def off(va): return va-BASE
def by(va,n=16): return " ".join("%02X"%x for x in d[off(va):off(va)+n])
def i32(va): return struct.unpack_from("<i",d,off(va))[0]
def i8(va):  return struct.unpack_from("<b",d,off(va))[0]

print("=== Region A: loop head 0x0056884F .. 0x00568870 (cell fetch + NULL test) ===")
print("0x0056884F: "+by(0x0056884F,0x22))
print()
print("=== Region B: the 'cell not null' branch -> unlink -> re-read  (0x005688C0..0x00568920) ===")
print("0x005688C0: "+by(0x005688C0,0x60))
print()
print("=== decode the cached-entry question ===")
print("At 0x005688B2/Ghidra `iVar7 = *(int*)(*(int*)(iVar2+0x13c) + iVar10*4)`:")
print("0x005688A0: "+by(0x005688A0,0x24))
print()
print("After the unlink call 0x005688EB, Ghidra shows:")
print("  0x005688F1: 85 F6            test esi,esi")
print("  0x005688F3: 7C 2E            jl   +0x2e")
print("  0x005688F5: 81 FE 00 00 04 00 cmp  esi,0x40000")
print("  0x005688FB: 7D 26            jge  +0x26")
print("  0x005688FD: 8B 44 24 18      mov  eax,[esp+0x18]")
print("  0x00568901: 8B 88 3C 01 00 00 mov ecx,[eax+0x13c]")
print("  0x00568907: 8B 34 B1         mov  esi,[ecx+esi*4]   <== RE-READ cell table, not a cached node")
print()
print("0x005688F1: "+by(0x005688F1,0x20))
print()
print("=== the loop's iteration tail / where the next cell coordinate comes from ===")
print("0x00568862 (loop head target of the two back-jmps): "+by(0x00568862,0x1A))
