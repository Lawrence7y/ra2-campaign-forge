import sys,struct,json,collections,array,bisect
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r109/_exec')
from pe import *
from pe import _img
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
TL,TH=0x401000,0x7e1000; SPAN=TH-TL
md=Cs(CS_ARCH_X86,CS_MODE_32)
raw=open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_insn.bin','rb').read(); n=len(raw)//5
STARTS=array.array('I'); STARTS.frombytes(raw[:4*n]); SIZES=array.array('B'); SIZES.frombytes(raw[4*n:])
size_by=dict(zip(STARTS,SIZES)); ISS=bytearray(SPAN)
for a in STARTS: ISS[a-TL]=1
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
        if e and TL<=e<TH and ISS[e-TL]: vtsl.add(e)
prol=set()
i=0
while True:
    i=seg.find(b'\x55\x8b\xec',i)
    if i<0: break
    if ISS[i]: prol.add(TL+i)
    i+=1
D=json.load(open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_dispatch.json'))

def build(E):
    E=sorted(set(E)); ES=set(E)
    FUNC=array.array('i',bytes(4*SPAN))
    ext={}; fid=0
    for e in E:
        if FUNC[e-TL]!=0: continue
        fid+=1; lo=hi=e; st=[e]
        while st:
            a=st.pop()
            while TL<=a<TH and ISS[a-TL] and FUNC[a-TL]==0:
                FUNC[a-TL]=fid
                o=foff(a); ins=None
                for x in md.disasm_lite(_img[o:o+16],a): ins=x; break
                if ins is None: break
                _,sz,mn,op=ins
                if a<lo: lo=a
                if a+sz>hi: hi=a+sz
                nxt=a+sz
                if mn.startswith('ret') or mn.startswith('iret'): break
                if mn=='jmp':
                    if op.startswith('0x'):
                        t=int(op,16)
                        if TL<=t<TH and ISS[t-TL]:
                            if t in ES: break     # tail call
                            st.append(t); break
                    break
                if mn.startswith('j') or mn.startswith('loop'):
                    if op.startswith('0x'):
                        t=int(op,16)
                        if TL<=t<TH: st.append(t)
                a=nxt
        ext[fid]=(e,lo,hi)
    ents=sorted((v[0],k) for k,v in ext.items()); es=[x[0] for x in ents]
    return FUNC,ext,ents,es,fid

def attribute(ext,ents,es):
    own=collections.Counter(); unres=[]
    for d in D:
        a=d['va']; j=bisect.bisect_right(es,a)-1; best=None
        while j>=0:
            e,f=ents[j]; lo,hi=ext[f][1],ext[f][2]
            if lo<=a<hi: best=e; break
            j-=1
        if best is None: unres.append(a)
        own[best]+=1
    return own,unres

sets={'call':callt,
      'call+prol':callt|prol,
      'call+vtsl':callt|vtsl,
      'call+prol+vtsl':callt|prol|vtsl,
      'call+jmp+prol+vtsl':callt|jmpt|prol|vtsl}
out={}
for nm,E in sets.items():
    FUNC,ext,ents,es,fid=build(E)
    own,unres=attribute(ext,ents,es)
    nn=len([k for k in own if k is not None])
    print('%-20s funcs=%-6d owners=%-4d unresolved=%d'%(nm,fid,nn,len(unres)))
    out[nm]=dict(funcs=fid,owners=nn,unresolved=len(unres),ext={str(k):list(v) for k,v in ext.items()})
json.dump(out,open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_matrix.json','w'))
