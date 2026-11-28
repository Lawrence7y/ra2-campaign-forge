import capstone, struct
P='ra2bench/gamemd.exe'; data=open(P,'rb').read()
def f2o(a):
    if 0x401000<=a<0x401000+0x3e0000: return 0x1000+(a-0x401000)
    if 0x812000<=a<0x812000+0x6c000: return 0x412000+(a-0x812000)
def o2a(o):
    if 0x1000<=o<0x1000+0x3e0000: return 0x401000+(o-0x1000)
    if 0x412000<=o<0x412000+0x6c000: return 0x812000+(o-0x412000)
fails=[]
def chk(n,c,d=''):
    print(('PASS' if c else 'FAIL'), n, d)
    if not c: fails.append(n)
# extent of the monotone pointer run around 0x874960
lo=0x874900; hi=0x874a60
run=[]
for a in range(lo,hi,4):
    v=struct.unpack('<I',data[f2o(a):f2o(a)+4])[0]
    run.append((a,v))
# find maximal run where value is in .text and increasing
start=None; end=None
i=0
while i<len(run):
    for j in range(i,len(run)):
        a,v=run[j]
        ok = 0x401000<=v<0x7e1000 and (j==i or v>run[j-1][1])
        if not ok: break
    else: j=len(run)
    if j-i>4:
        print("monotone .text-value run: 0x%x..0x%x  entries=%d  first=0x%x last=0x%x"%(
            run[i][0], run[j-1][0], j-i, run[i][1], run[j-1][1]))
        if start is None: start,end=i,j-1
    i=max(j,i+1)
vals=[v for a,v in run[start:end+1]] if start is not None else []
d=[vals[k+1]-vals[k] for k in range(len(vals)-1)]
print("deltas:",[hex(x) for x in d])
chk('T874.1 run length >= 20 entries', len(vals)>=20, str(len(vals)))
chk('T874.2 deltas are 0x200..0x210 (constant-stride block)', all(0x200<=x<=0x210 for x in d), str(set(d)))
# are these entry addresses or mid-instruction?
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=False
# check: is each value a valid function entry (preceded by int3/ret and decodable prologue)?
ent_ok=0
for v in vals:
    o=f2o(v); prev=data[o-1]
    if prev in (0xcc,0xc3,0xc2): ent_ok+=1
print("values preceded by int3/ret byte: %d/%d"%(ent_ok,len(vals)))
chk('T874.3 these are NOT function entries (few preceded by int3/ret)', ent_ok < len(vals)*0.2, "%d/%d"%(ent_ok,len(vals)))
# reference check: any literal dword equal to 0x874960 / 0x874900 / 0x8749c0 ?
for g in (0x874900,0x874960,0x87498c,0x8749c0):
    pat=struct.pack('<I',g); pos=0; L=[]
    while True:
        k=data.find(pat,pos)
        if k<0: break
        L.append(hex(o2a(k))); pos=k+1
    print("  literal refs to 0x%x: %d %s"%(g,len(L),L[:6]))
# value coincidence test: if it were a pointer table, values should be 4-aligned entry points
print("  alignment of values mod 4:", sorted(set(v%4 for v in vals)))
chk('T874.4 values are not uniform mod 4 (=> not a pointer table)', len(set(v%4 for v in vals))>1, str(sorted(set(v%4 for v in vals))))
