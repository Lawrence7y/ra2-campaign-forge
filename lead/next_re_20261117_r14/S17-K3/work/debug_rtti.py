#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug RTTI structure at known addresses."""
import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-F1\work")
import pe_util as P

def dump(va, n=64):
    b = P.read(va, n)
    if b is None:
        print(f"--- {va:08X} : NO MAPPING ---"); return
    print(f"--- {va:08X} ---")
    for i in range(0, n, 16):
        chunk = b[i:i+16]
        hexs = ' '.join(f'{x:02X}' for x in chunk)
        print(f"{va+i:08X}: {hexs}")

dump(0x7E3A20, 48)
col = P.u32(0x7E3A28)
print(f"pCOL@7E3A28 = {col:08X}" if col else "pCOL None")
if col:
    dump(col, 32)
    td = P.u32(col+0xC)
    print(f"TD@COL+0xC = {td:08X}" if td else "TD None")
    if td:
        dump(td, 32)
        nm = P.read(td+8, 40)
        print(f"name bytes @TD+8: {nm}")

print("=== sections ===")
for s in P.sections():
    print(f"{s[0]:10s} va={s[1]:08X} vsize={s[2]:08X} praw={s[3]:08X} rawsize={s[4]:08X} ch={s[5]:08X}")
