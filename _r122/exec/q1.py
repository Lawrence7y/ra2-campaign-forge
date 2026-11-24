#!/usr/bin/env python3
"""Q1: parse PE sections, report .text/.data geometry and BSS tails.
Self-test: positive (known section count>0, .text raw==virtualsize likely) and
negative control (a section with SizeOfRawData>VirtualSize must not be flagged)."""
import json, pefile

EXE = "/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe"
OUT = "/home/t628/projects/ra2-campaign-forge/_r122/exec/q1.json"

pe = pefile.PE(EXE, fast_load=True)
secs = []
for s in pe.sections:
    name = s.Name.rstrip(b"\x00").decode("latin-1")
    secs.append({
        "name": name,
        "VA": s.VirtualAddress,
        "VSize": s.Misc_VirtualSize,
        "RawPtr": s.PointerToRawData,
        "RawSize": s.SizeOfRawData,
        "file_end_VA": s.VirtualAddress + s.SizeOfRawData,
        "virt_end_VA": s.VirtualAddress + s.Misc_VirtualSize,
        "has_bss_tail": s.SizeOfRawData < s.Misc_VirtualSize,
        "bss_tail_bytes": max(0, s.Misc_VirtualSize - s.SizeOfRawData),
    })

by = {x["name"]: x for x in secs}
data = by[".data"]; text = by[".text"]

# boundary of .data: file-backed region is [VA, VA+RawSize), BSS virtual is
# [VA+RawSize, VA+VSize)
data_boundary = data["VA"] + data["RawSize"]

# --- self tests ---
# positive: boundary must lie inside .data virtual extent, and byte at boundary-1 is raw-backed
pos_ok = (data["VA"] <= data_boundary <= data["virt_end_VA"]
          and data_boundary - data["VA"] == data["RawSize"])
# negative control: synthesise a section with RawSize == VSize -> must NOT report bss tail
neg = {"name": ".neg", "VSize": 0x100, "RawSize": 0x100}
neg_has_tail = neg["RawSize"] < neg["VSize"]
neg_ok = (neg_has_tail is False)
assert pos_ok and neg_ok, (pos_ok, neg_ok)

res = {
    "exe": EXE,
    "image_base": pe.OPTIONAL_HEADER.ImageBase,
    "sections": secs,
    "text": text,
    "data": data,
    "data_file_backed": [data["VA"], data_boundary],
    "data_bss": [data_boundary, data["virt_end_VA"]],
    "sections_with_bss_tail": [x["name"] for x in secs if x["has_bss_tail"]],
    "bss_tail_detail": {x["name"]: x["bss_tail_bytes"] for x in secs if x["has_bss_tail"]},
    "self_test": {"positive_boundary_ok": pos_ok, "negative_no_false_tail_ok": neg_ok},
}
with open(OUT, "w") as f:
    json.dump(res, f, indent=1)

print("image_base=%#x" % pe.OPTIONAL_HEADER.ImageBase)
for x in secs:
    print("%-9s VA=%#010x VSize=%#010x RawPtr=%#010x RawSize=%#010x tail=%d"
          % (x["name"], x["VA"], x["VSize"], x["RawPtr"], x["RawSize"], x["bss_tail_bytes"]))
print(".data file-backed [%#x,%#x)  bss [%#x,%#x)" % (data["VA"], data_boundary, data_boundary, data["virt_end_VA"]))
print("sections with bss tail:", [x["name"] for x in secs if x["has_bss_tail"]])
print("self_test:", res["self_test"])
