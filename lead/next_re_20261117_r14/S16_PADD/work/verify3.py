import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S16_PADD\work")
import re_lib as R

# 1. Are the "4 globals" real vtables (RTTI at vt-4)?
for base in [0x7E9580, 0x7E9570, 0x7F4090, 0x7F4074, 0x7F406C, 0x7F4064, 0x7F3FE8, 0x7F3FCC, 0x7F3FC4, 0x7F3FBC]:
    info = R.rtti_of_vtable(base)
    print("vt %s -> %s" % (hex(base), info))

# 2. Find all atexit registrations: push <fn>; call 0x7C978A
data = R.all_bytes()
def off_to_va(off):
    for s in R.pe().sections:
        if s.PointerToRawData <= off < s.PointerToRawData + s.SizeOfRawData:
            return R.IMAGE_BASE + s.VirtualAddress + (off - s.PointerToRawData)
    return None
# pattern: E8 rel32 to 0x7C978A
regcall = b"\xe8"
target = 0x7C978A
regsites=[]
for i in range(len(data)-5):
    if data[i]==0xE8:
        rel=struct.unpack("<i",data[i+1:i+5])[0]
        va=off_to_va(i)
        if va is None: continue
        if va+5+rel==target:
            # look back up to 12 bytes for a push imm32 (68 imm32)
            prev=data[max(0,i-12):i]
            regsites.append((va,prev.hex()))
print("\natexit call sites:", len(regsites))
for va,prev in regsites[:60]:
    print("  %08X prev=%s" % (va,prev))
