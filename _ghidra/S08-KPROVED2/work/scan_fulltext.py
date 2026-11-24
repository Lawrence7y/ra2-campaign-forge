import json,os,struct,pefile
from capstone import *
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
SYM=r'D:\Project\ra2-campaign-forge\re_atlas\evidence\rtti\symbols.json'
OUT=r'D:\Project\ra2-campaign-forge\_ghidra\S08-KPROVED2\EVIDENCE\scan_stats.json'
pe=pefile.PE(EXE); base=pe.OPTIONAL_HEADER.ImageBase; buf=open(EXE,'rb').read()
sec=next(s for s in pe.sections if s.Name.rstrip(b'\x00').decode()=='.text')
TVA=base+sec.VirtualAddress; TSZ=sec.Misc_VirtualSize; TRAWSZ=sec.SizeOfRawData
def off(va):
 for s in pe.sections:
  v=base+s.VirtualAddress
  if v<=va<v+max(s.Misc_VirtualSize,s.SizeOfRawData): return s.PointerToRawData+va-v
 return None
def read(va,n):
 o=off(va); return b'' if o is None else buf[o:o+n]
text=read(TVA,TSZ)
# roots from raw E8/E9 rel32 and PE entry
roots=set()
if pe.OPTIONAL_HEADER.AddressOfEntryPoint:
 ep=base+pe.OPTIONAL_HEADER.AddressOfEntryPoint
 if TVA<=ep<TVA+TSZ: roots.add(ep)
for i in range(len(text)-5):
 op=text[i]
 if op in (0xE8,0xE9):
  rel=struct.unpack_from('<i',text,i+1)[0]
  t=TVA+i+5+rel
  if TVA<=t<TVA+TSZ: roots.add(t)
# roots from RTTI vfuncs
sym=json.load(open(SYM,encoding='utf-8'))
for c in sym.get('classes',{}).values():
 for v in c.get('vfuncs',[]):
  a=int(v,16)
  if TVA<=a<TVA+TSZ: roots.add(a)
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=False
md2=Cs(CS_ARCH_X86,CS_MODE_32); md2.detail=True
seen=set(); work=sorted(roots); decoded=0
while work:
 root=work.pop()
 if root in seen or not (TVA<=root<TVA+TSZ): continue
 chunk=read(root,min(0x4000,TVA+TSZ-root))
 n=0
 for ins in md.disasm(chunk,root,0x4000):
  n+=1
  if ins.address in seen:
   break
  seen.add(ins.address); decoded+=1
  op=ins.op_str.strip()
  if op.startswith('0x'):
   try: tgt=int(op,16)
   except: tgt=None
   if tgt is not None and TVA<=tgt<TVA+TSZ and tgt not in seen: work.append(tgt)
  if ins.mnemonic.startswith('ret'):
   break
  if ins.mnemonic=='jmp':
   break
  if n>12000: break
# stats
seen_sorted=sorted(seen)
e8_boundary=sum(1 for a in seen_sorted if read(a,1)==b'\xe8')
stats={
 'image_base':hex(base),'text_va':hex(TVA),'text_va_end':hex(TVA+TSZ),
 'virtual_size':hex(TSZ),'size_of_raw_data':hex(TRAWSZ),
 'roots':len(roots),'decoded_unique_instructions':len(seen),
 'e8_at_instruction_boundary':e8_boundary,
 'capstone_version':__import__('capstone').__version__,
 'addressing_mode':'CS_MODE_32',
 'op_index_present':hasattr(next(md2.disasm(b'\x8b\x01',0x401000,1)).operands[0],'index'),
 'mem_index_for_mem_no_index':next(md2.disasm(b'\x8b\x01',0x401000,1)).operands[1].mem.index,
 'note':'rooted traversal from raw E8/E9 rel32 targets, PE entry, and RTTI vfuncs; VirtualSize authoritative'
}
json.dump(stats,open(OUT,'w',encoding='utf-8'),indent=2,ensure_ascii=False)
print(json.dumps(stats,indent=2,ensure_ascii=False))
