import pathlib,struct
import pefile
pe=pefile.PE(str(pathlib.Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")),fast_load=False);ib=pe.OPTIONAL_HEADER.ImageBase;data=pe.__data__
def rvaoff(r,n=4):
 for s in pe.sections:
  if s.VirtualAddress<=r<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData) and r+n<=s.VirtualAddress+s.SizeOfRawData:return s.PointerToRawData+(r-s.VirtualAddress)
def u32(va):
 o=rvaoff(va-ib,4);return None if o is None else struct.unpack_from("<I",data,o)[0]
def cstr(va,n=200):
 o=rvaoff(va-ib,1)
 if o is None:return None
 b=data[o:o+n];z=b.find(b"\x00")
 if z<0:return None
 try:return b[:z].decode("ascii")
 except:return None
for va in [0x7fc7c8,0x7fc7e0,0x807b48,0x807b60,0x808640,0x808658]:
 print(hex(va),repr(cstr(va)))
for col in [0x7fa000+i*4 for i in range(0x200)]:
 td=u32(col+0xc)
 if td and 0x7e1000<=td<0x7e4100:
  nm=cstr(td+8)
  if nm and nm.startswith('.?AV') and any(x in nm for x in ['Bullet','Parasite','RadSite']):
   print('COL',hex(col),'TD',hex(td),nm)
