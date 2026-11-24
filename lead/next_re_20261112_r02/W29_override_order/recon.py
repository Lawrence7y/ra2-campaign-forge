#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
W29 recon (exploratory). Pure static, read-only on gamemd.exe.
Emits VA / RVA / FOFF / raw bytes / capstone disassembly for the
key resource-lookup sites, plus string + xref inventory.
This is a scratch tool; the deliverable is override_order.py.
"""
import sys, os, struct, hashlib
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe"
IB  = 0x400000

pe = pefile.PE(EXE, fast_load=True)
data = open(EXE, "rb").read()
print("FILE:", EXE)
print("SIZE:", len(data), "MD5:", hashlib.md5(data).hexdigest(), "SHA256:", hashlib.sha256(data).hexdigest())
print("ImageBase: 0x%X  Machine: 0x%X  Characteristics: 0x%X" % (pe.OPTIONAL_HEADER.ImageBase, pe.FILE_HEADER.Machine, pe.FILE_HEADER.Characteristics))
print("DllCharacteristics: 0x%X  RELOCS_STRIPPED=%s" % (pe.OPTIONAL_HEADER.DllCharacteristics, bool(pe.FILE_HEADER.Characteristics & 0x1)))
print("Sections:")
secs = []
for s in pe.sections:
    name = s.Name.rstrip(b"\x00").decode("latin1")
    va = IB + s.VirtualAddress
    vsz = s.Misc_VirtualSize
    raw = s.PointerToRawData
    rsz = s.SizeOfRawData
    secs.append((name, s.VirtualAddress, vsz, raw, rsz))
    print("  %-8s RVA=0x%08X VA=0x%08X VSize=0x%08X FOFF=0x%08X RawSize=0x%08X" % (name, s.VirtualAddress, va, vsz, raw, rsz))

def off2va(off):
    for name, rva, vsz, raw, rsz in secs:
        if raw <= off < raw + rsz:
            return IB + rva + (off - raw)
    return None

def va2off(va):
    rva = va - IB
    for name, srva, vsz, raw, rsz in secs:
        if srva <= rva < srva + max(vsz, rsz):
            o = raw + (rva - srva)
            if o < raw + rsz:
                return o
    return None

# .text raw hash (per tools/verify_anchors.py convention)
for name, rva, vsz, raw, rsz in secs:
    if name == ".text":
        print(".text raw SHA256:", hashlib.sha256(data[raw:raw+rsz]).hexdigest())
        print(".text: FOFF == RVA (for .text)?", "yes" if raw == rva else "NO raw=0x%X rva=0x%X" % (raw, rva))

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False

def disasm(va, n=40, label=""):
    off = va2off(va)
    print("\n---- DISASM %s VA=0x%08X RVA=0x%08X FOFF=0x%08X (n=%d) ----" % (label, va, va-IB, off if off is not None else -1, n))
    if off is None:
        print("  !! unmapped"); return
    buf = data[off:off+n*8]
    cnt = 0
    for i in md.disasm(buf, va):
        rva = i.address - IB
        o = va2off(i.address)
        b = " ".join("%02X" % x for x in i.bytes)
        print("  VA=0x%08X RVA=0x%08X FOFF=0x%08X  %-22s  %-7s %s" % (i.address, rva, o if o is not None else -1, b, i.mnemonic, i.op_str))
        cnt += 1
        if cnt >= n: break

# ---- key strings inventory (ASCII + UTF-16LE) ----
KEYS = [
    b".mix", b"MIX", b".MIX", b"EXPANDMD", b"RA2MD.MIX", b"LANGMD.MIX", b"LANGUAGE.MIX",
    b".csf", b".CSF", b"CSF", b"ra2md.csf", b"RA2MD.CSF", b"ra2.csf", b"RA2.CSF", b"ra2md.str", b"RA2MD.STR",
    b"Unable to initialize", b"please reinstall", b"string file label", b"MISSING:", b"MISSING",
    b"BATTLEMD", b"BATTLEMD.INI", b"BATTLEMD*.INI", b"BATTLEMD98.INI", b"BATTLEMD98",
    b"CreateFileA", b"FindFirstFileA", b"FindNextFileA", b"FindClose", b"SetCurrentDirectoryA", b"GetModuleFileNameA",
    b"local mix database", b"MIXFILES", b"InstallPath", b"CDPath", b"[CD]", b"-CD",
    b"DESC:", b"Description", b"Battles",
]
print("\n==== STRING HITS (ASCII, all offsets; VA via section map) ====")
def find_all(hay, needle):
    out=[]; start=0
    while True:
        p = hay.find(needle, start)
        if p < 0: break
        out.append(p); start = p+1
    return out
strhits = {}
for k in KEYS:
    hits = find_all(data, k)
    strhits[k] = hits
    val = ", ".join("FOFF=0x%X/VA=0x%X" % (h, off2va(h) if off2va(h) is not None else -1) for h in hits[:12])
    if len(hits) > 12: val += " ... (+%d more)" % (len(hits)-12)
    print("  %-26r : %d hit(s)  %s" % (k, len(hits), val))

# case-insensitive .csf scan, and UTF-16LE check for a few keys
print("\n==== ENCODING CHECKS ====")
low = data.lower()
for k in [b".csf", b"ra2md.csf", b"ra2.csf", b".mix", b"battlemd"]:
    print("  ci %-16r : %d hit(s)" % (k, len(find_all(low, k))))
for k in [b".csf", b"ra2md.csf", b"ra2.csf", b".mix", b"battlemd", b"CSF"]:
    u = k.decode("latin1").encode("utf-16le")
    print("  utf16le %-16r : %d hit(s)" % (k, len(find_all(data, u))))

# ---- xref to a VA: find 4-byte LE occurrences + preceding opcode hints ----
def xrefs(va, label=""):
    pat = struct.pack("<I", va)
    hits = find_all(data, pat)
    print("\n---- XREF imm32 0x%08X (%s): %d raw occurrence(s) ----" % (va, label, len(hits)))
    for h in hits[:40]:
        o = h
        v = off2va(h)
        prev = data[h-1] if h >= 1 else None
        prev2 = data[h-2] if h >= 2 else None
        hint = ""
        if prev == 0x68: hint = "push imm32"
        elif prev is not None and 0xB8 <= prev <= 0xBF: hint = "mov r32,imm32"
        elif prev2 == 0xFF and prev == 0x15: hint = "call [imm32]"
        elif prev == 0xE8: hint = "(E8 preceded, data?)"
        sec = "?"
        for name, rva, vsz, raw, rsz in secs:
            if raw <= h < raw+rsz: sec = name
        print("   FOFF=0x%08X VA=0x%08X sec=%-7s prev=0x%02X 0x%02X  %s" % (h, v if v is not None else -1, sec, prev2 or 0, prev or 0, hint))
    if len(hits) > 40: print("   ... +%d more" % (len(hits)-40))

# xref the CSF-ish strings by their VA
for k in [b"ra2md.csf", b"RA2MD.CSF", b"ra2.csf", b"RA2.CSF", b"ra2md.str", b"RA2MD.STR", b"Unable to initialize", b"please reinstall"]:
    for h in strhits.get(k, [])[:3]:
        v = off2va(h)
        if v is not None:
            xrefs(v, "%r@0x%X" % (k, h))

# ---- E8 raw call-target scan over .text (sync-independent) ----
print("\n==== E8 CALL-TARGET RAW SCAN (.text only, sync-independent) ====")
trva, tvsz, traw, trsz = None, None, None, None
for name, rva, vsz, raw, rsz in secs:
    if name == ".text":
        trva, tvsz, traw, trsz = rva, vsz, raw, rsz
TARGETS = {0x5B4430:"MixFileClass::Find", 0x431F10:"disk-open helper", 0x65CBF0:"RawFileClass::Open",
           0x473D10:"CCFileClass::Get_File", 0x4739F0:"CCFileClass ctor", 0x473C50:"CCFileClass::Open",
           0x4741F0:"INIClass::Load", 0x46CE10:"Register_Battles", 0x52CB90:"LoadBattleMdIni",
           0x5B3C20:"MixFileClass ctor", 0x7346A0:"(str-table loader?)", 0x7B84F0:"?", 0x7C978A:"?"}
reach = {}
for off in range(traw, traw+trsz-5):
    if data[off] != 0xE8: continue
    rel = struct.unpack_from("<i", data, off+1)[0]
    callva = IB + trva + (off - traw)
    tgt = callva + 5 + rel
    if tgt in TARGETS:
        reach.setdefault(tgt, []).append(callva)
for tgt, name in sorted(TARGETS.items()):
    lst = reach.get(tgt, [])
    print("  target 0x%08X %-28s : %d E8 site(s): %s" % (tgt, name, len(lst), ", ".join("0x%X"%x for x in lst[:20])))

# ---- disasm key functions ----
for va, n, lab in [
    (0x473D10, 46, "CCFileClass::Get_File (Q1 core)"),
    (0x473C50, 40, "CCFileClass::Open"),
    (0x431F10, 16, "disk-open helper -> RawFileClass::Open"),
    (0x65CBF0, 60, "RawFileClass::Open -> CreateFileA"),
    (0x5B4430, 60, "MixFileClass::Find (FIFO)"),
    (0x5B44A1, 22, "MixFileClass::Find mid (head->next)"),
    (0x52CB90, 80, "LoadBattleMdIni (BATTLEMD*.INI)"),
    (0x52CCCD, 22, "BATTLEMD.INI fallback branch"),
    (0x46CE10, 20, "Register_Battles merge"),
    (0x6BD7E8, 20, "LANGMD.MIX ctor call site"),
    (0x6BD840, 26, "startup string-table gate"),
    (0x7346A0, 30, "possible CSF/str loader"),
]:
    disasm(va, n, lab)

print("\nDONE recon")
