# -*- coding: utf-8 -*-
"""Extended RTTI slot search (k up to 128) + detailed ③b② site/callee dump for S06 B1."""
import os, sys, json, io, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
WORK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK)
import recore as R
import core2 as C2
from capstone import *

def resolve_slot_ext(refva, maxk=130):
    for k in range(0, maxk):
        vb = refva - 4 * k
        c = C2.u32(vb - 4)
        if not c:
            continue
        ci = C2.parse_col(c)
        if not ci or ci["sig"] != 0:
            continue
        tdi = C2.parse_td(ci["td"])
        if tdi and tdi["name"] and ".?AV" in tdi["name"]:
            return {"vb": vb, "off": 4*k, "slots": k, "col": ci["col"],
                    "td": tdi["td"], "name": tdi["name"], "name_va": tdi["name_va"]}
    return None

mode = sys.argv[1] if len(sys.argv) > 1 else "rtti"
AN = json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))

if mode == "rtti":
    # Check the 3 no-RTTI rows with extended search
    for e in ("00543330", "005FC570", "005FD270"):
        ea = int(e, 16)
        refs = C2.find_dword_refs(ea)
        print("ROW", e, "refs=", ["%08X" % r for r, s in refs])
        for refva, sec in refs:
            ext = resolve_slot_ext(refva)
            print("  ref %08X ext=" % refva, ext)
    # Also verify high-slot matches for all rows' clue slot numbers
    print("\n--- verify clue slot number vs found slot# ---")
    clues = {"00543330":73,"005439F0":6,"00543B10":8,"005FC570":73,"005FD270":54,
             "005F3E70":23,"005F92D0":25}
    for e, sn in clues.items():
        ea = int(e,16)
        for refva, sec in C2.find_dword_refs(ea):
            ext = resolve_slot_ext(refva)
            if ext:
                print("  %s clue_slot=%d -> ref=%08X vt=%08X slot#=%d name=%s %s" % (
                    e, sn, refva, ext["vb"], ext["slots"], ext["name"],
                    "MATCH" if ext["slots"]==sn else "MISMATCH"))
elif mode == "sites":
    # Dump candidate ③b② sites with instruction context + callee return profile
    rows = sys.argv[2:] if len(sys.argv) > 2 else [r["entry"] for r in AN]
    for rec in AN:
        if rec["entry"] not in rows: continue
        print("="*100)
        print("ROW", rec["entry"], rec["name"])
        chA = rec.get("chA") or {}
        sites = chA.get("sites", [])
        if not sites:
            print("  [NO ③b② SITE]")
            continue
        for st in sites:
            print("\n  SITE call=%08X callee=%s test=%s imm=%s jcc=%s->%s" % (
                st["call_addr"],
                ("%08X"%st["callee"]) if st.get("callee") else "?",
                st.get("test_kind"), st.get("test_imm"), st.get("jcc_mnemonic"),
                ("%08X"%st["jcc_target"]) if st.get("jcc_target") else "?"))
            # context around call (from call-6 to jcc+20 bytes)
            start = st["call_addr"] - 12
            end = st["jcc_addr"] + 24
            raw = R.read_va(start, end-start)
            for ins in R.disasm(start, raw):
                mark = ""
                if ins.address == st["call_addr"]: mark += " <== CALL"
                if ins.address == st["test_addr"]: mark += " <== TEST"
                if ins.address == st["jcc_addr"]: mark += " <== JCC"
                print("    %08X: %-8s %-32s | %s%s" % (
                    ins.address, ins.mnemonic, ins.op_str, ins.bytes.hex(" "), mark))
            # callee detail
            cal = st.get("callee")
            if cal and R.in_text(cal):
                cap = R.ATLAS.get(R.hx(cal), {}).get("size")
                if cap:
                    print("    CALLEE %08X size=%d:" % (cal, cap))
                    insns = R.disasm(cal, R.read_va(cal, cap))
                    for ins in insns:
                        if ins.id == 0: continue
                        print("      %08X: %-8s %-30s | %s" % (
                            ins.address, ins.mnemonic, ins.op_str, ins.bytes.hex(" ")))
                        if ins.address - cal >= cap: break
elif mode == "callee":
    # Dump specific calleeby addr
    for a in sys.argv[2:]:
        va = int(a,16)
        cap = R.ATLAS.get(R.hx(va), {}).get("size") or 96
        print("=== CALLEE %08X size=%d ===" % (va, cap))
        for ins in R.disasm(va, R.read_va(va, cap)):
            if ins.id==0: continue
            print("  %08X: %-8s %-30s | %s" % (ins.address, ins.mnemonic, ins.op_str, ins.bytes.hex(" ")))
