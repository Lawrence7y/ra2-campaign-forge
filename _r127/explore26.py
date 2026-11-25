import struct,json,collections
import pefile
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
def rd(va,n): return pe.get_data(va-IB,n)
def u32(va):
    b=rd(va,4); return struct.unpack('<I',b)[0] if len(b)==4 else None
def i32(va):
    b=rd(va,4); return struct.unpack('<i',b)[0] if len(b)==4 else None
def cstr(va,n=200):
    b=rd(va,n); e=b.find(b'\x00'); return (b[:e] if e>=0 else b).decode('latin1')
def gt(b):
    d1,d2,d3=struct.unpack('<IHH',b[:8])
    return '{%08X-%04X-%04X-%s-%s}'%(d1,d2,d3,b[8:10].hex().upper(),b[10:].hex().upper())
RD=S['.rdata']; RD_LO=RD.VirtualAddress+IB; RD_HI=RD_LO+RD.Misc_VirtualSize
def rtti(vt):
    col=u32(vt-4)
    if not col or not (RD_LO<=col<RD_HI): return None
    ptd=u32(col+12); pchd=u32(col+16)
    if not ptd or not (RD_LO<=ptd<RD_HI): return None
    n,arr=u32(pchd+8),u32(pchd+12)
    out=[]
    for i in range(min(n or 0,64)):
        bcd=u32(arr+4*i); td=u32(bcd)
        out.append((cstr(td+8,200), i32(bcd+8)))
    return cstr(ptd+8,200), out
sym=json.load(open('out/reverse/symbols.json',encoding='utf-8'))['classes']
def _va(x): return None if x is None else (x if isinstance(x,int) else int(str(x).strip(),16))
# hypothesis: GUID 16 bytes at vtable-0x14
res=[]
for k,v in sym.items():
    vt=_va(v.get('vtable_va'))
    if not vt: continue
    g=rd(vt-0x14,16)
    r=rtti(vt)
    if r is None: continue
    owner,bases=r
    res.append((k,vt,gt(g),owner,bases))
print('classes with vtable:',len(res))
byguid=collections.defaultdict(set)
for k,vt,g,owner,bases in res:
    au=[n for n,m in bases if n.startswith('.?AU') and not n.endswith('IUnknown@@')]
    byguid[g].add(tuple(sorted(au)))
multi={g:s for g,s in byguid.items() if len(s)>1}
print('GUIDs shared by classes with DIFFERENT interface sets:',len(multi))
for g,s in list(multi.items())[:8]: print('  ',g,s)
# test on ISwizzle / IApplication / IFlyControl
for target in ('.?AUISwizzle@@','.?AUIApplication@@','.?AUIFlyControl@@'):
    hits=[(k,hex(vt),g,owner) for k,vt,g,owner,bases in res if any(n==target for n,m in bases)]
    print(target,'classes:',len(hits))
    for h in hits[:6]: print('   ',h)
# dump neighborhood of 0x7e9b20 and 0x7e36c0
for base in (0x7e9b00,0x7e36a0,0x7f40e0):
    print('--- dump 0x%x'%base)
    for va in range(base,base+0x50,4):
        print('   %x: %08x'%(va,u32(va) or 0))
