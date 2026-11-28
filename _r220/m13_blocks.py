import sys,struct
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
R=P.RAW
# 0x879b30 block structure: 16-dword blocks = [asc8, neg8]?
o=P.r2o(0x879b30)
vals=struct.unpack_from('<2000i',R,o)
blocks=[]
for b in range(0,125):
    blk=vals[b*16:(b+1)*16]
    asc=blk[:8]; neg=blk[8:]
    ok=all(neg[i]==-asc[i] for i in range(8)) and all(asc[i]<asc[i+1] for i in range(7))
    blocks.append((b,ok,asc))
print("blocks ok:",sum(1 for b in blocks if b[1]),"of 125")
for b in blocks[:10]: print(b[0],b[1],b[2])
print("...")
for b in blocks[120:125]: print(b[0],b[1],b[2])
# find first failing block
fb=[b for b in blocks if not b[1]][:3]
print("first failing:",fb)
# 0x87bd90 extent: 256 bytes constant rows?
o3=P.r2o(0x87bd90)
ok=all(R[o3+r*16+c]==2*r for r in range(16) for c in range(16))
print("bd90 16x16 rows value=2*row:",ok, "next byte after 256:",R[o3+256:o3+272].hex())
# audio constants scan near tables: 22050/44100/11025
for v in (22050,44100,11025,8000,32000,48000):
    pat=struct.pack('<I',v); hits=[]
    st=0
    while True:
        k=R.find(pat,st)
        if k<0: break
        hits.append(k); st=k+1
        if len(hits)>5: break
    print("const",v,"file offsets",[hex(x) for x in hits[:5]])
