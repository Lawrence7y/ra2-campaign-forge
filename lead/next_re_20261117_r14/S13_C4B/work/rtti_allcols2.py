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
# Build COL list correctly in rdata
cols=set()
for s in pe.sections:
 if s.Name.rstrip(b'\x00')!=b'.rdata':continue
 for p in range(s.PointerToRawData,s.PointerToRawData+s.SizeOfRawData-12,4):
  col=ib+s.VirtualAddress+(p-s.PointerToRawData)
  td=u(col+0xc)
  if td and c(td+8) and c(td+8).startswith('.?AV'): cols.add(col)
print('cols',len(cols))
for vt in [0x7e48d4,0x7ef8ec,0x7ef8b8,0x7e17cc]:
 hits=[]
 for i in range(1,200):
  va=vt-4*i
  if va in cols:hits.append((i,hex(va),c(u(va+0xc)+8)))
 print(hex(vt),hits[:10])
for e in [0x468670,0x629fd0,0x62a260]:
 hits=[]
 for col in cols:
  for off in range(0,0x400,4):
   if u(col+off)==e:
    hits.append((hex(col+off),hex(col),hex(off),c(u(col+0xc)+8)));break
 print('entry',hex(e),hits[:20],len(hits))
