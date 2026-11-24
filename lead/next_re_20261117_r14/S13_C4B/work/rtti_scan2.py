import pathlib,struct,json
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
# known good from classification
for vt, expected in [(0x7e17cc,'.?AV?$DynamicVectorClass@PAVBombClass@@@@'),(0x7e1e84,'.?AV?$DynamicVectorClass@PAVWarheadTypeClass@@@@')]:
 col=u(vt-4); td=u(col+0xc); nm=c(td+8)
 print('GOOD',hex(vt),hex(col),hex(td),repr(nm),'expect',expected)
# candidate: scan up to 1024 bytes before/after vt for any COL whose TD+8 begins '.?AV' using direct scan of dword at each address
for vt in [0x7e48d4,0x7ef8ec,0x7ef8b8]:
 hits=[]
 for va in range(vt-0x400,vt+0x400,4):
  x=u(va)
  if not x or not(0x7e1000<=x<0x812000):continue
  o=ro(x+0xc-ib)
  if o is None:continue
  td=struct.unpack_from('<I',data,o)[0]
  if not (0x7e1000<=td<0x812000):continue
  nm=c(td+8)
  if nm and nm.startswith('.?AV'):
   hits.append((hex(va),hex(x),hex(td),nm))
 print('CAND',hex(vt),len(hits),hits[:20])
