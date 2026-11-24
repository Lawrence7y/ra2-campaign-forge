import sys,struct,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r109/_exec')
from pe import *
from pe import _img
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
TL,TH=0x401000,0x7e1000
md=Cs(CS_ARCH_X86,CS_MODE_32)
R=json.load(open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_vt_raw.json'))
VT={int(k,16):v for k,v in R['vtables'].items()}
def dec(a,n=8):
    o=foff(a)
    if o is None: return []
    return list(md.disasm_lite(_img[o:o+48],a))[:n]

def is_direct_jmp(i):
    return i[2]=='jmp' and i[3].startswith('0x') and len(i[3])>2

def follow(a,limit=8):
    cur=a; chain=0
    while chain<limit:
        ins=dec(cur,8)
        if not ins: return cur,'nocode'
        m0=ins[0]
        if is_direct_jmp(m0):
            cur=int(m0[3],16); chain+=1; continue
        # adjustor: mov eax,[esp+4] (then optional add/sub eax,imm) then jmp target
        if m0[2]=='mov' and m0[3].startswith('eax, dword ptr [esp + 4'):
            k=1; adj=0
            if len(ins)>1 and ins[1][2] in ('add','sub') and ins[1][3].startswith('eax,'):
                k=2
            if len(ins)>k and is_direct_jmp(ins[k]):
                cur=int(ins[k][3],16); chain+=1; continue
            return cur,'adjustor-nonjmp'
        # ecx adjustor: sub ecx,imm / add ecx,imm ; jmp
        if m0[2] in ('sub','add') and m0[3].startswith('ecx,') and len(ins)>1 and is_direct_jmp(ins[1]):
            cur=int(ins[1][3],16); chain+=1; continue
        return cur,'body'
    return cur,'limit'

res={}; kinds=collections.Counter()
for vt_va,v in VT.items():
    for j in range(v['slots']):
        e=u32(vt_va+4*j)
        if not e: continue
        f,kind=follow(e)
        res[(vt_va,j)]=(e,f,kind); kinds[kind]+=1
print('slot entries',len(res))
for k,c in kinds.most_common(): print(' ',k,c)
diff=[(k,v) for k,v in res.items() if v[0]!=v[1]]
print('entries whose final != slot value:',len(diff))
for (vt,j),(e,f,kind) in diff[:10]:
    print(' ',hex(vt),'slot',j,hex(e),'->',hex(f),kind)
json.dump(dict(kinds=dict(kinds),n=len(res),n_diff=len(diff),
               entries={('%x_%d'%(k[0],k[1])):[v[0],v[1],v[2]] for k,v in res.items()}),
          open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_thunks2.json','w'))
