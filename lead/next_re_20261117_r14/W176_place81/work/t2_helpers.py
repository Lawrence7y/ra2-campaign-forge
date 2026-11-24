import capstone, pefile, os
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W176_place81\EVIDENCE"
pe = pefile.PE(EXE, fast_load=True)
ib = pe.OPTIONAL_HEADER.ImageBase
def read(va,n):
    for s in pe.sections:
        v=ib+s.VirtualAddress
        if v<=va and va+n<=v+s.SizeOfRawData:
            off=s.PointerToRawData+(va-v); return pe.__data__[off:off+n]
    raise ValueError(hex(va))
m=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); m.detail=True; m.skipdata=True
for target,n,fn in [(0x5678E0,0x200,'T2_callee_5678E0.txt'),(0x5683C0,0x200,'T2_callee_5683C0_head.txt'),(0x47E8A0,0x100,'T2_callee_47E8A0_head.txt')]:
    lines=['disasm %08X first %d bytes skipdata=True'%(target,n)]
    for ins in m.disasm(read(target,n),target):
        if ins.id!=0: lines.append('  %08X %-9s %s'%(ins.address,ins.mnemonic,ins.op_str))
    open(os.path.join(OUT,fn),'w',encoding='utf-8').write('\n'.join(lines)+'\n')
    print('wrote',fn)
