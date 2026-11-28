import sys,struct
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
R=P.RAW
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=False; md.skipdata=True
def dis(a,n=14):
    o=P.r2o(a); out=[]
    for i in md.disasm_lite(R[o:o+n*8], a):
        out.append((hex(i[0]),i[2],i[3]))
        if len(out)>=n: break
    return out
for s in (0x7c63b0,0x7c64b0,0x7c65d0):
    print("---",hex(s))
    for t in dis(s,12): print("   ",t)
# function starts near 0x7c6300..0x7c6700 (CC based)
rp=P.B['.text']['rawptr']; lo=P.B['.text']['lo']; rs=P.B['.text']['rawsize']
i=rp
while i<rp+rs-2:
    if R[i]==0xCC and R[i+1]==0xCC:
        k=i+2
        while k<rp+rs-2 and R[k]==0xCC: k+=1
        va=lo+(k-rp)
        if 0x7c6000<=va<0x7c6a00: print("fn start",hex(va))
        i=k
    else: i+=1
# strings: search .rdata/.data for audio-related
for pat in (b'ADPCM',b'adpcm',b'audio',b'AUDIO',b'sound',b'SOUND',b'audio.bag',b'.wav',b'.aud'):
    st=0; hits=[]
    while True:
        k=R.find(pat,st)
        if k<0: break
        hits.append(k); st=k+1
        if len(hits)>4: break
    print(pat,[hex(x) for x in hits[:4]])
