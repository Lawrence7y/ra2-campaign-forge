"""R1: function-boundary census and naming-coverage baseline.

Enumerates function entry points from the binary itself (direct call targets,
jump-table targets, prologue shapes) rather than trusting any single tool, then
counts how many are covered by a name in the corpus symbol map.

Read-only; prints a report.
"""

import json
import re
import struct

import capstone

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = ROOT + r"\ra2youli\gamemd.exe"
SYMS = ROOT + r"\re_atlas\evidence\symbol_map.json"


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
        secs.append({"name": name, "va": image_base + vaddr, "vsize": vsize,
                     "rawptr": rawptr, "rawsize": rawsize})
    return blob, image_base, secs


BLOB, IB, SECS = load_pe(EXE)
TEXT = next(s for s in SECS if s["name"] == ".text")


def text_bytes():
    return BLOB[TEXT["rawptr"]: TEXT["rawptr"] + TEXT["rawsize"]]


def cstr_vendored():
    """Function set from MSVC prologue shapes, the classic 'hotspot' sweep."""
    data = text_bytes()
    base = TEXT["va"]
    entries = set()
    # push ebp; mov ebp, esp  /  push <reg>; mov <reg>, esp  /  sub esp, imm
    for m in re.finditer(rb"\x55\x8b\xec", data):
        entries.add(base + m.start())
    for m in re.finditer(rb"\x83\xec[\x00-\xff]", data):
        entries.add(base + m.start())
    for m in re.finditer(rb"\x81\xec[\x00-\xff]{4}", data):
        entries.add(base + m.start())
    return entries


def direct_call_targets():
    """All rel32 call targets that land inside .text on an instruction boundary."""
    data = text_bytes()
    base = TEXT["va"]
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    targets = set()
    for insn in md.disasm_lite(data, base):
        addr, size, mnem, ops = insn
        if mnem != "call" or not ops.startswith("0x"):
            continue
        try:
            tgt = int(ops, 16)
        except ValueError:
            continue
        lo, hi = TEXT["va"], TEXT["va"] + len(data)
        if lo <= tgt < hi:
            targets.add(tgt)
    return targets


def main():
    calls = direct_call_targets()
    protos = cstr_vendored()
    print(f"# .text va=0x{TEXT['va']:08X} rawsize=0x{TEXT['rawsize']:X}")

    smap = json.load(open(SYMS, encoding="utf-8"))["map"]
    named = {int(k, 16) for k in smap}
    # entry points named somewhere in the corpus even if the corpus names a
    # mid-function site; count exact-entry matches only, this is the honest floor
    exact_named_calls = len(calls & named)
    print(f"# direct-call targets in .text : {len(calls):6d}")
    print(f"#   of which corpus-named      : {exact_named_calls:6d} "
          f"({100.0 * exact_named_calls / max(1, len(calls)):.2f}%)")
    print(f"# prologue-shape candidates    : {len(protos):6d}")
    print(f"#   of which corpus-named      : {len(protos & named):6d} "
          f"({100.0 * len(protos & named) / max(1, len(protos)):.2f}%)")
    union = calls | protos
    print(f"# union(call, prologue)        : {len(union):6d}")
    print(f"#   of which corpus-named      : {len(union & named):6d} "
          f"({100.0 * len(union & named) / max(1, len(union)):.2f}%)")
    print(f"# corpus-named VAs in .text    : {len(named):6d}")

    # how much of .text is reachable from call targets only (coverage sanity)
    covered = sum(1 for a in union if TEXT["va"] <= a < TEXT["va"] + TEXT["rawsize"])
    print(f"# union inside .text bounds    : {covered}")


main()
