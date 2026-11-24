import struct, collections
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM
P='D:/Project/ra2-campaign-forge/ra2youli/gamemd.exe'
class IMG:
 def __init__(s):
  s.d=open(P,'rb').read(); s.pe=pefile.PE(data=s.d,fast_load=True); s.ib=s.pe.OPTIONAL_HEADER.ImageBase
  sec=[x for x in s.pe.sections if x.Name.rstrip(b'\0')==b'.text'][0]
  s.lo=s.ib+sec.VirtualAddress; s.hi=s.lo+sec.Misc_VirtualSize
  s.md=Cs(CS_ARCH_X86,CS_MODE_32); s.md.detail=True; s.md.skipdata=True
 def rd(s,va,n):
  o=va-s.ib
  return s.d[o:o+n] if 0<=o<=len(s.d)-n else b''
 def u32(s,va):
  d=s.rd(va,4); return struct.unpack('<I',d)[0] if len(d)==4 else None
 def cstr(s,va,n=128):
  d=s.rd(va,n); z=d.find(b'\0'); return d[:z if z>=0 else n].decode('latin1',errors='replace')
 def vtable(s,vt,n=64):
  o=[]
  for i in range(n):
   p=s.u32(vt+4*i)
   if p is None or not (s.lo<=p<s.hi): break
   o.append(p)
  return o
 def rtti(s,vt):
  col=s.u32(vt-4); td=s.u32(col+12) if col else None
  return col,td,s.cstr(td+8) if td else None
 def insns(s,a=None,b=None):
  a=s.lo if a is None else a; b=s.hi if b is None else b
  return {i.address:i for i in s.md.disasm(s.rd(a,b-a),a) if i.id!=0}
 def refs(s,v):
  pat=struct.pack('<I',v); o=[]; p=0
  while True:
   j=s.d.find(pat,p)
   if j<0: break
   o.append(s.ib+j); p=j+1
  return o
def form(op):
 if op.type!=X86_OP_MEM:return None
 if op.mem.base==0 and op.mem.index==0:return 'A_abs'
 if op.mem.base!=0 and op.mem.index==0:return 'B_regbase'
 if op.mem.base!=0 and op.mem.index!=0:return 'C_idx'
 return 'other'
def access(i):
 o=i.operands
 if not o:return (None,None,None)
 m=i.mnemonic; d=o[0]
 if m in ('call','jmp','ljmp','lcall') and d.type==X86_OP_MEM:return ('X',0,form(d))
 mi=[k for k,x in enumerate(o) if x.type==X86_OP_MEM]
 if not mi or m=='lea':return (None,None,None)
 if m in ('cmp','test','push'):a='R'
 elif m=='pop':a='W'
 elif m in ('xchg','cmpxchg','add','sub','or','and','xor','adc','sbb','inc','dec','shl','shr','sar','rol','ror','not','neg'):a='RW'
 elif d.type==X86_OP_MEM:a='W'
 else:a='R'
 return (a,mi[0],form(o[mi[0]]))
def sites(img,ins,disp=0x29):
 out=[]
 for a,i in sorted(ins.items()):
  for op in i.operands:
   if op.type==X86_OP_MEM and op.mem.disp==disp:
    acc,mi,f=access(i)
    out.append((a,i.bytes.hex(),i.mnemonic,i.op_str,acc,form(op),i.reg_name(op.mem.base) if op.mem.base else '-',i.reg_name(op.mem.index) if op.mem.index else '-'))
    break
 return out
img=IMG(); ins=img.insns()
tg=collections.defaultdict(list)
for a,i in ins.items():
 if i.mnemonic in ('call','jmp') and i.operands and i.operands[0].type==X86_OP_IMM: tg[i.operands[0].imm].append(a)
for t in [0x431A30,0x431B20,0x431B80,0x432050,0x431F50,0x431F70,0x4322A0,0x4324B0,0x4325A0,0x4325C0,0x432610]:
 print('tgt %08X callers %s'%(t,[hex(x) for x in sorted(tg.get(t,[]))]))
for target in [0x5CE4F4,0x5CE894,0x6CF1A9,0x4A08A6,0x544C05]:
 prev=[t for t in tg if t<=target]
 st=max(prev) if prev else None
 print('site %08X prev target %s callers %s'%(target,hex(st) if st else '-',[hex(x) for x in sorted(tg.get(st,[]))][:6] if st else []))
def dump(st,label,maxn=120):
 print('\n=== %s %08X ==='%(label,st)); a=st
 for k in range(maxn):
  i=ins.get(a)
  if i is None: break
  mark=' <<<' if a in (0x431A69,0x431A9A,0x432090,0x432107,0x43212A,0x432202,0x432225,0x5CE4F4,0x5CE894,0x6CF1A9) else ''
  print('  %08X %-20s %-6s %s%s'%(a,i.bytes.hex(),i.mnemonic,i.op_str,mark))
  if i.mnemonic.startswith('ret') or i.mnemonic=='retf': break
  a+=i.size
dump(0x431A30,'BUF second vptr writer',120)
dump(0x432050,'BUF vslot12',120)
# find nearest targets for non-BUF sites and dump around them
for target in [0x5CE4F4,0x6CF1A9]:
 prev=[t for t in tg if t<=target]; st=max(prev) if prev else target-32
 print('\n--- context around %08X from %08X ---'%(target,st))
 for a in range(st,target+16):
  i=ins.get(a)
  if i and target-8<=a<=target+8: print('  %08X %-20s %-6s %s'%(a,i.bytes.hex(),i.mnemonic,i.op_str))
