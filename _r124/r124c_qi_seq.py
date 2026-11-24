# -*- coding: utf-8 -*-
"""R124c: QI comparison sequence vs RTTI base-array order (pure bytes)."""
import io, json, os, struct, collections
import pefile, capstone
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pe = pefile.PE(os.path.join(ROOT,'ra2bench','gamemd.exe')); IB = pe.OPTIONAL_HEADER.ImageBase
def rd(va,n): return pe.get_data(va-IB,n)
def u32(va):
    b=rd(va,4); return struct.unpack('<I',b)[0] if len(b)==4 else None
def cstr(va,n=192):
    b=rd(va,n); e=b.find(b'\x00'); return b[:e].decode('latin1') if e>=0 else b.decode('latin1')
sym=json.load(io.open(os.path.join(ROOT,'out','reverse','symbols.json'),encoding='utf-8'))['classes']
qi =json.load(io.open(os.path.join(ROOT,'_r110','r110a_iidmap.json'),encoding='utf-8'))['rows']
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)

def basearray(vt):
    col=u32(vt-4); chd=u32(col+16); n=u32(chd+8); arr=u32(chd+12); out=[]
    for i in range(n):
        bcd=u32(arr+4*i); td=u32(bcd)
        out.append({'td':td,'name':cstr(td+8,192),
                    'mdisp':struct.unpack('<i',rd(bcd+4,4))[0],
                    'pdisp':struct.unpack('<i',rd(bcd+8,4))[0],
                    'vdisp':struct.unpack('<i',rd(bcd+12,4))[0]})
    return out

def cmp_seq(fn):
    """IID immediates loaded into edi (`mov edi, IMM`) matched by a nearby
    `mov ecx, 4` + `repe cmpsd` — the MSVC QI template. Stops at first ret."""
    ins=list(md.disasm(rd(fn,0x800),fn))
    seq=[]
    for i,x in enumerate(ins):
        if x.mnemonic=='mov' and x.op_str.startswith('edi, 0x'):
            v=int(x.op_str.split(', ')[1],16)
            w=ins[max(0,i-8):i+5]
            if any(y.mnemonic=='mov' and y.op_str=='ecx, 4' for y in w) and \
               any(y.mnemonic.startswith('repe') for y in w):
                seq.append(v)
    return seq

rows=[]
for r in qi:
    name=r['cls']; rec=sym[name]; vt=int(rec['vtable_va'],16)
    rows.append({'cls':name,'vt':vt,'slot0':int(r['slot0'],16),
                 'bases':basearray(vt),'seq':cmp_seq(int(r['slot0'],16)),
                 'accept':[i['ptr'] for i in r['iids']]})
json.dump({'rows':rows},io.open(os.path.join(ROOT,'_r124','r124c_qi_seq.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)

c=collections.Counter(tuple('0x%x'%x for x in x['seq']) for x in rows)
print('seq patterns:')
for k,v in c.most_common(10): print(' ',v,k)
print()
for x in rows:
    if x['cls'] in ('AITriggerTypeClass','AbstractClass','AnimClass','HouseClass','AbstractTypeClass','BuildingClass'):
        print(x['cls'])
        print('  bases:', [(b['name'],b['mdisp']) for b in x['bases']])
        print('  seq  :', ['0x%x'%v for v in x['seq']])
