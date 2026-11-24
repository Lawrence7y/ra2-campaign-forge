#!/usr/bin/env python3
# host-function resolution for B3 consumer sites (anchor-aligned)
import struct, json, os
from capstone import *
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"; OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_AUDIT_R9"
data=open(EXE,'rb').read()
e=struct.unpack_from('<I',data,0x3C)[0]; nsec=struct.unpack_from('<H',data,e+6)[0]
optsize=struct.unpack_from('<H',data,e+20)[0]; opt=e+24; IB=struct.unpack_from('<I',data,opt+28)[0]
secoff=opt+optsize; secs=[]
for i in range(nsec):
 o=secoff+40*i; nm=data[o:o+8].rstrip(b'\0').decode('latin1')
 vs,va,rs,ra=struct.unpack_from('<IIII',data,o+8); secs.append((nm,IB+va,ra,rs,vs))
T=next(x for x in secs if x[0]=='.text'); tva,traw,trs=T[1],T[2],T[3]
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=False

def find_anchor(buf,off,maxback=0x2000):
 j=off-1;g=0
 while j>4 and g<maxback:
  g+=1
  if buf[j]==0xC3 or buf[j]==0xC2:
   k=j+(1 if buf[j]==0xC3 else 3)
   while k<off and buf[k] in (0x90,0xCC): k+=1
   return k
  j-=1
 k=off-1;run=0
 while k>0 and buf[k] in (0x90,0xCC) and run<64: run+=1;k-=1
 return off if run>=2 else None

def resolve(site_va):
 off=site_va-tva; buf=data[traw:traw+trs]
 anc=find_anchor(buf,off)
 if anc is None: return dict(site=hex(site_va),anchor=None)
 start=tva+anc
 # disassemble from anchor up to site+0x200
 endoff=min(trs,off+0x200)
 insns=list(md.disasm(bytes(buf[anc:endoff]),start))
 site_ins=None; rets=[]
 for ins in insns:
  if ins.address<=site_va<ins.address+ins.size: site_ins=ins
  if ins.mnemonic in ('ret','retf'): rets.append(ins)
 # first ret after site whose following bytes are padding or another ret
 fn_end=None; retinfo=None
 for ins in rets:
  if ins.address<=site_va: continue
  na=ins.address+ins.size; noff=na-tva
  after=buf[noff:noff+8] if noff+8<=trs else b''
  pad=len(after)-len(after.lstrip(b'\xcc\x90'))
  fn_end=na
  retinfo=dict(ret_addr=hex(ins.address),ret_size=ins.size,fn_end=hex(na),after=after.hex(),pad_bytes=pad)
  break
 return dict(site=hex(site_va),anchor=hex(start),
   site_insn=(site_ins.mnemonic+' '+site_ins.op_str) if site_ins else None,
   retinfo=retinfo, assertion=(f'{hex(start)} <= {hex(site_va)} < {hex(fn_end)}' if fn_end else 'fn_end未取得'))

sites=[0x43B721,0x43B9FC,0x43BCFF,0x43B736,0x43BA11,0x43BD16]
out=[resolve(s) for s in sites]
with open(os.path.join(OUT,'hostcheck.json'),'w') as f: json.dump(out,f,indent=1)
print(json.dumps(out,indent=1))
