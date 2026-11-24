import pathlib,struct,json
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
for a in [0x816918,0x817658,0x8176d8,0x81af38,0x81d198,0x8296a8]:
 print(hex(a),repr(c(a,120)),'u+8',hex(u(a+8) if u(a+8) else 0),repr(c(u(a+8)) if u(a+8) else None))
# try COL+0xC = td for known COLs
for col in [0x7fa6a8,0x7faeb0,0x7faf48,0x7fc6c8,0x7fd240,0x804d58]:
 td=u(col+0xc); print('col',hex(col),'td',hex(td) if td else None,'name',repr(c(td+8) if td else None))
