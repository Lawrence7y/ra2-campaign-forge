import sys,struct,json
from collections import Counter,defaultdict
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
R=P.RAW; seg=P.B['.text']; lo=seg['lo']; rp=seg['rawptr']; rs=seg['rawsize']
o=P.r2o(0x87b170); w=list(struct.unpack_from('<1288H',R,o))
# honest per-record offsets
offs=defaultdict(Counter)
for i in range(161):
    r=w[i*8:(i+1)*8]
    # find a = mode of first 4
    for j in range(8):
        offs[j][r[j]-r[0]]+=1
for j in range(8):
    print("word%d - word0:"%j, offs[j].most_common(6))
# try alternate record size 16B still, but with a = word0 and check per-record consistency
bad=[]
for i in range(161):
    r=w[i*8:(i+1)*8]
    if not (r[0]==r[1]==r[2]==r[3]): bad.append((i,r))
print("records where w0!=w1..w3:",len(bad),bad[:6])
# so pattern of first4 holds but deltas differ; print delta sets per record index bucket
for lo_i,hi_i in ((0,10),(10,40),(40,80),(80,120),(120,161)):
    d=Counter()
    for i in range(lo_i,hi_i):
        r=w[i*8:(i+1)*8]; d[tuple(r[j]-r[0] for j in range(8))]+=1
    print("rec",lo_i,hi_i,"distinct delta-tuples",len(d),list(d)[:3])
# key: are the 161 records actually 8-word or is record 32B (16 words)?
for rw in (8,16):
    n=len(w)//rw; consist=0
    for i in range(n):
        r=w[i*rw:(i+1)*rw]
        if all(x==r[0] for x in r[:4]): consist+=1
    print("rec_words",rw,"records",n,"first4-equal records",consist)
# dump record 0..6 full 8 words and record at index 100..103
for i in (0,1,4,5,40,100,160):
    print("rec",i,w[i*8:(i+1)*8])
