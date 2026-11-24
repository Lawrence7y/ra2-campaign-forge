
from pathlib import Path
import pefile,struct,re,csv
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
ROOT=Path(r'D:\Project\ra2-campaign-forge')
EXE=ROOT/'ra2youli/gamemd.exe'; data=EXE.read_bytes(); pe=pefile.PE(str(EXE),fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections: secs.append((IB+s.VirtualAddress,IB+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData),s.PointerToRawData,s.SizeOfRawData,s.Name.rstrip(b'\0').decode('latin1')))
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
targets={0x5B3970:'save?',0x5B3A60:'dtor?',0x5B3A10:'?',0x5B3910:'Find',0x5B3060:'UpdateTimer'}
hits={t:[] for t in targets}
# scan all executable sections linearly
for a,b,r,z,n in secs:
 if not (s if False else False): pass
 if 'EXECUTE' not in '' : pass
 # use section characteristics
for s in pe.sections:
 a=IB+s.VirtualAddress; z=max(s.Misc_VirtualSize,s.SizeOfRawData); r=s.PointerToRawData
 if not (s.Characteristics & 0x20000000): continue
 print('SCAN SECTION',a,a+z)
 code=data[r:r+z]
 # disassemble entire section, skipdata handles gaps
 for it in md.disasm(code,a):
  if it.mnemonic in ('call','jmp') and it.op_str.startswith('0x'):
   t=int(it.op_str,16)
   if t in targets: hits[t].append((it.address,it.mnemonic,it.bytes.hex()))
for t,h in hits.items():
 print('TARGET %08X %s direct_refs=%d'%(t,targets[t],len(h)))
 for x in h[:100]: print('  %08X %s %s'%x)
