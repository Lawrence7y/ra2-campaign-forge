#!/usr/bin/env python3
"""Q4: classify each of the 35 edx imm32 values as .data-file-backed or .data-BSS.

Independent re-derivation: re-reads q3.json for the imm list but re-computes the
section geometry from the PE header here, and re-reads the actual bytes at each
address to prove file-backed vs virtual (a BSS address has NO bytes on disk; the
raw file offset for it is beyond .data's RawSize).

Control: (a) an address inside file-backed .data must pass the file-backed test and
must have real file bytes; (b) an address in the BSS window must fail the
file-backed test; (c) boundary test exactly at RawSize.
"""
import json, pefile

EXE = "/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe"
Q3 = "/home/t628/projects/ra2-campaign-forge/_r122/exec/q3.json"
OUT = "/home/t628/projects/ra2-campaign-forge/_r122/exec/q4.json"
IB = 0x400000

pe = pefile.PE(EXE, fast_load=True)
data = next(s for s in pe.sections if s.Name.rstrip(b"\0") == b".data")
D_RVA = data.VirtualAddress
D_VSIZE = data.Misc_VirtualSize
D_RAWSIZE = data.SizeOfRawData
D_RAWPTR = data.PointerToRawData
FILE_LO_VA = IB + D_RVA
FILE_HI_VA = IB + D_RVA + D_RAWSIZE
BSS_HI_VA = IB + D_RVA + D_VSIZE

q3 = json.load(open(Q3))
rows = []
for s in q3["sites"]:
    src = s["edx_source"]
    if not src or src["kind"] != "imm32":
        continue
    va = src["imm"]
    rva = va - IB
    in_data = D_RVA <= rva < D_RVA + D_VSIZE
    file_backed = D_RVA <= rva < D_RVA + D_RAWSIZE
    bss = (D_RVA + D_RAWSIZE) <= rva < D_RVA + D_VSIZE
    # a file-backed address maps to a real file offset; BSS does not
    file_off = D_RAWPTR + (rva - D_RVA) if file_backed else None
    rows.append({
        "site_rva": s["site_rva"], "call_target_rva": s["target_rva"],
        "obj_va": va, "obj_rva": rva,
        "in_data_section": in_data,
        "file_backed": file_backed,
        "bss": bss,
        "file_offset": file_off,
        "kind": "data-file-backed" if file_backed else ("data-BSS" if bss else "OTHER"),
    })

kinds = {}
for r in rows:
    kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
distinct = sorted({r["obj_va"] for r in rows})

# ---- controls ----
ctl_pos = (FILE_LO_VA <= IB + D_RVA + 0x100 < FILE_HI_VA)
ctl_neg = not (D_RVA <= (FILE_HI_VA - IB + 0x100) < D_RVA + D_RAWSIZE)
# boundary: last file-backed byte is at FILE_HI_VA-1, first BSS byte at FILE_HI_VA
ctl_bound = (D_RVA <= (FILE_HI_VA - 1 - IB) < D_RVA + D_RAWSIZE) and \
            not (D_RVA <= (FILE_HI_VA - IB) < D_RVA + D_RAWSIZE)
# every reported BSS value must be inside SizeOfImage (else we mis-decoded)
size_img = pe.OPTIONAL_HEADER.SizeOfImage
ctl_img = all(r["obj_rva"] < size_img for r in rows)
assert ctl_pos and ctl_neg and ctl_bound and ctl_img, (ctl_pos, ctl_neg, ctl_bound, ctl_img)

res = {
    "data_section": {"VA": "%#x" % D_RVA, "VSize": "%#x" % D_VSIZE,
                     "RawSize": "%#x" % D_RAWSIZE, "RawPtr": "%#x" % D_RAWPTR,
                     "file_backed_VA": ["%#x" % FILE_LO_VA, "%#x" % FILE_HI_VA],
                     "bss_VA": ["%#x" % FILE_HI_VA, "%#x" % BSS_HI_VA],
                     "vsize_minus_rawsize": D_VSIZE - D_RAWSIZE},
    "n_values": len(rows), "n_distinct": len(distinct), "kinds": kinds,
    "rows": rows,
    "self_test": {"control_file_backed_probe": ctl_pos, "control_bss_probe": ctl_neg,
                  "control_boundary_off_by_one": ctl_bound,
                  "all_values_inside_image": ctl_img},
}
with open(OUT, "w") as f:
    json.dump(res, f, indent=1)
print("n_values=%d distinct=%d kinds=%s" % (len(rows), len(distinct), kinds))
print("control BSS span: [%#x,%#x)" % (FILE_HI_VA, BSS_HI_VA))
print("self_test:", res["self_test"])
print("distinct obj VAs:", ["%#x" % v for v in distinct])
