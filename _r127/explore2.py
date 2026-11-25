import os,struct,json,collections
import pefile,capstone
EXE='ra2bench/gamemd.exe'
pe=pefile.PE(EXE); IB=pe.OPTIONAL_HEADER.ImageBase
hay=bytes(pe.__data__)
def rd(va,n): return pe.get_data(va-IB,n)
def u32(va):
    b=rd(va,4); return struct.unpack('<I',b)[0] if len(b)==4 else None
def i32(va):
    b=rd(va,4); return struct.unpack('<i',b)[0] if len(b)==4 else None
def cstr(va,n=192):
    b=rd(va,n); e=b.find(b'\x00')
    return (b[:e] if e>=0 else b).decode('latin1')
def guid_text(b):
    d1,d2,d3=struct.unpack('<IHH',b[:8])
    return '{%08X-%04X-%04X-%s-%s}'%(d1,d2,d3,b[8:10].hex().upper(),b[10:].hex().upper())
for va in (0x7f7c60,0x7f7c70,0x7f7c80,0x7f7c90,0x7f7ca0,0x817bc0,0x818858,0x820270):
    print(hex(va), guid_text(rd(va,16)))
# class list
sym=json.load(open('out/reverse/symbols.json',encoding='utf-8'))['classes']
print('classes',len(sym))
def _va(x):
    return None if x is None else (x if isinstance(x,int) else int(str(x).strip(),16))
RD=[s for s in pe.sections if s.Name.rstrip(b'\x00')==b'.rdata'][0]
RD_LO=RD.VirtualAddress+IB; RD_HI=RD_LO+RD.Misc_VirtualSize
def bcds(vt):
    col=u32(vt-4)
    if col is None or not (RD_LO<=col<RD_HI): return None
    chd=u32(col+16)
    if chd is None or not (RD_LO<=chd<RD_HI): return None
    n,arr=u32(chd+8),u32(chd+12)
    if n is None or n>64 or arr is None or not (RD_LO<=arr<RD_HI): return None
    out=[]
    for i in range(n):
        bcd=u32(arr+4*i)
        if bcd is None or not (IB<=bcd<0xB80000): return None
        td=u32(bcd)
        if td is None or not (IB<=td<0xB80000): return None
        out.append({'name':cstr(td+8,192),'mdisp':i32(bcd+8)})
    return out
rows=[]
for k,v in sym.items():
    vt=_va(v.get('vtable_va'))
    if not vt: continue
    b=bcds(vt)
    if b is None: continue
    rows.append((k,vt,b))
print('decoded',len(rows))
# names containing Persist
persist=[r for r in rows if any('Persist' in x['name'] for x in r[2])]
print('classes with Persist in RTTI:',len(persist))
names=collections.Counter()
for k,vt,b in persist:
    for x in b:
        if 'Persist' in x['name']: names[x['name']]+=1
print(names.most_common(12))
# classes with IPersist but NOT IPersistStream
def has(b,s): return any(s in x['name'] for x in b)
only_p=[ (k,vt,[ (x['name'],x['mdisp']) for x in b]) for k,vt,b in persist if has(b,'IPersist@@') and not has(b,'IPersistStream')]
both=[ (k,vt) for k,vt,b in persist if has(b,'IPersistStream')]
print('only IPersist:',len(only_p),'with IPersistStream:',len(both))
for r in only_p[:6]: print('  ',r[0],hex(r[1]),r[2][:8])
# slot identity sharing for the both-family
fam=[vt for k,vt in both]
for slot in range(0,12):
    tg=collections.Counter()
    for vt in fam:
        t=u32(vt+4*slot)
        tg[t]+=1
    print('slot',slot,'distinct',len(tg),'top',[(hex(k) if k else None,n) for k,n in tg.most_common(3)])
