# -*- coding: utf-8 -*-
"""W101 step5: hash function + Open + callers (read-only)."""
import json, os, struct, sys
import capstone, pefile

EXE  = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
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
KNOWN_CALLS = {0x4739F0: "CCFileClass::ctor(name)", 0x473C50: "CCFileClass::Open",
               0x4741F0: "INIClass::Load", 0x5B4430: "MixFileClass::Find",
               0x5B3C20: "MixFileClass::ctor", 0x4068E0: "DebugPrint stub(ret)",
               0x4A1DE0: "FILE-ID HASH?", 0x7DCFC4: "strupr?", 0x65CBF0: "RawFileClass::Open",
               0x431F10: "disk-open helper", 0x5B4610: "MixFileClass::? (arg=1)",
               0x4A1DE0: "id-hash(name,len)"}
PBUF = []
def P(*a):
    s = " ".join(str(x) for x in a); print(s); PBUF.append(s)

def disasm(start, end, title):
    P("")
    P("=" * 100)
    P(f"## {title}   0x{start:08X} - 0x{end:08X}")
    P("=" * 100)
    off = va2off(start)
    for ins in md.disasm(data[off: off + (end - start)], start):
        ann = []
        for tok in ins.op_str.replace(",", " ").split():
            if tok.startswith("0x"):
                try: v = int(tok, 16)
                except ValueError: continue
                if v in short: ann.append(f'"{short[v]}"')
                elif v in KNOWN_CALLS: ann.append(KNOWN_CALLS[v])
        if ins.mnemonic in ("call", "jmp") and ins.op_str.startswith("0x"):
            t = int(ins.op_str, 16)
            if t in KNOWN_CALLS: ann.append("-> " + KNOWN_CALLS[t])
        P(f"0x{ins.address:08X}  {ins.bytes.hex():<18s} {ins.mnemonic} {ins.op_str}"
          + ("   ; " + " ".join(ann) if ann else ""))

def find_callers(target):
    """find E8 rel32 / FF15 / direct refs to target in .text"""
    out = []
    tstart = va2off(0x401000); tend = va2off(0x7E1000)
    i = tstart
    while True:
        i = data.find(b"\xe8", i, tend)
        if i < 0: break
        rel = struct.unpack_from("<i", data, i + 1)[0]
        va = 0x401000 + (i - tstart)
        if va + 5 + rel == target:
            out.append(("call", va))
        i += 1
    return out

P("== callers of 0x52CD70 (rules+art INI block) ==")
for kind, va in find_callers(0x52CD70):
    P(f"  {kind} at 0x{va:08X}")
P("== callers of 0x679EE0 (ARTMD reload) ==")
for kind, va in find_callers(0x679EE0):
    P(f"  {kind} at 0x{va:08X}")
P("== callers of 0x5B4430 (MixFileClass::Find) ==")
cs = find_callers(0x5B4430)
P(f"  {len(cs)} direct call sites (first 30): " + " ".join(f"{va:08X}" for _, va in cs[:30]))
P("== callers of 0x5B3C20 (MixFileClass::ctor) ==")
cs2 = find_callers(0x5B3C20)
P(f"  {len(cs2)} direct call sites: " + " ".join(f"{va:08X}" for _, va in cs2[:40]))

disasm(0x4A1DE0, 0x4A1EC0, "FILE-ID HASH candidate 0x4A1DE0")
disasm(0x7DCFC4, 0x7DD000, "0x7DCFC4 (strupr?)")
disasm(0x473C50, 0x473D10, "CCFileClass::Open")
disasm(0x52C930, 0x52C990, "Init: 'Init Rules' / 'Failed to initialize Rules!' area")
disasm(0x52D140, 0x52D180, "0x52D140.. (after ARTMD success block, tail of INI fn)")

open(os.path.join(OUTD, "step5_disasm.txt"), "w", encoding="utf-8").write("\n".join(PBUF) + "\n")
print("\nsaved ->", os.path.join(OUTD, "step5_disasm.txt"))
