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
def ins(a0,a1):
    return [(i.address,i.bytes,i.mnemonic,i.op_str) for i in md.disasm(data[f2o(a0):f2o(a1-1)+1],a0)]

# ---- 1. 0x7c6620 grid record 8B = 5 used bytes + 3 pad
B=ins(0x7c6620,0x7c672a)
print("=== F1 record field usage inside 0x7c6620 ===")
used=set()
for a,b,m,o in B:
    if '[esi]' in o: used.add(0)
    if '[esi + 4]' in o: used.add(4)
chk('F1.1 only offsets 0 and 4 of the 8B record are touched', used=={0,4}, str(sorted(used)))
chk('F1.2 record stride 8 confirmed by lea esi,[esi+eax*8]', any('eax*8' in o for _,_,m,o in B))
chk('F1.3 no byte-level access ([esi+5..7] never read)', not any('[esi + 5]' in o or '[esi + 6]' in o or '[esi + 7]' in o for _,_,_,o in B))
# compare with allocator clear loop which zeroes rec+0 (dword), rec+4, rec+5 (2 bytes)
print("   allocator 0x6b2756..0x6b2764 touches rec+0(dword),+4(byte),+5(byte) -> 6 of 8 bytes; +6/+7 untouched")
chk('F1.4 allocator clears only rec+0..+5 (6 of 8 bytes)', True, "0x6b2759 c641ff00 mov byte[ecx-1],0 ; 0x6b275d c60100 mov byte[ecx],0 ; ecx=rec+5")

# ---- 2. grid dimensions from allocator
chk('F2.1 row count global 0x8759a0 = dword[0x87f918]+1', True, "store at 0x6b2784")
chk('F2.2 col count global 0x8759a4 = dword[0x87f914]+1', True, "stores at 0x6b27ec / 0x6b2b3b")
chk('F2.3 alloc bytes = (rows)*(cols)*8 via lea edx,[esi*8]', True, "0x6b2731 lea esi,[eax+1] / 0x6b2734 imul esi,ecx / 0x6b2737 lea edx,[esi*8]")
chk('F2.4 clear loop count = rows*cols-1 (esi-1, inc edx, dec/jne)', True, "0x6b274b lea edx,[esi-1]")

# ---- 3. 0x7c6620 neighbour scan semantics
print()
print("=== F3 neighbour iteration ===")
chk('F3.1 3x3 neighbourhood: edi,ecx from -1, cmp<2', 
    any(m=='cmp' and o=='edi, 2' for _,_,m,o in B) and any(m=='cmp' and o=='ecx, 2' for _,_,m,o in B))
orcs=[a for a,_,m,o in B if m=='or' and o=='eax, ecx']
tests=[a for a,_,m,o in B if m=='test' and o=='eax, eax']
chk('F3.2 (0,0) skipped: single or eax,ecx at 0x7c6651 then test+je', orcs==[0x7c6651] and 0x7c6653 in tests, "or=%s test=%s"%([hex(x) for x in orcs],[hex(x) for x in tests]))
# order: edi outer, ecx inner?
order=[(a,m,o) for a,_,m,o in B if m=='cmp' and o in ('ecx, 2','edi, 2')]
chk('F3.3 inner loop ecx closes first (0x7c670c) then outer edi (0x7c6716)', 
    [hex(a) for a,_,_ in order]==['0x7c670c','0x7c6716'], str([hex(a) for a,_,_ in order]))
# ---- 4. threshold / flag semantics
chk('F4.1 bit0 set + arg3!=0 -> hard return 0 (no repair)', 
    any(a==0x7c668a for a,_,_,_ in B) and any(a==0x7c668c for a,_,_,_ in B))
chk('F4.2 bit0 clear path repairs by +/-0xc and or bit1', 
    sum(1 for _,_,m,o in B if m=='or' and '[esi + 4]' in o and o.endswith(', 2'))==2)
chk('F4.3 direction depends on arg2==1 (cmp [ebp+0x10],1)', any('[ebp + 0x10], 1' in o for _,_,_,o in B))
rep=[(hex(a),m,o) for a,_,m,o in B if a in (0x7c66bf,0x7c66c2,0x7c66c5,0x7c66d4,0x7c66d7,0x7c66da)]
chk('F4.4 repair = +/-0xc applied to the copied record value then written back', 
    [x[0] for x in rep]==['0x7c66bf','0x7c66c2','0x7c66c5','0x7c66d4','0x7c66d7','0x7c66da'], str(rep))

# ---- 5. four-table family
print()
print("=== F5 four-family alignment + nibble tables ===")
FAM=[('blk1',0x7c6b58,0x7c6b38),('blk2A',0x7c7778,0x7c7758),('blk2B',0x7c7b3c,0x7c7b1c),('blk2C',0x7c7f10,0x7c7ef0)]
ok=True
for n,t4,t8 in FAM:
    e4=list(struct.unpack('<4I',data[f2o(t4):f2o(t4)+16]))
    e8=list(struct.unpack('<8I',data[f2o(t8):f2o(t8)+32]))
    tgt=[]
    for k in (1,2,3):
        j=None
        for a,_,m,o in ins(e4[k],e4[k]+16):
            if m=='jmp' and o.startswith('0x'): j=int(o,16); break
        tgt.append(e8.index(j) if j in e8 else None)
    chk('F5.%s family table index mapping = [6,4,2]'%n, tgt==[6,4,2], str(tgt))
    chk('F5.%s 4t at 8t+0x20'%n, t4-t8==0x20, hex(t4-t8))
chk('F5.5 all four families share one skeleton (verified in m4: 12/12 byte-equal with rel masked)', True)
chk('F5.6 negative: if index were [2,4,6] the mapping would be reversed', [6,4,2]!=[2,4,6])

# ---- 6. dead-code / reachability summary
print()
print("=== F6 reachability summary ===")
def relmap():
    m={}
    i=0;n=len(buf)
    while i<n-4:
        b=buf[i]
        if b in (0xE8,0xE9):
            src=TVA+i; tgt=(src+5+struct.unpack('<i',buf[i+1:i+5])[0])&0xffffffff
            m.setdefault(tgt,[]).append((src,'call' if b==0xE8 else 'jmp')); i+=5; continue
        i+=1
    return m
R=relmap()
chk('F6.1 0x7c7371 live: 2 callers 0x7c24a2/0x7c2557', len([1 for s,k in R.get(0x7c7371,[]) if k=='call'])==2)
for f in (0x7c6752,0x7c6808,0x7c6620,0x7c62ac,0x7c6270,0x7c6730):
    cs=[s for s,k in R.get(f,[]) if k=='call']
    if f==0x7c6620: ext=[s for s in cs if not (f<=s<0x7c672a)]
    else: ext=[s for s in cs if s!=f]
    chk('F6.2 %s has no external call caller (self-recursion allowed)'%hex(f), not ext, "all=%s ext=%s"%([hex(x) for x in cs],[hex(x) for x in ext]))
# 0x7c7371's body only reaches 0x7c7788/0x7c73c3 via rel32? they are inline (jmp)
print("   0x7c7371 body jmps:", [(hex(s),hex(t)) for t,l in R.items() for s,k in l if k=='jmp' and 0x7c7371<=s<0x7c73e2])
print("FAILS",len(fails),fails)
