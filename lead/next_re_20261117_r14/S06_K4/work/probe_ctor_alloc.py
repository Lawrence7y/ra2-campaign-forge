import struct,pefile,bisect,json,re
from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
R=Path(r'D:\Project\ra2-campaign-forge'); EXE=R/'ra2youli/gamemd.exe'; data=EXE.read_bytes(); pe=pefile.PE(str(EXE),fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
 va=IB+s.VirtualAddress; end=va+max(s.Misc_VirtualSize,s.SizeOfRawData); secs.append((s.Name.rstrip(b'\0').decode(),va,end,s.PointerToRawData,s.SizeOfRawData))
def off(va):
 for n,a,b,p,r in secs:
  if a<=va<b:
   d=va-a
   if d<r:return p+d
 return None
def at(va,n):
 o=off(va); return None if o is None or o+n>len(data) else data[o:o+n]
def u32(va):
 b=at(va,4); return None if b is None else struct.unpack('<I',b)[0]
def hx(x): return f'{x:08X}'
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
def dis(va,n,c=100):
 b=at(va,n); return [] if b is None else list(md.disasm(b,va,count=c))
# all direct E8 rel32 call targets in .text
text=[s for s in secs if s[0]=='.text'][0]; t_va,t_end,t_ptr,t_rs=text[1],text[2],text[3],text[4]
targets=set()
for i in range(t_rs-4):
 if data[t_ptr+i]==0xE8:
  rel=struct.unpack_from('<i',data,t_ptr+i+1)[0]; va=t_va+i+5+rel
  if t_va<=va<t_end: targets.add(va)
tlist=sorted(targets)
def enclosing(va):
 i=bisect.bisect_right(tlist,va)-1
 return tlist[i] if i>=0 else None
j=json.load(open(R/'lead/next_re_20261117_r14/S06_K4/work/all_rtti.json',encoding='utf-8'))
for cls in ['IsometricTileClass','OverlayClass','SmudgeClass']:
 v=next(v for v in j['vtables'] if v['class']=='.?AV'+cls+'@@' and v['offset']==0)
 vt=int(v['vt_hex'],16); pat=struct.pack('<I',vt)
 print('\nCLASS',cls,'VT',v['vt_hex'],'SLOT12',v['slots'][12],'SLOT11',v['slots'][11])
 # raw occurrences in text
 occ=[]
 for i in range(t_rs-3):
  if data[t_ptr+i:t_ptr+i+4]==pat: occ.append(t_va+i)
 print('vt byte occurrences',len(occ),[hx(x) for x in occ[:20]])
 ctors=set()
 for va in occ:
  e=enclosing(va)
  if e: ctors.add(e)
 print('candidate enclosing call targets',[hx(x) for x in sorted(ctors)])
 for e in sorted(ctors):
  ins=dis(e,384,220)
  writes=[it for it in ins if it.mnemonic=='mov' and vt in [int(op,16) for op in re.findall(r'0x([0-9A-Fa-f]+)',it.op_str)]]
  if writes:
   print('CTOR',hx(e),'writes',[(hx(it.address),it.bytes.hex(),it.op_str) for it in writes[:5]])
   # call sites to e
   cs=[]
   for i in range(t_rs-4):
    if data[t_ptr+i]==0xE8:
     rel=struct.unpack_from('<i',data,t_ptr+i+1)[0]; va=t_va+i+5+rel
     if va==e: cs.append(t_va+i)
   print(' callsites',len(cs),[hx(x) for x in cs[:20]])
   for c in cs[:10]:
    pre=dis(c-96,96,60)
    print('  PRE',hx(c),' | '.join(f'{hx(it.address)}:{it.mnemonic} {it.op_str}' for it in pre[-20:]))
