import struct, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
EXE=r"ra2youli\gamemd.exe"
pe=pefile.PE(EXE,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
d=open(EXE,"rb").read()
secs=[(s.Name.decode(errors="replace").rstrip("\x00"),IB+s.VirtualAddress,s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData) for s in pe.sections]
def v2o(v):
 for n,va,vs,r,rs in secs:
  if va<=v<va+max(vs,rs): return r+(v-va)
def rd(v): return struct.unpack_from("<I",d,v2o(v))[0]
lo,hi=0x816CAC,0x816D2C
n_enum=(hi-lo)//4
print("CORE1 enum count = %d  prior=0x%X byte@hi=0x%02X(%s)"%(n_enum,rd(lo-4),d[v2o(hi)],chr(d[v2o(hi)])))
fields=[0xAC,0xB0,0xB4,0xB8,0xBC,0xC0,0xC4,0xC8,0xCC,0xD0,0x6C]
print("CORE2 field count = %d"%len(fields))
tab=0x5B34E8; n_disp=0
for i in range(64):
 if rd(tab+4*i)==0x90909090: break
 n_disp+=1
print("CORE3 dispatch @0x%X count=%d sentinel@+0xX=0x%08X"%(tab,n_disp,rd(tab+4*n_disp)))
vts=[0x7EDCC0,0x7F0508,0x7F4960,0x7E8C94,0x7EB058,0x7E22A4,0x7E3EBC]
impl=set()
for b in vts:
 for s in range(129,157):
  a=rd(b+4*s)
  if not (0x5B2E10<=a<0x5B2FD0): impl.add(a)
print("CORE4 non-stub mission handlers = %d"%len(impl))
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
o=v2o(0x5B3060); found=None
for ins in md.disasm(d[o:o+0x500],0x5B3060):
 if ins.mnemonic=="jmp" and "0x5b34e8" in ins.op_str.lower(): found=ins.address; break
print("CORE5 dispatch point @0x%X"%found)
import re
