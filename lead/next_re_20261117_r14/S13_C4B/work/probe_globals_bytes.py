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
for a in [0x87f924,0x7fc7c8,0x807b48,0x808640,0xa8ed84,0xa8e7ac,0x8871e0,0x89de30,0xac4948]:
 o=ro(a-ib,32)
 print(hex(a),data[o:o+32].hex() if o else None, [hex(x) for x in struct.unpack_from('<8I',data,o)] if o else None, repr(c(a)))
