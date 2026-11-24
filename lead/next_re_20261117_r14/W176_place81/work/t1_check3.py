"""Validate the 3 channel-B-only byte hits against linear disasm instruction boundaries."""
import os, sys, bisect
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\_lead_audit")
import audit_lib

b = audit_lib.Bin()
rows, hdr = audit_lib.load_func_atlas()
entries = [r[0] for r in rows]
for target in (0x52A739, 0x5FF59A, 0x78D1B4):
    e = audit_lib.entry_at_or_before(rows, target)
    print("target", hex(target), "atlas entry", hex(e[0]) if e else None,
          "size", e[1].get("size") if e else None)
    if e:
        ok, insn, why = audit_lib.boundary_check(b, e[0], target)
        print("  boundary", ok, why, "insn", insn)
    # also disassemble 16 bytes around target from target-8
    insns = audit_lib.linear_from(b, target-8, 32)
    for ins in insns:
        if ins.address <= target+8:
            print("   ", "%08X %-8s %s" % (ins.address, ins.mnemonic, ins.op_str))
