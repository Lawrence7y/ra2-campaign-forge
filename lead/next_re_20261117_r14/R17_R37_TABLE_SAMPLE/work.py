#!/usr/bin/env python3
import hashlib, struct, bisect
from pathlib import Path
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_MEM, CS_AC_WRITE, CS_AC_READ

IMAGE = Path(r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe')
EXPECT = '73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476'
SLOT = 0x87F924
b = IMAGE.read_bytes(); sha = hashlib.sha256(b).hexdigest().upper(); assert sha == EXPECT
lfa=struct.unpack_from('<I',b,0x3c)[0]; coff=lfa+4
nsec=struct.unpack_from('<H',b,coff+2)[0]; size_opt=struct.unpack_from('<H',b,coff+16)[0]; opt=coff+20
ib=struct.unpack_from('<I',b,opt+28)[0]; sa=struct.unpack_from('<I',b,opt+32)[0]
secs=[]
for i in range(nsec):
 o=opt+size_opt+i*40
 name=b[o:o+8].decode('latin1').rstrip('\0')
 vsize,rva,raw_size,raw_ptr=struct.unpack_from('<IIII',b,o+8)
 secs.append(dict(name=name,rva=rva,va=ib+rva,vsize=vsize,raw=raw_ptr,raw_size=raw_size))
def align_up(x,a): return (x+a-1)//a*a
def map_va(va):
 rva=va-ib
 for s in secs:
  off=rva-s['rva']
  if 0 <= off < s['raw_size']: return s,off,s['raw']+off,'raw'
 for s in secs:
  off=rva-s['rva']
  if 0 <= off < align_up(s['vsize'],sa): return s,off,None,'virtual'
 return None
text=[s for s in secs if s['name']=='.text'][0]
code_lo=text['va']; code_hi=code_lo+text['vsize']; raw_lo=text['raw']; raw_hi=raw_lo+text['raw_size']
tcode=b[raw_lo:raw_hi]
# trusted entries: .text start + all in-range E8 targets + long padding successors; no ret-byte scan.
starts={code_lo}
for i in range(len(tcode)-4):
 if tcode[i] != 0xE8: continue
 site=code_lo+i; rel=struct.unpack_from('<i',tcode,i+1)[0]; dst=site+5+rel
 if code_lo <= dst < code_hi: starts.add(dst)
i=0
while i < len(tcode):
 c=tcode[i]
 if c in (0x90,0xCC):
  j=i
  while j < len(tcode) and tcode[j]==c: j+=1
  if ((c==0x90 and j-i>=4) or (c==0xCC and j-i>=2)) and code_lo+j < code_hi: starts.add(code_lo+j)
  i=j
 else: i+=1
starts=sorted(s for s in starts if code_lo <= s < code_hi)
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True
needle=struct.pack('<I',SLOT)
raw_hits=[code_lo+i for i in range(len(tcode)-3) if tcode[i:i+4]==needle]
print('SHA',sha,'entries',len(starts),'raw_hits',len(raw_hits),'text_raw',len(tcode))
# strict decode each anchor span; collect touching and writing instructions.
cands=[]; touches=[]; decode_fails=[]; decoded_total=0; span_count=0
for idx,host in enumerate(starts):
 end=starts[idx+1] if idx+1<len(starts) else code_hi
 if end<=host: continue
 off=map_va(host)[2]
 if off is None or off+end-host>len(b): continue
 ins=list(md.disasm(b[off:off+end-host],host))
 decoded_total += end-host; span_count += 1
 cover=0; last=host
 for x in ins:
  if x.address != last:
   decode_fails.append((host,end,last,x.address)); break
  last=x.address+x.size; cover+=x.size
  for op in x.operands:
   if op.type==CS_OP_MEM and op.mem.disp==SLOT and op.mem.base==0 and op.mem.index==0 and op.mem.segment==0:
    rec=(x,host,end,op.access)
    touches.append(rec)
    if op.access & CS_AC_WRITE: cands.append(rec)
 if last < end and not decode_fails[-1:]: decode_fails.append((host,end,last,end))
print('spans',span_count,'decoded_bytes',decoded_total,'touch',len(touches),'write',len(cands),'decode_fails',len(decode_fails))
print('DECODE_FAILS first',decode_fails[:20])
for x,host,end,acc in sorted(cands,key=lambda z:z[0].address):
 print('WRITE',hex(x.address),x.bytes.hex(' '),x.mnemonic,x.op_str,'host',hex(host),'end',hex(end),'acc',acc)
# also list all instructions touching slot but not writes, grouped by mnemonic, to know patterns
from collections import Counter
print('TOUCH MNEM',Counter(x.mnemonic for x,h,e,a in touches))
for x,host,end,acc in touches[:20]:
 print('TOUCH',hex(x.address),x.mnemonic,x.op_str,'host',hex(host),'acc',acc)
