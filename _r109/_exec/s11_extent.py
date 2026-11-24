import sys,struct,json,collections,array,bisect
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r109/_exec')
from pe import *
from pe import _img
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
TL,TH=0x401000,0x7e1000; SPAN=TH-TL
md=Cs(CS_ARCH_X86,CS_MODE_32)
raw=open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_insn.bin','rb').read(); n=len(raw)//5
STARTS=array.array('I'); STARTS.frombytes(raw[:4*n]); SIZES=array.array('B'); SIZES.frombytes(raw[4*n:])
size_by=dict(zip(STARTS,SIZES)); ISSTART=bytearray(SPAN)
for a in STARTS: ISSTART[a-TL]=1
seg=_img[foff(TL):foff(TL)+SPAN]

callt=set(); jmpt=set()
for a in STARTS:
    k=a-TL; b=seg[k]; s=size_by[a]
    if b==0xE8 and s==5:
        t=(a+5+struct.unpack('<i',seg[k+1:k+5])[0])&0xffffffff
        if TL<=t<TH: callt.add(t)
    elif b==0xE9 and s==5:
        t=(a+5+struct.unpack('<i',seg[k+1:k+5])[0])&0xffffffff
        if TL<=t<TH: jmpt.add(t)
R=json.load(open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_vt_raw.json'))
VT={int(k,16):v for k,v in R['vtables'].items()}
vtsl=set()
for k,v in VT.items():
    for j in range(v['slots']):
        e=u32(k+4*j)
        if e and ISSTART[e-TL]: vtsl.add(e)
prol=set()
i=0
while True:
    i=seg.find(b'\x55\x8b\xec',i)
    if i<0: break
    if ISSTART[i]: prol.add(TL+i)
    i+=1
# padding-preceded entries: 0xCC (int3) run or ret then start
pad_entries=set()
for a in STARTS:
    k=a-TL
    if k>=1 and seg[k-1]==0xcc: pad_entries.add(a)
    elif k>=1 and seg[k-1]==0xc3: pad_entries.add(a)
ENTRIES=sorted((callt|jmpt|vtsl|prol|pad_entries))
print('entries union:',len(ENTRIES),'call',len(callt),'jmp',len(jmpt),'vtsl',len(vtsl),'prol',len(prol),'pad',len(pad_entries))

ENTSET=set(ENTRIES)
def dec(a):
    o=foff(a)
    if o is None: return None
    for ins in md.disasm_lite(_img[o:o+16],a): return ins
    return None
FUNC=array.array('i',bytes(4*SPAN))
extents={}
fid=0
for e in ENTRIES:
    if not ISSTART[e-TL]: continue
    if FUNC[e-TL]!=0: continue
    fid+=1; lo=hi=e
    stack=[e]
    while stack:
        a=stack.pop()
        while TL<=a<TH and ISSTART[a-TL] and FUNC[a-TL]==0:
            FUNC[a-TL]=fid
            ins=dec(a)
            if ins is None: break
            _,sz,mn,op=ins
            if a<lo: lo=a
            if a+sz>hi: hi=a+sz
            nxt=a+sz
            if mn.startswith('ret') or mn.startswith('iret'): break
            if mn=='jmp':
                if op.startswith('0x') and TL<=int(op,16)<TH:
                    t=int(op,16)
                    if t in ENTSET: break        # tail call -> own func
                    stack.append(t); break
                break
            if mn.startswith('j') or mn.startswith('loop'):
                if op.startswith('0x') and TL<=int(op,16)<TH: stack.append(int(op,16))
            a=nxt
    extents[fid]=(e,lo,hi)
print('functions:',fid)
# build entry->extent index for containment
ent2f={e:f for f,(e,lo,hi) in extents.items()}
# interval list for containment (innermost = greatest entry <= site)
elist=sorted(extents.items(), key=lambda kv: kv[1][0])
by_entry=sorted((v[0],k) for k,v in extents.items())
ent_sorted=[x[0] for x in by_entry]

D=json.load(open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_dispatch.json'))
own=collections.Counter(); unresolved=0
for d in D:
    a=d['va']
    j=bisect.bisect_right(ent_sorted,a)-1
    best=None
    while j>=0:
        e,f=by_entry[j]
        lo,hi=extents[f][1],extents[f][2]
        if lo<=a<hi: best=f; break
        j-=1
    if best is None: unresolved+=1
    own[best]+=1
print('dispatch owners:',len([k for k in own if k is not None]),'unresolved',unresolved)
json.dump(dict(n_func=fid,n_entries=len(ENTRIES),n_owners=len([k for k in own if k is not None]),
               unresolved=unresolved,
               extents={str(k):v for k,v in extents.items()}),
          open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_extstat.json','w'))
with open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_funcmap2.bin','wb') as f: f.write(FUNC.tobytes())
