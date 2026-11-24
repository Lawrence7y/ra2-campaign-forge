#!/usr/bin/env python3
"""Fresh S11-K4 .rdata/RTTI/vtable reconstruction. Read-only binary.

No import from S11-K2 work. Uses pefile + capstone(skipdata=True) only.
Outputs work/layout.json and EVIDENCE/layout.txt (full, untruncated).
"""
from pathlib import Path
import json, struct, re, hashlib, sys
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT=Path(r"D:\Project\ra2-campaign-forge")
EXE=ROOT/"ra2youli/gamemd.exe"
CARD=ROOT/"lead/next_re_20261117_r14/S11_K4"
WORK=CARD/"work"; EVID=CARD/"EVIDENCE"
WORK.mkdir(parents=True,exist_ok=True); EVID.mkdir(parents=True,exist_ok=True)
pe=pefile.PE(str(EXE),fast_load=True)
IB=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    name=s.Name.rstrip(b"\0").decode("latin1")
    secs.append({"name":name,"va":IB+s.VirtualAddress,"end":IB+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData),"raw":s.PointerToRawData,"rsize":s.SizeOfRawData,"vsz":s.Misc_VirtualSize,"flags":s.Characteristics})
text=next(s for s in secs if s["name"]==".text")
rdata=next(s for s in secs if s["name"]==".rdata")
data=EXE.read_bytes()

def sec_of(va):
    for s in secs:
        if s["va"]<=va<s["end"]: return s
    return None
def off_of(va):
    s=sec_of(va)
    if not s: return None
    delta=va-s["va"]
    if delta>=s["rsize"]: return None
    return s["raw"]+delta
def u32(va):
    o=off_of(va)
    if o is None or o+4>len(data): return None
    return struct.unpack_from("<I",data,o)[0]
def read_cstr(va,limit=256):
    o=off_of(va)
    if o is None: return None
    b=data[o:o+limit]
    z=b.find(b"\0")
    if z<0: return None
    try: return b[:z].decode("ascii")
    except UnicodeDecodeError: return None
def in_text(va): return text["va"]<=va<text["end"]
def in_rdata(va): return rdata["va"]<=va<rdata["end"]
def hex8(x): return f"{x:08X}"

# MD: capstone skipdata=True sanity (we do not use atlas boundaries for discovery)
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True

# 1) TD candidates: RTTI name string is INLINE at TD+8, never a pointer.
tds={}
pat=re.compile(rb"\.\?AV[A-Za-z0-9_?@$]{0,120}Locomotion[A-Za-z0-9_?@$]*@@\x00")
for sec in secs:
    if sec["rsize"]<=0: continue
    start=sec["raw"]; stop=min(len(data),start+sec["rsize"])
    for m in pat.finditer(data,start,stop):
        name_va=sec["va"]+(m.start()-start)
        name=m.group()[:-1].decode("ascii")
        td=name_va-8
        pvf=u32(td); spare=u32(td+4); nm=read_cstr(name_va)
        if nm!=name: continue
        if pvf is None or not in_rdata(pvf): continue
        if spare is not None and spare!=0: continue
        tds[td]={"td":td,"td_hex":hex8(td),"name":name,"name_va":name_va,"pvf":pvf,"pvf_hex":hex8(pvf)}

# 2) COL descriptors: COL+0xC -> TD. Scan every mapped dword in image (not just .rdata) for TD.
cols={}
for s in secs:
    if s["rsize"]<=0: continue
    base=s["raw"]; lim=min(s["rsize"],len(data)-base)
    for rel in range(0,lim-3,4):
        val=struct.unpack_from("<I",data,base+rel)[0]
        if val in tds:
            va=s["va"]+rel; col=va-0xC
            if not in_rdata(col): continue
            sig=u32(col); off=u32(col+4); cd=u32(col+8); td=u32(col+0xC)
            if sig!=0 or td!=val: continue
            cols[col]={"col":col,"col_hex":hex8(col),"td":val,"class":tds[val]["name"],"offset":off,"cd":cd}

# 3) Vftables: every .rdata dword equal to a COL is vtable[-1]; vtable starts at +4.
vtables=[]
for s in secs:
    if s["name"]!=".rdata": continue
    base=s["raw"]; lim=min(s["rsize"],len(data)-base)
    for rel in range(0,lim-3,4):
        va=s["va"]+rel; val=struct.unpack_from("<I",data,base+rel)[0]
        if val not in cols: continue
        col=cols[val]; start_va=va+4
        slots=[]
        p=start_va
        while True:
            f=u32(p)
            if f is None or not in_text(f): break
            slots.append(f); p+=4
            if len(slots)>200: break
        if slots:
            vtables.append({"col":col["col"],"col_hex":col["col_hex"],"class":col["class"],"offset":col["offset"],"col_ref":va,"col_ref_hex":hex8(va),"vt":start_va,"vt_hex":hex8(start_va),"slots":[hex8(x) for x in slots],"nslots":len(slots),"after":hex8(p),"after_val":u32(p)})

vtables.sort(key=lambda v:(v["class"],v["offset"],v["vt"]))
lines=[]
lines.append("SHA256="+hashlib.sha256(data).hexdigest().upper())
lines.append("IMAGEBASE=0x%08X"%IB)
lines.append("SECTIONS="+" | ".join(f'{s["name"]}:{hex8(s["va"])}..{hex8(s["end"])}' for s in secs))
lines.append("TD_COUNT=%d"%len(tds))
for td in sorted(tds):
    t=tds[td]; lines.append(f'TD {t["td_hex"]} name={t["name"]} name_va={hex8(t["name_va"])} pVF={t["pvf_hex"]}')
lines.append("COL_COUNT=%d"%len(cols))
for c in sorted(cols):
    c=cols[c]; lines.append(f'COL {c["col_hex"]} off={c["offset"]} td={hex8(c["td"])} class={c["class"]} cd={c["cd"]}')
lines.append("VTABLE_COUNT=%d SLOTS_TOTAL=%d"%(len(vtables),sum(v["nslots"] for v in vtables)))
for v in vtables:
    lines.append(f'VT {v["vt_hex"]} COL={v["col_hex"]} off={v["offset"]} class={v["class"]} n={v["nslots"]} after={v["after"]}:{v["after_val"]}')
    for i,s in enumerate(v["slots"]):
        lines.append(f'  [{i:02d}] {s}')
(WORK/"layout.json").write_text(json.dumps({"tds":tds,"cols":cols,"vtables":vtables},indent=2,ensure_ascii=False),encoding="utf-8")
(EVID/"layout.txt").write_text("\n".join(lines)+"\n",encoding="utf-8")
print("\n".join(lines[:30]))
print("... wrote",WORK/"layout.json",EVID/"layout.txt")
