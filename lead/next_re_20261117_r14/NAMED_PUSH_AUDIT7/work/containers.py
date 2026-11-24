"""AUDIT7: resolve global container objects -> vtable -> Find slot (+0x10) -> -1 sentinel."""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT7\work")
from core import *
import fast

CONTAINERS = {
    0x00A83DC8: 'ParticleClass registry (0062D9A0)',
    0x00A83D68: 'ParticleSystemTypeClass registry (00644960)',
    0x00B0F670: 'shared type registry (00645950/0074BA30)',
    0x00A83D98: 'ParticleTypeClass 2nd registry (00645950)',
    0x00A8EB28: 'VoxelAnimTypeClass 2nd registry (0074BA30)',
}

for addr, tag in CONTAINERS.items():
    vt = u32(addr)
    print(f"\n=== container {addr:08X} {tag}")
    print(f"  [container] = {vt and hex(vt)}")
    if not vt or not (0x7E0000 <= vt <= 0x900000):
        print("  !! not a vtable-looking pointer")
        continue
    r = rtti_of_vtable(vt)
    print(f"  container vtable {vt:08X} RTTI col={r['col'] and hex(r['col'])} td={r['td'] and hex(r['td'])} name={r['name']!r}")
    find = u32(vt + 0x10)
    print(f"  vt[+0x10] (Find) = {find and hex(find)}")
    if find and in_text(find):
        b = fast.body(find, limit=200)
        print(f"  Find body {find:08X}..{b[-1][0]:08X} n={len(b)}")
        for a, mn, opstr, bh, imms in b:
            print(f"     {a:08X}  {bh:<22} {mn} {opstr}")
