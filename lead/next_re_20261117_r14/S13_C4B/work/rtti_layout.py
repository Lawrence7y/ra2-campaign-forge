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
for col in [0x7fa6a8,0x807a98,0x807b48,0x81afb0]:
 for a in [col,col+4,col+8,col+0xc,col+0x10]: print(hex(a),hex(u(a) or 0),repr(c(u(a) or 0) if u(a) else None))
 print()
