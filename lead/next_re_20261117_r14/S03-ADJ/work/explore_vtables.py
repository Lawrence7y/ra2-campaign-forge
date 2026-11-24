import pefile,struct
P=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
b=open(P,'rb').read(); pe=pefile.PE(data=b,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
print('IB',hex(IB))
for s in pe.sections:
 print(s.Name.decode(errors='replace').rstrip('\0'),hex(IB+s.VirtualAddress),hex(s.Misc_VirtualSize),hex(s.PointerToRawData),hex(s.SizeOfRawData))
def rd(va,n): return b[va-IB:va-IB+n]
def u32(va): return struct.unpack('<I',rd(va,4))[0]
def cstr(va,n=120):
 d=rd(va,n); z=d.find(b'\0'); return d[:z if z>=0 else n].decode('latin1')
for name,vt in [('RawFile',0x7F0904),('BufferIO',0x7E3A2C),('CDFile',0x7E1668),('CCFile',0x7E16B0),('MixFile',0x7EDF50)]:
 col=u32(vt-4); td=u32(col+0xC); nm=cstr(td+8)
 slots=[]; i=0
 while 0x401000<=u32(vt+i*4)<0x7E1000 and i<64: slots.append(u32(vt+i*4)); i+=1
 print(name,'vt',hex(vt),'COL',hex(col),'TD',hex(td),'NAME',repr(nm),'slots',len(slots))
 print('  ',' '.join(f'{k}:{v:08X}' for k,v in enumerate(slots)))
