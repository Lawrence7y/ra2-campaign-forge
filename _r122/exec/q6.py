#!/usr/bin/env python3
"""Q6: decode MSVC x86 RTTI for each c7 05 store value (the vptr).

Layout used (x86, 32-bit, MSVC):
  vptr            -> vtable (array of fn ptrs; slot [-1] is COL pointer)
  vtable - 4      -> CompleteObjectLocator*  (COL)
  COL + 0  = signature (must be 0 or 1)
  COL + 12 = TypeDescriptor*  (pTypeDescriptor)
  TD  + 0  = vftable ptr, +4 = spare, +8 = mangled name (char[])
Name is read as a NUL-terminated C string.

All addresses in the file are RVAs in section headers; vtable/COL/TD pointers
stored in the image are ABSOLUTE VAs. We normalise with rva = va - IB.

Positive/negative controls are built from the real data (see self_test).
"""
import json, struct, pefile

EXE = "/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe"
Q5 = "/home/t628/projects/ra2-campaign-forge/_r122/exec/q5.json"
OUT = "/home/t628/projects/ra2-campaign-forge/_r122/exec/q6.json"
IB = 0x400000

pe = pefile.PE(EXE, fast_load=True)
raw = open(EXE, "rb").read()

secs = []
for s in pe.sections:
    secs.append((s.Name.rstrip(b"\0").decode("latin-1"), s.VirtualAddress,
                 s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData))
SIZE_IMG = pe.OPTIONAL_HEADER.SizeOfImage

def sec_of(rva):
    for nm, va, vs, rp, rs in secs:
        if va <= rva < va + max(vs, rs):
            return nm
    return None

def read(rva, n):
    """Read n bytes at RVA; returns None if not file-backed (BSS) or OOB."""
    for nm, va, vs, rp, rs in secs:
        if va <= rva < va + rs:
            off = rp + (rva - va)
            if off + n <= len(raw):
                return raw[off:off + n]
            return None
        if va + rs <= rva < va + vs:
            return None          # inside BSS tail: no file bytes
    return None

def u32(rva):
    b = read(rva, 4)
    return None if b is None else struct.unpack("<I", b)[0]

def cstr(rva, maxlen=512):
    out = bytearray()
    for i in range(maxlen):
        b = read(rva + i, 1)
        if b is None:
            return None
        if b == b"\x00":
            return out.decode("latin-1") if out else None
        out += b
    return None

def valid_name(s):
    """A real MSVC mangled RTTI name starts with '.?A' (class) etc."""
    return bool(s) and s.startswith(".?") and len(s) > 4

def decode_rtti(vptr_va, vtable_delta=0):
    """vtable_delta shifts the assumed vtable start (used by the negative controls)."""
    vt_rva = vptr_va - IB + vtable_delta
    col_va = u32(vt_rva - 4)
    if col_va is None:
        return {"ok": False, "why": "vtable-4 unreadable"}
    col_rva = col_va - IB
    if not (0 <= col_rva < SIZE_IMG):
        return {"ok": False, "why": "COL out of image", "col_va": col_va}
    sig = u32(col_rva)
    td_va = u32(col_rva + 12)
    if td_va is None:
        return {"ok": False, "why": "COL+12 unreadable", "col_va": col_va}
    td_rva = td_va - IB
    if not (0 <= td_rva < SIZE_IMG):
        return {"ok": False, "why": "TD out of image", "td_va": td_va}
    name = cstr(td_rva + 8)
    return {"ok": bool(valid_name(name)), "col_va": col_va, "col_rva": col_rva,
            "signature": sig, "td_va": td_va, "td_rva": td_rva, "name": name,
            "why": None if valid_name(name) else "name not a mangled RTTI name"}

q5 = json.load(open(Q5))
objs = {}
for site in q5["sites"]:
    objs.setdefault(site["target_va"], []).append(site)

rows = []
for addr, sites in sorted(objs.items()):
    groups = {}
    for s in sites:
        groups.setdefault(s["value_va"], []).append(s["site_rva"])
    entries = []
    for vptr, srs in sorted(groups.items()):
        d = decode_rtti(vptr)
        entries.append({"vptr_va": vptr, "vptr_rva": vptr - IB,
                        "vptr_section": sec_of(vptr - IB),
                        "write_sites": sorted(srs), "rtti": d})
    rows.append({"obj_va": addr, "obj_rva": addr - IB,
                 "obj_section": sec_of(addr - IB),
                 "n_distinct_vptrs": len(groups), "vptrs": entries})

# ---- controls on a real object ----
ctl = {}
if rows:
    r0 = rows[0]
    v0 = r0["vptrs"][0]["vptr_va"]
    v1 = r0["vptrs"][1]["vptr_va"] if len(r0["vptrs"]) > 1 else None
    # (a) object addr +1 used as if it were a vptr source: read "vtable" from obj+1
    #     that is not a vtable -> must fail
    da = decode_rtti(r0["obj_va"] + 1)
    ctl["a_obj_addr_plus1_as_vptr"] = {"ok": da["ok"], "why": da.get("why")}
    # (b) real vptr + 4 as vtable start (slot shifted) -> must fail
    db = decode_rtti(v0, vtable_delta=4)
    ctl["b_vptr_plus4_as_vtable"] = {"ok": db["ok"], "why": db.get("why")}
    # (c) real vptr must decode, and the other vptr must give a different name
    dc = decode_rtti(v0)
    dd = decode_rtti(v1) if v1 else None
    ctl["c_real_vptr"] = {"ok": dc["ok"], "name": dc.get("name")}
    ctl["c_other_vptr_differs"] = (dd["name"] != dc.get("name")) if dd else None
ctl_ok = (ctl["a_obj_addr_plus1_as_vptr"]["ok"] is False
          and ctl["b_vptr_plus4_as_vtable"]["ok"] is False
          and ctl["c_real_vptr"]["ok"] is True
          and ctl.get("c_other_vptr_differs") in (True, None))

res = {"n_objects": len(rows), "objects": rows, "controls": ctl,
       "self_test": {"negative_obj_addr_plus1_fails": ctl["a_obj_addr_plus1_as_vptr"]["ok"] is False,
                     "negative_vptr_plus4_fails": ctl["b_vptr_plus4_as_vtable"]["ok"] is False,
                     "positive_real_vptr_decodes": ctl["c_real_vptr"]["ok"] is True,
                     "control_two_vptrs_differ": ctl.get("c_other_vptr_differs")}}
with open(OUT, "w") as f:
    json.dump(res, f, indent=1)

print("objects=%d" % len(rows))
for r in rows:
    print("%#x (n_vptr=%d)" % (r["obj_va"], r["n_distinct_vptrs"]))
    for e in r["vptrs"]:
        print("   vptr %#x %-6s -> %s" % (e["vptr_va"], e["vptr_section"],
                                          e["rtti"].get("name") or ("FAIL:" + str(e["rtti"].get("why")))))
print("controls:", json.dumps(ctl, indent=1))
print("self_test:", res["self_test"])
print("assert ok:", ctl_ok)
