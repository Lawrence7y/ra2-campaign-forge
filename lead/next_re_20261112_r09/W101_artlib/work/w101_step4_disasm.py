# -*- coding: utf-8 -*-
"""W101 step4: capstone disassembly of art/rules INI load sites + MixFileClass (read-only)."""
import json, os, struct, sys

import capstone
import pefile

EXE  = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUTD = r"D:\Project\ra2-campaign-forge\lead\next_re_2026112_r09\W101_artlib\EVIDENCE".replace("2026112_", "20261112_")
OUTD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W101_artlib\EVIDENCE"

data = open(EXE, "rb").read()
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
secs = [(s.Name.rstrip(b"\x00").decode(), s.VirtualAddress + IB, s.Misc_VirtualSize,
         s.PointerToRawData, s.SizeOfRawData) for s in pe.sections]

def va2off(va):
    for name, vstart, vsz, raw, rsz in secs:
        if vstart <= va < vstart + max(vsz, rsz):
            o = raw + (va - vstart)
            if o < len(data): return o
    return None

strings = {}
for rec in json.load(open(os.path.join(OUTD, "step2_strings.json"), encoding="utf-8")):
    strings.setdefault(rec["va"], rec["s"])
short = {va: s for va, s in strings.items() if 2 <= len(s) <= 64}

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = False

IAT = {0x7E11BC: "KERNEL32!CreateFileA", 0x7E1208: "KERNEL32!FindFirstFileA",
       0x7E120C: "KERNEL32!FindNextFileA", 0x7E1300: "KERNEL32!FindClose",
       0x7E1460: "USER32!MessageBoxA", 0x7E1148: "KERNEL32!SetCurrentDirectoryA"}
KNOWN_CALLS = {0x4739F0: "CCFileClass::ctor(name)", 0x473C50: "CCFileClass::Open (disk->MIX)",
               0x473D10: "CCFileClass::Get_File", 0x4741F0: "INIClass::Load",
               0x473D2D: "(disk-first branch site)", 0x5B4430: "MixFileClass::Find",
               0x5B3C20: "MixFileClass::ctor", 0x7C8D20: "_stricmp", 0x7C8EF4: "sprintf",
               0x4068E0: "DebugPrint stub (ret)", 0x4A4AC0: "DebugPrint stub2 (ret)",
               0x473E24: "fail path", 0x65CBF0: "RawFileClass::Open",
               0x431F10: "disk-open helper", 0x46CE10: "Battle-table merge"}

PBUF = []
def P(*a):
    s = " ".join(str(x) for x in a); print(s); PBUF.append(s)

def disasm(start, end, title):
    P("")
    P("=" * 100)
    P(f"## {title}   0x{start:08X} - 0x{end:08X}")
    P("=" * 100)
    off = va2off(start)
    code = data[off: off + (end - start)]
    for ins in md.disasm(code, start):
        line = f"0x{ins.address:08X}  {ins.bytes.hex():<20s} {ins.mnemonic} {ins.op_str}"
        ann = []
        # push imm32 / mov imm32 annotation
        for tok in ins.op_str.replace(",", " ").split():
            if tok.startswith("0x"):
                try: v = int(tok, 16)
                except ValueError: continue
                if v in short: ann.append(f'"{short[v]}"')
                elif v in KNOWN_CALLS: ann.append(KNOWN_CALLS[v])
                elif v in IAT: ann.append(IAT[v])
        if ins.mnemonic in ("call", "jmp") and ins.op_str.startswith("0x"):
            t = int(ins.op_str, 16)
            if t in KNOWN_CALLS: ann.append("-> " + KNOWN_CALLS[t])
        if ins.mnemonic.startswith("j") and ins.op_str.startswith("0x"):
            ann.append("-> 0x" + ins.op_str[2:])
        P(line + ("   ; " + " ".join(ann) if ann else ""))

def xrefs_imm32(va, lo=0x401000, hi=0x896000):
    pat = struct.pack("<I", va)
    out = []
    s = 0
    while True:
        i = data.find(pat, s)
        if i < 0: break
        # map offset -> VA
        for name, vstart, vsz, raw, rsz in secs:
            if raw <= i < raw + rsz:
                out.append(vstart + (i - raw))
        s = i + 1
    return out

P("== extra xrefs (imm32 == VA) ==")
for label, va in [("AIMD.INI", 0x82621C), ("LANGRULE.INI", 0x826228),
                  ("Failed to initialize Rules!", 0x825D18), ("Init Rules", 0x825D38),
                  ("%sMD.INI", 0x8295E8), ("Failed to load ARTMD.INI!", 0x826238),
                  ("Failed to instantiate Rules!", 0x82613C), ("Reading ARTMD.INI?", 0x82624C)]:
    xs = xrefs_imm32(va)
    P(f"{label:32s} VA={va:08X} xrefs={[f'{x:08X}' for x in xs]}")

disasm(0x52CD70, 0x52D140, "INI block: RULEMD*.INI wildcard + RULESMD.INI x2 + AIMD/LANGRULE/ARTMD")
disasm(0x679E60, 0x679F90, "second ARTMD.INI site (Rules reload?)")
disasm(0x5B4430, 0x5B4560, "MixFileClass::Find (id lookup)")
disasm(0x5B3C20, 0x5B3E90, "MixFileClass::ctor (index read)")

open(os.path.join(OUTD, "step4_disasm.txt"), "w", encoding="utf-8").write("\n".join(PBUF) + "\n")
print("\nsaved ->", os.path.join(OUTD, "step4_disasm.txt"))
