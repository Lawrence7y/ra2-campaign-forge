import sys,json,struct
from collections import Counter
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
R=P.RAW
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=False; md.skipdata=True
seg=P.B['.text']; lo=seg['lo']; rp=seg['rawptr']; rs=seg['rawsize']
# 1. callers of 0x7c7371 (E8 sweep already done in m5.json) -> sites
j=json.load(open('_r220/m5.json'))
# recompute sites for 0x7c7371 and 0x7c7350
def sweep():
    pos=rp; end=rp+rs; hits={}
    while pos<end:
        got=False
        for ins in md.disasm_lite(R[pos:pos+16], lo+(pos-rp)):
            got=True
            if ins[2]=='call':
                try: t=int(ins[3],16)
                except: t=None
                if t in (0x7c7371,0x7c7350,0x7c8d20): hits.setdefault(t,[]).append(ins[0])
            break
        pos += ins[1] if got else 1
    return hits
hits=sweep()
print("call sites:",{hex(k):[hex(x) for x in v] for k,v in hits.items()})
# 2. bytes at 0x87bd90
o=P.r2o(0x87bd90); print("0x87bd90 bytes:",R[o:o+64].hex())
# 3. what is right after the twin table 0x879b30 + its extent? scan for structure break
o=P.r2o(0x879b30)
dw=list(struct.unpack_from('<700I',R,o))
# signed
sd=[x-0x100000000 if x>=0x80000000 else x for x in dw]
print("0x879b30 signed first 40:",sd[:40])
# detect block boundaries: each block of 16 dwords? find where |value|>0x10000
big=[i for i,v in enumerate(sd) if abs(v)>0x2000]
print("first index with |v|>0x2000:",big[:5])
# 4. strings near .rdata referencing jpeg/IDCT? search raw for 'JPEG','IJG','idct'
for pat in (b'JPEG',b'jpeg',b'IJG',b'IDCT',b'idct',b'DCT'):
    idx=[]; s=0
    while True:
        k=R.find(pat,s)
        if k<0: break
        idx.append(k); s=k+1
        if len(idx)>6: break
    print(pat, [hex(k) for k in idx[:6]])
# 5. dataref: which funcs referenced between 0x7c7000-0x7c9000 (functions boundaries via CC pairs) -> just count CC-delimited funcs
fns=[]; i=rp
while i<rp+rs-2:
    if R[i]==0xCC and R[i+1]==0xCC:
        k=i+2
        while k<rp+rs-2 and R[k]==0xCC: k+=1
        fns.append(lo+(k-rp)); i=k
    else: i+=1
near=[hex(f) for f in fns if 0x7c7000<=f<0x7c9100]
print("function starts 0x7c7000..0x7c9100:",near)
json.dump({'callsites':{hex(k):[hex(x) for x in v] for k,v in hits.items()},
           'fns_near':near,'bd90':R[o:o+64].hex()},open('_r220/m7.json','w'),indent=1)
