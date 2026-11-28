import capstone, struct
P='ra2bench/gamemd.exe'; data=open(P,'rb').read()
TVA,TOFF,TRSZ=0x401000,0x1000,0x3e0000
buf=data[TOFF:TOFF+TRSZ]
def f2o(a): return TOFF+(a-TVA)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=False; md.skipdata=True
fails=[]
def chk(n,c,d=''):
    print(('PASS' if c else 'FAIL'), n, d)
    if not c: fails.append(n)
# 1) rel32 edges from whole .text
edges=[]
i=0;n=len(buf)
while i<n-4:
    b=buf[i]
    if b in (0xE8,0xE9):
        src=TVA+i; tgt=(src+5+struct.unpack('<i',buf[i+1:i+5])[0])&0xffffffff
        edges.append((src,tgt,'call' if b==0xE8 else 'jmp')); i+=5; continue
    i+=1
print("rel32 edges:",len(edges))
# 2) indirect jmp tables: source -> member set
ind={}
for i in md.disasm(data[f2o(0x7c6000):f2o(0x7c8000)],0x7c6000):
    if i.mnemonic=='jmp' and '*4 + 0x' in i.op_str:
        t=int(i.op_str[i.op_str.rindex('0x')+2:].rstrip(']'),16)
        ind[i.address]=(t, list(struct.unpack('<8I',data[f2o(t):f2o(t)+32])))
# 3) dword pointers anywhere in image
SEC=[('text',0x401000,0x1000,0x3e0000),('rdata',0x7e1000,0x3e1000,0x31000),
     ('data',0x812000,0x412000,0x6c000),('rsrc',0xb7a000,0x47e000,0x19000),('detour',0xb93000,0x497000,0x3000)]
ptr={}
for nm,va,off,rsz in SEC:
    for k in range(rsz//4):
        v=struct.unpack('<I',data[off+4*k:off+4*k+4])[0]
        if 0x401000<=v<0x7e1000: ptr.setdefault(v,[]).append((nm,va+4*k))
GROUPS=[('blk1_family',0x7c6752,0x7c6b68,'entry 0x7c6752 (dispatcher)'),
        ('blk2_family',0x7c7371,0x7c7f20,'entry 0x7c7371 (dispatcher)'),
        ('gridchk',0x7c6620,0x7c672a,'entry 0x7c6620'),
        ('unpacker',0x7c62ac,0x7c6613,'entry 0x7c62ac'),
        ('reset8',0x7c6270,0x7c62ac,'entry 0x7c6270'),
        ('reset4',0x7c6730,0x7c6752,'entry 0x7c6730'),
        ('stateclear',0x7c7350,0x7c7371,'entry 0x7c7350')]
print()
print("=== incoming reference audit per group [lo,hi) ===")
for name,lo,hi,desc in GROUPS:
    inc_rel=[(hex(s),k,hex(t)) for s,t,k in edges if lo<=t<hi and not (lo<=s<hi)]
    inc_ind=[(hex(s),hex(t)) for s,(t,mem) in ind.items() if any(lo<=m<hi for m in mem) and not (lo<=s<hi)]
    inc_ptr=[(x[0],hex(x[1]),hex(v)) for v in range(lo,hi) for x in ptr.get(v,[]) if not (lo<=x[1]<hi)]
    out_rel=[(hex(s),k,hex(t)) for s,t,k in edges if lo<=s<hi and not (lo<=t<hi)]
    print("  %-11s [0x%x,0x%x)"%(name,lo,hi))
    print("     incoming rel32 : %s"%inc_rel)
    print("     incoming ind   : %s"%inc_ind)
    print("     incoming dword : %s"%inc_ptr)
    print("     outgoing rel32 : %s"%[x for x in out_rel][:12])
    if name in ('blk1_family','gridchk','unpacker','reset8','reset4'):
        chk('X-%s has zero incoming reference (dead)'%name, not inc_rel and not inc_ind and not inc_ptr)
    if name=='blk2_family':
        chk('X-blk2 incoming = exactly 2 calls from 0x7c24a2/0x7c2557',
            sorted(x[0] for x in inc_rel)==['0x7c24a2','0x7c2557'], str(inc_rel))
    if name=='stateclear':
        chk('X-stateclear incoming = 1 call from 0x7c2a74', [x[0] for x in inc_rel]==['0x7c2a74'], str(inc_rel))
print()
print("=== function-boundary proof: each group entry is preceded by ret/int3/nop, never fallthrough ===")
for name,lo,hi,desc in GROUPS:
    o=f2o(lo)
    prev=data[o-1]
    # scan back over int3/nop padding
    pad=0; p=o-1
    while data[p] in (0xcc,0x90) and p>0: pad+=1; p-=1
    print("  %-11s entry 0x%x  prev_byte=0x%02x  padding_run=%d  byte_before_pad=0x%02x"%(name,lo,prev,pad,data[p]))
    chk('B-%s entry not reachable by fallthrough (prev is ret 0xc3/0xc2 or padding run)'%name,
        data[p] in (0xc3,0xc2) or pad>0, "0x%02x pad=%d"%(data[p],pad))
print("FAILS",len(fails),fails)
