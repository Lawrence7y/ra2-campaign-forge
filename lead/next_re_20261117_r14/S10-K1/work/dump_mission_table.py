#!/usr/bin/env python3
"""S10-K1: dump raw bytes around 0x816D00-0x816F00 and find pointer tables referencing mission strings."""
import struct, re
import pefile
EXE=r"ra2youli\gamemd.exe"
pe=pefile.PE(EXE,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
data=open(EXE,'rb').read()
secs=[]
for s in pe.sections:
    secs.append((s.Name.decode(errors='replace').rstrip('\x00'), IB+s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData))
def va2off(va):
    for n,v,vs,r,rs in secs:
        if v<=va<v+max(vs,rs): return r+(va-v)
    return None
def off2va(o):
    for n,v,vs,r,rs in secs:
        if r<=o<r+rs: return v+(o-r)
    return None

lo,hi=0x816D00,0x816F00
o0,o1=va2off(lo),va2off(hi)
blob=data[o0:o1]
print("=== raw hex %08X..%08X ===" % (lo,hi))
for i in range(0,len(blob),16):
    chunk=blob[i:i+16]
    hexs=' '.join('%02X'%b for b in chunk)
    asc=''.join(chr(b) if 32<=b<127 else '.' for b in chunk)
    print("%08X  %-47s  %s" % (lo+i, hexs, asc))

# Find all 4-byte little-endian values in the whole file that equal one of the mission string VAs
mission_strings=[]
for va in range(0x816DCC,0x816E80):
    off=va2off(va)
    if off is None: continue
    # check it's start of a null-terminated string
    if data[off-1]==0 and 32<=data[off]<127:
        end=off
        while end<len(data) and data[end]!=0: end+=1
        s=data[off:end].decode('ascii',errors='replace')
        if s and len(s)<30:
            mission_strings.append((va,s))
print("\n=== identified null-terminated strings in 0x816DCC..0x816E80 ===")
for va,s in mission_strings: print("  0x%08X: %r"%(va,s))

# search whole data for pointers to those VAs
print("\n=== xrefs (4-byte LE pointers) to mission strings ===")
for va,s in mission_strings:
    needle=struct.pack('<I',va)
    positions=[]
    start=0
    while True:
        idx=data.find(needle,start)
        if idx<0: break
        positions.append(idx); start=idx+1
    if positions:
        vas=[hex(off2va(p) or 0) for p in positions]
        print("  '%s'(0x%X): %d ptrs @ %s"%(s,va,len(positions),', '.join(vas)))
