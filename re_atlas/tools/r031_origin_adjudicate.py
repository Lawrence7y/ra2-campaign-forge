# -*- coding: utf-8 -*-
"""R-031 finalisation (step 2b): adjudicate the 2,305 vs 2,275 gap, correctly.

Step 1 ruled out the padding-byte hypothesis (nop-only and nop+int3+null give
byte-identical totals). Step 2's first cut was WRONG and is kept only as a
lesson: it walked back to the nearest `C3`/`C2` byte without validating it, so
it "found" rets inside instruction immediates (e.g. 0x41CC5C, where the byte
before the site is the tail of `call 0x5295F0`'s rel32). That inflated the
delta to 522 and proved nothing.

The independent sweep's rule, implemented faithfully here:

  * candidate p: a `C3` / `CB` / `C2 xx` / `CA xx` byte anywhere in
    [site-0x3000, site);
  * boundary b = p + retlen, then skip bytes in {0x90, 0xCC, 0x00};
  * forward-decode from b: the sequence must include an instruction AT the site
    that is `call <reader>`. If it does not, the candidate is fake (it was a
    byte inside a larger instruction) and is rejected;
  * take the NEAREST accepted candidate (largest p).

Our sweeper instead uses the enclosing function's true head from a forward pass.
The two differ when a function contains an internal `ret` that is followed by
code which decodes cleanly to the next call: the backward rule then starts the
argument window after that internal ret and cannot see pushes issued earlier.

Read-only on the exe. Run:
    python re_atlas/tools/r031_origin_adjudicate.py
"""

import hashlib
import os
import sys

import capstone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dump_ini_keyindex as K  # noqa: E402
from text_sweep import sweep  # noqa: E402

SHA256 = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
SKIP = (0x90, 0xCC, 0x00)


def sweep_func_map():
    """call_va -> enclosing function head from a forward pass (our rule)."""
    func_of, calls = {}, []
    func_start, pending_ret = K.TEXT_LO, False
    for insn in sweep(K.TEXT_LO, 0x7E1000):
        if pending_ret and insn.mnemonic != "nop":
            func_start = insn.address
            pending_ret = False
        if insn.mnemonic.startswith("ret"):
            pending_ret = True
        elif insn.mnemonic != "nop":
            pending_ret = False
        if insn.mnemonic != "call" or not insn.operands:
            continue
        op = insn.operands[0]
        if op.type == capstone.x86.X86_OP_IMM and (op.imm & 0xFFFFFFFF) in K.READERS:
            func_of[insn.address] = func_start
            calls.append(insn.address)
    return func_of, calls


def decode_lands_on(origin, site, limit=0x400):
    """Does a forward decode from `origin` reach `site` as call <reader>?"""
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    for insn in md.disasm(K.read_va(origin, limit), origin):
        if insn.address == site:
            if insn.mnemonic != "call" or not insn.operands:
                return False
            op = insn.operands[0]
            return (op.type == capstone.x86.X86_OP_IMM
                    and (op.imm & 0xFFFFFFFF) in K.READERS)
        if insn.address > site:
            return False
    return False


def retwalk_origin(site, limit=0x3000):
    """Nearest VALIDATED ret boundary before `site` (the independent rule)."""
    lo = max(K.TEXT_LO, site - limit)
    blob = K.read_va(lo, site - lo)
    for i in range(len(blob) - 1, -1, -1):
        b = blob[i]
        if b in (0xC3, 0xCB):
            nxt = lo + i + 1
        elif b in (0xC2, 0xCA):
            nxt = lo + i + 3
        else:
            continue
        if nxt >= site:
            continue
        j = nxt
        while j < site:
            bb = K.read_va(j, 1)
            if not bb or bb[0] not in SKIP:
                break
            j += 1
        if j >= site:
            continue
        if decode_lands_on(j, site):
            return j
    return None


def m1_from(site, origin):
    if origin is None or site <= origin:
        return None
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    found = None
    for insn in md.disasm(K.read_va(origin, site - origin), origin):
        if insn.address >= site:
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


def summarise(name, rec):
    distinct = {r[2] for r in rec.values()}
    multi = {}
    for r in rec.values():
        multi[r[2]] = multi.get(r[2], 0) + 1
    multi = {k for k, n in multi.items() if n > 1}
    pct_sites = sum(1 for r in rec.values() if "%" in r[2])
    pct_keys = {r[2] for r in rec.values() if "%" in r[2]}
    print("%-22s sites %4d  distinct %4d  multi %3d  %%-sites %2d  %%-keys %2d"
          % (name, len(rec), len(distinct), len(multi), pct_sites, len(pct_keys)))
    return len(rec), len(distinct), len(multi), pct_sites, len(pct_keys)

def main():
    h = hashlib.sha256(K.BLOB).hexdigest()
    ok = h == SHA256
    print("sha256 %s  %s" % (h[:16], "OK" if ok else "MISMATCH -- VOID"))
    if not ok:
        return 1

    smap, calls = sweep_func_map()
    print("call sites: %d\n" % len(calls))

    rec_sweep, rec_ret = {}, {}
    unresolved = 0
    origins_differ = 0
    for cv in calls:
        a = m1_from(cv, smap.get(cv))
        if a:
            rec_sweep[cv] = a
        rw = retwalk_origin(cv)
        if rw is None:
            unresolved += 1
        elif rw != smap.get(cv):
            origins_differ += 1
        b = m1_from(cv, rw)
        if b:
            rec_ret[cv] = b

    print("retwalk could not anchor a site : %d" % unresolved)
    print("origins differ from sweep head  : %d\n" % origins_differ)

    print("=== totals ===")
    summarise("sweep (our rule)", rec_sweep)
    summarise("retwalk (independent)", rec_ret)

    only_sweep = sorted(set(rec_sweep) - set(rec_ret))
    only_ret = sorted(set(rec_ret) - set(rec_sweep))
    changed = sorted(cv for cv in set(rec_sweep) & set(rec_ret)
                     if rec_sweep[cv][2] != rec_ret[cv][2])
    print("\nsites only sweep recovers : %d" % len(only_sweep))
    print("sites only retwalk recovers: %d" % len(only_ret))
    print("same site, different literal: %d" % len(changed))

    # For the sweep-only sites: is the recovered push an argument of THIS call,
    # i.e. does it sit after the retwalk origin? If it sits before, the shorter
    # window simply did not see it -- and whether it belongs is decidable by
    # whether the intervening code clobbers the stack slot.
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    print("\n=== sweep-only sites: where the push sits ===")
    n_before = 0
    for cv in only_sweep:
        push_site = rec_sweep[cv][0]
        rw = retwalk_origin(cv)
        if rw is not None and push_site < rw:
            n_before += 1
    print("  push before the retwalk origin: %d / %d"
          % (n_before, len(only_sweep)))
    print("  (these are the sites the two pipelines disagree about)\n")

    print("=== sample: sweep-only, push sits before the shorter window ===")
    shown = 0
    for cv in only_sweep:
        if shown >= 12:
            break
        ps, _v, txt = rec_sweep[cv]
        rw = retwalk_origin(cv)
        if rw is None or ps >= rw:
            continue
        # Is the pushed literal still reachable across the intervening code?
        between = list(md.disasm(K.read_va(rw, cv - rw), rw))[:3]
        bt = " | ".join("%s %s" % (i.mnemonic, i.op_str) for i in between)
        print("  0x%08X key=%-22r push@0x%08X  shorter-window head: %s"
              % (cv, txt, ps, bt))
        shown += 1

    print("\n=== sample: same site, different literal ===")
    for cv in changed[:10]:
        print("  0x%08X  sweep=%-22r  retwalk=%r"
              % (cv, rec_sweep[cv][2], rec_ret[cv][2]))

    print("\n=== verdict inputs ===")
    print("  sweep %d vs retwalk %d => delta %d"
          % (len(rec_sweep), len(rec_ret), len(rec_sweep) - len(rec_ret)))
    print("  independent reported 2275 => our-minus-independent %d"
          % (len(rec_sweep) - 2275))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
