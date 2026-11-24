#!/usr/bin/env python3
"""Fresh S11-K4 byte-level proof engine. Binary read-only.

Inputs: work/layout.json from rebuild_layout.py.
Outputs:
  work/closure.json, EVIDENCE/closure.txt: 2-point GetSize + ctor install + encodings
  work/entry_evidence.json, EVIDENCE/entry_evidence.txt: per-entry vtable/RTTI bytes
  work/shape_scan.json, EVIDENCE/shape_scan.txt: bare B8 imm32 C3 baseline/counterexamples
No prior-card data is imported. capstone skipdata=True is used for all instruction reads.
"""
from pathlib import Path
import json,struct,re,hashlib,collections
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32

ROOT=Path(r"D:\Project\ra2-campaign-forge"); CARD=ROOT/"lead/next_re_20261117_r14/S11_K4"
EXE=ROOT/"ra2youli/gamemd.exe"; WORK=CARD/"work"; EVID=CARD/"EVIDENCE"
data=EXE.read_bytes(); pe=pefile.PE(str(EXE),fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
sec=[]
for s in pe.sections:
    sec.append({"name":s.Name.rstrip(b"\0").decode("latin1"),"va":IB+s.VirtualAddress,"end":IB+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData),"raw":s.PointerToRawData,"rsize":s.SizeOfRawData})
def so(va):
    for s in sec:
        if s["va"]<=va<s["end"]:
            d=va-s["va"]
            if d<s["rsize"]: return s["raw"]+d
    return None
def u32(va):
    o=so(va)
    return None if o is None else struct.unpack_from("<I",data,o)[0]
def bytes_at(va,n):
    o=so(va)
    return None if o is None else data[o:o+n]
def in_text(va): return any(s["name"]==".text" and s["va"]<=va<s["end"] for s in sec)
def hx(x): return f"{x:08X}"
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
layout=json.loads((WORK/"layout.json").read_text(encoding="utf-8"))
vtables=layout["vtables"]; tds=layout["tds"]

def short(mangled):
    m=re.search(r"TClassFactory@V([A-Za-z0-9_]+)@@",mangled)
    if m: return m.group(1),"factory"
    m=re.match(r"\.>\?AV([A-Za-z0-9_]+)@@".replace(">","?"),mangled) # unused
    m=re.match(r"\.\?AV([A-Za-z0-9_]+)@@",mangled)
    return (m.group(1), "class") if m else (mangled,"class")

def disasm(va,maxb=128,count=40):
    b=bytes_at(va,maxb)
    if b is None: return []
    return list(md.disasm(b,va,count=count))

def find_call(insts,target):
    for i,it in enumerate(insts):
        if it.mnemonic=="call" and it.op_str.startswith("0x"):
            try: t=int(it.op_str,16)
            except ValueError: continue
            if t==target: return i,it
    return None,-1

def imm_size_and_enc(ci):
    """Parse push imm8/imm32 before call 0x7C8E17 in CreateInstance body."""
    ins=disasm(ci,maxb=160,count=80)
    idx,_=find_call(ins,0x7C8E17)
    if idx<0: return None,None,None,ins
    # nearest preceding push imm; require no other call between push and new
    for j in range(idx-1,-1,-1):
        it=ins[j]
        if it.mnemonic=="call": break
        if it.mnemonic=="push" and it.op_str.startswith("0x"):
            try: sz=int(it.op_str,16)
            except ValueError: continue
            enc="6A imm8" if it.bytes[0]==0x6A else ("68 imm32" if it.bytes[0]==0x68 else "other")
            return sz,enc,hx(it.address),ins
    return None,None,None,ins

def ctor_writes(ctor,class_vts):
    ins=disasm(ctor,maxb=320,count=160)
    targets=set(int(x,16) for x in class_vts)
    hits=[]
    for it in ins:
        if it.mnemonic=="mov" and ", 0x" in it.op_str:
            parts=it.op_str.split(", ")
            try: imm=int(parts[-1],16)
            except ValueError: continue
            if imm in targets: hits.append((hx(it.address),it.bytes.hex(),hx(imm)))
    return hits

# Map class short name to its canonical table addresses.
class_tables=collections.defaultdict(dict)
for v in vtables:
    if "TClassFactory" not in v["class"]:
        cn,_=short(v["class"]); class_tables[cn][v["offset"]]=v

closure=[]; lines=[]
lines.append("S11-K4 FRESH TWO-POINT GETSIZE CLOSURE")
lines.append("SHA256="+hashlib.sha256(data).hexdigest().upper())
lines.append("RULE: A=off0 slot9 B8<imm32>C3; B=factory vslot3 push<size>;call 0x7C8E17; ctor installs canonical off0/off4 vtables.")
for v in vtables:
    if "TClassFactory" not in v["class"]: continue
    cn,_=short(v["class"])
    ci=int(v["slots"][3],16)
    sz,enc,ipush,ins=imm_size_and_enc(ci)
    ctor=None; ctorhits=[]
    # first call after new to a non-operator-delete target is ctor; choose one whose body installs class vtables
    newi,_=find_call(ins,0x7C8E17)
    if newi>=0:
        for it in ins[newi+1:]:
            if it.mnemonic=="call" and it.op_str.startswith("0x"):
                try: t=int(it.op_str,16)
                except ValueError: continue
                if t==0x7C8B3D: continue
                hits=ctor_writes(t,[x["vt_hex"] for k,x in class_tables.get(cn,{}).items()])
                if hits: ctor=t; ctorhits=hits; break
    cls=class_tables.get(cn,{})
    vt0=cls.get(0,{}).get("vt_hex",""); slot9=cls.get(0,{}).get("slots",[None]*10)[9] if 0 in cls else None
    b9=bytes_at(int(slot9,16),6) if slot9 else None
    imm9=None
    if b9 and len(b9)>=6 and b9[0]==0xB8 and b9[5]==0xC3: imm9=struct.unpack_from("<I",b9,1)[0]
    ok=bool(imm9 is not None and sz is not None and imm9==sz and ctor is not None)
    rec={"class":cn,"factory_vt":v["vt_hex"],"factory_ci":hx(ci),"ci_push_addr":ipush,"size_from_push":sz,"push_encoding":enc,"operator_new":"7C8E17","ctor":hx(ctor) if ctor else None,"ctor_vptr_writes":ctorhits,"off0_vt":vt0,"off0_slot9":slot9,"slot9_bytes":b9.hex() if b9 else None,"slot9_imm":imm9,"closed":ok}
    closure.append(rec)
    lines.append(f'CLASS={cn} CI={hx(ci)} push={ipush}/{enc} size={sz} new=7C8E17 ctor={hx(ctor) if ctor else "?"} vptr_writes={ctorhits} off0VT={vt0} slot9={slot9} bytes={b9.hex() if b9 else "?"} imm={imm9} CLOSED={ok}')
lines.append("CLOSURE_TOTAL=%d/%d"%(sum(1 for r in closure if r["closed"]),len(closure)))
lines.append("ENCODING_6A=%d ENCODING_68=%d"%(sum(1 for r in closure if r["push_encoding"]=="6A imm8"),sum(1 for r in closure if r["push_encoding"]=="68 imm32")))
stub=hx(0x4C9150); lines.append("SHARED_STUB_4C9150_BYTES="+bytes_at(0x4C9150,3).hex()+" EXCLUDED_FROM_CONCRETE_CLOSURE")
(WORK/"closure.json").write_text(json.dumps(closure,indent=2),encoding="utf-8")
(EVID/"closure.txt").write_text("\n".join(lines)+"\n",encoding="utf-8")

# Baseline: bare B8 imm32 C3 in .text and slot-context hits.
alltext=bytes_at(sec[0]["va"],sec[0]["end"]-sec[0]["va"])
bare=[]; start=sec[0]["va"]
for i in range(len(alltext)-5):
    if alltext[i]==0xB8 and alltext[i+5]==0xC3:
        va=start+i; imm=struct.unpack_from("<I",alltext,i+1)[0]
        bare.append((va,imm))
# anchored: vtable slots whose entry starts B8 imm32 C3
anchored=[]
for v in vtables:
    if "TClassFactory" in v["class"]: continue
    cn,_=short(v["class"])
    for idx,sx in enumerate(v["slots"]):
        e=int(sx,16); b=bytes_at(e,6)
        if b and b[0]==0xB8 and b[5]==0xC3:
            anchored.append({"class":cn,"offset":v["offset"],"slot":idx,"entry":sx,"imm":struct.unpack_from("<I",b,1)[0],"is_getsize":(v["offset"]==0 and idx==9),"is_stub":(e==0x4C9150)})
sl=[]
sl.append("S11-K4 B8 imm32 C3 SHAPE BASELINE")
sl.append("BARE_TEXT_COUNT=%d"%len(bare))
sl.append("ANCHORED_LOCOMOTION_VTABLE_COUNT=%d"%len(anchored))
sl.append("ANCHORED_GETSIZE_COUNT=%d"%sum(1 for a in anchored if a["is_getsize"]))
sl.append("ANCHORED_NON_GETSIZE_COUNT=%d"%sum(1 for a in anchored if not a["is_getsize"]))
sl.append("ANCHORED_SHARED_STUB_COUNT=%d"%sum(1 for a in anchored if a["is_stub"]))
for a in anchored: sl.append("ANCHOR "+json.dumps(a,ensure_ascii=False))
# documented non-size counterexamples: entries with B8/C3 returning 0x7FFFFFFF or data VA, if present
ce=[a for a in anchored if a["imm"] in (0x7FFFFFFF,0x8182E0)]
sl.append("DOCUMENTED_NON_SIZE_IMM_HITS=%d"%len(ce))
for a in ce: sl.append("COUNTEREXAMPLE "+json.dumps(a,ensure_ascii=False))
(WORK/"shape_scan.json").write_text(json.dumps({"bare_count":len(bare),"anchored":anchored},indent=2),encoding="utf-8")
(EVID/"shape_scan.txt").write_text("\n".join(sl)+"\n",encoding="utf-8")

# Per-entry evidence from vtable dwords.
entry=collections.defaultdict(list)
for v in vtables:
    cn,_=short(v["class"])
    for idx,sx in enumerate(v["slots"]):
        e=int(sx,16)
        slot_va=int(v["vt_hex"],16)+4*idx
        entry[e].append({"class":cn,"mangled":v["class"],"interface_offset":v["offset"],"slot":idx,"vtable":v["vt_hex"],"col":v["col_hex"],"td":tds[next(k for k,x in tds.items() if x["name"]==v["class"])]["td_hex"],"slot_va":hx(slot_va),"slot_bytes":bytes_at(slot_va,4).hex(),"entry_bytes":bytes_at(e,16).hex(),"first_asm":"; ".join(f'{i.mnemonic} {i.op_str}' for i in disasm(e,maxb=32,count=4))})
el=[]
el.append("S11-K4 PER-ENTRY VTABLE/RTTI BYTE EVIDENCE")
el.append("Each row: entry, all vtable occurrences; vtable dword bytes are the direct pointer to this entry; TD name from COL+0xC -> TD+8 inline string.")
for e in sorted(entry):
    el.append(f"ENTRY {hx(e)} OCCURRENCES={len(entry[e])}")
    for o in entry[e]: el.append("  "+json.dumps(o,ensure_ascii=False))
(WORK/"entry_evidence.json").write_text(json.dumps({hx(k):v for k,v in entry.items()},indent=2),encoding="utf-8")
(EVID/"entry_evidence.txt").write_text("\n".join(el)+"\n",encoding="utf-8")
print("closure",sum(1 for r in closure if r["closed"]),"/",len(closure),"enc",sum(1 for r in closure if r["push_encoding"]=="6A imm8"),sum(1 for r in closure if r["push_encoding"]=="68 imm32"))
print("bare",len(bare),"anchored",len(anchored),"non-getsize",sum(1 for a in anchored if not a["is_getsize"]))
print("entries",len(entry),"wrote evidence files")
