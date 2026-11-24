import os,struct,pefile
from capstone import *
from capstone.x86 import *
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
OUT=r'D:\Project\ra2-campaign-forge\_ghidra\S08-KPROVED2\EVIDENCE'
pe=pefile.PE(EXE); base=pe.OPTIONAL_HEADER.ImageBase; buf=open(EXE,'rb').read()
def off(va):
 for s in pe.sections:
  v=base+s.VirtualAddress
  if v<=va<v+max(s.Misc_VirtualSize,s.SizeOfRawData): return s.PointerToRawData+va-v
 return None
def read(va,n):
 o=off(va); return b'' if o is None else buf[o:o+n]
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True
text=next(s for s in pe.sections if s.Name.rstrip(b'\x00').decode()=='.text')
TVA=base+text.VirtualAddress; TSZ=text.Misc_VirtualSize
ins=list(md.disasm(read(TVA,TSZ),TVA,TSZ))
vts=[0x7E44F4,0x7E4514,0x7E8B38,0x7E1964]
with open(os.path.join(OUT,'VT_BROAD.tsv'),'w',encoding='utf-8') as f, open(os.path.join(OUT,'VT_BROAD_CONTEXT.txt'),'w',encoding='utf-8') as g:
 f.write('vt\tsite\tinsn\top_types\n')
 for vt in vts:
  hits=[]
  for i in ins:
   for op in i.operands:
    if op.type==X86_OP_IMM and op.imm==vt:
     hits.append(i); break
  for i in hits:
   f.write(f'{vt:08X}\t{i.address:08X}\t{i.mnemonic} {i.op_str}\t{",".join(str(op.type) for op in i.operands)}\n')
  g.write(f'\n===== VT {vt:08X} hits={len(hits)} =====\n')
  for i in hits:
   g.write(f'--- site {i.address:08X}: {i.mnemonic} {i.op_str}\n')
   idx=next(k for k,x in enumerate(ins) if x.address==i.address)
   for j in range(max(0,idx-24),min(len(ins),idx+24)):
    x=ins[j]; mark='>>' if j==idx else '  '
    g.write(f'{mark} {x.address:08X}  {x.bytes.hex():<16}  {x.mnemonic:<8} {x.op_str}\n')
 # raw byte hits in text
 g.write('\n===== RAW BYTE HITS IN .text =====\n')
 for vt in vts:
  pat=struct.pack('<I',vt)
  hits=[]; pos=0
  while True:
   k=buf.find(pat,text.PointerToRawData,text.PointerToRawData+text.SizeOfRawData)
   if k<0: break
   hits.append(TVA+(k-text.PointerToRawData)); pos=k+1
   if len(hits)>100: break
  g.write(f'{vt:08X}: {[hex(x) for x in hits]}\n')
print('insns',len(ins))
