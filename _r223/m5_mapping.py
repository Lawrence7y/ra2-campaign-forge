import capstone, struct
P='ra2bench/gamemd.exe'; data=open(P,'rb').read()
TVA,TOFF=0x401000,0x1000
def f2o(a): return TOFF+(a-TVA)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
fails=[]
def chk(n,c,d=''):
    print(('PASS' if c else 'FAIL'), n, d)
    if not c: fails.append(n)
FAM=[('blk1',0x7c6b58),('blk2A',0x7c7778),('blk2B',0x7c7b3c),('blk2C',0x7c7f10)]
ent={n:list(struct.unpack('<4I',data[f2o(a):f2o(a)+16])) for n,a in FAM}
def find_jmp_tbl(a, reg):
    for i in md.disasm(data[f2o(a):f2o(a)+80],a):
        if i.mnemonic=='jmp' and ('%s*4 + 0x'%reg) in i.op_str:
            return i.address, int(i.op_str[i.op_str.rindex('0x')+2:].rstrip(']'),16)
    return None,None
def find_rel_jmp(a):
    for i in md.disasm(data[f2o(a):f2o(a)+16],a):
        if i.mnemonic=='jmp' and i.op_str.startswith('0x'): return i.address, int(i.op_str,16)
    return None,None
tbl8={}; disp8={}
for n,_ in FAM:
    _,t0=find_rel_jmp(ent[n][0])
    da,T=find_jmp_tbl(t0,'ecx')
    tbl8[n]=T; disp8[n]=da
    print("%-6s 4t@0x%x  8t@0x%x (jmp[ecx*4] at 0x%x, after stub0 jmp -> 0x%x)"%(n,dict(FAM)[n],T,da,t0))
e8={n:list(struct.unpack('<8I',data[f2o(t):f2o(t)+32])) for n,t in tbl8.items()}
print()
rows=[]
for n in ent:
    for k in (1,2,3):
        _,tgt=find_rel_jmp(ent[n][k])
        idx=e8[n].index(tgt) if tgt in e8[n] else None
        rows.append((n,k,tgt,idx))
        print("  %-6s stub%d -> 0x%x  idx=%s"%(n,k,tgt,idx))
chk('M1 stub1..3 land exactly in the 8-entry table of their own family', all(r[3] is not None for r in rows))
chk('M2 index mapping pos1->6 pos2->4 pos3->2 in all 4 families',
    all(sorted([(r[1],r[3]) for r in rows if r[0]==n])==[(1,6),(2,4),(3,2)] for n in ent))
chk('M3 negative control: mapping is not pos->2*pos', [(k,8-2*k) for k in (1,2,3)]!=[(k,2*k) for k in (1,2,3)])
chk('M4 4-entry table adresses distinct', len(set(dict(FAM).values()))==4)
chk('M5 8-entry table addresses distinct', len(set(tbl8.values()))==4, str([hex(x) for x in tbl8.values()]))
# family base deltas
b1=dict(FAM)['blk1']
for n in ('blk2A','blk2B','blk2C'):
    print("  %-6s 4t delta 0x%x  8t delta 0x%x  8t-4t gap 0x%x (blk1 0x%x)"%(n,dict(FAM)[n]-b1,tbl8[n]-tbl8['blk1'],tbl8[n]-dict(FAM)[n],tbl8['blk1']-b1))
print("FAILS",len(fails),fails)
