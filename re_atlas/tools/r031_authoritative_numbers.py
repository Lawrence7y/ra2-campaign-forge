# -*- coding: utf-8 -*-
"""R-031 finalisation: authoritative numbers for kb/30 section 12.

Why this replaces the M1 headline figures
----------------------------------------
§12 currently publishes M1 numbers: 2,305 "recovered keys", 1,893 "distinct
keys", 164 "keys read more than once", 21 "%-keys / 34 %-sites". M1 answers
"is there a printable string-literal push somewhere before this call". That is
NOT the same question as "what key does this call pass", and R-031 / G-37
already documented that M1 mis-attributes.

This tool answers the key question directly and verifies it twice:

  rule B  positional: the push occupying the KEY argument slot, counted over
          every push since the function head;
  rule C  stack model: same slot, but located by tracking esp, so a push whose
          bytes were reclaimed by `pop` / `add esp,N` / `leave` / `mov esp,X`
          cannot masquerade as a live argument.

B and C agree at every one of the 2,426 sites, which is the point: two
independent formulations of the ABI produce the same answer, so the figures
below are not an artifact of one heuristic.

Then the M1 population is split by WHY it differs from the key slot, because
the two causes have different consequences for a compiler:
  (1) key slot holds a register  -> M1's literal is a nearby template or an
      older consumed string; the key is genuinely runtime-built;
  (2) key slot holds a DIFFERENT literal -> M1 grabbed the section name (or a
      filename) that sits closer to the call than the key does.

Read-only on the exe. Deterministic. Run:
    python re_atlas/tools/r031_authoritative_numbers.py
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


def printable(s):
    return len(s) >= 2 and all(0x20 < ord(c) < 0x7F for c in s)


def as_literal(entry):
    if entry is None:
        return None
    site, kind, val = entry[0], entry[1], entry[2]
    if kind != "imm" or not (K.RDATA_LO <= val < K.DATA_HI):
        return None
    s = K.cstr(val)
    return (site, val, s) if printable(s) else None


def run():
    """One forward pass producing, per call site, both slot entries and M1."""
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    all_since_head = []      # rule B
    live = []                # rule C: (site, kind, value, depth_after)
    depth = 0
    head = K.TEXT_LO
    pending_ret = False
    out = []

    # M1 needs a decode from the head; cache per head to avoid re-walking.
    m1_cache = {}

    def m1(head_va, site):
        key = (head_va, site)
        if key in m1_cache:
            return m1_cache[key]
        found = None
        for insn in md.disasm(K.read_va(head_va, site - head_va), head_va):
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
            if printable(s):
                found = (insn.address, v, s)
        if len(m1_cache) < 3000:
            m1_cache[key] = found
        return found

    for insn in sweep(K.TEXT_LO, 0x7E1000):
        m = insn.mnemonic
        if pending_ret and m != "nop":
            head = insn.address
            pending_ret = False
            all_since_head, live, depth = [], [], 0
        if m.startswith("ret"):
            pending_ret = True
            all_since_head, live, depth = [], [], 0
        elif m != "nop":
            pending_ret = False

        if m == "push":
            txt = insn.op_str.strip()
            if txt.startswith("0x") and "[" not in txt:
                e = (insn.address, "imm", int(txt, 16))
            else:
                e = (insn.address, "reg", txt)
            all_since_head.append(e)
            depth += 4
            live.append((e[0], e[1], e[2], depth))
            continue

        if m == "pop":
            depth = max(0, depth - 4)
            live = [p for p in live if p[3] <= depth]
            continue

        if m in ("add", "sub") and len(insn.operands) >= 2:
            o = insn.operands
            if o[0].type == capstone.x86.X86_OP_REG and \
                    insn.reg_name(o[0].reg) == "esp" and \
                    o[1].type == capstone.x86.X86_OP_IMM:
                n = o[1].imm & 0xFFFFFFFF
                depth = max(0, depth - n if m == "add" else depth + n)
                live = [p for p in live if p[3] <= depth]
                continue

        if m in ("leave", "mov", "lea") and \
                insn.op_str.split(",")[0].strip() == "esp":
            depth = 0
            live = []
            all_since_head = []
            continue

        if m == "call" and insn.operands:
            op = insn.operands[0]
            if op.type == capstone.x86.X86_OP_IMM:
                t = op.imm & 0xFFFFFFFF
                if t in K.READERS:
                    name = K.READERS[t][0]
                    idx = -1 if name == "GetSection" else -2
                    eb = all_since_head[idx] if len(all_since_head) >= -idx else None
                    ec = live[idx] if len(live) >= -idx else None
                    out.append({
                        "site": insn.address, "reader": name, "head": head,
                        "B": eb, "C": ec, "M1": m1(head, insn.address),
                    })
                    all_since_head, live, depth = [], [], 0
                    continue
            continue
    return out


def main():
    h = hashlib.sha256(K.BLOB).hexdigest()
    if not chk("G0 sha256", h == SHA256, h[:16]):
        print("sha256 %s -- VOID" % h)
        return 1

    sites = run()
    chk("call sites == 2426", len(sites) == 2426, len(sites))

    per = {}
    for s in sites:
        d = per.setdefault(s["reader"], {"n": 0, "L": 0, "R": 0, "N": 0})
        d["n"] += 1
        c = as_literal(s["C"])
        if c:
            d["L"] += 1
        elif s["C"] is not None and s["C"][1] == "reg":
            d["R"] += 1
        else:
            d["N"] += 1

    print("=== §12.1  per-reader call sites and KEY-SLOT nature ===")
    print("%-22s %5s %6s %7s %6s" % ("reader", "sites", "literal", "register", "none"))
    order = ("ReadInteger", "ReadBool", "ReadString", "ReadDouble",
             "GetSection", "ReadUnicodeString", "ReadStringtableEntry")
    tot = {"n": 0, "L": 0, "R": 0, "N": 0}
    for n in order:
        d = per[n]
        for k in tot:
            tot[k] += d[k]
        print("%-22s %5d %6d %7d %6d" % (n, d["n"], d["L"], d["R"], d["N"]))
    print("%-22s %5d %6d %7d %6d" % ("TOTAL", tot["n"], tot["L"], tot["R"], tot["N"]))
    chk("per-reader sites 757/651/650/306/54/5/3",
        [per[n]["n"] for n in order] == [757, 651, 650, 306, 54, 5, 3],
        [per[n]["n"] for n in order])
    chk("key-slot literal 2209", tot["L"] == 2209, tot["L"])
    chk("key-slot register 210", tot["R"] == 210, tot["R"])
    chk("key-slot empty 7", tot["N"] == 7, tot["N"])
    chk("2209 + 210 + 7 == 2426", tot["L"] + tot["R"] + tot["N"] == 2426)

    # ---- rule B vs rule C agreement: the internal double-check -------------
    diff = [s for s in sites
            if (as_literal(s["B"]) or (None,))[0:1] != (as_literal(s["C"]) or (None,))[0:1]]
    chk("rule B == rule C at every site", len(diff) == 0, len(diff))

    # ---- literal key population -------------------------------------------
    lit_sites = [s for s in sites if as_literal(s["C"])]
    distinct = {}
    for s in lit_sites:
        distinct.setdefault(as_literal(s["C"])[2], []).append(s["site"])
    multi = {k: v for k, v in distinct.items() if len(v) > 1}
    print("\n=== §12.2  literal-key population ===")
    print("  sites with a literal key : %d" % len(lit_sites))
    print("  distinct literal keys    : %d" % len(distinct))
    print("  read at more than one site: %d" % len(multi))

    # ---- the % census: the decisive §12.3 correction ----------------------
    pct_keys = {k: v for k, v in distinct.items() if "%" in k}
    print("\n=== §12.3  keys containing '%%' ===")
    print("  distinct literal keys with '%%' : %d" % len(pct_keys))
    print("  sites whose literal key has '%%': %d"
          % sum(len(v) for v in pct_keys.values()))
    chk("no literal KEY contains '%' (all are M1 templates)",
        len(pct_keys) == 0, sorted(pct_keys))

    # ---- M1 vs key slot: causal split -------------------------------------
    # Case (1) is further split: the slot may hold a register, or hold nothing
    # at all (7 sites engine-wide). Both mean "M1's literal is not this call's
    # key", but only the register sub-population is the runtime-built-key case.
    reg_conf, none_conf, lit_conf = [], [], []
    for s in sites:
        m1r, c = s["M1"], as_literal(s["C"])
        if not m1r:
            continue
        if c and c[1] == m1r[1]:
            continue
        if c is not None:
            lit_conf.append((s, c))
        elif s["C"] is not None and s["C"][1] == "reg":
            reg_conf.append(s)
        else:
            none_conf.append(s)
    print("\n=== M1 vs key slot: %d of %d sites disagree ==="
          % (len(reg_conf) + len(none_conf) + len(lit_conf), len(sites)))
    print("  (1a) key slot is a register/buffer : %d sites" % len(reg_conf))
    print("  (1b) key slot holds nothing        : %d sites" % len(none_conf))
    print("  (2)  key slot is a DIFFERENT literal: %d sites" % len(lit_conf))
    chk("conflict total 340",
        len(reg_conf) + len(none_conf) + len(lit_conf) == 340,
        len(reg_conf) + len(none_conf) + len(lit_conf))
    chk("register-slot conflicts 91", len(reg_conf) == 91, len(reg_conf))
    chk("empty-slot conflicts 5", len(none_conf) == 5, len(none_conf))

    m1_pct = {}
    for s in reg_conf:
        m1_pct[s["M1"][2]] = m1_pct.get(s["M1"][2], 0) + 1
    pct_with = {k: v for k, v in m1_pct.items() if "%" in k}
    print("\n  M1 strings at register-slot conflicts: %d distinct" % len(m1_pct))
    print("  ...of which contain '%%': %d distinct / %d sites"
          % (len(pct_with), sum(pct_with.values())))
    chk("M1 %-templates 21 distinct / 34 sites",
        len(pct_with) == 21 and sum(pct_with.values()) == 34,
        (len(pct_with), sum(pct_with.values())))

    # (2) population: is the grabbed literal actually a section name?
    grabbed = {}
    for s, c in lit_conf:
        grabbed[s["M1"][2]] = grabbed.get(s["M1"][2], 0) + 1
    print("\n  top strings M1 grabbed instead of the key (case 2):")
    for k, v in sorted(grabbed.items(), key=lambda kv: -kv[1])[:12]:
        print("    %-24r %d" % (k, v))

    # ---- multi-read keys, for §12.4 ---------------------------------------
    print("\n=== §12.4  most-repeated literal keys ===")
    for k, v in sorted(multi.items(), key=lambda kv: -len(kv[1]))[:15]:
        print("    %-30r %3d sites" % (k, len(v)))

    # ---- controls ---------------------------------------------------------
    chk("N1 genuine Name@0x410AA0 is a literal key",
        any(s["site"] == 0x410AA0 and as_literal(s["C"])
            and as_literal(s["C"])[2] == "Name" for s in lit_sites))
    chk("N2 Scenario.CPP@0x686ED0 is NOT a literal key",
        not any(s["site"] == 0x686ED0 and as_literal(s["C"]) for s in sites))
    chk("N3 PowerUp template is a register-slot conflict",
        any(s["site"] == 0x4647ED and s["M1"][2] == "PowerUp%01dYSort"
            for s in reg_conf))
    orig = hashlib.sha256(open(
        r"D:\Project\ra2-campaign-forge\ra2youli\.ra2opt\orig\gamemd.exe",
        "rb").read()).hexdigest()
    chk("N4 sha gate live (orig differs)", orig != SHA256, orig[:10])

    fails = [r for r in results if r[1] == "FAIL"]
    print("\nR-031 authoritative gate: %d/%d PASS"
          % (len(results) - len(fails), len(results)))
    for c, st, d in results:
        print("%s\t%s\t%s" % (st, c, d))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
