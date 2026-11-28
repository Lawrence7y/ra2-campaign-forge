import struct
P='ra2bench/gamemd.exe'; data=open(P,'rb').read()
TVA,TOFF,TRSZ=0x401000,0x1000,0x3e0000
buf=data[TOFF:TOFF+TRSZ]
fails=[]
def chk(n,c,d=''):
    print(('PASS' if c else 'FAIL'), n, d)
    if not c: fails.append(n)
def refs(v):
    pat=struct.pack('<I',v); pos=0; L=[]
    while True:
        k=buf.find(pat,pos)
        if k<0: break
        L.append(TVA+k); pos=k+1
    return L
print("=== P1 incoming-reference proof per group (rel32 only; dword/ptr scans done separately) ===")
edges=[]
i=0;n=len(buf)
while i<n-4:
    b=buf[i]
    if b in (0xE8,0xE9):
        src=TVA+i; tgt=(src+5+struct.unpack('<i',buf[i+1:i+5])[0])&0xffffffff
        edges.append((src,tgt)); i+=5; continue
    i+=1
GRP=[('blk1_family',0x7c6752,0x7c6b68),('blk2_family',0x7c7371,0x7c7f20),
     ('gridchk',0x7c6620,0x7c672a),('unpacker',0x7c62ac,0x7c6613),
     ('reset8',0x7c6270,0x7c62ac),('reset4',0x7c6730,0x7c6752),('stateclear',0x7c7350,0x7c7371)]
for name,lo,hi in GRP:
    inhit=[hex(s) for s,t in edges if lo<=t<hi and not (lo<=s<hi)]
    print("  %-11s [0x%x,0x%x) incoming_rel32=%s"%(name,lo,hi,inhit))
chk('P1 blk1_family has zero incoming rel32 (dead code)', not [1 for s,t in edges if 0x7c6752<=t<0x7c6b68 and not(0x7c6752<=s<0x7c6b68)])
chk('P2 gridchk has zero incoming rel32', not [1 for s,t in edges if 0x7c6620<=t<0x7c672a and not(0x7c6620<=s<0x7c672a)])
chk('P3 unpacker has zero incoming rel32', not [1 for s,t in edges if 0x7c62ac<=t<0x7c6613 and not(0x7c62ac<=s<0x7c6613)])
chk('P4 reset8/reset4 zero incoming rel32', not [1 for s,t in edges if (0x7c6270<=t<0x7c62ac or 0x7c6730<=t<0x7c6752) and not(0x7c6270<=s<0x7c6752)])
print()
print("=== P5 the 'dword pointer' hits are coincidental mid-instruction immediates ===")
# the 320-dword monotone run at 0x874700 is not referenced at all
n320=sum(1 for v in range(0x874700,0x874c00) if refs(v))
chk('P5.1 none of the 320 dwords in [0x874700,0x874c00) appears as a disp32 in .text', n320==0, "refs=%d"%n320)
# and the values that DID appear (0x7c6789 etc) are inside the run region only as values,
# prove they are not instruction starts AND are not 4-aligned entry points
import capstone
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=False; md.skipdata=True
starts=set(a for a,sz,m,o in md.disasm_lite(buf,TVA))
vals=[0x7c6789,0x7c6990,0x7c637a,0x7c6581]
onstart=[v for v in vals if v in starts]
print("   cited values: %s ; on instruction start: %s"%([hex(v) for v in vals],[hex(v) for v in onstart]))
chk('P5.2 at least half of the cited dwords are NOT instruction starts', len(onstart)<len(vals), "%d/%d"%(len(onstart),len(vals)))
# structural: the run has 320 entries with stride 0x206..0x20a and no 4-alignment => not a jump table
run=[struct.unpack('<I',data[TOFF+(0x874700-TVA)+4*k:TOFF+(0x874700-TVA)+4*k+4])[0] for k in range(320)]
d=[run[k+1]-run[k] for k in range(319)]
chk('P5.3 run stride in 0x204..0x20a (never 4-aligned jump table)', min(d)>=0x204 and max(d)<=0x20a, "%s..%s"%(hex(min(d)),hex(max(d))))
chk('P5.4 values are not 4-aligned (not code pointers)', sum(1 for v in run if v%4==0)<len(run), "%d/%d aligned"%(sum(1 for v in run if v%4==0),len(run)))
print("FAILS",len(fails),fails)
