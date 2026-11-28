import capstone, struct
P='ra2bench/gamemd.exe'; data=open(P,'rb').read()
TVA,TOFF=0x401000,0x1000
def f2o(a): return TOFF+(a-TVA)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=False
fails=[]
def chk(n,c,d=''):
    print(('PASS' if c else 'FAIL'), n, d)
    if not c: fails.append(n)
TAB=[('blk1',0x7c6b58),('blk2A',0x7c7778),('blk2B',0x7c7b3c),('blk2C',0x7c7f10)]
ent={n:list(struct.unpack('<4I',data[f2o(a):f2o(a)+16])) for n,a in TAB}
# stub-extent: from entry start to next entry start (or first entry of next region)
def span(n,k):
    v=ent[n]
    if k<3: return v[k+1]-v[k]
    # last entry: extend until int3 padding run or a jmp rel32 end
    a=v[k]; o=f2o(a)
    L=list(md.disasm(data[o:o+32],a))
    total=0
    for i in L:
        total+=i.size
        if i.mnemonic=='jmp' and i.op_str.startswith('0x'): break
    return total
print("=== stub spans (entry k start -> next entry start) ===")
for n in ent:
    print(n, [hex(ent[n][k]) for k in range(4)], "spans", [span(n,k) for k in range(4)])
sp={n:[span(n,k) for k in range(4)] for n in ent}
chk('U1 blk1 spans == blk2B/2C spans', sp['blk1']==sp['blk2B']==sp['blk2C'], str(sp))
chk('U2 blk2A spans = blk1 spans + 1 for all k', [a+1 for a in sp['blk1']]==sp['blk2A'], str(sp['blk2A']))
print()
# raw bytes per stub, with rel32/table-disp32 masked
def stub_bytes(n,k):
    a=ent[n][k]; L=list(md.disasm(data[f2o(a):f2o(a)+32],a)); out=bytearray()
    for i in L:
        b=bytearray(i.bytes)
        if i.mnemonic=='jmp' and i.op_str.startswith('0x'):
            b[1:5]=b'\x00'*4
        if 'ebx*4 + 0x' in i.op_str:
            b[4:8]=b'\x00'*4
        # also mask the jmp dword pointer bytes: pattern ff 24 9d <disp32>
        out+=b
        if i.mnemonic=='jmp' and i.op_str.startswith('0x'): break
    return bytes(out)
print("=== byte-level stub compare (rel32 + table disp masked) ===")
for nm in ('blk2A','blk2B','blk2C'):
    for k in range(4):
        x=stub_bytes('blk1',k); y=stub_bytes(nm,k)
        ok = x==y
        print("  blk1 vs %s k=%d len %d/%d equal=%s"%(nm,k,len(x),len(y),ok))
        if not ok:
            print("     blk1:",x.hex())
            print("     %s  :"%nm,y.hex())
print()
# nop padding check between stubs
for n in ('blk1','blk2A'):
    pads=[]
    for k in range(3):
        a=ent[n][k]; L=list(md.disasm(data[f2o(a):f2o(a)+32],a)); tot=0; last=None
        for i in L:
            tot+=i.size; last=i
            if i.mnemonic=='jmp' and i.op_str.startswith('0x'): break
        gap=ent[n][k+1]-(a+tot)
        pads.append((hex(a+tot),gap,data[f2o(a+tot):f2o(ent[n][k+1])].hex()))
    print(n,"pad after each stub:",pads)
print()
# 8-entry nibble tables
T8={'blk1_8':0x7c6b38,'blk2_8':0x7c7758}
e8={n:list(struct.unpack('<8I',data[f2o(a):f2o(a)+32])) for n,a in T8.items()}
for n in e8: print(n,[hex(x) for x in e8[n]])
d=[e8['blk2_8'][i]-e8['blk1_8'][i] for i in range(8)]
print("per-entry delta:",[hex(x) for x in d])
chk('U3 8-entry table deltas all 0xc20', set(d)=={0xc20}, str([hex(x) for x in d]))
d4=[[ent[nm][k]-ent['blk1'][k] for k in range(4)] for nm in ('blk2A','blk2B','blk2C')]
print("4-entry table deltas:",[[hex(x) for x in row] for row in d4])
chk('U4 4-entry table deltas all 0xc1f', all(set(row)=={0xc1f} for row in d4), str([[hex(x) for x in r] for r in d4]))
chk('U5 8-entry delta 0xc20 != 4-entry delta 0xc1f (1-byte nop padding)', 0xc20!=0xc1f)
print("FAILS",len(fails),fails)
