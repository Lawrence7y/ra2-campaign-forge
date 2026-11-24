import pathlib,struct
import pefile
pe=pefile.PE(str(pathlib.Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")),fast_load=False);ib=pe.OPTIONAL_HEADER.ImageBase;data=pe.__data__
def ro(r,n=4):
 for s in pe.sections:
  if s.VirtualAddress<=r<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData) and r+n<=s.VirtualAddress+s.SizeOfRawData:return s.PointerToRawData+(r-s.VirtualAddress)
def c(va,n=240):
 o=ro(va-ib,1)
 if o is None:return None
 b=data[o:o+n];z=b.find(b'\x00')
 if z<0:return None
 try:return b[:z].decode('ascii')
 except:return None
for td in [0x81afb0,0x8366e8,0x839600]:
 print(hex(td),repr(c(td+8)))
for vt in [0x7e48d4,0x7ef8ec,0x7ef8b8]:
 print('VT',hex(vt))
 for i in range(-80,0):
  va=vt+4*i; o=ro(va-ib,4)
  if o is None: continue
  x=struct.unpack_from('<I',data,o)[0]
  td=u=None
  o2=ro(x+0xc-ib,4) if 0x400000<=x<0xC00000 else None
  if o2: td=struct.unpack_from('<I',data,o2)[0]
  nm=c(td+8) if td and 0x400000<=td<0xC00000 else None
  if nm and nm.startswith('.?AV'):print(' ',hex(va),hex(x),hex(td),nm)
