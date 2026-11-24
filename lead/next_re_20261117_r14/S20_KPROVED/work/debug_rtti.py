import pefile,struct,re
p=pefile.PE(r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe',fast_load=True)
raw=open(r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe','rb').read(); base=p.OPTIONAL_HEADER.ImageBase
def nv(x): return format(x & 0xffffffff,'08X')
def readva(v,n):
    try:
        off=p.get_offset_from_rva((int(v,16) if isinstance(v,str) else v)-base)
        return raw[off:off+n]
    except Exception as e:
        return b''
def rtti(vt):
    cb=readva(int(vt,16)-4,4); print('cb',cb.hex())
    col=struct.unpack_from('<I',cb,0)[0] if len(cb)==4 else 0
    tb=readva(col+0xC,4); print('tb',tb.hex())
    td=struct.unpack_from('<I',tb,0)[0] if len(tb)==4 else 0
    nb=readva(td+8,160); print('nb',nb[:40]); z=nb.find(b'\0'); print('name',nb[:z if z>=0 else len(nb)].decode('ascii','replace'))
    return nv(col),nv(td)
name='?$DynamicVectorClass::PAVVox::vslot3'
m=re.search('(?:v?slot)([0-9]+)$', name, re.I); slot=int(m.group(1)); site='007E1E38'; vt=nv(int(site,16)-4*slot)
print('slot',slot,'vt',vt); print('rtti',rtti(vt))
