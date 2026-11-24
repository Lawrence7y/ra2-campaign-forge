#!/usr/bin/env python3
"""S11-K5 fresh full-RTTI/vtable reconstruction. Read-only PE; no atlas input.

Name rule: TypeDescriptor is COL+0xC; TD+8 is an INLINE name string, never a pointer.
Vtable rule: .rdata dword pointing to COL is vtable[-1]; slots start at +4 and stop at first non-.text dword.
"""
from pathlib import Path
import pefile,struct,re,json,hashlib
ROOT=Path(r"D:\Project\ra2-campaign-forge")
EXE=ROOT/"ra2youli/gamemd.exe"; CARD=ROOT/"lead/next_re_20261117_r14/S10_K3"
WORK=CARD/"work"; EVID=CARD/"EVIDENCE"
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
def u32(va):
    o=off(va)
    return None if o is None or o+4>len(data) else struct.unpack_from("<I",data,o)[0]
def cstr(va,n=256):
    o=off(va)
    if o is None: return None
    b=data[o:o+n]; z=b.find(b"\0")
    if z<0: return None
    try: return b[:z].decode("ascii")
    except UnicodeDecodeError: return None
def in_sec(va,name):
    s=next((x for x in secs if x["name"]==name),None)
    return bool(s and s["va"]<=va<s["end"])
def hx(x): return f"{x:08X}"

# 1) all TDs with MSVC RTTI class names inline at TD+8
tds={}
pat=re.compile(rb"\.\?A[VU][A-Za-z0-9_?@$]{0,180}@@\x00")
for s in secs:
    if s["rsize"]<=0: continue
    st=s["raw"]; en=min(len(data),st+s["rsize"])
    for m in pat.finditer(data[st:en]):
        name_va=s["va"]+m.start(); name=m.group()[:-1].decode("ascii"); td=name_va-8
        if u32(td+4)!=0 or cstr(name_va)!=name: continue
        pvf=u32(td)
        if pvf is None or not in_sec(pvf,".rdata"): continue
        tds[td]={"td":td,"td_hex":hx(td),"name":name,"name_va":name_va,"pvf":pvf,"pvf_hex":hx(pvf)}

# 2) COL descriptors: COL+0xC -> TD
cols={}
for s in secs:
    if s["rsize"]<=0: continue
    st=s["raw"]; en=min(len(data),st+s["rsize"])
    for rel in range(0,en-st-3,4):
        val=struct.unpack_from("<I",data,st+rel)[0]
        if val not in tds: continue
        va=s["va"]+rel; col=va-0xC
        if not in_sec(col,".rdata"): continue
        if u32(col)!=0 or u32(col+0xC)!=val: continue
        cols[col]={"col":col,"col_hex":hx(col),"td":val,"class":tds[val]["name"],"offset":u32(col+4),"cd":u32(col+8)}

# 3) vtables from .rdata refs to COL; stop at first non-.text dword
vtables=[]; nslots=0
rd=next(s for s in secs if s["name"]==".rdata")
for rel in range(0,rd["rsize"]-3,4):
    va=rd["va"]+rel; val=struct.unpack_from("<I",data,rd["raw"]+rel)[0]
    if val not in cols: continue
    c=cols[val]; vt=va+4; slots=[]
    while True:
        f=u32(vt+4*len(slots))
        if f is None or not in_sec(f,".text"): break
        slots.append(f)
        if len(slots)>400: break
    if not slots: continue
    nslots+=len(slots)
    vtables.append({"vt":vt,"vt_hex":hx(vt),"col":val,"col_hex":hx(val),"class":c["class"],"offset":c["offset"],"nslots":len(slots),"slots":[hx(x) for x in slots]})
vtables.sort(key=lambda v:(v["class"],v["offset"],v["vt"]))

# 4) engine AbstractType name table at 0x816EE0: 74 entries {char* name,u32 value}
enum=[]; enum_va=0x816EE0
for i in range(100):
    ent=enum_va+8*i; nptr=u32(ent); val=u32(ent+4)
    if nptr is None or val is None: break
    nm=cstr(nptr,64)
    if nm is None or not re.fullmatch(r"[A-Za-z0-9_<>+-]{1,40}",nm): break
    enum.append({"index":i,"entry_va":hx(ent),"name_ptr":hx(nptr),"name":nm,"value":val,"value_hex":hx(val)})
enum=sorted(enum,key=lambda x:x["value"])
values=[e["value"] for e in enum]
enum_ok=(len(enum)==74 and values==list(range(0x4A)) and len(set(values))==74)

lines=[]
lines.append("S11-K5 FULL RTTI/VTABLE RECONSTRUCTION")
lines.append("SHA256="+hashlib.sha256(data).hexdigest().upper())
lines.append("IMAGEBASE=0x%08X"%IB)
lines.append("SECTIONS="+" | ".join(f'{s["name"]}:{hx(s["va"])}..{hx(s["end"])}' for s in secs))
lines.append("TD_COUNT=%d COL_COUNT=%d VTABLE_COUNT=%d SLOTS_TOTAL=%d"%(len(tds),len(cols),len(vtables),nslots))
lines.append("ABSTRACT_TYPE_TABLE_BASE=00816EE0 COUNT=%d VALUE_SET_OK=%s"%(len(enum),enum_ok))
for e in enum: lines.append("ENUM %02d value=%02X name=%s name_ptr=%s"% (e["index"],e["value"],e["name"],e["name_ptr"]))
for td in sorted(tds):
    t=tds[td]; lines.append("TD %s name=%s name_va=%s pVF=%s"%(t["td_hex"],t["name"],hx(t["name_va"]),t["pvf_hex"]))
for c in sorted(cols):
    c=cols[c]; lines.append("COL %s off=%d td=%s class=%s cd=%d"%(c["col_hex"],c["offset"],hx(c["td"]),c["class"],c["cd"]))
for v in vtables:
    lines.append("VT %s COL=%s off=%d class=%s n=%d"%(v["vt_hex"],v["col_hex"],v["offset"],v["class"],v["nslots"]))
    for i,s in enumerate(v["slots"]): lines.append("  [%02d] %s"%(i,s))
(WORK/"all_rtti.json").write_text(json.dumps({"tds":tds,"cols":cols,"vtables":vtables,"enum":enum,"enum_ok":enum_ok},ensure_ascii=False,indent=2),encoding="utf-8")
(EVID/"all_rtti.txt").write_text("\n".join(lines)+"\n",encoding="utf-8")
el=["S11-K5 ABSTRACT TYPE TABLE (engine name table 0x00816EE0)","COUNT=%d VALUE_SET_OK=%s"%(len(enum),enum_ok)]
el += ["%02d %02X %s ptr=%s"%(e["index"],e["value"],e["name"],e["name_ptr"]) for e in enum]
(EVID/"abstract_type_enum.txt").write_text("\n".join(el)+"\n",encoding="utf-8")
print("TD",len(tds),"COL",len(cols),"VT",len(vtables),"SLOTS",nslots,"ENUM",len(enum),"OK",enum_ok)
if not enum_ok: raise SystemExit(2)
