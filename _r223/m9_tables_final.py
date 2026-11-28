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
def stub_instrs(a, allow_indirect=False):
    out=[]
    for i in md.disasm(data[f2o(a):f2o(a)+32],a):
        out.append(i)
        if i.mnemonic=='jmp':
            if allow_indirect and i.op_str.startswith('0x'): continue
            break
    return out
def stub_mask(n,k):
    out=bytearray()
    for i in stub_instrs(ent[n][k]):
        b=bytearray(i.bytes)
        if 'ebx*4 + 0x' in i.op_str: b[4:8]=b'\x00'*4
        if i.mnemonic=='jmp' and i.op_str.startswith('0x'): b[1:5]=b'\x00'*4
        out+=b
    return bytes(out)
def stub_end(n,k):
    L=stub_instrs(ent[n][k]); return L[-1].address+L[-1].size
def indirect_jmp_at(a):
    for i in md.disasm(data[f2o(a):f2o(a)+8],a):
        return i
def filler_after_stub0(n):
    e=stub_end(n,0); j=indirect_jmp_at(e)
    assert j.mnemonic=='jmp' and 'ebx*4' in j.op_str
    start=e+j.size; return data[f2o(start):f2o(ent[n][1])].hex(), ent[n][1]-start
print("=== S1 stub bodies (masked) byte-equal across families ===")
ok=True
for k in range(4):
    lens=[len(stub_mask(n,k)) for n,_,_,_ in FAM]
    eq=[stub_mask(n,k)==stub_mask('blk1',k) for n,_,_,_ in FAM]
    print("  stub%d lens %s equal-to-blk1 %s"%(k,lens,eq)); ok=ok and all(eq)
chk('S1 16/16 stub bodies byte-identical (rel32 + table-disp masked)', ok)
print()
print("=== S2 inter-stub padding (only structural difference) ===")
pad={}
for n,_,_,_ in FAM:
    row=[]
    row.append(filler_after_stub0(n))
    for k in (1,2):
        e=stub_end(n,k); nxt=ent[n][k+1]
        row.append((data[f2o(e):f2o(nxt)].hex(), nxt-e))
    pad[n]=row; print("  %-6s"%n,row)
chk('S2.1 blk1 pads = 90 / 90 / 90', [p[0] for p in pad['blk1']]==['90','90','90'], str(pad['blk1']))
chk('S2.2 blk2A stub0 pad = 8bff then 90 / 90', [p[0] for p in pad['blk2A']]==['8bff','90','90'], str(pad['blk2A']))
chk('S2.3 blk2B & blk2C stub0 pad = 8d4900 then 90 / 90',
    [p[0] for p in pad['blk2B']]==['8d4900','90','90'] and [p[0] for p in pad['blk2C']]==['8d4900','90','90'])
chk('S2.4 pad width at stub0 = 1 / 2 / 3 / 3 for blk1 / 2A / 2B / 2C (max 3B alignment fill)',
    {n:pad[n][0][1] for n,_,_,_ in FAM}=={'blk1':1,'blk2A':2,'blk2B':3,'blk2C':3}, str({n:pad[n][0][1] for n,_,_,_ in FAM}))
print()
print("=== S3 table address vs entry deltas (measured, no equality assumed) ===")
t4b=ent['blk1']; t4a=dict((n,t) for n,t,_,_ in FAM)['blk1']; t8a=dict((n,t) for n,_,t,_ in FAM)['blk1']
for n,t4,t8,dec in FAM[1:]:
    d=[ent[n][k]-ent['blk1'][k] for k in range(4)]
    print("  %-6s 4t+0x%x 8t+0x%x | entry deltas %s | entry_delta - table_delta = %s"%(
        n,t4-t4a,t8-t8a,[hex(x) for x in d],[hex(x-(t4-t4a)) for x in d]))
chk('S3.1 |entry delta - family table delta| <= 4 (alignment jitter only)', all(abs((ent[n][k]-ent['blk1'][k])-(t4-t4a))<=4 for n,t4,t8,dec in FAM[1:] for k in range(4)))
chk('S3.2 8-table deltas == 4-table deltas', [t8-t8a for n,_,t8,_ in FAM[1:]]==[t4-t4a for n,t4,_,_ in FAM[1:]])
chk('S3.3 8-table exactly 0x20 before the 4-table in all families', all(t4-t8==0x20 for n,t4,t8,_ in FAM))
print()
print("=== S4 stub3 ends flush before family decoder ===")
for n,t4,t8,dec in FAM:
    chk('S4.%s stub3 end +1 == decoder entry'%n, dec-stub_end(n,3)==1, "gap %d"%(dec-stub_end(n,3)))
print()
print("=== S5 negative controls ===")
chk('S5.1 unmasked stub0 bytes differ across families (mask is necessary)',
    data[f2o(ent['blk1'][0]):f2o(ent['blk1'][0])+13]!=data[f2o(ent['blk2A'][0]):f2o(ent['blk2A'][0])+13])
_j=indirect_jmp_at(stub_end('blk1',0))
chk('S5.2 instruction right after stub0 body is jmp dword ptr [ebx*4+tbl]',
    _j.mnemonic=='jmp' and 'ebx*4' in _j.op_str, _j.mnemonic+' '+_j.op_str)
chk('S5.3 stub1..3 terminate with rel jmp',
    all(stub_instrs(ent[n][k])[-1].op_str.startswith('0x') for n,_,_,_ in FAM for k in (1,2,3)))
chk('S5.4 stub0 length 13 B in all families; stub1..3 15 B', 
    all(len(stub_mask(n,0))==13 and all(len(stub_mask(n,k))==15 for k in (1,2,3)) for n,_,_,_ in FAM))
print("FAILS",len(fails),fails)
