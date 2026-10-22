# -*- coding: utf-8 -*-
"""R-031 finalisation: decisive test for the 2209 vs 2187 gap.

After `r031_esp_slot_adjudicate.py` showed the stack model and the positional
rule agree EXACTLY (2209 literal / 210 register / 7 imm-nonstring), the only
remaining disagreement with the independent sweep is 22 sites: their report has
`none` = 22, meaning "no push in the key slot", where we have a literal.

Both pipelines agree that a `ret` ends the argument window. So the 22 sites can
only differ if the two pipelines disagree about WHICH ret is the last one
before the site. We derive rets from decoded INSTRUCTION boundaries, so a `C3`
byte that is really the tail of a `push imm32` / `mov` immediate is invisible
to us. A byte-scan finds it, declares a new window start, and loses the key.

This tool counts exactly that population: sites where a raw C3/C2/CB/CA byte
sits between the function head and the call, on a byte offset that is NOT an
instruction boundary. If that count tracks the 22-site gap, the gap is
explained as a byte-scan artifact and our figure is the correct one.

Read-only on the exe. Run:
    python re_atlas/tools/r031_ret_boundary_test.py
"""

import hashlib
import os
import sys

import capstone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dump_ini_keyindex as K  # noqa: E402
from text_sweep import sweep  # noqa: E402

SHA256 = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
RET_BYTES = (0xC3, 0xC2, 0xCB, 0xCA)


def main():
    h = hashlib.sha256(K.BLOB).hexdigest()
    print("sha256 %s  %s" % (h[:16], "OK" if h == SHA256 else "MISMATCH -- VOID"))
    if h != SHA256:
        return 1

    func_start = K.TEXT_LO
    pending_ret = False
    run = []
    sites = []                      # (call, name, run_all, head)
    boundaries = set()              # instruction START addresses only
    insn_bytes = {}

    for insn in sweep(K.TEXT_LO, 0x7E1000):
        if pending_ret and insn.mnemonic != "nop":
            func_start = insn.address
            pending_ret = False
            run = []
        if insn.mnemonic.startswith("ret"):
            pending_ret = True
        elif insn.mnemonic != "nop":
            pending_ret = False

        boundaries.add(insn.address)
        insn_bytes[insn.address] = (insn.mnemonic, insn.op_str, insn.size)

        if insn.mnemonic == "push":
            txt = insn.op_str.strip()
            if txt.startswith("0x") and "[" not in txt:
                run.append((insn.address, "imm", int(txt, 16)))
            else:
                run.append((insn.address, "reg", txt))
        elif insn.mnemonic == "call" and insn.operands:
            op = insn.operands[0]
            if op.type == capstone.x86.X86_OP_IMM and (op.imm & 0xFFFFFFFF) in K.READERS:
                sites.append((insn.address, K.READERS[op.imm & 0xFFFFFFFF][0],
                              list(run), func_start))
                run = []
        elif insn.mnemonic.startswith("ret"):
            run = []

    print("call sites: %d   instruction-boundary byte count: %d"
          % (len(sites), len(boundaries)))

    # A byte-scan sees a ret at every C3/C2/CB/CA byte. The ones that are NOT
    # instruction boundaries are the false rets that shorten a window.
    false_ret_sites = []
    for call, name, run_all, head in sites:
        idx = -1 if name == "GetSection" else -2
        if len(run_all) < -idx:
            continue
        blob = K.read_va(head, call - head)
        hits = []
        for i, b in enumerate(blob):
            if b in RET_BYTES and (head + i) not in boundaries:
                hits.append(head + i)
        if hits:
            false_ret_sites.append((call, name, len(run_all), head, hits))

    print("\n=== sites with a FALSE ret byte (not an instruction boundary) "
          "between head and call ===")
    total_hits = sum(len(h[4]) for h in false_ret_sites)
    print("  affected sites: %d   false ret bytes: %d"
          % (len(false_ret_sites), total_hits))

    per_name = {}
    for call, name, nrun, head, hits in false_ret_sites:
        per_name[name] = per_name.get(name, 0) + 1
    print("  by reader: %s" % per_name)

    print("\n=== would a byte-scan lose the key at these sites? ===")
    lost = 0
    shown = 0
    for call, name, nrun, head, hits in false_ret_sites:
        # simulate: window starts after the last false ret byte found
        last = max(hits)
        # count pushes strictly after that byte, at real boundaries
        n_after = 0
        for addr in sorted(insn_bytes):
            if last < addr < call:
                m, o, _s = insn_bytes[addr]
                if m == "push":
                    n_after += 1
        idx = 1 if name == "GetSection" else 2
        if n_after < idx:
            lost += 1
            if shown < 15:
                m, o, s = insn_bytes.get(last - (last - last), ("?", "?", 0))
                # report the instruction that CONTAINS the false ret byte
                containing = None
                for addr in sorted(insn_bytes):
                    a_m, a_o, a_s = insn_bytes[addr]
                    if addr <= last < addr + a_s:
                        containing = (addr, a_m, a_o)
                        break
                print("  0x%08X %-14s pushes_after_false_ret=%d (< %d)  "
                      "byte 0x%02X inside %s"
                      % (call, name, n_after, idx, K.read_va(last, 1)[0],
                         ("0x%08X `%s %s`" % containing) if containing
                         else "unknown"))
                shown += 1

    print("\n  sites where the shortened window loses the key slot: %d" % lost)
    print("\n=== verdict ===")
    print("  our literal count             : 2209")
    print("  independent literal count     : 2187")
    print("  gap                           : 22")
    print("  explained by false-ret window : %d" % lost)
    if abs(lost - 22) <= 3:
        print("  => the gap is a byte-scan artifact; our figure is authoritative.")
    else:
        print("  => NOT fully explained; record as unresolved pipeline divergence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
