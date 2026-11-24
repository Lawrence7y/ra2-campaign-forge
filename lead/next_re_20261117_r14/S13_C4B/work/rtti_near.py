import pathlib,struct
import pefile
pe=pefile.PE(str(pathlib.Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")),fast_load=False);ib=pe.OPTIONAL_HEADER.ImageBase;data=pe.__data__
def ro(r,n=4):
 for s in pe.sections:
  if s.VirtualAddress<=r<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData) and r+n<=s.VirtualAddress+s.SizeOfRawData:return s.PointerToRawData+(r-s.VirtualAddress)
def u(va):
 o=ro(va-ib);return None if o is None else struct.unpack_from("<I",data,o)[0]
def c(va,n=160):
 o=ro(va-ib,1)
 if o is None:return None
 b=data[o:o+n];z=b.find(b"\x00")
 if z<0:return None
 try:return b[:z].decode("ascii")
 except:return None
for vt in [0x7e48d4,0x7ef8ec,0x7ef8b8]:
 print('VT',hex(vt))
 for i in range(-512,512):
  va=vt+4*i; x=u(va)
  if not x or not (0x7e1000<=x<0x812000):continue
  td=u(x+0xc)
  if not td or not (0x7e1000<=td<0x812000):continue
  nm=c(td+8)
  if nm and nm.startswith('.?AV') and nm.endswith('@@'):
   print('  candidate at',hex(va),'COL',hex(x),'TD',hex(td),nm)
