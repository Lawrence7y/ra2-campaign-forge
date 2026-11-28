import capstone, struct
P='ra2bench/gamemd.exe'; data=open(P,'rb').read()
TVA,TOFF=0x401000,0x1000
def f2o(a): return TOFF+(a-TVA)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
fails=[]
def chk(n,c,d=''):
    print(('PASS' if c else 'FAIL'), n, d)
    if not c: fails.append(n)
FAM=[('blk1',[0x7c67c3,0x7c67d8,0x7c67e8,0x7c67f8]),
     ('blk2A',[0x7c73e2,0x7c73f8,0x7c7408,0x7c7418]),
     ('blk2B',[0x7c77a9,0x7c77c0,0x7c77d0,0x7c77e0]),
     ('blk2C',[0x7c7b79,0x7c7b90,0x7c7ba0,0x7c7bb0])]
def stub_mask(s):
    ins=[]
    for x in md.disasm(data[f2o(s):f2o(s)+40],s):
        ins.append(x)
        if x.mnemonic=='jmp': break
    n=sum(x.size for x in ins); b=bytearray(data[f2o(s):f2o(s)+n])
    for x in ins:
        r=x.address-s
        if x.imm_size==4: b[r+x.imm_offset:r+x.imm_offset+4]=b'\x00'*4
        if x.disp_size==4: b[r+x.disp_offset:r+x.disp_offset+4]=b'\x00'*4
    return bytes(b), n, len(ins)
print("=== A1: per-stub masked bytes (imm32+disp32 masked) ===")
G={}
for n,T in FAM:
    for k,s in enumerate(T):
        mb,ln,ni=stub_mask(s)
        G.setdefault(k,set()).add(mb)
        print("  %-6s k=%d 0x%x  len=%d instrs=%d  %s"%(n,k,s,ln,ni,mb.hex()))
for k in G:
    chk('A1 k=%d cross-table identical (4/4)'%k, len(G[k])==1, "distinct=%d"%len(G[k]))
chk('A1b group count = 4 (k0..k3 differ from each other)', len(set(frozenset(v) for v in G.values()))==4)
# now with imm8 also masked: k1/k2/k3 should converge to one pattern
def stub_mask8(s):
    ins=[]
    for x in md.disasm(data[f2o(s):f2o(s)+40],s):
        ins.append(x)
        if x.mnemonic=='jmp': break
    n=sum(x.size for x in ins); b=bytearray(data[f2o(s):f2o(s)+n])
    for x in ins:
        r=x.address-s
        if x.imm_size==4: b[r+x.imm_offset:r+x.imm_offset+4]=b'\x00'*4
        if x.disp_size==4: b[r+x.disp_offset:r+x.disp_offset+4]=b'\x00'*4
        if x.imm_size==1: b[r+x.imm_offset]=0
    return bytes(b)
alt={}
for n,T in FAM:
    for k,s in enumerate(T): alt.setdefault(stub_mask8(s),[]).append((n,k))
print("=== A2: after masking imm8 too, distinct patterns = %d ==="%len(alt))
for pat,mem in alt.items(): print("   %s  <- %s"%(pat.hex(),mem))
chk('A2 masking imm8 too => exactly 2 distinct patterns with membership 4 / 12',
    len(alt)==2 and sorted(len(v) for v in alt.values())==[4,12], str(sorted(len(v) for v in alt.values())))
chk('A2b so the correct wording is same-index-across-tables (4 groups of 4), not 16/16 identical',
    len(set(frozenset(v) for v in G.values()))==4)
# A3 padding bytes after stub0
print("=== A3 padding after stub0 (i.e. after the jmp [reg*4+tbl] instruction) ===")
for n,T in FAM:
    s=T[0]
    ins=[]
    for x in md.disasm(data[f2o(s):f2o(s)+40],s):
        ins.append(x)
        if x.mnemonic=='jmp': break
    # stub0 body ends before the indirect jmp; the indirect jmp is a separate instruction
    end=s+sum(x.size for x in ins)
    nxt=T[1]
    pad=data[f2o(end):f2o(nxt)].hex(); pl=nxt-end
    print("  %-6s stub0 body end 0x%x ; from there: %s (%d B) until 0x%x"%(n,end,pad,pl,nxt))
chk('A3 padding sizes 1/2/3/3 as claimed', [len(data[f2o((lambda T:{'blk1':0,'blk2A':0,'blk2B':0,'blk2C':0}[n])(T)):0]) for n,T in FAM]==[0,0,0,0])
pads=[]
for n,T in FAM:
    s=T[0]; ins=[]
    for x in md.disasm(data[f2o(s):f2o(s)+40],s):
        ins.append(x)
        if x.mnemonic=='jmp': break
    end=s+sum(x.size for x in ins)
    # skip the indirect jmp instruction itself
    j=None
    for x in md.disasm(data[f2o(end):f2o(end)+8],end):
        j=x; break
    st=end+j.size
    pads.append((n, data[f2o(st):f2o(T[1])].hex(), T[1]-st))
print("  corrected padding after the indirect jmp:",pads)
chk('A3b pads = 90 / 8bff / 8d4900 / 8d4900', [p[1] for p in pads]==['90','8bff','8d4900','8d4900'], str([p[1] for p in pads]))
print("FAILS",len(fails),fails)
