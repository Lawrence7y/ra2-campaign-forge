#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
S12-Q2 core: load gamemd.exe, linear-disassemble .text with capstone skipdata=True,
cache instructions, provide query helpers.  Read-only on target binary.
"""
import os, sys, pickle, struct, json
import pefile
from capstone import *
from capstone.x86 import *

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "text_insns.pkl")

def load_text():
    pe = pefile.PE(EXE, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    for s in pe.sections:
        name = s.Name.rstrip(b"\x00").decode("latin-1")
        if name == ".text":
            va = base + s.VirtualAddress
            raw = s.get_data()
            return pe, base, va, raw, s
    raise RuntimeError("no .text")

def build_cache():
    pe, base, va, raw, sec = load_text()
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    md.skipdata = True
    out = []
    for ins in md.disasm(raw, va):
        out.append((ins.address, ins.size, ins.mnemonic, ins.op_str))
    with open(CACHE, "wb") as f:
        pickle.dump({"base":base,"text_va":va,"text_end":va+len(raw),"insns":out}, f)
    return out

def get_insns():
    if os.path.exists(CACHE):
        with open(CACHE,"rb") as f:
            return pickle.load(f)
    build_cache()
    with open(CACHE,"rb") as f:
        return pickle.load(f)

if __name__ == "__main__":
    d = get_insns()
    print("base=%08X text=[%08X,%08X) insns=%d" % (d["base"],d["text_va"],d["text_end"],len(d["insns"])))
