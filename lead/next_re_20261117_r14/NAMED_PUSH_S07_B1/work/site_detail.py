# -*- coding: utf-8 -*-
"""Detailed per-site path signature dump: show taken vs fallthrough instructions."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
WORK = os.path.dirname(os.path.abspath(__file__))
ana = {r["entry"]: r for r in json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))}
sel = sys.argv[1:] if len(sys.argv) > 1 else list(ana.keys())
for e in sel:
    r = ana[e]
    ea = int(e, 16); size = r["atlas"].get("size", 0)
    insns = R.disasm(ea, R.read_va(ea, size if size else 512))
    idx = {ins.address: i for i, ins in enumerate(insns)}
    print("=" * 90)
    print("ENTRY %s %s sites=%d" % (e, r["hint_name"], len(r["chA_sites"])))
    for s in r["chA_sites"]:
        ca = int(s["call_addr"], 16) if isinstance(s["call_addr"], str) else s["call_addr"]
        ta = int(s["test_addr"], 16) if isinstance(s["test_addr"], str) else s["test_addr"]
        ja = int(s["jcc_addr"], 16) if isinstance(s["jcc_addr"], str) else s["jcc_addr"]
        jt = s.get("jcc_target")
        jt = int(jt, 16) if isinstance(jt, str) and jt else jt
        print("  --- site call@%08X callee=%s %s imm=%s jcc=%s@%08X -> %s" % (
            ca, s.get("callee"), s["test_kind"], s["test_imm"],
            s["jcc_mnemonic"], ja, ("%08X" % jt) if jt else "?"))
        # context around call (from call-2 to test+2)
        ci = idx.get(ca); ti = idx.get(ta)
        if ci is not None and ti is not None:
            print("    [ctx]")
            for ins in insns[max(0,ci-1):min(len(insns), ti+2)]:
                print("      %08X: %s %s | %s" % (ins.address, ins.mnemonic, ins.op_str, ins.bytes.hex()))
        # taken path (first 10 insns from jt)
        if jt in idx:
            print("    [TAKEN @%08X]" % jt)
            for ins in insns[idx[jt]:idx[jt]+10]:
                print("      %08X: %s %s | %s" % (ins.address, ins.mnemonic, ins.op_str, ins.bytes.hex()))
        # fallthrough
        ji = idx.get(ja)
        if ji is not None:
            print("    [FALLTHROUGH @%08X]" % insns[ji].address)
            for ins in insns[ji+1:ji+11]:
                print("      %08X: %s %s | %s" % (ins.address, ins.mnemonic, ins.op_str, ins.bytes.hex()))
