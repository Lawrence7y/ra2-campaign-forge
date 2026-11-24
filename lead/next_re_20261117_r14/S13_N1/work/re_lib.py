from __future__ import annotations
import os, sys, struct, hashlib, re, csv
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
ATLAS = os.path.join(ROOT, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
COV = os.path.join(ROOT, "lead", "next_re_20261117_r14", "COVERAGE", "coverage.tsv")
OUT = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.join(os.path.dirname(OUT), "EVIDENCE")
PE = pefile.PE(EXE, fast_load=True)
BASE = PE.OPTIONAL_HEADER.ImageBase
SEGS = []
for s in PE.sections:
    va = BASE + s.VirtualAddress
    SEGS.append((va, va + max(s.Misc_VirtualSize, s.SizeOfRawData), s.PointerToRawData, s.SizeOfRawData, s.Name.rstrip(b"\x00").decode("latin1")))
SEGS.sort()
def va_off(va):
    for lo, hi, raw, rawsz, name in SEGS:
        if lo <= va < hi:
            d = va - lo
            if d >= rawsz: raise ValueError(f"VA {va:#x} in {name} beyond raw")
            return raw + d, name
    raise KeyError(f"unmapped VA {va:#x}")
def read(va, n):
    off, _ = va_off(va); return PE.__data__[off:off+n]
def u32(va): return struct.unpack_from("<I", read(va,4))[0]
def u16(va): return struct.unpack_from("<H", read(va,2))[0]
def cstr(va, maxn=512):
    b=read(va,maxn); z=b.find(b"\x00"); return b[:z if z>=0 else len(b)]
def sha(): return hashlib.sha256(open(EXE,"rb").read()).hexdigest().upper()
MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.detail=True; MD.skipdata=True
def dis(va,n=512): return list(MD.disasm(read(va,n),va))
def fmt(i): return f"{i.address:08X}  {i.bytes.hex():<20} {i.mnemonic} {i.op_str}".rstrip()
def load_tsv(path):
    with open(path,"r",encoding="utf-8-sig",newline="") as f:
        lines=[x.rstrip("\r\n") for x in f if x.strip()]
    hdr=lines[0].split("\t"); return hdr,[dict(zip(hdr,x.split("\t"))) for x in lines[1:]]
def atlas_rows(): return {int(r["entry"],16):r for r in load_tsv(ATLAS)[1]}
def cov_rows():
    with open(COV, "r", encoding="utf-8-sig", newline="") as f:
        lines=[x.rstrip("\r\n") for x in f if x.strip()]
    hdr=lines[0].split(",")
    return {int(r["entry"],16):r for r in (dict(zip(hdr,x.split("\t"))) for x in lines[1:])}
def s13_rows():
    a=atlas_rows(); c=cov_rows()
    return [(k,c[k],a[k]) for k in sorted(c) if c[k]["subsystem"].upper()=="S13" and k in a]
def residual_rows():
    return [(k,c,a) for k,c,a in s13_rows() if c.get("name","").strip().lower().startswith("sub_")]
def find_imm_refs(va,n):
    refs=[]
    for i in dis(va,n):
        try: ops=i.operands
        except Exception: continue
        for op in ops:
            if op.type==2 and BASE <= op.imm < BASE+0x1000000:
                try: s=cstr(op.imm,160)
                except Exception: s=b""
                printable = all(32<=b<127 for b in s) and len(s)>=2
                refs.append((i.address,i.mnemonic,op.imm,s.decode("latin1") if printable else ""))
    return refs
def direct_xrefs(target):
    out=[]
    for lo,hi,raw,rawsz,name in SEGS:
        if name!=".text": continue
        blob=PE.__data__[raw:raw+rawsz]
        for opc in (b"\xe8", b"\xe9"):
            for site in range(len(blob)-5):
                if blob[site]!=opc[0]: continue
                rel=struct.unpack_from("<I",blob,site+1)[0]
                if lo+site+5+rel==target: out.append(lo+site)
    return sorted(out)
def rtti_name_from_vt(vt):
    try: col=u32(vt-4)
    except Exception: return None
    if not (BASE<=col<BASE+0x1000000): return None
    try:
        td=u32(col+12)
        nm=cstr(td+8,256).decode("latin1")
    except Exception: return None
    if nm.startswith("."): nm=nm[1:]
    if re.fullmatch(r"\?AV[A-Za-z0-9_@]+@@",nm): return nm
    return None
def vt_slots_for_entry(entry):
    hits=[]; pat=struct.pack("<I",entry)
    for lo,hi,raw,rawsz,name in SEGS:
        blob=PE.__data__[raw:raw+rawsz]; st=0
        while True:
            p=blob.find(pat,st)
            if p<0: break
            va=lo+p; st=p+1
            if (va-lo)%4: continue
            for slot in range(0,80):
                vt=va-4*slot
                nm=rtti_name_from_vt(vt)
                if nm: hits.append({"addr":va,"vt":vt,"slot":slot,"class":nm}); break
    return hits

def fn_ins(entry, size=None):
    if size is None:
        try: size=int(atlas_rows()[entry].get("size","512"))
        except Exception: size=512
    out=[]
    for i in dis(entry,max(16,int(size))):
        if i.id==0: continue
        out.append(i)
        if i.mnemonic.startswith("ret") or i.mnemonic in ("jmp","jmpf"): break
    return out
def printable_imm_refs(entry, size=None):
    refs=[]
    for i in fn_ins(entry,size):
        try: ops=i.operands
        except Exception: continue
        for op in ops:
            if op.type==2 and BASE <= op.imm < BASE+0x1000000:
                try: s=cstr(op.imm,160)
                except Exception: s=b""
                if all(32<=b<127 for b in s) and len(s)>=2:
                    refs.append((i.address,i.mnemonic,op.imm,s.decode("latin1")))
    return refs
