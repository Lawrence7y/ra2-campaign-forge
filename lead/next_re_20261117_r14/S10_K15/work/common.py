import os,csv,json,hashlib,collections,struct,pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32,CS_OPT_SKIPDATA,CS_OPT_ON
ROOT=r"D:\Project\ra2-campaign-forge"
COV=os.path.join(ROOT,r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATL=os.path.join(ROOT,r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
VTJ=os.path.join(ROOT,r"lead\next_re_20261112_r10\W130_atlas\vtables_v2.json")
EXE=os.path.join(ROOT,r"ra2youli\gamemd.exe")
PE=pefile.PE(EXE,fast_load=True)
BASE=PE.OPTIONAL_HEADER.ImageBase
MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.detail=True; MD.skipdata=True
def va_to_off(va):
 rva=va-BASE
 for s in PE.sections:
  if s.VirtualAddress<=rva<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData):
   return s.PointerToRawData+rva-s.VirtualAddress
 return None
def read(va,n):
 o=va_to_off(va)
 if o is None: return b''
 with open(EXE,'rb') as f:
  f.seek(o); return f.read(n)
def u32(va):
 b=read(va,4); return struct.unpack('<I',b)[0] if len(b)==4 else None
def cstr(va,n=128):
 b=read(va,n); return b.split(b'\0')[0].decode('latin1','replace')
def load_rows():
 with open(COV,'r',encoding='utf-8-sig',newline='') as f: rows=[r for r in csv.reader(f,delimiter='\t')]
 if rows and rows[0][0]=='entry,subsystem': rows=rows[1:]
 with open(ATL,'r',encoding='utf-8',newline='') as f: atl={r[0].lower():r for r in csv.reader(f,delimiter='\t') if r}
 cov={r[0].upper():r for r in rows if len(r)>=8}
 return rows,cov,atl
def disasm(va,size,detail=True):
 b=read(va,size); return list(MD.disasm(b,va))
def fmt(ins):
 ops=', '.join(ins.op_str.split(',')).strip()
 return f"{ins.address:08X}  {ins.bytes.hex():<20} {ins.mnemonic:<8} {ops}"
def direct_calls(insns):
 out=[]
 for i in insns:
  if i.mnemonic=='call' and i.op_str.startswith('0x'):
   try: out.append((i.address,int(i.op_str,16)))
   except: pass
 return out
def call_target(i):
 if i.mnemonic=='call' and i.op_str.startswith('0x'):
  try:return int(i.op_str,16)
  except:pass
 return None
def vtable_info():
 with open(VTJ,'r',encoding='utf-8') as f: j=json.load(f)
 return j['vtables']
def class_at_slot(addr):
 out=[]
 for vt in vtable_info():
  va=vt['vt']; n=vt['slots']
  for k in range(n):
   p=u32(va+4*k)
   if p==addr:
    cls=vt.get('class','?')
    # COL must be vt-4; TD=COL+0xC; inline string at TD+8
    col=u32(va-4); td=u32(col+0xC) if col else None
    name=cstr(td+8,80) if td else '?'
    out.append((cls,td,name,k,hex(va)))
 return out
def find_refs_to(addr):
 pat=struct.pack('<I',addr)
 res=[]
 for s in PE.sections:
  if not (s.Characteristics & 0x20000000): continue
  data=read(BASE+s.VirtualAddress,max(s.Misc_VirtualSize,s.SizeOfRawData))
  start=0
  while True:
   p=data.find(pat,start)
   if p<0:break
   res.append(BASE+s.VirtualAddress+p); start=p+1
 return res
