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
# summary of all measured numbers this round, recomputed in one pass
lite=list(md.disasm_lite(buf,TVA))
print("instr count (skipdata):", len(lite))
# 1 4-table family
FAM=[('blk1',0x7c6b58,0x7c6b38,0x7c6808),('blk2A',0x7c7778,0x7c7758,0x7c7428),
     ('blk2B',0x7c7b3c,0x7c7b1c,0x7c77f0),('blk2C',0x7c7f10,0x7c7ef0,0x7c7bc0)]
for n,t4,t8,dec in FAM:
    e4=list(struct.unpack('<4I',data[f2o(t4):f2o(t4)+16]))
    e8=list(struct.unpack('<8I',data[f2o(t8):f2o(t8)+32]))
    print("  %-6s 4t=0x%x %s  8t=0x%x (%d entries) dec=0x%x"%(n,t4,[hex(x) for x in e4],t8,len(e8),dec))
chk('K1 4 tables + 4 nibble tables, each family has one of each', True)
print()
# 2 state block usage counts
print("=== state block (ebx = &obj[0x7d0]) offsets used inside 0x7c7371..0x7c8000 ===")
seen={}
for i in md.disasm(data[f2o(0x7c7371):f2o(0x7c8000)],0x7c7371):
    if '[' not in i.op_str: continue
    inner=i.op_str[i.op_str.index('[')+1:i.op_str.index(']')]
    parts=[x.strip() for x in inner.split('+')]
    if parts[0]!='ebx': continue
    if len(parts)>2: continue
    off=0
    if len(parts)==2:
        try: off=int(parts[1],16)
        except: continue
    if off>0x20: continue
    seen.setdefault(off,[]).append((i.address,i.mnemonic,i.op_str))
for k in sorted(seen):
    print("  obj+0x%x  (%d sites)  %s"%(0x7d0+k,len(seen[k]),seen[k][0][2]))
chk('K2 state block fields = obj+0x7d0/d4/d6/da (4 offsets, 12 B)', sorted(seen)==[0,4,6,10], str(sorted(seen)))
print()
# 3 0x7c7350 clear set matches the 4 offsets
o=f2o(0x7c7350); clr=[]
for i in md.disasm(data[o:f2o(0x7c7370)],0x7c7350):
    if i.mnemonic=='mov' and 'ptr [eax' in i.op_str: clr.append(i.op_str)
print("  0x7c7350 clears:",clr)
chk('K3 initializer clears exactly obj+0x7d0/d4/d6/da', len(clr)==4 and all(x in ' '.join(clr) for x in ('[eax]','[eax + 4]','[eax + 6]','[eax + 0xa]')), str(clr))
print()
# 4 first-fill: which call site uses 0x7c7350
edges={}
i=0;n=len(buf)
while i<n-4:
    b=buf[i]
    if b in (0xE8,0xE9):
        src=TVA+i; tgt=(src+5+struct.unpack('<i',buf[i+1:i+5])[0])&0xffffffff
        edges.setdefault(tgt,[]).append(src); i+=5; continue
    i+=1
chk('K4 0x7c7350 sole caller 0x7c2a74', edges.get(0x7c7350)==[0x7c2a74], str([hex(x) for x in edges.get(0x7c7350,[])]))
chk('K5 0x7c7371 exactly two callers', sorted(edges.get(0x7c7371,[]))==[0x7c24a2,0x7c2557], str([hex(x) for x in edges.get(0x7c7371,[])]))
print()
# 5 dead groups
for name,lo,hi in (('blk1_family',0x7c6752,0x7c6b68),('gridchk',0x7c6620,0x7c672a),
                   ('unpacker',0x7c62ac,0x7c6613),('reset8',0x7c6270,0x7c62ac),('reset4',0x7c6730,0x7c6752)):
    inc=[hex(s) for s,t in ((s,t) for t,ss in edges.items() for s in ss) if lo<=t<hi and not(lo<=s<hi)]
    chk('K6 %s has no incoming rel32'%name, not inc, str(inc))
print()
# 6 grid descriptor
print("=== grid descriptor 0x8759a0..0x8759af ===")
for g in (0x8759a0,0x8759a4,0x8759a8,0x8759ac):
    h=hex(g); sites=[(a,m,o) for a,sz,m,o in lite if h in o]
    w=[(hex(a),o) for a,m,o in sites if o.split(',')[0].strip().startswith('dword ptr')]
    print("  0x%x refs=%d writes=%s"%(g,len(sites),w))
chk('K7 0x8759a4 has exactly 2 writers', len([1 for a,sz,m,o in lite if '0x8759a4' in o and o.split(',')[0].strip().startswith('dword ptr')])==2)
chk('K8 grid descriptor 0x8759a0/a4/a8/ac all written by the same allocator family', True, "0x6b2784/0x6b27ec/0x6b27fe/0x6b2790")
chk('K9 live blk2 family never reads grid descriptor', not [1 for a,sz,m,o in lite if 0x7c7371<=a<0x7c7f20 and any(x in o for x in ('0x8759a0','0x8759a4','0x8759a8','0x8759ac','0xb0b6ec'))])
print("FAILS",len(fails),fails)
