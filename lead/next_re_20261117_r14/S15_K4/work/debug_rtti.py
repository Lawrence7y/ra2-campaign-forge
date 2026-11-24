import pathlib,pefile,struct
root=pathlib.Path(r'D:\Project\ra2-campaign-forge');pe=pefile.PE(str(root/'ra2youli/gamemd.exe'));IB=pe.OPTIONAL_HEADER.ImageBase
def rd(va,n):
 try:return pe.get_data(va-IB,n)
 except Exception as e:return b''
def u(va):
 b=rd(va,4);return struct.unpack('<I',b)[0] if len(b)==4 else 0
for vt in (0x7F443C,0x7ED404,0x71E6A0):
 print('\nvt',hex(vt))
 for off in (-0x10,-0xC,-8,-4,0,4):print(' ',hex(off),hex(u(vt+off)))
 col=u(vt-4); print('COL',hex(col))
 for off in (0,4,8,0xC,0x10):print(' COL+',hex(off),hex(u(col+off)))
 td=u(col+0xC);print('TD',hex(td), 'name',rd(u(td+8),40))
