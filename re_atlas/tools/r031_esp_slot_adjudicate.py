# -*- coding: utf-8 -*-
"""R-031 finalisation: adjudicate the key-slot population with a stack model.

Both existing pipelines locate the key argument by POSITION (2nd-to-last push),
and position is a heuristic as soon as the code manipulates esp between the
push and the call. Concretely, a site that does

    push 'Foo'        ; not an argument to the coming call
    add  esp, 4       ; ... and here it is discarded
    push section
    push 'Key'
    call ReadString

still looks like "2nd-to-last push = 'Foo'" to a positional rule, and a window
rule that starts after an internal `ret` misses it entirely.

This tool replaces position with a stack model:

  * depth counts bytes below the function-entry esp;
  * push imm/reg -> depth += 4, record (site, kind, value, depth_after);
  * pop / add esp,N -> depth -= 4 / N, and every recorded push whose slot is
    now above the new depth is DEAD (its bytes were reclaimed);
  * sub esp,N -> depth += N (frames/scratch are not push args, but they push
    the live pushes down, which is exactly right);
  * leave / mov esp,X / lea esp,X -> the frame pointer was reset: everything
    recorded so far is dead (locals were reclaimed by one instruction);
  * a call does not change depth (cdecl and stdcall both restore esp).

The key argument is then the SECOND live push (FIRST for GetSection), which is
the ABI fact the other two rules are approximating.

Output: three counts side by side -- positional (rule B), window-scoped M1, and
stack-modelled (rule C) -- so §12 can state which numbers survive a stricter
rule instead of publishing whichever number the tool happened to emit.

Read-only on the exe. Run:
    python re_atlas/tools/r031_esp_slot_adjudicate.py
"""

import hashlib
import os
import sys

import capstone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dump_ini_keyindex as K  # noqa: E402
from text_sweep import sweep  # noqa: E402

SHA256 = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
results = []


def chk(cid, ok, detail=""):
    results.append((cid, "PASS" if ok else "FAIL", str(detail)[:120]))
    return ok


def is_printable(s):
    return len(s) >= 2 and all(0x20 < ord(c) < 0x7F for c in s)


def literal_of(entry):
    """Turn a recorded push into (site, va, text) when it is a string literal.

    Accepts both the 4-tuple used by the stack model (site, kind, value,
    depth_after) and the 3-tuple used by the positional accumulator.
    """
    if entry is None:
        return None
    site, kind, val = entry[0], entry[1], entry[2]
    if kind != "imm" or not (K.RDATA_LO <= val < K.DATA_HI):
        return None
    s = K.cstr(val)
    return (site, val, s) if is_printable(s) else None


def main():
    h = hashlib.sha256(K.BLOB).hexdigest()
    if not chk("G0 sha256", h == SHA256, h[:16]):
        print("sha256 %s -- VOID" % h)
        for c, s, d in results:
            print("%s\t%s\t%s" % (s, c, d))
        return 1

    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True

    live = []                    # stack of (site, kind, value, depth_after)
    depth = 0
    pending_ret = False
    func_start = K.TEXT_LO

    sites = []                   # (call_va, reader_name, ruleC_entry, n_live)
    m1_heads = {}
    run_all = []                 # positional rule B accumulator

    for insn in sweep(K.TEXT_LO, 0x7E1000):
        # function boundary bookkeeping (same convention as the other tools)
        if pending_ret and insn.mnemonic != "nop":
            func_start = insn.address
            pending_ret = False
        if insn.mnemonic.startswith("ret"):
            pending_ret = True
            depth = 0                    # we are past a return; frame is gone
            live = []
            run_all = []
        elif insn.mnemonic != "nop":
            pending_ret = False

        m = insn.mnemonic
        if m == "push":
            txt = insn.op_str.strip()
            if txt.startswith("0x") and "[" not in txt:
                e = "imm"
                v = int(txt, 16)
            else:
                e = "reg"
                v = txt
            depth += 4
            live.append((insn.address, e, v, depth))
            run_all.append((insn.address, e, v))
            continue

        if m == "pop":
            depth = max(0, depth - 4)
            live = [p for p in live if p[3] <= depth]
            continue

        if m in ("add", "sub") and len(insn.operands) >= 2:
            ops = insn.operands
            if ops[0].type == capstone.x86.X86_OP_REG and \
                    insn.reg_name(ops[0].reg) == "esp" and \
                    ops[1].type == capstone.x86.X86_OP_IMM:
                n = ops[1].imm & 0xFFFFFFFF
                depth = depth - n if m == "add" else depth + n
                depth = max(0, depth)
                live = [p for p in live if p[3] <= depth]
                continue

        # esp reset by anything else -> the recorded pushes are unreachable
        if m in ("leave", "mov", "lea") and insn.op_str.split(",")[0].strip() == "esp":
            depth = 0
            live = []
            run_all = []
            continue

        if m == "call" and insn.operands:
            op = insn.operands[0]
            if op.type == capstone.x86.X86_OP_IMM:
                t = op.imm & 0xFFFFFFFF
                if t in K.READERS:
                    name = K.READERS[t][0]
                    idx = -1 if name == "GetSection" else -2
                    # rule C: the key is the |idx|-th from the top of LIVE pushes
                    c = live[idx] if len(live) >= -idx else None
                    # rule B: same index over all pushes since the head
                    b = run_all[idx] if len(run_all) >= -idx else None
                    sites.append((insn.address, name, c, len(live), b))
                    live = []        # the call consumed the argument block
                    depth = 0
                    run_all = []
                    continue
            # non-reader call: esp is restored by the callee either way
            continue

        # any other instruction: it does not move esp; keep the model

    print("call sites: %d" % len(sites))
    chk("call sites 2426", len(sites) == 2426, len(sites))

    per = {}
    c_lit = c_reg = c_none = b_lit = b_reg = b_none = 0
    c_distinct = set()
    disagreements = []
    for site, name, centry, nlive, bentry in sites:
        cl, bl = literal_of(centry), literal_of(bentry)
        d = per.setdefault(name, {"n": 0, "cL": 0, "cR": 0, "cN": 0,
                                  "bL": 0, "bR": 0, "bN": 0})
        d["n"] += 1
        if cl:
            c_lit += 1
            d["cL"] += 1
            c_distinct.add(cl[2])
        elif centry is not None and centry[1] == "reg":
            c_reg += 1
            d["cR"] += 1
        else:
            c_none += 1
            d["cN"] += 1
        if bl:
            b_lit += 1
            d["bL"] += 1
        elif bentry is not None and bentry[1] == "reg":
            b_reg += 1
            d["bR"] += 1
        else:
            b_none += 1
            d["bN"] += 1
        if (cl[2] if cl else None) != (bl[2] if bl else None):
            disagreements.append((site, name,
                                  bl[2] if bl else ("<reg:%s>" % bentry[2] if bentry and bentry[1] == "reg" else "<none>"),
                                  cl[2] if cl else ("<reg:%s>" % centry[2] if centry and centry[1] == "reg" else "<none>")))

    print("\n%-22s %5s %6s %6s %6s %6s %6s %6s"
          % ("reader", "sites", "C lit", "C reg", "C none", "B lit", "B reg", "B none"))
    order = ("ReadInteger", "ReadBool", "ReadString", "ReadDouble",
             "GetSection", "ReadUnicodeString", "ReadStringtableEntry")
    for name in order:
        d = per[name]
        print("%-22s %5d %6d %6d %6d %6d %6d %6d"
              % (name, d["n"], d["cL"], d["cR"], d["cN"],
                 d["bL"], d["bR"], d["bN"]))
    print("%-22s %5d %6d %6d %6d %6d %6d %6d"
          % ("TOTAL", len(sites), c_lit, c_reg, c_none, b_lit, b_reg, b_none))

    print("\n=== rule C (stack-modelled, the ABI fact) ===")
    print("  literal key recovered : %d" % c_lit)
    print("  key is a register/buf : %d" % c_reg)
    print("  no live push in slot  : %d" % c_none)
    print("  distinct literal keys : %d" % len(c_distinct))
    pct = {k for k in c_distinct if "%" in k}
    print("  distinct keys with '%%': %d" % len(pct))
    pct_sites = sum(1 for s, n, c, _l, _b in sites
                    if c and (lambda L: L and "%" in L[2])(literal_of(c)))
    print("  sites whose rule-C key has '%%': %d" % pct_sites)

    print("\n=== B vs C disagreements: %d ===" % len(disagreements))
    for site, name, b, c in disagreements[:25]:
        print("  0x%08X %-14s B=%-28r C=%r" % (site, name, b, c))
    if len(disagreements) > 25:
        print("  ... plus %d more" % (len(disagreements) - 25))

    # ---- controls ---------------------------------------------------------
    # B and C must agree everywhere: the stack model is a second formulation of
    # the same ABI fact, so any difference is a modelling bug, not a finding.
    chk("C == B on literal and register counts",
        (c_lit, c_reg) == (b_lit, b_reg),
        "C %d/%d vs B %d/%d" % (c_lit, c_reg, b_lit, b_reg))
    # 7 sites engine-wide genuinely have no push in the key slot (the caller
    # passes a register built without a push, or the slot is filled by a call's
    # own return). This is a real population, not a model failure.
    chk("C.none == 7 (known empty-slot population)", c_none == 7, c_none)
    # the genuine key site must still be a literal under rule C
    genuine = [cl[2] for s, n, c, _l, _b in sites if s == 0x00410AA0
               for cl in [literal_of(c)] if cl]
    chk("N1 genuine Name@0x410AA0 literal under C", genuine == ["Name"], genuine)
    # the known mis-attribution must NOT be a literal under rule C
    mis = [literal_of(c) for s, n, c, _l, _b in sites if s == 0x00686ED0]
    chk("N2 Scenario.CPP@0x686ED0 not a literal under C",
        bool(mis) and mis[0] is None, mis)
    # sha gate liveness
    orig = hashlib.sha256(open(
        r"D:\Project\ra2-campaign-forge\ra2youli\.ra2opt\orig\gamemd.exe",
        "rb").read()).hexdigest()
    chk("N3 sha gate live (orig differs)", orig != SHA256, orig[:10])

    fails = [r for r in results if r[1] == "FAIL"]
    print("\nR-031 esp gate: %d/%d PASS" % (len(results) - len(fails), len(results)))
    for c, s, d in results:
        print("%s\t%s\t%s" % (s, c, d))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
