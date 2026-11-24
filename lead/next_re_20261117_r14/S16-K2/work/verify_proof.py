#!/usr/bin/env python3
"""S16-K2: verify string constants + dump candidate [已证] upgrade targets."""
import sys, struct, bisect
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S16-K2\work")
import re_lib as R
b=R.Bin()
MD=R.md(skipdata=True)

print("=== STRING CONSTANT VERIFICATION ===")
for va in (0x828034,0x82809c,0x8280b8,0x8216a8,0x83b828):
    print(f"[{va:08X}] '{R.cstr(b,va,120)}'")

print("\n=== vtable slot context (SuperClass 0x7F3FE8, SWType 0x7F4090) ===")
for base,label in ((0x7F3FE8,"SuperClass"),(0x7F4090,"SuperWeaponTypeClass")):
    print(f"-- {label} vftable @ {base:08X} (COL {b.u32(base-4):08X}) --")
    for k in range(0,24):
        v=b.u32(base+4*k)
        if not (0x400000<=v<0xC00000): break
        print(f"  v[{k:2d}] @{base+4*k:08X} = {v:08X}")

print("\n=== CANDIDATE [已证] UPGRADE TARGETS (full bytes) ===")
CAND = [
 (0x6CDFD0,"SuperClass::slot6 -> SuperClass::Save (v[6], forwarder to 0x410320 AbstractClass::Save)"),
 (0x6CE220,"SuperClass::slot8 -> ~SuperClass scalar deleting dtor (v[8])"),
 (0x6CE240,"0x6CE240 3-vector add"),
 (0x6CE270,"0x6CE270 virtual slot1 call"),
 (0x6CE280,"0x6CE280 timer countdown"),
 (0x6CE2C0,"0x6CE2C0 timer start"),
 (0x6CE2D0,"0x6CE2D0 vector remove by vslot4"),
 (0x6CE320,"0x6CE320 vector remove by index"),
 (0x53DD50,"T_DynVector_IonBlast slot0"),
 (0x53DAA0,"shared slot1"),
 (0x53DA90,"shared slot6"),
]
arows,hdr=R.load_atlas()
atlas=sorted([(va,sz) for va,sz,_ in arows]); keys=[x[0] for x in atlas]
def extent(va):
    i=bisect.bisect_right(keys,va)-1
    return (atlas[i][0],atlas[i][1]) if i>=0 and va<atlas[i][0]+atlas[i][1] else (va,0x80)
for va,desc in CAND:
    st,sz=extent(va)
    print(f"\n--- {va:08X}  {desc}  extent {st:08X}+{sz:#x} ---")
    for ins in R.disasm_range(b,va,st+sz,skipdata=True):
        print("   ",R.fmt(ins))

print("\n=== 0x734e60 / 0x5d3ba0 call-site context (message dispatch) ===")
# show what 0x734e60 is: dump first bytes
for va in (0x734e60,0x5d3ba0):
    print(f"-- {va:08X} --")
    for ins in R.disasm_range(b,va,va+0x40,skipdata=True)[:12]:
        print("   ",R.fmt(ins))
