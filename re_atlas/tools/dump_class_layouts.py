"""Re-derive trigger-family class sizes and the AbstractClass MI prefix.

Two facts this script establishes from bytes alone:

1. Instance size of each class = immediate in its vtable[12] body. Note that
   AbstractClass::GetSize returns 0 (``xor eax,eax; ret``) -- that is an
   abstract stub, not a size of zero, so sizes must be taken per class.

2. AbstractClass has FOUR vtable pointers (offsets 0/4/8/0xC), i.e. a
   multiple-inheritance layout. Proven by decoding the scalar deleting
   destructor and by resolving each vtable's CompleteObjectLocator offset.

Read-only. Run from the repository root:
    python re_atlas/tools/dump_class_layouts.py
"""

import json
import os
import struct
import sys

import capstone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
SYMS = os.path.join(ROOT, "re_atlas", "evidence", "rtti", "symbols.json")

IB = 0x400000
GETSIZE_SLOT = 12

# Classes covered by kb/11_class_layouts.md
TARGETS = [
    "ScriptClass", "TagClass", "TriggerClass", "TEventClass", "TActionClass",
    "TeamClass", "TaskForceClass", "ScriptTypeClass",
    "AbstractClass", "AbstractTypeClass",
]

# Scalar deleting destructor located by hand in R2-1 round 2
ABSTRACT_DTOR = 0x004105A0


def load():
    if not os.path.isfile(EXE):
        sys.exit(
            f"gamemd.exe not found at:\n  {EXE}\n"
            "This repository intentionally does not ship the game binary.\n"
            "Place a clean Yuri's Revenge gamemd.exe at ra2youli/gamemd.exe and retry."
        )
    if not os.path.isfile(SYMS):
        sys.exit(
            f"RTTI dump not found at:\n  {SYMS}\n"
            "Generate it first:  python -m ra2re rtti ra2youli/gamemd.exe --out re_atlas/evidence/rtti"
        )
    with open(EXE, "rb") as fh:
        return fh.read()


BLOB = load()
MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)


def u32(va):
    return struct.unpack_from("<I", BLOB, va - IB)[0]


def read(va, n):
    return BLOB[va - IB: va - IB + n]


def disasm(va, n):
    return list(MD.disasm(read(va, n), va))


def size_of(vtable_va):
    """Decode vtable[12]'s body: (size or None, asm text, fn_va)."""
    fn = u32(vtable_va + GETSIZE_SLOT * 4)
    insns = disasm(fn, 16)
    if not insns:
        return None, "", fn
    i0 = insns[0]
    if i0.mnemonic == "mov" and i0.op_str.replace(" ", "").startswith("eax,"):
        src = i0.op_str.split(",", 1)[1].strip()
        try:
            return int(src, 0), f"{i0.mnemonic} {i0.op_str}", fn
        except ValueError:
            pass
    return None, f"{i0.mnemonic} {i0.op_str}", fn


def main():
    d = json.load(open(SYMS, encoding="utf-8"))
    classes = {}
    for _k, c in d["classes"].items():
        classes[c["name"]] = c

    print("## 1. instance sizes from vtable[12]")
    print(f"# {'class':22s} {'vtable':>10s} {'slots':>5s} {'size':>6s}  body")
    for name in TARGETS:
        c = classes.get(name)
        if not c:
            print(f"  {name:22s}  (not in RTTI)")
            continue
        vt = int(c["vtable_va"], 16)
        nv = len(c.get("vfuncs") or [])
        size, asm, _fn = size_of(vt)
        shown = str(size) if size is not None else "-"
        print(f"  {name:22s} 0x{vt:08X} {nv:5d} {shown:>6s}  {asm}")

    print()
    print("## 2. AbstractClass vtable pointer writes (from the deleting destructor)")
    print(f"# dtor at 0x{ABSTRACT_DTOR:06X}")
    writes = []
    for insn in disasm(ABSTRACT_DTOR, 0x40):
        if insn.mnemonic == "mov" and insn.op_str.count(",") == 1:
            dst, src = [x.strip() for x in insn.op_str.split(",")]
            if dst.startswith("dword ptr [esi") and src.startswith("0x"):
                writes.append((insn.address, dst, int(src, 16)))
    for addr, dst, val in writes:
        print(f"#   0x{addr:06X}  {dst:24s} <- 0x{val:06X}")

    print()
    print("## 3. each vtable's CompleteObjectLocator offset (= this-adjustment)")
    print(f"# {'vtable':>10s} {'COL':>10s} {'COL.offset':>10s}  meaning")
    for _addr, _dst, vt in writes:
        col = u32(vt - 4)
        off = u32(col + 4)
        print(f"#   0x{vt:06X} 0x{col:08X} {off:10d}  "
              f"{'main class' if off == 0 else 'interface subobject'}")

    offsets = [u32(u32(vt - 4) + 4) for _a, _d, vt in writes]
    verdict = ("MULTIPLE INHERITANCE (offsets " + ",".join(map(str, offsets)) + ")"
               if len(set(offsets)) > 1 else "single inheritance")
    print(f"# VERDICT: {verdict}")


main()
