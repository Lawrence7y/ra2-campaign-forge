"""R-014: dump a class's primary vtable slot by slot, with a role guess.

The point is to make the slot contract re-derivable rather than quoted from a
previous round's notes. Every slot value is classified:

  TEXT   -> a real function in .text; body first instructions are printed
  COLPTR -> the value is in .rdata: this is MSVC's vtable[-1] CompleteObjectLocator
            of the NEXT table, not a virtual function of this one
  ZERO   -> null slot

Read-only.  Usage: python re_atlas/tools/dump_vtable_slots.py [--json] [VA ...]
"""

import json
import os
import struct
import sys

import capstone

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IB = 0x400000
TEXT_LO, TEXT_HI = 0x401000, 0x7E1000
RDATA_LO, RDATA_HI = 0x7E1000, 0x811074      # .rdata VA range (rva 0x3E1000 + 0x30074)
DATA_LO, DATA_HI = 0x812000, 0xB79BE4        # .data VA range
# CompleteObjectLocators live in .rdata, but the TypeDescriptors they point at
# live in .data -- so a name lookup must accept both.
STR_LO, STR_HI = RDATA_LO, DATA_HI

DEFAULT = [("AbstractClass", 0x007E1F50), ("TEventClass", 0x007F5578)]


def load(path):
    with open(path, "rb") as fh:
        return fh.read()


D = load(EXE)
MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)


def u32(va):
    off = va - IB
    if off < 0 or off + 4 > len(D):
        return None
    return struct.unpack_from("<I", D, off)[0]


def read_va(va, n):
    off = va - IB
    if off < 0 or off + n > len(D):
        return b""
    return D[off:off + n]


def cstr(va, cap=64):
    return read_va(va, cap).split(b"\x00")[0].decode("latin1")


def body(fn, n=6):
    out = []
    for insn in list(MD.disasm(read_va(fn, 48), fn))[:n]:
        out.append("%s %s" % (insn.mnemonic, insn.op_str))
        if insn.mnemonic.startswith("ret"):
            break
    return " ; ".join(out)


def classify(val):
    if val is None:
        return "OUT-OF-IMAGE", ""
    if val == 0:
        return "ZERO", ""
    if TEXT_LO <= val < TEXT_HI:
        return "TEXT", body(val)
    if RDATA_LO <= val < RDATA_HI:
        return "COLPTR", describe_col(val)
    return "OTHER", "0x%08X" % val


def describe_col(col):
    """Decode a CompleteObjectLocator and name the type it points at."""
    if not (RDATA_LO <= col < RDATA_HI):
        return "0x%08X (not in .rdata)" % col
    td = u32(col + 0x0C)
    if td is None:
        return "truncated COL"
    name = "?"
    if STR_LO <= td < STR_HI:
        name = cstr(td + 8, 96)
    return "COL -> %s" % name


def dump(name, vt, stop_at_col=True):
    """Walk slots until a COL pointer appears (that is the next table)."""
    rows = []
    for slot in range(64):
        val = u32(vt + 4 * slot)
        kind, detail = classify(val)
        rows.append({
            "slot": slot,
            "plus": "0x%02X" % (4 * slot),
            "value": "0x%08X" % (val if val is not None else 0),
            "kind": kind,
            "detail": detail,
        })
        if kind == "COLPTR" and stop_at_col:
            break
    return {"class": name, "vtable": "0x%08X" % vt, "slots": rows}


def main():
    if "--json" in sys.argv:
        targets = DEFAULT
        print(json.dumps([dump(n, v) for n, v in targets], indent=1))
        return

    for name, vt in DEFAULT:
        info = dump(name, vt)
        print("=== %s   vtable 0x%08X ===" % (name, vt))
        print("  %-5s %-6s %-12s %-7s %s"
              % ("slot", "plus", "value", "kind", "body / detail"))
        for r in info["slots"]:
            print("  [%2d]  %-6s %-12s %-7s %s"
                  % (r["slot"], r["plus"], r["value"], r["kind"], r["detail"]))
        print()
        n_text = sum(1 for r in info["slots"] if r["kind"] == "TEXT")
        n_col = sum(1 for r in info["slots"] if r["kind"] == "COLPTR")
        print("  -> %d function slots, ended by %d COL pointer(s)"
              % (n_text, n_col))
        print()


main()
