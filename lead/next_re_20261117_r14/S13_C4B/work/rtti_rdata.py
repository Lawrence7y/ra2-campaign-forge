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
for a in [0x807a98,0x807a9c,0x807aa0,0x807aa4,0x807aa8]:
 print(hex(a),hex(u(a) or 0),repr(c(u(a) or 0) if u(a) else None))
# find COL by scanning all dwords in rdata whose +0xc points to TD whose +8 is string
n=0
for s in pe.sections:
 if s.Name.rstrip(b'\x00')!=b'.rdata':continue
 for p in range(s.PointerToRawData,s.PointerToRawData+s.SizeOfRawData-12,4):
  col=ib+s.VirtualAddress+(p-s.PointerToRawData)
  td=u(col+0xc)
  if not td:continue
  nm=c(td+8)
  if nm and nm.startswith('.?AV'):
   n+=1
   if n<=10:print('COL',hex(col),hex(td),nm)
print('count',n)
