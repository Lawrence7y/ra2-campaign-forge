# -*- coding: utf-8 -*-
"""
W168 byte-level verification (NO Ghidra, NO atlas dependency).
- Verify the two wildcard strings + base-file strings bytes at their VAs.
- Count every occurrence of those ASCII strings in the whole PE (data).
- Full .text byte scan for 4-byte little-endian literal addresses (VA), with
  capstone skipdata=True linear sweep for instruction-boundary validation.
- pefile IAT parse: FindFirstFileA/W, FindNextFileA/W, FindClose, GetFileAttributesA/W.
- Scan .text for FF 15 <iat-va> (call dword ptr [iat]) direct call sites.
All output is deterministic; every number has a shown method.
"""
import sys, struct, hashlib
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OPT_SKIPDATA

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IMAGE_BASE = 0x400000

def rva_to_off(pe, rva):
    return pe.get_offset_from_rva(rva)

def va_to_off(pe, va):
    return rva_to_off(pe, va - IMAGE_BASE)

strings = {
    0x008261A8: "BATTLEMD*.INI",
    0x0082626C: "RULEMD*.INI",
    0x00826198: "BATTLEMD.INI",   # base file, per ledger
    0x00826260: "RULESMD.INI",    # base file, per ledger
}

print("=== FILE ===")
data = open(EXE, "rb").read()
print("sha256", hashlib.sha256(data).hexdigest())
print("size", len(data))
pe = pefile.PE(EXE, fast_load=False)

print("\n=== 1. STRING BYTES AT GIVEN VAs ===")
for va, expect in strings.items():
    off = va_to_off(pe, va)
    raw = data[off:off+len(expect)+1]
    actual = raw.split(b"\x00",1)[0].decode("ascii", "replace")
    print(f"VA 0x{va:08X} off=0x{off:08X} expect={expect!r} actual={actual!r} bytes={raw.hex()} match={actual==expect}")

print("\n=== 2. OCCURRENCES OF EACH STRING IN WHOLE FILE (ASCII literal) ===")
for va, s in strings.items():
    pat = s.encode("ascii")
    hits = []
    start = 0
    while True:
        i = data.find(pat, start)
        if i < 0:
            break
        # require NUL terminator right after to count as standalone string
        end_ok = (i+len(pat) >= len(data)) or data[i+len(pat)] == 0
        hits.append((i, end_ok))
        start = i+1
    print(f"{s!r}: {len(hits)} raw occurrences (offset, NUL-terminated): {[(hex(o),e) for o,e in hits]}")

print("\n=== 3. .text SECTION INFO ===")
text = None
for s in pe.sections:
    nm = s.Name.rstrip(b"\x00").decode("ascii", "replace")
    if nm == ".text":
        text = s
        print(f".text VA=0x{IMAGE_BASE+s.VirtualAddress:08X} RVA=0x{s.VirtualAddress:08X} "
              f"VSIZE=0x{s.Misc_VirtualSize:X} RAWSIZE=0x{s.SizeOfRawData:X} off=0x{s.PointerToRawData:08X}")
if text is None:
    sys.exit("no .text")

text_va = IMAGE_BASE + text.VirtualAddress
text_off = text.PointerToRawData
text_size = text.SizeOfRawData
text_bytes = data[text_off:text_off+text_size]

print("\n=== 4. FULL .text BYTE SCAN for dword little-endian VAs (relref style) ===")
targets = [0x008261A8, 0x0082626C, 0x00826198, 0x00826260]
for t in targets:
    pat = struct.pack("<I", t)
    hits = []
    start = 0
    while True:
        i = text_bytes.find(pat, start)
        if i < 0:
            break
        hits.append(text_va + i)
        start = i + 1
    print(f"VA 0x{t:08X} bytes={pat.hex()} => {len(hits)} hits in .text: {[hex(h) for h in hits]}")

print("\n=== 5. capstone skipdata=True LINEAR SWEEP of .text; boundary validation of literal hits ===")
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True
# build address -> (size, mnemonic, op_str, bytes) for all instructions
insn_at = {}
count = 0
for insn in md.disasm(text_bytes, text_va):
    insn_at[insn.address] = (insn.size, insn.mnemonic, insn.op_str, insn.bytes.hex())
    count += 1
print("total decoded instructions (skipdata=True):", count)
for t in targets:
    pat = struct.pack("<I", t)
    n = 0
    # find pattern occurrences, check if they are instruction starts
    start = 0
    while True:
        i = text_bytes.find(pat, start)
        if i < 0:
            break
        h = text_va + i
        if h in insn_at:
            sz, mn, op, by = insn_at[h]
            is_push = mn == "push" and op.lower().endswith(f"0x{t:08x}".lower().replace("0x","0x"))
            print(f"  0x{t:08X} hit@0x{h:08X} IS instruction boundary: {mn} {op} bytes={by} size={sz} push_literal={is_push}")
        else:
            print(f"  0x{t:08X} hit@0x{h:08X} NOT an instruction start (mid-instruction/data)")
        start = i + 1
        n += 1

print("\n=== 6. IAT: imports of interest ===")
interesting = {"FindFirstFileA","FindFirstFileW","FindNextFileA","FindNextFileW",
               "FindClose","GetFileAttributesA","GetFileAttributesW",
               "lstrcmpA","lstrcmpiA","_stricmp","strcmp","qsort"}
found_iat = {}
for entry in pe.DIRECTORY_ENTRY_IMPORT:
    dll = entry.dll.decode("ascii", "replace")
    for imp in entry.imports:
        nm = imp.name.decode("ascii", "replace") if imp.name else f"ord{imp.ordinal}"
        if nm in interesting:
            found_iat[imp.address] = (dll, nm)
            print(f"  IAT VA 0x{imp.address:08X} = {dll}!{nm}")
# print all IAT entries whose VA is near 0x7E1200 (the §910 claims)
print("  -- IAT slots in [0x7E1180,0x7E1320) --")
for entry in pe.DIRECTORY_ENTRY_IMPORT:
    dll = entry.dll.decode("ascii", "replace")
    for imp in entry.imports:
        if 0x007E1180 <= imp.address < 0x007E1320:
            nm = imp.name.decode("ascii","replace") if imp.name else f"ord{imp.ordinal}"
            print(f"    0x{imp.address:08X} = {dll}!{nm}")

print("\n=== 7. .text direct call sites to those IAT slots (FF 15 <va LE>) ===")
for iatva, (dll, nm) in sorted(found_iat.items()):
    pat = b"\xff\x15" + struct.pack("<I", iatva)
    hits = []
    start = 0
    while True:
        i = text_bytes.find(pat, start)
        if i < 0:
            break
        h = text_va + i
        boundary = h in insn_at
        hits.append((h, boundary, insn_at.get(h, ("?", "?", "?", "?"))[:3]))
        start = i + 1
    if hits:
        print(f"  {dll}!{nm} IAT 0x{iatva:08X}: {len(hits)} call sites:")
        for h, b, meta in hits:
            print(f"     @0x{h:08X} boundary={b} {meta}")
