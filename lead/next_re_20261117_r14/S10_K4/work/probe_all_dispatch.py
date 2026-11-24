
from pathlib import Path
import pefile,struct,re
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
ROOT=Path(r'D:\Project\ra2-campaign-forge')
data=(ROOT/'ra2youli/gamemd.exe').read_bytes(); pe=pefile.PE(str(ROOT/'ra2youli/gamemd.exe'),fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections: secs.append((IB+s.VirtualAddress,IB+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData),s.PointerToRawData,s.SizeOfRawData))
def off(va):
 for a,b,r,z in secs:
  if a<=va<b and va-a<z: return r+va-a
 return None
def rd(va,n):
 o=off(va); return None if o is None or o+n>len(data) else data[o:o+n]
def u32(va):
 b=rd(va,4); return struct.unpack('<I',b)[0] if b else None
def cstr(va):
 b=rd(va,200); return b.split(b'\0')[0].decode('latin1') if b else '<null>'
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
def dis(a,n,c=80):
 b=rd(a,n); return list(md.disasm(b,a,count=c)) if b else []
names=[cstr(u32(0x816CAC+4*i)) for i in range(32)]
table=[u32(0x5B34E8+4*i) for i in range(32)]
print('mid	name	stub	vslot	disp	call_abs	store_abs')
for i,stub in enumerate(table):
 ins=dis(stub,64,40)
 call=None; store=None; disp=None
 for k,it in enumerate(ins):
  if it.mnemonic=='call' and it.op_str.startswith('dword ptr ['):
   m=re.search(r'\+ (0x[0-9a-fA-F]+)\]',it.op_str)
   if m: disp=int(m.group(1),16); call=it.address
   for jt in ins[k+1:k+8]:
    if jt.mnemonic=='mov' and jt.op_str=='dword ptr [esi + 8], eax': store=jt.address
   break
 print('%d	%s	%08X	%s	%s	%s	%s'%(i,names[i],stub,disp//4 if disp is not None else '-',hex(disp) if disp is not None else '-',hex(call) if call else '-',hex(store) if store else '-'))
print('=== non-table stubs around 34A2,3480 ===')
for a in [0x34A2,0x3480,0x34C4,0x34E0]:
 print('--- %08X ---'%a)
 for it in dis(a,0x30,20): print('%08X %-18s %s'%(it.address,it.bytes.hex(),it.op_str))
