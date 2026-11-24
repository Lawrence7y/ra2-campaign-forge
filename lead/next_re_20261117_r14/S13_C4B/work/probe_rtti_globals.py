import pathlib,struct,json
import pefile
root=pathlib.Path(r"D:\Project\ra2-campaign-forge"); pe=pefile.PE(str(root/"ra2youli"/"gamemd.exe"),fast_load=False); ib=pe.OPTIONAL_HEADER.ImageBase; data=pe.__data__
def rvaoff(r,n=4):
 for s in pe.sections:
  if s.VirtualAddress<=r<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData) and r+n<=s.VirtualAddress+s.SizeOfRawData:return s.PointerToRawData+(r-s.VirtualAddress)
def u32(va):
 o=rvaoff(va-ib,4);return None if o is None else struct.unpack_from("<I",data,o)[0]
def cstr(va,n=120):
 o=rvaoff(va-ib,1)
 if o is None:return None
 b=data[o:o+n]; z=b.find(b"\x00")
 if z<0:return None
 try:return b[:z].decode("ascii")
 except:return None
for vt in [0x7e48d4,0x7ef8ec,0x7ef8b8,0x7e46f8,0x7ef8a4,0x7f0824]:
 col=vt-4; td=u32(col+0xc); print(hex(vt),"col",hex(col),"td",hex(td) if td else None,"name",repr(cstr(td+8) if td else None))
for g in [0xa8ed84,0xb0f5b8,0xb0f5bc,0xb0f5c0,0xb0f5c5,0xb0f5c8,0xb0f5cc,0x89de30,0x89de34,0x89de38,0xac4948,0xac494c,0xac4950]:
 print("global",hex(g),"vptr",hex(u32(g)) if u32(g) is not None else None)
