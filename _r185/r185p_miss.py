import struct,re
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
def cstr(va,m=200):
    o=r2o(va)
    if o is None: return None
    e=raw.find(b'\0',o,o+m); return raw[o:e]
def colname(a):
    d=[dw(a+4*i) for i in range(5)]
    if None in d or d[0] not in (0,1) or d[1]!=0 or d[2]!=0: return None
    if wr(d[3])!='DATA': return None
    return cstr(d[3]+8)
miss=[('ParticleClass',0x7ef954),('ParticleSystemClass',0x7efb9c),('ScriptClass',0x7f0f78),('SuperWeaponTypeClass',0x7f4090),('VoxelAnimClass',0x7f6318)]
for n,vt in miss:
    print('==',n,hex(vt))
    for j in range(-3,4):
        a=vt+4*j; v=dw(a)
        print('  ',hex(a),hex(v) if v is not None else None,wr(v), colname(v) if wr(v)=='RDATA' else '')
