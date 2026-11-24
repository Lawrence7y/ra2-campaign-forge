#!/usr/bin/env python3
"""S10-K1: disassemble candidate Mission_* handlers."""
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
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
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True

funcs={
 'Foot.Attack(v132)':0x4D4DC0,'Foot.Move(v139)':0x4D4200,'Foot.Guard(v135)':0x4D5070,
 'Foot.AreaGuard(v136)':0x4D6AA0,'Foot.Hunt(v138)':0x4D5350,'Foot.Retreat(v140)':0x4DA2C0,
 'Foot.Enter(v144)':0x4D9290,'Foot.Capture(v133)':0x4D4B20,'Foot.Eaten(v134)':0x4D4CB0,
 'Foot.Unload(v143)':0x4DA2B0,'Foot.Rescue(v150)':0x4DDF90,'Foot.Patrol(v151)':0x4D4280,
 'Inf.Attack':0x51F3E0,'Inf.Guard':0x51F620,'Inf.AreaGuard':0x51F640,'Inf.Harvest':0x522E70,
 'Air.Attack':0x417FE0,'Air.Guard':0x41A5C0,
 'Bld.Attack':0x44ACF0,'Bld.Harvest':0x44B770,
}
for name,a in funcs.items():
    oo=va2off(a)
    print("\n=== %s @ 0x%08X ==="%(name,a))
    for ins in md.disasm(data[oo:oo+0xA0],a):
        print("  0x%08X: %-24s %s %s"%(ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str))
        if ins.mnemonic.startswith('ret'): break
