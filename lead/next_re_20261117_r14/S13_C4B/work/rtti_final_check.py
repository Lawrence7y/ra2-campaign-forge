import pathlib,struct
import pefile
pe=pefile.PE(str(pathlib.Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")),fast_load=False);ib=pe.OPTIONAL_HEADER.ImageBase;data=pe.__data__
def ro(r,n=4):
 for s in pe.sections:
  if s.VirtualAddress<=r<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData) and r+n<=s.VirtualAddress+s.SizeOfRawData:return s.PointerToRawData+(r-s.VirtualAddress)
def u(va):
 o=ro(va-ib);return None if o is None else struct.unpack_from('<I',data,o)[0]
def c(va,n=200):
 o=ro(va-ib,1)
 if o is None:return None
 b=data[o:o+n];z=b.find(b'\x00')
 if z<0:return None
 try:return b[:z].decode('ascii')
 except:return None
for col in [0x7fa6a8,0x807a98]:
 for off in [0,4,8,0xc,0x10,0x14]:
  va=col+off;x=u(va)
  print(hex(va),hex(x) if x else None,repr(c(x) if x else None))
 print()
for vt in [0x7e17cc,0x7e48d4,0x7ef8ec,0x7ef8b8]:
 for back in range(4,0x1000,4):
  va=vt-back;x=u(va)
  if not x:continue
  td=u(x+0xc)
  if not td:continue
  nm=c(td+8)
  if nm and nm.startswith('.?AV'):
   print('VT',hex(vt),'COL',hex(va),hex(x),hex(td),nm,'back',hex(back));break
 else: print('VT',hex(vt),'no COL')
