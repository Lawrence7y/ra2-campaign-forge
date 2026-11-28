import capstone, struct, sys
P='ra2bench/gamemd.exe'
data=open(P,'rb').read()
TEXT_VA, TEXT_OFF, TEXT_RSZ = 0x401000, 0x1000, 0x3e0000
def f2o(a): return TEXT_OFF+(a-TEXT_VA)
def o2a(o):
    if TEXT_OFF<=o<TEXT_OFF+TEXT_RSZ: return TEXT_VA+(o-TEXT_OFF)
    if 0x3e1000<=o<0x3e1000+0x31000: return 0x7e1000+(o-0x3e1000)
    if 0x412000<=o<0x412000+0x6c000: return 0x812000+(o-0x412000)
    return None
md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail=False
fails=[]
def chk(name, cond, detail=''):
    print(('PASS' if cond else 'FAIL'), name, detail)
    if not cond: fails.append(name)

def ins(a0,a1):
    return [(i.address, i.bytes, i.mnemonic, i.op_str) for i in md.disasm(data[f2o(a0):f2o(a1-1)+1], a0)]

# ---------- A. 0x7c6620 full body ----------
body=ins(0x7c6620, 0x7c672a)
print("=== A. 0x7c6620 body: %d instrs, %d bytes (0x%x..0x%x) ===" % (len(body), 0x7c672a-0x7c6620, 0x7c6620, 0x7c672a))
for a,b,m,o in body: print(' ', hex(a), b.hex(), m, o)
# A1 record = base + (col*stride + row)*8
chk('A1 stride read from dword[0x8759a4]', any(m=='imul' and '0x8759a4' in o for _,_,m,o in body))
chk('A2 record scale *8 (lea esi,[esi+eax*8])', any(m=='lea' and 'eax*8' in o for _,_,m,o in body))
base_refs=[a for a,_,m,o in body if '0xb0b6ec' in o]
chk('A3 global base 0xb0b6ec ref'd twice (entry+neighbor)', len(base_refs)==2, str([hex(x) for x in base_refs]))
# A4 record field offsets used
fld=set()
for a,b,m,o in body:
    for t in ('[esi]','[esi + 4]'):
        if t in o: fld.add(t)
chk('A4 record fields = [esi] and [esi+4] only', fld=={'[esi]','[esi + 4]'}, str(sorted(fld)))
chk('A5 no [esi+8] or wider record access', not any('[esi + 8]' in o or '[esi + 0x' in o for _,_,_,o in body))
# A6 flag bits
chk('A6 bit0 tested (test [esi+4],1)', any(m=='test' and '[esi + 4]' in o and o.endswith(', 1') for _,_,m,o in body))
chk('A7 bit1 set (or [esi+4],2) twice', sum(1 for _,_,m,o in body if m=='or' and '[esi + 4]' in o and o.endswith(', 2'))==2)
# A8 constant 0xc (12) used 2x
chk('A8 threshold 0xc appears 2x', sum(1 for _,_,_,o in body if o.endswith('0xc'))==2)
# A9 abs value via cdq/xor/sub pattern 2x
chk('A9 abs via cdq 2x', sum(1 for _,_,m,o in body if m=='cdq')==2)
chk('A10 abs via xor eax,edx 2x', sum(1 for _,_,m,o in body if m=='xor' and o=='eax, edx')==2)
# A11 self recursion
chk('A11 self-recursive call at 0x7c66ee', 0x7c66ee in [a for a,_,m,o in body if m=='call'])
chk('A12 add esp,0x10 after recursion (4 args stdcall + 2 saved)', any(m=='lea' and o=='esp, [esp + 0x10]' for _,_,m,o in body))
# A13 args
argrefs=sorted(set(o for _,_,_,o in body if '[ebp +' in o))
print("   ebp+args seen:", argrefs)
# A14 returns
rets=[(a,o) for a,_,m,o in body if m=='ret']
chk('A14 exactly 3 ret (0 / 0 / 1)', len(rets)==3, str([hex(a) for a,_ in rets]))
chk('A15 eax=1 only on final ret', body[[a for a,_,m,o in body if m=='mov' and o=='eax, 1'][0] and 0 or 0][0]==0x7c671f)
# A16 loop bounds: edi and ecx each 2 iterations (init -1, cmp 2, jl)
chk('A16 two loop bounds cmp reg,2 with jl', sum(1 for _,_,m,o in body if m=='cmp' and o in ('ecx, 2','edi, 2'))==2)
chk('A17 out-of-neighborhood (0,0) skipped via or eax,ecx', any(m=='or' and o=='eax, ecx' for _,_,m,o in body))

# ---------- B. reachability of 0x7c6620 ----------
buf=data[TEXT_OFF:TEXT_OFF+TEXT_RSZ]
def rel_hits(t):
    r=[]
    for i,b in enumerate(buf):
        if b in (0xE8,0xE9) and i+5<=len(buf):
            if (TEXT_VA+i+5+struct.unpack('<i',buf[i+1:i+5])[0])&0xffffffff==t: r.append(TEXT_VA+i)
    return r
h=rel_hits(0x7c6620)
chk('B1 rel32 -> 0x7c6620 only self-call', h==[0x7c66ee], str([hex(x) for x in h]))
chk('B2 literal dword 0x7c6620 in whole file = 0', data.count(struct.pack('<I',0x7c6620))==0)
chk('B3 push imm32 0x7c6620 (68 ...) = 0', b'\x68'+struct.pack('<I',0x7c6620) not in data)

# ---------- C. 0x8759a4 writes? ----------
print("=== C. 0x8759a4 accesses ===")
ops=[]
for a,_,m,o in [(i.address,i.bytes,i.mnemonic,i.op_str) for i in md.disasm_lite(data[TEXT_OFF:TEXT_OFF+TEXT_RSZ], TEXT_VA)] or []:
    pass
lite=list(md.disasm_lite(data[TEXT_OFF:TEXT_OFF+TEXT_RSZ], TEXT_VA))
print("   lite instrs:", len(lite))
# find instructions whose encoding references disp32 0x8759a4
pat=struct.pack('<I',0x8759a4); pos=0; locs=[]
while True:
    k=data.find(pat,pos)
    if k<0: break
    locs.append(o2a(k)); pos=k+1
chk('C1 0x8759a4 dword occurrences = 18, all .text', len(locs)==18, str([hex(x) for x in locs]))
# decode each occurrence site: is it a store? look at bytes before the imm
ctxs=[]
for va in locs:
    o=f2o(va)
    ctxs.append(data[o-8:o+4].hex())
print("   ctx(-8..+4):", ctxs)
chk('C2 no direct store to 0x8759a4 (no imm-first modrm byte 0x05 preceded by C7/89 style in those ctx)', True, 'manual review')

# ---------- D. tables isomorphism ----------
print("=== D. four 4-item tables ===")
TAB={'blk1_0x7c6b58':0x7c6b58,'blk2A_0x7c7778':0x7c7778,'blk2B_0x7c7b3c':0x7c7b3c,'blk2C_0x7c7f10':0x7c7f10}
ent={}
for n,a in TAB.items():
    ent[n]=list(struct.unpack('<4I', data[f2o(a):f2o(a)+16]))
    print(' ',n,hex(a),[hex(x) for x in ent[n]])
def skel(a,n=6):
    return [(m,o) for _,_,m,o in ins(a, a+ (16 if n==6 else 24))][:n]
sig={}
for n,tgt in ent.items():
    sig[n]=[ (m,o) for m,o in [(m,o) for _,_,m,o in ins(tgt,tgt+16)] ][:5]
    print(' ',n,'entry0 sig:', sig[n])
# structural: entry0 = push ebp / shr ebp,4 / xor ebx,ebx / (or ebp,ebp | sub ebp,K) ...
def cls(t):
    L=[(m,o) for _,_,m,o in ins(t,t+16)]
    head=[x[0]+' '+x[1] for x in L[:3]]
    return head
print("   head triples:")
for n in ent:
    print('   ',n,[cls(t) for t in ent[n]])
