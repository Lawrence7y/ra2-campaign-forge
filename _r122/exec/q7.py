#!/usr/bin/env python3
"""Q7: three control families, each run over ALL 35 objects (not just one), with
expected vs measured for every case.

(a) take a BSS object address +1 as the object start, read the dword there as a vptr,
    and try to resolve RTTI -> must NOT yield a valid mangled class name.
(b) take a real vptr +4 as the vtable start -> must NOT yield a valid class name.
(c) the real vptr must resolve, and swapping it for the object's OTHER vptr must
    yield a DIFFERENT class name.

The RTTI reader is imported from q6 logic (re-implemented here so this script is
self-contained and independently runnable).
"""
import json, struct, pefile

EXE = "/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe"
Q6 = "/home/t628/projects/ra2-campaign-forge/_r122/exec/q6.json"
OUT = "/home/t628/projects/ra2-campaign-forge/_r122/exec/q7.json"
IB = 0x400000

pe = pefile.PE(EXE, fast_load=True)
raw = open(EXE, "rb").read()
SIZE_IMG = pe.OPTIONAL_HEADER.SizeOfImage
secs = [(s.Name.rstrip(b"\0").decode("latin-1"), s.VirtualAddress, s.Misc_VirtualSize,
         s.PointerToRawData, s.SizeOfRawData) for s in pe.sections]

def read(rva, n):
    for nm, va, vs, rp, rs in secs:
        if va <= rva < va + rs:
            off = rp + (rva - va)
            return raw[off:off + n] if off + n <= len(raw) else None
        if va + rs <= rva < va + vs:
            return None
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
    return bool(s) and s.startswith(".?") and len(s) > 4

def decode_vptr(vptr_va):
    """Resolve RTTI given an assumed vptr (absolute VA)."""
    if not (0 <= vptr_va - IB < SIZE_IMG):
        return {"ok": False, "why": "vptr outside image"}
    col_va = u32(vptr_va - IB - 4)
    if col_va is None:
        return {"ok": False, "why": "vtable-4 unreadable"}
    if not (0 <= col_va - IB < SIZE_IMG):
        return {"ok": False, "why": "COL out of image"}
    td_va = u32(col_va - IB + 12)
    if td_va is None or not (0 <= td_va - IB < SIZE_IMG):
        return {"ok": False, "why": "TD out of image/unreadable"}
    name = cstr(td_va - IB + 8)
    return {"ok": valid_name(name), "name": name,
            "why": None if valid_name(name) else "name not mangled RTTI"}

q6 = json.load(open(Q6))
objs = q6["objects"]

A, B, C = [], [], []
for o in objs:
    obj_va = o["obj_va"]
    vptrs = [e["vptr_va"] for e in o["vptrs"]]
    names = [e["rtti"].get("name") for e in o["vptrs"]]

    # (a) object start +1 -> read dword there, treat as vptr
    fake_vptr = u32(obj_va - IB + 1)
    ra = decode_vptr(fake_vptr) if fake_vptr is not None else {"ok": False, "why": "unreadable"}
    A.append({"obj_va": obj_va, "read_at": "%#x" % (obj_va + 1),
              "fake_vptr": None if fake_vptr is None else "%#x" % fake_vptr,
              "expected": "invalid", "measured_ok": ra["ok"],
              "measured_why": ra.get("why"), "measured_name": ra.get("name")})

    # (b) real vptr +4 as vtable start == read COL from vptr (slot 0 treated as COL)
    rb = decode_vptr(vptrs[0] + 4)
    B.append({"obj_va": obj_va, "real_vptr": "%#x" % vptrs[0],
              "assumed_vtable_start": "%#x" % (vptrs[0] + 4),
              "expected": "invalid", "measured_ok": rb["ok"],
              "measured_why": rb.get("why"), "measured_name": rb.get("name")})

    # (c) both real vptrs must decode and differ
    r0 = decode_vptr(vptrs[0])
    r1 = decode_vptr(vptrs[1]) if len(vptrs) > 1 else {"ok": False, "why": "no 2nd vptr"}
    C.append({"obj_va": obj_va, "vptr0": "%#x" % vptrs[0], "vptr1": "%#x" % vptrs[1],
              "name0": r0.get("name"), "name1": r1.get("name"),
              "expected": "both valid and different",
              "both_valid": r0["ok"] and r1["ok"],
              "different": (r0.get("name") != r1.get("name"))})

nA = sum(1 for x in A if x["measured_ok"] is False)
nB = sum(1 for x in B if x["measured_ok"] is False)
nC = sum(1 for x in C if x["both_valid"] and x["different"])

# ---- extra hard control: 1-byte-shift sweep over ALL offsets 1..7 of one object ----
ref = objs[0]
shift_probe = []
for d in range(-8, 9):
    if d == 0:
        continue
    r = decode_vptr(ref["vptrs"][0]["vptr_va"] + d)
    shift_probe.append({"delta": d, "ok": r["ok"], "name": r.get("name"), "why": r.get("why")})
n_shift_false_pos = sum(1 for x in shift_probe if x["ok"])
# ---- sanity: 0 delta must succeed (else the whole method is broken) ----
r0 = decode_vptr(ref["vptrs"][0]["vptr_va"])

res = {
    "n_objects": len(objs),
    "a_object_plus1": {"n_total": len(A), "n_correctly_invalid": nA, "cases": A},
    "b_vptr_plus4": {"n_total": len(B), "n_correctly_invalid": nB, "cases": B},
    "c_swap_vptr": {"n_total": len(C), "n_both_valid_and_different": nC, "cases": C},
    "shift_probe_on_one_object": {"cases": shift_probe,
                                  "n_false_positives_among_16_shifts": n_shift_false_pos},
    "self_test": {
        "a_all_35_invalid": nA == 35,
        "b_all_35_invalid": nB == 35,
        "c_all_35_valid_and_different": nC == 35,
        "delta0_positive_control": r0["ok"] is True,
        "shift_probe_no_false_positive": n_shift_false_pos == 0,
    },
}
with open(OUT, "w") as f:
    json.dump(res, f, indent=1)

print("(a) obj+1 as object start: %d/%d correctly invalid" % (nA, len(A)))
print("(b) real vptr+4 as vtable : %d/%d correctly invalid" % (nB, len(B)))
print("(c) swap vptr, both valid+different: %d/%d" % (nC, len(C)))
print("shift probe false positives:", n_shift_false_pos, "/16")
print("self_test:", res["self_test"])
bad = [x for x in A + B if x["measured_ok"]]
if bad:
    print("UNEXPECTED VALID:", json.dumps(bad, indent=1)[:2000])
