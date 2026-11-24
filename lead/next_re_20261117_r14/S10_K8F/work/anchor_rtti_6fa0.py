import struct,pefile
pe=pefile.PE(r'D:/Project/ra2-campaign-forge/ra2youli/gamemd.exe');base=pe.OPTIONAL_HEADER.ImageBase;d=pe.__data__
def off(v):return pe.get_offset_from_rva(v-base)
def u32(v):return struct.unpack_from('<I',d,off(v))[0]
def rdstr(v):
 o=off(v);e=d.find(b'\x00',o);return d[o:e].decode('ascii','replace')
for vt in [0x7F3650,0x7F36B4]:
 cols=[u32(vt-4*i) for i in (1,2,3)]
 print('VT',hex(vt),'cands',[hex(x) for x in cols])
 for col in cols:
  try:
   td=u32(col+0xc);print(' COL',hex(col),'TD',hex(td),'NAME',repr(rdstr(td+8)))
  except Exception as e:print(' COL',hex(col),'ERR',e)
for td in [0x00840120]:print('TD',hex(td),'NAME',repr(rdstr(td+8)))
