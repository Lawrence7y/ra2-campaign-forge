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
# enumerate cols from rdata as before
cols=set()
for p in range(pe.sections[1].PointerToRawData,pe.sections[1].PointerToRawData+pe.sections[1].SizeOfRawData-12,4):
 col=ib+pe.sections[1].VirtualAddress+(p-pe.sections[1].PointerToRawData)
 td=u(col+0xc)
 nm=c(td+8) if td else None
 if nm and nm.startswith('.?AV'):cols.add(col)
for e in [0x468670,0x629fd0,0x62a260]:
 hits=[]
 for col in cols:
  # for each col scan at most 256 dwords forward but require at least first 4 slots are code pointers and col immediately precedes table region
  for off in range(0,0x400,4):
   va=col+off
   if u(va)==e:
    first=[u(col+4*k) for k in range(8)]
    if sum(1 for x in first if x and 0x401000<=x<0x7e0000)>=4:
     hits.append((hex(va),hex(col),hex(off),c(u(col+0xc)+8)))
    break
 print(hex(e),hits[:30],len(hits))
