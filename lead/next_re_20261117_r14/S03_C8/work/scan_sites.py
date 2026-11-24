#!/usr/bin/env python3
"""Independent full-.text direct-call scan for the 5 rows.
④ per D-40: E8 at instruction boundary + site+5+rel32==entry + site outside function body + non-self."""
import os, json, struct
import common as C
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OPT_SKIPDATA

ROWS = {
    "00473C00": (0x00473C00, 0x00473C50),
    "00473CE0": (0x00473CE0, 0x00473D03),
    "00473FC0": (0x00473FC0, 0x00473FD4),
    "0047AAB0": (0x0047AAB0, 0x0047AABD),
    "00631D30": (0x00631D30, 0x00631D3F),
}
base = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03_C8"

# Full .text linear disassembly with skipdata, collect E8 at boundaries
cs = Cs(CS_ARCH_X86, CS_MODE_32)
cs.skipdata = True
tb = C.DATA[C.TEXT_RO:C.TEXT_RO+C.TEXT_RS]
n_insn = 0
sites = {e: [] for e in ROWS}
for i in cs.disasm(tb, C.TEXT_VA):
    n_insn += 1
    if i.mnemonic != 'call':
        continue
    b = i.bytes
    if len(b) != 5 or b[0] != 0xE8:
        continue
    rel = struct.unpack('<i', b[1:5])[0]
    tgt = (i.address + 5 + rel) & 0xFFFFFFFF
    for e, (lo, hi) in ROWS.items():
        if tgt == lo and not (lo <= i.address < hi):
            sites[e].append(i.address)

out = {'sha': C.SHA, 'n_insn_text': n_insn, 'text_vsize': C.TEXT_VS,
       'pct_text': None, 'sites': {}}
out['pct_text'] = round(n_insn/1392592*100, 2)
for e in ROWS:
    out['sites'][e] = sites[e]
    print(e, "sites=%d"%len(sites[e]), [hex(x) for x in sites[e][:40]])
print("total .text insn", n_insn, "(%.2f%% of 1,392,592)"%out['pct_text'])
json.dump(out, open(os.path.join(base,'EVIDENCE','direct_sites.json'),'w',encoding='utf-8'), indent=2)
print("wrote EVIDENCE/direct_sites.json")
