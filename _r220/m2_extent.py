import sys,struct,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
R=P.RAW
o=P.r2o(0x87b170)
w=list(struct.unpack_from('<1288H',R,o))
# pattern per record: [a,a,a,a,a+64,a+128,a+192,a+256]
recs=[w[i*8:(i+1)*8] for i in range(161)]
ok=[]
for i,r in enumerate(recs):
    a=r[0]; good = all(r[j]==a for j in range(4)) and r[4]==a+64 and r[5]==a+128 and r[6]==a+192 and r[7]==a+256
    ok.append((i,a,good))
bad=[x for x in ok if not x[2]]
print("records",len(recs),"pattern_fail",len(bad),bad[:5])
print("a sequence first 20:",[x[1] for x in ok[:20]])
print("a sequence last 10:",[x[1] for x in ok[-10:]])
# relation a vs index
rels=set()
for i,a,g in ok:
    rels.add((a - 32*(i//2)))
print("a==32*(i//2) residual set:",sorted(rels)[:6])
# how far does the pattern continue past 2576?
o2=o+2576
extra=0
i=161
while True:
    base=o2+extra
    if base+16>len(R): break
    r=struct.unpack_from('<8H',R,base)
    a=r[0]
    if not (all(r[j]==a for j in range(4)) and r[4]==a+64 and r[5]==a+128 and r[6]==a+192 and r[7]==a+256): break
    if a != 32*(i//2): break
    extra+=16; i+=1
print("continuation bytes after 2576:",extra,"records total:",161+extra//16)
# where does region start/end (raw bytes before 0x87b170 and after)
prev=R[o-16:o]; print("prev16:",prev.hex())
end=o+2576+extra
print("after table:",R[end:end+32].hex())
# twin table extent: 0x879b30
o3=P.r2o(0x879b30)
dws=struct.unpack_from('<700I',R,o3)
# find where pattern breaks: pairs where |value| <= 0x1000 and odd/even structure
print("twin first 8 pairs:",[ (dws[2*i],dws[2*i+1]) for i in range(8)])
# search table start: bytes before
print("twin prev16:",R[o3-16:o3].hex())
print("twin after 2576:",R[o3+2576:o3+2576+32].hex())
json.dump({'records':161,'extra_bytes':extra,'total_records':161+extra//16,
 'a_residual':sorted(rels)},open('_r220/m2.json','w'),indent=1)
