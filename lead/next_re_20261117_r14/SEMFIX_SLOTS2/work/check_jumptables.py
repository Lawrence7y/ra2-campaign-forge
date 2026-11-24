#!/usr/bin/env python3
# Dump the three S10 jump tables to prove dispatched targets are distinct .text
# addresses (NOT the 004DDDE0 "many guards -> one stub" pattern).
import pefile, struct
T=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IB=0x400000
pe=pefile.PE(T); data=open(T,'rb').read()
def off(rva):
    for s in pe.sections:
        vs=max(s.Misc_VirtualSize,s.SizeOfRawData)
        if s.VirtualAddress<=rva<s.VirtualAddress+vs:
            return s.PointerToRawData+(rva-s.VirtualAddress)
    raise ValueError(hex(rva))
def rd(va,n):
    o=off(va-IB); return data[o:o+n]

print("=== 00702D40 : byte-map @0x703214 (idx 0..14) -> dword-table @0x703200 ===")
seen=[]
for i in range(15):
    b=rd(0x703214+i,1)[0]
    t=struct.unpack('<I',rd(0x703200+b*4,4))[0]
    seen.append(t)
    print("  eax=%2d -> cl=0x%02X -> target=0x%08X"%(i,b,t))
print("  distinct targets:",len(set(seen)),"; all in .text[0x401000,0x7e1000):",all(0x401000<=x<0x7e1000 for x in seen))

print("=== 00706640 : dword-table @0x706bb8 (idx 0..4) ===")
seen=[]
for i in range(5):
    t=struct.unpack('<I',rd(0x706bb8+i*4,4))[0]
    seen.append(t); print("  eax=%d -> target=0x%08X"%(i,t))
print("  distinct targets:",len(set(seen)))

print("=== 00708C30 : dword-table @0x708d54 (idx 0..4) ===")
seen=[]
for i in range(5):
    t=struct.unpack('<I',rd(0x708d54+i*4,4))[0]
    seen.append(t); print("  eax=%d -> target=0x%08X"%(i,t))
print("  distinct targets:",len(set(seen)))
