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
# caller chain of the grid allocator
E={}
i=0;n=len(buf)
while i<n-4:
    b=buf[i]
    if b in (0xE8,0xE9):
        src=TVA+i; tgt=(src+5+struct.unpack('<i',buf[i+1:i+5])[0])&0xffffffff
        E.setdefault(tgt,[]).append((src,'call' if b==0xE8 else 'jmp')); i+=5; continue
    i+=1
def chain(f, depth=4):
    cur=[f]; out=[(0,f)]
    for d in range(1,depth+1):
        nxt=[]
        for c in cur:
            for s,k in E.get(c,[]):
                if k=='call': nxt.append(s); out.append((d,s))
        cur=nxt
        if not cur: break
    return out
print("=== grid allocator 0x6b2700 upward chain ===")
for d,s in chain(0x6b2700,4): print("   depth%d 0x%x"%(d,s))
print()
print("=== refresher 0x6b2a70 upward chain ===")
for d,s in chain(0x6b2a70,3): print("   depth%d 0x%x"%(d,s))
print()
# 0x8759a8 / 0x8759ac semantics: contexts
print("=== 0x8759a8 first-write context 0x6b27f8..0x6b2810 ===")
for i2 in md.disasm(data[f2o(0x6b27f0):f2o(0x6b2810)],0x6b27f0):
    print("   ",hex(i2.address), i2.bytes.hex(), i2.mnemonic, i2.op_str)
print()
print("=== 0x8759ac first-write context 0x6b2788..0x6b2796 ===")
for i2 in md.disasm(data[f2o(0x6b2788):f2o(0x6b2796)],0x6b2788):
    print("   ",hex(i2.address), i2.bytes.hex(), i2.mnemonic, i2.op_str)
print()
# does the live blk2 path read the grid globals?
for g in (0x8759a0,0x8759a4,0x8759a8,0x8759ac,0xb0b6ec):
    h=hex(g)
    sites=[a for a,sz,m,o in md.disasm_lite(buf,TVA) if h in o]
    inblk2=[a for a in sites if 0x7c7371<=a<0x7c7f20]
    print("  %s refs=%d  inside blk2_family=%d"%(h,len(sites),len(inblk2)))
chk('G7 the live blk2 family never touches the grid descriptor or grid base',
    not [a for a in (0x8759a0,0x8759a4,0x8759a8,0x8759ac,0xb0b6ec) for a2,sz,m,o in md.disasm_lite(buf,TVA) if hex(a) in o and 0x7c7371<=a2<0x7c7f20])
chk('G8 0x7c6620 reads both grid base 0xb0b6ec and stride 0x8759a4 (grid consumer)', 
    any('0xb0b6ec' in o for a,sz,m,o in md.disasm_lite(buf,TVA) if 0x7c6620<=a<0x7c672a) and
    any('0x8759a4' in o for a,sz,m,o in md.disasm_lite(buf,TVA) if 0x7c6620<=a<0x7c672a))
print("FAILS",len(fails),fails)
