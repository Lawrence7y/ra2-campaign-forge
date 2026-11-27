import struct
raw=open('ra2bench/gamemd.exe','rb').read()
def r2o(va):
    if 0x401000<=va<0x7E038D: return 0x1000-0x401000+va
    if 0x7E1000<=va<0x811074: return 0x3E1000-0x7E1000+va
    if 0x812000<=va<0x849BE4: return 0x412000-0x812000+va
    return None
def dw(va):
    o=r2o(va); return None if o is None else struct.unpack_from('<I',raw,o)[0]
def wr(v):
    if v is None: return 'None'
    if 0x401000<=v<0x7E038D: return 'text'
    if 0x7E1000<=v<0x811074: return 'rdata'
    if 0x812000<=v<0x849BE4: return 'data'
    return 'other'
def cstr(va,m=200):
    o=r2o(va)
    if o is None: return None
    e=raw.find(b'\0',o,o+m); return raw[o:e]
print('--- 0x7fb0e0 arr ---')
for i in range(10):
    a=0x7fb0e0+4*i; v=dw(a)
    print(i,hex(a),hex(v) if v is not None else None, wr(v))
for col in (0x7fb118,0x7fb160,0x7fafc0):
    chd=dw(col+16); nb=dw(chd+8); arr=dw(chd+12)
    print('COL',hex(col),'CHD',hex(chd),'nb',nb,'arr',hex(arr), [hex(dw(arr+4*i)) for i in range(min(nb,10))])
