import struct,re
d=open(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe",'rb').read()
e=struct.unpack_from('<I',d,0x3C)[0];n=struct.unpack_from('<H',d,e+6)[0];osz=struct.unpack_from('<H',d,e+20)[0];opt=e+24;ib=struct.unpack_from('<I',d,opt+28)[0];so=opt+osz
secs=[]
for i in range(n):
 o=so+40*i;nm=d[o:o+8].rstrip(b'\0').decode();vs,va,rs,ra=struct.unpack_from('<IIII',d,o+8);secs.append((nm,ib+va,ra,rs,vs))
R=next(x for x in secs if x[0]=='.rdata');rva,raw,rs=R[1],R[2],R[3]
def at(va):return struct.unpack_from('<I',d,raw+(va-rva))[0]
for va in (0x7E3E88,0x7E3E8C,0x7E3E90,0x7E3E94,0x7E3E98,0x7E3EA0,0x7E3EB8,0x7E3EBC,0x7E3EC0,0x7E43C4):
 v=at(va);print(hex(va),'->',hex(v),'TEXT' if 0x401000<=v<0x7E038D else ('IMG' if 0x401000<=v<0xB80000 else 'NON'))
blk=d[raw:raw+rs]
print('decorated .? in rdata',len(re.findall(rb'\.\?[A-Z]',blk)))
print('??_7 rdata',len(re.findall(rb'\?\?_7',blk)),'allfile',len(re.findall(rb'\?\?_7',d)))
print('allfile .? count',len(re.findall(rb'\.\?[A-Z]',d)))
