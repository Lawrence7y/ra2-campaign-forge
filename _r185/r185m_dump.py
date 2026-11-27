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
for a in range(0x7fb020,0x7fb140,4):
    print('%08x %08x %s'%(a,dw(a),wr(dw(a))))
