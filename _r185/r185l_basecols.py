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
    o=r2o(va)
    if o is None: return None
    e=raw.find(b'\0',o,o+m); return raw[o:e]
def colinfo(a):
    d=[dw(a+4*i) for i in range(5)]
    nm=cstr(d[3]+8) if d[3] else None
    return d,nm
for c in (0x7fb0c8,0x7fb0b0,0x7fb098,0x7fb080,0x7fb068,0x7fb050,0x7fb038,0x7fb020,0x7fb130,0x7faf90):
    d,nm=colinfo(c)
    print(hex(c),'sig/off/cd',d[0],d[1],d[2],'td',hex(d[3]) if d[3] else None,'chd',hex(d[4]) if d[4] else None,'name',nm)
