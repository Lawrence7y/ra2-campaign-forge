"""Step 12: launch chain + jump table verification."""
import sys, os, struct, json
sys.path.insert(0, os.path.dirname(__file__))
from re_lib import *
b=Bin(); out=[]
emit=out.append
cm=json.load(open(os.path.join(os.path.dirname(__file__),'calls_map.json')))
calls={int(k,16):[int(x,16) for x in v] for k,v in cm['calls'].items()}
rows,hdr=load_atlas()

emit("=== callers of ClickFire 0x6CB920 and Launch 0x6CC390 ===")
for f in (0x6CB920,0x6CC390):
    emit(f"  {f:08X}: {[hex(x) for x in calls.get(f,[])]}")
emit("\n=== ClickFire -> Launch call sites with context ===")
for s in calls.get(0x6CC390,[]):
    emit(f"  --- site {s:08X} ---")
    for l in dump(b,s-0x30,s+0x20).splitlines(): emit("    "+l)
emit("\n=== Launch jump table head @ 0x6CC390 ===")
for l in dump(b,0x6CC390,0x6CC3C0).splitlines(): emit("  "+l)
emit("\n=== jump table @ 0x6CDE44 (12 absolute VA) ===")
names=['Nuke','IronCurtain','LightningStorm','ChronoSphere','ChronoWarp','ParaDrop',
       'AmerParaDrop','PsychicDominator','SpyPlane','GeneticMutator','ForceShield','PsychicReveal']
for i,n in enumerate(names):
    emit(f"  case {i:2d} {n:<20s} -> {b.u32(0x6CDE44+4*i):08X}")

emit("\n=== caller of ClickFire (0x4FAE97) context ===")
for l in dump(b,0x4FAE50,0x4FAEE0).splitlines(): emit("  "+l)
r=func_containing(rows,0x4FAE97)
emit("  atlas fn: "+(f"{r[0]:08X}+{r[1]}" if r else "GAP"))

text="\n".join(out)
open(os.path.join(os.path.dirname(__file__),'..','EVIDENCE','E12_launch_chain.txt'),'w',encoding='utf-8').write(text)
print(text[:13000])
