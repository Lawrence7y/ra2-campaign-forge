import capstone, re, sys
P='ra2bench/gamemd.exe'; data=open(P,'rb').read()
TVA,TOFF,TRSZ=0x401000,0x1000,0x3e0000
buf=data[TOFF:TOFF+TRSZ]
mdl=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); mdl.detail=False; mdl.skipdata=True
fails=[]
def chk(n,c,d=''):
    print(('PASS' if c else 'FAIL'), n, d)
    if not c: fails.append(n)

pat=re.compile(r'\[ebx \+ 0x([0-9a-f]+)\]')
patx=re.compile(r'\[eax \+ 0x([0-9a-f]+)\]')
cand=[]; cx=0; n=0
for a,sz,m,o in mdl.disasm_lite(buf,TVA):
    n+=1
    if not o: continue
    for mm in pat.finditer(o):
        v=int(mm.group(1),16)
        if 0x7d0<=v<0x800: cand.append((a,v,sz,m,o))
    for mm in patx.finditer(o):
        v=int(mm.group(1),16)
        if 0x7d0<=v<0x800: cx+=1
print("instrs(skipdata lite):", n)
print("=== ebx + [0x7d0,0x800) candidate sites:", len(cand))
for a,v,sz,m,o in sorted(cand,key=lambda x:(x[1],x[0])):
    print("  off=0x%03x @0x%x sz=%d %s %s" % (v,a,sz,m,o))
offs=sorted(set(v for _,v,_,_,_ in cand))
print("distinct offsets:", len(offs), [hex(x) for x in offs])
chk('W1 offset 0x7d0 accessed', 0x7d0 in offs)
chk('W2 distinct offsets > 0', len(offs)>0, str(len(offs)))
print("neg-control eax-base hits:", cx)
chk('W3 neg control differs', cx!=len(cand), "ebx=%d eax=%d"%(len(cand),cx))
if offs:
    gaps=[v for v in range(0x7d0,0x800) if v not in offs]
    print("gaps:", len(gaps), "max", hex(max(offs)))
# also widen: ebx + 0x8xx and ebx + 0x6xx for context of the same object
wide={}
for a,sz,m,o in mdl.disasm_lite(buf,TVA):
    if not o: continue
    for mm in pat.finditer(o):
        v=int(mm.group(1),16)
        if 0x600<=v<0x900: wide.setdefault(v,[]).append((a,m,o))
print("=== ebx+[0x600,0x900) distinct offsets:", len(wide))
for v in sorted(wide): print("  0x%03x  n=%d  e.g. %s"%(v,len(wide[v]),wide[v][0][2]))
print("FAILS", len(fails), fails)
