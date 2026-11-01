import struct
P=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
data=open(P,'rb').read()
SECS=[('.text',0x1000,0x1000,0x3E0000),('.rdata',0x3E1000,0x3E1000,0x31000),('.data',0x412000,0x412000,0x6C000)]
def va2off(va):
    rva=va-0x400000
    for n,rva0,raw0,sz in SECS:
        if rva0<=rva<rva0+sz:
            return raw0+(rva-rva0), n
    return None,None
def rd(va,n):
    o,s=va2off(va)
    assert o is not None, hex(va)
    return data[o:o+n]
def cstr(va,maxn=200):
    b=rd(va,maxn); i=b.find(b'\x00')
    return b[:i if i>=0 else maxn].decode('latin1')
