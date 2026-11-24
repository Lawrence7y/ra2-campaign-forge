
import struct,pefile,capstone
ROOT=r'D:\Project\ra2-campaign-forge'
EV=ROOT+r'\lead\next_re_20261117_r14\S08_K1\EVIDENCE'
B=open(ROOT+r'\ra2youli\gamemd.exe','rb').read(); PE=pefile.PE(ROOT+r'\ra2youli\gamemd.exe',fast_load=True); BASE=PE.OPTIONAL_HEADER.ImageBase
S=[]
for s in PE.sections:
 nm=s.Name.rstrip(b'\x00').decode(errors='replace'); S.append((nm,BASE+s.VirtualAddress,BASE+s.VirtualAddress+s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData))
def v2o(va):
 for nm,a,z,ro,sz in S:
  if a<=va<z:
   o=ro+(va-a)
   return o if 0<=o<len(B) else None
 return None
def u32(va):
 o=v2o(va)
 return struct.unpack_from('<I',B,o)[0] if o is not None and o+4<=len(B) else None
def cstr(va,n=100):
 o=v2o(va)
 if o is None: return None
 e=B.find(b'\x00',o,o+n)
 if e<0:e=o+n
 try:s=B[o:e].decode('ascii')
 except:return None
 return s if all(32<=ord(c)<127 for c in s) else None
out=[]
# find dwords equal to target
hits=[]
for nm,a,z,ro,sz in S:
 if nm not in ('.rdata','.data'): continue
 for va in range(a,z-4,4):
  o=ro+(va-a)
  if o+4>len(B):break
  if struct.unpack_from('<I',B,o)[0]==0x004309D0: hits.append((nm,va))
out.append('dword hits for 004309D0: '+repr(hits))
# for each, try vtable candidate by scanning back to contiguous function-pointer region; test COL at vt-4
for nm,h in hits:
 out.append('\nHIT %s %08X'%(nm,h))
 for back in range(0,0x200,4):
  base=h-back
  col=u32(base-4)
  if col and 0x7e0000<=col<=0x820000:
   td=u32(col+0xC)
   name=cstr(td+8,120) if td else None
   if name:
    out.append(' candidate vt=%08X slot=%d col=%08X td=%08X name=%s'%(base,back//4,col,td,name))
# constructor area
MD=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); MD.detail=True
o=v2o(0x430180)
out.append('\nCTOR 00430180..00430220')
for i in MD.disasm(B[o:o+0xA0],0x430180):
 out.append('%08X  %-20s %-8s %s'%(i.address,i.bytes.hex().upper(),i.mnemonic,i.op_str))
open(EV+r'\RTTI_004309D0.txt','w',encoding='utf-8').write('\n'.join(out))
print('\n'.join(out[:120]))
