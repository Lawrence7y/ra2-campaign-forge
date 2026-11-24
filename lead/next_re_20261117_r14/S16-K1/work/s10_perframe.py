"""Step 10: prove per-frame call chain:
  CurrentFrame inc (0xA8ED84) -> 0x55E160 -> virtual House::Update (vslot 0x5C)
  -> 0x4F8440 loop -> HasChargeProgressed 0x6CBCA0 at 0x4F8E4A.
Also check that 0x4F9370 twin has no callers/refs (dead)."""
import sys, os, struct, json
sys.path.insert(0, os.path.dirname(__file__))
from re_lib import *
b=Bin(); out=[]
emit=out.append
cm=json.load(open(os.path.join(os.path.dirname(__file__),'calls_map.json')))
calls={int(k,16):[int(x,16) for x in v] for k,v in cm['calls'].items()}
jmps={int(k,16):[int(x,16) for x in v] for k,v in cm['jmps'].items()}

emit("=== all .text instructions referencing 0xA8ED84 (CurrentFrame) ===")
ins_all=disasm_range(b,b.sec('.text')['va'],b.sec('.text')['va']+b.sec('.text')['rawsize'])
writes=[]; reads=[]; other=[]
for i in ins_all:
    if i.id==0: continue
    if any(o.type==capstone.x86.X86_OP_MEM and o.mem.base==0 and o.mem.index==0 and (o.mem.disp&0xffffffff)==0xA8ED84 for o in i.operands):
        line=fmt(i)
        # determine write by mnemonic / op0
        w = (i.mnemonic in ('inc','dec','add','sub','mov','xor','or','and','xchg','pop') and
             i.operands and i.operands[0].type==capstone.x86.X86_OP_MEM and
             i.operands[0].mem.base==0 and i.operands[0].mem.disp==0xA8ED84)
        (writes if w else reads).append(line)
emit(f"writes ({len(writes)}):")
for l in writes: emit("  "+l)
emit(f"other reads ({len(reads)}):")
for l in reads[:40]: emit("  "+l)

emit("\n=== channel-B function containment: 0x4F8E4A inside fn 0x4F8440 ===")
ins8440=disasm_range(b,0x4F8440,0x4F8E60)
rets=[fmt(i) for i in ins8440 if i.mnemonic.startswith('ret')]
emit(f"  ret instructions between 0x4F8440 and 0x4F8E4A: {len(rets)}")
emit("  first 5: "+"; ".join(rets[:5]))
emit("  prologue: "+b.read(0x4F8440,12).hex())

emit("\n=== channel-B function containment: 0x55E269 inside fn 0x55E160 ===")
ins55=disasm_range(b,0x55E160,0x55E270)
rets=[fmt(i) for i in ins55 if i.mnemonic.startswith('ret')]
emit(f"  ret instructions between 0x55E160 and 0x55E269: {len(rets)}")

emit("\n=== chain instructions verbatim ===")
for tag,a,e in [("frame increment",0x55DE73,0x55DEA0),
                ("main-loop call",0x55E25C,0x55E26C),
                ("House::Update loop",0x4F8E28,0x4F8E52),
                ("dead twin",0x4F9370,0x4F939C)]:
    emit(f"\n  --- {tag} ---")
    for l in dump(b,a,e).splitlines(): emit("    "+l)

emit("\n=== 0x55DE60 function start discovery (scan back for ret) ===")
for va in range(0x55DE60,0x55DC00,-1):
    pass
# use call/jmp targets in range
cand=[t for t in list(calls)+list(jmps) if 0x55D800<=t<=0x55DE60]
emit("  call/jmp targets in 0x55D800..0x55DE60: "+" ".join(f"{x:08X}" for x in sorted(cand)))

text="\n".join(out)
open(os.path.join(os.path.dirname(__file__),'..','EVIDENCE','E10_perframe_chain.txt'),'w',encoding='utf-8').write(text)
print(text[:14000])
