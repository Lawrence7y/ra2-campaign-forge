import os,re,pefile
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
addrs=['0040D250','0045A070','0045A0A0','0045A0C0','0045A640','0045A680','0045A730','0045AB00','0045AB50','0045AC00','0045AC30','0045AC70','0045AC90','004D24A0','004D2510','004D27B0','004D27D0','004D2810','004D2910']
def parse_target(op):
 m=re.match(r'^(0x[0-9a-fA-F]+)',op.strip())
 return int(m.group(1),16) if m else None
feat_lines=['entry\tn\tlo\thi\tret\tret_imm\tjcc\tjmp\tback_jcc\tindirect_jmp\tcall\tindirect_call\tcmp_test\tor_eax_ff\tmem_writes']
for a in addrs:
 va=int(a,16)
 code=read(va,0x800)
 il=list(md.disasm(code,va,0x800))
 by={i.address:i for i in il}
 seen=set(); stack=[va]
 while stack:
  x=stack.pop()
  if x in seen or x not in by: continue
  seen.add(x); i=by[x]
  mnemonic=i.mnemonic
  if mnemonic.startswith('ret'): continue
  tgt=parse_target(i.op_str)
  if (mnemonic.startswith('j') or mnemonic.startswith('loop')) and tgt is not None:
   stack.append(tgt)
   if mnemonic!='jmp': stack.append(i.address+i.size)
   continue
  if mnemonic.startswith('j') or mnemonic.startswith('loop'):
   continue
  stack.append(i.address+i.size)
 ins=sorted((by[x] for x in seen),key=lambda x:x.address)
 lines=[]
 for i in ins:
  lines.append(f'{i.address:08X}  {i.bytes.hex():<20}  {i.mnemonic:<8} {i.op_str}')
 with open(os.path.join(OUT,f'DISASM_FN_{a}.txt'),'w',encoding='utf-8') as f:
  f.write('\n'.join(lines)+'\n')
 rets=[i for i in ins if i.mnemonic.startswith('ret')]
 jcc=[i for i in ins if i.mnemonic.startswith('j') and i.mnemonic!='jmp']
 jmp=[i for i in ins if i.mnemonic=='jmp']
 back=[i for i in ins if i.mnemonic.startswith('j') and (lambda t:t is not None and t<=i.address)(parse_target(i.op_str))]
 indj=[i for i in ins if i.mnemonic.startswith('j') and parse_target(i.op_str) is None]
 calls=[i for i in ins if i.mnemonic=='call']
 indc=[i for i in calls if parse_target(i.op_str) is None]
 cmps=[i for i in ins if i.mnemonic in ('cmp','test')]
 orff=[i for i in ins if i.mnemonic=='or' and 'eax, -1' in i.op_str]
 writes=[i for i in ins if i.mnemonic.startswith('mov') and i.operands and i.operands[0].type==X86_OP_MEM]
 ret_imm=sum(1 for i in rets if '0x' in i.op_str)
 feat_lines.append('\t'.join(map(str,[a,len(ins),f'{min(i.address for i in ins):08X}',f'{max(i.address for i in ins):08X}',len(rets),ret_imm,len(jcc),len(jmp),len(back),len(indj),len(calls),len(indc),len(cmps),len(orff),len(writes)])))
with open(os.path.join(OUT,'FEATURES.tsv'),'w',encoding='utf-8') as f: f.write('\n'.join(feat_lines)+'\n')
print('done')
