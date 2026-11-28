import sys,struct,hashlib,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
R=P.RAW
def h(va,n):
    o=P.r2o(va); return hashlib.sha256(R[o:o+n]).hexdigest()
out={}
A,B_=0x876ff4,0x87b170
out['sha_A']=h(A,2576); out['sha_B']=h(B_,2576)
out['same_bytes']= (P.r2o(A) is not None and R[P.r2o(A):P.r2o(A)+2576]==R[P.r2o(B_):P.r2o(B_)+2576])
# next 16 bytes after each
out['after_A']=R[P.r2o(A)+2576:P.r2o(A)+2592].hex()
out['after_B']=R[P.r2o(B_)+2576:P.r2o(B_)+2592].hex()
# words
o=P.r2o(B_)
w=list(struct.unpack_from('<1288H',R,o))
out['words48']=w[:48]
# period 8 words check + diffs
per={}
for comp in range(8):
    seq=[w[i*8+comp] for i in range(161)]
    d=sorted(set(seq[i+1]-seq[i] for i in range(len(seq)-1)))
    per[comp]={'first':seq[:6],'diffs':d[:12],'ndistinct':len(d),'last':seq[-1]}
out['per_word_component']=per
# dwords
out['dwords12']=['%08x'%x for x in struct.unpack_from('<12I',R,o)]
# twin table 0x879b30
o2=P.r2o(0x879b30)
dw2=list(struct.unpack_from('<64I',R,o2))
out['twin64']=['%08x'%x for x in dw2]
# hypotheses
twin_bytes=R[o2:o2+2576]
w2=list(struct.unpack_from('<1288H',R,o2))
hits={}
hits['H1_dword==word<<16']=sum(1 for i in range(64) if dw2[i]==(w2[i]<<16))
hits['H2_dword==word<<8']=sum(1 for i in range(64) if dw2[i]==(w2[i]<<8))
hits['H3_dword==word']=sum(1 for i in range(64) if dw2[i]==w2[i])
hits['H4_twinbytes==Bbytes']=1 if twin_bytes==R[P.r2o(B_):P.r2o(B_)+2576] else 0
out['twin_hyp']=hits
out['twin_firstwords']=w2[:24]
json.dump(out,open('/home/t628/projects/ra2-campaign-forge/_r220/m1.json','w'),indent=1)
print(json.dumps({k:v for k,v in out.items() if k in ('sha_A','sha_B','same_bytes','after_A','after_B','twin_hyp','dwords12','twin64')},indent=1))
print("words48",out['words48'])
print("per comp:")
for c,v in per.items(): print(' ',c,v['first'],'ndistinct',v['ndistinct'],'diffs',v['diffs'],'last',v['last'])
print("twin words24",out['twin_firstwords'])
