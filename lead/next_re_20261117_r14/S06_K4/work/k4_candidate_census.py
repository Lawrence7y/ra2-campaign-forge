#!/usr/bin/env python3
"""S06-K4 candidate census: two channels independent of atlas entry+size, plus atlas cross-check."""
from pathlib import Path
import csv,json,struct,re,hashlib,collections
ROOT=Path(r"D:\Project\ra2-campaign-forge")
EXE=ROOT/"ra2youli/gamemd.exe"; COV=ROOT/"lead/next_re_20261117_r14/COVERAGE/coverage.tsv"
ATL=ROOT/"lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv"
CARD=ROOT/"lead/next_re_20261117_r14/S06_K4"; WORK=CARD/"work"; EVID=CARD/"EVIDENCE"
data=EXE.read_bytes()
layout=json.loads((WORK/"all_rtti.json").read_text(encoding="utf-8"))
vtables=layout["vtables"]; enum=layout["enum"]; enum_by_val={e["value"]:e for e in enum}

# PE offsets for raw byte channel
import pefile
pe=pefile.PE(str(EXE),fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    secs.append({"name":s.Name.rstrip(b"\0").decode("latin1"),"va":IB+s.VirtualAddress,"end":IB+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData),"raw":s.PointerToRawData,"rsize":s.SizeOfRawData})
def at(va,n):
    for s in secs:
        if s["va"]<=va<s["end"]:
            d=va-s["va"]
            if d<s["rsize"] and d+n<=s["rsize"]: return data[s["raw"]+d:s["raw"]+d+n]
    return None
def hx(x): return f"{x:08X}"
def shape(va):
    b=at(va,6)
    if b and len(b)==6 and b[0]==0xB8 and b[5]==0xC3:
        return {"kind":"B8_IMM32_C3","imm":struct.unpack_from("<I",b,1)[0],"bytes":b.hex()}
    if b and len(b)==6 and b[0]==0xB8 and b[5]==0xC2:
        return {"kind":"B8_IMM32_C2_RET4","imm":struct.unpack_from("<I",b,1)[0],"bytes":b.hex()}
    return {"kind":"OTHER","bytes":b.hex() if b else None}

def norm(x): return x.strip().lower()
with COV.open("r",encoding="utf-8",newline="") as f:
    cov=[r for r in csv.DictReader(f,delimiter="\t") if r.get("subsystem","").strip().upper()=="S06"]
with ATL.open("r",encoding="utf-8",newline="") as f:
    atl={norm(r["entry"]) for r in csv.DictReader(f,delimiter="\t")}
cov_by={norm(r["entry"].strip()):r for r in cov}
inter=sorted(set(cov_by)&atl)
grades=collections.Counter(cov_by[e]["grade"].strip() for e in inter)

# Channel A: raw bytes at S06 coverage entries; does not use atlas size or vtable.
cov_shape=[]
for e,r in cov_by.items():
    va=int(r["entry"].strip(),16); sh=shape(va)
    if sh["kind"].startswith("B8_IMM32"):
        cov_shape.append({"entry":r["entry"].strip().upper(),"grade":r["grade"].strip(),"name":r["name"].strip(),"kind":sh["kind"],"imm":sh.get("imm"),"bytes":sh["bytes"],"in_atlas":e in atl})
cov_b8c3=[x for x in cov_shape if x["kind"]=="B8_IMM32_C3"]
cov_nonproved_b8c3=[x for x in cov_b8c3 if x["grade"]!="[已证]"]

# Channel B: all RTTI/COL/vtable anchors; no atlas input.
hits=[]
for v in vtables:
    for i,sx in enumerate(v["slots"]):
        va=int(sx,16); sh=shape(va)
        if sh["kind"]!="B8_IMM32_C3": continue
        hits.append({"entry":hx(va),"imm":sh["imm"],"imm_hex":hx(sh["imm"]),"bytes":sh["bytes"],"class":v["class"],"offset":v["offset"],"slot":i,"vtable":v["vt_hex"],"col":v["col_hex"]})
hit_by=collections.defaultdict(list)
for h in hits: hit_by[hx(int(h["entry"],16))].append(h)
cov_hit=[]
for e,r in cov_by.items():
    key=hx(int(r["entry"].strip(),16))
    if key in hit_by:
        for h in hit_by[key]: cov_hit.append({**h,"grade":r["grade"].strip(),"name":r["name"].strip(),"in_atlas":e in atl})
cov_hit.sort(key=lambda x:(x["entry"],x["class"],x["slot"]))
cov_hit_nonproved=[h for h in cov_hit if h["grade"]!="[已证]"]

# WhatAmI candidates: enum value + RTTI class semantic match. Slot 11 canonical interface is checked separately in proof script.
aliases={"IsometricTile":"Isotile","IsometricTileType":"IsotileType","BuildingLight":"Light","TAction":"Action","TEvent":"Event","Tactical":"TacticalMap","Super":"SuperWeapon","WaypointPath":"Waypoint"}
def enum_class_match(cname,ename):
    m=re.fullmatch(r"\.\?AV([A-Za-z0-9_]+)@@",cname)
    if not m or "$" in m.group(1): return False
    cls=m.group(1); base=cls[:-5] if cls.endswith("Class") else cls
    return ename==base or ename==aliases.get(base)
what=[]
for h in hits:
    e=enum_by_val.get(h["imm"])
    if not e or e["name"]=="<none>": continue
    if not enum_class_match(h["class"],e["name"]): continue
    what.append({**h,"enum_name":e["name"],"enum_value":e["value"],"semantic_match":True})
what_main=[w for w in what if w["offset"]==0 and w["slot"]==11]
cov_what=[]
for w in what_main:
    r=cov_by.get(norm(w["entry"]))
    if r: cov_what.append({**w,"grade":r["grade"].strip(),"name":r["name"].strip(),"in_atlas":norm(w["entry"]) in atl})

# slot12 risk census: same vtable slot11+12 both B8/C3, and slot12 values.
slot_pairs=[]
for w in what_main:
    v=next((v for v in vtables if v["vt_hex"]==w["vtable"]),None)
    if not v: continue
    s12=int(v["slots"][12],16) if len(v["slots"])>12 else None
    sh12=shape(s12) if s12 else {"kind":"NONE","imm":None,"bytes":None}
    r=cov_by.get(norm(hx(s12))) if s12 else None
    slot_pairs.append({"class":w["class"],"vtable":w["vtable"],"col":w["col"],"slot11":w["entry"],"imm11":w["imm"],"slot12":hx(s12) if s12 else None,"kind12":sh12["kind"],"imm12":sh12.get("imm"),"bytes12":sh12.get("bytes"),"coverage12":(r["grade"].strip()+"/"+r["name"].strip()) if r else None})

lines=["S06-K4 CANDIDATE CENSUS (two discovery channels; atlas only for baseline cross-check)","SHA256="+hashlib.sha256(data).hexdigest().upper()]
lines.append("S06_ROWS=%d ATLAS_INTERSECTION=%d GRADES=%r NAMED_LIKE=%d"%(len(cov),len(inter),dict(grades),sum(1 for e,r in cov_by.items() if r["name"].strip() and not r["name"].strip().startswith("sub_"))))
lines.append("CHANNEL_A_COVERAGE_ENTRY_SHAPE B8_IMM32_C3=%d NONPROVED_B8_IMM32_C3=%d B8_IMM32_C2_RET4=%d"%(len(cov_b8c3),len(cov_nonproved_b8c3),sum(1 for x in cov_shape if x["kind"]=="B8_IMM32_C2_RET4")))
for x in cov_shape: lines.append("COV_SHAPE "+json.dumps(x,ensure_ascii=False))
lines.append("CHANNEL_B_ALL_RTTI_ANCHORED_B8_IMM32_C3=%d INTERSECT_S06_COVERAGE=%d NONPROVED=%d"%(len(hits),len(cov_hit),len(cov_hit_nonproved)))
for x in cov_hit: lines.append("ANCHOR_INTERSECT "+json.dumps(x,ensure_ascii=False))
lines.append("WHATAMI_ENUM_RTTI_MATCHES_ALL=%d CANONICAL_SLOT11=%d S06_COVERAGE=%d"%(len(what),len(what_main),len(cov_what)))
for x in cov_what: lines.append("S06_WHATAMI "+json.dumps(x,ensure_ascii=False))
lines.append("SLOT11_SLOT12_RISK_PAIRS=%d"%len(slot_pairs))
for x in slot_pairs: lines.append("SLOT_PAIR "+json.dumps(x,ensure_ascii=False))
(EVID/"candidate_census.txt").write_text("\n".join(lines)+"\n",encoding="utf-8")
(WORK/"candidate_census.json").write_text(json.dumps({"cov_shape":cov_shape,"cov_hit":cov_hit,"cov_what":cov_what,"slot_pairs":slot_pairs},ensure_ascii=False,indent=2),encoding="utf-8")
print("S06",len(cov),"inter",len(inter),grades,"cov_shape",len(cov_shape),"B8C3",len(cov_b8c3),"nonproved",len(cov_nonproved_b8c3),"anchored",len(hits),"cov_hit",len(cov_hit),"nonproved",len(cov_hit_nonproved),"whatami S06",len(cov_what))
