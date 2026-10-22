# -*- coding: utf-8 -*-
"""R-031 finalisation: find WHY M1 recovers 2,305 and the independent GLM
sweep recovers 2,275.

The two pipelines share the string region [0x7E1000, 0xB79BE4) and the
"printable ASCII, len >= 2" filter, so a 30-site gap cannot come from the
literal predicate. It has to come from where the backward scan STARTS: the
enclosing function's first instruction. `dump_ini_keyindex.function_start`
treats only `nop` (0x90) as prologue padding, so a run of `int3` (0xCC) or
`add [eax],al` (0x00) between two functions makes it start the scan too early
and adopt pushes that belong to the preceding function.

This tool measures that directly: it recomputes M1 under three padding sets and
reports the site-level diff, plus dumps the disputed sites' prologue bytes so
the reading is auditable rather than asserted.

Read-only on the exe. Run:
    python re_atlas/tools/r031_m1_window_diag.py
"""

import hashlib
import os
import sys

import capstone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dump_ini_keyindex as K  # noqa: E402  module main-guard keeps it import-safe
from text_sweep import sweep  # noqa: E402

SHA256 = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"

PAD_SETS = {
    "A: nop only (current)": (0x90,),
    "B: nop+int3+null (GLM)": (0x90, 0xCC, 0x00),
}


def build_func_map(pad_bytes):
    """call_va -> enclosing function start, under a given padding set.

    Same shape as dump_ini_keyindex.call_sites(), but the "is this byte padding
    or code" decision is parameterised. A byte is padding when it is one of
    pad_bytes; anything else after a ret begins a function. Multi-byte nops
    (0x8D / 0x66 / 0x0F prefixed) still decode as code, which is correct: they
    are real instructions and must be skipped by the caller, not by the map.
    """
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    func_of = {}
    func_start = K.TEXT_LO
    pending_ret = False
    out = []
    for insn in sweep(K.TEXT_LO, 0x7E1000):
        if pending_ret and insn.bytes[0] not in pad_bytes:
            func_start = insn.address
            pending_ret = False
        if insn.mnemonic.startswith("ret"):
            pending_ret = True
        elif insn.bytes[0] not in pad_bytes:
            pending_ret = False
        if insn.mnemonic != "call" or not insn.operands:
            continue
        op = insn.operands[0]
        if op.type != capstone.x86.X86_OP_IMM:
            continue
        if (op.imm & 0xFFFFFFFF) in K.READERS:
            func_of[insn.address] = func_start
            out.append(insn.address)
    return func_of, out


def m1_under(func_of, call_va):
    """The key_before() rule, but starting from a supplied function origin."""
    origin = func_of.get(call_va, K.TEXT_LO)
    if call_va <= origin:
        return None
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    found = None
    for insn in md.disasm(K.read_va(origin, call_va - origin), origin):
        if insn.address >= call_va:
            break
        if insn.mnemonic != "push":
            continue
        txt = insn.op_str.strip()
        if not txt.startswith("0x") or "[" in txt:
            continue
        val = int(txt, 16)
        if not (K.RDATA_LO <= val < K.DATA_HI):
            continue
        s = K.cstr(val)
        if len(s) < 2 or not all(0x20 < ord(ch) < 0x7F for ch in s):
            continue
        found = (insn.address, val, s)
    return found


def main():
    h = hashlib.sha256(K.BLOB).hexdigest()
    print("sha256 %s  %s" % (h[:16], "OK" if h == SHA256 else "MISMATCH -- VOID"))
    if h != SHA256:
        return 1

    results = {}
    sites_by_variant = {}
    for label, pads in PAD_SETS.items():
        func_of, calls = build_func_map(pads)
        rec = {}
        for cv in calls:
            r = m1_under(func_of, cv)
            if r:
                rec[cv] = r
        distinct = {r[2] for r in rec.values()}
        multi = {}
        for cv, r in rec.items():
            multi[r[2]] = multi.get(r[2], 0) + 1
        multi = {k for k, n in multi.items() if n > 1}
        pct_sites = sum(1 for r in rec.values() if "%" in r[2])
        pct_keys = {r[2] for r in rec.values() if "%" in r[2]}
        results[label] = (len(rec), len(distinct), len(multi), pct_sites, len(pct_keys))
        sites_by_variant[label] = rec
        print("\n%-26s recovered %d  distinct %d  multi %d  %%-sites %d  %%-keys %d"
              % (label, len(rec), len(distinct), len(multi), pct_sites, len(pct_keys)))

    la = "A: nop only (current)"
    lb = "B: nop+int3+null (GLM)"
    ra, rb = sites_by_variant[la], sites_by_variant[lb]
    only_a = sorted(set(ra) - set(rb))
    only_b = sorted(set(rb) - set(ra))
    changed = sorted(cv for cv in set(ra) & set(rb) if ra[cv][2] != rb[cv][2])
    print("\n=== site-level diff A vs B ===")
    print("  A has, B lost : %d" % len(only_a))
    print("  B has, A lost : %d" % len(only_b))
    print("  same site, different literal : %d" % len(changed))

    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    for cv in only_a[:40]:
        fsa, fsb = K.function_start(cv), None
        fa, _ = build_func_map(PAD_SETS[la])
        fb, _ = build_func_map(PAD_SETS[lb])
        fsa, fsb = fa.get(cv), fb.get(cv)
        print("  0x%08X  A_key=%-28r A_fn=0x%08X  B_fn=0x%08X"
              % (cv, ra[cv][2], fsa or 0, fsb or 0))
        if fsb:
            gap = K.read_va(fsb, 0x10)
            print("      B fn head bytes: %s" % gap.hex(" "))
    for cv in changed[:20]:
        print("  0x%08X  A=%-28r -> B=%r" % (cv, ra[cv][2], rb[cv][2]))

    # Adjudication: which variant's function start is a real boundary?
    print("\n=== boundary sanity on the disputed sites ===")
    fb, _ = build_func_map(PAD_SETS[lb])
    bad = 0
    for cv in only_a:
        fn = fb.get(cv)
        if fn is None:
            continue
        b = K.read_va(fn, 1)
        if not b or b[0] in (0x90, 0xCC, 0x00):
            bad += 1
            print("  0x%08X B_fn 0x%08X starts on padding byte 0x%02X"
                  % (cv, fn, b[0] if b else -1))
    print("  B function starts landing on a padding byte: %d" % bad)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
