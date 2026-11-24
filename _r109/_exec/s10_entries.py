import sys,struct,json,collections,array,bisect
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r109/_exec')
from pe import *
from pe import _img
TL,TH=0x401000,0x7e1000; SPAN=TH-TL
raw=open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_insn.bin','rb').read()
n=len(raw)//5
STARTS=array.array('I'); STARTS.frombytes(raw[:4*n])
SIZES=array.array('B'); SIZES.frombytes(raw[4*n:])
ISSTART=bytearray(SPAN)
for a in STARTS: ISSTART[a-TL]=1
seg=_img[foff(TL):foff(TL)+SPAN]

def cnt(E,name):
    E=sorted(set(E))
    D=json.load(open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_dispatch.json'))
    own=set()
    for d in D:
        j=bisect.bisect_right(E,d['va'])-1
        if j>=0: own.add(E[j])
    print(name,'entries',len(E),'-> owners',len(own))
    return E,own

callt=set(); jmpt=set()
for k in range(SPAN-5):
    if not ISSTART[k]: continue
    b=seg[k]; a=TL+k
    if b==0xE8 and SIZES[STARTS.index(0) if False else 0] if False else False: pass
# simpler: use recorded sizes
for a in STARTS:
    k=a-TL; b=seg[k]
    if SIZES[a-STARTS[0]] if False else False: pass
# rebuild with dict
size_by={a:s for a,s in zip(STARTS,SIZES)}
callt=set(); jmpt=set()
for a in STARTS:
    k=a-TL; b=seg[k]; s=size_by[a]
    if b==0xE8 and s==5:
        t=(a+5+struct.unpack('<i',seg[k+1:k+5])[0])&0xffffffff
        if TL<=t<TH: callt.add(t)
    elif b==0xE9 and s==5:
        t=(a+5+struct.unpack('<i',seg[k+1:k+5])[0])&0xffffffff
        if TL<=t<TH: jmpt.add(t)
prol=set()
i=0
while True:
    i=seg.find(b'\x55\x8b\xec',i)
    if i<0: break
    if ISSTART[i]: prol.add(TL+i)
    i+=1
# address-taken text pointers anywhere in image
ptrtxt=set()
for s in SECS:
    for va in range(s['va'],s['vend'],4):
        v=u32(va)
        if v is not None and TL<=v<TH: ptrtxt.add(v)
print('call',len(callt),'jmp',len(jmpt),'prol',len(prol),'ptrtxt',len(ptrtxt))
c1=cnt(callt,'call-only')
c2=cnt(callt|prol,'call+prol')
c3=cnt(callt|prol|jmpt,'call+prol+jmp')
c4=cnt(callt|prol|ptrtxt,'call+prol+ptrtxt')
c5=cnt((callt|prol|ptrtxt|jmpt),'ALL')
# also add: start-aligned after int3 padding / alignment
extra=set()
for a in STARTS:
    k=a-TL
    if k>=2 and seg[k-1]==0xc3 and ISSTART[k]:  # after ret
        extra.add(a)
print('after-ret entries',len(extra))
c6=cnt(callt|prol|ptrtxt|jmpt|extra,'ALL+afterret')
json.dump(dict(call=sorted(callt),prol=sorted(prol),ptrtxt=sorted(ptrtxt),jmp=sorted(jmpt),afterret=sorted(extra)),
          open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_entrysets.json','w'))
