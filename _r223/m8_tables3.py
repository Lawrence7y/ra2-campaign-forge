import capstone, struct
P='ra2bench/gamemd.exe'; data=open(P,'rb').read()
TVA,TOFF=0x401000,0x1000
def f2o(a): return TOFF+(a-TVA)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=False
fails=[]
def chk(n,c,d=''):
    print(('PASS' if c else 'FAIL'), n, d)
    if not c: fails.append(n)
FAM=[('blk1',0x7c6b58,0x7c6b38,0x7c6808),('blk2A',0x7c7778,0x7c7758,0x7c7428),
     ('blk2B',0x7c7b3c,0x7c7b1c,0x7c77f0),('blk2C',0x7c7f10,0x7c7ef0,0x7c7bc0)]
ent={n:list(struct.unpack('<4I',data[f2o(t4):f2o(t4)+16])) for n,t4,t8,dec in FAM}
# stub = all instrs of the entry up to and including the terminating jmp (rel or jmp [reg*4+tbl])
def stub_instrs(a):
    out=[]
    for i in md.disasm(data[f2o(a):f2o(a)+32],a):
        out.append(i)
        if i.mnemonic=='jmp': break
    return out
def stub_mask(n,k):
    a=ent[n][k]; out=bytearray()
    for i in stub_instrs(a):
        b=bytearray(i.bytes)
        if 'ebx*4 + 0x' in i.op_str: b[4:8]=b'\x00'*4
        if i.mnemonic=='jmp' and i.op_str.startswith('0x'): b[1:5]=b'\x00'*4
        out+=b
    return bytes(out)
def stub_end(n,k):
    L=stub_instrs(ent[n][k]); return L[-1].address+L[-1].size
print("=== S1 stub bodies (masked) byte-equal across families ===")
ok=True
for k in range(4):
    lens=[len(stub_mask(n,k)) for n,_,_,_ in FAM]
    eq=[stub_mask(n,k)==stub_mask('blk1',k) for n,_,_,_ in FAM]
    print("  stub%d lens %s equal-to-blk1 %s"%(k,lens,eq)); ok=ok and all(eq)
chk('S1 16/16 stub bodies byte-identical (rel32 + table disp masked)', ok)
print()
print("=== S2 inter-stub padding (the only structural difference) ===")
pad={}
for n,_,_,_ in FAM:
    row=[]
    for k in (0,1,2):
        e=stub_end(n,k); nxt=ent[n][k+1]
        row.append((data[f2o(e):f2o(nxt)].hex(), nxt-e))
    pad[n]=row
    print("  %-6s"%n,row)
chk('S2.1 blk1 pads = 90 / 90 / 90', [p[0] for p in pad['blk1']]==['90','90','90'])
chk('S2.2 blk2A stub0 pad = 8bff (mov edi,edi 2B), then 90 / 90', [p[0] for p in pad['blk2A']]==['8bff','90','90'])
chk('S2.3 blk2B & blk2C stub0 pad = 8d4900 (lea ecx,[ecx+0] 3B), then 90 / 90',
    [p[0] for p in pad['blk2B']]==['8d4900','90','90'] and [p[0] for p in pad['blk2C']]==['8d4900','90','90'])
print("  pad lengths per family:", {n:[p[1] for p in pad[n]] for n,_,_,_ in FAM})
chk('S2.4 pad lengths differ across families (1/2/3 at stub0)', len({pad[n][0][1] for n,_,_,_ in FAM})==3,
    str({n:pad[n][0][1] for n,_,_,_ in FAM}))
print()
print("=== S3 table address deltas ===")
t4b=dict((n,t) for n,t,_,_ in FAM)['blk1']; t8b=dict((n,t) for n,_,t,_ in FAM)['blk1']
for n,t4,t8,dec in FAM[1:]:
    d=ent[n][0]-ent['blk1'][0]
    print("  %-6s 4t+0x%x  8t+0x%x  entry0 delta 0x%x  entry1..3 delta %s"%(n,t4-t4b,t8-t8b,d,[hex(ent[n][k]-ent['blk1'][k]) for k in (1,2,3)]))
    chk('S3.%s entry1..3 deltas == 4-table address delta'%n, [ent[n][k]-ent['blk1'][k] for k in (1,2,3)]==[t4-t4b]*3)
chk('S3.4 8-table deltas == 4-table deltas', [(t8-t8b) for n,_,t8,_ in FAM[1:]]==[(t4-t4b) for n,t4,_,_ in FAM[1:]])
chk('S3.5 8-table is exactly 0x20 before 4-table in all 4 families', all(t4-t8==0x20 for n,t4,t8,_ in FAM))
print()
print("=== S4 stub3 ends flush against the family decoder entry ===")
for n,t4,t8,dec in FAM:
    e=stub_end(n,3)
    print("  %-6s stub3 end 0x%x decoder 0x%x gap %d"%(n,e,dec,dec-e))
    chk('S4.%s stub3 end + 1 == decoder entry'%n, dec-e==1, "%d"% (dec-e))
print()
print("=== S5 negative controls ===")
chk('S5.1 dropping the table-disp mask would break equality', any(
    data[f2o(ent['blk1'][0]):f2o(ent['blk1'][0])+13]!=data[f2o(ent['blk2A'][0]):f2o(ent['blk2A'][0])+13] for _ in (0,)))
chk('S5.2 stub0 ends with jmp dword ptr [ebx*4+tbl] (not a rel jmp)', 
    stub_instrs(ent['blk1'][0])[-1].mnemonic=='jmp' and 'ebx*4' in stub_instrs(ent['blk1'][0])[-1].op_str)
chk('S5.3 stub1..3 end with rel jmp into the 8-entry table members',
    all(stub_instrs(ent[n][k])[-1].op_str.startswith('0x') for n,_,_,_ in FAM for k in (1,2,3)))
print("FAILS",len(fails),fails)
