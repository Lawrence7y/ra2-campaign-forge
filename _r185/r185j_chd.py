import struct
raw=open('ra2bench/gamemd.exe','rb').read()
def r2o(va):
    if 0x401000<=va<0x7E038D: return 0x1000-0x401000+va
    if 0x7E1000<=va<0x811074: return 0x3E1000-0x7E1000+va
    if 0x812000<=va<0x849BE4: return 0x412000-0x812000+va
    return None
def dw(va):
    o=r2o(va); return None if o is None else struct.unpack_from('<I',raw,o)[0]
def cstr(va,m=200):
    o=r2o(va); e=raw.find(b'\0',o,o+m); return raw[o:e]
for col,name in [(0x7fb118,'AbstractClass'),(0x7fb160,'INoticeSource'),(0x7fafc0,'INoticeSink')]:
    chd=dw(col+16)
    print(name,'COL',hex(col),'CHD',hex(chd))
    print('  CHD raw',[hex(dw(chd+4*i)) for i in range(6)])
    nb=dw(chd+8); arr=dw(chd+12)
    print('  numBase',nb,'arr',hex(arr))
    for i in range(min(nb,10)):
        e=dw(arr+4*i); td=dw(e+12) if e else None
        print('   base',i,hex(e) if e else None, cstr(td+8) if td else None)
