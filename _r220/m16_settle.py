import sys,struct,json
from collections import Counter,defaultdict
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
R=P.RAW; seg=P.B['.text']; lo=seg['lo']; rp=seg['rawptr']; rs=seg['rawsize']
mdl=Cs(CS_ARCH_X86,CS_MODE_32); mdl.detail=False; mdl.skipdata=True
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
# 1) all instrs whose operand mentions any dword in [0x87c484,0x87c4c0)
pos=rp; n=0; last=0; hits=[]
while pos<rp+rs:
    got=False
    for ins in mdl.disasm_lite(R[pos:pos+16], lo+(pos-rp)):
        got=True; n+=1; last=ins[0]
        op=ins[3]
        if '87c48' in op or '87c49' in op or '87c4a' in op or '87c4b' in op: hits.append((ins[0],ins[2],op))
        break
    pos += ins[1] if got else 1
print("sweep",n,"last",hex(last))
for h in hits: print("  ",hex(h[0]),h[1],h[2])
print("count",len(hits))
# 2) exact 0x87c484 forms
c=Counter()
for a_,m,op in hits:
    if '0x87c484' in op: c[m+' '+op.replace('0x87c484','T')]+=1
print("0x87c484 exact:",dict(c))
# 3) dither+delta context block (one iteration) 0x7c7428..0x7c7455 with bytes
o=P.r2o(0x7c7428)
print("bytes 0x7c7428..0x7c7456:",R[o:o+46].hex())
# 4) param structure of 0x7c7371: search first 0x120 bytes for [ebp+..] reads
o2=P.r2o(0x7c7371)
reads=[]
for i in md.disasm(R[o2:o2+0x120], 0x7c7371):
    for op in i.operands:
        if op.type==3 and op.mem.base==5:  # ebp
            reads.append((hex(i.address), i.mnemonic, i.op_str))
    if i.address>0x7c7490: break
print("ebp-relative in prologue:", reads[:14])
# 5) 0x7c76ac / 0x7c76e0 blocks (the ones jmp'd from 0x7c7422) get context
for s in (0x7c7690,0x7c76c0):
    print("---",hex(s))
    for i in list(md.disasm(R[P.r2o(s):P.r2o(s)+0x40], s))[:12]:
        print("   ",hex(i.address),i.mnemonic,i.op_str)
json.dump({'sweep':n,'last':hex(last),'c484_hits':[[hex(a),m,op] for a,m,op in hits]},open('_r220/m16.json','w'),indent=1)
