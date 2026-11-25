import struct,json,collections
import pefile
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
for n,s in S.items():
    print(n, 'va=0x%x'%(s.VirtualAddress+IB), 'vsize=0x%x'%s.Misc_VirtualSize, 'raw=0x%x'%s.SizeOfRawData)
def rd(va,n): return pe.get_data(va-IB,n)
def u32(va):
    b=rd(va,4); return struct.unpack('<I',b)[0] if len(b)==4 else None
def guid_text(b):
    d1,d2,d3=struct.unpack('<IHH',b[:8])
    return '{%08X-%04X-%04X-%s-%s}'%(d1,d2,d3,b[8:10].hex().upper(),b[10:].hex().upper())
for va in (0x7e36c0,0x7e36d4,0x7e9b20,0x7e9b40,0x7e9b00):
    print(hex(va),guid_text(rd(va,16)))
# is 0x429270 a vtable slot0?
sym=json.load(open('out/reverse/symbols.json',encoding='utf-8'))['classes']
def _va(x): return None if x is None else (x if isinstance(x,int) else int(str(x).strip(),16))
hits=collections.defaultdict(list)
for k,v in sym.items():
    vt=_va(v.get('vtable_va'))
    if not vt: continue
    hits[u32(vt)].append((k,vt))
for t in (0x429270,0x429210,0x6cf430,0x429400,0x429450):
    print(hex(t),'->',[(k,hex(v)) for k,v in hits.get(t,[])])
