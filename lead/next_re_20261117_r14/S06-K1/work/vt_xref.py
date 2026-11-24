from pehelp import *
import struct

def find_vtable_xrefs(vt):
    pat = struct.pack('<I', vt)
    return list(find_bytes(pat, section='.text'))

for vt in [0x7e4eec, 0x7ed404, 0x7e4ec0, 0x7e4ec8, 0x7e4ed0]:
    hits = find_vtable_xrefs(vt)
    print(f"vtable {vt:#x}: {len(hits)} .text xrefs -> {[hex(x) for x in hits]}")

print("\nMapClass CHD 0x8054b8:")
chd = 0x8054b8
for i in range(6):
    v = u32(chd+i*4); print(f"  +{i*4:#x}: {v and hex(v)}")
bca = u32(chd+0xc)
print("pBaseClassArray =", hex(bca or 0))
if bca:
    for i in range(6):
        v = u32(bca+i*4); print(f"  base[{i}] = {v and hex(v)}")

print("\nXref context for 0x7e4eec:")
for va in find_vtable_xrefs(0x7e4eec):
    for ins in disasm(max(0x401000, va-6), 12, count=5):
        mark = ' <<<' if ins.address == va else ''
        print("   ", fmt(ins), mark)
    print("   ---")
