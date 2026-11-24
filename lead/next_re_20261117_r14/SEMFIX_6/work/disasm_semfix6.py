# -*- coding: utf-8 -*-
import json, os, struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SEMFIX_6\EVIDENCE"

data = open(EXE, "rb").read()
pe = struct.unpack_from("<I", data, 0x3C)[0]
assert data[pe:pe+4] == b"PE\0\0"
coff = pe + 4
nsec = struct.unpack_from("<H", data, coff + 2)[0]
optsz = struct.unpack_from("<H", data, coff + 16)[0]
opt = coff + 20
image_base = struct.unpack_from("<I", data, opt + 28)[0]
sections = []
sec = opt + optsz
for i in range(nsec):
    o = sec + 40 * i
    name = data[o:o+8].rstrip(b"\0").decode("ascii", "replace")
    vsize, vaddr, rsize, raddr = struct.unpack_from("<IIII", data, o + 8)
    sections.append({"name": name, "vsize": vsize, "vaddr": vaddr, "rsize": rsize, "raddr": raddr})

def rva_to_off(rva):
    for s in sections:
        if s["vaddr"] <= rva < s["vaddr"] + max(s["vsize"], s["rsize"]):
            return s["raddr"] + rva - s["vaddr"]
    raise ValueError("RVA not mapped: 0x%X" % rva)

def va_to_off(va):
    return rva_to_off(va - image_base)

def section_for_va(va):
    rva = va - image_base
    for s in sections:
        if s["vaddr"] <= rva < s["vaddr"] + max(s["vsize"], s["rsize"]):
            return s["name"]
    return "UNMAPPED"

def read_u32(va):
    return struct.unpack_from("<I", data, va_to_off(va))[0]

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False

def fmt(insn):
    return "%08X  %-20s %-8s %s" % (insn.address, insn.bytes.hex(), insn.mnemonic, insn.op_str)

def disasm_range(start, end):
    off = va_to_off(start)
    size = end - start
    return [fmt(i) for i in md.disasm(data[off:off+size], start)]

blocks = {
    "0040F0A0": [(0x0040F0A0, 0x0040F150)],
    "0040F150": [(0x0040F150, 0x0040F176)],
    "00417FE0": [(0x00417FE0, 0x00418006), (0x00418D1D, 0x00418D55)],
    "0041A5C0": [(0x0041A5C0, 0x0041A936)],
    "0041FB10": [(0x0041FB10, 0x0041FC97)],
    "0044ACF0": [(0x0044ACF0, 0x0044B0DE), (0x0044B0DE, 0x0044B187)],
}

summary = {"image_base": hex(image_base), "sections": sections, "functions": {}, "tables": {}}
for entry, ranges in blocks.items():
    lines = []
    for start, end in ranges:
        lines.append("; RANGE %08X..%08X" % (start, end))
        lines.extend(disasm_range(start, end))
    path = os.path.join(OUT, "DISASM_FULL_%s.txt" % entry)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    summary["functions"][entry] = {"ranges": [[hex(a), hex(b)] for a,b in ranges], "lines": len(lines), "path": path}

tables = {"00417FE0": (0x00418D58, 10), "0044ACF0": (0x0044B728, 11)}
for entry, (tva, n) in tables.items():
    targets = [read_u32(tva + 4*i) for i in range(n)]
    lines = ["; TABLE %s VA=%08X slots=%d" % (entry, tva, n)]
    for i, t in enumerate(targets):
        lines.append("; slot %02d -> %08X (%s)" % (i, t, section_for_va(t)))
        lines.extend(disasm_range(t, t + 24))
        lines.append("")
    path = os.path.join(OUT, "JUMP_TARGETS_%s.txt" % entry)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    summary["tables"][entry] = {"table_va": hex(tva), "slots": n, "targets": [hex(t) for t in targets], "sections": [section_for_va(t) for t in targets], "path": path}

with open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SEMFIX_6\work\disasm_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

print(json.dumps({"image_base": hex(image_base), "functions": summary["functions"], "tables": summary["tables"]}, indent=2))
