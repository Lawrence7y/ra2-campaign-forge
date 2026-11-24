#!/usr/bin/env python3
"""S06-K4 strict semantic proof pass: WhatAmI (type 1) and GetSize (type 2) only."""
from pathlib import Path
import pefile,struct,json,csv,re,hashlib,bisect,collections
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
ROOT=Path(r"D:\Project\ra2-campaign-forge")
EXE=ROOT/"ra2youli/gamemd.exe"; COV=ROOT/"lead/next_re_20261117_r14/COVERAGE/coverage.tsv"
ATL=ROOT/"lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv"
CARD=ROOT/"lead/next_re_20261117_r14/S06_K4"; WORK=CARD/"work"; EVID=CARD/"EVIDENCE"
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
def hx(x): return f"{x:08X}"
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
def dis(va,n=256,c=120):
    b=at(va,n); return [] if b is None else list(md.disasm(b,va,count=c))
def shape(va):
    b=at(va,6)
    if b and len(b)==6 and b[0]==0xB8 and b[5]==0xC3:
        return {"kind":"B8_IMM32_C3","imm":struct.unpack_from("<I",b,1)[0],"bytes":b.hex()}
    return {"kind":"OTHER","bytes":b.hex() if b else None}
text=next(s for s in secs if s["name"]==".text")
call_targets=set(); callsites_by_target=collections.defaultdict(list)
for i in range(text["rsize"]-4):
    if data[text["raw"]+i]==0xE8:
        rel=struct.unpack_from("<i",data,text["raw"]+i+1)[0]; src=text["va"]+i; dst=src+5+rel
        if text["va"]<=dst<text["end"]:
            call_targets.add(dst); callsites_by_target[dst].append(src)
tlist=sorted(call_targets)
def enclosing(va):
    i=bisect.bisect_right(tlist,va)-1
    return tlist[i] if i>=0 else None
layout=json.loads((WORK/"all_rtti.json").read_text(encoding="utf-8"))
vtables=layout["vtables"]; enum=layout["enum"]; enum_by_val={e["value"]:e for e in enum}
factories=[v for v in vtables if "TClassFactory" in v["class"] and v["offset"]==0 and len(v["slots"])>3]
cnt=collections.Counter()
for v in factories:
    ci=int(v["slots"][3],16)
    for it in dis(ci,192,120):
        if it.mnemonic=="call" and it.op_str.startswith("0x"): cnt[int(it.op_str,16)]+=1
op_new,op_new_n=cnt.most_common(1)[0]
if op_new_n!=len(factories): raise SystemExit(f"operator_new not common: {op_new_n}/{len(factories)}")
def norm(x): return x.strip().lower()
with COV.open("r",encoding="utf-8",newline="") as f: cov=[r for r in csv.DictReader(f,delimiter="\t") if r.get("subsystem","").strip().upper()=="S06"]
with ATL.open("r",encoding="utf-8",newline="") as f: atl={norm(r["entry"]) for r in csv.DictReader(f,delimiter="\t")}
cov_by={norm(r["entry"].strip()):r for r in cov}
def ctor_vptr_writes(cls,vt):
    pat=struct.pack("<I",vt); out=[]; seen=set()
    for i in range(text["rsize"]-3):
        if data[text["raw"]+i:text["raw"]+i+4]!=pat: continue
        va=text["va"]+i; e=enclosing(va)
        if e is None or e in seen: continue
        for it in dis(e,1024,400):
            if it.mnemonic!="mov" or not it.op_str.startswith("dword ptr ["): continue
            m=re.search(r",\s*0x([0-9A-Fa-f]+)$",it.op_str)
            if m and int(m.group(1),16)==vt:
                seen.add(e); out.append({"ctor":hx(e),"addr":hx(it.address),"bytes":it.bytes.hex(),"op":it.op_str}); break
    return out
def factory_size_evidence(cls,expected):
    cls_short=cls[5:-2] if cls.startswith(".?AV") and cls.endswith("@@") else cls
    fv=next((v for v in factories if cls_short in v["class"]),None)
    if not fv: return None
    ci=int(fv["slots"][3],16); ins=dis(ci,192,120)
    idx=next((i for i,it in enumerate(ins) if it.mnemonic=="call" and it.op_str.startswith("0x") and int(it.op_str,16)==op_new),None)
    if idx is None: return None
    for j in range(idx-1,max(-1,idx-20),-1):
        it=ins[j]
        if it.mnemonic=="call": break
        if it.mnemonic!="push": continue
        try: sz=int(it.op_str,16)
        except ValueError: continue
        enc="68 imm32" if it.bytes[:1]==b"\x68" else ("6A imm8" if it.bytes[:1]==b"\x6a" else "other")
        if sz==expected:
            return {"kind":"factory","factory_vt":fv["vt_hex"],"create_instance":hx(ci),"push_addr":hx(it.address),"push_bytes":it.bytes.hex(),"push_encoding":enc,"size":sz,"operator_new":hx(op_new),"new_addr":hx(ins[idx].address)}
    return None
def raw_call(va):
    o=off(va)
    if o is None or o+5>len(data) or data[o]!=0xE8: return None
    return va+5+struct.unpack_from("<i",data,o+1)[0]
def allocation_size_evidence(ctors,expected):
    for cw in ctors:
        ctor=int(cw["ctor"],16)
        for cs in callsites_by_target.get(ctor,[]):
            for back in range(cs-160,cs):
                b0=at(back,1)
                if b0 is None or b0[0] not in (0x6A,0x68): continue
                b=at(back,6 if b0[0]==0x68 else 2)
                if b is None: continue
                if b[0]==0x6A: sz=b[1]; pb=b[:2].hex(); enc="6A imm8"; step=2
                elif b[0]==0x68: sz=struct.unpack_from("<I",b,1)[0]; pb=b[:5].hex(); enc="68 imm32"; step=5
                else: continue
                if sz!=expected: continue
                new_addr=next((q for q in range(back+step,cs-4) if raw_call(q)==op_new),None)
                if new_addr is not None:
                    return {"kind":"allocation","ctor":cw["ctor"],"callsite":hx(cs),"push_addr":hx(back),"push_bytes":pb,"push_encoding":enc,"size":sz,"operator_new":hx(op_new),"new_addr":hx(new_addr)}
    return None
size_cache={}
def size_closure(cls,vt_hex,expected):
    key=(cls,vt_hex,expected)
    if key in size_cache: return size_cache[key]
    ctors=ctor_vptr_writes(cls,int(vt_hex,16))
    se=factory_size_evidence(cls,expected) or allocation_size_evidence(ctors,expected)
    out={"imm":expected,"ctor_writes":ctors,"evidence":se}
    size_cache[key]=out
    return out

anchored=collections.defaultdict(list)
for v in vtables:
    for i,sx in enumerate(v["slots"]):
        va=int(sx,16); sh=shape(va)
        if sh["kind"]=="B8_IMM32_C3": anchored[hx(va).lower()].append({"class":v["class"],"offset":v["offset"],"slot":i,"vtable":v["vt_hex"],"col":v["col_hex"],"imm":sh["imm"],"bytes":sh["bytes"]})
cands=[]
for e,r in cov_by.items():
    ent=r["entry"].strip().upper(); grade=r["grade"].strip()
    if grade=="[已证]" or e not in anchored: continue
    a=[x for x in anchored[e] if x["offset"]==0]
    if a: cands.append({"entry":ent,"grade":grade,"old_name":r["name"].strip(),"anchor":a[0]})
class_vt={}
for v in vtables:
    if v["offset"]==0 and re.fullmatch(r"\.\?AV[A-Za-z0-9_]+@@",v["class"]): class_vt.setdefault(v["class"],v)
size_evidence={}
for c in cands:
    a=c["anchor"]; cls=a["class"]; v=class_vt.get(cls)
    if not v or v["vt_hex"]!=a["vtable"] or a["slot"]!=12: continue
    ctors=ctor_vptr_writes(cls,int(v["vt_hex"],16))
    se=factory_size_evidence(cls,a["imm"]) or allocation_size_evidence(ctors,a["imm"])
    size_evidence[cls]={"slot12_entry":c["entry"],"imm":a["imm"],"bytes":a["bytes"],"ctor_writes":ctors,"evidence":se}
aliases={"IsometricTile":"Isotile","IsometricTileType":"IsotileType","BuildingLight":"Light","TAction":"Action","TEvent":"Event","Tactical":"TacticalMap","WaypointPath":"Waypoint"}
def enum_class_match(cname,ename):
    m=re.fullmatch(r"\.\?AV([A-Za-z0-9_]+)@@",cname)
    if not m or "$" in m.group(1): return False
    base=m.group(1)[:-5] if m.group(1).endswith("Class") else m.group(1)
    return ename==base or ename==aliases.get(base)
what_rows=[]; getsize_rows=[]; unknowns=[]
for c in cands:
    a=c["anchor"]; cls=a["class"]; v=class_vt.get(cls)
    if a["slot"]==11:
        en=enum_by_val.get(a["imm"])
        if not en or en["name"]=="<none>" or not enum_class_match(cls,en["name"]):
            unknowns.append({"entry":c["entry"],"reason":"slot11 enum/RTTI mismatch","anchor":a}); continue
        sh12=shape(int(v["slots"][12],16)) if v and len(v["slots"])>12 else {"kind":"NONE","bytes":None,"imm":None}
        slot12_ok=True; note="slot12 not B8/C3; no same-shape ambiguity"
        if sh12["kind"]=="B8_IMM32_C3":
            se=size_closure(cls,v["vt_hex"],sh12["imm"]); ok=bool(se["evidence"]); slot12_ok=ok
            note=f"slot12 {hx(int(v['slots'][12],16))} same-shape; object-size closure {'OK' if ok else 'MISSING'}"
        ctors=ctor_vptr_writes(cls,int(v["vt_hex"],16)) if v else []
        if not ctors or not slot12_ok:
            unknowns.append({"entry":c["entry"],"reason":"no ctor vptr write" if not ctors else "slot11/slot12 ambiguity unresolved","anchor":a}); continue
        short=re.fullmatch(r"\.\?AV([A-Za-z0-9_]+)@@",cls).group(1)
        sem=f"WhatAmI: returns AbstractType::{en['name']}=0x{a['imm']:02X}; bytes {a['bytes']}; RTTI class {cls}; canonical COL {a['col']} vt {a['vtable']} slot11; ctor {ctors[0]['ctor']} writes vptr; {note}"
        what_rows.append({"entry":c["entry"],"subsystem":"S06","name":f"{short}::WhatAmI","sem":sem,"grade":"[已证]","evidence":"EVIDENCE/whatami_proofs.txt","detail":{"anchor":a,"enum":en,"ctor":ctors,"slot12":sh12,"slot12_note":note}})
    elif a["slot"]==12:
        se=size_closure(cls,a["vtable"],a["imm"])
        if not se["evidence"]:
            unknowns.append({"entry":c["entry"],"reason":"GetSize closure missing","anchor":a}); continue
        short=re.fullmatch(r"\.\?AV([A-Za-z0-9_]+)@@",cls).group(1); ev=se["evidence"]
        sem=f"GetSize: returns object size 0x{se['imm']:X}; bytes {a['bytes']}; independent {ev['kind']} size point {ev['push_bytes']} at {ev['push_addr']} => {ev['size']} before call operator new {ev['operator_new']}; canonical vt {a['vtable']} slot12"
        getsize_rows.append({"entry":c["entry"],"subsystem":"S06","name":f"{short}::GetSize","sem":sem,"grade":"[已证]","evidence":"EVIDENCE/getsize_proofs.txt","detail":{"anchor":a,"closure":se}})
rows=sorted(what_rows+getsize_rows,key=lambda r:r["entry"])
names=collections.Counter(r["name"] for r in rows)
assert len(rows)==len({r["entry"] for r in rows})
assert all(not re.search(r"::slot\d+$",r["name"]) for r in rows)
assert all(n==1 for n in names.values()),names
with (CARD/"coverage_delta.tsv").open("w",encoding="utf-8",newline="") as f:
    for r in rows: f.write("\t".join([r["entry"],r["subsystem"],r["name"],r["sem"],r["grade"],r["evidence"]])+"\n")
wl=["S06-K4 WHATAMI PROOFS (strict type 1)","SHA256="+hashlib.sha256(data).hexdigest().upper(),"RULE=B8 imm32 C3 + enum + RTTI + canonical slot11 + slot12 disambiguation",f"OPERATOR_NEW={hx(op_new)} FACTORY_AGREEMENT={op_new_n}/{len(factories)}"]
for r in what_rows:
    d=r["detail"]; wl.append("ROW "+json.dumps({"entry":r["entry"],"name":r["name"],"bytes":d["anchor"]["bytes"],"imm":d["anchor"]["imm"],"enum_name":d["enum"]["name"],"enum_value":d["enum"]["value"],"class":d["anchor"]["class"],"col":d["anchor"]["col"],"vtable":d["anchor"]["vtable"],"slot":d["anchor"]["slot"],"ctor_writes":d["ctor"],"slot12":d["slot12"],"slot12_note":d["slot12_note"],"semantics":r["sem"]},ensure_ascii=False))
wl.append("UNRESOLVED="+str(len(unknowns)))
for u in unknowns: wl.append("UNRESOLVED "+json.dumps(u,ensure_ascii=False))
(EVID/"whatami_proofs.txt").write_text("\n".join(wl)+"\n",encoding="utf-8")
gl=["S06-K4 GETSIZE DOUBLE-POINT CLOSURE PROOFS (strict type 2)","SHA256="+hashlib.sha256(data).hexdigest().upper(),"RULE=B8 imm32 C3 slot12 + factory/allocation push(size) before operator new",f"OPERATOR_NEW={hx(op_new)} FACTORY_AGREEMENT={op_new_n}/{len(factories)}"]
for r in getsize_rows:
    d=r["detail"]; gl.append("ROW "+json.dumps({"entry":r["entry"],"name":r["name"],"bytes":d["anchor"]["bytes"],"imm":d["anchor"]["imm"],"class":d["anchor"]["class"],"vtable":d["anchor"]["vtable"],"slot":d["anchor"]["slot"],"closure":d["closure"],"semantics":r["sem"]},ensure_ascii=False))
(EVID/"getsize_proofs.txt").write_text("\n".join(gl)+"\n",encoding="utf-8")
(WORK/"proofs.json").write_text(json.dumps({"whatami":what_rows,"getsize":getsize_rows,"unknowns":unknowns,"operator_new":hx(op_new)},ensure_ascii=False,indent=2),encoding="utf-8")
print("operator_new",hx(op_new),op_new_n,"/",len(factories))
print("candidates",len(cands),"whatami",len(what_rows),"getsize",len(getsize_rows),"unknowns",len(unknowns),"delta",len(rows))
for u in unknowns: print("UNKNOWN",u["entry"],u["reason"])
