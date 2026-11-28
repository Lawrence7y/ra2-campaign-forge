import capstone, struct
P='ra2bench/gamemd.exe'; data=open(P,'rb').read()
TVA,TOFF,TRSZ=0x401000,0x1000,0x3e0000
buf=data[TOFF:TOFF+TRSZ]
def f2o(a): return TOFF+(a-TVA)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=False
fails=[]
def chk(n,c,d=''):
    print(('PASS' if c else 'FAIL'), n, d)
    if not c: fails.append(n)

# build rel32 caller map for whole .text once
rel={}
i=0; n=len(buf)
while i < n-4:
    b=buf[i]
    if b in (0xE8,0xE9):
        src=TVA+i
        tgt=(src+5+struct.unpack('<i',buf[i+1:i+5])[0])&0xffffffff
        rel.setdefault(tgt,[]).append((src, 'call' if b==0xE8 else 'jmp'))
        i+=5; continue
    i+=1
print("rel32 edges:", sum(len(v) for v in rel.values()))

CLUSTER={'0x7c6270':'reset8','0x7c62ac':'unpacker','0x7c6620':'gridchk','0x7c6730':'reset4',
 '0x7c6752':'blk1_dispatch','0x7c6808':'blk1_dec','0x7c6b38':'blk1_tbl8','0x7c6b58':'blk1_tbl4',
 '0x7c7371':'blk2_dispatch','0x7c7428':'blk2_dec','0x7c77f0':'blk2_dec_unroll2','0x7c7bc0':'blk2_dec_unroll3',
 '0x7c7350':'stateclear'}
print()
print("=== direct rel32 callers (call only) of cluster entries ===")
for name,label in CLUSTER.items():
    a=int(name,16)
    cs=[ (hex(s),k) for s,k in rel.get(a,[])]
    calls=[x for x,k in rel.get(a,[]) if k=='call']
    chk('R-'+label+' kind', True, "call=%d jmp=%d sites=%s"%(len(calls), len(rel.get(a,[]))-len(calls), cs[:6]))
print()
# dword literal refs
print("=== dword literal refs ===")
for name,label in CLUSTER.items():
    a=int(name,16); print("  %-8s %s dword_occ=%d"%(name,label,data.count(struct.pack('<I',a))))
print()
# reachability from live entry 0x7c7371 within cluster (call edges only)
def reach(start):
    seen=set([start]); st=[start]
    while st:
        a=st.pop()
        for s,k in rel.get(a,[]):
            if k=='call' and s not in seen:
                seen.add(s); st.append(s)
    return seen
r=reach(0x7c7371)
def inrange(x): return 0x7c2000<=x<0x7c8000
print("reachable-from-0x7c7371 (call edges) count:",len(r))
for name,label in CLUSTER.items():
    a=int(name,16)
    print("  %-8s %-16s reachable=%s"%(name,label,a in r))
chk('R1 blk1 dispatcher 0x7c6752 unreachable from 0x7c7371', 0x7c6752 not in r)
chk('R2 blk1 dec 0x7c6808 unreachable from 0x7c7371', 0x7c6808 not in r)
chk('R3 0x7c6752 has zero call callers overall', not [x for x in rel.get(0x7c6752,[]) if x[1]=='call'])
chk('R4 0x7c6752 has zero jmp callers overall', not rel.get(0x7c6752,[]))
chk('R5 0x7c6808 zero call callers', not [x for x in rel.get(0x7c6808,[]) if x[1]=='call'])
print("   0x7c6808 all refs:",[(hex(s),k) for s,k in rel.get(0x7c6808,[])][:10])
print("FAILS",len(fails),fails)
