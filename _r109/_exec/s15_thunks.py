import sys,struct,json,collections,array,bisect
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r109/_exec')
from pe import *
from pe import _img
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
TL,TH=0x401000,0x7e1000
md=Cs(CS_ARCH_X86,CS_MODE_32)
R=json.load(open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_vt_raw.json'))
VT={int(k,16):v for k,v in R['vtables'].items()}

def decode_n(a,nmax=6):
    o=foff(a)
    if o is None: return []
    out=[]
    for ins in md.disasm_lite(_img[o:o+40],a):
        out.append(ins)
        if len(out)>=nmax: break
    return out

def follow_thunk(a,limit=6):
    """Return (final_target, kind). kind in direct/thunk-none/unknown"""
    cur=a; chain=0
    while chain<limit:
        ins=decode_n(cur,6)
        if not ins: return cur,'no-code'
        m0=ins[0]
        # 1) direct jmp target   (E9 rel32)
        if m0[2]=='jmp' and m0[3].startswith('0x'):
            t=int(m0[3],16)
            if TL<=t<TH: cur=t; chain+=1; continue
            return cur,'ext'
        # 2) mov eax,[esp+4] ; jmp target    (adjustor thunk, this-adjust)
        if (m0[2]=='mov' and m0[3].startswith('eax, dword ptr [esp + 4')
            and len(ins)>1 and ins[1][2]=='jmp' and ins[1][3].startswith('0x')):
            t=int(ins[1][3],16)
            if TL<=t<TH: cur=t; chain+=1; continue
            return cur,'ext'
        # 3) sub ecx, imm ; jmp target       (multiple-inheritance adjustor, thiscall)
        if m0[2]=='sub' and m0[3].startswith('ecx,') and len(ins)>1 \
           and ins[1][2]=='jmp' and ins[1][3].startswith('0x'):
            t=int(ins[1][3],16)
            if TL<=t<TH: cur=t; chain+=1; continue
            return cur,'ext'
        # 4) mov eax,[esp+4] ; add eax,imm ; jmp target
        if (m0[2]=='mov' and m0[3].startswith('eax, dword ptr [esp + 4')
            and len(ins)>2 and ins[1][2]=='add' and ins[1][3].startswith('eax,')
            and ins[2][2]=='jmp' and ins[2][3].startswith('0x')):
            t=int(ins[2][3],16)
            if TL<=t<TH: cur=t; chain+=1; continue
            return cur,'ext'
        return cur,'body'
    return cur,'chain-limit'

fwd={}; kinds=collections.Counter()
for v in VT.values():
    pass
slots=collections.Counter()
per_class=collections.defaultdict(list)
for vt_va,v in VT.items():
    for j in range(v['slots']):
        e=u32(vt_va+4*j)
        if not e: continue
        final,kind=follow_thunk(e)
        fwd[(vt_va,j)]=(e,final,kind)
        kinds[kind]+=1
        slots[j]+=1
print('slot entries:',len(fwd))
print('thunk kinds:',kinds.most_common())
changed=sum(1 for k,(e,f,kind) in fwd.items() if e!=f)
print('entries where thunk resolved to different addr:',changed)
json.dump(dict(kinds=dict(kinds),n_slots=len(fwd),
               changed=changed,
               fwd={('%x_%d'%(k[0],k[1])):list(v) for k,v in fwd.items()}),
          open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_thunks.json','w'))
