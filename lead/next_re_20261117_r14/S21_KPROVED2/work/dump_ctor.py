import os,json,struct
import pefile,capstone
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
OUT=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S21_KPROVED2'
pe=pefile.PE(EXE,fast_load=False); blob=open(EXE,'rb').read(); ib=pe.OPTIONAL_HEADER.ImageBase
t=[s for s in pe.sections if s.Name.rstrip(b'\0')==b'.text'][0]; base=ib+t.VirtualAddress; code=t.get_data()[:t.Misc_VirtualSize]
cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); cs.skipdata=True; cs.detail=False
by={i.address:(i.size,i.mnemonic,i.op_str,bytes(i.bytes).hex()) for i in cs.disasm(code,base)}
sel=['0046D000','0046D090','005C5850','00765600']
with open(os.path.join(OUT,'EVIDENCE','ctor_candidate_bodies.txt'),'w',encoding='utf-8') as f:
 for e in sel:
  a=int(e,16); f.write('\n### '+e+'\n')
  for _ in range(140):
   z=by.get(a)
   if not z: break
   s,m,o,b=z; f.write(f'{a:08X} +{a-int(e,16):04X} {b:<20} {m} {o}\n'); a+=s
print(open(os.path.join(OUT,'EVIDENCE','ctor_candidate_bodies.txt'),encoding='utf-8').read())
