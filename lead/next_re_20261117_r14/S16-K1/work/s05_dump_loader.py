"""Step 5: dump SWType INI loader 0x6CEA20 (atlas size 1085) and ctor; no truncation."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from re_lib import *
b=Bin()
rows,hdr=load_atlas()
r=func_containing(rows,0x6CEA20)
assert r and r[0]==0x6CEA20, r
start=r[0]; end=start+r[1]
out=[]
out.append(f"# SWType INI loader: atlas entry {start:08X} size {end-start} decimal; end {end:08X}")
out.append(dump(b,start,end))
out.append(f"\n# ctor 0x6CE5B0..0x6CE700")
out.append(dump(b,0x6CE5B0,0x6CE700))
open(os.path.join(os.path.dirname(__file__),'..','EVIDENCE','E05_swtype_ini_loader_full.txt'),'w',encoding='utf-8').write("\n".join(out))
print("wrote",len("\n".join(out)),"bytes; lines",len(out))
