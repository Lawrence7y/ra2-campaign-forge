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
# instruction-start set over whole .text (skipdata)
starts=set()
for a,sz,m,o in md.disasm_lite(buf,TVA): starts.add(a)
print("instruction starts (skipdata):", len(starts))
run=[struct.unpack('<I',data[TOFF+(0x874900-TVA)+4*k:TOFF+(0x874900-TVA)+4*k+4])[0] for k in range(88)]
hit=[v for v in run if v in starts]
print("the 88 monotone dwords: how many land on an instruction start?  %d/88"%len(hit))
chk('C1 the 0x874900 run is NOT a code-pointer table (few land on instruction starts)', len(hit)<=4, "%d/88 -> %s"%(len(hit),[hex(x) for x in hit]))
# the specific values cited as incoming-dword refs for our groups
for v in (0x7c6789,0x7c6990,0x7c637a,0x7c6581,0x7c73b4,0x7c75bb,0x7c77c3):
    print("   0x%x is instruction start: %s"%(v, v in starts))
chk('C2 the 7 cited values are not instruction starts', not any(v in starts for v in (0x7c6789,0x7c6990,0x7c637a,0x7c6581,0x7c73b4,0x7c75bb,0x7c77c3)))
# stride analysis of the run
d=[run[k+1]-run[k] for k in range(87)]
import collections
print("   stride histogram:", collections.Counter(d))
chk('C3 strides all in {0x206,0x207,0x208}', set(d)<={0x206,0x207,0x208}, str(set(d)))
chk('C4 run is monotone increasing', all(x>0 for x in d))
# does the run look like "one address per ~519 bytes" i.e. block boundaries of a synthetic region?
print("   span: 0x%x..0x%x  total 0x%x over 88 entries => mean stride %.1f"%(run[0],run[-1],run[-1]-run[0],(run[-1]-run[0])/87))
print("FAILS",len(fails),fails)
