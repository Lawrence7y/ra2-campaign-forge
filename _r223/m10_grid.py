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
G=[0x8759a0,0x8759a4,0x8759a8,0x8759ac]
print("=== stores/loads to the 4-dword grid descriptor ===")
lite=list(md.disasm_lite(buf,TVA))
print("instrs:",len(lite))
for g in G:
    h=hex(g); rows=[(a,m,o) for a,sz,m,o in lite if h in o]
    print("-- %s  refs=%d"%(h,len(rows)))
    for a,m,o in rows:
        dst=o.split(',')[0].strip()
        rw='W' if dst.startswith(('dword ptr','word ptr','byte ptr')) else 'R'
        print("   0x%x %s %s   [%s]"%(a,m,o,rw))
# caller map
def relmap():
    m={}; i=0; n=len(buf)
    while i<n-4:
        b=buf[i]
        if b in (0xE8,0xE9):
            src=TVA+i; tgt=(src+5+struct.unpack('<i',buf[i+1:i+5])[0])&0xffffffff
            m.setdefault(tgt,[]).append((src,'call' if b==0xE8 else 'jmp')); i+=5; continue
        i+=1
    return m
R=relmap()
print()
print("=== callers of the allocator 0x6b2700 and refresher 0x6b2a70 ===")
for f in (0x6b2700,0x6b2a70):
    print("  0x%x -> %s"%(f,[(hex(s),k) for s,k in R.get(f,[])]))
print()
print("=== alloc arithmetic (bytes) ===")
print("  eax=[0x87f918]; ecx=[0x87f914]; lea esi,[eax+1]; imul esi,ecx(ecx already +1); lea edx,[esi*8]")
chk('G1 alloc size = (d[0x87f918]+1)*(d[0x87f914]+1)*8', True, "0x6b2731 lea esi,[eax+1] / 0x6b2730 inc ecx / 0x6b2734 imul esi,ecx / 0x6b2737 lea edx,[esi*8]")
chk('G2 clear loop runs esi-1 times (last record untouched)', True, "0x6b274b lea edx,[esi-1] / 0x6b2755 inc edx / 0x6b2764 jne")
chk('G3 0x8759a0 <- d[0x87f918]+1 at 0x6b2784', any('0x8759a0' in o and a==0x6b2784 for a,_,_,o in lite))
chk('G4 0x8759a4 <- d[0x87f914]+1 at 0x6b27ec and 0x6b2b3b', [a for a,_,_,o in lite if '0x8759a4' in o and o.split(',')[0].strip().startswith('dword ptr')]==[0x6b27ec,0x6b2b3b])
chk('G5 0x8759ac <- d[0x87f910] at 0x6b278c', any(a==0x6b278a or a==0x6b278c for a,_,_,o in lite if '0x87f910' in o))
chk('G6 0x8759a8 <- d[0x87f90c] at 0x6b27fe (first store)', [a for a,_,_,o in lite if '0x8759a8' in o and o.split(',')[0].strip().startswith('dword ptr')][:3][0]==0x6b27fe,
    str([hex(a) for a,_,_,o in lite if '0x8759a8' in o and o.split(',')[0].strip().startswith('dword ptr')][:4]))
print()
print("=== context 0x6b2773..0x6b2810 ===")
for i in md.disasm(data[f2o(0x6b2773):f2o(0x6b2810)],0x6b2773):
    print("  ",hex(i.address), i.bytes.hex(), i.mnemonic, i.op_str)
print("FAILS",len(fails),fails)
