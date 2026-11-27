import struct,os,re
raw=open('ra2bench/gamemd.exe','rb').read()
def r2o(va):
    if 0x401000<=va<0x7E038D: return 0x1000-0x401000+va
    if 0x7E1000<=va<0x811074: return 0x3E1000-0x7E1000+va
    if 0x812000<=va<0x849BE4: return 0x412000-0x812000+va
    return None
def dw(va): 
    o=r2o(va); return None if o is None else struct.unpack_from('<I',raw,o)[0]
def where(v):
    if 0x401000<=v<0x7E038D: return 'text'
    if 0x7E1000<=v<0x811074: return 'rdata'
    if 0x812000<=v<0x849BE4: return 'data'
    return 'other'
def cstr(va,m=200):
    o=r2o(va); e=raw.find(b'\0',o,o+m); return raw[o:e]
def is_col(a):
    d=[dw(a+4*i) for i in range(5)]
    if None in d: return None
    if d[0] not in (0,1) or d[1]!=0 or d[2]!=0: return None
    if where(d[3])!='data' or where(d[4])!='rdata': return None
    nm=cstr(d[3]+8)
    if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): return None
    return (nm,d)
print('--- 0x7fb100..0x7fb140 ---')
for a in range(0x7fb100,0x7fb140,4):
    print(hex(a),hex(dw(a)),where(dw(a)))
print('--- is_col probe ---')
for a in (0x7fafd8,0x7faff0,0x7fb008,0x7fb118,0x7fb160,0x7fafc0,0x7fb130,0x7fb108):
    c=is_col(a)
    print(hex(a),'COL' if c else 'not',c[0] if c else '', 'next dword', hex(dw(a+20)) , where(dw(a+20)))
print('--- 0x7fafd0..0x7fb020 ---')
for a in range(0x7fafd0,0x7fb020,4):
    print(hex(a),hex(dw(a)),where(dw(a)))
