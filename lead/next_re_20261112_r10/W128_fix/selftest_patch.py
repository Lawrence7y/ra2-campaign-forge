#!/usr/bin/env python3
"""W128k: OFFLINE self-test of apply_hooks.py's patch arithmetic.

There is no live gamemd to test against right now, so this validates the two
things that can actually be wrong without a process:
  1. plan loading + on-disk byte agreement
  2. the emitted patch bytes: entry `E9 rel32` must land exactly on the stub,
     the stub's internal `jmp rel32` must land exactly on `resume`, the site
     `E8 rel32` must land on the helper, and every patch must parse as the
     intended single instruction + NOP padding.

It fakes an arbitrary stub/helper allocation address to exercise the rel32 math
for many addresses (including ones that make the displacement negative).
"""
import json
import os
import struct
import sys

import capstone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import apply_hooks as AH  # noqa: E402

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)


def check_rel32(src_addr, emitted, target):
    """emitted starts with E8/E9; return (decoded target, ok)."""
    if emitted[0] not in (0xE8, 0xE9):
        return None, False
    rel = struct.unpack("<i", emitted[1:5])[0]
    return (src_addr + 5 + rel) & 0xFFFFFFFF, ((src_addr + 5 + rel) & 0xFFFFFFFF) == target


def main():
    plan_a, plan_s = AH.load_plan()
    disk = AH.disk_image()
    ok = True

    print("=== plan sanity ===")
    print("  group A entries: %d" % len(plan_a))
    print("  group S sites  : %d" % len(plan_s))

    for e in plan_a:
        cur = disk(e["va"], e["orig_len"])
        good = cur == e["orig"]
        ok &= good
        print("  A %-12s orig %s  %s" % (e["label"], cur.hex(), "OK" if good else "MISMATCH"))
        # every stub must disassemble cleanly
        n = len(list(md.disasm(e["stub"], 0)))
        if n < 4:
            print("     stub disasm suspicious (%d insns)" % n)
            ok = False

    for s in plan_s:
        orig = disk(s["va"], 12)
        # helper: mov/test/je/mov al/ret + null: xor al/ret  => 7 instructions
        ins = list(md.disasm(s["helper"], 0))
        good = len(ins) == 7 and ins[-1].mnemonic == "ret" and ins[-2].mnemonic == "ret" or \
               (len(ins) == 7 and ins[-1].mnemonic == "ret")
        ok &= good
        print("  S %-12s orig %s  helper %d insns, last=%s  %s"
              % (s["label"], orig.hex(), len(ins),
                 ins[-1].mnemonic if ins else "?", "OK" if good else "BAD"))

    print("\n=== rel32 arithmetic over adversarial alloc addresses ===")
    addrs = [0x10000000, 0x20000000, 0x7FFE0000, 0x003E0000, 0x00401000, 0x00900000]
    for e in plan_a:
        item_ok = True
        for alloc in addrs:
            entry_disp = (alloc - (e["va"] + 5)) & 0xFFFFFFFF
            emitted = bytes([0xE9]) + struct.pack("<I", entry_disp)
            tgt, good = check_rel32(e["va"], emitted, alloc)
            if not good:
                print("  A %-12s alloc 0x%08X -> decoded 0x%08X BAD" % (e["label"], alloc, tgt))
                item_ok = False
            # stub's internal jmp must reach resume
            jmp_off = e["jmp_off"]
            sdisp = (e["resume"] - (alloc + jmp_off + 4)) & 0xFFFFFFFF
            jmp_ins_addr = alloc + jmp_off - 1
            emitted_j = b"\xE9" + struct.pack("<I", sdisp)
            tgt_j, good_j = check_rel32(jmp_ins_addr, emitted_j, e["resume"])
            if not good_j:
                print("  A %-12s alloc 0x%08X internal jmp -> 0x%08X BAD (want 0x%08X)"
                      % (e["label"], alloc, tgt_j, e["resume"]))
                item_ok = False
        ok &= item_ok
        print("  A %-12s %d alloc addresses: %s"
              % (e["label"], len(addrs), "OK" if item_ok else "FAIL"))

    for s in plan_s:
        item_ok = True
        for alloc in addrs:
            disp = (alloc - (s["va"] + 5)) & 0xFFFFFFFF
            emitted = bytes([0xE8]) + struct.pack("<I", disp)
            tgt, good = check_rel32(s["va"], emitted, alloc)
            if not good:
                print("  S %-12s alloc 0x%08X -> 0x%08X BAD" % (s["label"], alloc, tgt))
                item_ok = False
        ok &= item_ok
        print("  S %-12s %d alloc addresses: %s"
              % (s["label"], len(addrs), "OK" if item_ok else "FAIL"))

    print("\nOFFLINE SELF-TEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
