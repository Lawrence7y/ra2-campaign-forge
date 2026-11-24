#!/usr/bin/env python3
"""S03-C8 independent disassembly of the 5 remaining A rows, entry-relative offsets."""
import os, json
import common as C

# entry -> (lo,hi) extents from SURVEY_RING24 classification (self-CFG ext), verified below
ROWS = {
    "00473C00": (0x00473C00, 0x00473C50),
    "00473CE0": (0x00473CE0, 0x00473D03),
    "00473FC0": (0x00473FC0, 0x00473FD4),
    "0047AAB0": (0x0047AAB0, 0x0047AABD),
    "00631D30": (0x00631D30, 0x00631D3F),
}

base = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03_C8"
for e, (lo, hi) in ROWS.items():
    insns = C.md(lo, hi - lo)
    lines = ["# DISASM(entry=%s, range=[0x%X,0x%X), size=0x%X, n_insn=%d)  SHA=%s" %
             (e, lo, hi, hi - lo, len(insns), C.SHA[:8])]
    for i in insns:
        lines.append("+0x%03X 0x%08X: %-20s %s %s" %
                     (i.address - lo, i.address, i.bytes.hex(), i.mnemonic, i.op_str))
    txt = "\n".join(lines) + "\n"
    open(os.path.join(base, "EVIDENCE", "dis_%s.txt" % e), "w", encoding="utf-8").write(txt)
    print(txt)
