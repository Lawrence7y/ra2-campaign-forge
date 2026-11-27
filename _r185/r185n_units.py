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
    if v is None: return ''
    if 0x401000<=v<0x7E038D: return 'TEXT'
    if 0x7E1000<=v<0x811074: return 'RDATA'
    if 0x812000<=v<0x849BE4: return 'DATA'
    return ''
def cstr(va,m=120):
    o=r2o(va); e=raw.find(b'\0',o,o+m); return raw[o:e]
print('--- UnitClass region ---')
for a in range(0x7F5C40,0x7F5CA0,4):
    print('%08x %08x %s'%(a,dw(a),wr(dw(a))))
print('--- is there a COL at 0x7f5c5c? ---')
for base in (0x7F5C5C,0x7F5C6C):
    d=[dw(base+4*i) for i in range(5)]
    print(hex(base),[hex(x) if x is not None else None for x in d],'name@pTD+8:',cstr(d[3]+8) if d[3] and wr(d[3])=='DATA' else None)
