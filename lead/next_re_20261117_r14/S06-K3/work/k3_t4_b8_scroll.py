"""Dump contexts: ore +0xB8 writes, table init 0x721640, scroll-origin writers' function entries."""
from lib import *
import bisect, struct
asrt=sorted(atlas.items()); keys=[k for k,v in asrt]
def func_of(a):
    i=bisect.bisect_right(keys,a)-1
    if i>=0:
        e,sz=asrt[i]
        if e<=a<e+sz: return (e,sz)
    return None

for s in [0x482F14,0x48E804,0x48F980,0x721713,0x721B0C]:
    print(f"\n=== +0xB8 write {s:#x} func={func_of(s)} ===")
    lo=s-0x30
    for ins in disasm(lo,(s-lo)+0x18):
        if ins.id==0: continue
        m='<<<' if ins.address==s else ''
        print(f"  {ins.address:08X}: {ins.mnemonic} {ins.op_str} {m}")

print("\n\n=== table init 0x721640 .. 0x721760 ===")
for ins in disasm(0x721640,0x120):
    if ins.id==0: continue
    print(f"  {ins.address:08X}: {ins.bytes.hex():<16} {ins.mnemonic} {ins.op_str}")

print("\n\n=== scroll origin writers function entries ===")
for s in [0x40DA2C,0x40DA31,0x4A8987,0x4A8990]:
    f=func_of(s)
    print(f"  writer {s:#x} in func {f and (hex(f[0]),f[1])}")
    # entry first 12 insns
    if f:
        for ins in disasm(f[0],0x40,12):
            if ins.id==0: continue
            print(f"      {ins.address:08X}: {ins.mnemonic} {ins.op_str}")
