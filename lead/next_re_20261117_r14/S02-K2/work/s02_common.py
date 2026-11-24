# -*- coding: utf-8 -*-
"""S02-K2 shared helper: load PE, capstone disassembler, IAT map, atlas/S02 target sets."""
import csv, os
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = r"D:\Project\ra2-campaign-forge"
EXE  = os.path.join(ROOT, r"ra2youli\gamemd.exe")
COV  = os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATL  = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
CARD = os.path.join(ROOT, r"lead\next_re_20261117_r14\S02-K2")

pe_obj = pefile.PE(EXE, fast_load=False)
IMAGE_BASE = pe_obj.OPTIONAL_HEADER.ImageBase

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True

def rva2va(rva):
    return IMAGE_BASE + rva

def va2off(va):
    return pe_obj.get_offset_from_rva(va - IMAGE_BASE)

def read_bytes(va, n):
    off = va2off(va)
    return pe_obj.__data__[off:off+n]

def disasm(va, n=64):
    b = read_bytes(va, n)
    out = []
    for ins in md.disasm(b, va):
        out.append((ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
    return out

def build_iat_map():
    """map IAT VA -> (dll, funcname). Includes ordinal-based names."""
    iat = {}
    for entry in pe_obj.DIRECTORY_ENTRY_IMPORT:
        dll = entry.dll.decode("latin-1", "replace")
        for imp in entry.imports:
            if imp.address is None:
                continue
            va = imp.address
            name = imp.name.decode("latin-1", "replace") if imp.name else ("ord:%s" % imp.ordinal)
            iat[va] = (dll, name)
    return iat

def norm(e):
    e = str(e).strip().upper()
    if e.lower().startswith("0x"):
        e = e[2:]
    return e.zfill(8)

def load_targets():
    """return list of dict rows from TARGETS.tsv"""
    rows = []
    with open(os.path.join(CARD, "TARGETS.tsv"), encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            rows.append(r)
    return rows

if __name__ == "__main__":
    iat = build_iat_map()
    print("IMAGE_BASE=0x%X" % IMAGE_BASE)
    print("IAT entries:", len(iat))
    print("sample IAT (0x7E1000-0x7E1400):")
    for va in sorted(iat):
        if 0x7E1000 <= va <= 0x7E1400:
            print("  0x%08X %s!%s" % (va, iat[va][0], iat[va][1]))
    print()
    for a in [0x7C8E17, 0x7C8D20, 0x7C9430, 0x7CA090, 0x7C8B3D, 0x7C5F00, 0x7C8EF4]:
        print("=== 0x%08X ===" % a)
        for (ad, b, m, o) in disasm(a, 40):
            print("  0x%08X  %-20s %s %s" % (ad, b, m, o))
