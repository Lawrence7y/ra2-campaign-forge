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
ent={}; 
for n,a in TAB:
    ent[n]=list(struct.unpack('<4I',data[f2o(a):f2o(a)+16]))
    print(n,hex(a),[hex(x) for x in ent[n]])
chk('T1 all four tables have 4 entries pointing into .text', all(0x401000<=x<0x7e1000 for v in ent.values() for x in v))
chk('T2 each table entry0 is the smallest of its group', all(min(v)==v[0] for v in ent.values()))
# decode fixed skeleton: first 6 instrs of each entry
rec={}
for n in ent:
    for k,t in enumerate(ent[n]):
        L=[]
        for i in md.disasm(data[f2o(t):f2o(t)+20], t):
            L.append((i.address,i.bytes,i.mnemonic,i.op_str))
        rec[(n,k)]=L[:6]
# normalized signature: mnemonic + operands with abs imm/rel resolved to "T" (target) / numeric kept
import re
def norm(L, base):
    out=[]
    for a,b,m,o in L:
        o2=o
        # normalize hex imm that is an absolute .text address
        for mm in re.finditer(r'0x([0-9a-f]{5,8})', o):
            v=int(mm.group(1),16)
            if 0x401000<=v<0x7e1000:
                o2=o2.replace(mm.group(0),'@REL%+d'%(v-base))
        out.append((m,o2,len(b)))
    return out
print()
print("=== normalized signature comparison (base = table[0] entry0) ===")
sigs={}
for n in ent:
    base=ent[n][0]
    sigs[n]=[norm(rec[(n,k)],base) for k in range(4)]
    print(n,"base",hex(base))
    for k in range(4):
        print("   k=%d"%k, sigs[n][k])
print()
# entry struct: n instrs count per entry
cnts={n:[len(rec[(n,k)]) for k in range(4)] for n in ent}
print("instr counts per entry:", cnts)
chk('T3 all 4 tables have identical instruction-count profile', len({tuple(v) for v in cnts.values()})==1, str(cnts))
# compare blk2A vs blk1 fully (all 6 instrs, ignoring rel32 value)
def sig6(n,k):
    base=ent[n][0]
    return norm(rec[(n,k)],base)
same_A = all(sig6('blk1',k)==sig6('blk2A',k) for k in range(4))
chk('T4 blk2A == blk1 with rel normalized', same_A)
for k in range(4):
    a=sig6('blk1',k); b=sig6('blk2A',k)
    if a!=b: print("   diff k=%d"%k, a, b)
# blk2B / blk2C vs blk1
for nm in ('blk2B','blk2C'):
    eq=[sig6('blk1',k)==sig6(nm,k) for k in range(4)]
    print(nm,"per-entry equal to blk1:",eq)
# raw byte comparison with rel32 masked
def masked(n,k):
    t=ent[n][k]; nxt=ent[n][k+1] if k<3 else ent[n][0]+0x100
    b=bytearray(data[f2o(t):f2o(t)+16])
    L=rec[(n,k)]
    span=sum(x[2] for x in L)
    b=bytearray(data[f2o(t):f2o(t)+span])
    for a,bs,m,o in L:
        if m=='jmp' and o.startswith('0x'):
            off=a-t+1
            b[off:off+4]=b'\0\0\0\0'
    return bytes(b)
print()
print("=== raw byte compare with rel32 masked ===")
for nm in ('blk2A','blk2B','blk2C'):
    for k in range(4):
        x=masked('blk1',k); y=masked(nm,k)
        print("  blk1 vs %s k=%d  len %d/%d  equal=%s"%(nm,k,len(x),len(y),x==y))
        if x!=y and len(x)==len(y):
            d=[(i,hex(x[i]),hex(y[i])) for i in range(len(x)) if x[i]!=y[i]]
            print("     byte diffs:",d)
print("FAILS",len(fails),fails)
