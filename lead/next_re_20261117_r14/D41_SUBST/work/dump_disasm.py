# -*- coding: utf-8 -*-
"""Dump disassembly of selected candidates for ③b contract + byte-level channel-1 matching."""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from common import disasm_va, va2off, DATA, IB

WORK = os.path.dirname(__file__)
EVID = os.path.join(WORK, "..", "EVIDENCE")

targets = ["00407780","00407F40","00407FB0","007C9442",  # S02
           "00401F90","004025B0","004026A0","004026B0","004026F0","00405190","004052F0",
           "00405BE0","004060F0","00406130","00406170","004061D0","00406270","00406310",
           "00428B80","0065CA80"]  # S19

for e in targets:
    va = int(e, 16)
    # size from atlas
    sz = None
    for line in open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv", encoding="utf-8", errors="replace"):
        f = line.split("\t")
        if f and f[0].upper() == e:
            sz = int(f[1]); break
    if sz is None:
        sz = 0x200
    insns = disasm_va(va, min(sz, 0x800))
    path = os.path.join(EVID, "disasm_%s.txt" % e)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("; entry=%s size=%d\n" % (e, sz))
        for ins in insns:
            fh.write("%08X  %-20s  %s %s\n" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
    print("%s size=%d insns=%d -> %s" % (e, sz, len(insns), os.path.basename(path)))
print("done")
