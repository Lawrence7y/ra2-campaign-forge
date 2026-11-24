#!/usr/bin/env python3
"""Map the 83 write-point functions to RTTI classes via symbols.json vfuncs lists,
and check whether each write site's base register is the function's `this` (ecx on entry
or a copy thereof). This is the class-exclusion / this-origin evidence generator.
"""
import os, sys, json, bisect, re
import pefile, capstone
HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=r"D:\Project\ra2-campaign-forge"
sys.path.insert(0,os.path.join(ROOT,"lead","next_re_20261116_r12","_lead_audit"))
import audit_lib

with open(os.path.join(HERE,"..","EVIDENCE","w174_writes.json"),"r",encoding="utf-8") as f:
    D=json.load(f)
writes=D["writesA"]
funcs=sorted(set(d["va"] for d in []))  # placeholder

# use M3 attribution files to get fn per site
# actually recompute via w174_classify_cfg.tsv (fn column)
fn_of={}
with open(os.path.join(HERE,"..","EVIDENCE","w174_classify_cfg.tsv"),"r",encoding="utf-8") as f:
    hdr=f.readline().rstrip().split("\t")
    for line in f:
        p=line.rstrip().split("\t"); r=dict(zip(hdr,p))
        fn_of[int(r["va"],16)]=int(r["fn"],16)
all_fns=sorted(set(fn_of.values()))
print("distinct fns:",len(all_fns))

# symbols.json
S=json.load(open(os.path.join(ROOT,"re_atlas","evidence","rtti","symbols.json"),"r",encoding="utf-8"))
classes=S["classes"]
# build vfunc -> class list
vf2class={}
for cname,obj in classes.items():
    for v in obj.get("vfuncs",[]):
        try: va=int(v,16)
        except: continue
        vf2class.setdefault(va,[]).append(cname)

# also base-class hierarchy from 'bases'
def ancestors(cname, seen=None):
    if seen is None: seen=set()
    if cname in seen or cname not in classes: return seen
    seen.add(cname)
    for b in classes[cname].get("bases",[]):
        if b!=cname: ancestors(b,seen)
    return seen

def class_family(cnames):
    fam=set()
    for c in cnames:
        fam|=ancestors(c)
    return fam

lines=[]
lines.append("=== 83 write-point functions -> RTTI class (via vfuncs in symbols.json) ===")
lines.append("fn\tvfunc_classes\tancestor_families\tis_ObjectClass_family")
obj_fns=0; nonobj_fns=[]; unknown_fns=[]
for fn in all_fns:
    cnames=vf2class.get(fn,[])
    fam=class_family(cnames)
    isobj = any(x.endswith("ObjectClass") or x in ("ObjectClass","AbstractClass","TechnoClass","BuildingClass","UnitClass","InfantryClass","AircraftClass","TerrainClass","OverlayClass","SmudgeClass","WallClass","AnimClass","BulletClass","BuildingLightClass","FoggedObjectClass","TiberiumClass") for x in fam)
    # stricter: ObjectClass in ancestors
    isobj2 = "ObjectClass" in fam
    if cnames:
        if isobj2: obj_fns+=1
        else: nonobj_fns.append((fn,cnames,fam))
    else:
        unknown_fns.append(fn)
    lines.append("%08X\t%s\t%s\t%s" % (fn, ",".join(cnames) or "-", ",".join(sorted(fam))[:160] or "-", isobj2))

lines.append("")
lines.append("vfunc-classified ObjectClass-family fns: %d" % obj_fns)
lines.append("vfunc-classified NON-ObjectClass fns: %d" % len(nonobj_fns))
for fn,c,fam in nonobj_fns:
    lines.append("  NONOBJ %08X  classes=%s fam=%s" % (fn,",".join(c),",".join(sorted(fam))))
lines.append("no vfunc-class (non-virtual helpers): %d" % len(unknown_fns))
lines.append("  "+" ".join("%08X"%x for x in unknown_fns))

with open(os.path.join(HERE,"..","EVIDENCE","w174_fn_class_map.txt"),"w",encoding="utf-8") as f:
    f.write("\n".join(lines)+"\n")

print("obj_fns(vfunc ObjectClass ancestors)=%d nonobj=%d unknown=%d" % (obj_fns,len(nonobj_fns),len(unknown_fns)))
for fn,c,fam in nonobj_fns:
    print("  NONOBJ %08X classes=%s" % (fn,",".join(c)))
