import pathlib,struct,json
import pefile
root=pathlib.Path(r"D:\Project\ra2-campaign-forge"); pe=pefile.PE(str(root/"ra2youli"/"gamemd.exe"),fast_load=False); ib=pe.OPTIONAL_HEADER.ImageBase; data=pe.__data__
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
rtti={}
for s in pe.sections:
 for p in range(s.PointerToRawData,s.PointerToRawData+s.SizeOfRawData-12,4):
  v=struct.unpack_from("<I",data,p)[0]
  if not (0x7e1000<=v<0x812000):continue
  o=ro(v+0xc-ib)
  if o is None:continue
  td=struct.unpack_from("<I",data,o)[0]
  if not (0x7e1000<=td<0x812000):continue
  o2=ro(td+8-ib,1)
  if o2 is None:continue
  b=data[o2:o2+160];z=b.find(b"\x00")
  if z<0:continue
  try:nm=b[:z].decode("ascii")
  except:continue
  if nm.startswith(".?AV") and nm.endswith("@@"):
   va=ib+s.VirtualAddress+(p-s.PointerToRawData)
   rtti[v]=(hex(va),hex(td),nm)
for vt in [0x7e48d4,0x7ef8ec,0x7ef8b8,0x7e46f8,0x7ef8a4,0x7f0824]:
 print('VT',hex(vt))
 for i in range(-64,64):
  va=vt+4*i;x=u(va)
  if x in rtti:print(' ',i,hex(va),hex(x),rtti[x])
print('rtti count',len(rtti))
