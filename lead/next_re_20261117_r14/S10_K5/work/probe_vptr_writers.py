#!/usr/bin/env python3
"""Locate constructors writing the RTTI main vtables of S10 dtor candidates."""
import struct
from re_lib import *
VPTRS={0x004E0170:0x007E8C94,0x00523350:0x007EB058,0x005B3A60:0x007EDCC0,0x006B1390:0x007F31C8,0x006B8140:0x007F3650,0x00746E80:0x007F5C70}
for func,vp in VPTRS.items():
    pat=struct.pack('<I',vp)
    print('\n===== FUNC 0x%08X VPTR 0x%08X ====='%(func,vp))
    n=0
    for s in PE.sections:
        if not (s.Characteristics & 0x20): continue
        base=PE.OPTIONAL_HEADER.ImageBase+s.VirtualAddress
        nbytes=min(s.SizeOfRawData,s.Misc_VirtualSize or s.SizeOfRawData)
        data=read(base,nbytes)
        start=0
        while True:
            j=data.find(pat,start)
            if j<0: break
            va=base+j; start=j+1; n+=1
            # try instruction starts 0..7 bytes before immediate
            found=None
            for back in range(0,8):
                st=va-4-back
                try: ins=list(MD.disasm(read(st,16),st,count=1))[0]
                except Exception: continue
                if ins.id==0 or ins.mnemonic.startswith('.'): continue
                for op in ins.operands:
                    if op.type==X86_OP_IMM and op.imm==vp:
                        found=(st,fmt_insn(ins)); break
                if found: break
            print('  vptr-bytes@0x%08X %s'%(va,found[1] if found else 'no decoded immediate'))
            # context from 4 bytes before immediate
            print('  ctx '+read(max(0,va-12),28).hex(' '))
    if n==0: print('  NO_CODE_OCCURRENCE')
