"""Cross-check the instance sizes claimed in the ATLAS master table.

The ATLAS asserts that vtable[12] is AbstractClass::GetSize and that the body
begins with `mov eax, <size>`. This resolves vtable[12] for each cited class
straight from bytes and decodes the immediate, so sizes are re-derived rather
than copied.

It also reports the case the ATLAS misses: some classes put an accessor in slot
12 (`mov eax,[ecx]`), so the slot is NOT GetSize for them. Those rows come back
as NO-IMM instead of silently producing a wrong number.

Run from the repository root:
    python re_atlas/tools/xcheck_sizes.py
"""

import json
import os
import re
import struct

import capstone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
SYMS = os.path.join(ROOT, "re_atlas", "evidence", "rtti", "symbols.json")
ATLAS = os.path.join(ROOT, "docs", "re", "ARCHITECTURE_ATLAS.md")
GETSIZE_SLOT = 12

ROW_RE = re.compile(
    r"\|\s*\*\*`([A-Za-z_][A-Za-z0-9_]*)`\*\*\s*\|\s*\*\*`0x([0-9A-Fa-f]{8})`\*\*\s*\|\s*(\d+)\s*\|"
    r"\s*(\d+)\s*\|\s*`?0x([0-9A-Fa-f]+)`?\s*\|"
)


def load_pe(path):
    with open(path, "rb") as fh:
        blob = fh.read()
    e = struct.unpack_from("<I", blob, 0x3C)[0]
    nsec = struct.unpack_from("<H", blob, e + 6)[0]
    opt_size = struct.unpack_from("<H", blob, e + 20)[0]
    opt = e + 24
    image_base = struct.unpack_from("<I", blob, opt + 28)[0]
    tab = opt + opt_size
    secs = []
    for i in range(nsec):
        o = tab + i * 40
        name = blob[o:o + 8].rstrip(b"\0").decode("ascii", "replace")
        vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", blob, o + 8)
        secs.append((name, vaddr, vsize, rawsize, rawptr))
    return blob, image_base, secs


BLOB, IB, SECS = load_pe(EXE)
MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)


def read_va(va, n):
    rva = va - IB
    for _name, vaddr, vsize, rawsize, rawptr in SECS:
        if vaddr <= rva < vaddr + max(vsize, rawsize):
            d = rva - vaddr
            if d >= rawsize:
                return b""              # BSS tail: no backing bytes
            return BLOB[rawptr + d: rawptr + d + n]
    return b""


def u32_at(va):
    b = read_va(va, 4)
    return struct.unpack("<I", b)[0] if len(b) == 4 else None


def hx(v):
    return None if v is None else (int(v, 16) if isinstance(v, str) else int(v))


def size_from_getsize(fn_va):
    """Return (size, asm) from a GetSize body, or (None, asm) when it is not one."""
    code = read_va(fn_va, 24)
    if not code:
        return None, ""
    insns = list(MD.disasm(code, fn_va))
    for insn in insns[:4]:
        if insn.mnemonic == "mov" and insn.op_str.replace(" ", "").startswith("eax,"):
            src = insn.op_str.split(",")[1].strip()
            try:
                return int(src, 0), f"{insn.mnemonic} {insn.op_str}"
            except ValueError:
                return None, f"{insn.mnemonic} {insn.op_str}"
        if insn.mnemonic == "ret":
            break
    return None, (f"{insns[0].mnemonic} {insns[0].op_str}" if insns else "")


def load_classes():
    d = json.load(open(SYMS, encoding="utf-8"))
    out = {}
    for _k, c in d["classes"].items():
        c = dict(c)
        c["vtable_va"] = hx(c.get("vtable_va"))
        out[c["name"]] = c
    return out


def main():
    classes = load_classes()
    rows = []
    for line in open(ATLAS, encoding="utf-8", errors="replace"):
        m = ROW_RE.search(line)
        if m:
            rows.append((m.group(1), int(m.group(2), 16), int(m.group(3)),
                         int(m.group(4)), int(m.group(5), 16)))

    print(f"# ATLAS size rows parsed: {len(rows)}")
    print(f"# {'class':24s} {'atlas_vt':>10s} {'rtti_vt':>10s} {'vfun':>5s} "
          f"{'atlas_size':>10s} {'derived':>8s}  status")
    agree = differ = nodata = 0
    for name, vt, nvf, size, _hex in rows:
        c = classes.get(name)
        rtti_vt = c["vtable_va"] if c else None
        fn = u32_at(vt + GETSIZE_SLOT * 4)
        derived, asm = size_from_getsize(fn) if fn else (None, "")
        notes = []
        if rtti_vt is not None and rtti_vt != vt:
            notes.append("VT-DIFF")
        if derived is None:
            nodata += 1
            status = "NO-IMM " + asm
        elif derived == size:
            agree += 1
            status = "SIZE-OK"
        else:
            differ += 1
            status = f"SIZE-DIFF ({asm})"
        if notes:
            status = " ".join(notes) + " " + status
        print(f"  {name:24s} 0x{vt:08X} "
              + (f"0x{rtti_vt:08X}" if rtti_vt else "   -----  ")
              + f" {nvf:5d} {size:10d} "
              + (f"{derived:8d}" if derived is not None else "    ----") + f"  {status}")
    print(f"# RESULT size_agree={agree} size_differ={differ} no_immediate={nodata}")


main()
