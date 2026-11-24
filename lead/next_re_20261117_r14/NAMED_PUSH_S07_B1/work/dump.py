# -*- coding: utf-8 -*-
"""Compact evidence dump for verdict decisions."""
import os, json
WORK = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(WORK, "b1_rows.json"), encoding="utf-8"))
ana = json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))
name = {r["entry"]: r["name"] for r in rows}
for r in ana:
    e = r["entry"]
    print("=" * 100)
    print("%s  %s  size=%d in_text=%s insn=%d skip=%d" % (
        e, name[e], r["atlas"].get("size", 0), r["in_text"], r["n_insn_disasm"], r["n_skipdata"]))
    print("  chA p1/p2/p3=%d/%d/%d  chB=%d  direct=%d" % (
        r["chA"]["p1"], r["chA"]["p2"], r["chA"]["p3"], len(r["chB"]), len(r["direct_callers"])))
    if r["direct_callers"]:
        print("  direct_callers: " + ",".join(r["direct_callers"][:12]))
    if r["io_direction"]:
        print("  IO_DIR: " + " | ".join("%s@%s=%s" % (x["api"], x["site"], x["dir"]) for x in r["io_direction"]))
    # chA sites
    for s in r["chA_sites"]:
        callee = s.get("callee")
        callee_s = ("%08X" % int(callee)) if callee else "INDIRECT"
        prof = s.get("callee_profile", {})
        print("  [A] call@%s -> %s  %s imm=%s jcc=%s@%s->%s" % (
            s["call_addr"], callee_s, s["test_kind"], s["test_imm"],
            s["jcc_mnemonic"], s["jcc_addr"], s.get("jcc_target")))
        if prof:
            print("      prof consts=%s n_rets=%s origins=%s" % (
                prof.get("falsifiable_consts"), prof.get("n_rets"), prof.get("origins")))
    # eax trap
    for t in r["chA_eax_trap"]:
        if t["eax_overwritten"]:
            print("  [EAX-TRAP] test@%s jcc@%s overwritten: %s" % (
                t["test_addr"], t["jcc_addr"], t["eax_overwritten"]))
    # chB tables
    for t in r["chB"]:
        print("  [B] jmp@%s table=%s bound=%s ncase=%s targets=%d" % (
            t["jmp_addr"], t["table_va"], t["bound"], t["ncase"], len(t["targets"])))
    # slots
    for s in r["slots"]:
        if not s.get("rtti_name"):
            print("  [SLOT] %s NO-RTTI" % s["slot_va"])
            continue
        print("  [SLOT] slotva=%s vt=%s off=+%d slot#=%d class=%s" % (
            s["slot_va"], s["vtable_base"], s["slot_off"], s["slotno"], s["vtable_class"]))
        print("       RTTI %s -> %s -> %s  name_va=%s" % (
            s["col"], s["td"], s["rtti_name"], s["name_va"]))
        print("       vtable_head[0..3]=%s" % s["vtable_head"])
        print("       dispatch_sites(%d): %s" % (len(s["dispatch_sites"]), ",".join(s["dispatch_sites"][:8])))
        for ins in s["installs"][:12]:
            f = ins.get("in_func")
            fs = ("%08X" % f[0]) if f else "None"
            dt = ins.get("host_dtor") or {}
            print("       install@%s global=%s func=%s atexit=%s host_dtor=%s free=%s" % (
                ins.get("write_va"), ins.get("global"), fs, ins.get("atexit"),
                dt.get("verdict"), dt.get("has_free")))
print("=" * 100)
print("DONE")
