import bisect
import pefile,capstone
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
T=S['.text']; T_LO=T.VirtualAddress+IB
raw=pe.get_data(T.VirtualAddress,T.Misc_VirtualSize)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.skipdata=True
rows=[(a,s,m,o) for a,s,m,o in md.disasm_lite(raw[0x11*0x1000:0x12*0x1000], T_LO+0x11*0x1000)]
sel=[r for r in rows if 0x521150<=r[0]<0x5211b0]
for a,s,m,o in sel: print('%x (+%d): %-8s %s'%(a,s,m,o))
print('--- count of .byte mnemonics in whole text ---')
allrows=[(a,s,m,o) for a,s,m,o in md.disasm_lite(raw,T_LO)]
print(sum(1 for r in allrows if r[2]=='.byte'), len(allrows))
