# -*- coding: utf-8 -*-
"""
T5 guards adversarial verification for gamemd.exe (RA2: Yuri's Revenge).

Re-derives the call-site lists for six routines and classifies each site
guarded/unguarded, then attacks the claim table.

Verification methodology (deliberate; see report.md):
  * ONE authoritative linear sweep of .text with skipdata=True. Every claim
    "is this byte an instruction" is answered by membership in the sweep.
  * Raw-byte scans for E8/E9 rel32 and FF /2 find candidates cheaply; each is
    CROSS-CHECKED against the sweep. Candidates that are not instruction
    starts are reported as SPURIOUS and are never patched.
  * NEVER decode from site-16 or any derived offset. (A first version of this
    script did so inside its sample printer and produced visibly garbled
    disassembly -- the trap in the task brief is real and was hit and fixed.)
  * "guarded" is defined narrowly below and anything half-way is AMBIGUOUS,
    never silently counted as guarded.

Outputs (in OUTDIR): call_sites.tsv, diff_vs_claim.txt, samples.txt,
run_log.txt. Exit 0 on success.
"""
import bisect
import collections
import hashlib
import os
import sys

import capstone
import pefile

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUTDIR = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W135_ds\T5_guards"
EXPECT_SHA = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"

TARGETS = [0x724730, 0x724580, 0x7241A0, 0x724520, 0x724530, 0x724540]
CLAIM = {0x724730: 28, 0x724580: 18, 0x7241A0: 1,
         0x724520: 1, 0x724530: 1, 0x724540: 1}
CLAIM_TOTAL = 50
CLAIM_SITES_724730 = 30

X = capstone.x86
_md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
_md.detail = True
_md.skipdata = True


# --------------------------------------------------------------------- image
def load():
    data = open(EXE, "rb").read()
    sha = hashlib.sha256(data).hexdigest().upper()
    pe = pefile.PE(data=data, fast_load=True)
    ib = pe.OPTIONAL_HEADER.ImageBase
    secs = []
    for s in pe.sections:
        nm = s.Name.rstrip(b"\x00").decode(errors="replace")
        secs.append((nm, ib + s.VirtualAddress, s.Misc_VirtualSize,
                     s.PointerToRawData, s.SizeOfRawData))
    return data, sha, ib, secs


class Image:
    def __init__(self, data, ib, secs):
        self.data, self.ib, self.secs = data, ib, secs
        self.by_name = {s[0]: s for s in secs}

    def sec_of_va(self, va):
        for nm, sva, vs, ro, rs in self.secs:
            if sva <= va < sva + vs:
                return nm
        return None

    def va2off(self, va):
        for nm, sva, vs, ro, rs in self.secs:
            if sva <= va < sva + vs:
                d = va - sva
                if d < rs:
                    return ro + d
        return None

    def off2va(self, off):
        for nm, sva, vs, ro, rs in self.secs:
            if ro <= off < ro + rs:
                return sva + (off - ro)
        return None

    def read(self, va, n):
        o = self.va2off(va)
        return b"" if o is None else self.data[o:o + n]


class Sweep:
    """Authoritative linear sweep. instr_at: va -> insn; order: sorted vas."""

    def __init__(self, img, start, end):
        code = img.read(start, end - start)
        self.img = img
        self.start, self.end = start, end
        self.instr_at, self.order = {}, []
        self.skipped = 0
        for i in _md.disasm(code, start):
            if i.id == 0:
                self.skipped += 1
                continue
            self.instr_at[i.address] = i
            self.order.append(i.address)
        self.count = len(self.order)
        self.pos = {a: k for k, a in enumerate(self.order)}

    def at(self, va):
        return self.instr_at.get(va)

    def idx(self, va):
        return self.pos.get(va)


def scan_rel32(img, start, end, opcode):
    code = img.read(start, end - start)
    opb = bytes([opcode])
    out, idx, n = [], 0, len(code)
    while True:
        k = code.find(opb, idx)
        if k < 0 or k + 5 > n:
            break
        rel = int.from_bytes(code[k + 1:k + 5], "little", signed=True)
        site = start + k
        out.append((site, site + 5 + rel))
        idx = k + 1
    return out


# --------------------------------------------------------------- classifiers
ALIAS = {"al": "eax", "ah": "eax", "ax": "eax", "bl": "ebx", "bh": "ebx",
         "bx": "ebx", "cl": "ecx", "ch": "ecx", "cx": "ecx", "dl": "edx",
         "dh": "edx", "dx": "edx", "sil": "esi", "si": "esi", "dil": "edi",
         "di": "edi", "spl": "esp", "sp": "esp", "bpl": "ebp", "bp": "ebp",
         "eip": "eip"}


def reg_canon(n):
    if n is None:
        return None
    n = n.lower()
    return ALIAS.get(n, n)


FLAGS_SAFE = {X.X86_INS_NOP, X.X86_INS_LEA, X.X86_INS_MOV, X.X86_INS_MOVZX,
              X.X86_INS_MOVSX, X.X86_INS_MOVSXD, X.X86_INS_PUSH, X.X86_INS_POP,
              X.X86_INS_TEST, X.X86_INS_CMP}


def zero_test(ins):
    """(canon_reg, kind) if ins is a single-register zero test, else None."""
    ops = ins.operands
    if ins.id == X.X86_INS_TEST and len(ops) == 2:
        a, b = ops
        if a.type == X.X86_OP_REG and b.type == X.X86_OP_REG:
            if ins.reg_name(a.reg) == ins.reg_name(b.reg):
                return (reg_canon(ins.reg_name(a.reg)), "test r,r")
        if a.type == X.X86_OP_REG and b.type == X.X86_OP_IMM and b.imm == 0:
            return (reg_canon(ins.reg_name(a.reg)), "test r,0")
        return None
    if ins.id == X.X86_INS_CMP and len(ops) == 2:
        a, b = ops
        if a.type == X.X86_OP_REG and b.type == X.X86_OP_IMM and b.imm == 0:
            return (reg_canon(ins.reg_name(a.reg)), "cmp r,0")
        if a.type == X.X86_OP_IMM and a.imm == 0 and b.type == X.X86_OP_REG:
            return (reg_canon(ins.reg_name(b.reg)), "cmp 0,r")
        return None
    return None


def call_target(ins):
    if ins.id != X.X86_INS_CALL or not ins.operands:
        return None
    op = ins.operands[0]
    if op.type == X.X86_OP_IMM:
        return ("rel", op.imm)
    if op.type == X.X86_OP_REG:
        return ("reg", ins.reg_name(op.reg))
    if op.type == X.X86_OP_MEM:
        base = ins.reg_name(op.mem.base) if op.mem.base else None
        if base is None:
            return ("abs", op.mem.disp)
        return ("mem", "%s+0x%X" % (base, op.mem.disp & 0xFFFFFFFF))
    return ("?", None)


RULE = ("GUARDED iff within 12 insns before the call there is (T,J) with "
        "T=zero-test of GPR r, J=jz whose target == (call addr + call size), no "
        "write to r and no flag-clobber between T and J. Otherwise UNGUARDED, "
        "unless a near-miss exists -> AMBIGUOUS.")


def classify(sw, site):
    """Return (verdict, rule_text, meta)."""
    call = sw.at(site)
    if call is None or call.id != X.X86_INS_CALL:
        return ("NOT_AN_INSN", "not an instruction start in the linear sweep", None)
    call_end = site + call.size
    k = sw.idx(site)

    skips = []
    for step in range(1, 13):
        j = k - step
        if j < 0:
            break
        ins = sw.at(sw.order[j])
        if ins.mnemonic.startswith("j") and ins.operands and \
                ins.operands[0].type == X.X86_OP_IMM and ins.operands[0].imm == call_end:
            skips.append((sw.order[j], ins))
        if ins.id in (X.X86_INS_RET, X.X86_INS_JMP, X.X86_INS_CALL):
            break

    near = None
    for bva, bins in skips:
        jz = bins.id == X.X86_INS_JE
        bi = sw.idx(bva)
        for back in range(1, 13):
            j = bi - back
            if j < 1:
                break
            tva, tins = sw.order[j], sw.at(sw.order[j])
            zt = zero_test(tins)
            if zt is None:
                if tins.id in (X.X86_INS_RET, X.X86_INS_JMP, X.X86_INS_CALL):
                    break
                continue
            reg, kind = zt
            flags_ok = all(sw.at(sw.order[m]).id in FLAGS_SAFE for m in range(j + 1, bi))
            if not flags_ok:
                near = near or "zero-test %s@0x%X but flags clobbered before 0x%X" % (kind, tva, bva)
                break
            if not jz:
                near = near or "zero-test %s on %s@0x%X but branch 0x%X is %s" % (
                    kind, reg, tva, bva, bins.mnemonic)
                break
            return ("guarded",
                    "%s on %s at 0x%X; %s @0x%X skips to call_end 0x%X" % (
                        kind, reg, tva, bins.mnemonic, bva, call_end),
                    {"test": tva, "branch": bva, "reg": reg,
                     "branch_text": "%s %s" % (bins.mnemonic, bins.op_str)})
    if near:
        return ("AMBIGUOUS", near, None)
    return ("unguarded", "no zero-test+jz pair skipping this call (rule above)", None)


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    data, sha, ib, secs = load()
    L = []

    def P(s=""):
        L.append(s)
        print(s)

    P("SHA256 %s" % sha)
    P("HASH MATCH %s" % (sha == EXPECT_SHA))
    if sha != EXPECT_SHA:
        P("FATAL hash mismatch - refusing to analyse")
        open(os.path.join(OUTDIR, "run_log.txt"), "w", encoding="utf-8").write("\n".join(L))
        return 2
    P("ImageBase 0x%08X" % ib)
    for nm, sva, vs, ro, rs in secs:
        P("  %-9s va=0x%08X vsize=0x%06X raw=0x%08X rawsize=0x%06X" % (nm, sva, vs, ro, rs))

    img = Image(data, ib, secs)
    _n, tva, tvs, tro, trs = img.by_name[".text"]
    tend = tva + min(trs, tvs)
    sw = Sweep(img, tva, tend)
    P(".text 0x%08X..0x%08X  sweep=%d insns, %d skipdata bytes" % (tva, tend, sw.count, sw.skipped))

    # -------------------------------------------------- discovery per target
    e8 = scan_rel32(img, tva, tend, 0xE8)
    e8_by_t = collections.defaultdict(list)
    spurious = []
    for site, tgt in e8:
        ins = sw.at(site)
        if ins is None or ins.id != X.X86_INS_CALL:
            spurious.append((site, tgt))
            continue
        e8_by_t[tgt].append(site)

    e9 = scan_rel32(img, tva, tend, 0xE9)
    e9_by_t = collections.defaultdict(list)
    for site, tgt in e9:
        ins = sw.at(site)
        if ins is not None and ins.id == X.X86_INS_JMP:
            e9_by_t[tgt].append(site)

    abs_calls = collections.defaultdict(list)   # abs target -> [(site, ins)]
    reg_calls = []
    mem_calls = []
    for a in sw.order:
        ins = sw.at(a)
        if ins.id != X.X86_INS_CALL:
            continue
        ct = call_target(ins)
        if ct is None:
            continue
        kind, tgt = ct
        if kind == "abs":
            abs_calls[tgt].append((a, ins))
        elif kind == "reg":
            reg_calls.append((a, ins))
        elif kind == "mem":
            mem_calls.append((a, ins))

    P("")
    P("=== discovery ===")
    P("raw E8 byte hits: %d ; spurious (not insn starts): %d" % (len(e8), len(spurious)))
    P("direct call insns: %d ; call reg: %d ; call [reg+disp]: %d ; call [abs]: %d"
      % (sum(len(v) for v in e8_by_t.values()), len(reg_calls), len(mem_calls),
         sum(len(v) for v in abs_calls.values())))

    rows = []
    for t in TARGETS:
        for s in sorted(set(e8_by_t.get(t, []))):
            v, r, m = classify(sw, s)
            ins = sw.at(s)
            rows.append({"site": s, "callee": t, "guarded": v, "rule": r,
                         "kind": "call rel32", "text": "%s %s" % (ins.mnemonic, ins.op_str)})
        for s, ins in abs_calls.get(t, []):
            v, r, m = classify(sw, s)
            rows.append({"site": s, "callee": t, "guarded": v, "rule": r,
                         "kind": "call [abs]", "text": "%s %s" % (ins.mnemonic, ins.op_str)})

    P("")
    P("=== indirect resolves to the six ===")
    any_i = False
    for t in TARGETS:
        for s, ins in abs_calls.get(t, []):
            any_i = True
            P("  0x%06X -> 0x%06X  %s" % (s, t, ins.op_str))
        for s in sorted(set(e9_by_t.get(t, []))):
            any_i = True
            P("  0x%06X --jmp--> 0x%06X (tail jump, not a call)" % (s, t))
    if not any_i:
        P("  none: no call [abs] and no jmp rel32 targets any of the six")
    for t in TARGETS:
        for s in sorted(set(e9_by_t.get(t, []))):
            ins = sw.at(s)
            rows.append({"site": s, "callee": t, "guarded": "TAILJMP",
                         "rule": "E9 jmp rel32; not a call site",
                         "kind": "jmp rel32", "text": "%s %s" % (ins.mnemonic, ins.op_str)})

    P("")
    P("=== literal 4-byte pointer occurrences of the six (vtables/window procs) ===")
    for t in TARGETS:
        tb = t.to_bytes(4, "little")
        hits, idx = [], 0
        while True:
            k = data.find(tb, idx)
            if k < 0:
                break
            va = img.off2va(k)
            if va is not None:
                hits.append(va)
            idx = k + 1
        P("  0x%06X: %d  %s" % (t, len(hits), " ".join("0x%X" % h for h in hits)))

    # -------------------------------------------------------------- counting
    def counts(t):
        g = sum(1 for r in rows if r["callee"] == t and r["guarded"] == "guarded")
        u = sum(1 for r in rows if r["callee"] == t and r["guarded"] == "unguarded")
        a = sum(1 for r in rows if r["callee"] == t and r["guarded"] == "AMBIGUOUS")
        return g, u, a, g + u + a

    P("")
    P("=== measured per routine (all direct call sites) ===")
    for t in TARGETS:
        g, u, a, tot = counts(t)
        P("  0x%06X total=%2d guarded=%2d unguarded=%2d ambiguous=%d" % (t, tot, g, u, a))

    # --------------------------------------------------------- containing_fn
    calltgt = set()
    for a in sw.order:
        ins = sw.at(a)
        if ins.id == X.X86_INS_CALL:
            ct = call_target(ins)
            if ct and ct[0] == "rel":
                calltgt.add(ct[1])
    prologue = set()
    for a in sw.order:
        ins = sw.at(a)
        if ins.mnemonic == "push" and ins.op_str == "ebp":
            nx = sw.at(a + ins.size)
            if nx is not None and nx.mnemonic == "mov" and \
                    nx.op_str.replace(" ", "") == "ebp,esp":
                prologue.add(a)
    fn_starts = sorted(calltgt | prologue | set(TARGETS))

    def fn_of(va):
        k = bisect.bisect_right(fn_starts, va) - 1
        return fn_starts[k] if k >= 0 else None

    # ------------------------------------------------------------ call_sites
    out = ["site_addr\tcallee\tcontaining_fn\tguarded\trule_applied\tinsn_text"]
    for r in sorted(rows, key=lambda z: (z["callee"], z["site"])):
        out.append("0x%08X\t0x%08X\t0x%08X\t%s\t%s\t%s" % (
            r["site"], r["callee"], fn_of(r["site"]) or 0,
            r["guarded"], r["rule"].replace("\t", " "), r["text"]))
    open(os.path.join(OUTDIR, "call_sites.tsv"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(out) + "\n")

    # ------------------------------------------------------------------ diff
    D = []
    D.append("CLAIMED vs MEASURED -- unguarded direct call sites")
    D.append("")
    D.append("%-11s %8s %9s %6s %8s %8s  %s" % ("routine", "claimed", "measured",
                                               "delta", "guarded", "ambig", "verdict"))
    tc = tm = 0
    for t in TARGETS:
        g, u, a, _tot = counts(t)
        c = CLAIM[t]
        tc += c
        tm += u
        D.append("%-11s %8d %9d %6d %8d %8d  %s" % (
            "0x%06X" % t, c, u, u - c, g, a, "CONFIRMED" if c == u else "REFUTED"))
    D.append("%-11s %8d %9d %6d" % ("TOTAL", tc, tm, tm - tc))
    D.append("")
    D.append("TOTAL uguarded: claimed %d vs measured %d -> %s"
             % (CLAIM_TOTAL, tm, "CONFIRMED" if tm == CLAIM_TOTAL else "REFUTED"))
    g30 = counts(0x724730)
    D.append("0x724730 total call sites: claimed %d vs measured %d -> %s"
             % (CLAIM_SITES_724730, g30[3],
                "CONFIRMED" if g30[3] == CLAIM_SITES_724730 else "REFUTED"))
    D.append("")
    D.append("Per-routine measured site lists with classification:")
    for t in TARGETS:
        D.append("")
        D.append("0x%06X" % t)
        for r in sorted([x for x in rows if x["callee"] == t], key=lambda z: z["site"]):
            D.append("  0x%08X  %-9s %s" % (r["site"], r["guarded"], r["rule"]))
    D.append("")
    D.append("SPURIOUS E8 byte hits -- hex bytes that look like `call <one of the"
             " six>` but are NOT instruction starts (immediates). Patch code that"
             " keys on raw bytes would corrupt these. Full list: %d entries." % len(spurious))
    if spurious:
        # The dangerous subset: hits whose computed target lands inside .text,
        # i.e. they look plausible to a naive validator.
        in_text = [(s, t) for s, t in spurious if tva <= t < tend]
        D.append("  of these, %d resolve to a PLAUSIBLE in-.text address (most dangerous);"
                 " first 25:" % len(in_text))
        for s, t in in_text[:25]:
            D.append("    0x%08X -> 0x%08X" % (s, t))
        if len(in_text) > 25:
            D.append("    ... (%d more in-.text spurious hits, truncated)" % (len(in_text) - 25))
        D.append("  remaining %d resolve outside .text and are visibly bogus:"
                 % (len(spurious) - len(in_text)))
        for s, t in spurious[:10]:
            if not (tva <= t < tend):
                D.append("    0x%08X -> 0x%08X" % (s, t))
        D.append("    ... (truncated)")
    else:
        D.append("  none")
    open(os.path.join(OUTDIR, "diff_vs_claim.txt"), "w", encoding="utf-8",
         newline="\n").write("\n".join(D) + "\n")

    # --------------------------------------------------------------- samples
    S = []

    def show(va, before, after, note=""):
        """Dump from the AUTHORITATIVE sweep only (never re-decode)."""
        k = sw.idx(va)
        if k is None:
            S.append("## 0x%06X NOT AN INSN START" % va)
            return
        lo, hi = max(0, k - before), min(len(sw.order), k + after + 1)
        S.append("-- %s" % note)
        for j in range(lo, hi):
            a = sw.order[j]
            i = sw.at(a)
            S.append("0x%06X  %-22s %-7s %s%s" % (a, i.bytes.hex(), i.mnemonic,
                                                  i.op_str, "   <== SITE" if a == va else ""))
        S.append("")

    for t in (0x724730, 0x724580):
        for want in ("guarded", "unguarded"):
            sel = sorted([r for r in rows if r["callee"] == t and r["guarded"] == want],
                         key=lambda z: z["site"])[:6]
            S.append("=" * 76)
            S.append("0x%06X  %s  (%d sites total, showing %d)" % (
                t, want.upper(), len([r for r in rows if r["callee"] == t and
                                      r["guarded"] == want]), len(sel)))
            S.append("=" * 76)
            if not sel:
                S.append("  NONE")
            for r in sel:
                S.append("SITE 0x%08X  %s" % (r["site"], r["rule"]))
                show(r["site"], 10, 3, "context")
    for t in (0x7241A0, 0x724520, 0x724530, 0x724540):
        S.append("=" * 76)
        S.append("0x%06X all sites" % t)
        S.append("=" * 76)
        for r in sorted([x for x in rows if x["callee"] == t], key=lambda z: z["site"]):
            S.append("SITE 0x%08X  %s  %s" % (r["site"], r["guarded"], r["rule"]))
        show(t, 0, 6, "routine entry")
    S.append("")
    S.append("=" * 76)
    S.append("FALL-THROUGH 0x6D1744 -> 0x6D1749")
    S.append("=" * 76)
    show(0x6D1744, 12, 6, "0x6D1744 call 0x724730 then 0x6D1749 call 0x724580")
    i44, i49 = sw.at(0x6D1744), sw.at(0x6D1749)
    S.append("0x6D1744 in sweep: %s" % (i44 and "%s %s size %d" % (i44.mnemonic, i44.op_str, i44.size)))
    if i44:
        S.append("  0x6D1744 + %d = 0x%X" % (i44.size, 0x6D1744 + i44.size))
    S.append("0x6D1749 in sweep: %s" % (i49 and "%s %s" % (i49.mnemonic, i49.op_str)))
    S.append("")
    S.append("=" * 76)
    S.append("0x6F3F40 SITES")
    S.append("=" * 76)
    show(0x6F3F40, 0, 8, "0x6F3F40 entry")
    for site, claim_txt in ((0x6F409C, "this+0x155"), (0x6F4124, "this+0x159"),
                            (0x6F4173, "this+0xAC, claimed mov ecx form")):
        ins = sw.at(site)
        S.append("SITE 0x%06X (claim %s): %s" % (
            site, claim_txt,
            "%s %s [%s]" % (ins.mnemonic, ins.op_str, ins.bytes.hex()) if ins else "NOT AN INSN"))
        show(site, 4, 6, "context")
    open(os.path.join(OUTDIR, "samples.txt"), "w", encoding="utf-8",
         newline="\n").write("\n".join(S) + "\n")

    # --------------------------------------------------------------- miss hunt
    P("")
    P("=== MISS HUNT: [+0x250] dereferences in the whole .text ===")
    derefs = []
    for a in sw.order:
        ins = sw.at(a)
        for o in ins.operands:
            if o.type == X.X86_OP_MEM and o.mem.disp == 0x250 and o.mem.base:
                derefs.append((a, ins))
                break
    P("count %d" % len(derefs))
    per_fn = collections.defaultdict(list)
    for a, ins in derefs:
        per_fn[fn_of(a)].append((a, ins))
    for fn in sorted(per_fn):
        tag = "  <-- IN CLAIM LIST" if fn in TARGETS else ""
        P("  fn 0x%08X  %d use(s)%s" % (fn, len(per_fn[fn]), tag))
        for a, ins in per_fn[fn]:
            P("      0x%06X  %-7s %s" % (a, ins.mnemonic, ins.op_str))

    # routines whose FIRST memory operand is [this+0x250]
    P("")
    P("=== routines whose first memory operand is [this+0x250] ===")
    for fn in sorted(per_fn):
        first = None
        p = fn
        for _ in range(60):
            ins = sw.at(p)
            if ins is None:
                break
            if any(o.type == X.X86_OP_MEM for o in ins.operands):
                first = p
                break
            if ins.mnemonic == "ret":
                break
            p += ins.size
        if first is not None and first == min(a for a, _ in per_fn[fn]):
            mark = "IN LIST" if fn in TARGETS else ">>> NOT IN CLAIM LIST"
            P("  0x%08X first deref [this+0x250] at 0x%06X  %s" % (fn, first, mark))

    # which of the six actually deref +0x250
    P("")
    P("=== of the six, which touch +0x250 at all? ===")
    for t in TARGETS:
        n = len(per_fn.get(t, []))
        P("  0x%06X  [+0x250 uses: %d]  %s" % (t, n, "YES" if n else "NO"))

    # ------------------------------------------------------- ecx load sources
    P("")
    P("=== how ecx is set before each call (who supplies `this`) ===")
    for t in TARGETS:
        prev = collections.Counter()
        for r in [x for x in rows if x["callee"] == t and x["kind"] == "call rel32"]:
            j = sw.idx(r["site"]) - 1
            p = sw.at(sw.order[j])
            prev["%s %s" % (p.mnemonic, p.op_str)] += 1
        P("  0x%06X:" % t)
        for k2, c in prev.most_common(6):
            P("     %2d x  %s" % (c, k2))

    P("")
    P("=== writers of [0x887368] (the global most callers load into ecx) ===")
    for a in sw.order:
        ins = sw.at(a)
        if not ins.operands:
            continue
        d = ins.operands[0]
        if d.type == X.X86_OP_MEM and d.mem.disp == 0x887368 and d.mem.base == 0:
            P("  0x%06X  %s %s" % (a, ins.mnemonic, ins.op_str))

    open(os.path.join(OUTDIR, "run_log.txt"), "w", encoding="utf-8",
         newline="\n").write("\n".join(L) + "\n")
    P("")
    P("DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
