#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""0x47C3D0 entry prologue: verify selector stack arg [ebp+0xC] trace to pushed ebp=0."""
import pefile, capstone, hashlib
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W177_KA\EVIDENCE\ka_47c3d0_prologue.txt"
pe=pefile.PE(EXE); IB=pe.OPTIONAL_HEADER.ImageBase
sec=[s for s in pe.sections if IB+s.VirtualAddress<=0x47C3D0<IB+s.VirtualAddress+s.Misc_VirtualSize][0]
base=IB+sec.VirtualAddress; off=sec.PointerToRawData+(0x47C3D0-base)
data=open(EXE,'rb').read()[off:off+0x100]
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.skipdata=True
P=['EXE SHA256='+hashlib.sha256(open(EXE,'rb').read()).hexdigest().upper()]
for ins in md.disasm(data,0x47C3D0):
    P.append('  0x%08X  %-24s %s %s'%(ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str))
open(OUT,'w',encoding='utf-8').write('\n'.join(P)+'\n')
print('\n'.join(P)); print('saved',OUT)
