"""S09-F1 recon 09: final verification - vtables, sidebar layout, event ring, dispatcher."""
import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09-F1\work")
from s09lib import *

b = Bin(); atlas = Atlas()
calls, jmps, nins = sweep_calls(b)

print("=== vtable verification ===")
for vt,label,slots in [(0x7F3058,"SidebarClass",[16,33,34,50,53]),
                        (0x7F2FCC,"SelectClass@Strip",[31]),
                        (0x7E6114,"DisplayClass",[45,47,48]),
                        (0x7EBE3C,"CommandClass",[8]),
                        (0x7E182C,"CommandClass::Array?",[0])]:
    print("\n%s vtable %08X:"%(label,vt))
    for s in slots:
        print("  v[%d] @%08X = %08X"%(s,vt+s*4,b.u32(vt+s*4)))

print("\n=== GetTechnoType 0x48DCD0 callers (sample) ===")
print(" count=%d"%len(calls.get(0x48DCD0,[])))
for s in calls.get(0x48DCD0,[])[:12]:
    i=atlas.contains(s); print("  %08X in %s"%(s,"%08X+%d"%(i[0],i[1]) if i else "HOLE"))

print("\n=== 0x48DCD0 dump ===")
print(dump(b, 0x48DCD0, 0x90))

print("\n=== 0x4C6CB0 Dispatcher + jump table 0x4C8114 ===")
print(dump(b, 0x4C6CB0, 0x100))
for i in range(12):
    print("  jt[%d] @4C8114+%d = %08X"%(i,i*4,b.u32(0x4C8114+i*4)))

print("\n=== Event ring globals refs ===")
for g in (0xA802C8,0xA802D0,0xA802D4,0xA83A54,0xB0CEC8):
    found=sweep_disps(b,g)
    print("  %08X: %d refs"%(g,len(found)))
    for f in found[:6]: print("     %08X %s"%(f["va"],f["insn"]))

print("\n=== 0x6A9540 (Cameo draw) first 0xA0 ===")
print(dump(b, 0x6A9540, 0xA0))
print("\n=== 0x6A6C30 (Sidebar Draw) first 0x80 ===")
print(dump(b, 0x6A6C30, 0x80))
