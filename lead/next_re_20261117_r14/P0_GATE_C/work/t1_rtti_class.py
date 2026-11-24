# -*- coding: utf-8 -*-
"""P0-GATE-C Task1: RTTI TypeDescriptor-based class identification (fail-closed).
Given a set of function addresses (write-point containing functions), find every
MSVC vtable slot (>=4-byte aligned dword in .rdata/.data) that equals the function
address, then walk vtable[-1] -> COL -> COL+0xC -> TD -> TD+8 = type name.
Fail-closed: if any link cannot be read, print UNRESOLVED and do NOT guess a name.
"""
import struct, pefile, hashlib, bisect
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
WANT_SHA = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
data = open(EXE,"rb").read()
assert hashlib.sha256(data).hexdigest().upper()==WANT_SHA
pe = pefile.PE(EXE, fast_load=True); BASE=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    nm=s.Name.rstrip(b"\x00").decode("latin1")
    secs.append(dict(name=nm,va=BASE+s.VirtualAddress,vsize=s.Misc_VirtualSize,raw=s.PointerToRawData,rawsize=s.SizeOfRawData))
def sec_of(va):
    for s in secs:
        if s["va"]<=va<s["va"]+max(s["vsize"],s["rawsize"]): return s
    return None
def rd(va,n):
    s=sec_of(va)
    if s is None: return b""
    o=s["raw"]+(va-s["va"]); return data[o:o+n]
def u32(va):
    b=rd(va,4)
    return struct.unpack("<I",b)[0] if len(b)==4 else None
def fo_of_va(va):
    s=sec_of(va)
    return s["raw"]+(va-s["va"]) if s else None

# build reverse index: address -> list of sections
RDSEC=[s for s in secs if s["name"] in (".rdata",".data")]

def find_dword_refs(target):
    """all VAs in read-only/data sections where a dword == target"""
    out=[]
    pat=struct.pack("<I",target)
    for s in RDSEC:
        blob=data[s["raw"]:s["raw"]+s["rawsize"]]
        i=blob.find(pat)
        while i!=-1:
            if i%4==0:  # aligned slot candidate
                out.append(s["va"]+i)
            i=blob.find(pat,i+1)
    return out

def classify_col(colva):
    """Try to interpret colva as COL; return (TD, name) or (None, reason)."""
    sig=u32(colva)
    if sig is None or sig not in (0,1): return None,"sig=%r"%sig
    ptd=u32(colva+0xC)
    if ptd is None: return None,"TD unreadable"
    # TD name at +8
    nva=ptd+8
    b=rd(nva,64)
    if not b: return None,"TD name unreadable"
    z=b.find(b"\x00")
    nm=b[:z].decode("latin1") if z!=-1 else b.decode("latin1")
    if not nm.startswith(".?A"): return None,"name not RTTI-looking: %r"%nm[:20]
    return (ptd,nm)

def vtable_info(slotva):
    """Given a VA that holds a function pointer (a vtable slot), walk back to find COL."""
    # scan backwards from slotva for a COL pointer in the preceding 4 bytes at each candidate vtable base
    # In MSVC, vtable[-1] = COL, slots start at vtable[0]. We don't know vtable base; try all aligned positions
    # p such that p<=slotva, u32(p-4) is COL, and (slotva-p)%4==0.
    results=[]
    for back in range(0,0x400,4):
        vb=slotva-back
        col=u32(vb-4)
        if col is None: continue
        ci=classify_col(col)
        if ci[0] is not None:
            results.append((vb,col,ci[0],ci[1],back//4))
            break
    return results

# write-point containing functions from Task1
FNS = {
 0x45DD90:["16BF@45E145","16BE@45E13F","16B7@45E115","E58@45DE5E"],
 0x45FE95:["16BF@460ABA","16BE@460AAF","16B7@460A13"],
 0x465010:["E58@465210"], 0x465450:["E58@465531"], 0x465CC0:["E58@465D18"],
 0x5239D0:["E58@523AF8"], 0x524D70:["E58@524E98"],
 0x7470D0:["E58@7471A5"], 0x747620:["E58@747BC4"], 0x74800A:["E58@748098"],
}
print("SHA256", hashlib.sha256(data).hexdigest().upper())
print("=== RTTI class identification for write-point functions (fail-closed) ===")
for f, tags in FNS.items():
    refs=find_dword_refs(f)
    print("\nfn %08X  tags=%s  dword-ref-sites=%d" % (f,",".join(tags),len(refs)))
    if not refs:
        print("  NOT a vtable slot (no aligned dword ref in .rdata/.data) -> class via vtable UNRESOLVED")
        continue
    seen=set()
    for r in refs:
        vi=vtable_info(r)
        for vb,col,td,nm,idx in vi:
            key=(vb,col,td,nm)
            if key in seen: continue
            seen.add(key)
            print("  slot@%08X -> vtable %08X slotidx=%d COL %08X TD %08X name=%s" % (r,vb,idx,col,td,nm))

# Also: find HouseClass TD and all its vtables, list the write-point fns that appear
print("\n=== HouseClass RTTI chain ===")
hname=b".?AVHouseClass@@"
i=data.find(hname)
if i<0:
    print("HouseClass type name NOT FOUND -> fail-closed")
else:
    va,_=None,None
    for s in secs:
        if s["raw"]<=i<s["raw"]+s["rawsize"]:
            va=s["va"]+(i-s["raw"]); break
    TD=va-8
    print("name VA %08X -> TD %08X header [%08X,%08X]" % (va,TD,u32(TD) or 0,u32(TD+4) or 0))
    cols=[]
    pat=struct.pack("<I",TD)
    j=data.find(pat)
    while j!=-1:
        cva=None
        for s in secs:
            if s["raw"]<=j<s["raw"]+s["rawsize"]:
                cva=s["va"]+(j-s["raw"]); break
        if cva is not None:
            cand=cva-0xC
            sig=u32(cand)
            if sig in (0,1): cols.append(cand)
        j=data.find(pat,j+1)
    print("COLs referencing TD: %s" % " ".join("%08X"%c for c in cols))
    for c in cols:
        # vtables with [-1]==c
        patc=struct.pack("<I",c)
        j=data.find(patc)
        vts=[]
        while j!=-1:
            vva=None
            for s in secs:
                if s["raw"]<=j<s["raw"]+s["rawsize"]:
                    vva=s["va"]+(j-s["raw"]); break
            if vva is not None: vts.append(vva+4)
            j=data.find(patc,j+1)
        print("  COL %08X -> vtables: %s" % (c," ".join("%08X"%v for v in vts)))
        for vt in vts:
            slots=[]
            for f in FNS:
                for k in range(0,0x1000,4):
                    if u32(vt+k)==f: slots.append("%08X:+0x%X"%(f,k))
            if slots: print("    vtable %08X contains write-point fns: %s"%(vt," ".join(slots)))
