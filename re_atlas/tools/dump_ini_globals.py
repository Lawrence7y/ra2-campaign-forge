"""R-015: recover the static CCINIClass singletons.

Every engine-level INI object is a global whose vptr is stamped at startup:

    c7 05 <addr32> f4 1a 7e 00    mov dword ptr [addr], 0x7E1AF4

This finds those sites and reports each global. Names come from YRpp
(`CCINIClass.h`); the addresses are the byte-level fact, the names are community.

Note the deliberately-absent `INI_Rules`: it is a POINTER (0x887048), assigned at
runtime, so it never appears as a `mov dword [addr], vtable` site. Missing it here
is correct, not a gap.

Read-only.  Usage: python re_atlas/tools/dump_ini_globals.py [--json]
"""

import json
import struct
import sys

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IB = 0x400000
TEXT_LO, TEXT_HI = 0x1000, 0x3E1000          # raw offsets of .text
VPTR = 0x007E1AF4                             # CCINIClass primary vtable

# YRpp/CCINIClass.h:288-296
NAMES = {
    0x00887048: ("INI_Rules", "pointer, assigned at runtime -- never a vptr site"),
    0x00887128: ("INI_AI", "aimd.ini"),
    0x00887180: ("INI_Art", "artmd.ini"),
    0x00887208: ("INI_UIMD", "uimd.ini"),
    0x008870C0: ("INI_RA2MD", "ra2md.ini"),
}


def load(path):
    with open(path, "rb") as fh:
        return fh.read()


def main():
    d = load(EXE)
    pat = struct.pack("<I", VPTR)
    sites = []
    i = d.find(pat, TEXT_LO, TEXT_HI)
    while i != -1:
        # `c7 05 <addr32> <imm32>`: the opcode sits 6 bytes before the immediate,
        # and the address in the 4 bytes right after it. Off-by-two here silently
        # yields zero sites -- hence the positive control in the NOTE below.
        if i >= 6 and d[i - 6:i - 4] == b"\xc7\x05":
            addr = struct.unpack_from("<I", d, i - 4)[0]
            sites.append({"site": "0x%08X" % (i + IB), "addr": addr})
        i = d.find(pat, i + 1, TEXT_HI)

    seen = {}
    for s in sites:
        seen.setdefault(s["addr"], []).append(s["site"])

    rows = []
    for addr in sorted(seen):
        name, what = NAMES.get(addr, (None, None))
        rows.append({
            "addr": "0x%08X" % addr,
            "sites": seen[addr],
            "name": name,
            "what": what,
            "in_bss": addr >= 0x0087E000,
        })

    if "--json" in sys.argv:
        print(json.dumps({"vptr": "0x%08X" % VPTR, "rows": rows}, indent=1))
        return

    print("CCINIClass vptr literal 0x%08X: %d sites, %d distinct globals"
          % (VPTR, len(sites), len(rows)))
    print()
    print("%-12s %-14s %-12s %-6s %s"
          % ("global", "name", "write site", "BSS", "what"))
    for r in rows:
        print("%-12s %-14s %-12s %-6s %s"
              % (r["addr"], r["name"] or "(unnamed)", r["sites"][0],
                 "yes" if r["in_bss"] else "no", r["what"] or ""))
    print()
    print("NOTE: INI_Rules (0x00887048) is absent BY DESIGN -- it is a pointer")
    print("      assigned at runtime, never stamped as a vptr. Its absence is the")
    print("      positive control that this scan finds stamp sites and nothing else.")


main()
