#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, os, struct, json
import sys, os, struct, json
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\tools")
from re_gap_spysat_deep import read_bytes, read_u32, disasm_func, names, md, base, image
import capstone as _cs

print("=== JUMP TABLE 0x006CDE44 (SuperClass::Launch) ===")
jt_addr = 0x006CDE44
sw_names = [
    "Nuke", "IronCurtain", "LightningStorm", "ChronoSphere", 
    "ChronoWarp", "ParaDrop", "AmerParaDrop", "PsychicDominator", 
    "SpyPlane", "GeneticMutator", "ForceShield", "PsychicReveal"
]
for i in range(12):
    target = read_u32(jt_addr + i * 4)
    sw_n = sw_names[i] if i < len(sw_names) else "Unknown"
    print(f"  [{i:2d}] {sw_n:<18} -> 0x{target:08X} {names.get(target, '')}")

print("\n=== SuperClass::Launch 0x006CC390 (head & dispatch) ===")
disasm_func(0x006CC390, 60)

print("\n=== SuperClass::Launch Case 11 (PsychicReveal 0x006CD70C) ===")
disasm_func(0x006CD70C, 60)

print("\n=== MapClass::RevealArea2 0x005678E0 ===")
disasm_func(0x005678E0, 100)

print("\n=== 0x00567F70 (subroutine called by RevealArea2 or nearby) ===")
disasm_func(0x00567F70, 100)

print("\n=== 0x00567B2F (RevealArea2 loop body) ===")
disasm_func(0x00567B2F, 100)
