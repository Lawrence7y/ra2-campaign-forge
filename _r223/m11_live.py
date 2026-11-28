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
# all rel32 edges
E={}
i=0;n=len(buf)
while i<n-4:
    b=buf[i]
    if b in (0xE8,0xE9):
        src=TVA+i; tgt=(src+5+struct.unpack('<i',buf[i+1:i+5])[0])&0xffffffff
        E.setdefault(src,[]).append((tgt,'call' if b==0xE8 else 'jmp')); i+=5; continue
    i+=1
print("call/jmp sites in .text:",len(E))
# also indirect jmp [reg*4+tbl] targets inside cluster: treat table members as reachable from the disp instruction
IND={}
for i in md.disasm(data[f2o(0x7c6000):f2o(0x7c8000)],0x7c6000):
    if i.mnemonic=='jmp' and '*4 + 0x' in i.op_str:
        t=int(i.op_str[i.op_str.rindex('0x')+2:].rstrip(']'),16)
        IND[i.address]=(t, list(struct.unpack('<8I',data[f2o(t):f2o(t)+32])))
print("indirect jmp tables in cluster:", {hex(k):hex(v[0]) for k,v in IND.items()})
BAND=(0x7c6000,0x7c8000)
def inband(a): return BAND[0]<=a<BAND[1]
# roots: call sites outside the band targeting inside
roots=set()
for s,ts in E.items():
    if inband(s): continue
    for t,k in ts:
        if inband(t): roots.add(t)
print("external entries into band:", [hex(x) for x in sorted(roots)])
seen=set(roots); st=list(roots)
while st:
    a=st.pop()
    # follow rel edges from within a's function body conservatively: only from address a itself
    for t,k in E.get(a,[]):
        if inband(t) and t not in seen: seen.add(t); st.append(t)
    if a in IND:
        for t in IND[a][1]:
            if inband(t) and t not in seen: seen.add(t); st.append(t)
print("closure over call/jmp-from-entry:", len(seen), sorted(hex(x) for x in seen)[:20])
# a broader closure: any rel edge whose source is inside the band and whose source is already reachable-adjacent
def closure(seed, iters=40):
    seen=set(seed); st=list(seed)
    for _ in range(iters):
        new=False
        for s,ts in E.items():
            if not inband(s): continue
            if s in seen or any((t in seen) for t,k in ts):
                pass
        # simpler: propagate along edges whose source's *function* contains a reachable address
        for s,ts in list(E.items()):
            if not inband(s): continue
            if s in seen:
                for t,k in ts:
                    if inband(t) and t not in seen: seen.add(t); st.append(t); new=True
            if s in IND:
                for t in IND[s][1]:
                    if inband(t) and t not in seen: seen.add(t); st.append(t); new=True
        if not new: break
    return seen
S=closure(roots)
print("closure v2 (source must be reachable):", len(S))
KEY={'0x7c6270':'reset8(blk1+blk2?)','0x7c62ac':'unpacker','0x7c6620':'gridchk','0x7c6730':'reset4',
 '0x7c6752':'blk1_disp','0x7c6808':'blk1_dec','0x7c6981':'blk1_nibble_head','0x7c6a8c':'blk1_stub3tgt',
 '0x7c7371':'blk2_disp','0x7c7428':'blk2_dec','0x7c77f0':'blk2_dec2','0x7c7bc0':'blk2_dec3','0x7c7350':'stateclear'}
print()
for k,v in KEY.items():
    a=int(k,16)
    print("  %-8s %-18s in closure=%s"%(k,v,a in S))
chk('L1 blk2_disp 0x7c7371 live', 0x7c7371 in S)
chk('L2 blk1_disp 0x7c6752 dead (not reachable)', 0x7c6752 not in S)
chk('L3 blk1_dec 0x7c6808 dead', 0x7c6808 not in S)
chk('L4 0x7c6620 dead', 0x7c6620 not in S)
chk('L5 0x7c62ac dead', 0x7c62ac not in S)
chk('L6 stateclear 0x7c7350 live', 0x7c7350 in S)
print("FAILS",len(fails),fails)
