#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Recon: sections, data directories, load config / SafeSEH / .pdata / TLS / CFG."""
import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
import pefile

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe = pefile.PE(EXE, fast_load=False)
IB = pe.OPTIONAL_HEADER.ImageBase
data = pe.__data__

print("=== HEADERS ===")
print("ImageBase %08X  SizeOfImage %08X  SectionAlign %08X FileAlign %08X" % (
    IB, pe.OPTIONAL_HEADER.SizeOfImage, pe.OPTIONAL_HEADER.SectionAlignment,
    pe.OPTIONAL_HEADER.FileAlignment))
print("SizeOfHeaders %08X  CheckSum %08X" % (
    pe.OPTIONAL_HEADER.SizeOfHeaders, pe.OPTIONAL_HEADER.CheckSum))
print("Subsystem", pe.OPTIONAL_HEADER.Subsystem, "DllCharacteristics %04X" % pe.OPTIONAL_HEADER.DllCharacteristics)

print("\n=== SECTIONS ===")
for s in pe.sections:
    nm = s.Name.decode(errors="replace").rstrip("\x00")
    va = IB + s.VirtualAddress
    print("%-8s va=%08X vsize=%08X raw=%08X rawsize=%08X chars=%08X" % (
        nm, va, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData, s.Characteristics))

print("\n=== DATA DIRECTORIES ===")
DIRS = ["EXPORT","IMPORT","RESOURCE","EXCEPTION","SECURITY","BASERELOC",
        "DEBUG","ARCHITECTURE","GLOBALPTR","TLS","LOAD_CONFIG","BOUND_IMPORT",
        "IAT","DELAY_IMPORT","COM_DESCRIPTOR","RESERVED"]
for i, d in enumerate(pe.OPTIONAL_HEADER.DATA_DIRECTORY):
    nm = DIRS[i] if i < len(DIRS) else "D%d" % i
    print("%-16s RVA=%08X Size=%08X  (VA=%08X)" % (nm, d.VirtualAddress, d.Size, IB+d.VirtualAddress))

def rva2va(rva): return IB + rva
def rva2off(rva): return pe.get_offset_from_rva(rva)

# LOAD CONFIG
lc_dir = pe.OPTIONAL_HEADER.DATA_DIRECTORY[10]
if lc_dir.VirtualAddress:
    print("\n=== LOAD CONFIG (RVA %08X size %d) ===" % (lc_dir.VirtualAddress, lc_dir.Size))
    off = rva2off(lc_dir.VirtualAddress)
    # try 32-bit and 64-bit layouts by size
    size = lc_dir.Size
    print("lc size", size, "off", hex(off))
    # IMAGE_LOAD_CONFIG_DIRECTORY32 size = 0x5C (92) for older; newer fields extend
    # Print first 0xC0 bytes as dwords with offsets
    for j in range(0, min(size, 0xC0), 4):
        v = struct.unpack_from("<I", data, off+j)[0]
        print("  +%03X: %08X" % (j, v))
