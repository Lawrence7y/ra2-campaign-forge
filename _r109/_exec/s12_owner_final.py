import sys,struct,json,collections,array,bisect
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r109/_exec')
from pe import *
from pe import _img
TL,TH=0x401000,0x7e1000; SPAN=TH-TL
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
PAD_MARK=(0xcc,0xc3,0x90)
padents=set()
for a in STARTS:
    k=a-TL
    if k>=1 and seg[k-1] in (0xcc,0xc3): padents.add(a)
ALLENT=sorted(callt|jmpt|vtsl|prol|padents)
ENT_NEAR=ALLENT

E=json.load(open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_extstat.json'))
ext={int(k):tuple(v) for k,v in E['extents'].items()}
ents=sorted((v[0],k) for k,v in ext.items())
ent_sorted=[x[0] for x in ents]
def owner_contain(a):
    j=bisect.bisect_right(ent_sorted,a)-1
    while j>=0:
        e,f=ents[j]; lo,hi=ext[f][1],ext[f][2]
        if lo<=a<hi: return e,'contain'
        j-=1
    return None,None
def owner_final(a):
    e,how=owner_contain(a)
    if e is not None: return e,how
    j=bisect.bisect_right(ENT_NEAR,a)-1
    return (ENT_NEAR[j],'nearest') if j>=0 else (None,'none')

D=json.load(open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_dispatch.json'))
own=collections.Counter(); how_c=collections.Counter(); mapping={}
for d in D:
    e,how=owner_final(d['va'])
    own[e]+=1; how_c[how]+=1; mapping[d['va']]=e
print('owners_total:',len(own),how_c)
json.dump(dict(owners_total=len(own),how=dict(how_c),
               owner_of={hex(k):v for k,v in mapping.items()}),
          open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_owner_dispatch.json','w'))
