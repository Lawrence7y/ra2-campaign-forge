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
    if 0x401000<=v<0x7E038D: return 'TEXT'
    if 0x7E1000<=v<0x811074: return 'RDATA'
    if 0x812000<=v<0x849BE4: return 'DATA'
    return 'other'
for vt in (0x7ef954,0x7e1f50,0x7f5c70):
    a=vt-4; d=[dw(a+4*i) for i in range(5)]
    print(hex(vt),'COLdwords',[(hex(x) if x is not None else None, wr(x)) for x in d])
    k=0
    while wr(dw(vt+4*k))=='TEXT': k+=1
    print('   text run',k,'term',hex(dw(vt+4*k)),wr(dw(vt+4*k)))
