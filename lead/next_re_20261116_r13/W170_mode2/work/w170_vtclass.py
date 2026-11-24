"""Resolve vtable addresses from dword hits to class names and slot numbers (channel A)."""
import json, pefile, struct, os
VTAB=r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\vtables_canonical.json"
OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r13\W170_mode2\EVIDENCE"
d=json.load(open(VTAB,encoding="utf-8"))
vts=d["vtables"]
# build map va->class  and sorted list
m={}
for v in vts:
    m[int(v["vt"])]=v["class"]
# known vtable hits from fn_ownership
hits={
 0x7e3f98:"fn44EBF0", 0x7ec330:"fn543A10", 0x7ec32c:"fn543A40", 0x7ec278:"fn543B10",
 0x7e47b8:"fn5F4D30", 0x7edd94:"fn5F4D30",0x7ef134:"fn5F4D30",0x7ef4a8:"fn5F4D30",0x7efa28:"fn5F4D30",0x7efc70:"fn5F4D30",0x7f33d0:"fn5F4D30",0x7f63ec:"fn5F4D30",0x7f677c:"fn5F4D30",
 0x7e47bc:"fn5F4EC0",0x7edd98:"fn5F4EC0",0x7ef138:"fn5F4EC0",0x7efa2c:"fn5F4EC0",0x7efc74:"fn5F4EC0",0x7f05e0:"fn5F4EC0",0x7f33d4:"fn5F4EC0",0x7f63f0:"fn5F4EC0",0x7f6780:"fn5F4EC0",
 0x7ef4f8:"fn5FC570",0x7f478c:"fn6E9140",0x7f6ccc:"fn75F8B0",0x7f6cc8:"fn75F980",
}
lines=["=== vtable-hit -> class resolution ==="]
for h,who in sorted(hits.items()):
    cls=m.get(h,"UNKNOWN")
    lines.append("  @%08X (%s) -> %s"%(h,who,cls))
# For each class main table, derive slot for specific hits of interest
lines.append("")
lines.append("=== slot derivation for key hits (main tables col_off=0) ===")
for h in [0x7e3f98,0x7e47b8,0x7e47bc,0x7ec330,0x7ec32c,0x7ec278,0x7f478c,0x7f6ccc,0x7f6cc8]:
    # find all vts near h (vt<=h, h-vt < 0x1000, (h-vt)%4==0)
    cands=[]
    for v in vts:
        vt=int(v["vt"])
        if vt<=h<=vt+0x1000 and (h-vt)%4==0 and int(v.get("col_offset",0))==0:
            cands.append((vt,int((h-vt)//4),v["class"]))
    lines.append("  @%08X: %s"%(h, "; ".join("vt=%08X slot=%d(+0x%X) %s"%(vt,s,s*4,c) for vt,s,c in cands[:6]) or "NO MAIN-TABLE CAND"))
path=os.path.join(OUT,"Q2_vtclass_resolve.txt")
open(path,"w",encoding="utf-8").write("\n".join(lines)+"\n")
print("\n".join(lines))
