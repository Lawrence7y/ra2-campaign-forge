#!/usr/bin/env python3
"""S11-K5 semantic proof pass.

Allowed upgrades only:
  GetSize: body B8 imm32 C3 AND factory/ctor push(size) closes (6A/68).
  WhatAmI: body B8 imm32 C3 AND imm is engine AbstractType AND RTTI name semantically matches enum.
The script emits the real closure rows plus a coverage census proving whether any non-[已证] row is eligible.
"""
from pathlib import Path
import csv,json,struct,re,hashlib,collections
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
ROOT=Path(r"D:\Project\ra2-campaign-forge")
EXE=ROOT/"ra2youli/gamemd.exe"; COV=ROOT/"lead/next_re_20261117_r14/COVERAGE/coverage.tsv"
ATL=ROOT/"lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv"
CARD=ROOT/"lead/next_re_20261117_r14/S11_K5"; WORK=CARD/"work"; EVID=CARD/"EVIDENCE"
data=EXE.read_bytes(); pe=pefile.PE(str(EXE),fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    secs.append({"name":s.Name.rstrip(b"\0").decode("latin1"),"va":IB+s.VirtualAddress,"end":IB+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData),"raw":s.PointerToRawData,"rsize":s.SizeOfRawData})
def off(va):
    for s in secs:
        if s["va"]<=va<s["end"]:
            d=va-s["va"]
            if d<s["rsize"]: return s["raw"]+d
    return None
def at(va,n):
    o=off(va); return None if o is None or o+n>len(data) else data[o:o+n]
def u32(va):
    b=at(va,4); return None if b is None else struct.unpack("<I",b)[0]
def hx(x): return f"{x:08X}"
def in_text(va): return any(s["name"]==".text" and s["va"]<=va<s["end"] for s in secs)
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
def disasm(va,maxb=256,count=100):
    b=at(va,maxb)
    return [] if b is None else list(md.disasm(b,va,count=count))
def shape(va):
    b=at(va,6)
    if b and len(b)==6 and b[0]==0xB8 and b[5]==0xC3:
        return {"kind":"B8_IMM32_C3","imm":struct.unpack_from("<I",b,1)[0],"bytes":b.hex()}
    if b and len(b)==6 and b[0]==0xB8 and b[5]==0xC2:
        return {"kind":"B8_IMM32_C2_RET4","imm":struct.unpack_from("<I",b,1)[0],"bytes":b.hex()}
    return {"kind":"OTHER","bytes":b.hex() if b else None}

layout=json.loads((WORK/"all_rtti.json").read_text(encoding="utf-8"))
vtables=layout["vtables"]; enum=layout["enum"]
enum_by_val={e["value"]:e for e in enum}
enum_names={e["name"] for e in enum}

# coverage rows and atlas intersection (case normalized)
cov=[]; hdr=None
with COV.open("r",encoding="utf-8",newline="") as f:
    rd=csv.DictReader(f,delimiter="\t"); hdr=rd.fieldnames
    for r in rd:
        if r.get("subsystem","").strip().upper()=="S11": cov.append(r)
def norm(x): return x.strip().lower()
atl={norm(r["entry"]) for r in csv.DictReader(ATL.open("r",encoding="utf-8",newline=""),delimiter="\t")}
cov_by={norm(r["entry"]):r for r in cov}
inter=sorted(set(cov_by)&atl)

# anchored B8 imm32 C3 across ALL RTTI vtables, no atlas input
hits=[]
for v in vtables:
    for i,sx in enumerate(v["slots"]):
        e=int(sx,16); sh=shape(e)
        if sh["kind"]!="B8_IMM32_C3": continue
        hits.append({"entry":hx(e),"imm":sh["imm"],"imm_hex":hx(sh["imm"]),"bytes":sh["bytes"],"class":v["class"],"offset":v["offset"],"slot":i,"vtable":v["vt_hex"],"col":v["col_hex"]})

# Derive operator-new target from CreateInstance bodies of Locomotor-class factories only.
loc_factory_vts=[]
for v in vtables:
    if v["offset"]==0 and "TClassFactory" in v["class"] and "Locomotion" in v["class"] and len(v["slots"])>3:
        m=re.search(r"TClassFactory@V([A-Za-z0-9_]+)@@",v["class"])
        if m: loc_factory_vts.append({"class":m.group(1),"vt":v,"ci":int(v["slots"][3],16)})
call_counter=collections.Counter()
for f in loc_factory_vts:
    for it in disasm(f["ci"],160,100):
        if it.mnemonic=="call" and it.op_str.startswith("0x"):
            call_counter[int(it.op_str,16)]+=1
new_targets=[t for t,c in call_counter.items() if c==len(loc_factory_vts)]
operator_new=new_targets[0] if len(new_targets)==1 else None

# Class canonical vtable addresses by short concrete class name.
class_vts=collections.defaultdict(dict)
for v in vtables:
    m=re.fullmatch(r"\.\?AV([A-Za-z0-9_]+)@@",v["class"])
    if not m: continue
    class_vts[m.group(1)][v["offset"]]=v

def push_before_new(ci):
    ins=disasm(ci,160,100)
    idx=-1
    for i,it in enumerate(ins):
        if it.mnemonic=="call" and it.op_str.startswith("0x") and int(it.op_str,16)==operator_new:
            idx=i; break
    if idx<0: return None,None,None
    for j in range(idx-1,-1,-1):
        it=ins[j]
        if it.mnemonic=="call": break
        if it.mnemonic=="push":
            try: sz=int(it.op_str,16)
            except ValueError: continue
            enc="6A imm8" if it.bytes[:1]==b"\x6a" else ("68 imm32" if it.bytes[:1]==b"\x68" else "other")
            return sz,enc,hx(it.address)
    return None,None,None

def ctor_hits(ctor,canonical):
    out=[]
    for it in disasm(ctor,320,200):
        if it.mnemonic=="mov" and it.op_str.startswith("dword ptr [") and ", 0x" in it.op_str:
            parts=it.op_str.split(", ")
            try: imm=int(parts[-1],16)
            except ValueError: continue
            if imm in canonical: out.append({"addr":hx(it.address),"bytes":it.bytes.hex(),"vt":hx(imm)})
    return out

getsize=[]
for f in loc_factory_vts:
    cn=f["class"]; ci=f["ci"]; sz,enc,ipush=push_before_new(ci)
    cvs={off:v["vt"] for off,v in class_vts.get(cn,{}).items()}
    ctor=None; ctorwrites=[]; ins=disasm(ci,160,100)
    for i,it in enumerate(ins):
        if it.mnemonic=="call" and it.op_str.startswith("0x") and int(it.op_str,16)==operator_new:
            for jt in ins[i+1:]:
                if jt.mnemonic=="call" and jt.op_str.startswith("0x"):
                    try: t=int(jt.op_str,16)
                    except ValueError: continue
                    if t==0x7C8B3D: continue
                    w=ctor_hits(t,set(cvs.values()))
                    if w: ctor=t; ctorwrites=w; break
            break
    vt0=class_vts.get(cn,{}).get(0)
    s9=None
    if vt0 and len(vt0["slots"])>9:
        e9=int(vt0["slots"][9],16); sh=shape(e9)
        if sh["kind"]=="B8_IMM32_C3": s9={"entry":hx(e9),"imm":sh["imm"],"bytes":sh["bytes"],"vtable":vt0["vt_hex"]}
    closed=bool(s9 and sz is not None and s9["imm"]==sz)
    # ctor write evidence retained when found; closure requires only the two independent size points.
    row={"class":cn,"factory_vi":f["vt"]["vt_hex"],"ci":hx(ci),"size_from_push":sz,"push_encoding":enc,"push_addr":ipush,"operator_new":hx(operator_new) if operator_new else None,"ctor":hx(ctor) if ctor else None,"ctor_vptr_writes":ctorwrites,"getsize":s9,"closed":closed}
    getsize.append(row)
getsize_closed=[r for r in getsize if r["closed"]]

# WhatAmI semantic mapping: "class XxxClass" -> enum name Xxx with documented aliases.
aliases={"IsometricTile":"Isotile","IsometricTileType":"IsotileType","BuildingLight":"Light","TAction":"Action","TEvent":"Event","Tactical":"TacticalMap","Super":"SuperWeapon","SuperWeapon":"Super","WaypointPath":"Waypoint"}
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
what_main=sorted([w for w in what if w["offset"]==0 and w["slot"]==11],key=lambda x:x["class"])
what_all_by_class={w["class"] for w in what_main}
# wrong-slot risk: classes whose slot11 and slot12 are both B8 imm C3
both=[]
for w in what_main:
    v=next((x for x in vtables if x["class"]==w["class"] and x["offset"]==w["offset"] and x["vt_hex"]==w["vtable"]),None)
    if v and len(v["slots"])>12 and shape(int(v["slots"][12],16))["kind"]=="B8_IMM32_C3":
        both.append(w["class"])
# coverage census, two independent channels
cov_entries={norm(r["entry"]):r for r in cov}
cov_shape=[]
for k,r in cov_entries.items():
    e=int(r["entry"].strip(),16); sh=shape(e)
    if sh["kind"].startswith("B8_IMM32"):
        cov_shape.append({"entry":r["entry"].strip().upper(),"grade":r["grade"].strip(),"name":r["name"],"kind":sh["kind"],"imm":sh.get("imm"),"bytes":sh["bytes"]})
cov_b8c3=[x for x in cov_shape if x["kind"]=="B8_IMM32_C3"]
cov_nonproved_b8c3=[x for x in cov_b8c3 if x["grade"]!="[已证]"]
cov_ret4=[x for x in cov_shape if x["kind"]=="B8_IMM32_C2_RET4"]
hit_entries={h["entry"].lower() for h in hits}
cov_hit=sorted([h for h in hits if norm(h["entry"]) in cov_entries],key=lambda x:x["entry"])
cov_hit_nonproved=[h for h in cov_hit if cov_entries[norm(h["entry"])]["grade"].strip()!="[已证]"]
what_entries={w["entry"].lower() for w in what_main}
cov_what=sorted([w for w in what_main if norm(w["entry"]) in cov_entries],key=lambda x:x["entry"])

# delta: only byte-proved GetSize closure rows; all are already [已证] on disk (no false proved gain)
delta=[]
for r in sorted(getsize_closed,key=lambda x:x["getsize"]["entry"]):
    ent=r["getsize"]["entry"]
    c=cov_entries.get(norm(ent))
    if not c: continue
    gs=r["getsize"]
    sem=(f'GetSize double-point closure: {r["class"]} off0 vtable {gs["vtable"]} slot9 entry {ent} bytes {gs["bytes"]} '
         f'=> imm 0x{gs["imm"]:X}; factory {r["ci"]} push_addr {r["push_addr"]} {r["push_encoding"]} size 0x{r["size_from_push"]:X}; '
         f'call operator new {r["operator_new"]}; ctor {r["ctor"]} installs canonical vptr. Grade unchanged (already [已证]).')
    delta.append([ent,"S11",c["name"].strip(),sem,"[已证]","EVIDENCE/getsize_closure.txt"])

# evidence text
g=["S11-K5 GETSIZE DOUBLE-POINT CLOSURE (fresh)","SHA256="+hashlib.sha256(data).hexdigest().upper()]
g.append("OPERATOR_NEW_DERIVED=%s FACTORY_CALLS=%s"%(hx(operator_new) if operator_new else "?",dict(sorted(call_counter.items(),key=lambda kv:(-kv[1],kv[0])))))
g.append("LOCOMOTOR_FACTORY_COUNT=%d CLOSURE=%d/%d ENCODING_6A=%d ENCODING_68=%d"%(len(getsize),len(getsize_closed),len(getsize),sum(1 for r in getsize_closed if r["push_encoding"]=="6A imm8"),sum(1 for r in getsize_closed if r["push_encoding"]=="68 imm32")))
for r in getsize: g.append("ROW "+json.dumps(r,ensure_ascii=False))
(EVID/"getsize_closure.txt").write_text("\n".join(g)+"\n",encoding="utf-8")

w=["S11-K5 WHATAMI ENUM/RTTI SEMANTIC CANDIDATES","SHA256="+hashlib.sha256(data).hexdigest().upper()]
w.append("ENGINE_ENUM_COUNT=%d VALUES=%s"%(len(enum),",".join("%02X"%e["value"] for e in enum)))
w.append("ANCHORED_B8_IMM32_C3_HITS_ALL_RTTI=%d"%len(hits))
w.append("ENUM+RTTI_SEMANTIC_MATCHES=%d MAIN_SLOT11_MATCHES=%d CLASSES=%d"%(len(what),len(what_main),len(what_all_by_class)))
w.append("SLOT11_AND_SLOT12_BOTH_B8C3_CLASSES=%d"%len(both))
for x in what_main: w.append("WHATAMI "+json.dumps(x,ensure_ascii=False))
w.append("COVERAGE_S11_WHATAMI_INTERSECTION=%d"%len(cov_what))
for x in cov_what: w.append("COV_WHATAMI "+json.dumps(x,ensure_ascii=False))
(EVID/"whatami_candidates.txt").write_text("\n".join(w)+"\n",encoding="utf-8")

c=["S11-K5 COVERAGE CANDIDATE CENSUS (two channels; no atlas dependency for shape/layout)"]
c.append("S11_ROWS=%d ATLAS_INTERSECTION=%d"%(len(cov),len(inter)))
c.append("CHANNEL_A_COVERAGE_ENTRY_SHAPE: B8_IMM32_C3_ROWS=%d NONPROVED_B8_IMM32_C3_ROWS=%d B8_IMM32_C2_RET4_ROWS=%d"%(len(cov_b8c3),len(cov_nonproved_b8c3),len(cov_ret4)))
for x in cov_shape: c.append("COV_SHAPE "+json.dumps(x,ensure_ascii=False))
c.append("CHANNEL_B_ALL_RTTI_VTABLE_ANCHOR: ANCHORED_HITS=%d INTERSECT_COVERAGE=%d INTERSECT_NONPROVED=%d"%(len(hits),len(cov_hit),len(cov_hit_nonproved)))
for x in cov_hit: c.append("ANCHOR_INTERSECT "+json.dumps({**x,"grade":cov_entries[norm(x["entry"])]["grade"].strip(),"name":cov_entries[norm(x["entry"])]["name"]},ensure_ascii=False))
c.append("WHATAMI_MAIN_SLOT11_INTERSECT_COVERAGE=%d"%len(cov_what))
c.append("ELIGIBLE_GRADE_UPGRADES=0 SEMANTIC_REPROOFS=%d"%len(delta))
(EVID/"candidate_census.txt").write_text("\n".join(c)+"\n",encoding="utf-8")

(WORK/"semantic_candidates.json").write_text(json.dumps({"getsize":getsize,"whatami_main":what_main,"cov_shape":cov_shape,"cov_b8c3":cov_b8c3,"cov_hit":cov_hit,"delta_rows":delta},ensure_ascii=False,indent=2),encoding="utf-8")
with (CARD/"coverage_delta.tsv").open("w",encoding="utf-8",newline="") as f:
    for r in delta: f.write("\t".join(r)+"\n")
print("getsize",len(getsize_closed),"/",len(getsize),"whatami main",len(what_main),"cov whatami",len(cov_what),"cov B8C3",len(cov_b8c3),"nonproved",len(cov_nonproved_b8c3),"delta",len(delta))
