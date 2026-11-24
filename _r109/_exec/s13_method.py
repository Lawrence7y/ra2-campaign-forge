import sys,struct,json,collections,array,bisect
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r109/_exec')
from pe import *
from pe import _img
TL,TH=0x401000,0x7e1000; SPAN=TH-TL
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
# ---- padding-aligned starts: instruction start preceded by int3(cc)/ret(c3), or by a
#      run of nops that itself follows cc/c3 ----
padent=set()
for a in STARTS:
    k=a-TL
    if k==0: continue
    p=seg[k-1]
    if p in (0xcc,0xc3): padent.add(a); continue
    # walk back over nop/lea-reg-reg fillers up to 16 bytes
    t=k-1; steps=0
    while t>0 and steps<16 and seg[t] in (0x90,0x8b,0x66,0x2e): t-=1; steps+=1
    if steps>0 and t>=0 and seg[t] in (0xcc,0xc3): padent.add(a)
ENTRY=sorted(callt|jmpt|vtsl|prol|padent)
print('entry sets: call=%d jmp=%d vtsl=%d prol=%d pad=%d union=%d'%(
      len(callt),len(jmpt),len(vtsl),len(prol),len(padent),len(ENTRY)))

D=json.load(open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_dispatch.json'))
def nearest(E,a):
    j=bisect.bisect_right(E,a)-1
    return E[j] if j>=0 else None
for name,E in [('call',sorted(callt)),('call+prol',sorted(callt|prol)),
               ('call+jmp+vtsl+prol',sorted(callt|jmpt|vtsl|prol)),
               ('FULL(union)',ENTRY)]:
    own={nearest(E,d['va']) for d in D}
    print('%-22s owners=%d'%(name,len(own)))
json.dump(dict(call=sorted(callt),jmp=sorted(jmpt),vtsl=sorted(vtsl),
               prol=sorted(prol),pad=sorted(padent),entry=ENTRY),
          open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_entries_final.json','w'))
