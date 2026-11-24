"""S13-K1: merge loader (INI-anchored) + ctor offsets into final field tables.
Produces EVIDENCE/field_tables.txt and core numbers. Capstone skipdata=True throughout.
"""
import csv, sys, os
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-K1\work")
from re_lib import *

BASE=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-K1"
# vptr slots 0x0,0x4,0x8,0xC are not "fields" for counting
VPTR={0,4,8,12}

SIZES={"WeaponTypeClass":0x160,"WarheadTypeClass":0x1D0,"BulletTypeClass":0x2F8,"BulletClass":0x160}
# width map from ctor store size is not carried; use loader width where available else infer
# Manual overrides for pointer fields resolved by converters (verified in inspect_special.txt)
SPECIAL={
 ("WeaponTypeClass",0xA0):("BulletTypeClass* (Projectile=)","Projectile","0x7729AA (via 0x46C790)"),
 ("WeaponTypeClass",0xAC):("WarheadTypeClass* (Warhead=)","Warhead","0x772992 (via 0x75E3B0)"),
 ("WarheadTypeClass",None):("Verses double[11] @+0xA0..+0xF7","Verses","0x75DE48 (loop 11x via rep movsd ctor 0x75D1A7)"),
}

# load ini fields
ini={}  # (cls,off)-> list rows
with open(BASE+r"\EVIDENCE\ini_fields.tsv",encoding="utf-8") as f:
    for r in csv.DictReader(f,delimiter="\t"):
        off=int(r["store_off"],16)
        ini.setdefault((r["class"],off),[]).append(r)

# load ctor offsets
ctor={}
with open(BASE+r"\EVIDENCE\ctor_offsets.tsv",encoding="utf-8") as f:
    for r in csv.DictReader(f,delimiter="\t"):
        off=int(r["off"],16)
        ctor.setdefault((r["class"],off),[]).extend(r["sites"].split(",") if r["sites"] else [])

lines=[]
def p(x=""): lines.append(str(x))

for cls in ["WeaponTypeClass","WarheadTypeClass","BulletTypeClass","BulletClass"]:
    offs=sorted(set([o for (c,o) in ini if c==cls]+[o for (c,o) in ctor if c==cls]))
    p(f"\n######## {cls} (GetSize={hex(SIZES[cls])}) ########")
    p(f"distinct offsets incl vptr: {len(offs)}; excl vptr: {len([o for o in offs if o not in VPTR])}")
    p(f"{'off':>6} {'w':>2} {'semantic/INI key':<34} {'writer sites (loader store + ctor)':<52} reader site")
    nfield=0; maxend=0
    for o in offs:
        rows=ini.get((cls,o),[])
        if o in VPTR and not rows: continue
        w=rows[0]["width"] if rows else "?"
        if rows:
            keys=",".join(sorted(set(r["key"] for r in rows if r["key"])))
            sem=keys if keys else "[converter]"
            wsites=[r["store_site"] for r in rows]+ctor.get((cls,o),[])
            rsites=[r["default_site"] for r in rows if r["default_site"]]
            rsite=",".join(rsites[:2]) if rsites else ""
        else:
            sem="[未证]"
            wsites=ctor.get((cls,o),[])
            rsite=""
        # special label override
        if (cls,o) in SPECIAL:
            sem=SPECIAL[(cls,o)][0]+" ("+SPECIAL[(cls,o)][1]+")"
        try: wnum=int(w) if w!="?" else 1
        except: wnum=1
        maxend=max(maxend,o+wnum)
        nfield+=1
        p(f"  {o:04X}  {str(w):>2}  {sem[:34]:<34} {','.join(wsites)[:52]:<52} {rsite}")
    p(f"  -> field rows listed: {nfield}; max_end={hex(maxend)}; GetSize={hex(SIZES[cls])}; FIT={maxend<=SIZES[cls]}")
open(BASE+r"\EVIDENCE\field_tables.txt","w",encoding="utf-8").write("\n".join(lines))
print("\n".join(lines[:40]))
print("\n... full -> EVIDENCE/field_tables.txt")
