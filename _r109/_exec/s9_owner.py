import sys,struct,json,collections,array,bisect
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r109/_exec')
from pe import *
from pe import _img
TL,TH=0x401000,0x7e1000; SPAN=TH-TL

raw=open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_insn.bin','rb').read()
n=len(raw)//5
STARTS=array.array('I'); STARTS.frombytes(raw[:4*n])
ISSTART=bytearray(SPAN); SIZE=bytearray(SPAN)
SIZES=array.array('B'); SIZES.frombytes(raw[4*n:])
for a,s in zip(STARTS,SIZES):
    ISSTART[a-TL]=1; SIZE[a-TL]=s

entries=array.array('I'); entries.frombytes(open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_entries.bin','rb').read())
E=sorted(set(entries))
print('root entries (call targets):',len(E))

# prologue sites: start-aligned push ebp; mov ebp,esp  (55 8B EC)
seg=_img[foff(TL):foff(TL)+SPAN]
prol=[]
i=0
while True:
    i=seg.find(b'\x55\x8b\xec',i)
    if i<0: break
    va=TL+i
    if ISSTART[i]: prol.append(va)
    i+=1
print('prologue sites (start-aligned):',len(prol))

# merge: add prologues not already equal to an entry
allE=sorted(set(E)|set(prol))
print('merged entry set:',len(allE))

def owner(a):
    j=bisect.bisect_right(allE,a)-1
    return allE[j] if j>=0 else None

# ---- validate against dispatch sites ----
D=json.load(open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_dispatch.json'))
own=collections.Counter()
for d in D: own[owner(d['va'])]+=1
print('dispatch sites',len(D),'distinct owners',len(own))
print('top owners',[(hex(k),v) for k,v in own.most_common(5)])
json.dump(dict(n_entries=len(allE),n_dispatch_owners=len(own)),
          open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_ownerstat.json','w'))
with open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_entries_all.bin','wb') as f:
    f.write(array.array('I',allE).tobytes())
