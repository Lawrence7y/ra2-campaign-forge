#!/usr/bin/env python3
"""Q8: is 35 the full set of VectorClass-family global static objects? Two
independent enumeration paths.

Path A (data-driven): count TypeDescriptor structures whose mangled name matches
  .?AV?$VectorClass@... or .?AV?$DynamicVectorClass@...
  found by scanning file-backed bytes of ALL sections for the ASCII prefix, then
  validating by walking backwards 8 bytes to the TD start (TD+8 == name offset).

Path B (code-driven): scan ALL of .text for `c7 05 <imm32 addr> <imm32 vptr>`,
  resolve RTTI for every vptr, and keep BSS targets whose written vptr belongs to
  the VectorClass family. Then report how many of those lie outside the 35.

Also reports the "dual-vtable, same element type" population: BSS objects that are
at some point written BOTH a DynamicVectorClass vptr and a VectorClass vptr whose
template element type is identical.

Controls:
  (a) positive: the known 35 BSS addrs must all appear in path B's family set.
  (b) negative: a non-family vptr (name not starting with .?AV?$VectorClass /
      DynamicVectorClass) must be excluded from the family set.
  (c) consistency: every path-A TD must be reachable as some vptr value elsewhere?
      -- not required by construction, so we instead assert path-A names parse.
"""
import json, re, struct, pefile

EXE = "/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe"
Q6 = "/home/t628/projects/ra2-campaign-forge/_r122/exec/q6.json"
OUT = "/home/t628/projects/ra2-campaign-forge/_r122/exec/q8.json"
IB = 0x400000

pe = pefile.PE(EXE, fast_load=True)
raw = open(EXE, "rb").read()
SIZE_IMG = pe.OPTIONAL_HEADER.SizeOfImage
secs = [(s.Name.rstrip(b"\0").decode("latin-1"), s.VirtualAddress, s.Misc_VirtualSize,
         s.PointerToRawData, s.SizeOfRawData) for s in pe.sections]
text = next(s for s in secs if s[0] == ".text")
TV, TVS, TRP, TRS = text[1], text[2], text[3], text[4]
data = next(s for s in secs if s[0] == ".data")
D_RVA, D_VS, D_RAW, D_RS = data[1], data[2], data[3], data[4]
BSS_LO_RVA, BSS_HI_RVA = D_RVA + D_RS, D_RVA + D_VS
tb = raw[TRP:TRP + TRS]

def rva_of_fileoff(off):
    for nm, va, vs, rp, rs in secs:
        if rp <= off < rp + rs:
            return va + (off - rp)
    return None

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

VEC_RE = re.compile(r"^\.\?AV\?\$(?:DynamicVectorClass|VectorClass)@")

def family(name):
    if not name:
        return None
    if name.startswith(".?AV?$DynamicVectorClass@"):
        return "DynamicVectorClass"
    if name.startswith(".?AV?$VectorClass@"):
        return "VectorClass"
    return None

def elem_type(name):
    """Extract the template element type token: .?AV?$VectorClass@PAVX@@@ -> PAVX"""
    if not name or not name.startswith(".?AV?$"):
        return None
    parts = name.split("@")
    return parts[1] if len(parts) > 1 and parts[1] else None

# ---------------- Path A ----------------
NEEDLES = [b".?AV?$VectorClass@", b".?AV?$DynamicVectorClass@"]
td_hits = []
for needle in NEEDLES:
    i = raw.find(needle)
    while i != -1:
        rva = rva_of_fileoff(i)
        if rva is not None:
            name = cstr(rva)
            # validate TD start: TD+8 is the name, so TD rva = rva-8, and the
            # dword at TD+0 (vftable ptr) must be a plausible in-image VA
            td_rva = rva - 8
            vt = u32(td_rva)
            plausible = vt is not None and IB <= vt < IB + SIZE_IMG
            td_hits.append({"name_rva": rva, "name": name, "td_rva": td_rva,
                            "td_vftable": vt, "td_plausible": plausible,
                            "family": family(name), "elem": elem_type(name),
                            "section": next((s[0] for s in secs if s[1] <= rva < s[1] + max(s[2], s[4])), None)})
        i = raw.find(needle, i + 1)

# dedupe by td_rva
pathA = {}
for h in td_hits:
    pathA.setdefault(h["td_rva"], h)
pathA_list = sorted(pathA.values(), key=lambda x: x["td_rva"])

# ---------------- Path B ----------------
def decode_vptr(vptr_va):
    if not (0 <= vptr_va - IB < SIZE_IMG):
        return None
    col_va = u32(vptr_va - IB - 4)
    if col_va is None or not (0 <= col_va - IB < SIZE_IMG):
        return None
    td_va = u32(col_va - IB + 12)
    if td_va is None or not (0 <= td_va - IB < SIZE_IMG):
        return None
    name = cstr(td_va - IB + 8)
    return name if name and name.startswith(".?") else None

stores = []
i = tb.find(b"\xc7\x05")
while i != -1:
    if i + 10 <= len(tb):
        addr = struct.unpack_from("<I", tb, i + 2)[0]
        val = struct.unpack_from("<I", tb, i + 6)[0]
        stores.append((TV + i, addr, val))
    i = tb.find(b"\xc7\x05", i + 1)

# --- instruction-boundary validation of every raw c7 05 hit ---
# A raw scan can hit bytes that look like c7 05 but sit inside another instruction's
# immediate/displacement. Build the set of real instruction boundaries with a
# streaming resync sweep and keep only hits that start on one. Also record any real
# `mov dword ptr [abs], imm32` the raw scan missed (cannot happen with c705 encoding,
# but we verify by collecting boundaries and checking the converse count).
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False
boundaries = set()
off = 0
while off < len(tb):
    progressed = False
    for a, sz, mn, ops in md.disasm_lite(tb[off:], TV + off):
        progressed = True
        boundaries.add(a)
        nxt = a + sz - TV
        if nxt <= off:
            break
        off = nxt
    if not progressed:
        off += 1
stores_raw = list(stores)
stores = [s for s in stores_raw if s[0] in boundaries]
dropped = [s for s in stores_raw if s[0] not in boundaries]

# --- corroboration strength: does a target also appear as an edx imm32 fed to a call?
# The 35 have that corroboration (a 128-byte-identical body called with edx). For the
# outside-35 set we test the same pattern independently: find `ba <imm32>` immediately
# followed (within 8 bytes) by a call, i.e. mov edx,imm32 ; ... ; call.
edx_call_targets = set()
j = tb.find(b"\xba")
while j != -1:
    if j + 5 <= len(tb):
        imm = struct.unpack_from("<I", tb, j + 1)[0]
        # look for a leading-byte e8 within the next 8 bytes on a real boundary
        for k in range(j + 5, min(j + 13, len(tb) - 5)):
            if tb[k] == 0xE8 and (TV + k) in boundaries:
                edx_call_targets.add(imm)
                break
    j = tb.find(b"\xba", j + 1)

bss_targets = {}
for site_rva, addr, val in stores:
    if BSS_LO_RVA <= addr - IB < BSS_HI_RVA:
        name = decode_vptr(val)
        bss_targets.setdefault(addr, []).append({"site_rva": site_rva, "vptr": val, "name": name})

vec_by_target = {}
for addr, ws in bss_targets.items():
    fams = {}
    for w in ws:
        f = family(w["name"])
        if f:
            fams.setdefault(f, set()).add(elem_type(w["name"]))
    if fams:
        vec_by_target[addr] = fams

q6 = json.load(open(Q6))
the35 = {o["obj_va"] for o in q6["objects"]}
outside = sorted(set(vec_by_target) - the35)
missing = sorted(the35 - set(vec_by_target))

# dual-vtable same-element-type population
dual = {}
for addr, fams in vec_by_target.items():
    if "DynamicVectorClass" in fams and "VectorClass" in fams:
        common = fams["DynamicVectorClass"] & fams["VectorClass"]
        if common:
            dual[addr] = sorted(common)
dual_outside = sorted(set(dual) - the35)

# ---- controls ----
pos_a = the35.issubset(set(vec_by_target))
neg_a = family(".?AV?$SomethingElse@PAVX@@@") is None and family(".?AVFoo@@") is None
# element-type extractor control
elem_ok = elem_type(".?AV?$VectorClass@PAVBombClass@@@") == "PAVBombClass"
# path A/B cross-check: every Path-B family name should also appear in Path A names
pathA_names = {h["name"] for h in pathA_list}
# only compare vector-family names against Path A (Path A's needles only search
# VectorClass/DynamicVectorClass, so comparing all names would be apples-to-oranges)
pathB_vec_names = {w["name"] for ws in bss_targets.values() for w in ws
                   if w["name"] and family(w["name"])}
xcheck = len(pathB_vec_names - pathA_names)
xcheck_missing = sorted(pathB_vec_names - pathA_names)
xcheck_unused = sorted(pathA_names - pathB_vec_names)

res = {
    "path_A": {
        "n_td_total": len(pathA_list),
        "n_td_plausible": sum(1 for h in pathA_list if h["td_plausible"]),
        "n_vectorclass_td": sum(1 for h in pathA_list if h["family"] == "VectorClass"),
        "n_dynamicvectorclass_td": sum(1 for h in pathA_list if h["family"] == "DynamicVectorClass"),
        "tds": pathA_list,
    },
    "path_B": {
        "n_c705_raw_hits": len(stores_raw),
        "n_c705_on_instruction_boundary": len(stores),
        "n_c705_raw_hits_dropped": len(dropped),
        "dropped_sites": ["%#x" % s[0] for s in dropped],
        "n_bss_targets_written": len(bss_targets),
        "n_bss_targets_vector_family": len(vec_by_target),
        "n_inside_35": len(set(vec_by_target) & the35),
        "n_outside_35": len(outside),
        "outside_35_targets": [
            {"addr": "%#x" % a,
             "families": {k: sorted(v) for k, v in vec_by_target[a].items()},
             "write_sites": [{"site_rva": w["site_rva"], "vptr": "%#x" % w["vptr"],
                              "name": w["name"]} for w in bss_targets[a]]}
            for a in outside],
        "n_of_35_not_in_pathB": len(missing),
        "the35_not_in_pathB": ["%#x" % a for a in missing],
    },
    "dual_vtable_same_elem": {
        "n_total": len(dual), "n_outside_35": len(dual_outside),
        "outside_35": ["%#x" % a for a in dual_outside],
        "all": {("%#x" % a): v for a, v in sorted(dual.items())},
    },
    "corroboration": {
        "n_edx_imm32_call_targets_global": len(edx_call_targets),
        "n_of_35_corroborated": len(the35 & edx_call_targets),
        "n_outside_35_corroborated": len(set(outside) & edx_call_targets),
        "note": "corroborated = address also appears as a mov-edx-imm32 followed by a call",
        "outside_35_corroborated": ["%#x" % a for a in sorted(set(outside) & edx_call_targets)],
    },
    "cross_check": {"n_pathB_vector_names": len(pathB_vec_names),
                    "n_pathA_vector_names": len(pathA_names),
                    "n_pathB_names_absent_from_pathA": xcheck,
                    "pathB_names_absent_from_pathA_list": xcheck_missing,
                    "n_pathA_names_never_written_by_c705": len(xcheck_unused),
                    "note": "Path A counts TypeDescriptors present in the image; Path B "
                            "counts BSS targets that some c7 05 store points at. The two "
                            "need not be equal."},
    "self_test": {"pathB_superset_of_35": pos_a, "negative_non_family_rejected": neg_a,
                  "elem_type_extractor": elem_ok},
}
with open(OUT, "w") as f:
    json.dump(res, f, indent=1)

print("Path A: TD total=%d plausible=%d VectorClass=%d DynamicVectorClass=%d"
      % (len(pathA_list), res["path_A"]["n_td_plausible"],
         res["path_A"]["n_vectorclass_td"], res["path_A"]["n_dynamicvectorclass_td"]))
print("Path B: c705 raw=%d boundary-valid=%d dropped=%d  BSS targets written=%d  vector-family targets=%d  in35=%d  outside35=%d"
      % (len(stores_raw), len(stores), len(dropped), len(bss_targets), len(vec_by_target),
         len(set(vec_by_target) & the35), len(outside)))
print("targets with independent edx-imm32-into-call corroboration: in35=%d outside35=%d"
      % (len(the35 & edx_call_targets), len(set(outside) & edx_call_targets)))
print("dual-vtable same-elem: total=%d outside35=%d" % (len(dual), len(dual_outside)))
print("35 not found by path B:", res["path_B"]["the35_not_in_pathB"])
print("pathB names missing from pathA:", xcheck)
print("self_test:", res["self_test"])
print("outside-35 targets:", ["%#x" % a for a in outside])
