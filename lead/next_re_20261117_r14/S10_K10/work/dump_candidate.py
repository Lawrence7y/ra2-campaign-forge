from pathlib import Path
import sys,csv,re,bisect,struct
sys.path.insert(0,str(Path(__file__).parent))
from scan_candidates import load,feats
from capstone import *
from capstone.x86 import *
cov,atl,names,pe,data,image,off,string_at,md,dis=load()
textsec=next(s for s in pe.sections if s.Name.rstrip(b'\0')==b'.text')
tva=image+textsec.VirtualAddress; traw=textsec.PointerToRawData; tsize=textsec.SizeOfRawData
funcs=sorted((int(e,16),int(a['size'])) for e,a in atl.items())
def containing(va):
 i=bisect.bisect_right(funcs,(va,10**9))-1
 if i>=0 and funcs[i][0]<=va<funcs[i][0]+funcs[i][1]:
  return f'{funcs[i][0]:08X}'
 return ''
def annotate(m):
 s=f'{m.address:08X}  {m.bytes.hex():<20} {m.mnemonic:<8} {m.op_str}'
 if m.mnemonic=='call' and m.operands and m.operands[0].type==X86_OP_IMM:
  k=f'{m.operands[0].imm&0xffffffff:08X}'.lower(); r=names.get(k)
  if r: s+='    ; '+r['name']
 for op in m.operands:
  v=None
  if op.type==X86_OP_IMM:v=op.imm&0xffffffff
  elif op.type==X86_OP_MEM and op.mem.base==0:v=op.mem.disp&0xffffffff
  if v:
   st=string_at(v)
   if st: s+=f'    ; STR {st!r}'
 return s
def context(va,rad=8):
 sva=va-rad*8; n=rad*2+3
 return '\n'.join(annotate(m) for m in dis(f'{sva:08X}',n*8,maxb=n*8) if m.id)
def dump(entry):
 e=entry.strip().lower(); va=int(e,16); r=names[e]
 ins=dis(e)
 out=[f'ENTRY {entry}  NAME {r["name"]}  GRADE {r["grade"]}  SIZE {atl[e]["size"]}', 'DISASM:']
 out += [annotate(m) for m in ins if m.id]
 out.append('\nDIRECT CALLERS:')
 found=0
 for o in range(traw,traw+tsize-5):
  if data[o]!=0xE8:continue
  rel=struct.unpack_from('<i',data,o+1)[0]
  site=tva+(o-traw); target=(site+5+rel)&0xffffffff
  if target!=va:continue
  found+=1
  out.append(f'-- call site {site:08X} in {containing(site) or "?"}; target={target:08X}')
  out.append(context(site))
 if not found:out.append('(none)')
 slotm=re.search(r'::slot(\d+)$',r['name'])
 if slotm:
  offv=int(slotm.group(1))*4
  out.append(f'\nVCALL SITES offset +0x{offv:X} (locator only):')
  cnt=0
  # linear disasm from .text start; capstone skipdata
  for m in md.disasm(data[traw:traw+tsize],tva):
   if m.id==0:continue
   if m.mnemonic=='call' and m.operands and m.operands[0].type==X86_OP_MEM:
    mem=m.operands[0].mem
    if mem.disp==offv:
     cnt+=1
     out.append(f'-- vcall site {m.address:08X} in {containing(m.address) or "?"}: {m.mnemonic} {m.op_str}')
     out.append(context(m.address,6))
     if cnt>=40:break
  if not cnt:out.append('(none)')
 return '\n'.join(out)
if __name__=='__main__':
 for entry in sys.argv[1:]:
  p=Path(__file__).parent.parent/'EVIDENCE'/f'DISASM_{entry.upper()}.txt'
  p.write_text(dump(entry),'utf-8',newline='\n')
  print('wrote',p)
