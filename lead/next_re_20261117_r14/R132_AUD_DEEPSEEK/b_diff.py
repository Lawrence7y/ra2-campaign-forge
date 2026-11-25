#!/usr/bin/env python3
"""R132 task B: byte-level diff of the two template instances."""
import json
import pefile

EXE = "/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe"
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
t = [s for s in pe.sections if s.Name.rstrip(b"\x00") == b".text"][0]
TEXT_VA, TEXT_RAW, TEXT_SZ = IB + t.VirtualAddress, t.PointerToRawData, t.Misc_VirtualSize
raw = open(EXE, "rb").read()
CODE = raw[TEXT_RAW:TEXT_RAW + TEXT_SZ]

A = 0x6BEDB0
B = 0x41C250
cfg = json.load(open("a_cfg.json"))
L = cfg["A"]["cfg_len"]
assert cfg["B"]["cfg_len"] == L, (cfg["A"]["cfg_len"], cfg["B"]["cfg_len"])
print("L =", L)


def body(va, n):
    o = va - TEXT_VA
    return CODE[o:o + n]


A136, B136 = body(A, L), body(B, L)
A106, B106 = body(A, 106), body(B, 106)


def diff(x, y, base):
    out = []
    for i in range(len(x)):
        if x[i] != y[i]:
            out.append({"off": i, "vaA": hex(A + i), "vaB": hex(B + i),
                        "A": f"{x[i]:02x}", "B": f"{y[i]:02x}"})
    return out


d136 = diff(A136, B136, A)
d106 = diff(A106, B106, A)

print("diff count L=%d: %d" % (L, len(d136)))
for d in d136:
    print("  off=%-4d vaA=%s vaB=%s A=%s B=%s" % (d["off"], d["vaA"], d["vaB"], d["A"], d["B"]))
print("diff count first 106: %d" % len(d106))
for d in d106:
    print("  off=%-4d vaA=%s vaB=%s A=%s B=%s" % (d["off"], d["vaA"], d["vaB"], d["A"], d["B"]))

print("A hex:", A136.hex(" "))
print("B hex:", B136.hex(" "))

json.dump({"L": L, "diff_L": d136, "diff_106": d106,
           "hexA": A136.hex(), "hexB": B136.hex()},
          open("b_diff.json", "w"), indent=1)
