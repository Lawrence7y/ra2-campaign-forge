import struct,pefile
pe=pefile.PE(r'D:/Project/ra2-campaign-forge/ra2youli/gamemd.exe');base=pe.OPTIONAL_HEADER.ImageBase;d=pe.__data__
def off(v):return pe.get_offset_from_rva(v-base)
targ={0x6b6ea0:'6EA0',0x6b6c90:'6C90',0x6b6fa0:'6FA0',0x6b7f10:'7F10',0x41ba90:'41BA90',0x5b35e0:'5B35E0',0x5b3570:'5B3570',0x41b870:'41B870'}
lo=0x7e1000;hi=0x812000
for va in range(lo,hi,4):
 try:x=struct.unpack_from('<I',d,off(va))[0]
 except:continue
 if x in targ: print('REF',hex(va),'->',targ[x])
