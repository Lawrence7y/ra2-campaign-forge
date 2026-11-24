
import os,struct
import pefile,capstone
ROOT=r'D:\Project\ra2-campaign-forge'
EV=ROOT+r'\lead\next_re_20261117_r14\S08_K1\EVIDENCE'
EXE=ROOT+r'\ra2youli\gamemd.exe'
B=open(EXE,'rb').read(); PE=pefile.PE(EXE,fast_load=True); BASE=PE.OPTIONAL_HEADER.ImageBase
SECS=[]
for s in PE.sections:
 nm=s.Name.rstrip(b'\x00').decode(errors='replace')
 SECS.append((nm,BASE+s.VirtualAddress,BASE+s.VirtualAddress+s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData))
def v2o(va):
 for nm,a,z,ro,sz in SECS:
  if a<=va<z: return ro+(va-a)
 return None
def read(va,n):
 o=v2o(va)
 return B[o:o+n] if o is not None else b''
def cstr(va,maxn=120):
 o=v2o(va)
 if o is None: return None
 end=B.find(b'\x00',o,o+maxn)
 if end<0: end=o+maxn
 s=B[o:end]
 if len(s)<3: return None
 try: t=s.decode('ascii')
 except: return None
 return t if all(32<=ord(c)<127 or c in '\r\n\t' for c in t) else None
MD=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); MD.detail=True
out=[]
def dump(title,start,end):
 out.append('\n===== '+title+' '+f'{start:08X}'+('..'+f'{end:08X}' if end else '')+' =====')
 va=start
 raw=read(start,(end-start) if end else 180)
 for i in MD.disasm(raw,start):
  sx=''
  for o in i.operands:
   if o.type==capstone.x86.X86_OP_IMM:
    s=cstr(o.imm & 0xffffffff)
    if s: sx+=' ; STR@'+f'{o.imm&0xffffffff:08X}'+'='+repr(s)
  out.append(f'{i.address:08X}  {i.bytes.hex().upper():<20} {i.mnemonic:<8} {i.op_str}{sx}')
# atlas symbols for context
AT={}
with open(ROOT+r'\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv',encoding='utf8',errors='replace') as f:
 h=f.readline().rstrip().split('\t')
 for l in f:
  r=dict(zip(h,l.rstrip('\r\n').split('\t')))
  AT[int(r['entry'],16)]=r
for e in [0x004309D0,0x0047EFE0,0x0047F250,0x004801F0,0x00686B20,0x0065CA80,0x0065CA00,0x004A3890,0x005B40B0,0x004068E0]:
 r=AT.get(e)
 if r: out.append(f'ATLAS {e:08X}: size={r["size"]} n_instr={r["n_instr"]} n_callers={r["n_callers"]} n_callees={r["n_callees"]} strings={r["strings"]}')
dump('004309D0 full',0x004309D0,0x004309D0+235)
dump('0047EFE0 first 120B',0x0047EFE0,0x0047EFE0+120)
dump('0047F250 first 160B',0x0047F250,0x0047F250+160)
dump('004801F0 calls area',0x00480200,0x004802B0)
dump('00686B20 caller area',0x00431B70 if False else 0x00687B70,0x00687BEA)
open(EV+r'\DISASM_CANDIDATES.txt','w',encoding='utf-8').write('\n'.join(out))
print('wrote',EV+r'\DISASM_CANDIDATES.txt','lines',len(out))
