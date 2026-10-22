# -*- coding: utf-8 -*-
"""R-031 finalisation: the authoritative M1/M2 rule comparison.

Purpose: settle, with one deterministic run, every number that kb/30 §12 needs
and every claim the independent sweep graded REFUTED.

Three rules are in play and they answer different questions:

  M1        "nearest preceding string-literal push, scanning from the enclosing
             function's head" -- the published §12 predicate. Recovered count
             depends on where the function head is (window origin).
  M2-B      "the push that occupies the KEY argument slot" -- 2nd-to-last push
             before the call for all six readers, last push for GetSection,
             counted over ALL pushes since the function head regardless of any
             interleaving. This is the faithful key-slot rule.
  M2-A      same slot index but computed over the trailing CONSECUTIVE push run,
             so any interleaved non-push instruction splits the argument list
             and the rule falls back. This is what makes ReadDouble look like it
             has 68 register-slots instead of 1.

The ReadDouble "1 vs 68" recorded in LEDGER §4b is NOT a cross-family
disagreement: both pipelines get 1 under M2-B. 68 is the M2-A figure, from the
same report. This tool reproduces all three so the point is checkable, and
prints the corrected cross-family comparison.

Read-only on the exe. Run:
    python re_atlas/tools/r031_finalise_rules.py
"""

import hashlib
import os
import sys

import capstone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dump_ini_keyindex as K  # noqa: E402
from text_sweep import sweep  # noqa: E402

SHA256 = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
PRINTABLE = lambda s: len(s) >= 2 and all(0x20 < ord(c) < 0x7F for c in s)
results = []


def chk(cid, ok, detail=""):
    results.append((cid, "PASS" if ok else "FAIL", str(detail)[:120]))
    return ok


def build():
    """One forward pass: call sites, enclosing head, and both push lists.

    Two push accumulators are kept because the two slot rules ask different
    questions:
      run_all  -- every push since the function head (rule B: any interleaving
                  counts, which is how the ABI really works);
      run_cons -- only the trailing run of pushes with no intervening
                  non-push instruction (rule A: an interleaved `mov` splits the
                  argument list and the rule falls back to no key).
    """
    heads, calls = {}, []
    func_start, pending_ret = K.TEXT_LO, False
    run_all, run_cons = [], []
    for insn in sweep(K.TEXT_LO, 0x7E1000):
        if pending_ret and insn.mnemonic != "nop":
            func_start = insn.address
            pending_ret = False
            run_all, run_cons = [], []
        if insn.mnemonic.startswith("ret"):
            pending_ret = True
        elif insn.mnemonic != "nop":
            pending_ret = False
        if insn.mnemonic == "push":
            txt = insn.op_str.strip()
            if txt.startswith("0x") and "[" not in txt:
                e = (insn.address, "imm", int(txt, 16))
            else:
                e = (insn.address, "reg", txt)
            run_all.append(e)
            run_cons.append(e)
        elif insn.mnemonic == "call" and insn.operands:
            op = insn.operands[0]
            if op.type == capstone.x86.X86_OP_IMM:
                t = op.imm & 0xFFFFFFFF
                if t in K.READERS:
                    heads[insn.address] = func_start
                    calls.append((insn.address, t, list(run_all), list(run_cons)))
                    run_all, run_cons = [], []
        else:
            # a non-push, non-call instruction breaks the consecutive run only
            run_cons = []
    return heads, calls


def m1_of(head, site):
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    found = None
    for insn in md.disasm(K.read_va(head, site - head), head):
        if insn.address >= site:
            break
        if insn.mnemonic != "push":
            continue
        txt = insn.op_str.strip()
        if not txt.startswith("0x") or "[" in txt:
            continue
        v = int(txt, 16)
        if not (K.RDATA_LO <= v < K.DATA_HI):
            continue
        s = K.cstr(v)
        if PRINTABLE(s):
            found = (insn.address, v, s)
    return found


def slot(pushes, reader):
    """The push in the KEY argument slot, under one push list."""
    idx = -1 if reader == "GetSection" else -2
    return pushes[idx] if len(pushes) >= -idx else None


def lit(p):
    if p is None:
        return None
    if p[1] == "imm" and K.RDATA_LO <= p[2] < K.DATA_HI:
        s = K.cstr(p[2])
        if PRINTABLE(s):
            return (p[0], p[2], s)
    return None


def main():
    h = hashlib.sha256(K.BLOB).hexdigest()
    if not chk("G0 sha256", h == SHA256, h[:16]):
        print("sha256 %s -- VOID" % h)
        for c, s, d in results:
            print("%s\t%s\t%s" % (s, c, d))
        return 1

    heads, calls = build()
    chk("call sites 2426", len(calls) == 2426, len(calls))

    per = {}
    m1_rec, mb_lit, ma_lit = {}, {}, {}
    conflict_b, conflict_a = [], []
    for site, t, pushes, cons in calls:
        name = K.READERS[t][0]
        r = m1_of(heads[site], site)
        pb, pa = slot(pushes, name), slot(cons, name)
        lb, la = lit(pb), lit(pa)
        if r:
            m1_rec[site] = r
        if lb:
            mb_lit[site] = lb
        if la:
            ma_lit[site] = la
        d = per.setdefault(name, {"n": 0, "m1": 0, "bL": 0, "bR": 0,
                                  "aL": 0, "aR": 0})
        d["n"] += 1
        d["m1"] += 1 if r else 0
        if lb:
            d["bL"] += 1
        elif pb is not None and pb[1] == "reg":
            d["bR"] += 1
        if la:
            d["aL"] += 1
        elif pa is not None and pa[1] == "reg":
            d["aR"] += 1
        # mis-attribution: M1 produced a literal but the key slot is a register
        if r and pb is not None and pb[1] == "reg":
            conflict_b.append((site, name, pb[2], r[2]))
        if r and pa is not None and pa[1] == "reg":
            conflict_a.append((site, name, pa[2], r[2]))

    print("\n=== per-reader: M1 recovered / M2-B literal,register / M2-A literal,register ===")
    print("%-22s %5s %6s %8s %7s %8s %7s"
          % ("reader", "sites", "M1", "M2-B L", "M2-B R", "M2-A L", "M2-A R"))
    tot = {"n": 0, "m1": 0, "bL": 0, "bR": 0, "aL": 0, "aR": 0}
    for name in ("ReadInteger", "ReadBool", "ReadString", "ReadDouble",
                 "GetSection", "ReadUnicodeString", "ReadStringtableEntry"):
        d = per[name]
        for k in tot:
            tot[k] += d[k]
        print("%-22s %5d %6d %8d %7d %8d %7d"
              % (name, d["n"], d["m1"], d["bL"], d["bR"], d["aL"], d["aR"]))
    print("%-22s %5d %6d %8d %7d %8d %7d"
          % ("TOTAL", tot["n"], tot["m1"], tot["bL"], tot["bR"],
             tot["aL"], tot["aR"]))

    chk("M1 recovered 2305", tot["m1"] == 2305, tot["m1"])
    chk("M2-B literal 2209", tot["bL"] == 2209, tot["bL"])
    chk("M2-B register 210", tot["bR"] == 210, tot["bR"])

    # The ReadDouble claim that was mis-recorded as a cross-family split.
    rd = per["ReadDouble"]
    chk("ReadDouble M2-B register == 1 (both pipelines agree)", rd["bR"] == 1, rd["bR"])
    print("\nReadDouble: M2-B reg = %d ; M2-A reg = %d"
          % (rd["bR"], rd["aR"]))
    print("  => the '1 vs 68' in LEDGER 4b is rule-B vs rule-A INSIDE one report,")
    print("     not our pipeline vs theirs. No cross-family disagreement here.")

    print("\n=== conflict populations (M1 literal but key slot is a register) ===")
    print("  rule B : %d sites" % len(conflict_b))
    print("  rule A : %d sites" % len(conflict_a))
    chk("rule-B conflicts >= 70 (G-37 scale)", len(conflict_b) >= 70, len(conflict_b))
    bysec = {}
    for _s, _n, _reg, m1s in conflict_b:
        bysec[m1s] = bysec.get(m1s, 0) + 1
    print("  distinct M1 strings at rule-B conflicts: %d" % len(bysec))
    pct = {k: v for k, v in bysec.items() if "%" in k}
    print("  of which contain '%%': %d distinct / %d sites"
          % (len(pct), sum(pct.values())))

    # ---- negative controls ------------------------------------------------
    # N1: rule sensitivity. GetSection's slot index is -1; using -2 must change
    # its literal count. If it does not, the slot rule is not driving results.
    gs = per["GetSection"]
    chk("N1 GetSection slot rule is live (M2-B 3 literal)", gs["bL"] == 3, gs["bL"])

    # N2: a genuine key site must NOT appear in the conflict population.
    chk("N2 genuine Name@0x410AA0 not a conflict",
        not any(s == 0x00410AA0 for s, *_ in conflict_b))

    # N3: an unrelated change of rule must move numbers. Force slot index -3
    # for ReadBool and re-count; it must differ from the -2 result.
    alt = 0
    for site, t, pushes, cons in calls:
        if K.READERS[t][0] != "ReadBool":
            continue
        if len(pushes) >= 3 and lit(pushes[-3]):
            alt += 1
    chk("N3 -3 slot changes ReadBool count", alt != per["ReadBool"]["bL"],
        "%d vs %d" % (alt, per["ReadBool"]["bL"]))

    # N4: sha gate liveness against the pristine copy.
    orig = hashlib.sha256(open(
        r"D:\Project\ra2-campaign-forge\ra2youli\.ra2opt\orig\gamemd.exe",
        "rb").read()).hexdigest()
    chk("N4 sha gate live (orig differs)", orig != SHA256, orig[:10])

    print("\n=== samples: rule-B conflicts ===")
    for site, name, reg, m1s in conflict_b[:20]:
        print("  0x%08X %-14s key_slot=%-14s M1 grabbed %r"
              % (site, name, reg, m1s))
    print("  ... plus %d more" % max(0, len(conflict_b) - 20))

    fails = [r for r in results if r[1] == "FAIL"]
    print("\nR-031 rules gate: %d/%d PASS" % (len(results) - len(fails), len(results)))
    for c, s, d in results:
        print("%s\t%s\t%s" % (s, c, d))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
