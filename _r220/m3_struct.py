import sys,struct,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
R=P.RAW
o=P.r2o(0x87b170)
w=list(struct.unpack_from('<1288H',R,o))
print("total words",len(w))
print("first 96 words:",w[:96])
# find period p (2..8) such that w[i] - w[i-p] is constant-ish
best=[]
for p in range(1,9):
    d=[w[i]-w[i-p] for i in range(p,len(w))]
    ds=sorted(set(d))
    best.append((p,len(ds),ds[:8],max(ds),min(ds)))
for b in best: print("period",b[0],"ndistinct diffs",b[1],b[2],"max",b[3],"min",b[4])
# monotonic check
nondec=sum(1 for i in range(1,len(w)) if w[i]>=w[i-1])
print("nondecreasing steps",nondec,"of",len(w)-1)
# distinct values count
print("distinct values",len(set(w)),"min",min(w),"max",max(w))
# difference histogram
from collections import Counter
c=Counter(w[i]-w[i-1] for i in range(1,len(w)))
print("diff hist top12",c.most_common(12))
# Interleaved reading: maybe 4 lanes of 322 words
for lanes in (2,4,8):
    n=len(w)//lanes
    seqs=[w[i*lanes:(i+1)*lanes] for i in range(n)][:2]
    print("lanes",lanes,"first records",seqs)
# check: does w[i] == 32*floor(i/8) + something
res=Counter(w[i]-32*(i//8) for i in range(len(w)))
print("residual w[i]-32*(i//8) top8",res.most_common(8))
res2=Counter(w[i]-32*((i//8)//2) for i in range(len(w)))
print("residual w[i]-32*((i//8)//2) top8",res2.most_common(8))
# per-record word0 sequence and word4 sequence
print("rec word0:",[w[i*8] for i in range(24)])
print("rec word4:",[w[i*8+4] for i in range(24)])
print("rec word1:",[w[i*8+1] for i in range(24)])
json.dump({'words':w},open('_r220/m3.json','w'))
